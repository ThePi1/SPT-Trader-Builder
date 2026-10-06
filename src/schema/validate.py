"""Checking files: can SPT load them, and are they like what the base game ships?

An **error** is something SPT can't load or the game can't use (a missing key the server needs,
a wrong type, a broken link). A **warning** is something unlike the base game, or incomplete
(an empty item list, a task in a list vanilla never uses it in, an unknown key): the server may
load it anyway, and the game may or may not cope.
"""

import json
from functools import lru_cache
from pathlib import Path

from core.ids import is_id
from schema import locale as locale_schema
from schema import registry, server
from schema.choices import TASK_LIST_KEY, TASK_TIMING_OF
from schema.fields import IDLIST, REF
from schema.issues import ERROR, WARNING, Issue
from schema.quest import QUEST, text_pointers_ok

PROFILE_FILE = Path(__file__).resolve().parent / "vanilla_profile.json"

# Where a reward / task list key is called what in the quest ("Finish" for AvailableForFinish)
REWARD_LISTS = ("Success", "Started", "Fail")


@lru_cache(maxsize=1)
def profile():
	"""How the base game uses each kind: {kind name: {count, keys: {key: {count, types, values}}}}."""
	with open(PROFILE_FILE, encoding="utf-8") as f:
		return json.load(f)["kinds"]


def _profile_name(group, kind):
	return f"{group}:{kind}"


def validate_quests(quests, locale=None, gamedata=None):
	"""Every problem in a quests file ({quest id: quest}). locale ({key: text}) adds the text checks.
	gamedata (core.gamedata.GameData) adds checks against the real traders, items and maps."""
	issues = []
	if not isinstance(quests, dict):
		return [Issue(ERROR, (), "A quests file must be an object of quests, each under its own id.")]
	for quest_id, quest in quests.items():
		issues += validate_quest(quest, quest_id, gamedata)
	if locale is not None:
		issues += validate_quest_locale(quests, locale)
	return issues


def validate_quest(quest, quest_id=None, gamedata=None):
	"""Every problem in one quest."""
	quest_id = quest_id if quest_id is not None else (quest.get("_id") if isinstance(quest, dict) else None) or "?"
	root = (quest_id,)
	issues = server.check_record(quest, "Quest", root)
	if not isinstance(quest, dict):
		return issues
	if quest.get("_id") != quest_id:
		issues.append(Issue(ERROR, root + ("_id",), f"The quest's id ({quest.get('_id')}) doesn't match the id it is stored under ({quest_id})."))
	for key, value in text_pointers_ok(quest):
		issues.append(Issue(WARNING, root + (key,), f"Should be '{quest_id} {key}' so the game finds the quest's text (it is '{value}')."))
	issues += _profile_check(quest, "quest", "quest", root)
	issues += _check_choices(quest, QUEST, root, gamedata)

	ids = {}  # every task, subtask and reward id of the quest -> where
	conditions = quest.get("conditions") if isinstance(quest.get("conditions"), dict) else {}
	task_ids = set()
	for list_key, tasks in conditions.items():
		for task in tasks if isinstance(tasks, list) else []:
			if isinstance(task, dict) and isinstance(task.get("id"), str):
				task_ids.add(task["id"])
	for list_key, tasks in conditions.items():
		timing = TASK_TIMING_OF.get(list_key)
		if not isinstance(tasks, list):
			continue
		for i, task in enumerate(tasks):
			path = root + ("conditions", list_key, i)
			issues += _check_task(task, timing, path, ids, task_ids, gamedata)
	rewards = quest.get("rewards") if isinstance(quest.get("rewards"), dict) else {}
	for list_key, items in rewards.items():
		if not isinstance(items, list):
			continue
		for i, reward in enumerate(items):
			issues += _check_reward(reward, list_key, root + ("rewards", list_key, i), ids, gamedata)
	return issues


def _remember_id(ids, value, path, issues, what):
	if not isinstance(value, str) or not value:
		return
	if value in ids:
		issues.append(Issue(WARNING, path, f"The {what} id {value} is used twice in this quest."))
	else:
		ids[value] = path


