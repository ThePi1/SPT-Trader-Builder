import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication

from core.documents import Document
from schema import validate
from schema.issues import errors
from ui.quest_outline import ROLE, QuestOutline


def fix_trader(doc):
	for quest in doc.data.values():
		quest["traderId"] = "54cb50c76803fa8b248b4571"


@pytest.fixture(scope="module")
def app():
	return QApplication.instance() or QApplication([])


def add_to_quest(outline, group, kind):
	"""Add with the quest row selected (no list chosen), so the item goes where the base game usually puts it."""
	outline.tree.setCurrentItem(outline.tree.topLevelItem(0))
	outline.add_item(group, kind)


def make(data=None):
	outline = QuestOutline()
	doc = Document(data if data is not None else {})
	outline.set_document(doc)
	return outline, doc


def test_new_quest_task_reward_are_valid(app):
	outline, doc = make()
	outline.add_quest()
	assert len(doc.data) == 1
	for kind in ("HandoverItem", "Level", "CounterCreator"):
		add_to_quest(outline, "task", kind)
	add_to_quest(outline, "reward", "Experience")
	counter = outline.tree.currentItem()
	outline.tree.setCurrentItem(next(i for i in outline._walk() if i.data(0, ROLE).kind == "task" and i.data(0, ROLE).path[-1] == 1))
	outline.add_item("subtask", "Kills")
	fix_trader(doc)
	assert not errors(validate.validate_quests(doc.data))


def test_counter_subtasks_and_undo(app):
	outline, doc = make()
	outline.add_quest()
	outline.add_item("task", "CounterCreator")
	outline.add_item("subtask", "Kills")
	quest = next(iter(doc.data.values()))
	counter = quest["conditions"]["AvailableForFinish"][0]
	assert len(counter["counter"]["conditions"]) == 1
	doc.undo()
	assert counter["counter"]["conditions"] == [] or quest["conditions"]["AvailableForFinish"][0]["counter"]["conditions"] == []


def test_copy_delete_retime(app):
	outline, doc = make()
	outline.add_quest()
	outline.add_item("reward", "Experience")
	outline.copy_selected()
	quest = next(iter(doc.data.values()))
	rewards = quest["rewards"]["Success"]
	assert len(rewards) == 2 and rewards[0]["id"] != rewards[1]["id"]
	outline.retime(outline._current(), "Started")
	assert len(quest["rewards"]["Started"]) == 1
	outline.delete_selected()
	assert not quest["rewards"]["Started"]


def test_copy_quest_gets_new_ids(app):
	outline, doc = make()
	outline.add_quest()
	outline.add_item("task", "Level")
	outline._select_key(("quest", (next(iter(doc.data)),)))
	outline.copy_selected()
	assert len(doc.data) == 2
	fix_trader(doc)
	assert not errors(validate.validate_quests(doc.data))


def test_opens_every_vanilla_quest(app, vanilla_quests):
	import itertools

	outline, doc = make(dict(itertools.islice(vanilla_quests.items(), 40)))
	assert outline.tree.topLevelItemCount() == 40
	before = repr(doc.data)
	for item in outline._walk():
		outline.tree.setCurrentItem(item)
	assert repr(doc.data) == before


def test_problems_are_listed_and_jump(app):
	outline, doc = make()
	outline.add_quest()
	outline.add_item("task", "CounterCreator")  # a Counter with no steps is a problem
	outline.check()
	assert outline.problems.list.count() >= 1
	items = [outline.problems.list.item(i) for i in range(outline.problems.list.count())]
	item = next(i for i in items if "no steps" in i.text())
	outline.problems.activated.emit(item.data(256))
	assert outline._current().kind in ("task", "quest")


def test_item_reward_parts_editor(app):
	from core import parts as P

	outline, doc = make()
	outline.picker = lambda ref, multi, parent: ["a" * 24]
	outline.add_quest()
	outline.add_item("reward", "Item")
	from ui.parts_editor import PartsEditor

	editor = outline.pane.findChild(PartsEditor)
	assert editor is not None
	editor.add_item()
	reward = next(iter(doc.data.values()))["rewards"]["Success"][0]
	assert len(reward["items"]) == 1 and reward["target"] == reward["items"][0]["_id"]
	outline.picker = lambda ref, multi, parent: ["b" * 24]
	editor.ctx.picker = outline.picker
	editor._ask_slot = lambda parent, tpl: "mod_x"  # no template data, so it would ask
	editor.add_item()
	assert [p.get("slotId") for p in reward["items"]] == [None, "mod_x"]
	assert P.roots(reward["items"])[0]["_id"] == reward["target"]


