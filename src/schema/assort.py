"""A trader's assort (what it sells) and its quest locks, and composite items.

assort.json is ``{items, barter_scheme, loyal_level_items}``. An *offer* is a root entry of
``items`` (parentId and slotId both "hideout") plus its parts (mods), and the offer's root id
keys its price (``barter_scheme``) and trader level (``loyal_level_items``).
questassort.json is ``{started, success, fail}``, each ``{offer id: quest id}``: the offer is
unlocked when the quest is started / completed, or locked when it fails.
"""

from core import parts as P
from core.ids import new_id
from schema import server
from schema.copying import with_new_ids
from schema.issues import ERROR, WARNING, Issue

ROOT = "hideout"
QUEST_LOCKS = ("started", "success", "fail")
LEVELS = (1, 2, 3, 4)
MONEY = {"roubles": "5449016a4bdc2d6f028b456f", "dollars": "5696686a4bdc2d3b5c8b4568", "euros": "569668774bdc2da2298b4568"}


def is_root(part):
	return part.get("parentId") == ROOT and part.get("slotId") == ROOT


def offer_ids(assort):
	return [p["_id"] for p in assort.get("items", []) if is_root(p)]


def offer_parts(assort, offer_id):
	"""The offer's root entry and all parts hanging off it, root first."""
	items = assort.get("items", [])
	found = {offer_id}
	parts = [p for p in items if p.get("_id") == offer_id]
	grew = True
	while grew:
		grew = False
		for p in items:
			if p.get("parentId") in found and p["_id"] not in found:
				found.add(p["_id"])
				parts.append(p)
				grew = True
	return parts


def new_offer(tpl, price=1, currency=MONEY["roubles"], level=1, stack=9999999, restriction=None, ids=new_id):
	"""(items, barter list, level) for a new offer of one item sold for money."""
	upd = {"UnlimitedCount": True, "StackObjectsCount": stack}
	if restriction:
		upd.update(BuyRestrictionMax=restriction, BuyRestrictionCurrent=0)
	root = {"_id": ids(), "_tpl": tpl, "parentId": ROOT, "slotId": ROOT, "upd": upd}
	return [root], [[{"count": price, "_tpl": currency}]], level


def new_offer_from_parts(parts, price=1, currency=MONEY["roubles"], level=1, stack=9999999, ids=new_id):
	"""(items, barter list, level) for a new offer of a composite item sold for money. The offer is the first main
	part with everything attached to it; the parts are copied with new ids."""
	copy = with_new_ids(parts, ids)
	main = P.roots(copy)[0]
	main.update(parentId=ROOT, slotId=ROOT, upd={**(main.get("upd") or {}), "UnlimitedCount": True, "StackObjectsCount": stack})
	items = offer_parts({"items": copy}, main["_id"])
	return items, [[{"count": price, "_tpl": currency}]], level


def add_offer(assort, items, barter, level):
	assort["items"].extend(items)
	assort["barter_scheme"][items[0]["_id"]] = barter
	assort["loyal_level_items"][items[0]["_id"]] = level
	return items[0]["_id"]


def remove_offer(assort, offer_id):
	gone = {p["_id"] for p in offer_parts(assort, offer_id)}
	assort["items"] = [p for p in assort["items"] if p["_id"] not in gone]
	assort["barter_scheme"].pop(offer_id, None)
	assort["loyal_level_items"].pop(offer_id, None)


def empty_assort():
	return {"items": [], "barter_scheme": {}, "loyal_level_items": {}}


def empty_questassort():
	return {"started": {}, "success": {}, "fail": {}}


def _parts_issues(parts, path, issues, rooted):
	ids = set()
	for i, part in enumerate(parts):
		pid = part.get("_id") if isinstance(part, dict) else None
		if pid in ids:
			issues.append(Issue(ERROR, path + (i, "_id"), "This id is used by another item."))
		ids.add(pid)
	for i, part in enumerate(parts):
		if not isinstance(part, dict):
			continue
		parent = part.get("parentId")
		if parent and parent != ROOT and parent not in ids:
			issues.append(Issue(WARNING, path + (i, "parentId"), "This part is attached to an item that isn't in the list."))
		if rooted and not parent:
			issues.append(Issue(WARNING, path + (i, "parentId"), "This item isn't attached to anything."))


