from core.library import Library, preset_parts
from schema import assort


def parts():
	return [{"_id": "a" * 24, "_tpl": "b" * 24}, {"_id": "c" * 24, "_tpl": "d" * 24, "parentId": "a" * 24, "slotId": "mod_x"}]


def test_save_load_and_new_ids(tmp_path):
	lib = Library(tmp_path / "lib.json")
	entry = lib.add("My gun", parts())
	assert Library(tmp_path / "lib.json").entries[entry]["name"] == "My gun"
	copy = lib.parts_of(entry)
	assert copy[0]["_id"] != "a" * 24 and copy[1]["parentId"] == copy[0]["_id"]
	assert not assort.validate_composite(lib.entries[entry])
	lib.update(entry, name="Renamed")
	assert lib.names() == [(entry, "Renamed")]
	lib.remove(entry)
	assert not lib.entries


def test_bad_file_gives_empty_library(tmp_path):
	(tmp_path / "lib.json").write_text("not json")
	assert Library(tmp_path / "lib.json").entries == {}


def test_preset_parts_keeps_links():
	preset = {"_items": [{"_id": "a" * 24, "_tpl": "b" * 24}, {"_id": "c" * 24, "_tpl": "d" * 24, "parentId": "a" * 24, "slotId": "s"}], "_name": "x"}
	got = preset_parts(preset)
	assert got[1]["parentId"] == got[0]["_id"] != "a" * 24
