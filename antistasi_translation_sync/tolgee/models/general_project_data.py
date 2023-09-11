"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import sys
import dataclasses
from typing import TYPE_CHECKING, Union
from pathlib import Path

if sys.version_info >= (3, 11):
    pass
else:
    pass
# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    ...

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion [Constants]


@dataclasses.dataclass(frozen=True, slots=True, weakref_slot=True, order=True)
class GeneralProjectData:
    project_id: int = dataclasses.field(hash=True, compare=True)
    name: str = dataclasses.field(hash=False, compare=False)
    slug: str = dataclasses.field(hash=False, compare=False, repr=False)
    project_url: str = dataclasses.field(hash=True, compare=False, repr=False)
    description: str = dataclasses.field(hash=False, compare=False, repr=False, default="")
    avatar_url: Union[str, None] = dataclasses.field(hash=False, compare=False, repr=False, default=None)
    avatar_thumbnail_url: Union[str, None] = dataclasses.field(hash=False, compare=False, repr=False, default=None)

# region [Main_Exec]


if __name__ == '__main__':
    pass

# endregion [Main_Exec]
