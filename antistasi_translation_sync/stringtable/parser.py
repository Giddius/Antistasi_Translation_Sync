"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import re
import sys
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING, Any, Union, TextIO
from pathlib import Path
from xml.etree.ElementTree import Element

from .models import StringTable, StringTableKey, StringTableEntry, StringTableContainer

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


class StringtableParser:
    _header_regex: re.Pattern = re.compile(r'\<\?xml *(?P<attributes>(?:(?:[\w\_\-]+)\=(?:\".*?\") *)*)\?\>')

    def __init__(self) -> None:
        self._stringtable_obj: Union["StringTable", None] = None
        self._root: Union[ET.Element, None] = None

    def _resolve_header_from_text(self, text: str) -> None:
        match = self._header_regex.search(text)
        if match:
            header = match.group()
            self._stringtable_obj.header = header

    def _resolve_header_from_file_obj(self, file_obj: TextIO) -> None:
        orig_pos = file_obj.tell()
        file_obj.seek(0)
        for line_number, line in enumerate(file_obj):

            match = self._header_regex.search(line)
            if match:
                header = match.group()
                self._stringtable_obj.header = header
                break

            if line_number >= 10:
                break
        file_obj.seek(orig_pos)

    def _resolve_project_name(self) -> None:

        project_element = self._root if self._root.tag == "Project" else self._root.find("Project")
        if project_element is not None:
            project_name = project_element.get("name")
            self._stringtable_obj.project_name = project_name

    def _resolve_package_name(self) -> None:

        package_element = self._root if self._root.tag == "Package" else self._root.find("Package")
        if package_element is not None:
            package_name = package_element.get("name")
            self._stringtable_obj.package_name = package_name

    def _handle_entry(self, entry_element: ET.Element, key: "StringTableKey") -> None:
        if entry_element.tag.casefold() == "chinese":
            return
        entry = StringTableEntry.from_xml_element(entry_element)
        key.add_entry(entry)

    def _handle_key(self, key_element: ET.Element, container: "StringTableContainer") -> None:

        key = StringTableKey.from_xml_element(key_element)
        container.add_key(key)
        for _entry in key_element.iter():
            if _entry.tag == "Key":
                continue

            self._handle_entry(entry_element=_entry, key=key)

    def _handle_container(self, container_element: ET.Element) -> None:

        container = StringTableContainer.from_xml_element(container_element)
        self._stringtable_obj.add_container(container)

        for _key in container_element.iter("Key"):

            self._handle_key(key_element=_key, container=container)

    def _create_xml_parser(self) -> ET.XMLParser:
        parser = ET.XMLParser(target=ET.TreeBuilder())
        return parser

    def clear(self) -> None:
        self._stringtable_obj = None
        self._root = None

    def parse_text(self, text: str) -> "StringTable":
        self.clear()
        self._stringtable_obj = StringTable()
        self._root = ET.fromstring(text, parser=self._create_xml_parser())

        self._resolve_header_from_text(text)

        self._resolve_project_name()
        self._resolve_package_name()

        for _container in self._root.iter("Container"):
            self._handle_container(container_element=_container)

        return self._stringtable_obj

    def parse_file_obj(self, file_obj: TextIO) -> "StringTable":
        self.clear()

        self._stringtable_obj = StringTable()
        self._root = ET.parse(file_obj, parser=self._create_xml_parser()).getroot()

        self._resolve_header_from_file_obj(file_obj=file_obj)

        self._resolve_project_name()
        self._resolve_package_name()

        for _container in self._root.iter("Container"):
            self._handle_container(container_element=_container)

        return self._stringtable_obj

    def parse_file(self, file: Union[str, os.PathLike, Path]) -> "StringTable":
        with open(file, "r", encoding='utf-8', errors='ignore') as f:
            return self.parse_file_obj(f)

    def parse(self, stringtable: Union[str, TextIO, Path, os.PathLike]) -> "StringTable":
        if isinstance(stringtable, TextIO):
            return self.parse_file_obj(stringtable)

        if isinstance(stringtable, Path):
            return self.parse_file(stringtable)
        if isinstance(stringtable, str):
            if len(stringtable.splitlines()) == 1 and os.path.exists(stringtable):
                return self.parse_file(stringtable)

            else:
                return self.parse_text(stringtable)


# region [Main_Exec]
if __name__ == '__main__':
    pass

# endregion [Main_Exec]
