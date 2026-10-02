"""Quest rewards, and the item entries used by Item / AssortmentUnlock rewards."""

import copy


def reward_item(
	item_id,
	tpl,
	*,
	stack_count=None,
	spawned_in_session=False,
	parent_id=None,
	slot_id=None,
):
	"""One item inside an Item / AssortmentUnlock reward. Optional fields are left out when None/False."""
	item = {"_id": item_id, "_tpl": tpl}
	if stack_count is not None or spawned_in_session:
		item["upd"] = {}
	if stack_count is not None:
		item["upd"]["StackObjectsCount"] = stack_count
	if spawned_in_session:
		item["upd"]["SpawnedInSession"] = True
	if parent_id is not None:
		item["parentId"] = parent_id
	if slot_id is not None:
		item["slotId"] = slot_id
	return item


def first_item_id(items):
	"""The reward target defaults to the id of the first item in the list (or "" if none)."""
	if items is None or len(items) <= 0:
		return ""
	if len(items[0]) >= 1:
		try:
			return items[0]["_id"]
		except Exception:
			return ""
	return ""  # Should never happen, but if there is no ID (empty item list might happen)


def achievement(reward_id, *, target, unknown):
	return {
		"availableInGameEditions": [],
		"id": reward_id,
		"index": 0,
		"target": target,
		"type": "Achievement",
		"unknown": unknown,
	}


def assortment_unlock(reward_id, *, items, loyalty_level, target, trader_id, unknown):
	return {
		"availableInGameEditions": [],
		"id": reward_id,
		"index": 0,
		"items": items,
		"loyaltyLevel": loyalty_level,
		"target": target,
		"traderId": trader_id,
		"type": "AssortmentUnlock",
		"unknown": unknown,
	}


def experience(reward_id, *, unknown, value):
	return {
		"availableInGameEditions": [],
		"id": reward_id,
		"index": 0,
		"type": "Experience",
		"unknown": unknown,
		"value": value,
	}


def item(reward_id, *, find_in_raid, items, target, unknown, value):
	return {
		"availableInGameEditions": [],
		"findInRaid": find_in_raid,
		"id": reward_id,
		"index": 0,
		"items": items,
		"target": target,
		"type": "Item",
		"unknown": unknown,
		"value": value,
	}


def skill(reward_id, *, target, unknown, value):
	return {
		"availableInGameEditions": [],
		"id": reward_id,
		"index": 0,
		"target": target,
		"type": "Skill",
		"unknown": unknown,
		"value": value,
	}


def stash_rows(reward_id, *, unknown, value):
	return {
		"availableInGameEditions": [],
		"id": reward_id,
		"index": 0,
		"type": "StashRows",
		"unknown": unknown,
		"value": value,
	}


def trader_standing(reward_id, *, target, unknown, value):
	return {
		"availableInGameEditions": [],
		"id": reward_id,
		"index": 0,
		"target": target,
		"type": "TraderStanding",
		"unknown": unknown,
		"value": value,
	}


def trader_unlock(reward_id, *, target, unknown):
	return {
		"availableInGameEditions": [],
		"id": reward_id,
		"index": 0,
		"target": target,
		"type": "TraderUnlock",
		"unknown": unknown,
	}


# The keys of each kind of reward that the Reward Builder has a control for (see windows/reward.py)
EDITABLE_KEYS = {
	"Achievement": ("target", "unknown"),
	"AssortmentUnlock": ("items", "loyaltyLevel", "target", "traderId", "unknown"),
	"Experience": ("unknown", "value"),
	"Item": ("findInRaid", "items", "target", "unknown", "value"),
	"Skill": ("target", "unknown", "value"),
	"StashRows": ("unknown", "value"),
	"TraderStanding": ("target", "unknown", "value"),
	"TraderUnlock": ("target", "unknown"),
}


def _same_number(original, new):
	"""Whether original is a number written as text ("5000") that is the number new."""
	if not isinstance(original, str) or isinstance(new, bool) or not isinstance(new, (int, float)):
		return False
	try:
		return float(original) == new
	except ValueError:
		return False


def edited_reward(original, built):
	"""A reward that was edited in the Reward Builder: the original, with the edited fields replaced.

	built is what the builder made from the form. Only the keys the form has a control for are taken
	from it; the rest (id, index, availableInGameEditions, anything unknown) stays as the original
	had it. Two details keep an untouched reward exactly as it was: a number that the original wrote
	as text ("5000") stays text if the form still has that number, and a key the original doesn't
	have is not added just to say "false" or 0.
	"""
	merged = copy.deepcopy(original)
	for key in EDITABLE_KEYS[original["type"]]:
		new = built[key]
		if _same_number(original.get(key), new):
			continue
		if key not in original and not new:
			continue
		merged[key] = new
	return merged
