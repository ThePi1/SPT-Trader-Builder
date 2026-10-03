"""The windows made from Qt Designer files (ui/designer/*.ui, compiled to ui/compiled/ui_*.py)."""

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import compile_ui  # noqa: E402

pytest.importorskip("PySide6")
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QApplication, QMessageBox

from core.documents import Document
from core.gamedata import GameData
from core.paths import BUNDLED_DATABASE_DIR
from core.settings import Settings
from schema import assort as assort_schema
from ui import dialogs, updates
from ui.main_window import MainWindow


@pytest.fixture(scope="module")
def app():
	return QApplication.instance() or QApplication([])


# --- the compiled files match the .ui files ------------------------------------------------------


def test_every_ui_file_has_a_compiled_file_and_the_other_way_round():
	ui = {compile_ui.compiled_name(f).name for f in compile_ui.ui_files()}
	compiled = {p.name for p in compile_ui.COMPILED_DIR.glob("ui_*.py")}
	assert ui and ui == compiled


def test_the_compiled_files_are_up_to_date():
	"""If this fails: run  python tools/compile_ui.py  and commit the compiled files with the .ui change."""
	uic = compile_ui.find_uic()
	if uic is None:
		pytest.skip("pyside6-uic is not available")
	assert compile_ui.out_of_date(uic) == []


# --- the main window's menus ---------------------------------------------------------------------


@pytest.fixture
def window(app, tmp_path, monkeypatch):
	monkeypatch.setattr(updates, "fetch_remote_version", lambda config: None)
	# (closing a window with unsaved changes asks; nobody is there to answer)
	monkeypatch.setattr("ui.main_window.QMessageBox.question", lambda *a, **k: QMessageBox.StandardButton.Discard)
	settings = Settings.load(tmp_path / "none.ini")
	win = MainWindow(settings, GameData(None, "en", BUNDLED_DATABASE_DIR))
	yield win
	win.close()


def action(win, name):
	return getattr(win, f"action{name}")


def test_the_menu_bar_has_the_four_menus_with_their_entries(window):
	assert [a.text() for a in window.menubar.actions()] == ["&File", "&Edit", "&Settings", "&Help"]
	file_entries = [a.text().replace("&", "") for a in window.menuFile.actions() if not a.isSeparator()]
	assert file_entries == [
		"New quest file", "Open quest file...", "Save quest file", "Save quest file as...",
		"New locale file", "Open locale file...", "Save locale file", "Save locale file as...",
		"Trader assort", "Quest locks", "Exit",
	]
	assert [a.text() for a in window.menuAssort.actions()] == ["New", "Open...", "Save", "Save as..."]
	assert [a.text() for a in window.menuLocks.actions()] == ["New", "Open...", "Save", "Save as..."]


@pytest.mark.parametrize("name,keys", [
	("NewQuests", "Ctrl+N"), ("OpenQuests", "Ctrl+O"), ("SaveQuests", "Ctrl+S"), ("SaveQuestsAs", "Ctrl+Shift+S"),
	("SaveLocale", "Ctrl+Alt+S"), ("Undo", "Ctrl+Z"), ("Redo", "Ctrl+Y"), ("Exit", "Alt+F4"),
])
def test_the_shortcuts(window, name, keys):
	assert action(window, name).shortcut() == QKeySequence(keys)


def test_every_menu_entry_does_something(window, monkeypatch):
	"""Each entry opens its file dialog (named for what it opens or saves), or resets what it is for."""
	dialogs_seen = []
	monkeypatch.setattr("ui.main_window.QFileDialog.getOpenFileName", lambda parent, title, *a: dialogs_seen.append(title) or ("", ""))
	monkeypatch.setattr("ui.main_window.QFileDialog.getSaveFileName", lambda parent, title, *a: dialogs_seen.append(title) or ("", ""))
	expected = {
		"OpenQuests": "Open quest file", "SaveQuests": "Save quest file", "SaveQuestsAs": "Save quest file",
		"OpenLocale": "Open locale file", "SaveLocale": "Save locale file", "SaveLocaleAs": "Save locale file",
		"AssortOpen": "Open trader assort file", "AssortSave": "Save trader assort file", "AssortSaveAs": "Save trader assort file",
		"LocksOpen": "Open quest locks file", "LocksSave": "Save quest locks file", "LocksSaveAs": "Save quest locks file",
	}
	for name, title in expected.items():
		dialogs_seen.clear()
		action(window, name).trigger()
		assert dialogs_seen == [title], name


