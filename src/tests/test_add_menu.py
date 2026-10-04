"""The Add menu (the button's, and the right-click one) offers what fits the selected item, and adds to the open list."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication

from core.documents import Document
from ui.quest_outline import ROLE, QuestOutline

SUBTASK = "Subtask (in this counter)"


@pytest.fixture(scope="module")
def app():
	return QApplication.instance() or QApplication([])


def make():
	outline = QuestOutline()
	doc = Document({})
	outline.set_document(doc)
	return outline, doc


def menu_texts(outline):
	outline._fill_add_menu()
	return [a.text() for a in outline.add_menu.actions() if not a.isSeparator()]


def select(outline, kind, group=None, timing=None, index=None):
	"""Select the tree item of this kind (and list, and place in its list)."""
	for item in outline._walk():
		a = item.data(0, ROLE)
		if a.kind == kind and (group is None or a.group == group) and (timing is None or a.timing == timing) and (index is None or a.path[-1] == index):
			outline.tree.setCurrentItem(item)
			return item
	raise AssertionError((kind, group, timing, index))


def add(outline, group, kind):
	outline.add_item(group, kind)


def test_nothing_selected_offers_only_a_new_quest(app):
	outline, doc = make()
	assert menu_texts(outline) == ["New quest"]
	outline.add_quest()
	assert len(doc.data) == 1
	outline.tree.clearSelection()  # (a click on blank space)
	assert menu_texts(outline) == ["New quest"]
	assert "Add" == outline._context_actions(None)[0][0] and menu_texts(outline) == ["New quest"]  # (the right-click menu on blank space)


def test_new_quest_is_in_the_add_menu_and_the_button_is_gone(app):
	outline, doc = make()
	assert not hasattr(outline, "new_quest_button")
	outline._fill_add_menu()
	next(a for a in outline.add_menu.actions() if a.text() == "New quest").trigger()
	assert len(doc.data) == 1 and outline._current().kind == "quest"
	assert menu_texts(outline)[0] == "New quest"  # (still there with a quest selected)


def test_a_quest_offers_conditions_and_rewards_and_adds_to_finish_and_success(app):
	outline, doc = make()
	outline.add_quest()
	quest = next(iter(doc.data.values()))
	select(outline, "quest")
	assert menu_texts(outline) == ["New quest", "Condition", "Reward"]
	add(outline, "task", "Level")
	select(outline, "quest")
	add(outline, "reward", "Experience")
	assert len(quest["conditions"]["AvailableForFinish"]) == 1 and not quest["conditions"]["AvailableForStart"]
	assert len(quest["rewards"]["Success"]) == 1


def test_a_condition_list_offers_only_conditions_and_adds_to_that_list(app):
	outline, doc = make()
	outline.add_quest()
	quest = next(iter(doc.data.values()))
	for timing, key in (("Start", "AvailableForStart"), ("Fail", "Fail"), ("Finish", "AvailableForFinish")):
		select(outline, "group", "task", timing)
		assert menu_texts(outline) == ["New quest", "Condition"]
		add(outline, "task", "HandoverItem")
		assert len(quest["conditions"][key]) == 1, timing


def test_a_plain_condition_offers_conditions_and_adds_to_its_own_list(app):
	outline, doc = make()
	outline.add_quest()
	quest = next(iter(doc.data.values()))
	select(outline, "group", "task", "Fail")
	add(outline, "task", "HandoverItem")  # (selected afterwards)
	assert outline._current().kind == "task" and menu_texts(outline) == ["New quest", "Condition"]
	add(outline, "task", "Level")
	assert len(quest["conditions"]["Fail"]) == 2 and not quest["conditions"]["AvailableForFinish"]


def test_a_counter_or_subtask_offers_subtasks_and_conditions(app):
	outline, doc = make()
	outline.add_quest()
	quest = next(iter(doc.data.values()))
	select(outline, "group", "task", "Fail")
	add(outline, "task", "CounterCreator")
	assert menu_texts(outline) == ["New quest", SUBTASK, "Condition"]
	add(outline, "subtask", "Kills")  # (under the Counter)
	counter = quest["conditions"]["Fail"][0]
	assert len(counter["counter"]["conditions"]) == 1
	assert outline._current().kind == "subtask" and menu_texts(outline) == ["New quest", SUBTASK, "Condition"]
	add(outline, "task", "HandoverItem")  # (a subtask is selected: the condition goes in the Counter's list)
	assert [t["conditionType"] for t in quest["conditions"]["Fail"]] == ["CounterCreator", "HandoverItem"]
	select(outline, "task", "task", "Fail", 0)
	add(outline, "task", "Level")  # (the Counter is selected: same list)
	assert len(quest["conditions"]["Fail"]) == 3 and not quest["conditions"]["AvailableForFinish"]


def test_rewards_offer_only_rewards_and_add_to_the_open_list_else_success(app):
	outline, doc = make()
	outline.add_quest()
	quest = next(iter(doc.data.values()))
	select(outline, "group", "rewards")  # (the Rewards heading)
	assert menu_texts(outline) == ["New quest", "Reward"]
	add(outline, "reward", "Experience")
	assert len(quest["rewards"]["Success"]) == 1
	select(outline, "group", "reward", "Started")
	assert menu_texts(outline) == ["New quest", "Reward"]
	add(outline, "reward", "Experience")
	assert len(quest["rewards"]["Started"]) == 1
	assert outline._current().kind == "reward" and menu_texts(outline) == ["New quest", "Reward"]
	add(outline, "reward", "Skill")  # (a reward is selected: its own list)
	assert len(quest["rewards"]["Started"]) == 2 and len(quest["rewards"]["Success"]) == 1


def test_the_right_click_add_is_the_same_menu(app):
	outline, doc = make()
	outline.add_quest()
	select(outline, "group", "task", "Start")
	item = outline.tree.currentItem()
	actions = dict(outline._context_actions(item))
	assert actions["Add"] is outline.add_menu
	assert menu_texts(outline) == ["New quest", "Condition"]
	assert "Task" not in [a.text() for a in outline.add_menu.actions()]


def test_the_condition_menu_lists_conditions_by_their_new_names(app):
	outline, doc = make()
	outline.add_quest()
	select(outline, "quest")
	outline._fill_add_menu()
	actions = {a.text(): a for a in outline.add_menu.actions()}
	texts = [a.text() for a in actions["Condition"].menu().actions()]
	assert "Counter (subtask container)" in texts and "Quest state" in texts and "Player level" in texts
	assert "In-raid objective" not in texts and "Another quest" not in texts