def _check_task(task, timing, path, ids, task_ids, gamedata):
	issues = []
	if not isinstance(task, dict):
		return [Issue(ERROR, path, "A condition must be an object.")]
	_remember_id(ids, task.get("id"), path + ("id",), issues, "task")
	kind = registry.kind_of(task, "task")
	spec = registry.spec_of(task, "task")
	if not registry.is_known(task, "task"):
		issues.append(Issue(WARNING, path + ("conditionType",), f"'{kind}' is not a condition kind this app knows; it is kept as it is."))
		return issues
	if timing is not None and spec.vanilla_timing_use and timing not in spec.vanilla_timing_use:
		where = {"Start": "start", "Finish": "finish", "Fail": "fail"}[timing]
		issues.append(Issue(WARNING, path, f"The base game never puts a '{spec.label}' condition in the {where} list."))
	issues += _profile_check(task, "task", kind, path, skip=("visibilityConditions", "counter"))
	issues += _check_choices(task, spec, path, gamedata)
	issues += _check_required(task, spec, path)
	for j, visible in enumerate(task.get("visibilityConditions") or []):
		if isinstance(visible, dict) and visible.get("target") not in task_ids:
			issues.append(Issue(ERROR, path + ("visibilityConditions", j, "target"), "This points at a condition that isn't in the quest."))
	if kind == "CounterCreator":
		counter = task.get("counter")
		if not isinstance(counter, dict):
			issues.append(Issue(ERROR, path + ("counter",), "A Counter needs a 'counter' with its steps."))
		else:
			if not counter.get("id"):
				issues.append(Issue(WARNING, path + ("counter", "id"), "The counter has no id."))
			subs = counter.get("conditions") or []
			if not subs:
				issues.append(Issue(WARNING, path + ("counter", "conditions"), "This Counter has no steps yet. Add a subtask, such as Kill enemies."))
			for k, sub in enumerate(subs):
				issues += _check_subtask(sub, timing, path + ("counter", "conditions", k), ids, gamedata)
	return issues


def _check_subtask(sub, timing, path, ids, gamedata):
	issues = []
	if not isinstance(sub, dict):
		return [Issue(ERROR, path, "A subtask must be an object.")]
	_remember_id(ids, sub.get("id"), path + ("id",), issues, "subtask")
	kind = registry.kind_of(sub, "subtask")
	spec = registry.spec_of(sub, "subtask")
	if not registry.is_known(sub, "subtask"):
		issues.append(Issue(WARNING, path + ("conditionType",), f"'{kind}' is not a subtask kind this app knows; it is kept as it is."))
		return issues
	issues += _profile_check(sub, "subtask", kind, path)
	issues += _check_choices(sub, spec, path, gamedata)
	return issues


def _check_reward(reward, list_key, path, ids, gamedata):
	issues = []
	if not isinstance(reward, dict):
		return [Issue(ERROR, path, "A reward must be an object.")]
	_remember_id(ids, reward.get("id"), path + ("id",), issues, "reward")
	kind = registry.kind_of(reward, "reward")
	spec = registry.spec_of(reward, "reward")
	if not registry.is_known(reward, "reward"):
		issues.append(Issue(WARNING, path + ("type",), f"'{kind}' is not a reward kind this app knows; it is kept as it is."))
		return issues
	if spec.vanilla_timing_use and list_key not in spec.vanilla_timing_use:
		issues.append(Issue(WARNING, path, f"The base game never gives a '{spec.label}' reward in the {list_key} list."))
	issues += _profile_check(reward, "reward", kind, path, skip=("items",))
	issues += _check_choices(reward, spec, path, gamedata)
	issues += _check_required(reward, spec, path)
	if kind in ("Item", "AssortmentUnlock", "ProductionScheme"):
		issues += _check_reward_items(reward, path)
	return issues


def _check_reward_items(reward, path):
	issues = []
	items = reward.get("items")
	if not isinstance(items, list):
		return issues
	part_ids = {p.get("_id") for p in items if isinstance(p, dict)}
	if len(part_ids) != len(items):
		issues.append(Issue(ERROR, path + ("items",), "Two parts of this item share an id."))
	roots = [p for p in items if isinstance(p, dict) and not p.get("parentId")]
	if items and not roots:
		issues.append(Issue(ERROR, path + ("items",), "Every part is attached to another part; one must be the main item."))
	for i, part in enumerate(items):
		if not isinstance(part, dict):
			continue
		parent = part.get("parentId")
		if parent and parent not in part_ids:
			issues.append(Issue(ERROR, path + ("items", i, "parentId"), "This part is attached to a part that isn't in the list."))
		if parent and not part.get("slotId"):
			issues.append(Issue(WARNING, path + ("items", i, "slotId"), "A part attached to another needs a slot."))
	target = reward.get("target")
	if items and target not in part_ids:
		issues.append(Issue(ERROR, path + ("target",), "The reward's main item id isn't one of its parts."))
	return issues


def _check_required(item, spec, path):
	"""Warnings for the fields the spec marks required that are empty."""
	issues = []
	for field in spec.fields:
		if not field.required:
			continue
		value = item.get(field.key)
		if value in (None, "", [], {}):
			issues.append(Issue(WARNING, path + (field.key,), f"{field.label}: nothing chosen yet."))
	return issues


