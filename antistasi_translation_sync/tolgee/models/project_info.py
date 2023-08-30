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
from weakref import proxy

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

if TYPE_CHECKING:
    from ..client import TolgeeClient
    from .language import Language
    from ...stringtable import ArmaLanguage

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion [Constants]


@dataclasses.dataclass(frozen=True, slots=True)
class ProjectInfo:
    projectId: int = dataclasses.field()
    languageCount: int = dataclasses.field()
    keyCount: int = dataclasses.field()
    baseWordsCount: int = dataclasses.field()
    translatedPercentage: float = dataclasses.field()
    reviewedPercentage: float = dataclasses.field()
    membersCount: int = dataclasses.field()
    tagCount: int = dataclasses.field()
    projectName: str = dataclasses.field()
    lastUsedAt: datetime = dataclasses.field()

    @property
    def name(self) -> str:
        return self.projectName

    @property
    def project_name(self) -> str:
        return self.projectName

    @property
    def project_id(self) -> int:
        return self.projectId

    @property
    def language_count(self) -> int:
        return self.languageCount

    @property
    def key_count(self) -> int:
        return self.keyCount

    @property
    def base_words_count(self) -> int:
        return self.baseWordsCount

    @property
    def translated_percentage(self) -> float:
        return self.translatedPercentage

    @property
    def translated_percentage_pretty(self) -> float:
        return round(self.translated_percentage, ndigits=2)

    @property
    def reviewed_percentage(self) -> float:
        return self.reviewedPercentage

    @property
    def reviewed_percentage_pretty(self) -> float:
        return round(self.reviewed_percentage, ndigits=2)

    @property
    def members_count(self) -> int:
        return self.membersCount

    @property
    def tag_count(self) -> int:
        return self.tagCount


# region [Main_Exec]


if __name__ == '__main__':
    pass

# endregion [Main_Exec]
