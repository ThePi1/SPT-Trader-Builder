"""Assort item names come from ab_itemName_reference.json, which is read once."""

import json

import pytest

from paths import DATA_DIR
from windows import assort
from windows.assort import Gui_AssortDlg


@pytest.fixture
def reference(tmp_path, monkeypatch):
	"""Point the assort window at a small reference file in a temp data folder."""
	data = {
		"items": [
			{"id": "a", "name": "Alpha"},
			{"id": "b", "name": "Bravo"},
			{"id": "a", "name": "Alpha again"},
			{"id": "noname"},
		]
	}
	(tmp_path / "ab_itemName_reference.json").write_text(json.dumps(data), encoding="utf-8")
	monkeypatch.setattr(assort, "DATA_DIR", tmp_path)
	return tmp_path


def test_known_ids_return_their_names(reference):
	assert Gui_AssortDlg.itemDatabase("b") == "Bravo"


def test_unknown_ids_return_the_id_itself(reference):
	assert Gui_AssortDlg.itemDatabase("zzz") == "zzz"


def test_the_first_entry_wins_for_a_repeated_id(reference):
	assert Gui_AssortDlg.itemDatabase("a") == "Alpha"


def test_an_entry_without_a_name_gives_an_empty_name(reference):
	assert Gui_AssortDlg.itemDatabase("noname") == ""


def test_the_file_is_only_read_once(reference):
	before = assort._load_item_names.cache_info()
	for _ in range(50):
		Gui_AssortDlg.itemDatabase("a")
		Gui_AssortDlg.itemDatabase("missing")
	after = assort._load_item_names.cache_info()
	assert after.misses - before.misses == 1
	assert after.hits - before.hits == 99


def test_matches_the_old_scan_on_the_real_file():
	reference_file = json.loads(
		(DATA_DIR / "ab_itemName_reference.json").read_text(encoding="utf-8")
	)

	def old_lookup(tpl):
		for item in reference_file.get("items", []):
			if tpl == item.get("id", ""):
				return item.get("name", "")
		return tpl

	ids = [item.get("id", "") for item in reference_file["items"]]
	for tpl in ids[::25] + ids[:20] + ids[-20:] + ["not-an-id", ""]:
		assert Gui_AssortDlg.itemDatabase(tpl) == old_lookup(tpl)
