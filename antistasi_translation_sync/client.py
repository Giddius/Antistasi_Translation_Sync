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
from math import ceil, floor
from time import sleep, process_time, process_time_ns, perf_counter, perf_counter_ns, monotonic, time, thread_time
from io import BytesIO, StringIO
from abc import ABC, ABCMeta, abstractmethod
from copy import copy, deepcopy
from enum import Enum, Flag, auto, unique
from pprint import pprint, pformat
from pathlib import Path
from string import Formatter, digits, printable, whitespace, punctuation, ascii_letters, ascii_lowercase, ascii_uppercase
from timeit import Timer
from typing import (TYPE_CHECKING, NamedTuple, TypeVar, Unpack, TypeGuard, TypeAlias, Final, TypedDict, Generic, Union, Optional, ForwardRef, final, Callable,
                    no_type_check, no_type_check_decorator, overload, get_type_hints, cast, Protocol, runtime_checkable, NoReturn, NewType, Literal, AnyStr, IO, BinaryIO, TextIO, Any)
from collections import Counter, ChainMap, deque, defaultdict
from collections.abc import (AsyncGenerator, MappingView, AsyncIterable, AsyncIterator, Awaitable, ByteString, Callable, Collection, Container, Coroutine, Generator,
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
from types import TracebackType, MappingProxyType
from weakref import ref, proxy, ProxyType, ProxyTypes
import httpx
from threading import Lock, RLock, Thread
from concurrent.futures import Future, wait, ALL_COMPLETED, as_completed, ThreadPoolExecutor
import dataclasses
if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

if TYPE_CHECKING:
    ...


from antistasi_translation_sync.stringtable import StringTableEntry, StringTableContainer, StringTableKey, StringTable, ArmaLanguage
from antistasi_translation_sync.retrier import Retrier, unchanged_timeout, exponential_timeout, increasing_timeout, ResponsePaginator
import pp
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
    originalName: str = dataclasses.field(compare=False, hash=False)
    base: bool = dataclasses.field(compare=False, hash=False)
    flagEmoji: str = dataclasses.field(compare=False, hash=False)
    client: Union["TolgeeClient", None] = dataclasses.field(default=None, repr=False, hash=False)

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

    @property
    def translations(self) -> "TranslationEntry":
        return self.client.get_translations_for_language(self)

    def __str__(self) -> str:
        return self.tag


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

    languages: tuple[Language] = dataclasses.field()
    default_language: Language = dataclasses.field()

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
    def reviewed_percentage(self) -> float:
        return self.reviewedPercentage

    @property
    def members_count(self) -> int:
        return self.membersCount

    @property
    def tag_count(self) -> int:
        return self.tagCount

    def language_from_arma_language(self, arma_language: "ArmaLanguage") -> "Language":
        try:
            return self.get_language_by_name(arma_language.language_name)
        except KeyError:
            return self.get_language_by_name(arma_language.name)

    def get_language_by_name(self, name: str) -> "Language":
        mod_name = name.casefold()
        language = next((l for l in self.languages if l.name.casefold() == mod_name), None)
        if language is None:
            raise KeyError(f"{self!r} has no Language with the name {name!r}.")

        return language

    def get_language_by_tag(self, tag: str) -> "Language":
        mod_tag = tag.casefold()
        language = next((l for l in self.languages if l.tag.casefold() == mod_tag), None)
        if language is None:
            raise KeyError(f"{self!r} has no Language with the tag {tag!r}.")

        return language


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


@dataclasses.dataclass(frozen=True, slots=True)
class TranslationEntry:

    translation_id: int = dataclasses.field()
    name_space: str = dataclasses.field()
    key_name: str = dataclasses.field()
    language: Language = dataclasses.field()
    text: str = dataclasses.field()
    state: EntryState = dataclasses.field()
    outdated: bool = dataclasses.field()
    auto: bool = dataclasses.field()
    mtProvider: MachineTranslationProvider = dataclasses.field()
    commentCount: Optional[int] = dataclasses.field(default=None)
    unresolvedCommentCount: Optional[int] = dataclasses.field(default=None)
    fromTranslationMemory: bool = dataclasses.field(default=False)
    client: Union["TolgeeClient", None] = dataclasses.field(default=None, repr=False, hash=False)

    @property
    def mt_provider(self) -> MachineTranslationProvider:
        return self.mtProvider

    @property
    def comment_count(self) -> int:
        return self.commentCount

    @property
    def unresolved_comment_count(self) -> int:
        return self.unresolvedCommentCount

    @property
    def from_translation_memory(self) -> bool:
        return self.fromTranslationMemory

    @classmethod
    def from_response_data(cls,
                           name_space: str,
                           key_name: str,
                           language: Language,
                           client: "TolgeeClient" = None,
                           **response_data: Unpack[dict[str, object]]) -> Self:
        client = proxy(client) if client is not None else client

        mod_data = response_data.copy()
        translation_id = mod_data.pop("id")
        text = mod_data.pop("text").strip()
        mtProvider = MachineTranslationProvider(mod_data.pop("mtProvider"))
        state = EntryState(mod_data.pop("state"))

        return cls(client=client,
                   name_space=name_space,
                   key_name=key_name,
                   language=language,
                   translation_id=translation_id,
                   text=text,
                   mtProvider=mtProvider,
                   state=state,
                   **mod_data)


@dataclasses.dataclass(frozen=True, slots=True)
class TranslationKey:
    key_id: int = dataclasses.field()
    name: str = dataclasses.field()
    namespace: str = dataclasses.field()
    client: Union["TolgeeClient", None] = dataclasses.field(default=None, repr=False, hash=False)

    @classmethod
    def from_response_data(cls, client: "TolgeeClient" = None, **response_data: Unpack[dict[str, object]]) -> Self:
        client = proxy(client) if client is not None else client

        key_id = response_data.pop("id")
        name = response_data.pop("name")
        namespace = response_data.pop("namespace")

        return cls(key_id=key_id, client=client, name=name, namespace=namespace)

    @property
    def entries(self) -> tuple["TranslationEntry"]:
        return self.client._get_entries_for_key(self)


@dataclasses.dataclass(frozen=True, slots=True)
class TranslationNamespace:
    namespace_id: int = dataclasses.field()
    name: str = dataclasses.field()
    client: Union["TolgeeClient", None] = dataclasses.field(default=None, repr=False, hash=False)

    @classmethod
    def from_response_data(cls, client: "TolgeeClient" = None, **response_data: Unpack[dict[str, object]]) -> Self:
        client = proxy(client) if client is not None else client

        namespace_id = response_data.pop("id")
        return cls(namespace_id=namespace_id, client=client, **response_data)


class RateLimit:
    __slots__ = ("_consume_lock",
                 "_max_request_amount",
                 "_reset_seconds",
                 "_rate_fractions",
                 "_time_provider",
                 "_consume_sleep",
                 "_bucket",
                 "_start_time",
                 "_random_sleep_on_consume")

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

        self._time_provider = time_provider or time

        self._bucket: int = 0
        self._start_time: float = None
        self._random_sleep_on_consume = random_sleep_on_consume

    def _refill_bucket(self) -> None:
        self._bucket = max(floor((self._max_request_amount - 5) / self._rate_fractions), 1)

        self._start_time = self._time_provider()

    def _get_sleep_time(self) -> float:
        base_sleep_time = (self._reset_seconds / self._rate_fractions) * 1.01
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

    def consume(self) -> None:
        if self._random_sleep_on_consume is True:
            sleep(random.random() / 10)
        with self._consume_lock:
            self._bucket -= 1
            if self._bucket <= 0:
                self._on_empty_bucket()

            return

    def __enter__(self) -> Self:
        self.consume()
        return self

    def __exit__(self,
                 exc_type: Optional[type[BaseException]] = None,
                 exc_value: Optional[BaseException] = None,
                 traceback: Optional[TracebackType] = None) -> None:
        pass


class TolgeeClient:

    __slots__ = ("_base_url",
                 "_api_key",
                 "client",
                 "_project_info",
                 "request_counter",
                 "_entry_map",
                 "__weakref__")

    rate_limit_spec: RateLimit = RateLimit(400, 60, rate_fractions=1, random_sleep_on_consume=True)

    def __init__(self,
                 base_url: Union[str, httpx.URL],
                 api_key: str) -> None:
        self._base_url = httpx.URL(base_url)
        self._api_key = api_key
        self.client: httpx.Client = None
        self._project_info: ProjectInfo = None
        self.request_counter: int = 0
        self._entry_map: dict[str, dict[Language, TranslationEntry]] = None

    @ property
    def entry_map(self) -> MappingProxyType[dict[str, dict[Language, TranslationEntry]]]:
        if self._entry_map is None:
            self._entry_map = self._get_entry_map()

        return MappingProxyType(self._entry_map)

    @ property
    def project_info(self) -> ProjectInfo:
        return self._project_info

    @ property
    def default_language(self) -> Language:
        return self.project_info.default_language

    @ property
    def languages(self) -> tuple[Language]:
        return self.project_info.languages

    def on_response(self, response: httpx.Response):
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            response.read()
            print(f"{response.text=}", flush=True)
            print(f"{response.url=}", flush=True)

            raise e

    def update_in_entry_map(self, translation: TranslationEntry) -> None:
        if translation.key_name not in self._entry_map:
            self._entry_map[translation.key_name] = {}
        self._entry_map[translation.key_name][translation.language] = translation

    def on_request(self, request: httpx.Request):

        self.rate_limit_spec.consume()

        # if self.request_counter > self.request_amount_threshold:
        #     sleep_time = round((60 / 40) + random.random(), ndigits=3)

        #     print(f"cooling down for {sleep_time}s", flush=True)
        #     sleep(sleep_time)
        #     self.request_counter = 0

    def _create_client(self) -> httpx.Client:
        client = httpx.Client(base_url=self._base_url,
                              headers={"X-API-Key": self._api_key},
                              event_hooks={'response': [self.on_response],
                                           "request": [self.on_request]},
                              timeout=httpx.Timeout(timeout=30.0),
                              limits=httpx.Limits(max_connections=10, max_keepalive_connections=5))
        return client

    def _get_project_info(self) -> dict[str, object]:
        response = self.client.get("/stats", params={})

        data = response.json()
        del data["languageStats"]
        languages = self.get_available_languages()

        default_language = next((l for l in languages if l.is_default is True))
        return ProjectInfo(**data, languages=languages, default_language=default_language)

    def _get_entries_for_key(self, key: "TranslationKey") -> tuple[TranslationEntry]:
        params = {"filterNamespace": [key.namespace],
                  "filterKeyName": [key.name],
                  "languages": [l.tag for l in self.languages]}

        _out = []

        while True:
            response = self.client.get("/translations", params=params)

            response_data = response.json()

            embedded_data = response_data.get("_embedded", None)
            if embedded_data is None:
                break

            data = embedded_data["keys"]

            for item in data:

                for language, value in item["translations"].items():

                    language = self.project_info.get_language_by_tag(language)
                    _out.append(TranslationEntry.from_response_data(client=self, language=language, name_space=item["keyNamespace"],
                                                                    key_name=item["keyName"], **value))

            next_cursor = response_data["nextCursor"]
            if next_cursor is not None:
                params["cursor"] = next_cursor
            else:
                break

        return tuple(_out)

    def get_translation(self, name_space: str, key: str, language: Language) -> Union[TranslationEntry, None]:

        query = {"filterNamespace": [name_space],
                 "filterKeyName": [key],
                 "languages": [language.tag]}
        response = self.client.get("/translations", params=query)

        try:
            return TranslationEntry.from_response_data(name_space=name_space, key_name=key, language=language, client=self, **response.json()["_embedded"]["keys"][0]["translations"][language.tag])
        except KeyError:
            return None

    def get_all_namespaces(self):
        params = {"page": 0}
        data = []

        while True:
            response = self.client.get("/namespaces", params=params)
            response_data = response.json()
            data += [TranslationNamespace.from_response_data(client=self, **i) for i in response_data["_embedded"]["namespaces"]]

            curr_page = response_data["page"]["number"]
            total_pages = response_data["page"]["totalPages"]

            if (curr_page + 1) == total_pages:
                break

            params["page"] += 1
        return data

    def get_all_keys(self) -> tuple["TranslationKey"]:
        data = []
        params = {"page": 0}
        response = self.client.get("/keys", params=params)

        for _response_data in ResponsePaginator(response=response, client=self.client):
            data += [TranslationKey.from_response_data(client=self, **i) for i in _response_data["keys"]]

        return tuple(data)

    def get_translations_for_language(self,
                                      language: Language) -> tuple[TranslationEntry]:

        params = {"size": 250,
                  "languages": [language.tag]}

        _out = []

        while True:

            response = self.client.get("/translations", params=params)

            response_data = response.json()

            embedded_data = response_data.get("_embedded", None)
            if embedded_data is None:
                break

            data = embedded_data["keys"]

            for item in data:

                for language, value in item["translations"].items():

                    language = self.project_info.get_language_by_tag(language)
                    _out.append(TranslationEntry.from_response_data(client=self, language=language, name_space=item["keyNamespace"],
                                                                    key_name=item["keyName"], **value))

            next_cursor = response_data["nextCursor"]
            if next_cursor is not None:
                params["cursor"] = next_cursor
            else:
                break

        return tuple(_out)

    def get_all_translations(self,
                             exclude_default_language: bool = False,
                             exclude_outdated: bool = False) -> tuple[TranslationEntry]:

        if exclude_default_language is True:
            languages_tags = [l.tag for l in self.languages if l.is_default is False]
        else:
            languages_tags = [l.tag for l in self.languages]

        params = {"size": 250,
                  "languages": languages_tags}

        if exclude_outdated is True:
            params["filterNotOutdatedLanguage"] = [l.tag for l in self.languages if l.is_default is False]

        _out = []
        response = self.client.get("/translations", params=params)

        for response_data in ResponsePaginator(response=response, client=self.client):
            data = response_data["keys"]

            for item in data:

                for language, value in item["translations"].items():

                    language = self.project_info.get_language_by_tag(language)
                    _out.append(TranslationEntry.from_response_data(client=self, language=language, name_space=item["keyNamespace"],
                                                                    key_name=item["keyName"], **value))

        return tuple(_out)

    def set_outdated(self, translation_id: int, outdated_state: bool = True) -> None:
        raise NotImplementedError()

        response = self.client.put(f"/translations/{translation_id}/set-outdated-flat/{outdated_state}")

    def get_available_languages(self) -> tuple[Language]:

        data = []
        params = {"page": 0}
        while True:
            response = self.client.get("/languages", params=params)
            response_data = response.json()
            data += [Language.from_response_data(client=self, **i) for i in response.json()["_embedded"]["languages"]]

            curr_page = response_data["page"]["number"]
            total_pages = response_data["page"]["totalPages"]

            if (curr_page + 1) == total_pages:
                break

            params["page"] += 1
        return tuple(data)

    def update_translations(self,
                            name_space: str,
                            key: str,
                            entry_values: Mapping["Language", str]):

        data = {"key": key,
                "namespace": name_space,
                "translations": {language.tag: value for language, value in entry_values.items()},
                "languagesToReturn": [l.tag for l in entry_values.keys()]}
        response = self.client.post(f"/translations", json=data).json()
        for raw_lang, values in response["translations"].items():
            item = TranslationEntry.from_response_data(name_space=name_space, key_name=key, language=self.project_info.get_language_by_tag(raw_lang), client=self, **values)
            self.update_in_entry_map(item)
        return response

    def update_namespace_for_key(self, key_name: str, new_namespace: str) -> None:
        key_id = next((k for k in self.get_all_keys() if k.name == key_name)).key_id

        response = self.client.put(f"/keys/{key_id}", json={"name": key_name, "namespace": new_namespace})
        del self._entry_map[key_name]

        query = {"filterNamespace": [new_namespace],
                 "filterKeyName": [key_name],
                 "languages": [l.tag for l in self.languages]}
        response = self.client.get("/translations", params=query)
        response_data = response.json()["_embedded"]["keys"][0]["translations"]
        for raw_lang, entry in response_data.items():
            if key_name not in self._entry_map:
                self._entry_map[key_name] = {}

            language_item = self.project_info.get_language_by_tag(raw_lang)
            entry_item = TranslationEntry.from_response_data(name_space=new_namespace, key_name=key_name, language=language_item, client=self, **entry)
            self._entry_map[key_name][language_item] = entry_item
            print(f"Update {entry_item!r} in key_map", flush=True)

    def update_translation_from_stringtable_entry(self, entry: "StringTableEntry") -> None:
        try:
            existing_item = self.entry_map[entry.key_name][self.project_info.get_language_by_tag(entry.language.tag)]
        except KeyError:
            existing_item = None

        if existing_item is not None and existing_item.text == entry.text and existing_item.name_space == entry.container_name:
            return

        if existing_item is not None and existing_item.name_space != entry.container_name:
            self.update_namespace_for_key(key_name=entry.key_name, new_namespace=entry.container_name)

        name_space = entry.container_name
        key_name = entry.key_name
        values = {self.project_info.get_language_by_tag(entry.language.tag): entry.text}
        self.update_translations(name_space=name_space, key=key_name, entry_values=values)
        print(f"updated {entry}.")

    def _get_entry_map(self) -> dict[str, dict[Language, TranslationEntry]]:
        key_map = defaultdict(dict)

        for translation in self.get_all_translations():
            key_map[translation.key_name][translation.language] = translation

        return dict(key_map)

    def connect(self, _from_enter: bool = False) -> Self:
        self.client = self._create_client()
        if _from_enter is True:
            self.client.__enter__()

        self._project_info = self._get_project_info()

        return self

    def close(self) -> None:
        if self.client is not None:
            self.client.close()
            self.client = None

    def __enter__(self) -> Self:
        self.connect(_from_enter=True)
        return self

    def __exit__(self,
                 exc_type: Optional[type[BaseException]] = None,
                 exc_value: Optional[BaseException] = None,
                 traceback: Optional[TracebackType] = None) -> None:
        self.client.__exit__(exc_type=exc_type, exc_value=exc_value, traceback=traceback)

    def __repr__(self) -> str:

        return f'{self.__class__.__name__}(base_url={self._base_url!r})'

# region [Main_Exec]


if __name__ == '__main__':
    start_time = perf_counter()
    import dotenv

    dotenv.load_dotenv()
    with TolgeeClient(api_key=os.environ["TEST_API_KEY"], base_url="https://tolgee.targetingsnake.de/v2/projects") as client:
        print(len({i.key_name for i in client.get_all_translations()}))
        print(len(set(client.get_all_keys())))
        # for member in ArmaLanguage._member_map_.values():
        #     _lang = client.project_info.language_from_arma_language(member)
        #     print(f"{member!r}  ->   {_lang!r}")
        #     pp(_lang.translations)
        #     print("-" * 50)
        # with open("language_data.json", "rb") as f:
        #     dd = json.load(f)

        # for item in dd:
        #     print(f"{item['name']}  |{item['flagEmoji']}|")
        # string_table = StringTable(THIS_FILE_DIR.joinpath(r"Stringtable_example.xml").resolve()).parse()
        # for _key in string_table.all_keys():
        #     original_entry = _key.entry_map[ArmaLanguage.ORIGINAL]
        #     client.update_translation_from_stringtable_entry(_key.entry_map[ArmaLanguage.ORIGINAL])

        # for item in client.get_all_translations(exclude_default_language=True, exclude_outdated=False):
        #     for _key in string_table.all_keys():

        #         if _key.name == item.key_name:
        #             try:
        #                 entry = _key.entry_map[ArmaLanguage(item.language.tag)]

        #                 entry.text = item.text
        #             except KeyError:
        #                 entry = StringTableEntry(ArmaLanguage(item.language.tag), item.text)
        #                 _key.add_entry(entry)

        #             if item.outdated is True:
        #                 _key.remove_entry(entry)

        # string_table.file_path.write_text(string_table.as_text(), encoding='utf-8', errors='ignore')

    # end_time = perf_counter()
    # print(f"Execution took {seconds2human(end_time-start_time)}", flush=True)
# endregion [Main_Exec]
