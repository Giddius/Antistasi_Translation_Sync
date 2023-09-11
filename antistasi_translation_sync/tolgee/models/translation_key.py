"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import sys
from typing import TYPE_CHECKING, Unpack
from pathlib import Path
from weakref import proxy
from collections.abc import Iterable

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self
# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from .tag import Tag
    from ..client import TolgeeClient
    from .project import Project
    from .language import Language
    from .translation_entry import TranslationEntry
    from ...stringtable.models import LanguageLike
    from .translation_namespace import TranslationNamespace

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion [Constants]


class TranslationKey:

    __slots__ = ("_key_id",
                 "_name",
                 "_namespace",
                 "_tags",
                 "_client",
                 "_entry_map")

    def __init__(self,
                 key_id: int,
                 name: str,
                 namespace: "TranslationNamespace",
                 tags: Iterable["Tag"],
                 client: "TolgeeClient") -> None:

        self._key_id: int = key_id
        self._name: str = name
        self._namespace = namespace
        self._tags = frozenset(tags)
        self._client = client

        self._entry_map: dict["Language", "TranslationEntry"] = {}

    @property
    def key_id(self) -> int:
        return self._key_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def namespace(self) -> "TranslationNamespace":
        return self._namespace

    @property
    def project(self) -> "Project":
        return self.namespace.project

    @property
    def tags(self) -> frozenset["Tag"]:
        return self._tags

    @property
    def is_deleted(self) -> bool:
        return "DELETED" in {t.name for t in self.tags}

    @classmethod
    def from_response_data(cls, client: "TolgeeClient" = None, **response_data: Unpack[dict[str, object]]) -> Self:
        client = proxy(client) if client is not None else client

        key_id = response_data.pop("id")
        name = response_data.pop("name")
        namespace = response_data.pop("namespace")

        return cls(key_id=key_id, client=client, name=name, namespace=namespace)

    def add_entry(self, entry: "TranslationEntry") -> None:
        self._entry_map[entry.language] = entry

    def add_tag(self, tag_name: str) -> None:
        if tag_name in {t.name for t in self.tags}:
            return
        tag = self._client.set_tag_for_key(self, tag_name=tag_name)
        self.refresh()

    def remove_tag(self, tag_name: str) -> None:
        # if tag_name not in {t.name for t in self.tags}:
        #     return
        tag = next((t for t in self.tags if t.name == tag_name), None)
        if tag is not None:
            print(f"Removing tag {tag!r}")
            self._client.remove_tag_for_key(key=self, tag=tag)
            self.refresh()

    def set_deleted(self) -> None:
        self.add_tag("DELETED")

    def unset_deleted(self) -> None:
        self.remove_tag("DELETED")

    def refresh(self) -> None:
        self._client.refresh_key(self)

    def change_namespace(self, new_namespace_name: str) -> None:
        self._client.update_namespace_for_key(self, new_namespace_name=new_namespace_name)

    def __getitem__(self, language: "LanguageLike") -> "TranslationEntry":
        language = self.project.get_language(language.language_name)
        return self._entry_map[language]

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.key_id == other.key_id and self.namespace == other.namespace and self.name == other.name
        return NotImplemented

    def __hash__(self) -> int:
        return self.key_id

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(key_id={self.key_id!r}, namespace={self.namespace.name!r}, name={self.name!r})"


# region [Main_Exec]
if __name__ == '__main__':
    pass

# endregion [Main_Exec]
