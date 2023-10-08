import zlib
import importlib.resources as imp_resources
from typing import Union
import json
from functools import cache


def _load_builtin_arma_key_names_from_compressed_data() -> frozenset[str]:

    file = imp_resources.files(__package__).joinpath("builtin_arma_key_names_compressed_data.bin")

    decompressed_data = json.loads(zlib.decompress(file.read_bytes()))

    # text = decompressed_data.decode(encoding='utf-8', errors='ignore')

    # parts = (i.strip().casefold() for i in text.split(";"))

    # return frozenset(i.strip().casefold() for i in zlib.decompress(file.read_bytes()).decode(encoding='utf-8', errors='ignore').split(";"))
    return frozenset(decompressed_data)


get_all_builtin_arma_key_names = _load_builtin_arma_key_names_from_compressed_data
