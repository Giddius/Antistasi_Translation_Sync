"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from pathlib import Path
from typing import Generator

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion [Constants]


class AntistasiTranslationSyncError(BaseException):
    ...


class StringtableError(AntistasiTranslationSyncError):
    ...


class UnremoveableEntryError(StringtableError):
    ...


class StringtableContainerError(StringtableError):
    ...


class DuplicateContainerError(StringtableContainerError):
    ...


class StringtableKeyError(StringtableError):
    ...


class DuplicateKeyError(StringtableKeyError):
    ...


class StringtableEntryError(StringtableError):
    ...


class DuplicateEntryError(StringtableEntryError):
    ...


class TolgeeError(AntistasiTranslationSyncError):
    ...


class TolgeeHTTPError(TolgeeError):
    ...


class MaxRetriesReachedError(TolgeeHTTPError):
    ...


class NoRetryStatusError(TolgeeHTTPError):
    ...


class NoTokenFoundError(TolgeeError):
    ...


class TolgeeProjectError(TolgeeError):
    ...


# region [Main_Exec]
if __name__ == '__main__':
    ...
# endregion [Main_Exec]
