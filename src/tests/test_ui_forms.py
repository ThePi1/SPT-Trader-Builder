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


# --- groups of items (equipment, weapon mods) -------------------------------------------------

A, B, C, D = ("a" * 24, "b" * 24, "c" * 24, "d" * 24)


def groups_form(value):
	item = registry.new_item("subtask", "Equipment")
	item["equipmentInclusive"] = value
	form = forms.FormWidget(registry.spec_for("subtask", "Equipment"))
	form.bind(item)
	control = next(c for c in form.controls if c.field.key == "equipmentInclusive")
	return item, form, control


def tree_text(control):
	out = []
	for g in range(control.tree.topLevelItemCount()):
		top = control.tree.topLevelItem(g)
		out.append((top.text(0), [top.child(i).text(0) for i in range(top.childCount())]))
	return out


def test_groups_control_shows_each_group_with_its_items(app):
	item, form, control = groups_form([[A, B], [C]])
	assert isinstance(control, forms.GroupsControl)
	assert [(name, len(items)) for name, items in tree_text(control)] == [("Group 1", 2), ("Group 2", 1)]
	assert item["equipmentInclusive"] == [[A, B], [C]]  # (showing it wrote nothing)


def test_groups_control_adds_a_group_from_typed_ids(app):
	item, form, control = groups_form([[A]])
	control.entry.setText(f"{B}, {C}")
	control._new_group()
	assert item["equipmentInclusive"] == [[A], [B, C]]
	assert control.entry.text() == ""


def test_groups_control_adds_to_the_selected_group_or_starts_one(app):
	item, form, control = groups_form([[A], [B]])
	control.tree.setCurrentItem(control.tree.topLevelItem(1))
	control.entry.setText(C)
	control._add_to_group()
	assert item["equipmentInclusive"] == [[A], [B, C]]
	control.entry.setText(C)  # (already in that group: not added twice)
	control.tree.setCurrentItem(control.tree.topLevelItem(1))
	control._add_to_group()
	assert item["equipmentInclusive"] == [[A], [B, C]]
	control.tree.setCurrentItem(None)
	control.entry.setText(D)
	control._add_to_group()
	assert item["equipmentInclusive"] == [[A], [B, C], [D]]


def test_groups_control_removes_an_item_or_a_whole_group(app):
	item, form, control = groups_form([[A, B], [C]])
	control.tree.setCurrentItem(control.tree.topLevelItem(0).child(0))
	control._remove()
	assert item["equipmentInclusive"] == [[B], [C]]
	control.tree.setCurrentItem(control.tree.topLevelItem(1))
	control._remove()
	assert item["equipmentInclusive"] == [[B]]
	control.tree.setCurrentItem(control.tree.topLevelItem(0).child(0))
	control._remove()  # (the last item of a group takes the group with it)
	assert item["equipmentInclusive"] == []


def test_groups_are_kept_when_something_else_is_edited(app):
	item, form, control = groups_form([[A, B], [C]])
	other = next(c for c in form.controls if c.field.key == "IncludeNotEquippedItems")
	other.check.click()
	assert item["equipmentInclusive"] == [[A, B], [C]] and item["IncludeNotEquippedItems"] is True


def test_groups_control_accepts_a_flat_list_from_an_older_tool(app):
	item, form, control = groups_form([A, B])
	assert [len(items) for _name, items in tree_text(control)] == [1, 1]
	assert item["equipmentInclusive"] == [A, B]  # (until it is edited)


def test_weapon_mods_use_the_same_control(app):
	form = forms.FormWidget(registry.spec_for("subtask", "Kills"), show_advanced=True)
	assert isinstance([c for c in form.controls if c.field.key == "weaponModsInclusive"][0], forms.GroupsControl)


# --- "Only show after" -------------------------------------------------------------------------

TASKS = [(A, "Level >= 5 (Start)"), (B, "Find 1x Salewa (Finish)")]


def visibility_form(value, tasks=TASKS):
	item = registry.new_item("task", "HandoverItem")
	item["visibilityConditions"] = value
	form = forms.FormWidget(registry.spec_for("task", "HandoverItem"), forms.Context(tasks=tasks))
	form.bind(item)
	control = next(c for c in form.controls if c.field.key == "visibilityConditions")
	return item, form, control


def condition(target, ident="1" * 24):
	return {"conditionType": "CompleteCondition", "id": ident, "target": target}


def test_visibility_control_shows_the_tasks_by_name(app):
	item, form, control = visibility_form([condition(A), condition("f" * 24, "2" * 24)])
	assert isinstance(control, forms.VisibilityControl)
	assert [control.list.item(i).text() for i in range(control.list.count())] == ["Level >= 5 (Start)", "f" * 24]
	assert len(item["visibilityConditions"]) == 2  # (nothing written by showing it)


def test_visibility_control_adds_a_new_condition_and_keeps_the_old_ones(app):
	old = condition(A)
	item, form, control = visibility_form([old])
	control.combo.setCurrentIndex(1)
	control._add()
	added = item["visibilityConditions"]
	assert added[0] is old and added[1]["target"] == B and added[1]["conditionType"] == "CompleteCondition"
	assert len(added[1]["id"]) == 24 and added[1]["id"] != old["id"]
	control._add()  # (the same task twice is not added)
	assert len(item["visibilityConditions"]) == 2


def test_visibility_control_removes_one(app):
	item, form, control = visibility_form([condition(A, "1" * 24), condition(B, "2" * 24)])
	control.list.setCurrentRow(0)
	control._remove()
	assert [c["target"] for c in item["visibilityConditions"]] == [B]


def test_visibility_control_with_no_other_tasks_does_nothing(app):
	item, form, control = visibility_form([], tasks=[])
	control._add()
	assert item["visibilityConditions"] == []


def test_visibility_control_keeps_an_older_tools_plain_ids(app):
	item, form, control = visibility_form([A])
	assert control.list.item(0).text() == "Level >= 5 (Start)" and item["visibilityConditions"] == [A]


def test_every_yes_no_box_saves_when_clicked_like_a_user_would(app):
	from PySide6.QtCore import Qt
	from PySide6.QtTest import QTest

	from schema import fields as F

	checked = 0
	for group in ("quest", "task", "subtask", "reward"):
		kinds = ["quest"] if group == "quest" else list(registry.GROUPS[group])
		for kind in kinds:
			spec = registry.spec_for(group, kind)
			for field in forms.flatten(spec.fields):
				if field.kind != F.BOOL:
					continue
				item = registry.new_item(group, kind)
				form = forms.FormWidget(spec, show_advanced=True)
				form.bind(item)
				form.show()
				control = next(c for c in form.controls if c.field.key == field.key)
				was = bool(F.get_path(item, field.key, False))
				QTest.mouseClick(control.check, Qt.MouseButton.LeftButton)
				assert F.get_path(item, field.key) is (not was), f"{group} {kind}: {field.key}"
				checked += 1
	assert checked >= 10
