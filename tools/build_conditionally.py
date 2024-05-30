"""
WiP.

Soon.
"""

# region [Imports]

import os
import re
import sys
import json


import subprocess


from pathlib import Path

from typing import TYPE_CHECKING, Callable, Optional, Union
import dataclasses

from contextlib import contextmanager

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Future, wait, as_completed, ALL_COMPLETED, FIRST_EXCEPTION, FIRST_COMPLETED
import atexit

import hashlib


if TYPE_CHECKING:
    ...

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR: Path = Path(__file__).parent.absolute().resolve()


# endregion [Constants]

@dataclasses.dataclass(frozen=True, slots=True)
class BuildVariant:
    mod_name: str = dataclasses.field(hash=True)
    workshop_id: str = dataclasses.field(hash=True)
    key_name: str = dataclasses.field(hash=True)


DEFAULT_BUILD_VARIANT = BuildVariant(mod_name="", workshop_id="", key_name="a3a")

BUILD_VARIANTES = frozenset([BuildVariant(mod_name="Antistasi - The Mod", workshop_id="2867537125", key_name="antistasi"),
                             BuildVariant(mod_name="[Dev1] Antistasi Dev Build", workshop_id="2729074499", key_name="antistasi_dev1"),
                             BuildVariant(mod_name="[Dev2] Antistasi Dev Build", workshop_id="2873632521", key_name="antistasi_dev2"),
                             DEFAULT_BUILD_VARIANT])


def variant_from_workshop_id(workshop_id: Optional[str] = None) -> "BuildVariant":
    if workshop_id is None:
        return DEFAULT_BUILD_VARIANT

    return {variant.workshop_id: variant for variant in BUILD_VARIANTES}[workshop_id]


@contextmanager
def context_chdir(new_dir: str | os.PathLike):
    old_cwd = Path.cwd()

    new_cwd = Path(new_dir).resolve()

    os.chdir(new_cwd)
    yield

    os.chdir(old_cwd)


class ImportantPaths:
    __slots__ = ("repository_folder",
                 "source_folder",
                 "build_folder",
                 "target_folder",
                 "pbo_folder",
                 "keys_folder",
                 "version_file",
                 "meta_file",
                 "build_hashes_file",
                 "hemtt_exe_file",
                 "create_key_exe",
                 "sign_file_exe")

    def __init__(self) -> None:
        self.repository_folder: Path = self._determine_repository_folder()
        self.source_folder: Path = self.repository_folder.joinpath("A3A")
        self.build_folder: Path = self.repository_folder.joinpath("build")
        self.target_folder: Path = self.build_folder.joinpath("A3A")
        self.pbo_folder: Path = self.target_folder.joinpath("addons")
        self.keys_folder: Path = self.target_folder.joinpath("Keys")
        self.version_file: Path = self._find_specific_file("script_version.hpp")
        self.build_hashes_file = self.build_folder.joinpath("build_hashes.json")
        self.meta_file = self.target_folder.joinpath("meta.cpp")

        self.hemtt_exe_file = self._find_specific_file("hemtt.exe")
        self.create_key_exe = self._find_specific_file("DSCreateKey.exe")
        self.sign_file_exe = self._find_specific_file("DSSignFile.exe")

    @staticmethod
    def _determine_repository_folder() -> Path:

        def _search_for_git_folder(directory: Path, level=0):
            if level >= 4:
                return None

            sub_folder_names = {folder.name.casefold() for folder in directory.iterdir() if folder.is_dir()}
            sub_file_names = {file.name.casefold() for file in directory.iterdir() if file.is_file()}

            if all(['.git' in sub_folder_names, '.gitignore' in sub_file_names, 'readme.md' in sub_file_names]):
                return directory.resolve()

            return _search_for_git_folder(directory.parent, level=level + 1)
        for start_dir in (Path.cwd(), THIS_FILE_DIR):
            maybe_repo_folder = _search_for_git_folder(start_dir)
            if maybe_repo_folder is not None:
                return maybe_repo_folder

        raise FileNotFoundError("Unable to determine repository Path.")

    def _find_specific_file(self, in_file_name: str, start_folder: Path = None) -> Path:
        _in_file_name = in_file_name.casefold()
        start_folder = start_folder or self.repository_folder
        for dirname, folderlist, filelist in start_folder.walk():
            for file_name in filelist:
                if file_name.casefold() == _in_file_name:
                    return Path(dirname, file_name).resolve()

        raise FileNotFoundError(f"Unable to find file {in_file_name!r}.")


