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
from ui.tabs import fill_tabs


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
	assert file_entries == ["Import files...", "Quests", "Locale", "Trader assort", "Quest assort", "Exit"]
	section = ["New (empty)", "Open...", "Import...", "Save", "Save as..."]
	for menu in (window.menuLocale, window.menuAssort, window.menuLocks):
		assert [a.text() for a in menu.actions() if not a.isSeparator()] == section
	assert [a.text() for a in window.menuQuests.actions() if not a.isSeparator()] == section + ["&Export selected quests..."]


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
		"LocksOpen": "Open quest assort file", "LocksSave": "Save quest assort file", "LocksSaveAs": "Save quest assort file",
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
	outline._fill_add_menu()
	next(a for a in outline.add_menu.actions() if a.text() == "New quest").trigger()  # (Add > New quest)
	assert len(outline.doc.data) == 3 and outline.doc.data[outline._current().path[0]]["QuestName"] == "New quest"
	outline._select_key(("quest", (first,)))
	outline.copy_button.click()
	assert [q["QuestName"] for q in outline.doc.data.values()].count("First (copy)") == 1
	outline._select_key(("task", (first, "conditions", "AvailableForFinish", 0)))
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


# --- the tab bar (main_window.ui has a placeholder page per tab) ---------------------------------


def test_the_tabs_come_from_the_ui_file_and_hold_the_real_widgets(window):
	from PySide6.QtWidgets import QTabWidget

	expected = [
		("Quests", window.quest_outline), ("Locale", window.locale_tab), ("Trader", window.assort_tab),
		("Composite items", window.composite_tab), ("Find IDs", window.lookup_tab), ("Schema Explorer", window.explorer_tab),
	]
	assert [(window.tabs.tabText(i), window.tabs.widget(i)) for i in range(window.tabs.count())] == expected
	assert isinstance(window.tabs, QTabWidget) and window.tabs.currentIndex() == 0


def test_the_placeholder_pages_are_gone_and_a_mismatch_with_the_ui_file_is_reported(window, app):
	assert not [n for n in vars(window) if n.startswith("page_")]
	with pytest.raises(RuntimeError, match="the .ui file has the tab pages"):
		fill_tabs(window.tabs, window, {"page_quests": window.quest_outline})  # (the tabs already hold real widgets: names don't match)


def test_switching_tabs_still_refreshes_the_tab(window):
	window._set_locale(Document({"a": "b"}))
	window.tabs.setCurrentWidget(window.locale_tab)
	assert window.locale_tab.model.total == 1
	window.tabs.setCurrentWidget(window.lookup_tab)
	assert window.lookup_tab.view.table.rowCount() > 0


def test_the_tree_gets_the_spare_height_and_the_problems_list_stays_small(app):
	from ui.quest_outline import QuestOutline

	class Expanded:
		show_json_preview = show_all_fields = problems_collapsed = False

		def update(self, values):
			pass

	outline = QuestOutline(None, Expanded())
	outline.set_document(Document({}))
	outline.resize(1000, 700)
	outline.show()
	app.processEvents()
	assert outline.problems.list.isVisible()
	assert outline.problems.height() < 200 and outline.tree.height() > 3 * outline.problems.height()
	assert outline.tree.geometry().bottom() < outline.problems.geometry().top() <= outline.tree.geometry().bottom() + 10


def test_the_button_row_fills_the_width_in_equal_parts(app):
	outline, _first = _outline(app)
	outline.resize(1800, 700)
	outline.splitter.setSizes([1200, 500])  # (wide enough that the buttons have room to spare)
	app.processEvents()
	buttons = [outline.add_button, outline.copy_button, outline.delete_button]
	margins = outline.leftLayout.contentsMargins()
	assert buttons[0].geometry().left() == margins.left()
	assert buttons[-1].geometry().right() + 1 == outline.leftPane.width() - margins.right()
	widths = [b.width() for b in buttons]
	assert max(widths) - min(widths) <= 2


# --- the other tabs (composite, trader, find ids, the picker, the schema explorer) ---------------


def test_the_composite_tab_buttons(app, tmp_path, monkeypatch):
	from core.library import Library
	from ui.composite_tab import CompositeTab

	library = Library(tmp_path / "l.json")
	tab = CompositeTab(library, GameData(None, "en", BUNDLED_DATABASE_DIR))
	answers = iter([("Gun", True), ("Rifle", True)])
	monkeypatch.setattr("ui.composite_tab.QInputDialog.getText", lambda *a, **k: next(answers))
	monkeypatch.setattr("ui.composite_tab.QMessageBox.question", lambda *a, **k: QMessageBox.StandardButton.Yes)
	tab.newButton.click()
	assert [e["name"] for e in library.entries.values()] == ["Gun"] and tab.mine.count() == 1
	tab.renameButton.click()
	assert [e["name"] for e in library.entries.values()] == ["Rifle"]
	assert tab.vanilla.count() > 0
	tab.vanilla.setCurrentRow(0)
	tab.copyButton.click()
	assert len(library.entries) == 2 and tab.mine.count() == 2
	tab.deleteButton.click()
	assert len(library.entries) == 1
	assert tab.splitter.count() == 2 and tab.editor is not None


