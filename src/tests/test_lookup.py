import json

from core import lookup
from core.gamedata import GameData


def make_db(tmp_path):
	(tmp_path / "templates").mkdir()
	(tmp_path / "locales" / "global").mkdir(parents=True)
	(tmp_path / "templates" / "items.json").write_text(json.dumps({
		"a" * 24: {"_id": "a" * 24, "_name": "weapon_x", "_parent": "b" * 24, "_type": "Item", "_props": {}},
		"b" * 24: {"_id": "b" * 24, "_name": "Pistol", "_parent": "", "_type": "Node", "_props": {}},
	}))
	(tmp_path / "templates" / "quests.json").write_text(json.dumps({"c" * 24: {"traderId": "d" * 24, "QuestName": "Debut"}}))
	(tmp_path / "locales" / "global" / "en.json").write_text(json.dumps({
		"a" * 24 + " Name": "Makarov PM", "a" * 24 + " ShortName": "PM", "c" * 24 + " name": "Debut",
	}))
	return GameData(tmp_path, "en", None)


def test_rows_and_search(tmp_path):
	rows = lookup.build_rows(make_db(tmp_path), quests={"e" * 24: {"QuestName": "My quest"}}, kinds=("item", "quest"))
	assert [r.kind for r in rows] == ["quest", "quest", "item"]
	assert rows[0].name == "My quest" and rows[0].detail == "your quest"
	found = lookup.search(rows, "makarov pistol")
	assert [r.id for r in found] == ["a" * 24]
	assert lookup.search(rows, "zzz") == []
	assert lookup.search(rows, "", kinds=("quest",)) == rows[:2]


def test_search_by_id(tmp_path):
	rows = lookup.build_rows(make_db(tmp_path), kinds=("item",))
	assert lookup.search(rows, "aaaa")


def test_picker_and_view(tmp_path):
	import os

	os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
	import pytest

	pytest.importorskip("PySide6")
	from PySide6.QtWidgets import QApplication

	from ui.lookup_view import LookupView

	app = QApplication.instance() or QApplication([])
	rows = lookup.build_rows(make_db(tmp_path), kinds=("item", "quest"))
	view = LookupView(rows)
	view.search.setText("makarov")
	view.refresh()
	assert view.table.rowCount() == 1 and view.selected_ids() == ["a" * 24]
	got = []
	view.picked.connect(got.extend)
	view._enter()
	assert got == ["a" * 24]


def test_find_button_fills_a_ref_field(tmp_path):
	import os

	os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
	import pytest

	pytest.importorskip("PySide6")
	from PySide6.QtWidgets import QApplication

	from schema import registry
	from ui import forms

	app = QApplication.instance() or QApplication([])
	ctx = forms.Context(make_db(tmp_path), picker=lambda ref, multi, parent: ["a" * 24] if multi else ["c" * 24])
	task = registry.new_item("task", "HandoverItem")
	form = forms.FormWidget(registry.spec_for("task", "HandoverItem"), ctx)
	form.bind(task)
	control = next(c for c in form.controls if c.field.key == "target")
	control._find()
	assert task["target"] == ["a" * 24]


def test_item_categories_are_found_by_their_name_and_id_and_are_not_items():
	from core.paths import BUNDLED_DATABASE_DIR

	handgun = "5447b5cf4bdc2d65278b4567"
	data = GameData(None, "en", BUNDLED_DATABASE_DIR)
	rows = lookup.build_rows(data, kinds=(lookup.ITEM, lookup.CATEGORY))
	found = lookup.search(rows, handgun)
	assert [(r.kind, r.name, r.detail) for r in found] == [(lookup.CATEGORY, "Handgun", "Weapon")]  # (the category it is in)
	assert lookup.KIND_LABEL[lookup.CATEGORY] == "Item category"
	assert not any(r.id == handgun for r in lookup.build_rows(data, kinds=(lookup.ITEM,)))  # (an item search stays items)
	assert any(r.kind == lookup.CATEGORY and r.id == handgun for r in lookup.build_rows(data))  # (the Find IDs tab lists everything)
	assert [r.kind for r in lookup.search(rows, "handgun", (lookup.CATEGORY,))] == [lookup.CATEGORY]


def test_the_item_lists_of_conditions_search_categories_too_but_offers_and_rewards_do_not(tmp_path):
	import os

	os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
	from PySide6.QtWidgets import QApplication

	from ui.main_window import MainWindow

	app = QApplication.instance() or QApplication([])
	seen = {}

	class Dialog:
		ids = []

		def __init__(self, rows, kinds, title, multi, settings, parent):
			seen["kinds"] = kinds

		def exec(self):
			return False

	import ui.main_window as module

	original, module.PickerDialog = module.PickerDialog, Dialog
	try:
		window = MainWindow.__new__(MainWindow)
		window.rows, window.settings = lambda kinds=None: [], None
		window.pick("item_id")
		assert lookup.CATEGORY in seen["kinds"] and lookup.ITEM in seen["kinds"]
		for ref in ("part", "item"):
			window.pick(ref)
			assert lookup.CATEGORY not in seen["kinds"]  # (a category can't be sold or given)
	finally:
		module.PickerDialog = original
