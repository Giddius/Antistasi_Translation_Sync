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
from typing import (TYPE_CHECKING, Unpack, TypeVar, TypeGuard, TypeAlias, Final, TypedDict, Generic, Union, Optional, ForwardRef, final, Callable,
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
from weakref import proxy

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

if TYPE_CHECKING:
    from ..client import TolgeeClient
    from .language import Language
    from .translation_namespace import TranslationNamespace
    from .translation_key import TranslationKey
    from .project import Project
    from ...stringtable.models import StringTableEntry

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion [Constants]


class EntryState(Enum):
    TRANSLATED = auto()
    UNTRANSLATED = auto()
    REVIEWED = auto()

    @classmethod
    def _missing_(cls, value: object) -> Any:
        if isinstance(value, str):
            mod_value = value.casefold()
            for name, instance in cls._member_map_.items():
                if name.casefold() == mod_value:
                    return instance
        return super()._missing_(value)


class MachineTranslationProvider(Enum):
    NONE = auto()
    GOOGLE = auto()
    AWS = auto()
    DEEPL = auto()
    AZURE = auto()
    BAIDU = auto()
    TOLGEE = auto()

    @classmethod
    def _missing_(cls, value: object) -> Any:
        if value is None:
            return cls.NONE
        if isinstance(value, str):
            mod_value = value.casefold()
            for name, instance in cls._member_map_.items():
                if name.casefold() == mod_value:
                    return instance
        return super()._missing_(value)


class TranslationEntry:
    __slots__ = ("_entry_id",
                 "_key",
                 "_language",
                 "_text",
                 "_state",
                 "_outdated",
                 "_auto",
                 "_mtProvider",
                 "_commentCount",
                 "_unresolvedCommentCount",
                 "_fromTranslationMemory",
                 "_client",
                 "_comments")

    def __init__(self,
                 entry_id: int,
                 key: "TranslationKey",
                 language: "Language",
                 text: str,
                 state: Union[str, EntryState],
                 outdated: bool,
                 auto: bool,
                 mtProvider: Union[str, MachineTranslationProvider],
                 commentCount: Optional[int],
                 unresolvedCommentCount: Optional[int],
                 fromTranslationMemory: bool,
                 client: Union["TolgeeClient", None] = None) -> None:
        self._entry_id: int = entry_id
        self._key: "TranslationKey" = key
        self._language: "Language" = language
        self._text: str = text
        self._state: EntryState = EntryState(state)
        self._outdated: bool = outdated
        self._auto: bool = auto
        self._mtProvider: MachineTranslationProvider = MachineTranslationProvider(mtProvider)
        self._commentCount: Optional[int] = commentCount
        self._unresolvedCommentCount: Optional[int] = unresolvedCommentCount
        self._fromTranslationMemory: bool = fromTranslationMemory
        self._client: Union["TolgeeClient", None] = client

        self._comments: tuple[str] = None

    @property
    def comments(self) -> tuple[str]:
        if self._comments is None:
            if self.comment_count <= 0:
                self._comments = tuple()
            else:
                comments = []

                params = {"size": 250}
                response = self.client.client.get(f"/translations/{self.entry_id}/comments", params=params)

                data = response.json()["_embedded"]

                for comment_data in data["translationComments"]:
                    comments.append(comment_data["text"])

                self._comments = tuple(comments)

        return self._comments

    @property
    def entry_id(self) -> int:
        return self._entry_id

    @property
    def key(self) -> "TranslationKey":
        return self._key

    @property
    def namespace(self) -> "TranslationNamespace":
        return self._key.namespace

    @property
    def project(self) -> "Project":
        return self.namespace.project

    @property
    def language(self) -> "Language":
        return self._language

    @property
    def text(self) -> str:
        return self._text

    @property
    def state(self) -> EntryState:
        return self._state

    @property
    def outdated(self) -> bool:
        return self._outdated

    @property
    def auto(self) -> bool:
        return self._auto

    @property
    def mtProvider(self) -> MachineTranslationProvider:
        return self._mtProvider

    @property
    def commentCount(self) -> Optional[int]:
        return self._commentCount

    @property
    def unresolvedCommentCount(self) -> Optional[int]:
        return self._unresolvedCommentCount

    @property
    def fromTranslationMemory(self) -> bool:
        return self._fromTranslationMemory

    @property
    def client(self) -> Union["TolgeeClient", None]:
        return self._client

    @property
    def is_deleted(self) -> bool:
        return self._key.is_deleted

    @property
    def mt_provider(self) -> MachineTranslationProvider:
        return self._mtProvider

    @property
    def comment_count(self) -> int:
        return self._commentCount

    @property
    def unresolved_comment_count(self) -> int:
        return self._unresolvedCommentCount

    @property
    def is_from_translation_memory(self) -> bool:
        return self._fromTranslationMemory

    def update_from_stringtable_entry(self, stringtable_entry: "StringTableEntry") -> bool:
        if stringtable_entry.text == self.text:
            return False

        request_data = {"key": self.key.name,
                        "namespace": self.namespace.name,
                        "translations": {self.language.tag: stringtable_entry.text}}

        response = self.client.client.post("/translations", json=request_data)

        return True


# region [Main_Exec]
if __name__ == '__main__':
    pass

# endregion [Main_Exec]