def test_problems_list_can_be_hidden_and_the_choice_is_remembered(app, tmp_path):
	from core.settings import Settings

	ini = tmp_path / "settings.ini"
	ini.write_text("[display]\nshow_all_fields = false\n", encoding="utf-8")
	settings = Settings.load(ini)
	outline = QuestOutline(None, settings)
	outline.set_document(Document({"a" * 24: {"QuestName": "x"}}))
	outline.show()
	assert not outline.problems.list.isVisible() and settings.problems_collapsed  # (hidden unless the user opens it)
	assert outline.problems.header.text()  # (the counts stay)
	outline.problems.header.click()
	assert outline.problems.list.isVisible() and not settings.problems_collapsed
	assert "problems_collapsed = false" in ini.read_text(encoding="utf-8")
	assert not Settings.load(ini).problems_collapsed
	again = QuestOutline(None, Settings.load(ini))
	again.show()
	assert again.problems.list.isVisible()  # (a new window starts the way it was left)
	again.problems.header.click()
	assert not again.problems.list.isVisible()


def test_only_show_after_offers_the_other_tasks_of_the_quest(app):
	from ui import forms

	outline, doc = make()
	outline.add_quest()
	add_to_quest(outline, "task", "Level")
	add_to_quest(outline, "task", "HandoverItem")
	hand_over = outline.tree.currentItem()
	task_id = doc.data[next(iter(doc.data))]["conditions"]["AvailableForFinish"][0]["id"]
	pane = outline.pane
	control = next(w for w in pane.findChildren(forms.VisibilityControl))
	assert [tid for tid, _label in control.ctx.tasks] != [] and task_id not in [tid for tid, _l in control.ctx.tasks]
	assert any("Level" in label for _tid, label in control.ctx.tasks)
	control.combo.setCurrentIndex(0)
	control._add()
	conditions = doc.data[next(iter(doc.data))]["conditions"]["AvailableForFinish"][0]["visibilityConditions"]
	assert len(conditions) == 1 and conditions[0]["target"] == control.ctx.tasks[0][0]


def select_group(outline, kind, timing):
	outline.tree.setCurrentItem(next(
		i for i in outline._walk() if i.data(0, ROLE).kind == "group" and i.data(0, ROLE).group == kind and i.data(0, ROLE).timing == timing
	))


def test_a_task_goes_in_the_list_that_is_open_even_if_the_base_game_never_does_that(app):
	outline, doc = make()
	outline.add_quest()
	quest = next(iter(doc.data.values()))
	select_group(outline, "task", "Finish")
	outline.add_item("task", "Level")  # (the base game only puts Player level in Start)
	assert [t["conditionType"] for t in quest["conditions"]["AvailableForFinish"]] == ["Level"]
	assert not quest["conditions"]["AvailableForStart"]
	fix_trader(doc)
	issues = validate.validate_quests(doc.data)
	assert not errors(issues)  # (it only warns)
	assert any("never puts a 'Player level' task in the finish list" in i.message for i in issues)


def test_a_new_item_with_no_list_open_goes_in_the_one_the_base_game_uses_most(app):
	outline, doc = make()
	outline.add_quest()
	quest = next(iter(doc.data.values()))
	add_to_quest(outline, "task", "Level")
	add_to_quest(outline, "task", "HandoverItem")
	add_to_quest(outline, "reward", "TraderStanding")
	assert len(quest["conditions"]["AvailableForStart"]) == 1 and len(quest["conditions"]["AvailableForFinish"]) == 1
	assert len(quest["rewards"]["Success"]) == 1


def test_the_when_row_offers_every_list(app):
	from PySide6.QtWidgets import QComboBox

	outline, doc = make()
	outline.add_quest()
	outline.add_item("task", "Level")
	combos = outline.findChildren(QComboBox)
	assert any([c.itemText(i) for i in range(c.count())] == ["Start", "Finish", "Fail"] for c in combos)
	outline.add_item("reward", "Experience")
	combos = outline.findChildren(QComboBox)
	assert any([c.itemText(i) for i in range(c.count())] == ["Success", "Started", "Fail"] for c in combos)
