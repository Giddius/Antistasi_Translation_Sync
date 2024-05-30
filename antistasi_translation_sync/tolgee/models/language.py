"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import sys
import dataclasses
from typing import TYPE_CHECKING, Union, Unpack
from pathlib import Path
from weakref import proxy

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self
# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from ..client import TolgeeClient

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
    originalName: str = dataclasses.field(compare=False, hash=False, repr=False)
    base: bool = dataclasses.field(compare=False, hash=False)
    flagEmoji: str = dataclasses.field(compare=False, hash=False, repr=False)

    @property
    def language_name(self) -> str:
        return self.name

    @property
    def original_name(self) -> str:
        return self.originalName

    @property
    def flag_emoji(self) -> str:
        return self.flagEmoji

    @property
    def is_default(self) -> str:
        return self.base

    @property
    def has_valid_language_id(self) -> bool:
        return self.language_id != -1 and self.language_id >= 0

    @classmethod
    def from_response_data(cls,
                           **response_data: Unpack[dict[str, object]]) -> Self:

        language_id = response_data["id"]
        name = response_data["name"]
        tag = response_data["tag"]
        original_name = response_data["originalName"]
        base = response_data["base"]
        flag_emoji = response_data["flagEmoji"]

        return cls(language_id=language_id, name=name, tag=tag, originalName=original_name, base=base, flagEmoji=flag_emoji)

    def to_data(self) -> dict[str, str]:
        return {"name": self.name,
                "originalName": self.original_name,
                "tag": self.tag,
                "flagEmoji": self.flag_emoji}

    def __str__(self) -> str:
        return self.tag


# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]
