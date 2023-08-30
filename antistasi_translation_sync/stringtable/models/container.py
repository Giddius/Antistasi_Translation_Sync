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
from itertools import chain

import xml.etree.ElementTree as ET
from html import escape as html_escape

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from .key import StringTableKey

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

    def as_text(self) -> str:
        indent_value = (" " * 2) * 2
        text = f'{indent_value}<Container name="{self.name}">\n'
        text += "\n".join(k.as_text() for k in sorted(self.keys, key=self._sort_func_for_text))
        text += f"\n{indent_value}</Container>"
        return text


# region [Main_Exec]
if __name__ == '__main__':
    pass

# endregion [Main_Exec]
