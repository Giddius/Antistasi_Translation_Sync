"""
WiP.

Soon.
"""

# region [Imports]


import sys


from abc import ABC, ABCMeta, abstractmethod

from enum import Enum, Flag, auto, unique

from pathlib import Path

from typing import (TYPE_CHECKING, TypeVar, TypeGuard, TypeAlias, Final, TypedDict, Generic, Union, Optional, ForwardRef, final, Callable,
                    no_type_check, no_type_check_decorator, overload, get_type_hints, cast, Protocol, runtime_checkable, NoReturn, NewType, Literal, AnyStr, IO, BinaryIO, TextIO, Any)


if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

if TYPE_CHECKING:
    from antistasi_translation_sync.tolgee.models import TranslationKey, TranslationEntry, TranslationNamespace, Project

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
ZERO_WIDTH = '\u200b'

# endregion [Constants]


class ChangeTypus(Enum):
    UPDATED_ORIGINAL_TEXT = auto()
    DELETED_KEY = auto()
    CHANGED_NAMESPACE = auto()
    OUTDATED_ENTRY = auto()


class TextFormat(Enum):
    PLAIN = auto()
    MARKDOWN = auto()

    @classmethod
    def _missing_(cls, value: object) -> Any:
        if isinstance(value, str):
            try:
                return cls._member_map_[value.upper()]
            except KeyError:
                pass

        return super()._missing_(value)


_TEXT_FORMAT_TYPE = Union[TextFormat, Literal["plain", "markdown"], None]


class ChangedItem(ABC):
    typus: ChangeTypus = None

    def __init__(self, project: "Project") -> None:
        self.project = project

    def to_text(self, text_format: _TEXT_FORMAT_TYPE = None) -> str:

        return str(self)

    def __repr__(self) -> str:
        arguments_text = ', '.join(f"{k}={v!r}" for k, v in vars(self).items())
        return f'{self.__class__.__name__}({arguments_text})'


class UpdatedOriginalTextChange(ChangedItem):
    typus: ChangeTypus = ChangeTypus.UPDATED_ORIGINAL_TEXT

    def __init__(self,
                 project: "Project",
                 key: "TranslationKey",
                 old_text: str) -> None:
        super().__init__(project=project)
        self.key = key
        self.old_text = old_text


class DeletedKeyChange(ChangedItem):
    typus: ChangeTypus = ChangeTypus.DELETED_KEY

    def __init__(self,
                 project: "Project",
                 key: "TranslationKey") -> None:
        super().__init__(project=project)
        self.key = key


class ChangedNamespaceChange(ChangedItem):
    typus: ChangeTypus = ChangeTypus.CHANGED_NAMESPACE

    def __init__(self,
                 project: "Project",
                 key: "TranslationKey",
                 new_namespace: "TranslationNamespace",
                 old_namespace: "TranslationNamespace") -> None:
        super().__init__(project=project)
        self.key = key
        self.new_namespace = new_namespace
        self.old_namespace = old_namespace

    def to_text(self, text_format: _TEXT_FORMAT_TYPE = None) -> str:

        text_format = TextFormat(text_format) if text_format is not None else text_format
        match text_format:
            case TextFormat.PLAIN:
                text = f"changed Namespace for key {self.key.name!r} from {self.old_namespace.name!r} to {self.new_namespace.name!r}"

            case TextFormat.MARKDOWN:
                text = f"- **{self.key.name}**:\n    -`{self.old_namespace.name}` -> `{self.new_namespace.name}`"

            case _:
                text = str(self)
        return text


class OutdatedEntryChange(ChangedItem):

    def __init__(self,
                 project: "Project",
                 key: "TranslationKey",
                 entry: "TranslationEntry") -> None:
        super().__init__(project)
        self.key = key
        self.entry = entry


class ChangeRecorder:

    def __init__(self) -> None:
        self._changes: dict[str, dict[ChangeTypus, list[ChangedItem]]] = {}

    def add_change_item(self, change_item: ChangedItem) -> None:
        if change_item.project.name not in self._changes:
            self._changes[change_item.project.name] = {m: [] for m in ChangeTypus.__members__.values()}

        self._changes[change_item.project.name][change_item.typus].append(change_item)


# region [Main_Exec]
if __name__ == '__main__':
    pass

# endregion [Main_Exec]
