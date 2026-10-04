"""Everything the app creates must be valid and look like what the base game has."""

import pytest

from schema import locale, registry, rewards, server, subtasks, tasks, validate
from schema.choices import TASK_LIST_KEY
from schema.issues import errors
from schema.quest import make_quest


def quest_with(task=None, timing="Finish", reward=None, reward_timing="Success"):
	quest = make_quest(name="Test", trader_id="54cb50c76803fa8b248b4571")
	if task is not None:
		quest["conditions"][TASK_LIST_KEY[timing]].append(task)
	if reward is not None:
		quest["rewards"][reward_timing].append(reward)
	return quest


def test_new_quest_has_no_errors():
	quest = make_quest(name="Test", trader_id="54cb50c76803fa8b248b4571")
	assert not errors(validate.validate_quest(quest))


def test_new_quest_text_keys_point_at_its_id():
	quest = make_quest()
	assert quest["name"] == f"{quest['_id']} name"
	from schema.quest import text_pointers_ok

	assert not text_pointers_ok(quest)


@pytest.mark.parametrize("kind", sorted(tasks.TASKS))
def test_new_task_is_valid(kind):
	spec = tasks.TASKS[kind]
	task = registry.new_item("task", kind)
	quest = quest_with(task, spec.default_timing())
	issues = validate.validate_quest(quest)
	assert not errors(issues), [str(i) for i in errors(issues)]


@pytest.mark.parametrize("kind", sorted(tasks.TASKS))
def test_new_task_has_only_keys_the_base_game_uses(kind):
	spec = tasks.TASKS[kind]
	profile_keys = set(validate.profile()[f"task:{kind}"]["keys"]) if f"task:{kind}" in validate.profile() else None
	if profile_keys is None:
		pytest.skip("kind not in the sample")
	extra = set(spec.base) - profile_keys - {"visibilityConditions", "counter"}
	assert not extra, extra


@pytest.mark.parametrize("kind", sorted(subtasks.SUBTASKS))
def test_new_subtask_is_valid_and_vanilla_like(kind):
	spec = subtasks.SUBTASKS[kind]
	sub = registry.new_item("subtask", kind)
	assert not server.check(sub, "QuestConditionCounterCondition")
	profile = validate.profile().get(f"subtask:{kind}")
	if profile:
		assert not set(spec.base) - set(profile["keys"])


@pytest.mark.parametrize("kind", sorted(rewards.REWARDS))
def test_new_reward_is_valid_and_vanilla_like(kind):
	spec = rewards.REWARDS[kind]
	reward = registry.new_item("reward", kind)
	quest = quest_with(reward=reward, reward_timing=spec.default_timing())
	assert not errors(validate.validate_quest(quest))
	profile = validate.profile().get(f"reward:{kind}")
	if profile:
		assert not set(spec.base) - set(profile["keys"]) - {"items"}


def test_every_field_of_every_spec_is_known_to_the_server_models():
	"""A form field for a key the server ignores would do nothing in the game."""
	records = {
		"task": "QuestCondition", "subtask": "QuestConditionCounterCondition", "reward": "Reward", "quest": "Quest",
	}
	missing = []
	groups = {"task": tasks.TASKS, "subtask": subtasks.SUBTASKS, "reward": rewards.REWARDS}
	for group, specs in groups.items():
		props = server.record(records[group])["properties"]
		for spec in specs.values():
			for field in spec.fields:
				if field.key.split(".")[0] not in props:
					missing.append((group, spec.kind, field.key))
	assert not missing, missing


def test_locale_keys_of_a_new_quest():
	quest = make_quest(name="Test")
	keys = dict(locale.keys_for_quest(quest))
	assert f"{quest['_id']} name" in keys
	assert f"{quest['_id']} startedMessageText" not in keys
	assert f"{quest['_id']} startedMessageText" in dict(locale.keys_for_quest(quest, optional=True))
