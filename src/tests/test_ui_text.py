import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication, QLineEdit

from core.documents import Document
from schema import locale as L
from ui.locale_tab import LocaleTab
from ui.quest_outline import QuestOutline
from ui.text_panels import QuestTextPanel, TaskTextPanel


@pytest.fixture(scope="module")
def app():
	return QApplication.instance() or QApplication([])


def test_quest_text_panel_writes_to_the_locale(app):
	from schema.quest import make_quest

	quest = make_quest(name="Q")
	locale = Document({})
	panel = QuestTextPanel(locale, quest)
	box = panel.findChild(QLineEdit)
	box.setText("Hello")
	box.textEdited.emit("Hello")
	assert locale.data == {f"{quest['_id']} name": "Hello"}
	locale.undo()
	assert locale.data == {}


def test_blank_untouched_text_is_not_written(app):
	from PySide6.QtWidgets import QPlainTextEdit

	locale = Document({})
	panel = TaskTextPanel(locale, "a" * 24, "Finish")
	panel.findChild(QPlainTextEdit).setPlainText("")
	assert locale.data == {}


def test_copying_a_quest_copies_its_text(app):
	quests, locale = Document({}), Document({})
	outline = QuestOutline()
	outline.locale = locale
	outline.set_document(quests)
	outline.add_quest()
	outline.add_item("task", "HandoverItem")
	quest = next(iter(quests.data.values()))
	task_id = quest["conditions"]["AvailableForFinish"][0]["id"]
	locale.set_value("x", (f"{quest['_id']} name",), "Name")
	locale.set_value("x", (task_id,), "Hand it over")
	outline._select_key(("quest", (quest["_id"],)))
	outline.copy_selected()
	assert len(quests.data) == 2
	assert sorted(locale.data.values()) == ["Hand it over", "Hand it over", "Name", "Name"]


def test_locale_tab_filters_and_adds_missing(app):
	from schema.quest import make_quest

	quest = make_quest(name="Q")
	quests, locale = Document({quest["_id"]: quest}), Document({"unrelated": "text"})
	tab = LocaleTab(locale, quests)
	assert tab.model.total == 1
	tab.add_missing()
	assert tab.mode.currentData() == "mine"  # (shows everything that was added)
	assert all(k.startswith(quest["_id"]) for k in locale.data if k != "unrelated")
	assert {k.split(" ", 1)[1] for k in locale.data if k != "unrelated"} == set(L.QUEST_TEXT_KEYS)  # (every field, needed or not)
	index = tab.model.index(0, 2)
	tab.model.setData(index, "typed")
	assert "typed" in locale.data.values()


def test_add_all_missing_fields_adds_the_condition_text_the_game_uses(app):
	from schema import registry
	from schema.quest import make_quest

	quest = make_quest(name="Q")
	ids = {}
	for timing, key in (("Finish", "AvailableForFinish"), ("Fail", "Fail"), ("Start", "AvailableForStart")):
		task = registry.new_item("task", "CounterCreator" if timing == "Finish" else "HandoverItem")
		quest["conditions"][key].append(task)
		ids[timing] = task["id"]
	counter = quest["conditions"]["AvailableForFinish"][0]
	counter["counter"]["conditions"].append(registry.new_item("subtask", "Kills"))
	locale = Document({ids["Fail"]: "Already written"})
	tab = LocaleTab(locale, Document({quest["_id"]: quest}))
	tab.add_missing()
	assert locale.data[ids["Finish"]] == "" and locale.data[ids["Fail"]] == "Already written"  # (kept, not blanked)
	assert ids["Start"] not in locale.data  # (the game writes the text of Start conditions itself)
	assert counter["counter"]["id"] not in locale.data and counter["counter"]["conditions"][0]["id"] not in locale.data  # (subtasks have none)
	assert {k for k in locale.data if k.startswith(quest["_id"])} == {L.quest_key(quest["_id"], f) for f in L.QUEST_TEXT_KEYS}
	locale.data.pop(ids["Fail"])
	tab.add_missing()
	assert locale.data[ids["Fail"]] == ""  # (a Fail condition's text is added too)