IMPORTANT_PATHS = ImportantPaths()


def get_version():
    parse_pattern = re.compile(r"\#define (?P<name>\w+) (?P<value>\w+)")

    version_parts = []
    with IMPORTANT_PATHS.version_file.open("r", encoding='utf-8', errors='ignore') as f:
        for line in (raw_line.strip() for raw_line in f):
            if match := parse_pattern.match(line):

                version_parts.append(match.group("value").strip())

    return "-".join(version_parts)


def ensure_target_paths():
    IMPORTANT_PATHS.build_folder.mkdir(exist_ok=True, parents=True)
    IMPORTANT_PATHS.target_folder.mkdir(exist_ok=True, parents=True)
    IMPORTANT_PATHS.pbo_folder.mkdir(exist_ok=True, parents=True)
    IMPORTANT_PATHS.keys_folder.mkdir(exist_ok=True, parents=True)


def load_existing_hashes():

    if not IMPORTANT_PATHS.build_hashes_file.exists():
        return

    with IMPORTANT_PATHS.build_hashes_file.open("r", encoding='utf-8', errors='ignore') as f:
        data = json.load(f)

    return data


FILE_HASH_INCREMENTAL_THRESHOLD: int = 2621440  # 2.5mb


def _hash_file(in_file: Path, hash_algo: Callable = hashlib.blake2b) -> str:
    if in_file.stat().st_size > FILE_HASH_INCREMENTAL_THRESHOLD:
        _hash = hash_algo(usedforsecurity=False)
        with in_file.open("rb", buffering=FILE_HASH_INCREMENTAL_THRESHOLD // 4) as f:
            for chunk in f:
                _hash.update(chunk)
        return _hash.hexdigest()

    return hash_algo(in_file.read_bytes(), usedforsecurity=False).hexdigest()


def calculate_hashes_for_files(pbo_name: str) -> dict[str, str]:
    data = {}
    for dirname, folderlist, filelist in os.walk(IMPORTANT_PATHS.source_folder.joinpath("addons", pbo_name)):
        for file_name in filelist:
            file_path = Path(dirname, file_name).resolve()
            data[file_path.as_posix()] = _hash_file(file_path)

    return data


def calculate_hash_for_existing_pbo(pbo_file: Path) -> str:
    return _hash_file(pbo_file)


def check_rebuild(existing_hash_data, addon_name: str):
    existing_addon_hashes = existing_hash_data.get(addon_name, {}).get("files")

    existing_pbo_hash = existing_hash_data.get(addon_name, {}).get("pbo")
    pbo_file = IMPORTANT_PATHS.pbo_folder.joinpath(f"{addon_name}.pbo")
    if existing_pbo_hash is None or pbo_file.exists() is False or existing_pbo_hash != calculate_hash_for_existing_pbo(pbo_file):
        return addon_name

    if existing_addon_hashes is None:
        return addon_name

    new_addon_hashes = calculate_hashes_for_files(addon_name)

    if set(existing_addon_hashes) != set(new_addon_hashes):
        return addon_name

    if any(hash_value != existing_addon_hashes.get(sub_path) for sub_path, hash_value in new_addon_hashes.items()):
        return addon_name


def get_conditional_build_names(existing_hash_data: dict[str, dict[str, str]]):
    tasks: list[Future] = []

    with ThreadPoolExecutor() as pool:
        for addon_name in (folder.name for folder in IMPORTANT_PATHS.source_folder.joinpath("addons").iterdir() if folder.is_dir()):
            tasks.append(pool.submit(check_rebuild, existing_hash_data, addon_name))

        finished, _ = wait(tasks, return_when=ALL_COMPLETED)
        return [task.result() for task in finished if task.result() is not None]


def build_pbo(pbo_name: str):
    pbo_path = IMPORTANT_PATHS.pbo_folder.joinpath(f"{pbo_name}.pbo")
    pbo_path.unlink(missing_ok=True)

    subprocess.run([IMPORTANT_PATHS.hemtt_exe_file, "armake", "pack", "--force", IMPORTANT_PATHS.source_folder.joinpath("addons").joinpath(pbo_name), pbo_path], check=True)


def build_bikey() -> tuple[Path, Path]:

    KEY_NAME = "a3a"
    for file in IMPORTANT_PATHS.keys_folder.iterdir():
        file.unlink(missing_ok=True)

    with context_chdir(IMPORTANT_PATHS.keys_folder):
        subprocess.run([IMPORTANT_PATHS.create_key_exe, KEY_NAME], check=True, text=True, capture_output=True)

    public_key_file = IMPORTANT_PATHS.keys_folder.joinpath(f"{KEY_NAME}.bikey")
    private_key_file = IMPORTANT_PATHS.keys_folder.joinpath(f"{KEY_NAME}.biprivatekey")

    atexit.register(private_key_file.unlink, True)

    return public_key_file, private_key_file


def build_bisign(pbo_name: str, private_key_file: Path):
    bisign_path = IMPORTANT_PATHS.pbo_folder.joinpath(f"{pbo_name}.pbo.a3a.bisign")
    bisign_path.unlink(missing_ok=True)

    pbo_path = IMPORTANT_PATHS.pbo_folder.joinpath(f"{pbo_name}.pbo")
    subprocess.run([IMPORTANT_PATHS.sign_file_exe, private_key_file, pbo_path])


def get_all_possible_pbo_names() -> tuple[str]:
    return tuple([folder.name for folder in IMPORTANT_PATHS.source_folder.joinpath("addons").iterdir() if folder.is_dir()])


def create_meta_cpp():
    with IMPORTANT_PATHS.meta_file.open("w", encoding='utf-8', errors='ignore') as f:
        f.write("protocol = 1;")


def create_mod_cpp():
    with IMPORTANT_PATHS.target_folder.joinpath("mod.cpp").open("w", encoding='utf-8', errors='ignore') as f_src:
        with IMPORTANT_PATHS._find_specific_file("mod.cpp", IMPORTANT_PATHS.source_folder).open("r", encoding='utf-8', errors='ignore') as f_tgt:
            for line in f_tgt:
                f_src.write(line)


def handle_pbo_helper(pbo_name: str, private_key_file: Path, should_rebuild: bool):
    if should_rebuild:
        print(f"building '{pbo_name}.pbo'", flush=True)
        build_pbo(pbo_name=pbo_name)

    build_bisign(pbo_name=pbo_name, private_key_file=private_key_file)

    return {pbo_name: {"files": calculate_hashes_for_files(pbo_name=pbo_name),
            "pbo": calculate_hash_for_existing_pbo(IMPORTANT_PATHS.pbo_folder.joinpath(f"{pbo_name}.pbo"))}}


def main():
    version = get_version()
    print(f"building version {version!r}", flush=True)

    ensure_target_paths()

    existing_hash_data = load_existing_hashes()

    create_meta_cpp()
    create_mod_cpp()

    if existing_hash_data is None:
        build_names = get_all_possible_pbo_names()

    else:
        build_names = get_conditional_build_names(existing_hash_data=existing_hash_data)

    public_key_file, private_key_file = build_bikey()

    tasks = []
    with ThreadPoolExecutor() as pool:
        for pbo_name in get_all_possible_pbo_names():
            tasks.append(pool.submit(handle_pbo_helper, pbo_name, private_key_file, pbo_name in build_names))

        new_hash_data = {}
        for _task in wait(tasks, return_when=ALL_COMPLETED)[0]:
            new_hash_data |= _task.result()

    with IMPORTANT_PATHS.build_hashes_file.open("w", encoding='utf-8', errors='ignore') as f:
        json.dump(new_hash_data, f, indent=4, default=str)


# region [Main_Exec]
if __name__ == '__main__':
    main()


# endregion [Main_Exec]
