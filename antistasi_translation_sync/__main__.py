"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from typing import Union
from pathlib import Path
from weakref import proxy

# * Third Party Imports --------------------------------------------------------------------------------->


# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_translation_sync import __version__, get_description
from antistasi_translation_sync.errors import StringtableError, NoTokenFoundError
from antistasi_translation_sync.tolgee import TolgeeClient
from antistasi_translation_sync.stringtable import StringTable, ArmaLanguage, get_and_resolve_stringtable
from antistasi_translation_sync.configuration import Config
from antistasi_translation_sync.tolgee.models import Project
from antistasi_translation_sync.command_line_parser import get_command_line_parser
from antistasi_translation_sync.constants import FALLBACK_NAMESPACE_NAME

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion [Constants]


IN_FILE = THIS_FILE_DIR.joinpath("Stringtable_example_complex.xml")

# import dotenv
# dotenv.load_dotenv(dotenv.find_dotenv("translation_automation.env"))


class Syncer:

    def __init__(self,
                 stringtable_file_path: Union[str, os.PathLike, Path],
                 config: "Config") -> None:

        self.stringtable_file_path: Path = Path(stringtable_file_path).resolve()
        self.config = config

        self.stringtable: "StringTable" = None
        self.tolgee_project: "Project" = None

    def _sync_namespaces(self) -> None:
        for translation_key in self.tolgee_project.keys:

            # if translation_key.is_deleted:
            #     continue
            if translation_key.namespace.name == FALLBACK_NAMESPACE_NAME:
                continue
            try:
                stringtable_key = self.stringtable.get_key(translation_key.name)
                if translation_key.namespace.name != stringtable_key.container.name:
                    print(f"Updating Namespace for key {translation_key.name!r} from {translation_key.namespace.name!r} to {stringtable_key.container.name!r}")
                    translation_key.change_namespace(new_namespace_name=stringtable_key.container.name)
            except KeyError:
                continue

    def _sync_removed_keys(self) -> None:
        for translation_key in self.tolgee_project.keys:

            # if translation_key.is_deleted:
            #     continue

            try:
                stringtable_key = self.stringtable.get_key(translation_key.name)
                translation_key.unset_deleted()
            except KeyError:
                translation_key.set_deleted()

    def _sync_original_online_translation(self) -> None:
        for stringtable_key in self.stringtable.iter_keys():
            original_text = stringtable_key.original_text
            was_updated = self.tolgee_project.update_or_create_from_stringtable_entry(stringtable_entry=stringtable_key.original_entry)
            if was_updated:
                print(f"Updated original translation for {stringtable_key.container.name!r}|{stringtable_key.name!r}|{original_text!r}")

    def _sync_online_translations_to_stringtable(self) -> None:
        for stringtable_key in self.stringtable.iter_keys():
            translation_key = self.tolgee_project.get_key_by_name(stringtable_key.name)
            stringtable_key.remove_all_not_original_entries()
            for translation_entry in (_entry for _entry in translation_key._entry_map.values() if ArmaLanguage(_entry.language) is not ArmaLanguage.ORIGINAL):

                if translation_entry.outdated is True:
                    continue

                if translation_entry.text == "":
                    continue

                stringtable_key.set_text_for_language(translation_entry.language, translation_entry.text)

    def _sync_stringtable_to_stringtable_file(self) -> None:
        self.stringtable_file_path.write_text(self.stringtable.as_text(self.config.stringtable_config.indentation), encoding='utf-8', errors='ignore')

    def _load_stringtable(self) -> None:
        if self.stringtable_file_path.exists() is False or self.stringtable_file_path.is_file() is False:
            raise StringtableError(f"invalid stringtable file {self.stringtable_file_path.as_posix()!r}.")

        self.stringtable = get_and_resolve_stringtable(self.stringtable_file_path)

    def _load_tolgee_project(self) -> None:
        self.tolgee_project.setup()

    def _remove_tolgee_project(self, project_object: "Project") -> None:
        self.tolgee_project = None

    def run(self) -> None:
        self._load_stringtable()
        with TolgeeClient(base_url=f"{self.config.tolgee_config.base_url}/v2/projects", api_key=self.config.tolgee_config.get_tolgee_api_project_token(self.stringtable.name)) as tolgee_client:
            self.tolgee_project = proxy(tolgee_client.project, self._remove_tolgee_project)
            self._load_tolgee_project()
            self._sync_namespaces()
            self._sync_removed_keys()
            self._sync_original_online_translation()
            self._sync_online_translations_to_stringtable()
            self._sync_stringtable_to_stringtable_file()


def main() -> None:

    config = Config()
    description = get_description()

    cl_parser = get_command_line_parser(version=__version__, description=description)

    cl_parser.parse_args(config=config)

    print("")

    for target in config.targets:
        try:
            syncer = Syncer(stringtable_file_path=target, config=config)
            syncer.run()
        except NoTokenFoundError:
            print(f"!!!!!! NO TOKEN FOUND FOR {target!r}")
            print(f"!!!!!! skipping {target!r}")
            continue


# region [Main_Exec]
if __name__ == '__main__':
    main()


# endregion [Main_Exec]
