"""Looking things up in an items.json (the game's item database)."""

# The top of the item tree: climbing parents stops here.
ROOT_ITEM_ID = "54009119af1c881c07000029"


def find_descendants(items, parent_id):
	"""The ids of every item that sits somewhere under parent_id in the item tree.

	items is the items.json dict ({item id: {"_parent": parent id, ...}}). An item counts
	if climbing its chain of "_parent" links reaches parent_id before the top of the tree.
	Results are in the file's order. A chain that leaves the file or loops back on itself
	just ends instead of failing.
	"""
	found = []
	for item_id in items:
		current_id = item_id
		seen = set()
		while current_id in items and current_id not in seen:
			seen.add(current_id)
			current_parent = items[current_id].get("_parent")
			if current_parent == parent_id:
				found.append(item_id)
				break
			if current_id == ROOT_ITEM_ID:
				break
			current_id = current_parent
	return found


def format_id_list(ids):
	"""The ids as the text the old console tool printed: a bracketed list, one quoted id per line."""
	return "\n".join(["["] + [f'"{item_id}",' for item_id in ids] + ["]"])
