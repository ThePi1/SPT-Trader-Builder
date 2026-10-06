"""Importing a trader assort asks for its trader and fills in the Trader box; changing a trader that is set asks first."""

import json
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication, QMessageBox

from core import merge as M
from core.documents import Document
from core.gamedata import GameData
from core.paths import BUNDLED_DATABASE_DIR
from schema import assort as A
from ui.assort_tab import AssortTab
from ui.import_dialog import ImportDialog

PRAPOR, MECHANIC = "54cb50c76803fa8b248b4571", "5a7c2eca46aef81a7ca2145d"
TPL = "5449016a4bdc2d6f028b456f"


@pytest.fixture(scope="module")
def app():
	return QApplication.instance() or QApplication([])


def assort_file(folder):
	items, barter, level = A.new_offer(TPL)
	path = folder / "assort.json"
	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_text(json.dumps({"items": items, "barter_scheme": {items[0]["_id"]: barter}, "loyal_level_items": {items[0]["_id"]: level}}), encoding="utf-8")
	return path


def answer(monkeypatch, reply):
	asked = []
	monkeypatch.setattr("ui.assort_tab.QMessageBox.question", lambda parent, title, text, *a: asked.append((title, text)) or reply)
	return asked


# --- where a file says whose it is --------------------------------------------------------------

def test_a_trader_is_guessed_from_where_the_file_is(tmp_path):
	known = {PRAPOR: "Prapor", MECHANIC: "Mechanic"}
	assert M.guess_trader(tmp_path / "db" / "traders" / MECHANIC / "assort.json", known) == MECHANIC
	assert M.guess_trader(tmp_path / "db" / "CustomAssort" / ("a" * 24) / "Assorts" / "a.json", known) == "a" * 24  # (a mod's own trader)
	assert M.guess_trader(tmp_path / ("b" * 24) / "x" / PRAPOR / "assort.json", known) == PRAPOR  # (a known one is preferred)
	assert M.guess_trader(tmp_path / "mod" / "assort.json", known) == ""
	(tmp_path / "t").mkdir()
	(tmp_path / "t" / "base.json").write_text(json.dumps({"_id": "c" * 24, "nickname": "Modder"}), encoding="utf-8")
	assert M.guess_trader(tmp_path / "t" / "assort.json", known) == "c" * 24  # (its base.json says)


# --- the import window -------------------------------------------------------------------------------

def test_the_import_window_asks_for_the_trader_of_an_assort_file(app, tmp_path):
	path = assort_file(tmp_path / "traders" / MECHANIC)
	quests = tmp_path / "quests.json"
	quests.write_text(json.dumps({"a" * 24: {"conditions": {}, "rewards": {}}}), encoding="utf-8")
	traders = {PRAPOR: "Prapor", MECHANIC: "Mechanic"}
	dialog = ImportDialog(M.load_items([path]), {}, traders=traders, trader="")
	assert not dialog.traderBox.isHidden() and dialog.trader_id == MECHANIC and dialog.chosen_trader() == MECHANIC  # (from the folder name)
	assert [dialog.traderBox.itemText(i) for i in range(dialog.traderBox.count())] == ["(not set)", "Prapor", "Mechanic"]
	dialog.traderBox.setCurrentIndex(0)
	assert dialog.chosen_trader() == ""
	dialog.traderBox.setEditText("b" * 24)  # (a pasted id)
	assert dialog.chosen_trader() == "b" * 24
	only_quests = ImportDialog(M.load_items([quests]), {}, traders=traders, trader=PRAPOR)
	assert only_quests.traderBox.isHidden() and only_quests.chosen_trader() == ""  # (nothing to ask when no assort comes in)
	nowhere = ImportDialog(M.load_items([assort_file(tmp_path / "mod")]), {}, traders=traders, trader=PRAPOR)
	assert nowhere.trader_id == PRAPOR  # (no clue in the path: the trader that is chosen now)


