import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication

from core.library import Library
from ui.composite_tab import CompositeTab


def test_new_edit_saves(tmp_path, monkeypatch):
	app = QApplication.instance() or QApplication([])
	lib = Library(tmp_path / "l.json")
	entry = lib.add("Gun", [])
	tab = CompositeTab(lib, None, lambda ref, multi, parent: ["a" * 24])
	assert tab.current_id() == entry
	tab.editor.add_item()
	assert Library(tmp_path / "l.json").entries[entry]["items"][0]["_tpl"] == "a" * 24


def test_a_base_game_item_opens_read_only_and_a_saved_item_stays_editable(tmp_path):
	from PySide6.QtWidgets import QLabel, QPushButton

	from core.gamedata import GameData
	from core.paths import BUNDLED_DATABASE_DIR

	app = QApplication.instance() or QApplication([])
	lib = Library(tmp_path / "l.json")
	mine = lib.add("Gun", [])
	tab = CompositeTab(lib, GameData(None, "en", BUNDLED_DATABASE_DIR), lambda ref, multi, parent: ["a" * 24])
	assert tab.current_id() == mine and tab.vanilla.count() > 0
	editable = tab.editor
	assert editable.add_button.isEnabled() and editable.more_button.isEnabled()
	tab.vanilla.setCurrentRow(0)
	assert tab.current_id() is None and tab.mine.currentRow() == -1  # (only one list has a selection)
	viewer = tab.editor
	assert viewer is not editable and viewer.read_only and viewer.tree.topLevelItemCount() > 0
	assert not viewer.add_button.isEnabled() and not viewer.more_button.isEnabled() and not viewer.remove_button.isEnabled()
	assert not viewer.slot.isEnabled() and not viewer.stack.isEnabled() and not viewer.found.isEnabled()
	assert viewer.tree.isEnabled()
	assert any("read only" in label.text() for label in tab.right.findChildren(QLabel))
	assert [b.text() for b in tab.right.findChildren(QPushButton) if b.isEnabled()] == ["View as JSON..."]  # (looking is allowed)
	# the details of each part can still be looked at
	names = set()
	for item in viewer._walk():
		viewer.tree.setCurrentItem(item)
		names.add(viewer.name_label.text())
		assert not viewer.remove_button.isEnabled() and not viewer.stack.isEnabled()
	assert len(names) >= 2  # (a base game item has several parts)
	# the base game item's parts are a copy: looking at it changes nothing
	assert len(lib.entries) == 1
	# going back to one of mine makes it editable again and clears the other list
	tab.mine.setCurrentRow(0)
	assert tab.vanilla.currentRow() == -1 and tab.editor.add_button.isEnabled() and not tab.editor.read_only
	# a copy button still works from a selected base game item
	tab.vanilla.setCurrentRow(1)
	tab.copyButton.click()
	assert len(lib.entries) == 2 and tab.current_id() is not None and tab.vanilla.currentRow() == -1 and not tab.editor.read_only


def test_clicking_a_base_game_item_with_the_mouse_keeps_it_open(tmp_path):
	"""In a shown window (the first focus change must not put the selection back on one of mine)."""
	from PySide6.QtCore import Qt
	from PySide6.QtTest import QTest

	from core.gamedata import GameData
	from core.paths import BUNDLED_DATABASE_DIR

	app = QApplication.instance() or QApplication([])
	lib = Library(tmp_path / "l.json")
	lib.add("Gun", [])
	tab = CompositeTab(lib, GameData(None, "en", BUNDLED_DATABASE_DIR), lambda ref, multi, parent: [])
	tab.resize(900, 600)
	tab.show()
	QTest.qWait(100)
	item = tab.vanilla.item(3)
	tab.vanilla.scrollToItem(item)
	QTest.mouseClick(tab.vanilla.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, tab.vanilla.visualItemRect(item).center())
	QTest.qWait(150)
	assert tab.vanilla.currentRow() == 3 and tab.mine.currentRow() == -1 and tab.editor.read_only
	assert not tab.editor.add_button.isEnabled() and tab.editor.tree.topLevelItemCount() > 0
	mine = tab.mine.item(0)
	QTest.mouseClick(tab.mine.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, tab.mine.visualItemRect(mine).center())
	QTest.qWait(100)
	assert tab.mine.currentRow() == 0 and tab.vanilla.currentRow() == -1 and not tab.editor.read_only


