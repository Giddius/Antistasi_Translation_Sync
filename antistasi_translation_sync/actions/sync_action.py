"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import sys
from typing import TYPE_CHECKING
from pathlib import Path

from .base_action import BaseAction

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


class SyncAction(BaseAction):

    def run_action(self) -> None:
        ...


# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]