def validate_assort(assort):
	issues = []
	for e in server.check_record(assort, "TraderAssort"):
		issues.append(e if isinstance(e, Issue) else Issue(ERROR, (), str(e)))
	if not isinstance(assort, dict) or issues:
		return issues
	items = assort.get("items", [])
	_parts_issues(items, ("items",), issues, rooted=True)
	roots = {p["_id"] for p in items if isinstance(p, dict) and is_root(p)}
	barter = assort.get("barter_scheme", {})
	levels = assort.get("loyal_level_items", {})
	for rid in sorted(roots):
		if rid not in barter:
			issues.append(Issue(WARNING, ("barter_scheme", rid), "This item has no price, so the trader can't sell it."))
		elif not barter[rid] or not all(barter[rid]):
			issues.append(Issue(WARNING, ("barter_scheme", rid), "This item's price is empty."))
		if rid not in levels:
			issues.append(Issue(WARNING, ("loyal_level_items", rid), "This item has no trader level."))
	for rid in barter:
		if rid not in roots:
			issues.append(Issue(WARNING, ("barter_scheme", rid), "A price for an item the trader doesn't sell."))
	for rid, level in levels.items():
		if level not in LEVELS:
			issues.append(Issue(WARNING, ("loyal_level_items", rid), "Trader level should be 1 to 4."))
	return issues


def validate_questassort(data, assort=None, quest_ids=None, knows_quest=None):
	"""Problems in a quest assort file. quest_ids: the quests that are open; knows_quest(id): True for a quest the game
	or a reference file has. A quest is only reported when neither knows it (and at least one of them was given)."""
	issues = []
	if not isinstance(data, dict):
		return [Issue(ERROR, (), "This should be an object with started, success and fail.")]
	for e in server.check(data, "Dictionary<string, Dictionary<MongoId, MongoId>>"):
		issues.append(e if isinstance(e, Issue) else Issue(ERROR, (), str(e)))
	if issues:
		return issues
	for key in data:
		if key not in QUEST_LOCKS:
			issues.append(Issue(WARNING, (key,), "Unknown section; SPT only uses started, success and fail."))
	roots = set(offer_ids(assort)) if assort is not None else None
	for lock in QUEST_LOCKS:
		for offer, quest in (data.get(lock) or {}).items():
			if roots is not None and offer not in roots:
				issues.append(Issue(WARNING, (lock, offer), "This offer isn't in the assort."))
			if (quest_ids is not None or knows_quest is not None) and not (
				(quest_ids is not None and quest in quest_ids) or (knows_quest is not None and knows_quest(quest))
			):
				issues.append(Issue(WARNING, (lock, offer), "This quest isn't known (it isn't in the open quests, the base game or the reference files)."))
	return issues


# --- quest locks and the quests' unlock rewards ----------------------------------------------
# An offer locked behind a quest is listed in questassort.json, and the quest gives an AssortmentUnlock
# reward for the same item at the same trader. The two are matched by the item (the root part's _tpl),
# not by id: the reward's parts have ids of their own (checked on all 236 vanilla quest locks).

LOCK_TIMING = {"started": "Started", "success": "Success", "fail": "Fail"}  # the lock section -> the reward list
UNLOCKED_BY = ("started", "success")  # the lock sections that a quest reward goes with (a "fail" lock has none)


def offer_tpl(assort, offer_id):
	"""The item an offer sells."""
	root = next((p for p in assort.get("items", []) if p.get("_id") == offer_id), None)
	return (root or {}).get("_tpl", "")


def reward_root(reward):
	"""The main part of an AssortmentUnlock reward (the part its target points at, else the first)."""
	parts = reward.get("items") or []
	target = reward.get("target")
	return next((p for p in parts if p.get("_id") == target), parts[0] if parts else None)


def unlocks(quests, trader_id=None):
	"""[(quest id, lock section, reward, item)] for every AssortmentUnlock reward in the quests
	(only those at this trader if trader_id is given)."""
	found = []
	for quest_id, quest in quests.items():
		if not isinstance(quest, dict):
			continue
		for status, timing in LOCK_TIMING.items():
			for reward in (quest.get("rewards") or {}).get(timing) or []:
				if isinstance(reward, dict) and reward.get("type") == "AssortmentUnlock" and (not trader_id or reward.get("traderId") == trader_id):
					root = reward_root(reward)
					if root:
						found.append((quest_id, status, reward, root.get("_tpl", "")))
	return found


