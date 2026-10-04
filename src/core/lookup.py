"""Finding ids and names: every item, quest, trader, map, achievement and customization the
game has (plus the quests being edited), searchable by name or id. No Qt."""

from dataclasses import dataclass

ITEM, QUEST, TRADER, MAP, ACHIEVEMENT, CUSTOMIZATION, MINE, PRESET = (
	"item", "quest", "trader", "map", "achievement", "customization", "my_composite", "composite",
)
KIND_LABEL = {
	ITEM: "Item", QUEST: "Quest", TRADER: "Trader", MAP: "Map", ACHIEVEMENT: "Achievement",
	CUSTOMIZATION: "Clothing", MINE: "Your composite item", PRESET: "Vanilla composite item",
}


@dataclass(frozen=True)
class Row:
	id: str
	name: str
	kind: str
	detail: str = ""  # a short extra: an item's short name and type, a quest's trader

	def haystack(self):
		return f"{self.name} {self.detail} {self.id}".lower()


def _item_rows(gamedata):
	locale, items = gamedata.locale, gamedata.items
	rows = []
	for tpl, item in items.items():
		if item.get("_type") != "Item":
			continue
		name = locale.get(f"{tpl} Name") or item.get("_name", "")
		short = locale.get(f"{tpl} ShortName") or ""
		parent = items.get(item.get("_parent"), {}).get("_name", "")
		rows.append(Row(tpl, name, ITEM, ", ".join(x for x in (short if short != name else "", parent) if x)))
	return rows


def library_rows(library):
	"""The user's saved composite items (core.library.Library), as rows."""
	if library is None:
		return []
	return [Row(i, name, MINE, _parts(library.entries[i].get("items"))) for i, name in library.names()]


def _parts(items):
	count = len(items) if isinstance(items, list) else 0
	return f"{count} part{'' if count == 1 else 's'}"


def build_rows(gamedata, quests=None, kinds=None, library=None):
	"""Every Row for the kinds asked for (all if None). quests is {id: quest} being edited; they come first,
	then the saved composite items of the library, if given."""
	want = set(kinds) if kinds else set(KIND_LABEL)
	rows = []
	seen = set()
	if QUEST in want:
		for quest_id, quest in (quests or {}).items():
			if isinstance(quest, dict):
				rows.append(Row(quest_id, quest.get("QuestName", ""), QUEST, "your quest"))
				seen.add(quest_id)
		for quest_id, quest in gamedata.vanilla_quests.items():
			if quest_id not in seen:
				rows.append(Row(quest_id, gamedata.quest_name(quest_id), QUEST, gamedata.trader_name(quest.get("traderId", ""))))
	if ITEM in want:
		rows += _item_rows(gamedata)
	if TRADER in want:
		rows += [Row(i, n, TRADER) for i, n in gamedata.traders.items()]
	if MAP in want:
		rows += [Row(i, n, MAP) for i, n in gamedata.locations.items() if i != "any"]
	if ACHIEVEMENT in want:
		rows += [Row(a["id"], gamedata.locale.get(f"{a['id']} name", ""), ACHIEVEMENT) for a in gamedata.achievements if isinstance(a, dict) and "id" in a]
	if CUSTOMIZATION in want:
		rows += [
			Row(i, gamedata.locale.get(f"{i} Name") or c.get("_name", ""), CUSTOMIZATION, c.get("_props", {}).get("BodyPart", ""))
			for i, c in gamedata.customization.items() if isinstance(c, dict) and c.get("_type") == "Item"
		]
	if MINE in want:
		rows += library_rows(library)
	if PRESET in want:
		rows += [Row(i, p.get("_name", ""), PRESET, _parts(p.get("_items"))) for i, p in gamedata.item_presets.items() if isinstance(p, dict)]
	return rows


def search(rows, text, kinds=None, limit=None):
	"""Rows matching every word of the text (case-insensitive, in the name, details or id), best first:
	names that start with the text, then the rest in their order."""
	words = text.lower().split()
	text_l = text.strip().lower()
	found = [r for r in rows if (not kinds or r.kind in kinds) and all(w in r.haystack() for w in words)]
	if text_l:
		found.sort(key=lambda r: (not r.name.lower().startswith(text_l), not r.id.lower().startswith(text_l)))
	return found[:limit] if limit else found
