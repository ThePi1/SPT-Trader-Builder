"""Importing files into what is open, the files strip, the title, and the Save setting (ui/main_window.py)."""

import json
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtCore import QMimeData, QPointF, Qt, QUrl
from PySide6.QtGui import QDropEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QCheckBox

from core import merge as M
from core.documents import Document
from core.gamedata import GameData
from core.paths import BUNDLED_DATABASE_DIR
from core.settings import Settings
from schema import assort as A
from ui import dialogs, updates
from ui.files_strip import FileSegment
from ui.import_dialog import COLUMNS, ImportDialog
from ui.main_window import MainWindow

Q1, Q2, Q3, T1, T2, T3 = "a" * 24, "b" * 24, "9" * 24, "c" * 24, "d" * 24, "8" * 24
OFFER, ITEM = "e" * 24, "1" * 24


@pytest.fixture(scope="module")
def app():
	return QApplication.instance() or QApplication([])


def quest(quest_id, name, task_id):
	return {
		"_id": quest_id, "QuestName": name, "name": f"{quest_id} name", "description": f"{quest_id} description",
		"conditions": {"AvailableForStart": [], "Fail": [], "AvailableForFinish": [{"id": task_id, "conditionType": "Level", "value": 5, "compareMethod": ">="}]},
		"rewards": {"Success": [], "Started": [], "Fail": []},
	}


def write(folder, name, data):
	path = folder / name
	path.write_text(json.dumps(data), encoding="utf-8")
	return path


@pytest.fixture
def window(app, tmp_path, monkeypatch):
	monkeypatch.setattr(updates, "fetch_remote_version", lambda config: None)
	monkeypatch.setattr("ui.main_window.QMessageBox.question", lambda *a, **k: dialogs.QMessageBox.StandardButton.Discard)
	win = MainWindow(Settings.load(tmp_path / "none.ini"), GameData(None, "en", BUNDLED_DATABASE_DIR))
	monkeypatch.setattr(ImportDialog, "exec", lambda self: True)  # (accept the import window as it opens)
	yield win
	win.close()


def files(tmp_path):
	"""Four files of a small mod: two quest files, their text, and an offer with its lock."""
	mod = tmp_path / "mod"
	mod.mkdir(exist_ok=True)
	assort = A.empty_assort()
	A.add_offer(assort, *A.new_offer(ITEM, ids=lambda: OFFER))
	return [
		write(mod, "kappa.json", {Q1: quest(Q1, "One", T1)}),
		write(mod, "side_jobs.json", {Q2: quest(Q2, "Two", T2)}),
		write(mod, "en.json", {f"{Q1} name": "One", f"{Q2} name": "Two", T2: "do it", "vanilla": "x"}),
		write(mod, "assort.json", assort),
		write(mod, "locks.json", {"started": {}, "success": {OFFER: Q1}, "fail": {}}),
	]


def segment_text(window, key):
	segment = window.files_strip.segment(key)
	return segment.titleLabel.text(), segment.stateLabel.text(), segment.fileLabel.text()


# --- importing ------------------------------------------------------------------------------

def test_five_files_import_into_one_workspace(window, tmp_path):
	plan = window.import_files(files(tmp_path))
	assert plan is not None
	assert set(window.quests.data) == {Q1, Q2} and A.offer_ids(window.assort.data) == [OFFER]
	assert window.locks.data["success"] == {OFFER: Q1}
	assert window.locale.data == {f"{Q1} name": "One", f"{Q2} name": "Two", T2: "do it"}  # (only the text of the quests)
	assert window.quest_sources == {Q1: "kappa.json", Q2: "side_jobs.json"}
	assert window.imported["quests"] == ["kappa.json", "side_jobs.json"] and window.imported["locale"] == ["en.json"]
	assert "Imported 2 quests" in window.statusBar().currentMessage()
	assert window.quests.undo_label == "Import 5 files"
	window.quests.undo()
	assert window.quests.data == {}  # (an import is one undo step per section)


def test_save_after_an_import_writes_the_combined_file(window, tmp_path, monkeypatch):
	paths = files(tmp_path)
	window._set_quests(Document.open(write(tmp_path, "mine.json", {Q3: quest(Q3, "Mine", T3)})))
	window.import_files(paths[:2])
	assert window.quests.dirty and set(window.quests.data) == {Q1, Q2, Q3}
	monkeypatch.setattr("ui.main_window.QFileDialog.getSaveFileName", lambda *a: pytest.fail("Save should not ask"))
	assert window.save_quests()
	assert set(json.loads((tmp_path / "mine.json").read_text(encoding="utf-8"))) == {Q1, Q2, Q3}


