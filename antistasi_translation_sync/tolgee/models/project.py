"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import sys
import dataclasses
from typing import TYPE_CHECKING, Union, TypeVar
from pathlib import Path
from datetime import datetime
from itertools import chain
from collections import ChainMap

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from .tag import Tag
from .language import Language
from .project_info import ProjectInfo
from .translation_key import TranslationKey
from .translation_entry import TranslationEntry
from .translation_namespace import TranslationNamespace

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from ..client import TolgeeClient
    from ...stringtable.models import LanguageLike, StringTableEntry

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

            else:
                raise KeyError(key)

        except KeyError:
            raise KeyError(f"No Namespace found for key {key!r} in {self!r}.")

    def __delitem__(self, key: Union[str, int]) -> None:
        try:
            if isinstance(key, int):
                namespace = self._id_map[key]
            elif isinstance(key, str):
                namespace = self._name_map[key]

            else:
                raise KeyError(key)

            self._namespaces.remove(namespace)
            del self._id_map[namespace.namespace_id]
            del self._name_map[namespace.name]
        except KeyError:
            raise KeyError(f"No Namespace found for key {key!r} in {self!r}.")

    def add(self, namespace: "TranslationNamespace") -> None:
        if namespace in self._namespaces:
            raise RuntimeError(f"{namespace!r} already in {self!r}.")
        self._namespaces.append(namespace)
        self._id_map[namespace.namespace_id] = namespace
        self._name_map[namespace.name] = namespace

    def get(self, key: Union[str, int], default: _GET_DEFAULT_TYPE = None) -> Union["TranslationNamespace", _GET_DEFAULT_TYPE]:
        try:
            return self[key]
        except KeyError:
            return default

    def remove(self, namespace: "TranslationNamespace") -> None:
        self._namespaces.remove(namespace)
        del self._id_map[namespace.namespace_id]
        del self._name_map[namespace.name]


class TagContainer:

    def __init__(self) -> None:
        self._tags: list["Tag"] = []
        self._name_map: dict[str, "Tag"] = {}
        self._id_map: dict[int, "Tag"] = {}

    def __getitem__(self, key: Union[str, int]) -> "Tag":
        try:

            if isinstance(key, int):
                return self._id_map[key]
            elif isinstance(key, str):
                return self._name_map[key]

        except KeyError:
            pass

        raise KeyError(f"No Tag found for key {key!r} in {self!r}.")

    def add(self, tag: "Tag") -> None:
        if Tag in self._tags:
            raise RuntimeError(f"{tag!r} already in {self!r}.")
        self._tags.append(tag)
        self._id_map[tag.tag_id] = tag
        self._name_map[tag.name] = tag

    def get(self, key: Union[str, int], default: _GET_DEFAULT_TYPE = None) -> Union["Tag", _GET_DEFAULT_TYPE]:
        try:
            return self[key]
        except KeyError:
            return default


@dataclasses.dataclass(frozen=True, slots=True)
class ChangeItem:
    timestamp: datetime = dataclasses.field(hash=True, compare=True, repr=True)
    item_path: str = dataclasses.field(hash=True, compare=True, repr=True)
    action: str = dataclasses.field(hash=True, compare=True, repr=True)
    comment: str = dataclasses.field(hash=False, compare=False, repr=False)


