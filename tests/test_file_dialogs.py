"""A cancelled file or folder dialog does nothing."""

import json

import pytest
from PySide6.QtWidgets import QFileDialog

from windows import data_editor
from windows.common import safe_file_dialog


def test_a_cancelled_folder_dialog_is_a_cancel():
	# getExistingDirectory returns "" when cancelled
	assert safe_file_dialog(lambda caption: "", "pick") == (None, False)


def test_a_cancelled_dialog_returning_none_is_a_cancel():
	assert safe_file_dialog(lambda caption: None, "pick") == (None, False)


def test_a_cancelled_file_dialog_is_a_cancel():
	assert safe_file_dialog(lambda caption: ("", ""), "pick") == (None, False)


def test_a_chosen_folder_is_returned():
	assert safe_file_dialog(lambda caption: "C:/some/folder", "pick") == ("C:/some/folder", True)


def test_a_chosen_file_is_returned():
	assert safe_file_dialog(lambda caption: ("C:/a.json", "JSON (*.json)"), "pick") == (
		"C:/a.json",
		"JSON (*.json)",
	)


def test_a_dialog_that_raises_is_a_cancel():
	def boom(caption):
		raise RuntimeError("no display")

	assert safe_file_dialog(boom, "pick") == (None, False)


@pytest.fixture
def wtt_setup(main_window, tmp_path, monkeypatch):
	"""A data folder holding a saved datafiles.json, and a working folder with a WTT-looking file in it."""
	data_dir = tmp_path / "data"
	data_dir.mkdir()
	saved = '{"CustomItems": ["precious/saved/list.json"]}'
	(data_dir / "datafiles.json").write_text(saved)
	lookalike = {"k": {"locales": {"en": {"name": "N", "shortName": "S", "description": "D"}}}}
	(tmp_path / "CustomItems_here.json").write_text(json.dumps(lookalike))  # in the working folder
	monkeypatch.setattr(data_editor, "DATA_DIR", data_dir)
	return data_dir / "datafiles.json", saved


def test_cancelling_the_wtt_folder_dialog_keeps_the_saved_list(main_window, wtt_setup, monkeypatch):
	datafiles, saved = wtt_setup
	monkeypatch.setattr(QFileDialog, "getExistingDirectory", staticmethod(lambda *a, **k: ""))
	editor = main_window.spawnWindow("DataWindow")
	editor.import_wtt()
	assert datafiles.read_text() == saved
	assert editor.ui.statusbar.currentMessage() == ""
	assert main_window.state.id_search == {}  # and nothing from the working folder was indexed


def test_choosing_a_wtt_folder_still_imports_it(main_window, wtt_setup, tmp_path, monkeypatch):
	datafiles, saved = wtt_setup
	wtt = tmp_path / "wtt" / "CustomItems"
	wtt.mkdir(parents=True)
	(wtt / "items.json").write_text(
		json.dumps({"abc": {"locales": {"en": {"name": "N", "shortName": "S", "description": "D"}}}})
	)
	monkeypatch.setattr(QFileDialog, "getExistingDirectory", staticmethod(lambda *a, **k: str(tmp_path / "wtt")))
	editor = main_window.spawnWindow("DataWindow")
	editor.import_wtt()
	assert datafiles.read_text() != saved
	assert main_window.state.id_search["N"] == "abc"
