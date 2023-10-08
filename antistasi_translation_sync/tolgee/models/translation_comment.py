"""
WiP.

Soon.
"""

# region [Imports]


import sys


from enum import Enum, Flag, auto, unique

from pathlib import Path

from typing import (TYPE_CHECKING, TypeVar, TypeGuard, TypeAlias, Final, TypedDict, Generic, Union, Optional, ForwardRef, final, Callable,
                    no_type_check, no_type_check_decorator, overload, get_type_hints, cast, Protocol, runtime_checkable, NoReturn, NewType, Literal, AnyStr, IO, BinaryIO, TextIO, Any)

from datetime import datetime, timezone, timedelta


if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

if TYPE_CHECKING:
    from .translation_entry import TranslationEntry

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion [Constants]


class CommentState(Enum):
    RESOLUTION_NOT_NEEDED = auto()
    NEEDS_RESOLUTION = auto()
    RESOLVED = auto()

    @classmethod
    def _missing_(cls, value: object) -> Any:
        if isinstance(value, str):
            mod_value = value.casefold()
            for name, instance in cls._member_map_.items():
                if name.casefold() == mod_value:
                    return instance
        return super()._missing_(value)


def handle_tolgee_datetime_value(in_value: Union[int, datetime]) -> datetime:
    if isinstance(in_value, datetime):
        return in_value

    elif isinstance(in_value, int):
        return datetime.fromtimestamp(in_value / 1000, tz=timezone.utc)

    raise TypeError(f"Unknown type for tolgee datetime -> {type(in_value)!r} with value {in_value!r}.")


class TranslationCommentAuthor:
    __slots__ = ("_author_id",
                 "_username",
                 "_deleted",
                 "_disabled",
                 "_name")

    def __init__(self,
                 author_id: int,
                 username: str,
                 deleted: bool,
                 disabled: bool,
                 name: Union[str, None] = None) -> None:
        self._author_id = author_id
        self._username = username
        self._deleted = deleted
        self._disabled = disabled
        self._name = name

    @property
    def author_id(self) -> int:
        return self._author_id

    @property
    def username(self) -> str:
        return self._username

    @property
    def deleted(self) -> bool:
        return self._deleted

    @property
    def disabled(self) -> bool:
        return self._disabled

    @property
    def name(self) -> Union[str, None]:
        return self._name

    def __hash__(self) -> int:
        return self._author_id

    def __eq__(self, other: object) -> bool:
        if isinstance(other, TranslationCommentAuthor):
            return self.author_id == other._author_id

        return NotImplemented

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(author_id={self.author_id!r}, username={self.username!r}, name={self.name!r})"


class TranslationComment:
    __slots__ = ("_comment_id",
                 "_entry",
                 "_text",
                 "_state",
                 "_author",
                 "_created_at",
                 "_updated_at")

    def __init__(self,
                 comment_id: int,
                 entry: "TranslationEntry",
                 text: str,
                 state: Union[str, CommentState],
                 author: TranslationCommentAuthor,
                 created_at: datetime,
                 updated_at: datetime) -> None:

        self._comment_id = comment_id
        self._entry = entry
        self._text = text
        self._state = CommentState(state)
        self._author = author
        self._created_at = handle_tolgee_datetime_value(created_at)
        self._updated_at = handle_tolgee_datetime_value(updated_at)

    @property
    def comment_id(self) -> int:
        return self._comment_id,

    @property
    def entry(self) -> "TranslationEntry":
        return self._entry,

    @property
    def text(self) -> str:
        return self._text,

    @property
    def state(self) -> CommentState:
        return self._state,

    @property
    def author(self) -> TranslationCommentAuthor:
        return self._author,

    @property
    def created_at(self) -> datetime:
        return self._created_at,

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    def __hash__(self) -> int:
        return self._comment_id

    def __eq__(self, other: object) -> bool:
        if isinstance(other, TranslationComment):
            return self._comment_id == other._commment_id

        return NotImplemented

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(comment_id={self.comment_id!r},created_at={self.created_at!r}, text={self.text!r}, author={self.author!r})"
# region [Main_Exec]


if __name__ == '__main__':
    pass

# endregion [Main_Exec]
