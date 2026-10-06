"""The "Load last files on open" setting: the files each section was opened from or saved to are kept, and opened again at start."""

import json
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication, QMessageBox

from core import merge as M
from core.documents import Document
from core.gamedata import GameData
from core.last_files import LastFiles
from core.paths import BUNDLED_DATABASE_DIR
from core.settings import BY_KEY, Settings
from schema import assort as A
from ui import dialogs, updates
from ui.main_window import MainWindow

QID, TPL, TRADER = "a" * 24, "5449016a4bdc2d6f028b456f", "5a7c2eca46aef81a7ca2145d"


@pytest.fixture(scope="module")
def app():
	return QApplication.instance() or QApplication([])


def files(folder):
	"""A quest file, its locale, a trader assort (in a trader's folder) and a quest assort."""
	folder.mkdir(parents=True, exist_ok=True)
	items, barter, level = A.new_offer(TPL)
	paths = {
		"quests": folder / "quests.json", "locale": folder / "en.json",
		"assort": folder / "traders" / TRADER / "assort.json", "locks": folder / "questassort.json",
	}
	paths["assort"].parent.mkdir(parents=True, exist_ok=True)
	paths["quests"].write_text(json.dumps({QID: {"_id": QID, "QuestName": "Kept", "conditions": {}, "rewards": {}}}), encoding="utf-8")
	paths["locale"].write_text(json.dumps({f"{QID} name": "Kept"}), encoding="utf-8")
	paths["assort"].write_text(json.dumps({"items": items, "barter_scheme": {items[0]["_id"]: barter}, "loyal_level_items": {items[0]["_id"]: level}}), encoding="utf-8")
	paths["locks"].write_text(json.dumps({"started": {}, "success": {items[0]["_id"]: QID}, "fail": {}}), encoding="utf-8")
	return paths


def make_window(tmp_path, monkeypatch, enabled=True):
	monkeypatch.setattr("core.references.REFERENCES_FILE", tmp_path / "references.json")
	monkeypatch.setattr("core.last_files.LAST_FILES_FILE", tmp_path / "last_files.json")
	monkeypatch.setattr(updates, "fetch_remote_version", lambda config: None)
	monkeypatch.setattr("ui.main_window.QMessageBox.question", lambda *a, **k: QMessageBox.StandardButton.Discard)
	monkeypatch.setattr("ui.main_window.QInputDialog.getItem", lambda parent, title, text, items, start, editable: (items[start], True))  # (the trader question: the guess)
	settings = Settings(path=None)
	settings.load_last_files = enabled
	return MainWindow(settings, GameData(None, "en", BUNDLED_DATABASE_DIR))


# --- the setting ---------------------------------------------------------------------------------

def test_the_setting_exists_is_off_by_default_and_is_in_the_settings_window(app):
	assert BY_KEY["load_last_files"].default is False and BY_KEY["load_last_files"].kind == "bool"
	assert Settings().load_last_files is False  # (a missing entry is off)
	dialog = dialogs.SettingsDialog(Settings(), None)
	assert "load_last_files" in dialog.controls and dialogs._LABELS["load_last_files"] == "Load last files on open"


def test_the_list_of_last_files_is_read_and_written_safely(tmp_path):
	last = LastFiles(tmp_path / "last_files.json")
	assert last.read() == {}
	last.write({"quests": "a.json", "locale": None, "assort": "c.json", "locks": None})
	assert last.read() == {"quests": "a.json", "assort": "c.json"}  # (a section with no file is left out)
	(tmp_path / "last_files.json").write_text("not json", encoding="utf-8")
	assert last.read() == {}
	(tmp_path / "last_files.json").write_text(json.dumps({"quests": 5, "other": "x"}), encoding="utf-8")
	assert last.read() == {}


# --- keeping track -----------------------------------------------------------------------------------

