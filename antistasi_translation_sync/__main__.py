"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from typing import Union
from pathlib import Path
from typing import TypeVar, Iterable, Generator
from weakref import proxy
import sys
import httpx
from time import sleep

import random
import textwrap

# * Third Party Imports --------------------------------------------------------------------------------->


# * Local Imports --------------------------------------------------------------------------------------->
import logging
from antistasi_translation_sync.stringtable.models import ArmaLanguage
from antistasi_translation_sync.tolgee.models import EntryState, Language as TolgeeLanguage
from antistasi_translation_sync import __version__, get_description, get_package_name
from antistasi_translation_sync.errors import StringtableError, NoTokenFoundError
from antistasi_translation_sync.tolgee import TolgeeClient
from antistasi_translation_sync.stringtable import StringTable, ArmaLanguage, get_and_resolve_stringtable
from antistasi_translation_sync.configuration import Config
from antistasi_translation_sync.tolgee.models import Project
from antistasi_translation_sync.command_line_parser import get_command_line_parser
from antistasi_translation_sync.change_recorder import ChangeRecorder, ChangedNamespaceChange, ChangeTypus
# from antistasi_translation_sync.validation.repo_usage_collector import RepoUsageCollector

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR: Path = Path(__file__).parent.absolute()
log = logging.getLogger(get_package_name())
# endregion [Constants]


if sys.flags.dev_mode is True or os.getenv("IS_DEV", "false") == "true":
    try:
        import dotenv

        dotenv.load_dotenv(dotenv.find_dotenv("translation_automation.env"))

    except ImportError:
        pass


class Syncer:

    def __init__(self,
                 stringtable_file_path: Union[str, os.PathLike, Path],
                 config: "Config",
                 change_recorder: Union[None, ChangeRecorder] = None) -> None:

        self.stringtable_file_path: Path = Path(stringtable_file_path).resolve()
        self.config = config

        self.stringtable: "StringTable" = None
        self.tolgee_project: "Project" = None

        self.change_recorder = change_recorder

    def _sync_namespaces(self) -> None:
        for translation_key in self.tolgee_project.keys:

            # if translation_key.is_deleted:
            #     continue

            try:
                stringtable_key = self.stringtable.get_key(translation_key.name)
                if translation_key.namespace.name != stringtable_key.container.name:
                    print(f"Updating Namespace for key {translation_key.name!r} from {translation_key.namespace.name!r} to {stringtable_key.container.name!r}")
                    old_namespace = translation_key.namespace
                    translation_key.change_namespace(new_namespace_name=stringtable_key.container.name)
                    if self.change_recorder is not None:
                        self.change_recorder.add_change_item(ChangedNamespaceChange(translation_key.project, key=translation_key, new_namespace=translation_key.namespace, old_namespace=old_namespace))
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
        self.tolgee_project.refresh()
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


T = TypeVar("T")


def iter_grouped(in_iterable: Iterable[T], group_size: int = 2) -> Generator[list[T], None, None]:
    sentinel = object()
    _iterator = iter(in_iterable)
    collected = []
    while True:
        next_item = next(_iterator, sentinel)
        if next_item is sentinel:
            break

        collected.append(next_item)
        if len(collected) == group_size:
            yield collected.copy()
            collected.clear()

    if len(collected) != 0:
        yield collected.copy()
        collected.clear()


def send_changed_namespace_data(webhook_url: httpx.URL,
                                project_name: str,
                                changed_namespaces: list["ChangedNamespaceChange"] = None,
                                *,
                                avatar_url: str = None,
                                ) -> None:

    if changed_namespaces is None or len(changed_namespaces) <= 0:
        return

    for _changed_namespaces in iter_grouped(changed_namespaces, 5):

        data = {
            "content": "",
            "username": "Tolgee",
            "avatar_url": avatar_url or "https://res.cloudinary.com/practicaldev/image/fetch/s--lEHWeOyj--/c_fill,f_auto,fl_progressive,h_320,q_auto,w_320/https://dev-to-uploads.s3.amazonaws.com/uploads/organization/profile_image/4876/6f470322-e090-4c8a-8aba-3c40e786607d.png"
        }

        data["embeds"] = [
            {

                "title": f"Project: `{project_name!s}`",
                "description": "# Namespace Changes:\n\n",
                "color": 15105570,
                "fields": [{"name": f"__{c.key.name!s}__", "value": f"```js\n{c.old_namespace.name!r} -> {c.new_namespace.name!r}\n```", "inline": False} for idx, c in enumerate(_changed_namespaces, 1)]

            }
        ]
        print("------------------")
        print(data["embeds"][0]["description"])
        print("------------------")

        with httpx.Client() as _client:
            request = _client.build_request("POST", webhook_url, json=data)
            response = _client.send(request)
            response.raise_for_status()
            response.close()


