"""
WiP.

Soon.
"""

# region [Imports]

import os
import re
import sys


from pathlib import Path

from typing import (TYPE_CHECKING, Generator, TypeVar, TypeGuard, TypeAlias, Final, TypedDict, Generic, Union, Optional, ForwardRef, final, Callable,
                    no_type_check, no_type_check_decorator, overload, get_type_hints, cast, Protocol, runtime_checkable, NoReturn, NewType, Literal, AnyStr, IO, BinaryIO, TextIO, Any)
from collections import defaultdict
from .builtin_arma_key_names import get_all_builtin_arma_key_names

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

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


SQF_STRING_NAME_REGEX = re.compile(r'localize +[\'\"](?P<string_name>[\w\_]+)[\'\"]')
CPP_STRING_NAME_REGEX = re.compile(r'\$(?P<string_name>[\w\_]+) *\;')


MULTILINE_COMMMENT_REMOVE_REGEX = re.compile(r"(\/\*).*?(\*\/)", re.DOTALL)
SINGLELINE_COMMENT_REMOVE_REGEX = re.compile(r"(\/\/).*?$")


def iter_file_content_by_semi_colon(in_file_obj: TextIO) -> Generator[str, None, None]:

    def _remove_comment_content(_text: str) -> str:
        _text = MULTILINE_COMMMENT_REMOVE_REGEX.sub("", _text)
        _text = SINGLELINE_COMMENT_REMOVE_REGEX.sub("", _text)
        return _text

    _found = []
    while True:
        _char = in_file_obj.read(1)
        if _char == "":
            break

        _found.append(_char)
        if _char == ";":
            yield _remove_comment_content(''.join(_found))
            _found.clear()

    if _found:
        yield _remove_comment_content(''.join(_found))


class RepoUsageCollector:

    def __init__(self, base_folder: Union[os.PathLike, str, Path]) -> None:
        self.base_folder = Path(base_folder).resolve()
        self._data: defaultdict[str, set[Path]] = defaultdict(set)
        self._missing: set[str] = set()
        self._builtin_arma_key_names: Union[None, frozenset[str]] = None

    @property
    def builtin_arma_key_names(self) -> frozenset[str]:
        if self._builtin_arma_key_names is None:
            self._builtin_arma_key_names = get_all_builtin_arma_key_names()

        return self._builtin_arma_key_names

    def iter_files(self) -> Generator[Path, None, None]:
        allowed_extensions = {".sqf", ".cpp", ".hpp"}
        for dirname, folderlist, filelist in os.walk(self.base_folder):
            for file_name in filelist:
                if os.path.splitext(file_name)[-1] in allowed_extensions:
                    yield Path(dirname, file_name)

    def handle_sqf_file(self, file: Path) -> set[str]:
        found = set()
        with file.open("r", encoding='utf-8', errors='ignore') as f:
            for stmt in iter_file_content_by_semi_colon(f):
                for match in SQF_STRING_NAME_REGEX.finditer(stmt):
                    found.add(match.group("string_name"))

        return {i.casefold() for i in found}.difference(self.builtin_arma_key_names)

    def handle_cpp_and_hpp_file(self, file: Path) -> set[str]:
        found = set()
        with file.open("r", encoding='utf-8', errors='ignore') as f:
            for stmt in iter_file_content_by_semi_colon(f):
                for match in CPP_STRING_NAME_REGEX.finditer(stmt):
                    found.add(match.group("string_name"))

        return {i.casefold() for i in found}.difference(self.builtin_arma_key_names)

    def search(self) -> Self:
        for file in self.iter_files():
            if file.suffix == ".sqf":
                string_names = self.handle_sqf_file(file=file)

            elif file.suffix in {".cpp", ".hpp"}:
                string_names = self.handle_cpp_and_hpp_file(file=file)

            for string_name in string_names:
                self._data[string_name.casefold()].add(file)

        self._missing = {s.casefold() for s in self._data.keys()}
        return self

    def __contains__(self, obj: object) -> bool:
        if isinstance(obj, str):
            _contains = obj.casefold() in self._data.keys()
            try:
                self._missing.remove(obj.casefold())
            except KeyError:
                pass
            return _contains

        return NotImplemented

# region [Main_Exec]


if __name__ == '__main__':
    ...
# endregion [Main_Exec]