def test_a_note_is_shown_for_imported_quests_without_text(window, tmp_path):
	window.import_files(files(tmp_path)[:1])
	assert "1 imported quest has no text yet" in window.statusBar().currentMessage()


def test_importing_into_one_section_only_ticks_files_of_that_kind(window, tmp_path, monkeypatch):
	shown = []
	monkeypatch.setattr(ImportDialog, "exec", lambda self: shown.append([(i.name, i.include, i.error) for i in self.items]) or False)
	monkeypatch.setattr("ui.main_window.QFileDialog.getOpenFileNames", lambda *a: (["%s" % p for p in files(tmp_path)[:3]], ""))
	window.import_into("locale")
	assert [(name, include) for name, include, _e in shown[0]] == [("kappa.json", False), ("side_jobs.json", False), ("en.json", True)]
	assert "looks like a quests file" in shown[0][0][2]
	assert window.quests.data == {}  # (cancelled)


def test_the_import_window_previews_conflicts_and_the_policy(app, tmp_path):
	mine = {Q1: quest(Q1, "Mine", T1)}
	theirs = {Q1: quest(Q1, "Theirs", T2), Q2: quest(Q2, "Two", T3)}
	workspace = {M.QUESTS: mine, M.LOCALE: {}, M.ASSORT: A.empty_assort(), M.LOCKS: A.empty_questassort()}
	dialog = ImportDialog([M.Item("q.json", M.QUESTS, theirs), M.Item("x.json")], workspace)
	table = dialog.table
	assert table.item(0, COLUMNS["new"]).text() == "1 quest" and table.item(0, COLUMNS["there"]).text() == "1 differ"
	assert dialog.plan.data[M.QUESTS][Q1]["QuestName"] == "Mine" and "kept as they are" in dialog.summaryLabel.text()
	dialog.replaceRadio.setChecked(True)
	assert dialog.plan.data[M.QUESTS][Q1]["QuestName"] == "Theirs"
	dialog.bothRadio.setChecked(True)
	assert len(dialog.plan.data[M.QUESTS]) == 3
	table.item(0, COLUMNS["include"]).setCheckState(Qt.CheckState.Unchecked)
	assert dialog.plan.changed == set() and "Nothing new" in dialog.summaryLabel.text()
	assert not dialog.buttons.button(dialog.buttons.StandardButton.Ok).isEnabled()
	assert table.item(1, COLUMNS["include"]).checkState() == Qt.CheckState.Unchecked  # (not recognised: left out)


def test_the_import_window_can_change_a_files_type_and_import_all_the_text(app):
	workspace = {M.QUESTS: {Q1: quest(Q1, "Mine", T1)}, M.LOCALE: {}, M.ASSORT: A.empty_assort(), M.LOCKS: A.empty_questassort()}
	dialog = ImportDialog([M.Item("t.json", M.LOCALE, {f"{Q1} name": "N", "other": "O"})], workspace)
	assert dialog.plan.data[M.LOCALE] == {f"{Q1} name": "N"}
	dialog.everythingBox.setChecked(True)
	assert dialog.plan.data[M.LOCALE] == {f"{Q1} name": "N", "other": "O"}
	dialog.combos[0].setCurrentIndex(dialog.combos[0].findData(M.QUESTS))  # (told it is a quest file instead)
	assert dialog.plan.data == {} and not dialog.everythingBox.isEnabled()


# --- the files strip and the title ----------------------------------------------------------

def test_the_title_is_constant_with_a_star_when_something_is_unsaved(window, tmp_path):
	assert window.windowTitle() == dialogs.APP_NAME
	window.locale.set_value("Edit text", ("k",), "v")
	assert window.windowTitle() == dialogs.APP_NAME + "*"
	window.locale.save(tmp_path / "en.json")
	assert window.windowTitle() == dialogs.APP_NAME
	window._set_quests(Document.open(write(tmp_path, "quests.json", {Q1: quest(Q1, "One", T1)})))
	assert window.windowTitle() == dialogs.APP_NAME  # (an opened file's name is not in the title)


