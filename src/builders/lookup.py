"""The ID Lookup tab: which rows exist, and which of them match a search."""

import re

# The three columns of the table, in order: the id, the data (a name), and where it came from.
COLUMNS = ("id", "data", "type")


def lookup_rows(custom_ids, quests, items, locations, traders):
	"""Every row the ID Lookup table can show, as (id, data, type) tuples.

	custom_ids   {name: id} from an imported WTT folder        -> type "wtt_custom"
	quests       {id: quest} made or imported in this session  -> "new_quest"
	items        {id: {"_name": ...}} the item database (items.json) -> "eft_item"
	locations    {name: id}                                    -> "location"
	traders      {name: id}                                    -> "trader"
	"""
	rows = [(item_id, name, "wtt_custom") for name, item_id in custom_ids.items()]
	rows += [(quest_id, quest["QuestName"], "new_quest") for quest_id, quest in quests.items()]
	rows += [(item_id, item.get("_name", ""), "eft_item") for item_id, item in items.items()]
	rows += [(location_id, name, "location") for name, location_id in locations.items()]
	rows += [(trader_id, name, "trader") for name, trader_id in traders.items()]
	return rows


def compile_search(text):
	"""A case-insensitive regex for the search box. Text that isn't a valid regex (like a half-typed
	"(") is searched for as plain text instead of matching everything."""
	try:
		return re.compile(text, re.IGNORECASE)
	except re.error:
		return re.compile(re.escape(text), re.IGNORECASE)


def filter_rows(rows, text):
	"""The rows where the search text matches any column: the id, the data, or the type."""
	pattern = compile_search(text)
	return [row for row in rows if any(pattern.search(str(field)) for field in row)]
