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
		outline.add_item("task", kind)
	outline.add_item("reward", "Experience")
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


def test_copy_delete_move_retime(app):
	outline, doc = make()
	outline.add_quest()
	outline.add_item("reward", "Experience")
	outline.copy_selected()
	quest = next(iter(doc.data.values()))
	rewards = quest["rewards"]["Success"]
	assert len(rewards) == 2 and rewards[0]["id"] != rewards[1]["id"]
	outline.move_selected(-1)
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
	outline.add_item("task", "Level")
	outline.add_item("task", "HandoverItem")
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
