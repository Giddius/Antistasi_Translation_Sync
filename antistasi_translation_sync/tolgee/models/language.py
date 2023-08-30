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
    from .translation_entry import TranslationEntry
# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion [Constants]


@dataclasses.dataclass(frozen=True, slots=True, order=True)
class Language:
    language_id: int = dataclasses.field(compare=True, hash=True)
    name: str = dataclasses.field(compare=False, hash=False)
    tag: str = dataclasses.field(compare=False, hash=False)
    originalName: str = dataclasses.field(compare=False, hash=False, repr=False)
    base: bool = dataclasses.field(compare=False, hash=False)
    flagEmoji: str = dataclasses.field(compare=False, hash=False, repr=False)
    client: Union["TolgeeClient", None] = dataclasses.field(default=None, repr=False, hash=False)

    @property
    def language_name(self) -> str:
        return self.name

    @property
    def original_name(self) -> str:
        return self.originalName

    @property
    def flag_emoji(self) -> str:
        return self.flagEmoji

    @property
    def is_default(self) -> str:
        return self.base

    @classmethod
    def from_response_data(cls,
                           client: "TolgeeClient" = None,
                           **response_data: Unpack[dict[str, object]]) -> Self:

        client = proxy(client) if client is not None else client
        language_id = response_data["id"]
        name = response_data["name"]
        tag = response_data["tag"]
        original_name = response_data["originalName"]
        base = response_data["base"]
        flag_emoji = response_data["flagEmoji"]

        return cls(language_id=language_id, name=name, tag=tag, originalName=original_name, base=base, flagEmoji=flag_emoji, client=client)

    def __str__(self) -> str:
        return self.tag


# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]
