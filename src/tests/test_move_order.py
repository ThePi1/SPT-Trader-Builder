"""Moving quests, conditions, subtasks and rewards: the order is the order in the file, and the file counts as edited."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import json

import pytest

pytest.importorskip("PySide6")
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from core.documents import Document
from schema import registry
from ui.quest_outline import ROLE, QuestOutline

A, B, C, D = ("a" * 24, "b" * 24, "c" * 24, "d" * 24)


@pytest.fixture(scope="module")
def app():
	return QApplication.instance() or QApplication([])


def quest(quest_id, name):
	return {
		"_id": quest_id, "QuestName": name,
		"conditions": {"AvailableForStart": [], "Fail": [], "AvailableForFinish": []},
		"rewards": {"Success": [], "Started": [], "Fail": []},
	}


def make(order=(A, B, C, D)):
	doc = Document({q: quest(q, q[0].upper()) for q in order})
	outline = QuestOutline()
	outline.set_document(doc)
	outline.show()
	return outline, doc


def top_rows(outline):
	return [outline.tree.topLevelItem(i) for i in range(outline.tree.topLevelItemCount())]


def row(outline, quest_id):
	return next(i for i in top_rows(outline) if i.data(0, ROLE).path[0] == quest_id)


def select(outline, *quest_ids):
	outline.tree.clearSelection()
	outline.tree.setCurrentItem(row(outline, quest_ids[0]))
	for quest_id in quest_ids[1:]:
		row(outline, quest_id).setSelected(True)


def test_a_reordered_file_is_edited_undoable_and_saved_in_the_new_order(tmp_path):
	doc = Document({A: {"x": 1}, B: {"x": 2}})
	path = tmp_path / "quests.json"
	doc.save(path)
	assert not doc.dirty
	doc.change("Move quest", lambda data: (lambda items: (data.clear(), data.update(items)))({B: data[B], A: data[A]}))
	assert list(doc.data) == [B, A] and doc.dirty  # (same content, different order: still counts as edited)
	doc.undo()
	assert list(doc.data) == [A, B] and not doc.dirty
	doc.redo()
	assert list(doc.data) == [B, A]
	doc.save()
	assert list(json.loads(path.read_text(encoding="utf-8"))) == [B, A]


def test_move_a_quest_up_down_to_the_top_and_to_the_bottom(app):
	outline, doc = make()
	select(outline, C)
	outline.move_selected("up")
	assert list(doc.data) == [A, C, B, D] and outline._current().path[0] == C
	outline.move_selected("down")
	outline.move_selected("down")
	assert list(doc.data) == [A, B, D, C]
	outline.move_selected("top")
	assert list(doc.data) == [C, A, B, D]
	outline.move_selected("bottom")
	assert list(doc.data) == [A, B, D, C]
	assert doc.dirty and doc.undo_label == "Move quest"
	doc.undo()
	assert list(doc.data) == [C, A, B, D]


def test_the_buttons_follow_what_can_move(app):
	outline, doc = make()
	select(outline, A)
	assert not outline.moveUpButton.isEnabled() and outline.moveDownButton.isEnabled()
	select(outline, B)
	assert outline.moveUpButton.isEnabled() and outline.moveDownButton.isEnabled()
	select(outline, D)
	assert outline.moveUpButton.isEnabled() and not outline.moveDownButton.isEnabled()
	outline.tree.clearSelection()
	assert not outline.moveUpButton.isEnabled() and not outline.moveDownButton.isEnabled()  # (nothing selected)
	outline.moveUpButton.setEnabled(True)
	select(outline, B)
	outline.moveUpButton.click()
	assert list(doc.data) == [B, A, C, D]


def test_several_selected_quests_move_together_and_stay_selected(app):
	outline, doc = make()
	select(outline, B, C)
	outline.move_selected("up")
	assert list(doc.data) == [B, C, A, D]
	outline.move_selected("up")  # (already at the top: nothing happens)
	assert list(doc.data) == [B, C, A, D]
	assert not outline.can_move("up") and outline.can_move("down")
	assert {i.data(0, ROLE).path[0] for i in outline.tree.selectedItems() if i.data(0, ROLE).kind == "quest"} == {B, C}
	outline.move_selected("bottom")
	assert list(doc.data) == [A, D, B, C]
	select(outline, A, C)  # (not next to each other)
	outline.move_selected("top")
	assert list(doc.data) == [A, C, D, B]


def test_a_search_moves_a_quest_past_the_next_shown_quest_and_hidden_ones_stay(app):
	outline, doc = make()
	outline.search.setText("")  # (names are A, B, C, D)
	doc.data[B]["QuestName"] = "Zed B"
	outline.rebuild()
	outline.search.setText("zed")
	assert [i.data(0, ROLE).path[0] for i in top_rows(outline) if not i.isHidden()] == [B]
	select(outline, B)
	assert not outline.can_move("up") and not outline.can_move("down")  # (the only one shown)
	doc.data[D]["QuestName"] = "Zed D"
	outline.rebuild()
	select(outline, D)
	outline.move_selected("up")  # (past B, the previous quest that is shown; C is hidden and stays between them)
	assert list(doc.data) == [A, D, C, B]


def test_conditions_subtasks_and_rewards_move_and_their_order_field_is_left_alone(app):
	outline, doc = make()
	quest_a = doc.data[A]
	items = [registry.new_item("task", kind) for kind in ("HandoverItem", "FindItem", "Level")]
	for number, task in enumerate(items):
		task["index"] = number + 10
	quest_a["conditions"]["AvailableForFinish"] += items
	counter = registry.new_item("task", "CounterCreator")
	counter["counter"]["conditions"] += [registry.new_item("subtask", "Kills"), registry.new_item("subtask", "Shots")]
	quest_a["conditions"]["Fail"].append(counter)
	quest_a["rewards"]["Success"] += [registry.new_item("reward", "Experience"), registry.new_item("reward", "Skill")]
	outline.rebuild()
	kinds = lambda: [t["conditionType"] for t in quest_a["conditions"]["AvailableForFinish"]]
	outline._select_key(("task", (A, "conditions", "AvailableForFinish", 2)))
	outline.move_selected("top")
	assert kinds() == ["Level", "HandoverItem", "FindItem"]
	assert [t["index"] for t in quest_a["conditions"]["AvailableForFinish"]] == [12, 10, 11]  # (carried along, never renumbered)
	assert outline._current().path[-1] == 0 and not outline.can_move("up")
	outline._select_key(("subtask", (A, "conditions", "Fail", 0, "counter", "conditions", 0)))
	outline.move_selected("down")
	assert [s["conditionType"] for s in counter["counter"]["conditions"]] == ["Shots", "Kills"]
	outline._select_key(("reward", (A, "rewards", "Success", 1)))
	outline.move_selected("up")
	assert [r["type"] for r in quest_a["rewards"]["Success"]] == ["Skill", "Experience"]
	assert doc.undo_label == "Move"
	heading = next(i for i in outline._walk() if i.data(0, ROLE).kind == "group" and i.data(0, ROLE).group == "task" and i.data(0, ROLE).timing == "Fail")
	outline.tree.setCurrentItem(heading)
	assert not outline.can_move("up") and not outline.can_move("down")  # (a list heading doesn't move)


def test_the_right_click_menu_and_the_keys_move_too(app):
	from PySide6.QtGui import QShortcut

	outline, doc = make()
	select(outline, B)
	names = [t for t, _s in outline._context_actions(row(outline, B))]
	assert all(n in names for n in ("Move up", "Move down", "Move to top", "Move to bottom"))
	dict(outline._context_actions(row(outline, B)))["Move to bottom"]()
	assert list(doc.data) == [A, C, D, B]
	keys = {s.key().toString() for s in outline.findChildren(QShortcut)}
	assert {"Alt+Up", "Alt+Down", "Alt+Home", "Alt+End"} <= keys
