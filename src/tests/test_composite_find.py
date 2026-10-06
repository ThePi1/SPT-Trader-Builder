"""Composite items (the user's saved ones and the game's) can be found in Find IDs and in the Find... picker."""

import json
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from core import lookup
from core.gamedata import GameData
from core.library import Library

PART = "1" * 24
PRESET_ID = "9" * 24


def database(tmp_path):
	(tmp_path / "templates").mkdir()
	(tmp_path / "locales" / "global").mkdir(parents=True)
	(tmp_path / "templates" / "items.json").write_text("{}")
	(tmp_path / "locales" / "global" / "en.json").write_text("{}")
	(tmp_path / "globals.json").write_text(json.dumps({"ItemPresets": {
		PRESET_ID: {"_id": PRESET_ID, "_name": "Vanilla gun", "_items": [{"_id": "2" * 24, "_tpl": "a" * 24}, {"_id": "3" * 24, "_tpl": "b" * 24, "parentId": "2" * 24, "slotId": "mod_x"}]},
	}}))
	return GameData(tmp_path, "en", None)


def library(tmp_path):
	lib = Library(tmp_path / "my_items.json")
	return lib, lib.add("My gun", [{"_id": PART, "_tpl": "a" * 24}])


def test_find_ids_lists_saved_and_vanilla_composite_items(tmp_path):
	lib, entry_id = library(tmp_path)
	rows = lookup.build_rows(database(tmp_path), kinds=(lookup.MINE, lookup.PRESET), library=lib)
	assert [(r.id, r.name, r.kind, r.detail) for r in rows] == [
		(entry_id, "My gun", lookup.MINE, "1 part"), (PRESET_ID, "Vanilla gun", lookup.PRESET, "2 parts"),
	]
	assert lookup.KIND_LABEL[lookup.MINE] == "Your composite item"
	assert [r.id for r in lookup.search(rows, "my gun")] == [entry_id]
	assert [r.id for r in lookup.search(rows, entry_id[:8])] == [entry_id]  # (by id too)
	assert lookup.library_rows(None) == []


def test_the_find_ids_tab_and_the_picker_offer_them(tmp_path, monkeypatch):
	pytest.importorskip("PySide6")
	from PySide6.QtWidgets import QApplication

	from core.settings import Settings
	from ui import updates
	from ui.main_window import MainWindow

	app = QApplication.instance() or QApplication([])
	monkeypatch.setattr(updates, "fetch_remote_version", lambda config: None)
	win = MainWindow(Settings.load(tmp_path / "none.ini"), database(tmp_path))
	try:
		_lib, entry_id = library(tmp_path)
		win.library.entries = Library(tmp_path / "my_items.json").entries
		ids = {r.id for r in win.rows()}
		assert {entry_id, PRESET_ID} <= ids  # (the Find IDs tab)
		assert {r.id for r in win.rows((lookup.MINE, lookup.PRESET))} == {entry_id, PRESET_ID}  # (the composite picker)
		win.lookup_tab.set_rows(win.rows())
		view = win.lookup_tab.view
		labels = [view.filter.itemText(i) for i in range(view.filter.count())]
		assert "Your composite item" in labels and "Vanilla composite item" in labels  # (so the Find IDs list can be narrowed to them)
		assert not view.filter.isHidden()
		view.filter.setCurrentIndex(labels.index("Your composite item"))
		assert [view.table.item(r, 3).text() for r in range(view.table.rowCount())] == [entry_id]
	finally:
		win.close()


def test_the_parts_editor_adds_a_composite_item_found_in_the_picker(tmp_path):
	pytest.importorskip("PySide6")
	from PySide6.QtWidgets import QApplication

	from schema.common import Names
	from ui.forms import Context
	from ui.parts_editor import PartsEditor

	app = QApplication.instance() or QApplication([])
	lib, entry_id = library(tmp_path)
	data = database(tmp_path)
	asked = []
	ctx = Context(data, Names(data), lambda ref, multi, parent: asked.append(ref) or [chosen[0]], lib)
	chosen = [entry_id]
	parts = []
	editor = PartsEditor(parts, ctx)
	editor.add_composite()
	assert asked == ["composite"] and [p["_tpl"] for p in parts] == ["a" * 24]
	assert parts[0]["_id"] != PART  # (new ids, so the saved item itself is untouched)
	chosen[0] = PRESET_ID
	editor.add_composite()
	assert [p["_tpl"] for p in parts] == ["a" * 24, "a" * 24, "b" * 24] and parts[-1]["slotId"] == "mod_x"


