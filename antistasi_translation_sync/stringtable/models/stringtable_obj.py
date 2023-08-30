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

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


from .language import ArmaLanguage, LanguageLike
from .container import StringTableContainer
if TYPE_CHECKING:
    from . import StringTableEntry, StringTableKey

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
        result.__dict__.update(self.__dict__)

        return result

    def copy(self) -> Self:
        return self.__copy__()

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        return result

    def deepcopy(self) -> Self:
        return deepcopy(self)

    def as_text(self) -> str:
        text = ""
        if self.header is not None:
            text += self.header + "\n"
        text_parts = [c.as_text() for c in sorted(self.containers, key=self._sort_func_for_text)]
        if self.package_name is not None:
            text_parts.insert(0, (" " * 2) + f'<Package name="{self.package_name}">')
            text_parts.append((" " * 2) + "</Package>")
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
