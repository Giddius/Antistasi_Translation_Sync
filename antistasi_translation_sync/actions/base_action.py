"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import sys
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Union
from pathlib import Path

if sys.version_info >= (3, 11):
    pass
else:
    pass
# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_translation_sync.configuration import Config

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion [Constants]


class BaseAction(ABC):

    _name: str = None
    _description: str = None

    def __init__(self,
                 stringtable_file: Path,
                 config: "Config") -> None:
        self.stringtable_file = stringtable_file
        self.config = config

    @classmethod
    @property
    def name(cls) -> str:
        if cls._name is not None:
            return cls._name

        raw_name = cls.__name__.removesuffix("Action")
        return raw_name

    @classmethod
    @property
    def description(cls) -> Union[str, None]:
        if cls._description is not None:
            return cls._description

        return cls.__doc__ or cls.__init__.__doc__

    @abstractmethod
    def run_action(self) -> None:
        ...


# region [Main_Exec]
if __name__ == '__main__':
    print(BaseAction.description)

# endregion [Main_Exec]
