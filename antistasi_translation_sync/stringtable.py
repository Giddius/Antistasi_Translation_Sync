"""
WiP.

Soon.
"""

# region [Imports]

import os
import re
import sys
import json
import queue
import math
import base64
import pickle
import random
import shelve
import dataclasses
import shutil
import asyncio
import logging
import sqlite3
import platform

import subprocess
import inspect

from time import sleep, process_time, process_time_ns, perf_counter, perf_counter_ns
from io import BytesIO, StringIO
from abc import ABC, ABCMeta, abstractmethod
from copy import copy, deepcopy
from enum import Enum, Flag, auto, unique
from pprint import pprint, pformat
from pathlib import Path
from string import Formatter, digits, printable, whitespace, punctuation, ascii_letters, ascii_lowercase, ascii_uppercase
from timeit import Timer
from typing import (TYPE_CHECKING, TypeVar, TypeGuard, TypeAlias, Final, TypedDict, Generic, Union, Optional, ForwardRef, final, Callable,
                    no_type_check, no_type_check_decorator, overload, get_type_hints, cast, Protocol, runtime_checkable, NoReturn, NewType, Literal, AnyStr, IO, BinaryIO, TextIO, Any)
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from collections.abc import (AsyncGenerator, AsyncIterable, AsyncIterator, Awaitable, ByteString, Callable, Collection, Container, Coroutine, Generator,
                             Hashable, ItemsView, Iterable, Iterator, KeysView, Mapping, MappingView, MutableMapping, MutableSequence, MutableSet, Reversible, Sequence, Set, Sized, ValuesView)
from zipfile import ZipFile, ZIP_LZMA
from datetime import datetime, timezone, timedelta
from tempfile import TemporaryDirectory
from textwrap import TextWrapper, fill, wrap, dedent, indent, shorten
from functools import wraps, partial, lru_cache, singledispatch, total_ordering, cached_property, cache
from contextlib import contextmanager, asynccontextmanager, nullcontext, closing, ExitStack, suppress
from statistics import mean, mode, stdev, median, variance, pvariance, harmonic_mean, median_grouped
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Future, wait, as_completed, ALL_COMPLETED, FIRST_EXCEPTION, FIRST_COMPLETED
import xml.etree.ElementTree as ET
from html import escape as html_escape
from itertools import chain
import pp
if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

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

STRINGTABlE_TEXT_TEMPLATE: str = """

<?xml version="1.0" encoding="utf-8"?>
<Project name="A3-Antistasi">
  <Package name="A3-Antistasi Mission">
{content}
  </Package>
</Project>

""".strip()


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

    @property
    def language_name(self) -> str:
        return self.value

    @classmethod
    def _missing_(cls, value: object) -> Any:
        if isinstance(value, str):
            mod_value = value.casefold()
            if mod_value == "english":
                return cls.ORIGINAL

            for member in cls._member_map_.values():
                if member.name.casefold() == mod_value or member.value.casefold() == mod_value:
                    return member
        return super()._missing_(value)


class StringTableEntry:

    def __init__(self,
                 language: ArmaLanguage,
                 text: str) -> None:
        self.language = language
        self.text = text
        self.key: "StringTableKey" = None

    @classmethod
    def from_xml_element(cls, element: ET.Element, key: "StringTableKey" = None) -> Self:
        raw_language = element.tag
        raw_text = element.text
        instance = cls(language=ArmaLanguage(raw_language), text=raw_text)
        if key is not None:
            key.add_entry(instance)

        return instance

    def set_key(self, key: "StringTableKey") -> None:
        self.key = key

    @property
    def key_name(self) -> str:
        return self.key.name

    @property
    def container_name(self) -> str:
        return self.key.container.name

    def as_text(self) -> str:
        indent_value = (" " * 2) * 4
        if self.language is ArmaLanguage.ORIGINAL:
            language_text = "Original"
        elif self.language is ArmaLanguage.CHINESESIMP:
            language_text = "Chinesesimp"
        else:
            language_text = self.language.name.title()
        return f"{indent_value}<{language_text}>{html_escape(self.text, False)}</{language_text}>"

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(language={self.language!r}, text={self.text!r})'


class StringTableKey:

    def __init__(self,
                 id_value: str) -> None:
        self.container: "StringTableContainer" = None
        self.id_value = id_value
        self.entry_map: dict[ArmaLanguage, "StringTableEntry"] = {}

    @property
    def entries(self) -> tuple["StringTableEntry"]:
        return tuple(self.entry_map.values())

    @property
    def name(self) -> str:
        return self.id_value

    @property
    def container_name(self) -> str:
        return self.container.name

    @classmethod
    def from_xml_element(cls, element: ET.Element, container: "StringTableContainer" = None) -> Self:
        id_value = element.attrib["ID"]
        instance = cls(id_value=id_value)
        if container is not None:
            container.add_key(instance)
        return instance

    def set_container(self, container: "StringTableContainer") -> None:
        self.container = container

    def add_entry(self, entry: "StringTableEntry") -> None:
        entry.set_key(self)
        self.entry_map[entry.language] = entry

    def remove_entry(self, entry: "StringTableEntry") -> None:
        del self.entry_map[entry.language]

    def _sort_func_for_text(self, entry: StringTableEntry):
        if entry.language is ArmaLanguage.ORIGINAL:
            return 0
        return list(ArmaLanguage).index(entry.language)

    def as_text(self) -> str:
        indent_value = (" " * 2) * 3
        text = f'{indent_value}<Key ID="{self.name}">\n'
        text += '\n'.join(i.as_text() for i in sorted(self.entries, key=self._sort_func_for_text))
        text += f"\n{indent_value}</Key>"
        return text

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(name={self.name!r})'


