"""Finding ids and names: every item, item category, quest, trader, map, achievement and customization the
game has (plus the quests being edited), searchable by name or id. No Qt."""

from dataclasses import dataclass

ITEM, QUEST, TRADER, MAP, ACHIEVEMENT, CUSTOMIZATION, MINE, PRESET, CATEGORY = (
	"item", "quest", "trader", "map", "achievement", "customization", "my_composite", "composite", "category",
)
# the same things found in the reference files
REF_ITEM, REF_QUEST, REF_TRADER, REF_OFFER = "ref_item", "ref_quest", "ref_trader", "ref_offer"
KIND_LABEL = {
	ITEM: "Item", CATEGORY: "Item category", QUEST: "Quest", TRADER: "Trader", MAP: "Map", ACHIEVEMENT: "Achievement",
	CUSTOMIZATION: "Clothing", MINE: "Your composite item", PRESET: "Vanilla composite item",
	REF_ITEM: "Item (reference)", REF_QUEST: "Quest (reference)", REF_TRADER: "Trader (reference)", REF_OFFER: "Trader offer (reference)",
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


def _category_rows(gamedata):
	"""The game's item categories (the 'Node' entries of the item templates: Handgun, Assault rifle, ...), which some conditions take
	as well as items. The detail is the category they are in."""
	locale, items = gamedata.locale, gamedata.items
	rows = []
	for tpl, node in items.items():
		if node.get("_type") != "Node":
			continue
		parent = items.get(node.get("_parent"), {})
		rows.append(Row(tpl, locale.get(f"{tpl} Name") or node.get("_name", ""), CATEGORY, locale.get(f"{node.get('_parent')} Name") or parent.get("_name", "")))
	return rows


def category_items(items, category_id):
	"""The ids of all the items under an item category, at any depth (Handgun: every pistol), in the order of the item templates.
	items is the game's templates/items.json."""
	below, found = {category_id}, []
	grew = True
	while grew:  # (the categories under it, and the ones under those)
		grew = False
		for tpl, node in items.items():
			if node.get("_type") == "Node" and node.get("_parent") in below and tpl not in below:
				below.add(tpl)
				grew = True
	for tpl, item in items.items():
		if item.get("_type") == "Item" and item.get("_parent") in below:
			found.append(tpl)
	return found


def library_rows(library):
	"""The user's saved composite items (core.library.Library), as rows."""
	if library is None:
		return []
	return [Row(i, name, MINE, _parts(library.entries[i].get("items"))) for i, name in library.names()]


def _parts(items):
	count = len(items) if isinstance(items, list) else 0
	return f"{count} part{'' if count == 1 else 's'}"


def build_rows(gamedata, quests=None, kinds=None, library=None, references=None):
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
	if CATEGORY in want:
		rows += _category_rows(gamedata)
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
	if references is not None:  # (what the reference files know that the game and the open quests do not)
		if REF_QUEST in want:
			known = set(quests or {}) | set(gamedata.vanilla_quests)
			rows += [Row(i, n, REF_QUEST, source) for i, n, source in references.quest_rows() if i not in known]
		if REF_ITEM in want:
			rows += [Row(i, n, REF_ITEM, source) for i, n, source in references.item_rows() if i not in gamedata.items]
		if REF_TRADER in want:
			rows += [Row(i, n, REF_TRADER, source) for i, n, source in references.trader_rows() if i not in gamedata.traders]
		if REF_OFFER in want:
			rows += [Row(i, n, REF_OFFER, source) for i, n, source in references.offer_rows()]
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
