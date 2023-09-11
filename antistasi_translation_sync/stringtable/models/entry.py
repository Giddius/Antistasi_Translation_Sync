"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import sys
import xml.etree.ElementTree as ET
from html import escape as html_escape
from typing import TYPE_CHECKING
from pathlib import Path

from .language import ArmaLanguage

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self
# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_translation_sync.stringtable.models.key import StringTableKey

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion [Constants]


class StringTableEntry:

    __slots__ = ("language",
                 "text",
                 "key")

    def __init__(self,
                 language: "ArmaLanguage",
                 text: str) -> None:
        self.language = language
        self.text = text
        self.key: "StringTableKey" = None

    @classmethod
    def from_xml_element(cls, element: ET.Element) -> Self:
        raw_language = element.tag
        raw_text = element.text
        instance = cls(language=ArmaLanguage(raw_language), text=raw_text)

        return instance

    def set_key(self, key: "StringTableKey") -> None:
        self.key = key

    @property
    def is_original(self) -> bool:
        return ArmaLanguage(self.language) is ArmaLanguage.ORIGINAL

    @property
    def html_escaped_text(self) -> str:
        text = html_escape(self.text, False)

        # text = text.replace(r'\n', r'&lt;br/&gt;')

        return text

    @property
    def key_name(self) -> str:
        return self.key.name

    @property
    def container_name(self) -> str:
        return self.key.container.name

    def as_text(self, indentation: int = 2) -> str:
        indent_value = (" " * indentation) * 4

        language_text = self.language.name.title()
        return f"{indent_value}<{language_text}>{self.html_escaped_text}</{language_text}>"

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(language={self.language!r}, text={self.text!r})'


# region [Main_Exec]
if __name__ == '__main__':
    pass

# endregion [Main_Exec]