def _check_choices(item, spec, path, gamedata):
	"""Warnings for ids that don't exist, when the game data is known."""
	issues = []
	if gamedata is None:
		return issues
	for field in spec.fields:
		if field.kind not in (REF, IDLIST) or not field.ref:
			continue
		value = item.get(field.key)
		values = value if isinstance(value, list) else [value]
		for v in values:
			if not isinstance(v, str) or not v:
				continue
			if field.ref == "trader" and not gamedata.knows_trader(v):
				issues.append(Issue(WARNING, path + (field.key,), f"Trader {v} isn't in the game data."))
			elif field.ref == "item" and gamedata.items and not gamedata.knows_item(v):
				issues.append(Issue(WARNING, path + (field.key,), f"Item {v} isn't in the game's item list (a custom item?)."))
	return issues


def _profile_check(item, group, kind, path, skip=()):
	"""Warnings for keys and value types the base game never uses for this kind."""
	issues = []
	kinds = profile()
	name = "quest" if group == "quest" else _profile_name(group, kind)
	known = kinds.get(name)
	if known is None:
		return issues
	for key, value in item.items():
		if key in skip:
			continue
		seen = known["keys"].get(key)
		if seen is None:
			if key in ("conditions", "rewards") and group == "quest":
				continue
			issues.append(Issue(WARNING, path + (key,), f"The base game doesn't use '{key}' here."))
			continue
		kind_name = _type_name(value)
		if kind_name not in seen["types"] and not (kind_name in ("int", "float") and ("int" in seen["types"] or "float" in seen["types"])):
			issues.append(Issue(WARNING, path + (key,), f"The base game always has {_describe_types(seen['types'])} here, not {_describe_types({kind_name: 1})}."))
	return issues


def _type_name(value):
	if value is None:
		return "null"
	if isinstance(value, bool):
		return "bool"
	if isinstance(value, int):
		return "int"
	if isinstance(value, float):
		return "float"
	if isinstance(value, str):
		return "string"
	if isinstance(value, list):
		return "list"
	return "object"


_TYPE_WORDS = {"null": "empty", "bool": "true/false", "int": "a whole number", "float": "a number", "string": "text", "list": "a list", "object": "an object"}


def _describe_types(types):
	return " or ".join(_TYPE_WORDS.get(t, t) for t in types)


# --- locale ---------------------------------------------------------------------------------


def validate_locale(locale):
	"""Problems in a locale file on its own: not an object of text, wrong spellings, etc."""
	if not isinstance(locale, dict):
		return [Issue(ERROR, (), "A locale file must be an object of text, one entry per key.")]
	issues = []
	for key, text in locale.items():
		if not isinstance(text, str):
			issues.append(Issue(ERROR, (key,), "The text must be text (in quotes)."))
			continue
		parts = locale_schema.split_quest_key(key)
		if parts and parts[1] in locale_schema.MISSPELLED:
			right = locale_schema.quest_key(parts[0], locale_schema.MISSPELLED[parts[1]])
			issues.append(Issue(WARNING, (key,), f"Misspelled key; the game looks for '{right}'."))
	return issues


def validate_quest_locale(quests, locale):
	"""Problems in the text of the quests: missing or blank entries, misspelled keys."""
	issues = validate_locale(locale)
	for quest_id, quest in quests.items():
		if not isinstance(quest, dict):
			continue
		lacking = []
		for key, what in locale_schema.keys_for_quest(quest):
			if not locale_schema.is_needed(what) or locale.get(key):
				continue  # (text that isn't needed is never a problem, blank or not there)
			if what == "task":
				issues.append(Issue(WARNING, _task_path(quest_id, quest, key), "This condition has no text yet; the game would show its raw id."))
			else:
				lacking.append(_label(what))
		if lacking:
			issues.append(Issue(WARNING, (quest_id, "text"), "Text missing for: " + ", ".join(lacking) + "."))
	return issues


def _task_path(quest_id, quest, task_id):
	"""The path of the task with this id, so the problem points at it."""
	for list_key, tasks in (quest.get("conditions") or {}).items():
		for i, task in enumerate(tasks if isinstance(tasks, list) else []):
			if isinstance(task, dict) and task.get("id") == task_id:
				return (quest_id, "conditions", list_key, i, "id")
	return (quest_id, "text", task_id)


def _label(field):
	for f in locale_schema.QUEST_TEXT:
		if f.key == field:
			return f.label.lower()
	return field


def _what(what):
	return "a condition" if what == "task" else f"'{what}'"
