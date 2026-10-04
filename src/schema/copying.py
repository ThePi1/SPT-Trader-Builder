"""Copying things with new ids, so the copy doesn't clash with the original."""

import copy

from core.ids import new_id
from schema.locale import quest_key
from schema.quest import TEXT_POINTER_KEYS


def with_new_ids(node, ids=new_id, id_map=None):
	"""A deep copy of a task, subtask or reward where every 'id' (and the '_id' of item parts) is new.

	Things that point at an id inside the copy (a part's parentId, a reward's target, a task's
	visibility conditions) are pointed at the new one. Returns the copy; id_map ({old: new}) is filled in.
	"""
	id_map = {} if id_map is None else id_map
	clone = copy.deepcopy(node)
	_collect(clone, ids, id_map)
	_remap(clone, id_map)
	return clone


def _collect(node, ids, id_map):
	if isinstance(node, dict):
		for key, value in node.items():
			if key in ("id", "_id") and isinstance(value, str) and value:
				id_map.setdefault(value, ids())
			elif isinstance(value, (dict, list)):
				_collect(value, ids, id_map)
	elif isinstance(node, list):
		for value in node:
			_collect(value, ids, id_map)


def _remap(node, id_map):
	if isinstance(node, dict):
		for key, value in node.items():
			if isinstance(value, str) and value in id_map and key in ("id", "_id", "parentId", "target"):
				node[key] = id_map[value]
			elif isinstance(value, (dict, list)):
				_remap(value, id_map)
	elif isinstance(node, list):
		for value in node:
			_remap(value, id_map)


def copy_quest(quest, ids=new_id):
	"""A copy of a quest with a new id, new ids on every task, subtask and reward, and its text keys pointed at the new id.

	Returns (new quest, {old id: new id} for the quest and everything inside it).
	"""
	id_map = {}
	clone = with_new_ids(quest, ids, id_map)
	old_id = quest.get("_id", "")
	new = id_map.get(old_id) or ids()
	clone["_id"] = new
	for key in TEXT_POINTER_KEYS:
		if key in clone:
			clone[key] = quest_key(new, key)
	id_map[old_id] = new
	return clone, id_map
