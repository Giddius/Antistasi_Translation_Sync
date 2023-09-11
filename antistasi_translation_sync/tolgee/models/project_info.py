"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import sys
import dataclasses
from typing import TYPE_CHECKING
from pathlib import Path
from datetime import datetime

if sys.version_info >= (3, 11):
    pass
else:
    pass
# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    pass

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion [Constants]


@dataclasses.dataclass(frozen=True, slots=True)
class ProjectInfo:
    projectId: int = dataclasses.field()
    languageCount: int = dataclasses.field()
    keyCount: int = dataclasses.field()
    baseWordsCount: int = dataclasses.field()
    translatedPercentage: float = dataclasses.field()
    reviewedPercentage: float = dataclasses.field()
    membersCount: int = dataclasses.field()
    tagCount: int = dataclasses.field()
    projectName: str = dataclasses.field()
    lastUsedAt: datetime = dataclasses.field()

    @property
    def name(self) -> str:
        return self.projectName

    @property
    def project_name(self) -> str:
        return self.projectName

    @property
    def project_id(self) -> int:
        return self.projectId

    @property
    def language_count(self) -> int:
        return self.languageCount

    @property
    def key_count(self) -> int:
        return self.keyCount

    @property
    def base_words_count(self) -> int:
        return self.baseWordsCount

    @property
    def translated_percentage(self) -> float:
        return self.translatedPercentage

    @property
    def translated_percentage_pretty(self) -> float:
        return round(self.translated_percentage, ndigits=2)

    @property
    def reviewed_percentage(self) -> float:
        return self.reviewedPercentage

    @property
    def reviewed_percentage_pretty(self) -> float:
        return round(self.reviewed_percentage, ndigits=2)

    @property
    def members_count(self) -> int:
        return self.membersCount

    @property
    def tag_count(self) -> int:
        return self.tagCount


# region [Main_Exec]


if __name__ == '__main__':
    pass

# endregion [Main_Exec]
