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
from .translation_key import TranslationKey
if TYPE_CHECKING:
    from ..client import TolgeeClient
    from .project import Project


# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion [Constants]


class TranslationNamespace:

    __slots__ = ("_namespace_id",
                 "_name",
                 "_project",
                 "_client",
                 "_key_map")

    def __init__(self,
                 namespace_id: int,
                 name: str,
                 project: "Project",
                 client: "TolgeeClient") -> None:
        self._namespace_id: int = namespace_id
        self._name: str = name
        self._project = project
        self._client: Union["TolgeeClient", None] = client
        self._key_map: dict[str, "TranslationKey"] = {}

    @property
    def namespace_id(self) -> int:
        return self._namespace_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def project(self) -> "Project":
        return self._project

    @classmethod
    def from_response_data(cls, client: "TolgeeClient" = None, **response_data: Unpack[dict[str, object]]) -> Self:
        client = proxy(client) if client is not None else client
        return cls(namespace_id=response_data["id"], name=response_data["name"], client=client)

    def add_key(self, key: "TranslationKey") -> None:
        if key.name in self._key_map:
            raise RuntimeError(f"key {key.name!r} already is in {self!r}.")
        self._key_map[key.name] = key

    def remove_key(self, key: Union[str, "TranslationKey"]) -> None:
        if isinstance(key, str):
            del self._key_map[key]

        else:
            del self._key_map[key.name]

    def __getitem__(self, name: str) -> "TranslationKey":
        return self._key_map[name]

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.namespace_id == other.namespace_id and self.name == other.name

        return NotImplemented

    def __hash__(self) -> int:
        return self.namespace_id

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(namespace_id={self.namespace_id!r}, name={self.name!r})"
# region [Main_Exec]


if __name__ == '__main__':
    pass

# endregion [Main_Exec]
