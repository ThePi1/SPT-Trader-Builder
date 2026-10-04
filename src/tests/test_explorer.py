import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import json

import pytest

from schema import explorer
from schema.issues import errors


def test_detect_kind(vanilla_quests, vanilla_locale, vanilla_assort):
	assert explorer.detect_kind(vanilla_quests) == "quests"
	assert explorer.detect_kind(vanilla_locale) == "locale"
	assert explorer.detect_kind(vanilla_assort) == "assort"
	assert explorer.detect_kind({"success": {"a" * 24: "b" * 24}}) == "questassort"
	assert explorer.detect_kind([1]) is None


def test_check_each_kind(vanilla_quests, vanilla_locale, vanilla_assort):
	assert not errors(explorer.check(vanilla_quests, "quests"))
	assert not errors(explorer.check(vanilla_assort, "assort"))
	assert not explorer.check(vanilla_locale, "locale")
	assert explorer.check({"x": 1}, "locale")[0].level == "error"
	assert explorer.check({}, "nope")


def test_every_spec_has_rows():
	for title, specs in explorer.all_specs():
		assert specs
		for spec in specs:
			explorer.field_rows(spec)


def test_pages_work(tmp_path):
	pytest.importorskip("PySide6")
	from PySide6.QtWidgets import QApplication

	from ui.explorer_tab import ExplorerTab

	app = QApplication.instance() or QApplication([])
	tab = ExplorerTab(lambda: {}, lambda: {})
	tab.browse.tree.setCurrentItem(tab.browse.tree.topLevelItem(1).child(0))
	assert tab.browse.table.rowCount() > 0
	path = tmp_path / "t.json"
	path.write_text(json.dumps({"a" * 24 + " name": "x", "bad": 3}))
	tab.check.load(str(path))
	assert "doesn't look like" in tab.check.summary.text()
	tab.check.kind.setCurrentIndex(tab.check.kind.findData("locale"))
	assert tab.check.list.count() == 1
