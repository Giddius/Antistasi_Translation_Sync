"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from pathlib import Path
from time import sleep
import sys
import os
from time import sleep
from datetime import datetime, UTC, timedelta
import httpx
# * Gid Imports ----------------------------------------------------------------------------------------->
import dotenv
from antistasi_translation_sync.stringtable import StringtableParser, get_and_resolve_stringtable
from tolgee import TolgeeClient
# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion [Constants]


IN_FILE = THIS_FILE_DIR.parent.joinpath("tests", "data", "Stringtable_example_complex.xml")


dotenv.load_dotenv(dotenv.find_dotenv("translation_automation.env"))


def main() -> None:
    stringtable = get_and_resolve_stringtable(IN_FILE)

    with TolgeeClient(base_url="https://tolgee.targetingsnake.de/v2/projects", api_key=os.environ["TEST_TOLGEE_API_KEY"]) as tolgee:
        tolgee.project.setup()
        idx = 0
        for original_lang_entry in stringtable.iter_all_original_language_entries():
            entry = tolgee.project[original_lang_entry.container_name][original_lang_entry.key_name][original_lang_entry.language]
            if entry.update_from_stringtable_entry(original_lang_entry) is True:
                print(f"UPDATED {original_lang_entry.container_name!r} {original_lang_entry.key_name!r} {original_lang_entry.language!r}", flush=True)
    IN_FILE.write_text(stringtable.as_text(), encoding='utf-8', errors='ignore')


# region [Main_Exec]
if __name__ == '__main__':
    main()


# endregion [Main_Exec]
