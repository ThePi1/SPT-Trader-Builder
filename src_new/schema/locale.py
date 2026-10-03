"""Locale: the text the game shows for quests and tasks.

The quest JSON holds no text, only keys. A quest's own keys are ``"<quest id> <field>"``
(its ``name``, ``description``, ...); a task's key is its id. The text is in a locale file: a
flat ``{key: text}`` JSON, one file per language.

What the base game does (checked against its en.json): every quest has text for the fields in
QUEST_TEXT_USED and never for the three optional ones; every Finish task has text, Start tasks
have none (the game writes their text itself), Fail tasks sometimes do.
"""

from dataclasses import dataclass

from schema.choices import TASK_LIST_KEY


@dataclass(frozen=True)
class TextField:
	key: str  # the quest key, also the locale key suffix
	label: str
	multiline: bool
	used: bool  # the base game writes it for every quest
	needed: bool = False  # the base game never leaves it blank


QUEST_TEXT = (
	TextField("name", "Quest name", False, True, True),
	TextField("description", "Description", True, True, True),
	TextField("acceptPlayerMessage", "Reply when accepting", True, True),
	TextField("declinePlayerMessage", "Reply when declining", True, True),
	TextField("completePlayerMessage", "Reply when completing", True, True),
	TextField("successMessageText", "Message on completion", True, True, True),
	TextField("failMessageText", "Message on failure", True, True),
	TextField("startedMessageText", "Message on start", True, False),
	TextField("changeQuestMessageText", "Message on change", True, False),
	TextField("note", "Note", True, False),
)
QUEST_TEXT_KEYS = tuple(f.key for f in QUEST_TEXT)
QUEST_TEXT_USED = tuple(f.key for f in QUEST_TEXT if f.used)
QUEST_TEXT_NEEDED = tuple(f.key for f in QUEST_TEXT if f.needed)

# Old versions of this tool wrote some keys with the wrong spelling
MISSPELLED = {"successMessagetext": "successMessageText"}


def quest_key(quest_id, field):
	return f"{quest_id} {field}"


def split_quest_key(key):
	"""("<quest id>", "<field>") for a quest text key, or None for any other key."""
	quest_id, _, field = key.partition(" ")
	if len(quest_id) == 24 and field and all(c in "0123456789abcdefABCDEF" for c in quest_id):
		return quest_id, field
	return None


def task_text_needed(timing):
	"""'needed' (Finish), 'optional' (Fail) or 'none' (Start) for a task in this list ('Finish', ...)."""
	return {"Finish": "needed", "Fail": "optional"}.get(timing, "none")


def quest_tasks(quest):
	"""[(task id, timing, task)] for the tasks of a quest that can have text, with the timing
	as 'Start' / 'Finish' / 'Fail'."""
	found = []
	for timing, list_key in (("Finish", TASK_LIST_KEY["Finish"]), ("Fail", TASK_LIST_KEY["Fail"]), ("Start", TASK_LIST_KEY["Start"])):
		for task in (quest.get("conditions") or {}).get(list_key, []) or []:
			if isinstance(task, dict) and task.get("id"):
				found.append((task["id"], timing, task))
	return found


def keys_for_quest(quest, optional=False):
	"""The keys a quest should have text for: its text fields, and its tasks that need text.

	optional=True adds the optional fields and the Fail tasks. Returns [(key, what)] where what is
	the field name for a quest key or 'task' for a task id.
	"""
	quest_id = quest.get("_id", "")
	keys = [(quest_key(quest_id, f.key), f.key) for f in QUEST_TEXT if f.used or optional]
	for task_id, timing, _task in quest_tasks(quest):
		need = task_text_needed(timing)
		if need == "needed" or (optional and need == "optional"):
			keys.append((task_id, "task"))
	return keys


def quest_entries(quest, texts=None, optional=False):
	"""A quest's locale entries as {key: text}; keys without text given in texts are blank."""
	texts = texts or {}
	return {key: texts.get(key, "") for key, _what in keys_for_quest(quest, optional)}


def missing_keys(quests, locale, optional=False):
	"""The keys the quests need that the locale lacks or leaves blank, as {key: what}."""
	missing = {}
	for quest in quests.values():
		for key, what in keys_for_quest(quest, optional):
			if not locale.get(key):
				missing[key] = what
	return missing


def key_owners(quests):
	"""{key: name of the quest it belongs to} for every key the quests use or could use."""
	owners = {}
	for quest in quests.values():
		if not isinstance(quest, dict):
			continue
		name = quest.get("QuestName", "")
		for key in QUEST_TEXT_KEYS:
			owners[quest_key(quest.get("_id", ""), key)] = name
		for task_id, _timing, _task in quest_tasks(quest):
			owners[task_id] = name
	return owners


def unused_keys(quests, locale):
	"""Quest and task keys in the locale that none of the quests uses."""
	used = set()
	for quest in quests.values():
		quest_id = quest.get("_id", "")
		used |= {quest_key(quest_id, key) for key in QUEST_TEXT_KEYS}
		used |= {task_id for task_id, _t, _task in quest_tasks(quest)}
	quest_ids = {q.get("_id") for q in quests.values()}
	return [
		key for key in locale
		if (split_quest_key(key) and split_quest_key(key)[0] in quest_ids and key not in used)
	]


def merge_locale(base, entries):
	"""The existing locale plus an entry for every key it lacks; existing entries are never changed."""
	merged = dict(base)
	for key, text in entries.items():
		merged.setdefault(key, text)
	return merged


def fix_misspelled(locale):
	"""A copy of the locale with the old wrong key spellings corrected (an existing correct key wins)."""
	fixed = {}
	for key, text in locale.items():
		parts = split_quest_key(key)
		if parts and parts[1] in MISSPELLED:
			new_key = quest_key(parts[0], MISSPELLED[parts[1]])
			if new_key in locale:
				continue
			key = new_key
		fixed[key] = text
	return fixed
