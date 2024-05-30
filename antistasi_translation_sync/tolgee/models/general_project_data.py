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
class GeneralOrganizationData:
    organization_id: int = dataclasses.field(hash=True, compare=True, repr=True)
    name: str = dataclasses.field(hash=False, compare=False, repr=True)
    slug: str = dataclasses.field(hash=False, compare=False, repr=False)
    description: str = dataclasses.field(hash=False, compare=False, repr=False, default="")


@dataclasses.dataclass(frozen=True, slots=True, weakref_slot=True, order=True)
class GeneralProjectData:
    project_id: int = dataclasses.field(hash=True, compare=True, repr=True)
    name: str = dataclasses.field(hash=False, compare=False, repr=True)
    slug: str = dataclasses.field(hash=False, compare=False, repr=False)
    project_url: str = dataclasses.field(hash=True, compare=False, repr=False)
    organization: GeneralOrganizationData = dataclasses.field(hash=True, compare=True, repr=True)
    description: str = dataclasses.field(hash=False, compare=False, repr=False, default="")
    avatar_url: Union[str, None] = dataclasses.field(hash=False, compare=False, repr=False, default=None)
    avatar_thumbnail_url: Union[str, None] = dataclasses.field(hash=False, compare=False, repr=False, default=None)


class ProjectRepository:

    __slots__ = ("_projects",
                 "_organizations")

    def __init__(self) -> None:
        self._projects: set["GeneralProjectData"] = set()
        self._organizations: set["GeneralOrganizationData"] = set()

    @property
    def projects(self) -> tuple["GeneralProjectData"]:
        return tuple(sorted(self._projects))

    @property
    def organizations(self) -> tuple["GeneralOrganizationData"]:
        return tuple(sorted(self._organizations))

    def add_project(self, project: "GeneralProjectData") -> None:
        self._projects.add(project)
        self._organizations.add(project.organization)

    def get_projects_by_organization_name(self, organization_name: str) -> tuple["GeneralProjectData"]:
        return tuple(sorted(p for p in self._projects if p.organization.name == organization_name or p.organization.name.casefold() == organization_name.casefold()))

    def get_project_by_name(self, project_name: str, organization_name: str = None) -> "GeneralProjectData":
        projects = self.projects if organization_name is None else self.get_projects_by_organization_name(organization_name)

        return {p.name.casefold(): p for p in projects}[project_name.casefold()]

    def __repr__(self) -> str:

        return f"{self.__class__.__name__}(projects={self.projects!r})"


# region [Main_Exec]


if __name__ == '__main__':
    pass

# endregion [Main_Exec]