@pytest.fixture
def window(app, tmp_path, monkeypatch):
	from core.settings import Settings
	from ui import updates
	from ui.main_window import MainWindow

	monkeypatch.setattr("core.references.REFERENCES_FILE", tmp_path / "references.json")
	monkeypatch.setattr(updates, "fetch_remote_version", lambda config: None)
	monkeypatch.setattr("ui.main_window.QMessageBox.question", lambda *a, **k: QMessageBox.StandardButton.Discard)  # (closing with unsaved changes)
	win = MainWindow(Settings.load(tmp_path / "none.ini"), GameData(None, "en", BUNDLED_DATABASE_DIR))
	monkeypatch.setattr(ImportDialog, "exec", lambda self: True)  # (accept the import window as it opens)
	yield win
	win.close()


def test_importing_a_trader_assort_fills_in_the_trader_box(window, tmp_path):
	assert window.assort_tab.trader_id == ""
	window.import_files([str(assort_file(tmp_path / "traders" / PRAPOR))])
	assert window.assort_tab.trader_id == PRAPOR and window.assort_tab.trader.currentText() == "Prapor"
	assert len(A.offer_ids(window.assort.data)) == 1 and "No trader has been chosen" not in window.assort_tab.note.text()


def test_importing_for_another_trader_asks_before_changing_it(window, tmp_path, monkeypatch):
	tab = window.assort_tab
	tab.set_trader(MECHANIC)
	asked = answer(monkeypatch, QMessageBox.StandardButton.No)
	window.import_files([str(assort_file(tmp_path / "traders" / PRAPOR))])
	assert len(asked) == 1 and "from Mechanic to Prapor" in asked[0][1]
	assert tab.trader_id == MECHANIC and len(A.offer_ids(window.assort.data)) == 1  # (the offers came in; the trader stayed)
	answer(monkeypatch, QMessageBox.StandardButton.Yes)
	window.import_files([str(assort_file(tmp_path / "again" / PRAPOR))])
	assert tab.trader_id == PRAPOR


# --- the Trader box ---------------------------------------------------------------------------------------

def make_tab():
	items, barter, level = A.new_offer(TPL)
	doc = Document({"items": items, "barter_scheme": {items[0]["_id"]: barter}, "loyal_level_items": {items[0]["_id"]: level}})
	return AssortTab(doc, Document(A.empty_questassort()), GameData(None, "en", BUNDLED_DATABASE_DIR))


def test_changing_a_trader_that_is_set_asks_first(app, monkeypatch):
	tab = make_tab()
	asked = answer(monkeypatch, QMessageBox.StandardButton.Yes)
	tab.trader.setCurrentIndex(tab.trader.findData(PRAPOR))
	tab._trader_changed()
	assert asked == [] and tab.trader_id == PRAPOR  # (from (not set): no question)
	tab.trader.setCurrentIndex(tab.trader.findData(MECHANIC))
	tab._trader_changed()
	assert len(asked) == 1 and asked[0][0] == "Change trader" and "from Prapor to Mechanic" in asked[0][1] and tab.trader_id == MECHANIC
	asked = answer(monkeypatch, QMessageBox.StandardButton.No)
	tab.trader.setCurrentIndex(tab.trader.findData(PRAPOR))
	tab._trader_changed()
	assert len(asked) == 1 and tab.trader_id == MECHANIC and tab.trader.currentText() == "Mechanic"  # (No puts it back)
	tab.trader.setCurrentIndex(0)  # ((not set) is a change too)
	tab._trader_changed()
	assert len(asked) == 2 and "to (not set)" in asked[1][1] and tab.trader_id == MECHANIC
	answer(monkeypatch, QMessageBox.StandardButton.Yes)
	tab.trader.setCurrentIndex(0)
	tab._trader_changed()
	assert tab.trader_id == ""


def test_the_note_says_when_no_trader_has_been_chosen(app, monkeypatch):
	tab = make_tab()
	assert tab.note.text() == "1 of 1 offers. No trader has been chosen."
	tab.set_trader(PRAPOR)
	assert tab.note.text() == "1 of 1 offers."
	answer(monkeypatch, QMessageBox.StandardButton.Yes)
	tab.set_trader("")
	assert tab.note.text() == "1 of 1 offers. No trader has been chosen."


