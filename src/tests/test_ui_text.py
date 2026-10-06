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


# --- Generate locale (Find items and Hand over items) ------------------------------------------------------------

def names_for(**known):
	class Names:
		def item(self, tpl):
			return known.get(tpl, tpl[:12])

	return Names()


def test_the_text_of_a_find_or_hand_over_task_is_made_from_its_items():
	names = names_for(a="Salewa", b="Bandage", c="Splint")
	find = {"conditionType": "FindItem", "target": ["a"], "onlyFoundInRaid": False}
	assert L.generated_task_text(find, names) == "Find Salewa"
	assert L.generated_task_text({**find, "onlyFoundInRaid": True}, names) == "Find Salewa in raid"
	assert L.generated_task_text({**find, "conditionType": "HandoverItem", "onlyFoundInRaid": True}, names) == "Hand over Salewa"  # (found in raid is only said for Find)
	assert L.generated_task_text({**find, "target": ["a", "b", "c"]}, names) == "Find Salewa, Bandage or Splint"
	assert L.generated_task_text({**find, "target": ["a", "b"], "onlyFoundInRaid": True}, names) == "Find Salewa or Bandage in raid"
	assert L.generated_task_text({**find, "target": []}, names) == "" and L.generated_task_text({"conditionType": "Kills", "target": ["a"]}, names) == ""


def outline_with_task(kind):
	quests, locale = Document({}), Document({})
	outline = QuestOutline()
	outline.locale = locale
	outline.set_document(quests)
	outline.add_quest()
	outline.add_item("task", kind)
	quest = next(iter(quests.data.values()))
	task = quest["conditions"]["AvailableForFinish"][0]
	outline._select_key(("task", (quest["_id"], "conditions", "AvailableForFinish", 0)))
	return outline, locale, task


def generate_button(outline):
	from PySide6.QtWidgets import QPushButton

	return next((b for b in outline.pane.findChildren(QPushButton) if b.text() == "Generate locale"), None)


def test_generate_locale_fills_the_locale_box_of_a_find_task_and_writes_it(app, monkeypatch):
	from PySide6.QtWidgets import QPlainTextEdit

	outline, locale, task = outline_with_task("FindItem")
	task["target"] = ["5448bd6b4bdc2dfc2f8b4569"]
	task["onlyFoundInRaid"] = True
	outline._select_key(outline._current_key())  # (the form shows the edited task)
	button = generate_button(outline)
	assert button is not None
	told = []
	monkeypatch.setattr("ui.quest_outline.QMessageBox.information", lambda *a: told.append(a))
	button.click()
	assert locale.data[task["id"]] == "Find 5448bd6b4bd... in raid" and not told  # (no game data open: the id stands for the name)
	assert outline.pane.findChild(QPlainTextEdit).toPlainText() == "Find 5448bd6b4bd... in raid"  # (the box shows it)
	locale.undo()
	assert task["id"] not in locale.data


def test_generate_locale_on_a_hand_over_task_and_without_an_item(app, monkeypatch):
	outline, locale, task = outline_with_task("HandoverItem")
	told = []
	monkeypatch.setattr("ui.quest_outline.QMessageBox.information", lambda *a: told.append(a[2]))
	generate_button(outline).click()
	assert locale.data == {} and told == ["Choose the item (or the skill) first: the text is made from its name."]
	task["target"] = ["5448bd6b4bdc2dfc2f8b4569"]
	outline._select_key(outline._current_key())
	generate_button(outline).click()
	assert locale.data[task["id"]] == "Hand over 5448bd6b4bd..."


def test_only_find_and_hand_over_tasks_have_a_generate_locale_button(app):
	outline, _locale, _task = outline_with_task("Kills")
	assert generate_button(outline) is None
	outline.locale = None
	outline, _locale, _task = outline_with_task("FindItem")
	outline.locale = None
	outline._select_key(outline._current_key())
	assert generate_button(outline) is None  # (no locale open: nowhere to put the text)


def test_the_text_of_a_skill_level_task_names_the_skill_as_the_game_does():
	from core.gamedata import GameData
	from core.paths import BUNDLED_DATABASE_DIR
	from schema.common import PLAIN, Names

	data = Names(GameData(None, "en", BUNDLED_DATABASE_DIR))
	skill = {"conditionType": "Skill", "target": "Sniper", "value": 7}
	assert L.generated_task_text(skill, data) == "Reach the required Bolt-action Rifles skill level"  # (the base game's own words for it)
	assert L.generated_task_text({**skill, "target": "Endurance"}, data) == "Reach the required Endurance skill level"
	assert L.generated_task_text({**skill, "target": "MadeUp"}, data) == "Reach the required MadeUp skill level"  # (a skill the locale doesn't know: as written)
	assert L.generated_task_text(skill, PLAIN) == "Reach the required Sniper skill level"  # (no game data: the id)
	assert L.generated_task_text({**skill, "target": ""}, data) == ""


def test_a_skill_level_task_has_a_generate_locale_button_that_fills_its_box(app, monkeypatch):
	from core.gamedata import GameData
	from core.paths import BUNDLED_DATABASE_DIR

	outline, locale, task = outline_with_task("Skill")
	outline.gamedata = GameData(None, "en", BUNDLED_DATABASE_DIR)
	task["target"] = "Sniper"
	outline._select_key(outline._current_key())
	generate_button(outline).click()
	assert locale.data[task["id"]] == "Reach the required Bolt-action Rifles skill level"