def test_the_file_of_each_section_is_kept_as_it_is_opened_saved_or_started_again(app, tmp_path, monkeypatch):
	paths = files(tmp_path / "mod")
	window = make_window(tmp_path, monkeypatch)
	window.open_quests(paths["quests"])
	window.open_locale(paths["locale"])
	window._open_other("assort", paths["assort"])
	window._open_other("locks", paths["locks"])
	last = LastFiles(tmp_path / "last_files.json")
	assert {k: v.replace("\\", "/") for k, v in last.read().items()} == {k: str(p).replace("\\", "/") for k, p in paths.items()}
	window.new_quests()  # (started again from nothing: no file to open next time)
	assert "quests" not in last.read() and "locale" in last.read()
	monkeypatch.setattr("ui.main_window.QFileDialog.getSaveFileName", lambda *a, **k: (str(tmp_path / "saved.json"), ""))
	window.save_quests_as()
	assert last.read()["quests"] == str(tmp_path / "saved.json")
	window.close()


def test_nothing_is_kept_while_the_setting_is_off(app, tmp_path, monkeypatch):
	paths = files(tmp_path / "mod")
	window = make_window(tmp_path, monkeypatch, enabled=False)
	window.open_quests(paths["quests"])
	window.close()
	assert not (tmp_path / "last_files.json").exists() and window.restore_last_files() == []


def test_importing_a_file_is_not_part_of_it(app, tmp_path, monkeypatch):
	from ui.import_dialog import ImportDialog

	paths = files(tmp_path / "mod")
	window = make_window(tmp_path, monkeypatch)
	monkeypatch.setattr(ImportDialog, "exec", lambda self: True)
	window.import_files([str(paths["quests"]), str(paths["locale"])])
	assert window.quests.data and LastFiles(tmp_path / "last_files.json").read() == {}  # (imported, so nothing was opened)
	window.close()


# --- opening them again ------------------------------------------------------------------------------------

def test_the_files_are_opened_again_at_start_and_the_trader_is_asked_for(app, tmp_path, monkeypatch):
	paths = files(tmp_path / "mod")
	first = make_window(tmp_path, monkeypatch)
	for key, opener in (("quests", first.open_quests), ("locale", first.open_locale)):
		opener(paths[key])
	first._open_other("assort", paths["assort"])
	first._open_other("locks", paths["locks"])
	first.close()
	asked = []
	second = make_window(tmp_path, monkeypatch)
	monkeypatch.setattr("ui.main_window.QInputDialog.getItem", lambda parent, title, text, items, start, editable: asked.append(items[start]) or (items[start], True))
	assert second.quests.path is None and second.restore_last_files() == [str(paths[k]) for k in ("quests", "locale", "assort", "locks")]
	assert second.quests.path == paths["quests"] and second.locale.path == paths["locale"] and second.assort.path == paths["assort"] and second.locks.path == paths["locks"]
	assert list(second.quests.data) == [QID] and len(A.offer_ids(second.assort.data)) == 1 and not second.quests.dirty
	assert asked == ["Mechanic"] and second.assort_tab.trader_id == TRADER  # (the same question as Open: the folder says Mechanic)
	assert LastFiles(tmp_path / "last_files.json").read() == {k: str(p) for k, p in paths.items()}  # (still kept: nothing was forgotten on the way)
	second.close()


def test_a_file_that_is_gone_is_skipped_and_the_others_still_open(app, tmp_path, monkeypatch):
	paths = files(tmp_path / "mod")
	first = make_window(tmp_path, monkeypatch)
	first.open_quests(paths["quests"])
	first.open_locale(paths["locale"])
	first.close()
	paths["quests"].unlink()
	second = make_window(tmp_path, monkeypatch)
	assert second.restore_last_files() == [str(paths["locale"])]
	assert second.quests.path is None and second.locale.path == paths["locale"]
	assert "quests.json" in second.statusBar().currentMessage()
	assert LastFiles(tmp_path / "last_files.json").read() == {"locale": str(paths["locale"])}
	second.close()


def test_nothing_is_opened_when_the_setting_is_off(app, tmp_path, monkeypatch):
	paths = files(tmp_path / "mod")
	LastFiles(tmp_path / "last_files.json").write({"quests": str(paths["quests"])})
	window = make_window(tmp_path, monkeypatch, enabled=False)
	assert window.restore_last_files() == [] and window.quests.path is None
