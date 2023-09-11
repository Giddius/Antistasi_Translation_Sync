"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import sys
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING, Union, TypeVar
from pathlib import Path
from itertools import chain

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_translation_sync.errors import DuplicateKeyError

from .key import StringTableKey

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_translation_sync.stringtable.models.entry import StringTableEntry
    from antistasi_translation_sync.stringtable.models.stringtable_obj import StringTable

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion [Constants]


_GET_DEFAULT_TYPE = TypeVar("_GET_DEFAULT_TYPE", object, None)


class StringTableContainer:

    __slots__ = ("name",
                 "string_table",
                 "key_map")

    def __init__(self,
                 name: str) -> None:

        self.name = name
        self.string_table: "StringTable" = None
        self.key_map: dict[str, "StringTableKey"] = {}

    def get_or_create_key(self, key_name: str) -> StringTableKey:
        try:
            return self.key_map[key_name]
        except KeyError:
            key = StringTableKey(id_value=key_name)
            self.add_key(key)
            return key

    def __getitem__(self, name: str) -> StringTableKey:
        return self.key_map[name]

    def get(self, name: str, default: _GET_DEFAULT_TYPE = None) -> Union[StringTableKey, _GET_DEFAULT_TYPE]:
        try:
            return self[name]
        except KeyError:
            return default

    @property
    def keys(self) -> tuple["StringTableKey"]:
        return tuple(self.key_map.values())

    @property
    def entries(self) -> tuple["StringTableEntry"]:
        return tuple(chain(*[i.entries for i in self.keys]))

    @classmethod
    def from_xml_element(cls, element: ET.Element) -> Self:
        name = element.attrib["name"]
        instance = cls(name=name)

        return instance

    def add_key(self, key: "StringTableKey") -> None:
        if key.name in self.key_map:
            raise DuplicateKeyError(key, self, self.string_table)
        key.set_container(self)
        self.key_map[key.name] = key

    def set_string_table(self, string_table: str) -> None:
        self.string_table = string_table

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(name={self.name!r})'

    def _sort_func_for_text(self, key: "StringTableKey"):
        # parts = []
        # for part in key.name.split("_"):
        #     part = part.casefold()
        #     if part == "generic":
        #         part = "aaaaaaa"

        #     parts.append(part)
        parts = tuple(part.casefold() for part in key.name.split("_"))
        return parts

    def as_text(self, indentation: int = 2) -> str:
        indent_value = (" " * indentation) * 2
        text = f'{indent_value}<Container name="{self.name}">\n'
        text += "\n".join(k.as_text(indentation) for k in sorted(self.keys, key=self._sort_func_for_text))
        text += f"\n{indent_value}</Container>"
        return text


# region [Main_Exec]
if __name__ == '__main__':
    pass

# endregion [Main_Exec]