def find_unlock(quest, status, tpl, trader_id=None):
	"""The reward of this quest that unlocks the item when the lock section applies, or None."""
	for _qid, found_status, reward, found_tpl in unlocks({"q": quest}, trader_id):
		if found_status == status and found_tpl == tpl:
			return reward
	return None


def lock_problems(quests, locks, assort, trader_id=None):
	"""Warnings for what doesn't add up between the quest locks, the offers and the quests' unlock rewards.

	A lock whose quest has no reward unlocking that item gets a warning at (section, offer id). With a
	trader_id, a reward at that trader that no offer's lock matches gets a warning at ("unlock", quest id,
	reward id). Locks for offers or quests that aren't there are left to validate_questassort.
	"""
	issues = []
	offers = set(offer_ids(assort))
	for status in UNLOCKED_BY:
		for offer, quest_id in (locks.get(status) or {}).items():
			quest = quests.get(quest_id)
			if offer not in offers or not isinstance(quest, dict):
				continue
			if find_unlock(quest, status, offer_tpl(assort, offer), trader_id) is None:
				issues.append(Issue(WARNING, (status, offer), f"The quest \"{quest.get('QuestName', quest_id)}\" has no reward that unlocks this item."))
	if trader_id:
		by_tpl = {}
		for offer in offers:
			by_tpl.setdefault(offer_tpl(assort, offer), []).append(offer)
		for quest_id, status, reward, tpl in unlocks(quests, trader_id):
			if status not in UNLOCKED_BY:
				continue
			if not any((locks.get(status) or {}).get(offer) == quest_id for offer in by_tpl.get(tpl, [])):
				name = quests[quest_id].get("QuestName", quest_id)
				issues.append(Issue(WARNING, ("unlock", quest_id, reward.get("id", "")), f"The quest \"{name}\" unlocks an item here, but no offer for it is locked to the quest."))
	return issues


def unlock_reward(assort, offer_id, trader_id, level=None, ids=new_id):
	"""A new AssortmentUnlock reward for an offer: the same item and mods (with ids of their own), at this
	trader and level. Put it in the quest's Success / Started list to match a quest lock."""
	import copy

	from schema import registry

	parts = offer_parts(assort, offer_id)
	id_map = {p["_id"]: ids() for p in parts}
	items = []
	for part in parts:
		item = {"_id": id_map[part["_id"]], "_tpl": part["_tpl"]}
		if part["_id"] != offer_id:  # (the main part is just the id and the item, as in the base game)
			item["parentId"] = id_map.get(part.get("parentId"), part.get("parentId"))
			item["slotId"] = part.get("slotId", "")
			for key in ("location", "upd"):
				if part.get(key):
					item[key] = copy.deepcopy(part[key])
		items.append(item)
	reward = registry.new_item("reward", "AssortmentUnlock")
	if level is None:
		level = assort.get("loyal_level_items", {}).get(offer_id, 1)
	reward.update(traderId=trader_id, loyaltyLevel=level, items=items, target=items[0]["_id"])
	return reward


# --- does a reward's preview match an offer? ---------------------------------------------------
# A reward's item is only the preview the client shows. The offer lives in the trader assort; the two are compared by
# shape (items, slots and mods, never ids). In the base game 212 of 236 unlock previews are exactly their offer and the
# rest are the bare main item.

def structure(parts, root_id):
	"""The shape of a multi-part item, ignoring ids: (item, slot, its mods in order of shape...), the main part first."""
	kids = {}
	for part in parts:
		kids.setdefault(part.get("parentId"), []).append(part)

	def shape(part, top):
		return (part.get("_tpl", ""), "" if top else part.get("slotId", ""), tuple(sorted(shape(c, False) for c in kids.get(part.get("_id"), []))))

	root = next((p for p in parts if p.get("_id") == root_id), None)
	return shape(root, True) if root else None


def offer_structure(assort, offer_id):
	return structure(offer_parts(assort, offer_id), offer_id)


def reward_structure(reward):
	root = reward_root(reward)
	return structure(reward.get("items") or [], root["_id"]) if root else None


def offers_matching(assort, reward):
	"""(exact, same_item): the offers whose parts are the reward's parts, and the others that sell the same main item."""
	shape, root = reward_structure(reward), reward_root(reward)
	if shape is None:
		return [], []
	exact, same_item = [], []
	for offer in offer_ids(assort):
		if offer_structure(assort, offer) == shape:
			exact.append(offer)
		elif offer_tpl(assort, offer) == root.get("_tpl"):
			same_item.append(offer)
	return exact, same_item