class Project:
    __slots__ = ("client",
                 "project_info",
                 "tag_container",
                 "namespace_container",
                 "language_map",
                 "default_language",
                 "changes",
                 "__weakref__")

    def __init__(self,
                 client: "TolgeeClient") -> None:
        self.client = client
        self.project_info: "ProjectInfo" = None
        self.tag_container: TagContainer = TagContainer()
        self.namespace_container: NamespaceContainer = NamespaceContainer()
        self.language_map: dict[str, "Language"] = {}
        self.default_language: "Language" = None

        self.changes: list[ChangeItem] = []

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
    def tags(self) -> list["Tag"]:
        return self.tag_container._tags.copy()

    @property
    def keys(self) -> list["TranslationKey"]:
        return list(chain(*[list(n._key_map.values()) for n in self.namespaces]))

    @property
    def entries(self) -> list["TranslationEntry"]:
        return list(chain(*[list(k._entry_map.values()) for k in self.keys]))

    def setup(self) -> Self:

        self.project_info = self.client._get_project_info()

        self.language_map = {lang.language_name.casefold(): lang for lang in self.client.get_available_languages()}
        self.default_language = next(lang for lang in self.languages if lang.is_default)

        self.client._build_project_tree(self)

        return self

    def refresh(self) -> Self:
        self.namespace_container = NamespaceContainer()
        return self.setup()

    def remove_namespace(self, namespace: "TranslationNamespace") -> None:
        self.namespace_container.remove(namespace)

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
        language = next((lang for lang in self.languages if lang.tag.casefold() == mod_tag), None)
        if language is None:

            raise KeyError(f"{self!r} has no Language with the tag {tag!r}.")

        return language

    def get_language(self, in_item: Union[str, "LanguageLike"]) -> "Language":

        for language_get_method in (self.language_from_arma_language, self.get_language_by_tag, self.get_language_by_name):
            try:
                return language_get_method(in_item)
            except (AttributeError, KeyError) as e:
                # print(f"{e!r} error for method {language_get_method.__name__!r} and in_item {in_item!r}", flush=True)
                pass

        raise KeyError(f"No language found for {in_item!r} in {self!r}.")

    def get_key_by_name(self, key_name: str) -> "TranslationKey":
        for name_space in self.namespaces:
            try:
                return name_space._key_map[key_name]
            except KeyError:
                continue

        raise KeyError(f"No key with name {key_name!r} found.")
        # return ChainMap(*[ns._key_map for ns in self.namespaces])[key_name]

    def add_namespace(self, namespace: "TranslationNamespace"):
        self.namespace_container.add(namespace)

    def add_tag(self, tag: "Tag") -> None:
        self.tag_container.add(tag)

    def __getitem__(self, key: Union[str, int]) -> "TranslationNamespace":
        return self.namespace_container[key]

    def get_or_create_tag(self, tag_id: int, tag_name: str) -> "Tag":
        try:
            return self.tag_container._id_map[tag_id]
        except KeyError:
            tag = Tag(tag_id=tag_id, name=tag_name, project=self)
            self.add_tag(tag=tag)
            return tag

    def get_or_create_namespace(self, name: str, namespace_id: int = None) -> "TranslationNamespace":
        try:
            return self[namespace_id] if namespace_id is not None else self[name]
        except KeyError:
            if namespace_id is None:
                namespace_id = self.client.get_namespace_id_by_name(namespace_name=name)
            namespace = TranslationNamespace(namespace_id=namespace_id, name=name, project=self)
            self.add_namespace(namespace=namespace)
            return namespace

    def update_or_create_from_stringtable_entry(self, stringtable_entry: "StringTableEntry") -> bool:
        try:
            key = self.get_key_by_name(stringtable_entry.key_name)
        except KeyError:
            key = None

        if key is None:
            key = self.client.insert_translation_for_new_key(namespace_name=stringtable_entry.container_name, key_name=stringtable_entry.key_name, language=stringtable_entry.language, text=stringtable_entry.text)
            key.refresh()
            return True

        else:
            try:
                result = key[self.get_language(stringtable_entry.language)].update_from_stringtable_entry(stringtable_entry)
                if result is True:
                    key.refresh()
                return result
            except KeyError:
                request_data = {"key": key.name,
                                "namespace": key.namespace.name,
                                "translations": {self.get_language(stringtable_entry.language).tag: stringtable_entry.text}}

                response = self.client.client.post("/translations", json=request_data)
                response.close()
                key.refresh()
                return True

    def __repr__(self) -> str:

        return f'{self.__class__.__name__}(project_id={self.project_id!r}, name={self.name!r})'


# region [Main_Exec]
if __name__ == '__main__':
    pass

# endregion [Main_Exec]
