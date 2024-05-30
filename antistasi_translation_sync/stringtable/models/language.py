"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import sys
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable
from pathlib import Path
import re
if sys.version_info >= (3, 11):
    pass
else:
    pass
# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    ...

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion [Constants]


@runtime_checkable
class LanguageLike(Protocol):

    @property
    def language_name(self) -> str:
        ...


LANGUAGE_NAME_BRACKET_REGEX = re.compile(r"\(.*?\)$")


class ArmaLanguage(Enum):
    ORIGINAL = "Original"
    GERMAN = "German"
    ITALIAN = "Italian"
    SPANISH = "Spanish"
    FRENCH = 'French'
    KOREAN = "Korean"
    JAPANESE = "Japanese"
    RUSSIAN = "Russian"
    POLISH = "Polish"
    CZECH = "Czech"
    PORTUGUESE = "Portuguese"
    TURKISH = "Turkish"
    CHINESESIMP = "Chinesesimp"
    UKRAINIAN = "Ukrainian"
    DUTCH = "Dutch"
    NORWEGIAN = "Norwegian"
    SWEDISH = "Swedish"
    FINNISH = "Finnish"
    DANISH = "Danish"

    @property
    def language_name(self) -> str:
        return self.value

    @classmethod
    def _missing_(cls, value: object) -> Any:
        try:
            value = value.language_name
        except AttributeError:
            pass

        if isinstance(value, str):
            mod_value = LANGUAGE_NAME_BRACKET_REGEX.sub("", value).strip().upper()
            if mod_value == "ENGLISH":
                return cls.ORIGINAL

            try:
                return cls._member_map_[mod_value]
            except KeyError:
                pass
        return super()._missing_(value)


# region [Main_Exec]
if __name__ == '__main__':
    pass

# endregion [Main_Exec]