def test_the_new_entries_start_empty_files(window):
	window._set_quests(Document({"a": {}}))
	window._set_locale(Document({"k": "v"}))
	window._set_other("assort", Document({
		"items": [{"_id": "a" * 24, "_tpl": "b" * 24, "parentId": "hideout", "slotId": "hideout", "upd": {}}],
		"barter_scheme": {}, "loyal_level_items": {},
	}))
	window._set_other("locks", Document({"started": {"x": "y"}, "success": {}, "fail": {}}))
	for name in ("NewQuests", "NewLocale", "AssortNew", "LocksNew"):
		action(window, name).trigger()
	assert window.quests.data == {} and window.locale.data == {}
	assert window.assort.data == assort_schema.empty_assort() and window.locks.data == assort_schema.empty_questassort()


def test_undo_and_redo_entries_work_and_show_what_they_undo(window):
	window.locale.set_value("Edit text", ("k",), "v")
	window._update_edit_menu()
	assert window.actionUndo.isEnabled() and "Edit text" in window.actionUndo.text()
	window.actionUndo.trigger()
	assert "k" not in window.locale.data and window.actionRedo.isEnabled() is False
	window._update_edit_menu()
	assert window.actionRedo.isEnabled()
	window.actionRedo.trigger()
	assert window.locale.data == {"k": "v"}


def test_settings_about_and_updates_entries_open_their_dialogs(window, monkeypatch):
	opened = []
	monkeypatch.setattr(dialogs.QDialog, "exec", lambda self: opened.append(type(self).__name__) or 0)
	for name in ("Settings", "About", "Updates"):
		action(window, name).trigger()
	assert opened == ["SettingsDialog", "AboutDialog", "UpdatesDialog"]


def test_exit_closes_the_window(window):
	window.show()
	window.actionExit.trigger()
	assert not window.isVisible()


# --- the dialogs and tabs ------------------------------------------------------------------------


def test_the_dialogs_close_with_their_buttons(app, tmp_path):
	about = dialogs.AboutDialog("0.1", "https://example.com")
	assert "0.1" in about.label.text() and about.label.openExternalLinks()
	about.show()
	about.buttons.rejected.emit()
	assert not about.isVisible()
	settings = Settings.load(tmp_path / "none.ini")
	dialog = dialogs.SettingsDialog(settings, None)
	dialog.show()
	dialog.buttons.rejected.emit()
	assert not dialog.isVisible() and dialog.tabs.count() == 5


# --- the Quests tab's buttons (ui/designer/quest_outline.ui) -------------------------------------


def _outline(app):
	from ui.quest_outline import QuestOutline

	a, b = "a" * 24, "b" * 24

	def quest(qid, name):
		return {
			"_id": qid, "QuestName": name, "traderId": "t" * 24,
			"conditions": {
				"AvailableForStart": [], "Fail": [],
				"AvailableForFinish": [{"id": "1" * 24, "conditionType": "Level", "value": 5, "compareMethod": ">="}, {"id": "2" * 24, "conditionType": "Level", "value": 9, "compareMethod": ">="}],
			},
			"rewards": {"Success": [], "Started": [], "Fail": []},
		}

	outline = QuestOutline(None, None)
	outline.set_document(Document({a: quest(a, "First"), b: quest(b, "Second")}))
	outline.show()
	return outline, a


def test_the_outline_buttons_do_what_they_say(app, monkeypatch):
	monkeypatch.setattr("ui.quest_outline.QMessageBox.question", lambda *a, **k: QMessageBox.StandardButton.Yes)
	outline, first = _outline(app)
	outline._select_key(("quest", (first,)))
	outline.new_quest_button.click()
	assert len(outline.doc.data) == 3 and outline.doc.data[outline._current().path[0]]["QuestName"] == "New quest"
	outline._select_key(("quest", (first,)))
	outline.copy_button.click()
	assert [q["QuestName"] for q in outline.doc.data.values()].count("First (copy)") == 1
	outline._select_key(("task", (first, "conditions", "AvailableForFinish", 0)))
	outline.down_button.click()
	assert [t["value"] for t in outline.doc.data[first]["conditions"]["AvailableForFinish"]] == [9, 5]
	outline.up_button.click()
	assert [t["value"] for t in outline.doc.data[first]["conditions"]["AvailableForFinish"]] == [5, 9]
	outline.delete_button.click()
	assert [t["value"] for t in outline.doc.data[first]["conditions"]["AvailableForFinish"]] == [9]
	outline._select_key(("quest", (first,)))
	outline.delete_button.click()
	assert first not in outline.doc.data


def test_the_add_button_opens_its_menu_and_the_outline_has_its_panes(app):
	outline, first = _outline(app)
	outline._select_key(("quest", (first,)))
	assert outline.add_button.menu() is outline.add_menu
	outline.add_menu.aboutToShow.emit()
	assert outline.add_menu.actions()  # (what can be added to the selected quest)
	assert outline.splitter.count() == 2 and outline.rightSplitter.count() == 2
	assert outline.pane_layout.count() > 0 and outline.problems.parent() is outline.leftPane
