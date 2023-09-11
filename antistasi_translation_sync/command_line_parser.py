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

import argparse

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

if TYPE_CHECKING:
    from .configuration import Config
    from argparse import _FormatterClass
# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion [Constants]


def _resolve_target_type(in_data) -> Union[Path, Callable]:
    if in_data.upper() == "AUTO_ALL":
        return in_data.upper()

    return Path(in_data)


class CommandLineParser(argparse.ArgumentParser):

    def __init__(self,
                 prog: str = None,
                 usage: str = None,
                 description: str = None,
                 epilog: str = None,
                 parents: Sequence[argparse.ArgumentParser] = None,
                 formatter_class: "argparse._FormatterClass" = argparse.HelpFormatter,
                 prefix_chars: str = '-',
                 fromfile_prefix_chars: str = None,
                 argument_default: Any = None,
                 conflict_handler: str = 'error',
                 add_help: bool = True,
                 allow_abbrev: bool = True,
                 exit_on_error: bool = True,
                 version: Union[str, None] = None) -> None:

        super().__init__(prog=prog,
                         usage=usage,
                         description=description,
                         epilog=epilog,
                         parents=parents or [],
                         formatter_class=formatter_class,
                         prefix_chars=prefix_chars,
                         fromfile_prefix_chars=fromfile_prefix_chars,
                         argument_default=argument_default,
                         conflict_handler=conflict_handler,
                         add_help=add_help,
                         allow_abbrev=allow_abbrev,
                         exit_on_error=exit_on_error)

        self.version = version

    def add_meta_actions(self) -> None:
        if self.version is not None:
            self.add_argument("-v", "--version", action=argparse._VersionAction, version=self.version)

    def parse_args(self, args: list[str] = None, config: "Config" = None) -> "Config":
        return super().parse_args(args=args, namespace=config).resolve_targets()

    def parse_known_args(self, args: list[str] = None, config: "Config" = None) -> "Config":
        return super().parse_known_args(args=args, namespace=config)


def get_command_line_parser(**kwargs) -> CommandLineParser:
    parser = CommandLineParser(**kwargs)
    parser.add_meta_actions()
    parser.add_argument("--working-dir", "-wd", type=Path, dest="working_dir", metavar="", default=argparse.SUPPRESS)
    parser.add_argument("--base-url", "-u", type=str, dest="tolgee_config.base_url", metavar="", required=True)
    parser.add_argument("targets", type=_resolve_target_type, nargs="+")

    parser.add_argument("--token-suffix", "-t", type=str, dest="tolgee_config.api_project_token_suffix", metavar="", required=False, default=argparse.SUPPRESS)
    parser.add_argument("--indentation", "-i", type=int, dest="stringtable_config.indentation", metavar="", default=argparse.SUPPRESS)

    return parser


# region [Main_Exec]
if __name__ == '__main__':
    pass

# endregion [Main_Exec]
