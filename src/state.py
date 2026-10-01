"""Data shared by all the windows.

``AppState`` is created once at startup and handed to every window, so a window
never has to reach through its parent window to get at traders, items, the quests
built so far, or the half-finished table rows of the dialog being edited.
It deliberately knows nothing about Qt.
"""

import copy
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

		# Rows of the tables in the dialog currently being filled in, keyed by table type
		# ("RewardSuccess", "ConditionFinish", "KillsWep", ...), then by row id.
		self.table_fields = {}
		# When clearing table fields, keep any k/v pair with these strings in the key
		self.table_fields_keep_str = ["Reward", "Condition"]

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

	# --- table fields -------------------------------------------------------

	def safe_clear_table_fields(self):
		pre_fields = copy.deepcopy(self.table_fields)
		for k, v in pre_fields.items():
			found_safe = False
			for keepstr in self.table_fields_keep_str:
				if keepstr in k:
					found_safe = True
			if not found_safe:
				log.debug(f"removing {k}:{v}, not a safe field")
				self.table_fields.pop(k)

	def clear_table_fields(self):
		self.table_fields = {}

	def get_singlecolumn_field_list(self, key):
		if key in self.table_fields:
			return list(self.table_fields[key].keys())
		else:
			return []

	def get_multicolumn_values_list(self, key):
		if key in self.table_fields:
			return list(self.table_fields[key].values())
		else:
			return []

	def reset_by_key(self, key):
		if key in self.table_fields:
			del self.table_fields[key]

	def reset_by_id(self, id):
		for category, cat_dict in self.table_fields.items():
			if id in cat_dict:
				del cat_dict[id]
			# if id is found, remove it similar to reset by key above

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