# --- opening a trader assort asks too ------------------------------------------------------------------

def open_with(window, monkeypatch, path, reply):
	"""Open the assort file at path; reply is what the Trader question gives back ((text, True), or None for cancel)."""
	seen = []
	monkeypatch.setattr("ui.main_window.QFileDialog.getOpenFileName", lambda *a, **k: (str(path), ""))

	def question(parent, title, text, items, start, editable):
		seen.append((items, start, editable))
		return reply if reply is not None else ("", False)

	monkeypatch.setattr("ui.main_window.QInputDialog.getItem", question)
	window._open_other("assort")
	return seen


def test_opening_a_trader_assort_asks_which_trader_starting_from_where_the_file_is(window, tmp_path, monkeypatch):
	path = assort_file(tmp_path / "traders" / MECHANIC)
	seen = open_with(window, monkeypatch, path, ("Mechanic", True))
	items, start, editable = seen[0]
	assert items[0] == "(not set)" and items[start] == "Mechanic" and editable  # (the folder name says Mechanic; ids can be pasted)
	assert len(A.offer_ids(window.assort.data)) == 1 and window.assort.path == path
	assert window.assort_tab.trader_id == MECHANIC and "No trader has been chosen" not in window.assort_tab.note.text()


def test_the_answer_can_be_another_trader_a_pasted_id_or_nothing(window, tmp_path, monkeypatch):
	path = assort_file(tmp_path / "traders" / MECHANIC)
	open_with(window, monkeypatch, path, ("Prapor", True))
	assert window.assort_tab.trader_id == PRAPOR
	answer(monkeypatch, QMessageBox.StandardButton.Yes)  # (changing a trader that is set asks)
	open_with(window, monkeypatch, path, ("d" * 24, True))
	assert window.assort_tab.trader_id == "d" * 24
	open_with(window, monkeypatch, path, ("(not set)", True))
	assert window.assort_tab.trader_id == ""


def test_cancelling_the_question_keeps_the_trader_but_the_file_is_open(window, tmp_path, monkeypatch):
	window.assort_tab.set_trader(PRAPOR)
	open_with(window, monkeypatch, assort_file(tmp_path / "traders" / MECHANIC), None)
	assert window.assort_tab.trader_id == PRAPOR and len(A.offer_ids(window.assort.data)) == 1


def test_opening_for_another_trader_asks_before_changing_one_that_is_set(window, tmp_path, monkeypatch):
	window.assort_tab.set_trader(PRAPOR)
	asked = answer(monkeypatch, QMessageBox.StandardButton.No)
	open_with(window, monkeypatch, assort_file(tmp_path / "traders" / MECHANIC), ("Mechanic", True))
	assert len(asked) == 1 and "from Prapor to Mechanic" in asked[0][1] and window.assort_tab.trader_id == PRAPOR


def test_the_question_is_asked_once_even_when_the_box_loses_focus_while_it_is_open(app, monkeypatch):
	"""Opening the question takes the focus from the Trader box, which then says it is finished while the question is still up."""
	tab = make_tab()
	tab.set_trader(PRAPOR)
	asked = []

	def question(parent, title, text, *a):
		asked.append(text)
		tab.trader.lineEdit().editingFinished.emit()  # (what the focus change does)
		tab.trader.activated.emit(tab.trader.currentIndex())
		return QMessageBox.StandardButton.No

	monkeypatch.setattr("ui.assort_tab.QMessageBox.question", question)
	tab.trader.setCurrentIndex(tab.trader.findData(MECHANIC))
	tab._trader_changed()
	assert len(asked) == 1 and tab.trader_id == PRAPOR  # (asked once; No put Prapor back)
	asked.clear()
	monkeypatch.setattr("ui.assort_tab.QMessageBox.question", lambda parent, title, text, *a: question(parent, title, text) and QMessageBox.StandardButton.Yes)
	tab.trader.setCurrentIndex(tab.trader.findData(MECHANIC))
	tab._trader_changed()
	assert len(asked) == 1 and tab.trader_id == MECHANIC