def test_the_find_an_item_list_offers_composite_items_and_adds_them_whole(tmp_path):
	pytest.importorskip("PySide6")
	from PySide6.QtWidgets import QApplication

	from schema.common import Names
	from ui.forms import Context
	from ui.lookup_view import PickerDialog
	from ui.parts_editor import PartsEditor

	app = QApplication.instance() or QApplication([])
	lib, entry_id = library(tmp_path)
	data = database(tmp_path)
	rows = [lookup.Row("a" * 24, "Gun", lookup.ITEM)] + lookup.library_rows(lib) + lookup.build_rows(data, kinds=(lookup.PRESET,))
	dialog = PickerDialog(rows, (lookup.ITEM, lookup.MINE, lookup.PRESET), "Find an item", True)
	view = dialog.view
	assert not view.filter.isHidden()  # (a Type filter, since it lists several kinds)
	assert [view.filter.itemText(i) for i in range(view.filter.count())] == ["Everything", "Item", "Your composite item", "Vanilla composite item"]
	assert PickerDialog(rows, (lookup.ITEM,), "Find an item").view.filter.isHidden()  # (one kind: no filter)
	asked = []
	ctx = Context(data, Names(data), lambda ref, multi, parent: asked.append(ref) or ["c" * 24, entry_id, PRESET_ID], lib)
	parts = []
	editor = PartsEditor(parts, ctx)
	editor.add_item()
	assert asked == ["part"]
	assert sorted(p["_tpl"] for p in parts) == sorted(["c" * 24, "a" * 24, "a" * 24, "b" * 24])  # (the item, the saved one, the game's two parts)
	assert [p.get("slotId") for p in parts].count("mod_x") == 1


def picked_ctx(tmp_path, ids, asked=None):
	from schema.common import Names
	from ui.forms import Context

	lib, entry_id = library(tmp_path)
	data = database(tmp_path)
	ctx = Context(data, Names(data), lambda ref, multi, parent: (asked.append(ref) if asked is not None else None) or list(ids(entry_id)), lib)
	return ctx, entry_id


def test_every_item_list_uses_the_same_window_and_a_composite_gives_its_main_items_id(tmp_path):
	pytest.importorskip("PySide6")
	from PySide6.QtWidgets import QApplication

	from schema import fields as F
	from ui import forms

	app = QApplication.instance() or QApplication([])
	asked = []
	ctx, entry_id = picked_ctx(tmp_path, lambda entry: ["c" * 24, entry, PRESET_ID, "c" * 24], asked)
	lst = forms.ListControl(F.Field("target", "Items", F.IDLIST, [], ref=F.ITEM), ctx)  # (Find items, Hand over items, ...)
	lst._find()
	assert lst.values == ["c" * 24, "a" * 24]  # (the item, then the main item of both composites, once: never a composite's own id)
	groups = forms.GroupsControl(F.Field("equipmentInclusive", "Wearing", F.GROUPS, [], ref=F.ITEM), ctx)
	groups._find()
	assert groups.entry.text() == "c" * 24 + ", " + "a" * 24
	single = forms.RefControl(F.Field("target", "Main item", F.REF, "", ref=F.ITEM), ctx)
	single._find()
	assert single.entry.text() == "c" * 24
	assert asked == ["item_id", "item_id", "item_id"]  # (one search window for all of them)
	quest = forms.RefControl(F.Field("target", "Quest", F.REF, "", ref=F.QUEST), ctx)
	quest._find()
	assert asked[-1] == F.QUEST  # (other kinds of id keep their own search)


def test_trader_offers_take_composite_items_whole_and_prices_their_main_item(tmp_path):
	pytest.importorskip("PySide6")
	from PySide6.QtWidgets import QApplication

	from core.documents import Document
	from schema import assort as A
	from ui.assort_tab import AssortTab

	app = QApplication.instance() or QApplication([])
	lib, entry_id = library(tmp_path)
	data = database(tmp_path)
	picks = {"part": [PRESET_ID, entry_id, "c" * 24]}
	doc = Document(A.empty_assort())
	tab = AssortTab(doc, Document(A.empty_questassort()), data, lambda ref, multi, parent: picks[ref], lib)
	tab.add_offer()
	assert len(A.offer_ids(doc.data)) == 3 and not A.validate_assort(doc.data)
	sizes = sorted(len(A.offer_parts(doc.data, o)) for o in A.offer_ids(doc.data))
	assert sizes == [1, 1, 2]  # (the game's two-part composite is one offer with both parts; the saved one and the item have one part)
	offer = next(o for o in A.offer_ids(doc.data) if len(A.offer_parts(doc.data, o)) == 2)
	assert A.offer_parts(doc.data, offer)[1]["slotId"] == "mod_x"
	picks["part"] = [entry_id]
	tab._add_price(offer, tab._ctx().pick_item_ids(True, tab))
	assert doc.data["barter_scheme"][offer][0][-1] == {"count": 1, "_tpl": "a" * 24}


def test_the_vanilla_ak_102_composite_gives_the_ak_102_item_id():
	from core.paths import BUNDLED_DATABASE_DIR
	from schema.common import Names
	from ui.forms import Context

	data = GameData(None, "en", BUNDLED_DATABASE_DIR)
	composite_id, item_id = "5acf7dfc86f774401e19c390", "5ac66d015acfc400180ae6e4"  # AK-102 Default, and the rifle itself
	assert composite_id in data.item_presets and composite_id not in data.items  # (a composite's id is not an item id)
	ctx = Context(data, Names(data), lambda ref, multi, parent: [composite_id])
	assert ctx.pick_item_ids(False) == [item_id] and item_id in data.items
