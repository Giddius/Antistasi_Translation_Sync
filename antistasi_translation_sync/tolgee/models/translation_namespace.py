"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import sys
from typing import TYPE_CHECKING, Union, Unpack
from pathlib import Path
from weakref import proxy

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from .translation_key import TranslationKey

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


class TranslationNamespace:

    __slots__ = ("_namespace_id",
                 "_name",
                 "_project",
                 "_client",
                 "_key_map")

    def __init__(self,
                 namespace_id: int,
                 name: str,
                 project: "Project",
                 client: "TolgeeClient") -> None:
        self._namespace_id: int = namespace_id
        self._name: str = name
        self._project = project
        self._client: Union["TolgeeClient", None] = client
        self._key_map: dict[str, "TranslationKey"] = {}

    @property
    def namespace_id(self) -> int:
        return self._namespace_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def project(self) -> "Project":
        return self._project

    @classmethod
    def from_response_data(cls, client: "TolgeeClient" = None, **response_data: Unpack[dict[str, object]]) -> Self:
        client = proxy(client) if client is not None else client
        return cls(namespace_id=response_data["id"], name=response_data["name"], client=client)

    def add_key(self, key: "TranslationKey") -> None:
        if key.name in self._key_map:
            raise RuntimeError(f"key {key.name!r} already is in {self!r}.")
        self._key_map[key.name] = key

    def remove_key(self, key: Union[str, "TranslationKey"]) -> None:
        if isinstance(key, str):
            del self._key_map[key]

        else:
            del self._key_map[key.name]

    def __getitem__(self, name: str) -> "TranslationKey":
        return self._key_map[name]

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.namespace_id == other.namespace_id and self.name == other.name

        return NotImplemented

    def __hash__(self) -> int:
        return self.namespace_id

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(namespace_id={self.namespace_id!r}, name={self.name!r})"
# region [Main_Exec]


if __name__ == '__main__':
    pass

# endregion [Main_Exec]