def parts_word(count):
	return f"{count} part{'' if count == 1 else 's'}"


def preview_differences(assort, offer_id, reward, trader_id=None):
	"""How the reward's preview differs from the offer, as short phrases ([] when it is the same)."""
	root = reward_root(reward)
	if root is None:
		return ["the preview has no item"]
	found = []
	if root.get("_tpl") != offer_tpl(assort, offer_id):
		found.append("a different main item")
	elif reward_structure(reward) != offer_structure(assort, offer_id):
		found.append(f"{parts_word(len(reward.get('items') or []))} in the preview, {parts_word(len(offer_parts(assort, offer_id)))} in the offer")
	level = assort.get("loyal_level_items", {}).get(offer_id)
	if level is not None and reward.get("loyaltyLevel") != level:
		found.append(f"level {reward.get('loyaltyLevel')} in the quest, {level} in the offer")
	if trader_id and reward.get("traderId") != trader_id:
		found.append("another trader")
	return found


def refresh_unlock(reward, assort, offer_id, trader_id=None, ids=new_id):
	"""Make the reward's preview the offer's: its parts (with ids of their own), main part and level, and the trader when
	it is known. The reward's other keys stay as they are."""
	fresh = unlock_reward(assort, offer_id, trader_id or reward.get("traderId", ""), ids=ids)
	reward.update(items=fresh["items"], target=fresh["target"], loyaltyLevel=fresh["loyaltyLevel"])
	if trader_id:
		reward["traderId"] = trader_id
	return reward


def unlock_state(assort, locks, quest_id, timing, reward, trader_id=None):
	"""What the open trader assort says about a reward's preview: (tone, message, offer id or None, differs).
	tone is "ok", "note" or "warn"; offer id is the offer the preview belongs to (the one locked to the quest, else the
	only offer that matches); differs says whether the preview is not the same as that offer."""
	offers = offer_ids(assort)
	if not offers:
		return "note", "No trader assort is open, so the preview can't be compared with an offer.", None, False
	status = next((s for s, when in LOCK_TIMING.items() if when == timing and s in UNLOCKED_BY), None)
	locked = [o for o in offers if status and (locks.get(status) or {}).get(o) == quest_id]
	exact, same_item = offers_matching(assort, reward)
	owner = next((o for o in locked if o in exact), None) or next((o for o in locked if o in exact + same_item), None)
	if owner is None and len(exact) == 1:
		owner = exact[0]
	if owner is None and not exact and len(same_item) == 1:
		owner = same_item[0]
	if owner is not None and owner in locked:
		found = preview_differences(assort, owner, reward, trader_id)
		if not found:
			return "ok", "The preview is the same as the offer locked to this quest.", owner, False
		return "note", "The offer locked to this quest differs from the preview: " + "; ".join(found) + ".", owner, True
	if exact:
		where = "None of them is locked to this quest." if len(exact) > 1 else "It is not locked to this quest."
		return "note", f"The trader assort has {len(exact)} offer{'' if len(exact) == 1 else 's'} for these parts. {where}", owner, False
	if same_item:
		return (
			"note",
			f"The trader assort sells this item, but with different parts ({parts_word(len(offer_parts(assort, same_item[0])))} in the offer, "
			f"{parts_word(len(reward.get('items') or []))} in the preview). A preview showing only the main item is how some base game quests do it.",
			owner, bool(owner),
		)
	return "warn", "The trader assort has no offer for this item, so the player would be unlocking nothing.", None, False


# --- composite items: a saved multi-part item (a weapon with mods) ---------------------------

def new_composite(name, parts):
	return {"name": name, "items": parts}


def validate_composite(composite):
	issues = []
	parts = composite.get("items") if isinstance(composite, dict) else None
	if not isinstance(parts, list) or not parts:
		return [Issue(ERROR, ("items",), "A composite item needs at least one part.")]
	_parts_issues(parts, ("items",), issues, rooted=False)
	roots = [p for p in parts if isinstance(p, dict) and (not p.get("parentId") or p.get("parentId") == ROOT)]
	if len(roots) != 1:
		issues.append(Issue(WARNING, ("items",), "A composite item should have exactly one main part."))
	for i, p in enumerate(parts):
		for e in server.check_record(p, "Item", ("items", i)):
			issues.append(e if isinstance(e, Issue) else Issue(ERROR, ("items", i), str(e)))
	return issues
