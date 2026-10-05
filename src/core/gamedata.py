"""The game's own data (items, names, presets, traders, ...) read from an SPT database folder.

``GameData`` reads from the SPT_Data/database folder chosen in Settings; any file that folder
lacks (or every file, when none is chosen) comes from the copy bundled with the app
(data/database, same layout). Files are read the first time they are needed.
"""

import logging
from functools import cached_property
from pathlib import Path

from core.jsonio import read_json
from core.paths import BUNDLED_DATABASE_DIR, DATA_DIR

log = logging.getLogger(__name__)

# Where each file sits inside a database folder
ITEMS = "templates/items.json"
QUESTS = "templates/quests.json"
HANDBOOK = "templates/handbook.json"
ACHIEVEMENTS = "templates/achievements.json"
CUSTOMIZATION = "templates/customization.json"
EQUIPMENT_PRESETS = "templates/defaultEquipmentPresets.json"
GLOBALS = "globals.json"
HIDEOUT_AREAS = "hideout/areas.json"
LANGUAGES = "locales/languages.json"


def locale_file(language):
	return f"locales/global/{language}.json"


class GameData:
	def __init__(self, database_dir=None, language="en", fallback_dir=BUNDLED_DATABASE_DIR):
		self.database_dir = Path(database_dir) if database_dir else None
		self.language = language or "en"
		self.fallback_dir = Path(fallback_dir) if fallback_dir else None
		self.references = None  # the reference files (core.references.References): what they know is added to the names and checks

	def path(self, relative):
		"""The file to read for a path inside the database folder, or None if neither folder has it."""
		for folder in (self.database_dir, self.fallback_dir):
			if folder is not None and (folder / relative).is_file():
				return folder / relative
		return None

	def read(self, relative, default=None):
		path = self.path(relative)
		if path is None:
			log.warning(f"Game data file not found: {relative}")
			return default
		return read_json(path)

	def source(self, relative):
		"""'yours', 'included' or 'missing': where a file is read from (for the Settings dialog)."""
		path = self.path(relative)
		if path is None:
			return "missing"
		return "yours" if self.database_dir is not None and path.is_relative_to(self.database_dir) else "included"

	# --- the files ---------------------------------------------------------------------

	@cached_property
	def items(self):
		"""{tpl: item template} (templates/items.json)."""
		return self.read(ITEMS, {})

	@cached_property
	def vanilla_quests(self):
		"""{quest id: quest} of the base game (templates/quests.json)."""
		return self.read(QUESTS, {})

	@cached_property
	def handbook(self):
		return self.read(HANDBOOK, {"Categories": [], "Items": []})

	@cached_property
	def achievements(self):
		return self.read(ACHIEVEMENTS, [])

	@cached_property
	def customization(self):
		return self.read(CUSTOMIZATION, {})

	@cached_property
	def equipment_presets(self):
		"""Vanilla equipment loadouts: [{Id, Name, Items, ...}]."""
		return self.read(EQUIPMENT_PRESETS, [])

	@cached_property
	def item_presets(self):
		"""Vanilla composite items: {preset id: {_id, _name, _parent, _items, _encyclopedia, ...}}."""
		return (self.read(GLOBALS, {}) or {}).get("ItemPresets", {})

	@cached_property
	def hideout_areas(self):
		return self.read(HIDEOUT_AREAS, [])

	@cached_property
	def languages(self):
		"""{code: name} of the languages the game has text for."""
		return self.read(LANGUAGES, {"en": "English"})

	@cached_property
	def locale(self):
		"""The text in the chosen language ({key: text}); English where that language is missing."""
		text = self.read(locale_file(self.language))
		if text is None and self.language != "en":
			text = self.read(locale_file("en"))
		return text or {}

	def read_locale(self, language):
		return self.read(locale_file(language), {})

	@cached_property
	def traders(self):
		"""{trader id: name}, from the app's own list (data/traders.json). The name is the trader's nickname in
		the chosen language where the locale has it. A trader that is not in that list can still be used by id."""
		return {
			trader_id: self.locale.get(f"{trader_id} Nickname") or name
			for name, trader_id in read_json(DATA_DIR / "traders.json").items()
		}

	@cached_property
	def locations(self):
		"""{location id (as quests use it): name}. 'any' means any location."""
		names = {"any": "Any"}
		for name, location_id in read_json(DATA_DIR / "locations.json").items():
			names.setdefault(location_id, self.locale.get(f"{location_id} Name") or name)
		return names

	# --- names -------------------------------------------------------------------------

	def item_name(self, tpl):
		"""An item's name in the chosen language, else its internal name, else ''."""
		name = self.locale.get(f"{tpl} Name")
		if name:
			return name
		item = self.items.get(tpl)
		if item and item.get("_name"):
			return item["_name"]
		return self.references.item_name(tpl) if self.references is not None else ""

	def quest_name(self, quest_id):
		name = self.locale.get(f"{quest_id} name")
		if name:
			return name
		quest = self.vanilla_quests.get(quest_id)
		if quest and quest.get("QuestName"):
			return quest["QuestName"]
		return self.references.quest_name(quest_id) if self.references is not None else ""

	def trader_name(self, trader_id):
		return self.traders.get(trader_id) or (self.references.trader_name(trader_id) if self.references is not None else "")

	# --- what is known (the game's data, and the reference files) ----------------------------
	def all_traders(self):
		"""{trader id: name}: the app's list, then the traders in the reference files."""
		if self.references is None:
			return self.traders
		merged = dict(self.traders)
		for trader_id, name, _source in self.references.trader_rows():
			merged.setdefault(trader_id, name)
		return merged

	def knows_trader(self, trader_id):
		return trader_id in self.traders or (self.references is not None and self.references.knows_trader(trader_id))

	def knows_item(self, tpl):
		return tpl in self.items or (self.references is not None and self.references.knows_item(tpl))

	def knows_quest(self, quest_id):
		return quest_id in self.vanilla_quests or (self.references is not None and self.references.knows_quest(quest_id))