def gather_comments() -> dict:
    ...


def sync_translations(config: Config) -> None:
    print("")
    recorder = None
    for target in config.targets:
        log.info(f"--------- Working on file {target!s}")

        try:
            # repo_usage_collector = RepoUsageCollector(target.parent).search()

            syncer = Syncer(stringtable_file_path=target, config=config, change_recorder=recorder)
            syncer.run()

        except NoTokenFoundError:
            print(f"!!!!!! NO TOKEN FOUND FOR {target!r}")
            print(f"!!!!!! skipping {target!r}")
            continue


def clone(base_url: str, src_token: str, tgt_token: str) -> None:
    with TolgeeClient(base_url=f"{base_url}/v2/projects", api_key=src_token) as src_tolgee_client:
        src_project = src_tolgee_client.project.setup()

        with TolgeeClient(base_url=f"{base_url}/v2/projects", api_key=tgt_token) as tgt_tolgee_client:

            tgt_tolgee_client.project.setup()
            total_amount_keys = len(src_project.keys)
            for _idx, src_key in enumerate(src_project.keys, 1):
                request_data = {"key": src_key.name,
                                "namespace": src_key.namespace.name,
                                "translations": {_entry.language.tag: _entry.text for _entry in src_key._entry_map.values()}}

                tgt_tolgee_client.client.post("/translations", json=request_data)
                log.info("%r/%r Cloned Key %r", _idx, total_amount_keys, src_key)
            sleep(1)
            tgt_tolgee_client.project.refresh()
            sleep(1)
            log.info("Starting to clone outdated value for all entries")

            total_amount_entries = len(src_project.entries)
            for idx, src_entry in enumerate(src_project.entries, 1):

                tgt_key = tgt_tolgee_client.project.get_key_by_name(src_entry.key.name)
                try:
                    tgt_entry = tgt_key[src_entry.language]

                except KeyError:
                    continue
                tgt_tolgee_client.set_outdated_for_translation_entry(tgt_entry, src_entry.outdated)
                if src_entry.state is not EntryState.UNTRANSLATED:
                    tgt_tolgee_client.set_state_for_translation_entry(tgt_entry, src_entry.state)
                    log.info("%r set State for %r to %r", idx, tgt_entry, src_entry.state)

                log.info("%r/%r set Outdated for %r to %r", idx, total_amount_entries, tgt_entry, src_entry.outdated)


STD_LANGUAGES: tuple[TolgeeLanguage] = (
    TolgeeLanguage(language_id=-1, name='Original', tag='en', originalName='English', base=True, flagEmoji='🇬🇧'),
    TolgeeLanguage(language_id=-1, name='Ukrainian', tag='uk-UA', originalName='українська (Україна)', base=False, flagEmoji='🇺🇦'),
    TolgeeLanguage(language_id=-1, name='Czech', tag='cs-CZ', originalName='čeština (Česko)', base=False, flagEmoji='🇨🇿'),
    TolgeeLanguage(language_id=-1, name='German', tag='de', originalName='Deutsch', base=False, flagEmoji='🇩🇪'),
    TolgeeLanguage(language_id=-1, name='Spanish', tag='es-ES', originalName='español (España)', base=False, flagEmoji='🇪🇸'),
    TolgeeLanguage(language_id=-1, name='French', tag='fr-FR', originalName='français (France)', base=False, flagEmoji='🇫🇷'),
    TolgeeLanguage(language_id=-1, name='Italian', tag='it-IT', originalName='italiano (Italia)', base=False, flagEmoji='🇮🇹'),
    TolgeeLanguage(language_id=-1, name='Korean', tag='ko-KR', originalName='한국어(대한민국)', base=False, flagEmoji='🇰🇷'),
    TolgeeLanguage(language_id=-1, name='Polish', tag='pl-PL', originalName='polski (Polska)', base=False, flagEmoji='🇵🇱'),
    TolgeeLanguage(language_id=-1, name='Portuguese', tag='pt-BR', originalName='português (Brasil)', base=False, flagEmoji='🇧🇷'),
    TolgeeLanguage(language_id=-1, name='Russian', tag='ru', originalName='русский', base=False, flagEmoji='🇷🇺'),
    TolgeeLanguage(language_id=-1, name='Turkish', tag='tr-TR', originalName='Türkçe (Türkiye)', base=False, flagEmoji='🇹🇷'),
    TolgeeLanguage(language_id=-1, name='Chinesesimp', tag='zh-Hans', originalName='简体中文', base=False, flagEmoji='🇸🇬'),
    TolgeeLanguage(language_id=-1, name='Danish', tag='da-DK', originalName='dansk (Danmark)', base=False, flagEmoji='🇩🇰'),
    TolgeeLanguage(language_id=-1, name='Dutch', tag='nl-NL', originalName='Nederlands (Nederland)', base=False, flagEmoji='🇳🇱'),
    TolgeeLanguage(language_id=-1, name='Norwegian', tag='nn-NO', originalName='norsk nynorsk (Noreg)', base=False, flagEmoji='🇳🇴'),
    TolgeeLanguage(language_id=-1, name='Swedish', tag='sv-SE', originalName='svenska (Sverige)', base=False, flagEmoji='🇸🇪'),
    TolgeeLanguage(language_id=-1, name='Finnish', tag='fi-FI', originalName='suomi (Suomi)', base=False, flagEmoji='🇫🇮'),
    TolgeeLanguage(language_id=-1, name='Japanese', tag='ja', originalName="日本語", base=False, flagEmoji='🇯🇵')
)


