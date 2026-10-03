"""What the Schema Explorer shows: the kinds the app knows and their fields, and checking a whole file."""

from schema import assort as assort_schema
from schema import fields as F
from schema import registry, validate
from schema.issues import ERROR, Issue
from schema.quest import QUEST

KIND_WORDS = {
	F.TEXT: "Text", F.MULTILINE: "Text", F.INT: "Whole number", F.NUMBER: "Number", F.BOOL: "Yes / no",
	F.CHOICE: "Pick one", F.REF: "An id", F.LIST: "List", F.IDLIST: "List of ids", F.GROUPS: "Groups of values",
	F.OBJECT: "A few settings", F.REWARD_ITEMS: "Item parts", F.VISIBILITY: "Conditions", F.JSON: "Anything (JSON)",
}
GROUP_TITLES = (
	("quest", "Quest"), ("task", "Tasks"), ("subtask", "Subtasks (steps of an in-raid objective)"), ("reward", "Rewards"),
)
FILE_KINDS = (
	("quests", "Quests"), ("locale", "Text (locale)"), ("assort", "Trader assort"), ("questassort", "Quest locks for assort"),
)


def all_specs():
	"""[(group title, [Spec])] in the order the explorer lists them."""
	out = []
	for group, title in GROUP_TITLES:
		specs = [QUEST] if group == "quest" else registry.kinds(group)
		out.append((title, specs))
	return out


def field_rows(spec):
	"""[(label, key, kind words, 'Needed' / 'Optional', default text, shown under More)] for a spec's fields."""
	rows = []
	for field in spec.fields:
		default = field.default if field.default is not None else spec.base.get(field.key)
		rows.append((
			field.label, field.key, KIND_WORDS.get(field.kind, field.kind), "Needed" if field.required else "Optional",
			"" if default is None else str(default), field.advanced,
		))
	return rows


def detect_kind(data):
	"""'quests', 'locale', 'assort', 'questassort' for the shape of a loaded JSON file, or None."""
	if not isinstance(data, dict):
		return None
	if {"items", "barter_scheme"} <= set(data):
		return "assort"
	if data and set(data) <= set(assort_schema.QUEST_LOCKS):
		return "questassort"
	values = list(data.values())
	if values and all(isinstance(v, dict) and ("conditions" in v or "rewards" in v) for v in values[:20]):
		return "quests"
	if not values or all(isinstance(v, str) for v in values[:50]):
		return "locale"
	return None


def check(data, kind, quests=None, locale=None, gamedata=None):
	"""Every problem in a loaded file of this kind. quests lets a questassort or text check use the quests."""
	if kind == "quests":
		return validate.validate_quests(data, locale, gamedata)
	if kind == "locale":
		return validate.validate_quest_locale(quests, data) if quests else validate.validate_locale(data)
	if kind == "assort":
		return assort_schema.validate_assort(data)
	if kind == "questassort":
		return assort_schema.validate_questassort(data, quest_ids=set(quests) if quests else None)
	return [Issue(ERROR, (), "This file isn't one the app knows how to check.")]