def test_the_strip_shows_count_file_and_state_for_each_section(window, tmp_path):
	assert [segment_text(window, key)[2] for key in ("quests", "locale", "assort", "locks")] == ["empty"] * 4
	window._set_quests(Document.open(write(tmp_path, "quests.json", {Q1: quest(Q1, "One", T1)})))
	title, state, file_text = segment_text(window, "quests")
	assert "Quests" in title and "1" in title and "saved" in state and file_text == "quests.json"
	window.quests.set_value("Rename", (Q1, "QuestName"), "Changed")
	assert "unsaved" in segment_text(window, "quests")[1]
	window.import_files(files(tmp_path)[1:2])
	assert segment_text(window, "quests")[2] == "quests.json · +1 file imported"
	window.locale.set_value("Edit text", ("k",), "v")
	assert segment_text(window, "locale")[2] == "not saved yet" and "unsaved" in segment_text(window, "locale")[1]
	window.import_files(files(tmp_path)[3:])
	assert "1" in segment_text(window, "assort")[0] and segment_text(window, "locks")[0].count("1") == 1


def test_opening_a_file_forgets_what_was_imported(window, tmp_path):
	window.import_files(files(tmp_path)[:2])
	assert window.quest_sources and window.imported["quests"]
	window._set_quests(Document({}))
	assert window.quest_sources == {} and window.imported["quests"] == []
	assert segment_text(window, "quests")[2] == "empty"


def test_the_segment_menus_use_the_same_actions_as_the_file_menu(window):
	names = [a.text() for a in window.files_strip.segment("locale").menu.actions() if not a.isSeparator()]
	assert names == ["New (empty)", "Open...", "Import...", "Save", "Save as..."]
	assert window.actionSaveLocale in window.files_strip.segment("locale").menu.actions()
	assert window.actionSaveLocale in window.menuLocale.actions()


def test_clicking_a_segment_opens_its_menu(app, window, monkeypatch):
	opened = []
	monkeypatch.setattr(FileSegment, "show_menu", lambda self: opened.append(self.title))
	window.show()
	QTest.mouseClick(window.files_strip.segment("assort"), Qt.MouseButton.LeftButton)
	window.files_strip.segment("locks").setFocus()
	QTest.keyClick(window.files_strip.segment("locks"), Qt.Key.Key_Return)
	assert opened == ["Trader assort", "Quest locks"]


# --- saving and dropping files --------------------------------------------------------------

def test_the_setting_makes_save_ask_for_a_file_name_every_time(window, tmp_path, monkeypatch):
	target = tmp_path / "en.json"
	window.locale.save(target)
	window.locale.set_value("Edit text", ("k",), "v")
	asked = []

	def dialog(parent, title, start, *rest):
		asked.append((title, start))
		return str(tmp_path / "other.json"), ""

	monkeypatch.setattr("ui.main_window.QFileDialog.getSaveFileName", dialog)
	assert window.save_locale() and asked == []  # (the default: write to the linked file)
	window.settings.save_asks_for_file = True
	window.locale.set_value("Edit text", ("k2",), "v")
	assert window.save_locale()
	assert asked == [("Save locale file", str(target))] and window.locale.path.name == "other.json"
	assert json.loads((tmp_path / "other.json").read_text(encoding="utf-8")) == {"k": "v", "k2": "v"}


def test_the_save_setting_is_in_the_settings_window_and_off_by_default(app, tmp_path):
	settings = Settings.load(tmp_path / "none.ini")
	assert settings.save_asks_for_file is False
	dialog = dialogs.SettingsDialog(settings, None)
	box = dialog.controls["save_asks_for_file"]
	assert isinstance(box, QCheckBox) and not box.isChecked()


def drop(window, paths):
	mime = QMimeData()
	mime.setUrls([QUrl.fromLocalFile(str(p)) for p in paths])
	event = QDropEvent(QPointF(5, 5), Qt.DropAction.CopyAction, mime, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
	window.dropEvent(event)
	return event


def test_dropping_json_files_or_a_folder_opens_the_import_window(app, window, tmp_path, monkeypatch):
	seen = []
	monkeypatch.setattr(window, "import_files", lambda paths, only=None: seen.append(list(paths)))
	paths = files(tmp_path)
	event = drop(window, paths[:2])
	assert event.isAccepted()
	app.processEvents()
	assert [[Path(x) for x in group] for group in seen] == [paths[:2]]
	drop(window, [tmp_path / "mod"])
	app.processEvents()
	assert [Path(x) for x in seen[1]] == [tmp_path / "mod"]


def test_only_json_files_and_folders_are_accepted_for_dropping(window, tmp_path):
	def mime_for(*paths):
		mime = QMimeData()
		mime.setUrls([QUrl.fromLocalFile(str(p)) for p in paths])
		return mime

	assert window._droppable(mime_for(write(tmp_path, "a.json", {})))
	assert window._droppable(mime_for(tmp_path))
	assert not window._droppable(mime_for(write(tmp_path, "notes.txt", {})))
	assert not window._droppable(QMimeData())
