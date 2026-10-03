"""A multi-part item as the game stores it: a flat list of parts, each pointing at its parent
(``parentId``) and the slot it sits in (``slotId``). The helpers here work on that list in place."""

from core.ids import new_id

TOP_PARENTS = (None, "", "hideout")  # a part with one of these as parentId is a main part, not a mod


def ids_of(parts):
	return {p.get("_id") for p in parts}


def roots(parts):
	"""The main parts: no parent, or a parent that isn't in the list."""
	known = ids_of(parts)
	return [p for p in parts if p.get("parentId") in TOP_PARENTS or p.get("parentId") not in known]


def children(parts, parent_id):
	return [p for p in parts if p.get("parentId") == parent_id]


def find(parts, part_id):
	return next((p for p in parts if p.get("_id") == part_id), None)


def add_part(parts, tpl, parent_id=None, slot_id=None, stack=None, ids=new_id):
	"""Append a new part. A main part (no parent) gets a stack size of 1 unless stack says otherwise."""
	part = {"_id": ids(), "_tpl": tpl}
	if parent_id:
		part["parentId"] = parent_id
		part["slotId"] = slot_id or ""
	if stack is not None or not parent_id:
		part["upd"] = {"StackObjectsCount": stack or 1}
	parts.append(part)
	return part


def remove_part(parts, part_id):
	"""Remove a part and everything attached to it (and to those). Returns how many parts were removed."""
	gone, queue = {part_id}, [part_id]
	while queue:
		for child in children(parts, queue.pop()):
			if child["_id"] not in gone:
				gone.add(child["_id"])
				queue.append(child["_id"])
	before = len(parts)
	parts[:] = [p for p in parts if p.get("_id") not in gone]
	return before - len(parts)


# --- what an item's template says it can hold -----------------------------------------------

def slots_of(items, tpl):
	"""[(slot name, {allowed item ids})] of an item template. items is the game's templates/items.json.
	Cartridge slots (magazines) are included under the name 'cartridges'."""
	props = (items.get(tpl) or {}).get("_props", {})
	out = []
	for slot in props.get("Slots", []) or []:
		allowed = {t for f in slot.get("_props", {}).get("filters", []) for t in f.get("Filter", [])}
		out.append((slot.get("_name", ""), allowed))
	for slot in props.get("Cartridges", []) or []:
		allowed = {t for f in slot.get("_props", {}).get("filters", []) for t in f.get("Filter", [])}
		out.append((slot.get("_name", "cartridges"), allowed))
	return out


def slot_names(items, tpl):
	return [name for name, _allowed in slots_of(items, tpl)]


def fits(items, parent_tpl, slot, tpl):
	"""True / False if the parent's template says the item does / doesn't go in that slot; None if unknown."""
	for name, allowed in slots_of(items, parent_tpl):
		if name == slot:
			return tpl in allowed if allowed else None
	return None if not items or parent_tpl not in items else False


def free_slot_for(items, parts, parent, tpl):
	"""The first slot of the parent that takes this item and isn't used yet, or None."""
	used = {p.get("slotId") for p in children(parts, parent["_id"])}
	for name, allowed in slots_of(items, parent["_tpl"]):
		if name not in used and tpl in allowed:
			return name
	return None
