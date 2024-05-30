"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import sys
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Union, Optional
from pathlib import Path
from .translation_comment import TranslationComment, TranslationCommentAuthor
if sys.version_info >= (3, 11):
    pass
else:
    pass
# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from ..client import TolgeeClient
    from .project import Project
    from .language import Language
    from .translation_key import TranslationKey
    from ...stringtable.models import StringTableEntry
    from .translation_namespace import TranslationNamespace

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion [Constants]


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


class TranslationEntry:
    __slots__ = ("_entry_id",
                 "_key",
                 "_language",
                 "_text",
                 "_state",
                 "_outdated",
                 "_auto",
                 "_mtProvider",
                 "_commentCount",
                 "_unresolvedCommentCount",
                 "_fromTranslationMemory",
                 "_comments")

    def __init__(self,
                 entry_id: int,
                 key: "TranslationKey",
                 language: "Language",
                 text: str,
                 state: Union[str, EntryState],
                 outdated: bool,
                 auto: bool,
                 mtProvider: Union[str, MachineTranslationProvider],
                 commentCount: Optional[int],
                 unresolvedCommentCount: Optional[int],
                 fromTranslationMemory: bool) -> None:
        self._entry_id: int = entry_id
        self._key: "TranslationKey" = key
        self._language: "Language" = language
        self._text: str = text.rstrip("\n")
        self._state: EntryState = EntryState(state)
        self._outdated: bool = outdated
        self._auto: bool = auto
        self._mtProvider: MachineTranslationProvider = MachineTranslationProvider(mtProvider)
        self._commentCount: Optional[int] = commentCount
        self._unresolvedCommentCount: Optional[int] = unresolvedCommentCount
        self._fromTranslationMemory: bool = fromTranslationMemory

        self._comments: tuple[str] = None

    @property
    def comments(self) -> tuple[TranslationComment]:
        if self._comments is None:
            if self.comment_count <= 0:
                self._comments = tuple()
            else:
                comments = []

                params = {"size": 250}
                response = self.project.client.client.get(f"/translations/{self.entry_id}/comments", params=params)

                data = response.json()["_embedded"]

                for comment_data in data["translationComments"]:
                    comment_author = TranslationCommentAuthor(author_id=comment_data["author"]["id"],
                                                              username=comment_data["author"]["username"],
                                                              deleted=comment_data["author"]["deleted"],
                                                              disabled=comment_data["author"]["disabled"],
                                                              name=comment_data["author"].get("name"))

                    comment_item = TranslationComment(comment_id=comment_data["id"],
                                                      entry=self,
                                                      text=comment_data["text"],
                                                      state=comment_data["state"],
                                                      author=comment_author,
                                                      created_at=comment_data["createdAt"],
                                                      updated_at=comment_data["updatedAt"])
                    comments.append(comment_item)

                self._comments = tuple(comments)

        return self._comments

    @property
    def entry_id(self) -> int:
        return self._entry_id

    @property
    def key(self) -> "TranslationKey":
        return self._key

    @property
    def namespace(self) -> "TranslationNamespace":
        return self._key.namespace

    @property
    def project(self) -> "Project":
        return self.namespace.project

    @property
    def language(self) -> "Language":
        return self._language

    @property
    def text(self) -> str:
        return self._text

    @property
    def state(self) -> EntryState:
        return self._state

    @property
    def outdated(self) -> bool:
        return self._outdated

    @property
    def auto(self) -> bool:
        return self._auto

    @property
    def mtProvider(self) -> MachineTranslationProvider:
        return self._mtProvider

    @property
    def commentCount(self) -> Optional[int]:
        return self._commentCount

    @property
    def unresolvedCommentCount(self) -> Optional[int]:
        return self._unresolvedCommentCount

    @property
    def fromTranslationMemory(self) -> bool:
        return self._fromTranslationMemory

    @property
    def client(self) -> Union["TolgeeClient", None]:
        return self._client

    @property
    def is_deleted(self) -> bool:
        return self._key.is_deleted

    @property
    def mt_provider(self) -> MachineTranslationProvider:
        return self._mtProvider

    @property
    def comment_count(self) -> int:
        return self._commentCount

    @property
    def unresolved_comment_count(self) -> int:
        return self._unresolvedCommentCount

    @property
    def is_from_translation_memory(self) -> bool:
        return self._fromTranslationMemory

    def update_from_stringtable_entry(self, stringtable_entry: "StringTableEntry") -> bool:
        if stringtable_entry.text == self.text:
            return False

        request_data = {"key": self.key.name,
                        "namespace": self.namespace.name,
                        "translations": {self.language.tag: stringtable_entry.text}}

        response = self.project.client.client.post("/translations", json=request_data)
        response.close()

        return True

    # def __str__(self) -> str:
    #     return self.name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(entry_id={self.entry_id!r}, key={self.key.name}, namespace={self.namespace.name!r}, language={self.language.name!r})"


# region [Main_Exec]
if __name__ == '__main__':
    pass

# endregion [Main_Exec]