def test_the_trader_tab_buttons_and_the_trader_box(app, monkeypatch):
	from ui.assort_tab import AssortTab

	monkeypatch.setattr("ui.assort_tab.QMessageBox.question", lambda *a, **k: QMessageBox.StandardButton.Yes)
	gamedata = GameData(None, "en", BUNDLED_DATABASE_DIR)
	tab = AssortTab(Document(assort_schema.empty_assort()), Document(assort_schema.empty_questassort()), gamedata, lambda ref, multi, parent: ["a" * 24, "b" * 24])
	tab.addButton.click()
	assert tab.list.count() == 2
	tab.copyButton.click()
	assert tab.list.count() == 3
	tab.deleteButton.click()
	assert tab.list.count() == 2
	# the trader box: only a different trader refreshes the tab (the box also reports losing focus)
	refreshed = []
	tab.refresh = lambda select=None: refreshed.append(select)
	tab.trader.lineEdit().editingFinished.emit()
	assert refreshed == []
	tab.trader.setCurrentIndex(1)
	tab.trader.activated.emit(1)
	tab.trader.lineEdit().editingFinished.emit()
	assert len(refreshed) == 1 and tab.trader_id == tab.trader.itemData(1)


def test_the_tab_order_of_the_trader_tab_ends_with_the_trader_box(app):
	from ui.assort_tab import AssortTab

	tab = AssortTab(Document(assort_schema.empty_assort()), Document(assort_schema.empty_questassort()))
	tab.show()
	app.processEvents()
	named = [tab.search, tab.list, tab.addButton, tab.copyButton, tab.deleteButton, tab.trader]
	chain, widget = [], tab.search
	for _ in range(60):  # (the chain also holds inner widgets such as the list's scroll bars)
		if widget in named and widget not in chain:
			chain.append(widget)
		widget = widget.nextInFocusChain()
	assert chain == named


def test_the_find_ids_tab_copies_ids_and_names(app):
	from PySide6.QtGui import QGuiApplication

	from core import lookup
	from ui.lookup_view import LookupTab

	rows = [lookup.Row(id="a" * 24, name="Alpha", kind="item"), lookup.Row(id="b" * 24, name="Beta", kind="item")]
	tab = LookupTab(rows)
	tab.view.table.selectRow(1)
	tab.copy_id_button.click()
	assert QGuiApplication.clipboard().text() == "b" * 24
	tab.copy_name_button.click()
	assert QGuiApplication.clipboard().text() == "Beta"
	assert tab.view is tab.verticalLayout.itemAt(0).widget()


def test_the_picker_dialog_returns_the_chosen_ids_or_nothing(app):
	from core import lookup
	from ui.lookup_view import PickerDialog

	rows = [lookup.Row(id="a" * 24, name="Alpha", kind="item"), lookup.Row(id="b" * 24, name="Beta", kind="item")]
	dialog = PickerDialog(rows, ("item",), "Find an item")
	assert dialog.windowTitle() == "Find an item" and dialog.view.table.rowCount() == 2
	dialog.view.table.selectRow(1)
	dialog.buttons.accepted.emit()
	assert dialog.result() == dialog.DialogCode.Accepted and dialog.ids == ["b" * 24]
	cancelled = PickerDialog(rows, ("item",), "Find an item")
	cancelled.buttons.rejected.emit()
	assert cancelled.result() == cancelled.DialogCode.Rejected and cancelled.ids == []


def test_the_schema_explorer_pages(app):
	from ui.explorer_tab import ExplorerTab

	tab = ExplorerTab(lambda: {}, lambda: {})
	assert [tab.tabText(i) for i in range(tab.count())] == ["What things are made of", "Check a file"]
	assert tab.widget(0) is tab.browse and tab.widget(1) is tab.check
	assert not [n for n in vars(tab) if n.startswith("page_")]
	assert tab.browse.tree.topLevelItemCount() > 0
	first = tab.browse.tree.topLevelItem(0).child(0)
	tab.browse.tree.setCurrentItem(first)
	assert tab.browse.title.text() and tab.browse.table.rowCount() > 0
	assert [tab.browse.table.horizontalHeaderItem(i).text() for i in range(5)] == ["Field", "Key in the file", "Kind", "Needed", "Starts as"]


def test_a_long_description_in_the_schema_explorer_does_not_squeeze_the_tree(app):
	from ui.explorer_tab import BrowsePage

	page = BrowsePage()
	page.resize(900, 500)
	page.show()
	app.processEvents()
	before = page.tree.width()
	page.tree.setCurrentItem(page.tree.topLevelItem(0).child(0))  # (Quest: its "filled in by the app" line is very long)
	app.processEvents()
	assert "Filled in by the app" in page.where.text() and len(page.where.text()) > 150
	assert page.where.wordWrap() and page.tree.width() == before and page.tree.width() >= 200
	assert page.where.width() <= page.splitter.width() - page.tree.width()
