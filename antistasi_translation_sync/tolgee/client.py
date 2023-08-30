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
import traceback

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

import httpx
from types import MappingProxyType, TracebackType
from .rate_limiter import get_rate_limiter, RateLimit

from .models import Language, ProjectInfo, TranslationNamespace, TranslationKey, TranslationEntry, MachineTranslationProvider, EntryState, Tag, Project
from .retrier import ResponsePaginator, Retrier
if TYPE_CHECKING:
    from ..stringtable import StringTableEntry

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion [Constants]


class TolgeeClient:

    __slots__ = ("_base_url",
                 "_api_key",
                 "client",
                 "project",
                 "rate_limit_spec",
                 "__weakref__")

    def __init__(self,
                 base_url: Union[str, httpx.URL],
                 api_key: str) -> None:
        self._base_url = httpx.URL(base_url)
        self._api_key = api_key
        self.client: httpx.Client = None
        self.project: "Project" = None
        self.rate_limit_spec: RateLimit = get_rate_limiter(self._base_url)

    @ property
    def project_info(self) -> ProjectInfo:
        return self.project.project_info

    @ property
    def default_language(self) -> Language:
        return self.project.default_language

    @ property
    def languages(self) -> tuple[Language]:
        return self.project.languages

    def on_response(self, response: httpx.Response):
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            response.read()
            print(f"{response.text=}", flush=True)
            print(f"{response.url=}", flush=True)

            raise e

    def on_request(self, request: httpx.Request):

        self.rate_limit_spec.consume()

    def _create_client(self) -> httpx.Client:
        client = httpx.Client(base_url=self._base_url,
                              headers={"X-API-Key": self._api_key},
                              event_hooks={'response': [self.on_response],
                                           "request": [self.on_request]},
                              timeout=httpx.Timeout(timeout=30.0),
                              limits=httpx.Limits(max_connections=1, max_keepalive_connections=1))
        return client

    def _get_project_info(self) -> "ProjectInfo":
        stats_unwanted_keys = {"languageStats"}
        stats_response = self.client.get("/stats", params={})

        stats_data = {k: v for k, v in stats_response.json().items() if k not in stats_unwanted_keys}

        info_unwanted_keys = {"userFullName", "id", "scopes", "expiresAt", "username", "description", "permittedLanguageIds"}
        info_request = self.client.build_request("GET", str(self._base_url).removesuffix("/").removesuffix("/projects") + "/api-keys/current")

        info_response = self.client.send(info_request)

        info_data = {k: v for k, v in info_response.json().items() if k not in info_unwanted_keys}
        info_data["lastUsedAt"] = datetime.fromtimestamp(info_data["lastUsedAt"] / 1000, tz=timezone.utc)
        return ProjectInfo(**(stats_data | info_data))

    def _build_project_tree(self, project: "Project") -> None:

        params = {"languages": [l.tag for l in project.language_map.values()],
                  "size": 75
                  }

        while True:
            response = self.client.get("/translations", params=params)

            general_response_data = response.json()
            try:
                response_data = general_response_data["_embedded"]
            except KeyError:
                break
            for data in response_data["keys"]:
                namespace = project.get_or_create_namespace(namespace_id=data["keyNamespaceId"], name=data["keyNamespace"])
                key = TranslationKey(key_id=data["keyId"],
                                     name=data["keyName"],
                                     namespace=namespace,
                                     tags=[Tag(tag_id=i["id"],
                                               name=i["name"], client=self) for i in data["keyTags"]],
                                     client=self)
                namespace.add_key(key)

                for language_tag, translation_data in data["translations"].items():

                    if not translation_data["text"]:
                        continue

                    translation = TranslationEntry(entry_id=translation_data["id"],
                                                   key=key,
                                                   language=project.get_language_by_tag(language_tag),
                                                   text=translation_data["text"],
                                                   state=translation_data["state"],
                                                   outdated=translation_data["outdated"],
                                                   auto=translation_data["auto"],
                                                   mtProvider=translation_data["mtProvider"],
                                                   commentCount=translation_data["commentCount"],
                                                   unresolvedCommentCount=translation_data["unresolvedCommentCount"],
                                                   fromTranslationMemory=translation_data["fromTranslationMemory"],
                                                   client=self)
                    key.add_entry(translation)

            try:
                cursor = general_response_data["nextCursor"]
                if not cursor:
                    break
                params["cursor"] = cursor
            except KeyError:
                break

    def get_all_tags(self) -> Generator["Tag", None, None]:
        params = {"page": 0}
        response = self.client.get("/tags", params=params)

        for _response_data in ResponsePaginator(response=response, client=self.client):
            for item in _response_data["tags"]:
                yield Tag.from_response_data(client=self, **item)

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

    def set_tag_for_key(self, key: "TranslationKey", tag_name: str) -> "Tag":
        response = self.client.put(f"/keys/{key.key_id}/tags", json={"name": tag_name})

        tag = Tag.from_response_data(response_data=response.json())
        return tag

    def remove_tag_for_key(self, key: "TranslationKey", tag: "Tag") -> None:
        response = self.client.delete(f"/keys/{key.key_id}/tags/{tag.tag_id}")

    def get_all_translations(self,
                             exclude_default_language: bool = False,
                             exclude_outdated: bool = False,
                             exclude_deleted: bool = True) -> Generator[TranslationEntry, None, None]:

        if exclude_default_language is True:
            languages_tags = [l.tag for l in self.languages if l.is_default is False]
        else:
            languages_tags = [l.tag for l in self.languages]

        params = {"size": 250,
                  "languages": languages_tags}

        if exclude_outdated is True:
            params["filterNotOutdatedLanguage"] = [l.tag for l in self.languages if l.is_default is False]

        response = self.client.get("/translations", params=params)

        for response_data in ResponsePaginator(response=response, client=self.client):
            data = response_data["keys"]

            for item in data:
                if exclude_deleted and "DELETED" in {i["name"] for i in item["keyTags"]}:
                    continue
                print(f'{item["contextPresent"]=}')
                for language, value in item["translations"].items():

                    language = self.project_info.get_language_by_tag(language)
                    yield TranslationEntry.from_response_data(client=self, language=language, name_space=item["keyNamespace"],
                                                              key_name=item["keyName"], **value)

    def _get_entries_for_key(self, key: "TranslationKey") -> Generator[TranslationEntry, None, None]:
        params = {"filterNamespace": [key.namespace],
                  "filterKeyName": [key.name],
                  "languages": [l.tag for l in self.languages]}

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

                    entry = TranslationEntry.from_response_data(client=self, language=language, name_space=item["keyNamespace"],
                                                                key_name=item["keyName"], **value)
                    if entry.text is not None:
                        yield entry
            next_cursor = response_data["nextCursor"]
            if next_cursor is not None:
                params["cursor"] = next_cursor
            else:
                break

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

        while True:
            response = self.client.get("/namespaces", params=params)
            response_data = response.json()
            yield from (TranslationNamespace.from_response_data(client=self, **i) for i in response_data["_embedded"]["namespaces"])

            curr_page = response_data["page"]["number"]
            total_pages = response_data["page"]["totalPages"]

            if (curr_page + 1) == total_pages:
                break

            params["page"] += 1

    def get_all_keys(self) -> Generator["TranslationKey", None, None]:

        params = {"page": 0}
        response = self.client.get("/keys", params=params)

        for _response_data in ResponsePaginator(response=response, client=self.client):
            for item in _response_data["keys"]:

                yield TranslationKey.from_response_data(client=self, **item)

    def get_translations_for_language(self,
                                      language: Language) -> Generator[TranslationEntry, None, None]:

        params = {"size": 250,
                  "languages": [language.tag]}

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
                    yield TranslationEntry.from_response_data(client=self, language=language, name_space=item["keyNamespace"],
                                                              key_name=item["keyName"], **value)

            next_cursor = response_data["nextCursor"]
            if next_cursor is not None:
                params["cursor"] = next_cursor
            else:
                break

    def get_all_translations(self,
                             exclude_default_language: bool = False,
                             exclude_outdated: bool = False,
                             exclude_deleted: bool = True) -> Generator[TranslationEntry, None, None]:

        if exclude_default_language is True:
            languages_tags = [l.tag for l in self.languages if l.is_default is False]
        else:
            languages_tags = [l.tag for l in self.languages]

        params = {"languages": languages_tags}

        if exclude_outdated is True:
            params["filterNotOutdatedLanguage"] = [l.tag for l in self.languages if l.is_default is False]

        response = self.client.get("/translations", params=params)

        for response_data in ResponsePaginator(response=response, client=self.client):
            data = response_data["keys"]

            for item in data:
                if exclude_deleted and "DELETED" in {i["name"] for i in item["keyTags"]}:
                    continue
                print(f'{item["contextPresent"]=}')
                for language, value in item["translations"].items():

                    language = self.project_info.get_language_by_tag(language)
                    yield TranslationEntry.from_response_data(client=self, language=language, name_space=item["keyNamespace"],
                                                              key_name=item["keyName"], **value)

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
            existing_item = self.entry_map[entry.key_name][self.project_info.language_from_arma_language(entry.language)]
        except KeyError:
            existing_item = None

        if existing_item is not None and existing_item.text == entry.text and existing_item.name_space == entry.container_name:
            return

        if existing_item is not None and existing_item.name_space != entry.container_name:
            self.update_namespace_for_key(key_name=entry.key_name, new_namespace=entry.container_name)

        name_space = entry.container_name
        key_name = entry.key_name
        values = {self.project_info.language_from_arma_language(entry.language): entry.text}
        self.update_translations(name_space=name_space, key=key_name, entry_values=values)
        print(f"updated {entry}.")

    def get_daily_activity(self) -> dict[str, int]:
        response = self.client.get("/stats/daily-activity")

        return response.json()

    def connect(self, _from_enter: bool = False) -> Self:
        self.client = self._create_client()

        if _from_enter is True:
            self.client.__enter__()

        self.project = Project(client=self)
        # self.project.setup()

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
    ...

# endregion [Main_Exec]
