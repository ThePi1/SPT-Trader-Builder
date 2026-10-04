"""Only the text the game always fills in counts as missing: the name, description, completion message and Finish tasks."""

from schema import locale as L
from schema import registry, validate
from schema.quest import make_quest

NEEDED = {"name", "description", "successMessageText"}


def quest_with_finish_task():
	quest = make_quest(name="Q")
	task = registry.new_item("task", "HandoverItem")
	quest["conditions"]["AvailableForFinish"].append(task)
	return quest, task["id"]


def text_for(quest, *fields):
	return {L.quest_key(quest["_id"], f): "text" for f in fields}


def text_problems(quest, locale):
	return [i.message for i in validate.validate_quest_locale({quest["_id"]: quest}, locale)]


def test_only_the_name_description_and_completion_message_are_needed():
	assert set(L.QUEST_TEXT_NEEDED) == NEEDED
	assert {f.key for f in L.QUEST_TEXT if f.needed} == NEEDED


def test_the_other_fields_are_never_missing_even_when_absent_or_blank():
	quest, task_id = quest_with_finish_task()
	locale = {**text_for(quest, *NEEDED), task_id: "Hand it over", L.quest_key(quest["_id"], "acceptPlayerMessage"): ""}
	assert text_problems(quest, locale) == []  # (the replies and failure message are absent or blank)
	assert L.missing_keys({quest["_id"]: quest}, locale) == {}


def test_each_needed_field_and_finish_task_is_reported_when_absent_or_blank():
	quest, task_id = quest_with_finish_task()
	for field in NEEDED:
		for locale in (
			{**text_for(quest, *NEEDED - {field}), task_id: "x"},
			{**text_for(quest, *NEEDED - {field}), L.quest_key(quest["_id"], field): "", task_id: "x"},
		):
			assert any("Text missing for" in m for m in text_problems(quest, locale)), field
			assert list(L.missing_keys({quest["_id"]: quest}, locale)) == [L.quest_key(quest["_id"], field)]
	locale = text_for(quest, *NEEDED)
	assert any("condition has no text" in m for m in text_problems(quest, locale))
	assert L.missing_keys({quest["_id"]: quest}, locale) == {task_id: "task"}


def test_optional_adds_the_optional_text_to_what_is_missing():
	quest, _task_id = quest_with_finish_task()
	needed_only = set(L.missing_keys({quest["_id"]: quest}, {}))
	everything = set(L.missing_keys({quest["_id"]: quest}, {}, optional=True))
	assert needed_only < everything
	assert L.quest_key(quest["_id"], "acceptPlayerMessage") in everything - needed_only


def test_the_base_game_has_nothing_missing(vanilla_quests, vanilla_locale):
	assert L.missing_keys(vanilla_quests, vanilla_locale) == {}
