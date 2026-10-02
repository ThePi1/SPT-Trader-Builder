"""Data shared by all the windows.

``AppState`` is created once at startup and handed to every window, so a window
never has to reach through its parent window to get at traders, items, the quests
built so far, or the half-finished table rows of the dialog being edited.
It deliberately knows nothing about Qt.
"""

import logging

from config import DEFAULT_ITEMS_FILE, resolve_items_path
from paths import DATA_DIR
from utils import read_json

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


def load_json(path):
	"""Load a JSON file (UTF-8, or the Russian code page as a fallback; see utils.read_json)."""
	return read_json(path)


def load_items_file(path):
	"""Load an items.json (the game's item database): {item id: {"_name": ..., "_parent": ...}}.

	Raises OSError if it can't be read, and ValueError (bad JSON, or not an items file).
	"""
	items = read_json(path)
	if not isinstance(items, dict) or not all(isinstance(item, dict) for item in items.values()):
		raise ValueError("this doesn't look like an items.json (expected a dictionary of items)")
	return items


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


def _reason(error):
	"""A short, readable reason for a failed load ("No such file or directory", not Python's repr)."""
	return error.strerror if isinstance(error, OSError) and error.strerror else str(error)


def load_configured_items(config):
	"""Load the item database the settings point at.

	Returns (items, path, error). If the chosen file can't be used, the included one is loaded
	instead and error says what went wrong; if that fails too there are no items ({} and a None
	path) and error says why.
	"""
	chosen = config.items_path()
	try:
		return load_items_file(chosen), str(chosen), None
	except (OSError, ValueError) as e:
		error = f"{chosen}: {_reason(e)}"
	included = resolve_items_path(DEFAULT_ITEMS_FILE)
	if chosen == included:
		return {}, None, error
	try:
		return load_items_file(included), str(included), error
	except (OSError, ValueError) as e:
		return {}, None, f"{error} (the included {included} could not be loaded either: {_reason(e)})"


class AppState:
	def __init__(
		self, config, traders, weapons, locations, status, items, datafiles=None, items_path=None, items_error=None
	):
		self.config = config

		# Game data
		self.traders = traders
		self.weapons = weapons
		self.locations = locations
		self.status = status

		# The item database (one items.json, used by the ID Lookup tab and the child-item finder).
		# items_path is where it came from (None if none is loaded); items_error says why the file
		# chosen in Settings couldn't be used, if that happened.
		self.items = {}
		self.items_path = None
		self.items_error = None
		self.set_items(items, items_path, items_error)

		# Custom data imported from a WTT folder
		self.datafiles = datafiles or {}
		self.customdata = {}
		self.id_search = {}

		# Quests built so far, by quest id
		self.quests = {}

	def set_items(self, items, path=None, error=None):
		"""Use this as the item database ({} and no path for none)."""
		self.items = items
		self.items_path = path
		self.items_error = error

	@property
	def loaded_items(self):
		"""The item database, or None if none is loaded."""
		return self.items if self.items_path is not None else None

	@classmethod
	def load(cls, config):
		"""Load the game data files from data/ and the item database the settings point at."""
		items, items_path, items_error = load_configured_items(config)
		if items_error:
			log.warning(f"Could not use the items.json set in Settings: {items_error}")
		if items_path is not None:
			log.info(f"Imported {len(items)} items from {items_path}.")
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
			items_path=items_path,
			items_error=items_error,
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
