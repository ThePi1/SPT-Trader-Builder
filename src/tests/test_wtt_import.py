"""Importing a WTT folder: what the status bar reports, and what is saved."""

import json

import pytest
from PySide6.QtWidgets import QFileDialog

from modules.utils import read_json
from modules.windows import data_editor

ITEM = {"locales": {"en": {"name": "N", "shortName": "S", "description": "D"}}}


@pytest.fixture
def importer(main_window, tmp_path, monkeypatch):
	"""Returns a function that imports a WTT folder and gives back (status bar text, saved datafiles.json)."""
	data_dir = tmp_path / "data"
	data_dir.mkdir()
	monkeypatch.setattr(data_editor, "DATA_DIR", data_dir)

	def run(folder):
		monkeypatch.setattr(QFileDialog, "getExistingDirectory", staticmethod(lambda *a, **k: str(folder)))
		editor = main_window.spawnWindow("DataWindow")
		editor.import_wtt()
		saved = read_json(data_dir / "datafiles.json")
		return editor.ui.statusbar.currentMessage(), saved

	return run


def make_files(root, names):
	"""Create WTT-style item files (names are relative paths such as 'CustomItems/a.json')."""
	for name in names:
		path = root / name
		path.parent.mkdir(parents=True, exist_ok=True)
		path.write_text(json.dumps({name.replace("/", "_"): ITEM}), encoding="utf-8")
	return root


def test_the_status_counts_the_files_loaded(importer, tmp_path):
	root = make_files(tmp_path / "wtt", ["CustomItems/a.json", "CustomItems/b.json"])
	message, saved = importer(root)
	assert message == "Loaded 2 data files."
	assert len(saved["CustomItems"]) == 2


def test_one_file_is_singular(importer, tmp_path):
	message, _ = importer(make_files(tmp_path / "wtt", ["CustomItems/a.json"]))
	assert message == "Loaded 1 data file."


def test_the_count_adds_up_across_categories(importer, tmp_path):
	root = make_files(tmp_path / "wtt", ["CustomItems/a.json", "CustomLocales/b.json", "CustomQuestZones/c.json"])
	message, saved = importer(root)
	assert message == "Loaded 3 data files."
	assert sorted(saved) == ["CustomItems", "CustomLocales", "CustomQuestZones"]


def test_the_root_folder_itself_is_not_counted_as_a_file(importer, tmp_path):
	message, _ = importer(make_files(tmp_path / "wtt", ["CustomItems/a.json"]))
	assert "1 data file" in message  # (it used to add the folder's entry and the length of the names)


def test_a_file_matching_two_categories_is_counted_once(importer, tmp_path):
	# its path contains both "CustomItems" and "CustomLocales"
	root = make_files(tmp_path / "wtt", ["CustomItems/CustomLocales/a.json"])
	message, saved = importer(root)
	assert message == "Loaded 1 data file."
	assert len(saved["CustomItems"]) == 1 and len(saved["CustomLocales"]) == 1


def test_files_that_are_not_wtt_data_are_not_counted(importer, tmp_path):
	root = make_files(tmp_path / "wtt", ["CustomItems/a.json", "readme/notes.json"])
	message, _ = importer(root)
	assert message == "Loaded 1 data file."


def test_a_folder_with_nothing_to_load_reports_zero(importer, tmp_path):
	(tmp_path / "empty").mkdir()
	message, saved = importer(tmp_path / "empty")
	assert message == "Loaded 0 data files." and saved == {}


def test_a_file_that_cannot_be_read_is_skipped_and_not_counted(importer, tmp_path):
	root = make_files(tmp_path / "wtt", ["CustomItems/good.json"])
	(root / "CustomItems" / "bad.json").write_text("{ not json", encoding="utf-8")
	message, saved = importer(root)
	assert message == "Loaded 1 data file."
	assert len(saved["CustomItems"]) == 1


def test_a_folder_with_russian_letters_in_its_name_is_saved_readably(importer, tmp_path):
	root = make_files(tmp_path / "Папка мода", ["CustomItems/a.json"])
	message, saved = importer(root)
	assert message == "Loaded 1 data file."
	assert "Папка мода" in saved["CustomItems"][0]


def test_importing_twice_does_not_double_the_count(importer, tmp_path):
	root = make_files(tmp_path / "wtt", ["CustomItems/a.json", "CustomItems/b.json"])
	importer(root)
	message, _ = importer(root)
	assert message == "Loaded 2 data files."
