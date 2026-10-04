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
TRADERS_DIR = "traders"


def locale_file(language):
	return f"locales/global/{language}.json"


class GameData:
	def __init__(self, database_dir=None, language="en", fallback_dir=BUNDLED_DATABASE_DIR):
		self.database_dir = Path(database_dir) if database_dir else None
		self.language = language or "en"
		self.fallback_dir = Path(fallback_dir) if fallback_dir else None

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
		"""{trader id: name}. From each traders/<id>/base.json, named from the locale; the
		app's own list fills in traders the folder doesn't have."""
		names = {}
		for folder in (self.database_dir, self.fallback_dir):
			if folder is None or not (folder / TRADERS_DIR).is_dir():
				continue
			for base_file in sorted((folder / TRADERS_DIR).glob("*/base.json")):
				trader_id = base_file.parent.name
				if trader_id in names:
					continue
				try:
					base = read_json(base_file)
				except (OSError, ValueError) as e:
					log.warning(f"Could not read {base_file}: {e}")
					continue
				names[trader_id] = self.locale.get(f"{trader_id} Nickname") or base.get("nickname") or trader_id
		for name, trader_id in read_json(DATA_DIR / "traders.json").items():
			names.setdefault(trader_id, name)
		return names

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
		return item.get("_name", "") if item else ""

	def quest_name(self, quest_id):
		name = self.locale.get(f"{quest_id} name")
		if name:
			return name
		quest = self.vanilla_quests.get(quest_id)
		return quest.get("QuestName", "") if quest else ""

	def trader_name(self, trader_id):
		return self.traders.get(trader_id, "")
