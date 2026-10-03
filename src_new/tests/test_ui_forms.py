import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication

from schema import registry
from ui import forms


@pytest.fixture(scope="module")
def app():
	return QApplication.instance() or QApplication([])


def test_every_spec_makes_a_form(app):
	for group in ("task", "subtask", "reward"):
		for kind in registry.GROUPS[group]:
			item = registry.new_item(group, kind)
			before = repr(item)
			form = forms.FormWidget(registry.spec_for(group, kind))
			form.bind(item)
			assert repr(item) == before, f"{group} {kind}: binding a form changed the item"


def test_editing_writes_only_that_key(app):
	item = registry.new_item("reward", "Experience")
	item["strange"] = {"x": 1}
	form = forms.FormWidget(registry.spec_for("reward", "Experience"))
	form.bind(item)
	seen = []
	form.changed.connect(lambda: seen.append(1))
	control = next(c for c in form.controls if c.field.key == "value")
	control.entry.setText("2500")
	control.entry.textEdited.emit("2500")
	assert item["value"] == 2500 and item["strange"] == {"x": 1} and seen
	control.entry.textEdited.emit("abc")
	assert item["value"] == 2500


def test_text_number_is_kept_until_edited(app):
	item = registry.new_item("reward", "Experience")
	item["value"] = "1500"
	form = forms.FormWidget(registry.spec_for("reward", "Experience"))
	form.bind(item)
	assert item["value"] == "1500"


def test_unknown_choice_is_kept(app):
	quest = {"side": "Weird"}
	form = forms.FormWidget(registry.spec_for("quest", "quest"))
	form.bind(quest)
	assert quest["side"] == "Weird"
