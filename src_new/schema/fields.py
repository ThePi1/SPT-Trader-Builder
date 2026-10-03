"""Describing the data: a Field is one key of a quest, task, reward, ...; a Spec is one kind
of thing (a Kills subtask, an Experience reward) made of fields.

Forms, the validator, the Schema Explorer and the defaults for new items are all made from these.
"""

import copy
from dataclasses import dataclass, field
from typing import Callable

# Field kinds
TEXT = "text"  # one line of text
MULTILINE = "multiline"  # several lines of text
INT = "int"  # a whole number
NUMBER = "number"  # a number with decimals
BOOL = "bool"  # yes / no
CHOICE = "choice"  # one value from a list (a list name from choices.py, or (value, label) pairs)
REF = "ref"  # an id of something: an item, trader, quest, location, ... (see Field.ref)
LIST = "list"  # a list of text values; with choices, picked from them
IDLIST = "idlist"  # a list of ids (see Field.ref)
GROUPS = "groups"  # a list of lists of values (mods that must all be present together, ...)
OBJECT = "object"  # a small object with its own fields (see Field.fields)
REWARD_ITEMS = "reward_items"  # the list of parts of an Item / AssortmentUnlock reward
VISIBILITY = "visibility"  # "only show after these tasks": a list of {conditionType, id, target}
JSON = "json"  # anything else: edited as JSON text

# What an id field refers to (Field.ref)
ITEM, TRADER, QUEST, LOCATION, TASK, ACHIEVEMENT, CUSTOMIZATION, SKILL = (
	"item", "trader", "quest", "location", "task", "achievement", "customization", "skill",
)


@dataclass(frozen=True)
class Field:
	key: str  # the key in the JSON; "distance.value" reaches into an object
	label: str  # short, plain English, what the user sees
	kind: str = TEXT
	default: object = None  # the value for a new item (None: the spec's base decides)
	choices: object = ()  # a list name in choices.py, or a tuple of values / (value, label) pairs
	open: bool = False  # a choice field that also accepts values not in its list
	ref: str = ""  # for REF / IDLIST: what the id refers to
	advanced: bool = False  # rare: shown under "More"
	required: bool = False  # the server needs this key
	minimum: float = None
	maximum: float = None
	fields: tuple = ()  # for OBJECT: the fields inside


@dataclass(frozen=True)
class Spec:
	group: str  # quest, task, subtask, reward, reward_item
	kind: str  # the conditionType / reward type / "quest"
	label: str  # short, plain English
	fields: tuple  # the Fields with a control
	base: dict  # a new item: every key with its default, in the order they are written
	timings: tuple = ()  # where it may sit: for tasks Start / Finish / Fail, for rewards Success / Started / Fail
	managed: tuple = ()  # keys the app fills in itself (ids, the type): never shown as fields
	summary: Callable = None  # (item, names) -> text for the outline
	everyday: bool = True  # False: rare kind, shown with a generic form or as JSON
	note: str = ""  # one plain sentence about the kind, for the Schema Explorer
	fresh_ids: tuple = ()  # more keys that get a new id when a new item is made ("counter.id")

	def field(self, key):
		for f in self.fields:
			if f.key == key:
				return f
		return None

	def known_keys(self):
		return set(self.base) | {f.key.split(".")[0] for f in self.fields} | set(self.managed)


def make(spec, new_id=None):
	"""A new item of this kind: a copy of the base, with a new id where the kind has one."""
	item = copy.deepcopy(spec.base)
	if new_id is not None:
		for key in (("id",) if "id" in item else ()) + tuple(spec.fresh_ids):
			set_path(item, key, new_id())
	return item


# --- reading and writing keys by path ("distance.value") -----------------------------

def get_path(data, key, default=None):
	for part in key.split("."):
		if not isinstance(data, dict) or part not in data:
			return default
		data = data[part]
	return data


def set_path(data, key, value):
	parts = key.split(".")
	for part in parts[:-1]:
		data = data.setdefault(part, {})
	data[parts[-1]] = value
