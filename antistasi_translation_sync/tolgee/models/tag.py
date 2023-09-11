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

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self
# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from ..client import TolgeeClient
    from .project import Project

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion [Constants]


@dataclasses.dataclass(frozen=True, slots=True)
class Tag:
    tag_id: int = dataclasses.field(hash=True, compare=True)
    name: str = dataclasses.field(compare=True)
    project: "Project" = dataclasses.field()
    client: Union["TolgeeClient", None] = dataclasses.field(default=None, repr=False, hash=False, compare=False)

    @classmethod
    def from_response_data(cls,
                           client: "TolgeeClient" = None,
                           **response_data: Unpack[dict[str, object]]) -> Self:

        tag_id = response_data.pop("id")
        name = response_data.pop("name")

        return cls(tag_id=tag_id, name=name, client=client, **response_data)


# region [Main_Exec]
if __name__ == '__main__':
    pass

# endregion [Main_Exec]
