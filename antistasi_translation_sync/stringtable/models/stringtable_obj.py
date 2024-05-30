"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import sys
from copy import deepcopy
from typing import TYPE_CHECKING, Union, TypeVar
from pathlib import Path
from itertools import chain
from collections import ChainMap
from collections.abc import Generator

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_translation_sync.errors import DuplicateContainerError

from .language import ArmaLanguage, LanguageLike
from .container import StringTableContainer

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from . import StringTableKey, StringTableEntry

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion [Constants]


_GET_DEFAULT_TYPE = TypeVar("_GET_DEFAULT_TYPE", object, None)


class StringTable:

    __slots__ = ("project_name",
                 "package_name",
                 "header",
                 "container_map")

    def __init__(self) -> None:
        self.project_name: Union[str, None] = None
        self.package_name: Union[str, None] = None
        self.header: Union[str, None] = None
        self.container_map: dict[str, "StringTableContainer"] = {}

    @property
    def name(self) -> Union[str, None]:
        if self.package_name is None:
            return

        return self.package_name.strip().split(" ")[-1]

    def get_or_create_container(self, container_name: str) -> StringTableContainer:
        try:
            return self.container_map[container_name]
        except KeyError:
            container = StringTableContainer(name=container_name)
            self.add_container(container=container)
            return container

    def __getitem__(self, name: str) -> "StringTableContainer":
        return self.container_map[name]

    def get(self, name: str, default: _GET_DEFAULT_TYPE = None) -> Union["StringTableContainer", _GET_DEFAULT_TYPE]:
        try:
            return self[name]

        except KeyError:
            return default

    @property
    def containers(self) -> tuple["StringTableContainer"]:
        return tuple(self.iter_containers())

    def iter_containers(self) -> Generator["StringTableContainer", None, None]:
        yield from (c for c in self.container_map.values())

    def iter_keys(self) -> Generator["StringTableKey", None, None]:
        yield from chain(*[c.keys for c in self.containers])

    def iter_entries(self) -> Generator["StringTableEntry", None, None]:
        yield from (entry for entry in chain(*[c.entries for c in self.containers]))

    def iter_all_original_language_entries(self) -> Generator["StringTableEntry", None, None]:
        yield from (entry for entry in self.iter_entries() if entry.language is ArmaLanguage.ORIGINAL)

    def iter_all(self) -> Generator[Union["StringTableContainer", "StringTableKey", "StringTableEntry"], None, None]:
        for container in self.iter_containers():
            yield container
            for key in container.keys:
                yield key
                for entry in key.entries:
                    yield entry

    def get_all_entries(self) -> tuple["StringTableEntry"]:
        return tuple(self.iter_entries())

    def get_all_keys(self) -> tuple["StringTableKey"]:
        return tuple(self.iter_keys())

    def add_container(self, container: "StringTableContainer") -> None:
        if container.name in self.container_map:
            # raise DuplicateContainerError(container, self)
            return
        container.set_string_table(self)
        self.container_map[container.name] = container

    def get_key(self, name: str) -> "StringTableKey":
        return ChainMap(*[c.key_map for c in self.containers])[name]

    def get_entry(self, key_name: str, language: Union["LanguageLike", str]) -> "StringTableEntry":
        key = self.get_key(key_name)
        return key.entry_map[ArmaLanguage(language)]

    def _sort_func_for_text(self, container: StringTableContainer):
        return container.name.casefold()

    def __copy__(self) -> Self:
        cls = self.__class__
        result = cls.__new__(cls)
        for attr_name in self.__class__.__slots__:
            setattr(result, getattr(self, attr_name))
        return result

    def copy(self) -> Self:
        return self.__copy__()

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for attr_name in self.__class__.__slots__:
            setattr(result, attr_name, deepcopy(getattr(self, attr_name), memo))
        return result

    def deepcopy(self) -> Self:
        return deepcopy(self)

    def as_text(self, indentation: int = 2) -> str:
        text = ""
        if self.header is not None:
            text += self.header + "\n"
        text_parts = [c.as_text(indentation) for c in sorted(self.containers, key=self._sort_func_for_text)]
        if self.package_name is not None:
            text_parts.insert(0, (" " * indentation) + f'<Package name="{self.package_name}">')
            text_parts.append((" " * indentation) + "</Package>")
        if self.project_name is not None:
            text_parts.insert(0, f'<Project name="{self.project_name}">')
            text_parts.append("</Project>")
        return text + '\n'.join(text_parts)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(project_name={self.project_name!r}, package_name={self.package_name!r})'

# region [Main_Exec]


if __name__ == '__main__':
    pass

# endregion [Main_Exec]