def _tab(tmp_path):
	from core.gamedata import GameData
	from core.paths import BUNDLED_DATABASE_DIR

	QApplication.instance() or QApplication([])
	lib = Library(tmp_path / "l.json")
	mine = lib.add("Gun", [{"_id": "1" * 24, "_tpl": "a" * 24}])
	return lib, mine, CompositeTab(lib, GameData(None, "en", BUNDLED_DATABASE_DIR), lambda ref, multi, parent: [])


def test_my_item_can_be_edited_as_json(tmp_path, monkeypatch):
	import json

	from ui.quest_outline import JsonDialog

	lib, mine, tab = _tab(tmp_path)
	assert tab.json_button.text() == "Edit as JSON..."
	original = json.loads(json.dumps(lib.entries[mine]))  # (adding gave the part a new id)
	seen = {}

	def edit(self):
		seen["data"] = json.loads(self.text.toPlainText())
		seen["title"], seen["read_only"] = self.windowTitle(), self.text.isReadOnly()
		self.text.setPlainText(json.dumps({"name": "Rifle", "items": [{"_id": "2" * 24, "_tpl": "b" * 24}, {"_id": "3" * 24, "_tpl": "c" * 24, "parentId": "2" * 24, "slotId": "mod_stock"}]}))
		self._ok()
		return True

	monkeypatch.setattr(JsonDialog, "exec", edit)
	tab.json_button.click()
	assert seen["data"] == original and seen["data"]["items"][0]["_tpl"] == "a" * 24 and seen["title"] == "Edit as JSON" and not seen["read_only"]
	assert [e["name"] for e in lib.entries.values()] == ["Rifle"] and len(lib.entries[mine]["items"]) == 2
	assert Library(tmp_path / "l.json").entries[mine]["items"][1]["slotId"] == "mod_stock"  # (saved)
	assert tab.mine.item(0).text() == "Rifle" and tab.editor.tree.topLevelItemCount() == 1 and tab.current_id() == mine


def test_json_without_a_list_of_items_is_refused_and_cancel_changes_nothing(tmp_path, monkeypatch):
	from ui.quest_outline import JsonDialog

	lib, mine, tab = _tab(tmp_path)
	before = {k: dict(v) for k, v in lib.entries.items()}
	warned = []
	monkeypatch.setattr("ui.composite_tab.QMessageBox.warning", lambda *a: warned.append(a[2]))
	monkeypatch.setattr(JsonDialog, "exec", lambda self: self.text.setPlainText('{"name": "X", "items": "no"}') or self._ok() or True)
	tab.json_button.click()
	assert warned and lib.entries == before
	monkeypatch.setattr(JsonDialog, "exec", lambda self: False)
	tab.json_button.click()
	assert lib.entries == before


def test_a_base_game_item_can_be_viewed_as_json_but_not_changed(tmp_path, monkeypatch):
	import json

	from PySide6.QtWidgets import QDialogButtonBox

	from ui.quest_outline import JsonDialog

	lib, mine, tab = _tab(tmp_path)
	tab.vanilla.setCurrentRow(2)
	assert tab.json_button.text() == "View as JSON..."
	preset = tab.gamedata.item_presets[tab.vanilla.item(2).data(256)]
	seen = {}

	def view(self):
		seen["data"] = json.loads(self.text.toPlainText())
		seen["title"], seen["read_only"] = self.windowTitle(), self.text.isReadOnly()
		seen["buttons"] = [b.text().replace("&", "") for b in self.findChild(QDialogButtonBox).buttons()]
		return 0

	monkeypatch.setattr(JsonDialog, "exec", view)
	tab.json_button.click()
	assert seen["data"] == preset and seen["title"] == "View as JSON" and seen["read_only"]
	assert seen["buttons"] == ["Close"]
	assert len(lib.entries) == 1 and lib.entries[mine]["name"] == "Gun"
