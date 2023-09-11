import pytest
from pytest import param
from pytest_lazyfixture import lazy_fixture
from typing import TYPE_CHECKING
from antistasi_translation_sync.stringtable import StringTable, StringtableParser, StringTableKey, StringTableEntry, StringTableContainer, ArmaLanguage, LanguageLike
from contextlib import nullcontext
from ..data import DATA_DIR

if TYPE_CHECKING:
    from .conftest import StringtableObjExpectedResult


test_stringtable_obj_params = [param(lazy_fixture("parsed_simple_stringtable"), lazy_fixture("simple_stringtable_expected_result"), id="simple"),
                               param(lazy_fixture("parsed_intermediate_stringtable"), lazy_fixture("intermediate_stringtable_expected_result"), id="intermediate"),
                               param(lazy_fixture("parsed_complex_stringtable"), lazy_fixture("complex_stringtable_expected_result"), id="complex")]


@pytest.mark.parametrize(["parsed_stringtable", "expected_result"], test_stringtable_obj_params)
def test_stringtable_obj(parsed_stringtable: StringTable, expected_result: "StringtableObjExpectedResult"):
    assert parsed_stringtable.header == expected_result.header

    assert parsed_stringtable.project_name == expected_result.project_name

    assert parsed_stringtable.package_name == expected_result.package_name

    assert parsed_stringtable.name == expected_result.name


@pytest.mark.parametrize(["parsed_stringtable", "expected_result"], test_stringtable_obj_params)
def test_simple_containers(parsed_stringtable: StringTable, expected_result: "StringtableObjExpectedResult"):

    assert len(parsed_stringtable.containers) == expected_result.amount_containers

    container_names = set(c.name for c in parsed_stringtable.containers)

    assert container_names == expected_result.container_names

    for container in parsed_stringtable.containers:
        assert type(container) == StringTableContainer
        assert container.string_table is parsed_stringtable

    new_stringtable = parsed_stringtable.deepcopy()

    new_stringtable.get_or_create_container(container_name="Wurst")

    assert len(new_stringtable.containers) == (expected_result.amount_containers + 1)

    assert len(parsed_stringtable.containers) == (expected_result.amount_containers)


@pytest.mark.parametrize(["parsed_stringtable", "expected_result"], test_stringtable_obj_params)
def test_simple_keys(parsed_stringtable: StringTable, expected_result: "StringtableObjExpectedResult"):

    assert len(parsed_stringtable.get_all_keys()) == expected_result.amount_keys

    all_keys = []
    for container in parsed_stringtable.containers:
        for key in container.keys:
            assert type(key) == StringTableKey
            assert key.container is container
            assert key.container.string_table is parsed_stringtable
            all_keys.append(key)

    assert len(all_keys) == expected_result.amount_keys

    all_key_names = set(k.name for k in all_keys)

    assert all_key_names == expected_result.key_names

    for item in expected_result.example_keys:

        ctx = pytest.raises(item.error) if item.error else nullcontext()
        with ctx:
            key = parsed_stringtable.get_key(item.name)
            if item.language is ArmaLanguage.ORIGINAL:
                assert key.original_text == item.text

            assert key[item.language].text == item.text


@pytest.mark.parametrize(["parsed_stringtable", "expected_result"], test_stringtable_obj_params)
def test_simple_entries(parsed_stringtable: StringTable, expected_result: "StringtableObjExpectedResult"):
    assert len(parsed_stringtable.get_all_entries()) == expected_result.amount_entries

    all_entries = []
    for container in parsed_stringtable.containers:
        for key in container.keys:
            for entry in key.entries:
                assert type(entry) == StringTableEntry
                assert type(entry.language) == ArmaLanguage
                assert entry.key is key
                assert entry.key.container is container
                assert entry.key.container.string_table is parsed_stringtable
                all_entries.append(entry)

    assert len(all_entries) == expected_result.amount_entries
