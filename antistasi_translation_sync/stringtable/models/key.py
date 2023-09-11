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

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from .language import ArmaLanguage, LanguageLike
from .entry import StringTableEntry
from antistasi_translation_sync.errors import UnremoveableEntryError, DuplicateEntryError
if TYPE_CHECKING:
    from antistasi_translation_sync.stringtable.models.container import StringTableContainer
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


class StringTableKey:

    __slots__ = ("container",
                 "id_value",
                 "entry_map")

    def __init__(self,
                 id_value: str) -> None:
        self.container: "StringTableContainer" = None
        self.id_value = id_value
        self.entry_map: dict["ArmaLanguage", "StringTableEntry"] = {}

    def set_text_for_language(self, language: Union["LanguageLike", str], text: str) -> None:
        language = ArmaLanguage(language)
        try:
            entry = self.entry_map[language]
            entry.text = text
        except KeyError:
            entry = StringTableEntry(language=language, text=text)
            self.add_entry(entry)

    def remove_entry_for_language(self, language: Union["LanguageLike", str]) -> None:
        entry = self.get(language=language)
        if entry is not None:
            self.remove_entry(entry)

    def remove_all_not_original_entries(self) -> None:
        self.entry_map = {k: v for k, v in self.entry_map.items() if v.language is ArmaLanguage.ORIGINAL}

    def __getitem__(self, language: "LanguageLike") -> StringTableEntry:
        return self.entry_map[ArmaLanguage(language)]

    def get(self, language: "LanguageLike", default: _GET_DEFAULT_TYPE = None) -> Union[StringTableEntry, _GET_DEFAULT_TYPE]:
        try:
            return self[language]
        except KeyError:
            return default

    @property
    def original_entry(self) -> Union[StringTableEntry, None]:
        _out = self.get(ArmaLanguage.ORIGINAL, default=None)
        if _out is None:
            print(f"{self!r}  {self.entries!r}  {self.entry_map!r}")
        return _out

    @property
    def original_text(self) -> Union[str, None]:
        entry = self.original_entry
        if entry is not None:
            return entry.text

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
    def from_xml_element(cls, element: ET.Element) -> Self:
        id_value = element.attrib["ID"]
        instance = cls(id_value=id_value)

        return instance

    def set_container(self, container: "StringTableContainer") -> None:
        self.container = container

    def add_entry(self, entry: "StringTableEntry") -> None:
        if entry.language in self.entry_map:
            raise DuplicateEntryError(entry, self, self.container, self.container.string_table)
        entry.set_key(self)
        self.entry_map[entry.language] = entry

    def remove_entry(self, entry: "StringTableEntry") -> None:
        if entry.language is ArmaLanguage.ORIGINAL:
            raise UnremoveableEntryError(f"Entry for Language {entry.language!r} cannot be removed.")
        del self.entry_map[entry.language]

    def _sort_func_for_text(self, entry: "StringTableEntry"):
        if entry.language is ArmaLanguage.ORIGINAL:
            return 0
        return list(ArmaLanguage).index(entry.language)

    def as_text(self, indentation: int = 2) -> str:
        indent_value = (" " * indentation) * 3
        text = f'{indent_value}<Key ID="{self.name}">\n'
        text += '\n'.join(i.as_text(indentation) for i in sorted(self.entries, key=self._sort_func_for_text))
        text += f"\n{indent_value}</Key>"
        return text

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(name={self.name!r})'


# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]