def create_project_with_specific_languages(base_url: str,
                                           token: str,
                                           project_name: str,
                                           organization_id: int,
                                           languages: Iterable[TolgeeLanguage]):
    _base_languages = [lang for lang in languages if lang.base is True]
    if len(_base_languages) <= 0:
        raise ValueError("No Base language provided.")

    if len(_base_languages) > 1:
        raise ValueError(f"Only a single language is allowed to be the base language not {len(_base_languages)!r}.")

    base_language = _base_languages[0]

    data = {"name": project_name,
            "organizationId": organization_id,
            "icuPlaceholders": False,
            "baseLanguageTag": base_language.tag,
            "languages": [lang.to_data() for lang in languages]}

    with httpx.Client(base_url=base_url, headers={"X-API-Key": token}) as _client:
        result = _client.post("v2/projects", json=data)
        result.raise_for_status()
        result_data = result.json()
        log.debug("%r", result_data)
        log.info("Created Project %r with ID: %r and slug: %r", result_data.get("name"), result_data.get("id"), result_data.get("slug"))


def main() -> None:

    # config = Config()
    # description = get_description()
    cl_parser = get_command_line_parser()

    config = cl_parser.parse_args(config=Config())

    sync_translations(config=config)


# region [Main_Exec]
if __name__ == '__main__':
    from antistasi_translation_sync import add_file_logging_handler

    add_file_logging_handler(log)

    import json
    import dotenv
    from pprint import pp
    dotenv.load_dotenv(dotenv.find_dotenv("translation_automation.env"))
    with httpx.Client(headers={"X-API-Key": os.getenv("AUTOMATION_TOKEN")}) as client:

        response = client.get("https://tolgee.targetingsnake.de/v2/api-keys/39", params={"projectId": 11})
        print(f"{response.text=}", flush=True)

        response.raise_for_status()
        pp(response.json())
    # project_names_to_create = ("A3-Addons-language_f_beta",
    #                            "A3-Addons-language_f_bootcamp",
    #                            "A3-Addons-language_f_decade",
    #                            "A3-Addons-language_f_epa",
    #                            "A3-Addons-language_f_epb",
    #                            "A3-Addons-language_f_epc",
    #                            "A3-Addons-language_f_exp_a",
    #                            "A3-Addons-language_f_exp_b",
    #                            "A3-Addons-language_f_gamma",
    #                            "A3-Addons-language_f_mod",
    #                            "A3-Addons-language_f_warlords",
    #                            "A3-Addons-languagemissions_f",
    #                            "A3-Addons-languagemissions_f_beta",
    #                            "A3-Addons-languagemissions_f_bootcamp",
    #                            "A3-Addons-languagemissions_f_epa",
    #                            "A3-Addons-languagemissions_f_epb",
    #                            "A3-Addons-languagemissions_f_epc",
    #                            "A3-Addons-languagemissions_f_exp_a",
    #                            "A3-Addons-languagemissions_f_gamma",
    #                            "A3-Dta-languagecore_f")

    # token = os.getenv("AUTOMATION_TOKEN")
    # organization_id = 11
    # base_url = "https://tolgee.targetingsnake.de"

    # for project_name in project_names_to_create:
    #     create_project_with_specific_languages(base_url=base_url, token=token, project_name=project_name, organization_id=organization_id, languages=list(STD_LANGUAGES))
    #     sleep(30 + sum([random.random() for _ in range(10)]))
# endregion [Main_Exec]
