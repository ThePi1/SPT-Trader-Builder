"""Data shared by all the windows.

``AppState`` is created once at startup and handed to every window, so a window
never has to reach through its parent window to get at traders, items, the quests
built so far, or the half-finished table rows of the dialog being edited.
It deliberately knows nothing about Qt.
"""

import json
import logging

from paths import DATA_DIR

log = logging.getLogger(__name__)

# Custom (WTT) data file categories, matched against the file path
CUSTOM_DATA_TYPES = (
	"CustomItems",
	"CustomLocales",
	"CustomQuestZones",
	"CustomQuests",
	"CustomLootspawns",
	"RootWTTFolder",
)


def load_json(path, encoding="utf-8"):
	with open(path, "r", encoding=encoding) as f:
		return json.load(f)


class TableFields:
	"""The rows of the tables in ONE dialog, keyed by table type ("KillsWep", "RewardItem", ...), then row id.

	Each dialog creates its own, so what a dialog collects can never leak into another
	dialog (or another quest), and goes away when the dialog does.
	"""

	def __init__(self):
		self.data = {}

	def get_singlecolumn_field_list(self, key):
		"""The row ids for one table type."""
		return list(self.data.get(key, {}).keys())

	def get_multicolumn_values_list(self, key):
		"""The stored objects for one table type."""
		return list(self.data.get(key, {}).values())


class AppState:
	def __init__(self, config, traders, weapons, locations, status, items, datafiles=None):
		self.config = config

		# Game data
		self.traders = traders
		self.weapons = weapons
		self.locations = locations
		self.status = status
		self.items = items
		self.item_id_name = {_data["_name"]: _id for _id, _data in items.items()}

		# Custom data imported from a WTT folder
		self.datafiles = datafiles or {}
		self.customdata = {}
		self.id_search = {}

		# Quests built so far, by quest id
		self.quests = {}

	@classmethod
	def load(cls, config):
		"""Load the game data files from data/."""
		items = load_json(DATA_DIR / "items.json")
		log.info(f"Imported {len(items)} items.")
		try:
			datafiles = load_json(DATA_DIR / "datafiles.json")
		except Exception:
			datafiles = {}
		state = cls(
			config,
			traders=load_json(DATA_DIR / "traders.json"),
			weapons=load_json(DATA_DIR / "weapons.json"),
			locations=load_json(DATA_DIR / "locations.json"),
			status=load_json(DATA_DIR / "status.json"),
			items=items,
			datafiles=datafiles,
		)
		# import custom data from WTT file list
		allfiles = [item for sublist in state.datafiles.values() for item in sublist]
		state.import_customdata(allfiles, root_folder=None)
		return state

	# --- custom (WTT) data --------------------------------------------------

	def import_customdata(self, pathlist, root_folder=None):
		"""Load WTT JSON files, index them into id_search, and remember them as customdata.

		Returns (datafiles, datafiles_to_disk): the loaded JSON per category, and the
		file paths per category (what gets saved to data/datafiles.json).
		"""
		datafiles_to_disk = {}
		datafiles = {}
		for path in pathlist:
			for datatype in CUSTOM_DATA_TYPES:
				if datatype in str(path):
					try:
						loaded_json = load_json(str(path))
					except Exception:
						log.error(f"Cannot load {str(path)}, skipping")
						continue
					if datatype not in datafiles:
						datafiles[datatype] = []
					if datatype not in datafiles_to_disk:
						datafiles_to_disk[datatype] = []
					# insert path in disk dict
					datafiles_to_disk[datatype].append(str(path))
					# category-specific logic
					if "CustomItems" in str(path):
						for _id, _data in loaded_json.items():
							self.id_search[_data["locales"]["en"]["name"]] = _id
							self.id_search[_data["locales"]["en"]["shortName"]] = _id
							self.id_search[_data["locales"]["en"]["description"]] = _id
					elif "CustomQuests" in str(path):
						if "en.json" in str(path):
							for _id, _data in loaded_json.items():
								self.id_search[_data] = _id
						elif "quest_definitions.json" in str(path):
							for _id, _data in loaded_json.items():
								quest = loaded_json[_id]
								self.id_search[quest["QuestName"]] = _id

					datafiles[datatype].append(loaded_json)
		if root_folder:
			datafiles["RootWTTFolder"] = [str(root_folder)]
		self.customdata = datafiles
		return datafiles, datafiles_to_disk