class StringTableContainer:

    def __init__(self,
                 name: str) -> None:

        self.name = name
        self.string_table: "StringTable" = None
        self.key_map: dict[str, "StringTableKey"] = {}

    @property
    def keys(self) -> tuple["StringTableKey"]:
        return tuple(self.key_map.values())

    @property
    def entries(self) -> tuple["StringTableEntry"]:
        return tuple(chain(*[i.entries for i in self.keys]))

    @classmethod
    def from_xml_element(cls, element: ET.Element, string_table: "StringTable" = None) -> Self:
        name = element.attrib["name"]
        instance = cls(name=name)
        if string_table is not None:
            string_table.add_container(instance)

        return instance

    def add_key(self, key: "StringTableKey") -> None:
        key.set_container(self)
        self.key_map[key.id_value] = key

    def set_string_table(self, string_table: str) -> None:
        self.string_table = string_table

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(name={self.name!r})'

    def _sort_func_for_text(self, key: StringTableKey):
        return key.name.casefold()

    def as_text(self) -> str:
        indent_value = (" " * 2) * 2
        text = f'{indent_value}<Container name="{self.name}">\n'
        text += "\n".join(k.as_text() for k in sorted(self.keys, key=self._sort_func_for_text))
        text += f"\n{indent_value}</Container>"
        return text


class StringTable:
    _text_template: str = STRINGTABlE_TEXT_TEMPLATE

    def __init__(self,
                 file_path: Path,
                 project_name: str = None) -> None:

        self.file_path = file_path.resolve()
        self.project_name = project_name or self.file_path.parent.name
        self.container_map: dict[str, "StringTableContainer"] = {}

    @property
    def containers(self) -> tuple[StringTableContainer]:
        return tuple(self.container_map.values())

    def all_entries(self) -> tuple[StringTableEntry]:
        return tuple(chain(*[c.entries for c in self.containers]))

    def all_keys(self) -> tuple[StringTableKey]:
        return tuple(chain(*[c.keys for c in self.containers]))

    def add_container(self, container: "StringTableContainer") -> None:
        container.set_string_table(self)
        self.container_map[container.name] = container

    def get_key(self, name: str) -> StringTableKey:
        return ChainMap(*[c.key_map for c in self.containers])[name]

    def get_entry(self, key_name: str, language: Union[ArmaLanguage, str]) -> StringTableEntry:
        key = self.get_key(key_name)
        return key.entry_map[ArmaLanguage(language)]

    def parse(self) -> Self:
        entries = []
        root = ET.fromstring(self.file_path.read_bytes())

        for _container in root.iter("Container"):
            container_item = StringTableContainer.from_xml_element(_container, string_table=self)

            for _key in _container.iter("Key"):
                key_item = StringTableKey.from_xml_element(_key, container=container_item)

                for i in _key.iter():
                    if i.tag == "Key":
                        continue

                    entry_item = StringTableEntry.from_xml_element(i, key=key_item)

                    entries.append(entry_item)

        return self

    def _sort_func_for_text(self, container: StringTableContainer):
        return container.name.casefold()

    def as_text(self) -> str:

        content = "\n".join(c.as_text() for c in sorted(self.containers, key=self._sort_func_for_text))
        text = self._text_template.format(content=content)
        return text
# region [Main_Exec]


if __name__ == '__main__':
    check_file_1 = Path(r"D:\Dropbox\hobby\Modding\Programs\Github\Foreign_Repos\A3-Antistasi\A3A\addons\garage\Stringtable.xml")
    check_file_2 = Path(r"D:\Dropbox\hobby\Modding\Programs\Github\Foreign_Repos\A3-Antistasi\A3A\addons\core\Stringtable.xml")
    check_file_3 = Path(r"D:\Dropbox\hobby\Modding\Programs\Github\Foreign_Repos\A3-Antistasi\A3A\addons\events\Stringtable.xml")
    print(f"")
    # for file in (check_file_1, check_file_2, check_file_3):
    for file in [THIS_FILE_DIR.joinpath("Stringtable_example.xml")]:
        print(f"{file.as_posix()=}")
        x = StringTable(file)
        x.parse()
        outfile = THIS_FILE_DIR.joinpath(file.with_stem(f"{file.stem}_{file.parent.name}").name)
        print(f"{outfile.as_posix()=}")
        # with outfile.open("w", encoding='utf-8', errors='ignore') as f:
        #     f.write(x.as_text())

        print(x.get_entry(key_name="STR_A3A_EXAMPLE_KEY", language="RusSian"))


# endregion [Main_Exec]
