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

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from .language import Language
from .tag import Tag
from .project_info import ProjectInfo

from .translation_namespace import TranslationNamespace
from .translation_key import TranslationKey
from .translation_entry import TranslationEntry
if TYPE_CHECKING:
    from ..client import TolgeeClient
    from ...stringtable.models import ArmaLanguage, LanguageLike


# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion [Constants]
_GET_DEFAULT_TYPE = TypeVar("_GET_DEFAULT_TYPE")


class NamespaceContainer:

    def __init__(self) -> None:
        self._namespaces: list["TranslationNamespace"] = []
        self._name_map: dict[str, "TranslationNamespace"] = {}
        self._id_map: dict[int, "TranslationNamespace"] = {}

    def __getitem__(self, key: Union[str, int]) -> "TranslationNamespace":
        try:

            if isinstance(key, int):
                return self._id_map[key]
            elif isinstance(key, str):
                return self._name_map[key]

        except KeyError:
            pass

        raise KeyError(f"No Namespace found for key {key!r} in {self!r}.")

    def add(self, namespace: "TranslationNamespace") -> None:
        self._namespaces.append(namespace)
        self._id_map[namespace.namespace_id] = namespace
        self._name_map[namespace.name] = namespace

    def get(self, key: Union[str, int], default: _GET_DEFAULT_TYPE = None) -> Union["TranslationNamespace", _GET_DEFAULT_TYPE]:
        try:
            return self[key]
        except KeyError:
            return default


class Project:
    __slots__ = ("client",
                 "project_info",
                 "tags",
                 "namespace_container",
                 "language_map",
                 "default_language")

    def __init__(self,
                 client: "TolgeeClient") -> None:
        self.client = client
        self.project_info: "ProjectInfo" = None
        self.tags: set["Tag"] = set()
        self.namespace_container: NamespaceContainer = NamespaceContainer()
        self.language_map: dict[str, "Language"] = {}
        self.default_language: "Language" = None

    @property
    def name(self) -> str:
        return self.project_info.projectName

    @property
    def project_id(self) -> int:
        return self.project_info.project_id

    @property
    def languages(self) -> tuple["Language"]:
        return tuple(self.language_map.values())

    @property
    def namespaces(self) -> list["TranslationNamespace"]:
        return self.namespace_container._namespaces.copy()

    @property
    def keys(self) -> list["TranslationKey"]:
        return list(chain(*[list(n._key_map.values()) for n in self.namespaces]))

    @property
    def entries(self) -> list["TranslationEntry"]:
        return list(chain(*[list(k._entry_map.values()) for k in self.keys]))

    def setup(self) -> Self:

        self.project_info = self.client._get_project_info()

        self.language_map = {l.language_name.casefold(): l for l in self.client.get_available_languages()}
        self.default_language = next(l for l in self.languages if l.is_default)
        self.tags = frozenset(self.client.get_all_tags())

        self.client._build_project_tree(self)

        return self

    def refresh(self) -> Self:
        self.namespace_container = NamespaceContainer()
        return self.setup()

    def language_from_arma_language(self, arma_language: "LanguageLike") -> "Language":
        try:
            return self.get_language_by_name(arma_language.language_name)
        except KeyError:
            return self.get_language_by_name(arma_language.name)

    def get_language_by_name(self, name: str) -> "Language":
        mod_name = name.casefold()
        language = self.language_map.get(mod_name, None)
        if language is None:
            raise KeyError(f"{self!r} has no Language with the name {name!r}.")

        return language

    def get_language_by_tag(self, tag: str) -> "Language":
        mod_tag = tag.casefold()
        language = next((l for l in self.languages if l.tag.casefold() == mod_tag), None)
        if language is None:

            raise KeyError(f"{self!r} has no Language with the tag {tag!r}.")

        return language

    def add_namespace(self, namespace: "TranslationNamespace"):
        self.namespace_container.add(namespace)

    def __getitem__(self, key: Union[str, int]) -> "TranslationNamespace":
        return self.namespace_container[key]

    def get_or_create_namespace(self, namespace_id: int, name: str) -> "TranslationNamespace":
        try:
            return self[namespace_id]
        except KeyError:
            namespace = TranslationNamespace(namespace_id=namespace_id, name=name, project=self, client=self.client)
            self.add_namespace(namespace=namespace)
            return namespace

    # def get_or_create_key(self, key_id: int, name: str, namespace: "TranslationNamespace", tags: Iterable["Tag"]) -> "TranslationKey":
    #     try:
    #         return namespace[name]
    #     except KeyError:
    #         key = TranslationKey(key_id=key_id, name=name, namespace=namespace, tags=tags, client=self.client)
    #         namespace.add_key(key)
    #         return key

    def __repr__(self) -> str:

        return f'{self.__class__.__name__}(project_id={self.project_id!r}, name={self.name!r})'


# region [Main_Exec]
if __name__ == '__main__':
    pass

# endregion [Main_Exec]
