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
from time import time
from math import floor, ceil
import atexit
from threading import Lock, RLock
from types import TracebackType
if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


from weakref import proxy, WeakValueDictionary
import httpx
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


class RateLimit:
    __slots__ = ("_consume_lock",
                 "_max_request_amount",
                 "_reset_seconds",
                 "_rate_fractions",
                 "_time_provider",
                 "_consume_sleep",
                 "_bucket",
                 "_start_time",
                 "_random_sleep_on_consume",
                 "__weakref__")

    def __init__(self,
                 max_request_amount: int,
                 reset_seconds: float,
                 rate_fractions: int = None,
                 time_provider: Callable[[], float] = None,
                 random_sleep_on_consume: bool = False) -> None:
        self._consume_lock = Lock()
        self._max_request_amount = max_request_amount
        self._reset_seconds = reset_seconds
        self._rate_fractions = rate_fractions or 1

        self._time_provider = time_provider or perf_counter

        self._bucket: int = 0
        self._start_time: float = None
        self._random_sleep_on_consume = random_sleep_on_consume

    def _refill_bucket(self) -> None:
        self._bucket = max(floor((self._max_request_amount - 5) / self._rate_fractions), 1)

        self._start_time = self._time_provider()

    def _get_sleep_time(self) -> float:
        base_sleep_time = (self._reset_seconds / self._rate_fractions) * 1.05
        used_time = self._time_provider() - self._start_time

        sleep_time = max((base_sleep_time - used_time), 0.00001)

        sleep_time = ceil(sleep_time * 1000) / 1000

        return sleep_time

    def _on_empty_bucket(self) -> None:
        if self._start_time is None:
            self._refill_bucket()
            return

        sleep_amount = self._get_sleep_time()
        print(f"sleeping {sleep_amount!r}", flush=True)
        sleep(sleep_amount)
        self._refill_bucket()

    def _random_sleep(self) -> None:
        sleep_amount = (1.0 / (self._rate_fractions / 2)) * random.random()
        sleep(sleep_amount)
        # print(f"slept randomly for {sleep_amount:.4f}", flush=True)

    def consume(self) -> None:
        if self._random_sleep_on_consume is True:
            # sleep(random.random() / 2)
            self._random_sleep()
        with self._consume_lock:
            self._bucket -= 1
            if self._bucket <= 0:
                self._on_empty_bucket()

            return

    def force_sleep(self) -> None:
        with self._consume_lock:
            self._on_empty_bucket()

    def __enter__(self) -> Self:
        self.consume()
        return self

    def __exit__(self,
                 exc_type: Optional[type[BaseException]] = None,
                 exc_value: Optional[BaseException] = None,
                 traceback: Optional[TracebackType] = None) -> None:
        pass


RATE_LIMIT_MANAGER: dict[httpx.URL, RateLimit] = {}


def _sleep_max_sleep_seconds():
    all_sleep_seconds = [rl._get_sleep_time() for rl in RATE_LIMIT_MANAGER.values()]
    if all_sleep_seconds:
        max_sleep_seconds = max(all_sleep_seconds)
        print(f"sleeping for {max_sleep_seconds} on exit")
        sleep(max_sleep_seconds)


atexit.register(_sleep_max_sleep_seconds)


def get_rate_limiter(base_url: httpx.URL) -> "RateLimit":
    try:
        return RATE_LIMIT_MANAGER[base_url]
    except KeyError:
        rate_limit = RateLimit(300, 70.0, rate_fractions=10, random_sleep_on_consume=True)
        RATE_LIMIT_MANAGER[base_url] = rate_limit

        return rate_limit

# region [Main_Exec]


if __name__ == '__main__':
    pass

# endregion [Main_Exec]
