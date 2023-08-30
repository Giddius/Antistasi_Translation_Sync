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
from .language import ArmaLanguage
if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

if TYPE_CHECKING:
    from antistasi_translation_sync.stringtable.models.key import StringTableKey
    from antistasi_translation_sync.stringtable.models.container import StringTableContainer

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion [Constants]


class StringTableEntry:

    def __init__(self,
                 language: "ArmaLanguage",
                 text: str) -> None:
        self.language = language
        self.text = text
        self.key: "StringTableKey" = None

    @classmethod
    def from_xml_element(cls, element: ET.Element) -> Self:
        raw_language = element.tag
        raw_text = element.text
        instance = cls(language=ArmaLanguage(raw_language), text=raw_text)

        return instance

    def set_key(self, key: "StringTableKey") -> None:
        self.key = key

    @property
    def is_original(self) -> bool:
        return ArmaLanguage(self.language) is ArmaLanguage.ORIGINAL

    @property
    def html_escaped_text(self) -> str:
        return html_escape(self.text, False)

    @property
    def key_name(self) -> str:
        return self.key.name

    @property
    def container_name(self) -> str:
        return self.key.container.name

    def as_text(self) -> str:
        indent_value = (" " * 2) * 4

        language_text = self.language.name.title()
        return f"{indent_value}<{language_text}>{self.html_escaped_text}</{language_text}>"

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(language={self.language!r}, text={self.text!r})'


# region [Main_Exec]
if __name__ == '__main__':
    pass

# endregion [Main_Exec]
