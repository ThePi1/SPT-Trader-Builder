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
