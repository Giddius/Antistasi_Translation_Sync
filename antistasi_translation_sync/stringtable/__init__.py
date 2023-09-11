from .models import StringTable, StringTableContainer, StringTableKey, StringTableEntry, ArmaLanguage, LanguageLike

from .parser import StringtableParser


from typing import Union
import os
from pathlib import Path


def get_and_resolve_stringtable(stringtable_file_path: Union[str, os.PathLike, Path]) -> StringTable:

    stringtable_file_path = Path(stringtable_file_path).resolve()
    parser = StringtableParser()

    stringtable = parser.parse(stringtable_file_path)

    return stringtable
