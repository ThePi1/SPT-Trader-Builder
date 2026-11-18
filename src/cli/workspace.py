"""The files the command line works on, named in a project file, and everything it needs to look things up.

A project file is JSON. Paths are relative to the project file's folder:

    {
        "quests": "db/quests.json",              the quests file (made if it isn't there)
        "locale": "db/locales/en.json",          the quests' text in one language (made if it isn't there)
        "assort": "db/assort.json",              the trader's assort (optional)
        "questassort": "db/questassort.json",    the trader's quest locks (optional)
        "trader": "Prapor or a trader id",       the trader the assort is for (optional)
        "zones": "db/CustomQuestZones/new.json", the custom zone file new zones go into (optional)
        "zone_files": ["db/CustomQuestZones"],   more custom zone files or folders, for checking (optional)
        "game": "I:/Games/SPT",                  the game's folder, for importing maps (optional)
        "spt": "I:/Games/SPT/SPT_Runtime",       the SPT server's folder, for `check --server` (optional; default:
                                                 the game folder's SPT_Runtime)
        "database": "I:/Games/SPT/.../database", the SPT_Data/database to look names up in (optional; default: the
                                                 game folder's, else the app's setting, else the bundled copy)
        "language": "en",                        the language of names (optional; default: the app's setting)
        "references": ["db/CustomItems"]         files and folders whose ids are looked up too: other traders' quests,
                                                 custom items, trader files (optional; default: the app's list)
    }

`project init` writes these for a WTT-CommonLib mod. Without the last three, the app's own settings
(data/settings.ini) and reference list (data/references.json) are used as the app uses them; the defaults for new
quests (icon, side) always come from the app's settings. `sources()` says which were used. No Qt.
"""

from pathlib import Path

from core import jsonio
from core.documents import Document
from core.gamedata import GameData
from core.library import Library
from core.paths import BUNDLED_DATABASE_DIR
from core.references import References
from core.settings import Settings
from maps.zones import ZoneIndex
from schema import assort as assort_schema

KEYS = ("quests", "locale", "assort", "questassort", "trader", "zones", "zone_files", "game", "spt", "database", "language", "references")
# Where an SPT install keeps its database, under the game folder (SPT 4.1, then 4.0)
DATABASE_IN_GAME = ("SPT_Runtime/SPT_Data/database", "SPT_Data/database", "SPT/SPT_Data/database")
BUNDLED = "the copy bundled with the program (SPT 4.1.6)"


class ProjectError(Exception):
	"""The project file or a file it names can't be used."""


class Workspace:
	def __init__(self, project=None, settings=None, maps_dir=None):
		self.project_path = Path(project).resolve() if project else None
		self.config = {}
		if self.project_path is not None:
			try:
				self.config = jsonio.read_json(self.project_path)
			except (OSError, ValueError) as e:
				raise ProjectError(f"Can't read the project file {self.project_path}: {e}") from e
			if not isinstance(self.config, dict):
				raise ProjectError("A project file must be a JSON object.")
			unknown = sorted(set(self.config) - set(KEYS))
			if unknown:
				raise ProjectError(f"Unknown keys in the project file: {', '.join(unknown)} (it can have {', '.join(KEYS)}).")
		self.settings = settings if settings is not None else Settings.load()
		self.language = self.config.get("language") or self.settings.language
		self.database, self.database_from = self._database()
		self.gamedata = GameData(self.database, self.language, BUNDLED_DATABASE_DIR if BUNDLED_DATABASE_DIR.is_dir() else None)
		listed = self.config.get("references")
		if listed is not None:
			if not isinstance(listed, list) or not all(isinstance(p, str) for p in listed):
				raise ProjectError("\"references\" in the project file must be a list of files and folders.")
			self.references = References.of([self._full(p) for p in listed], self.language)
		else:
			self.references = References(language=self.language)
		self.gamedata.references = self.references
		self.library = Library()
		self.maps_dir = maps_dir
		self.quests = self._open("quests", {})
		self.locale = self._open("locale", {})
		self.assort = self._open("assort", assort_schema.empty_assort()) if self.config.get("assort") else None
		self.questassort = self._open("questassort", assort_schema.empty_questassort()) if self.config.get("questassort") else None
		self._zones = None

	# --- the files -------------------------------------------------------------------------------------
	def path(self, key):
		"""The full path of a file the project names, or None."""
		value = self.config.get(key)
		if not value or not isinstance(value, str):
			return None
		return self._full(value)

	def _full(self, value):
		path = Path(value)
		return path if path.is_absolute() or self.project_path is None else self.project_path.parent / path

	def _database(self):
		"""(the SPT_Data/database folder names are looked up in or None for the bundled copy, where that came from)."""
		given = self.path("database")
		if given is not None:
			if not given.is_dir():
				raise ProjectError(f"\"database\" in the project file isn't a folder: {given}")
			return given, "the project file"
		game = self.path("game")
		for sub in DATABASE_IN_GAME if game is not None else ():
			if (game / sub).is_dir():
				return game / sub, "the game folder"
		app = self.settings.resolve("database_folder")
		if app is not None:
			return app, "the app's settings (data/settings.ini)"
		return None, BUNDLED

	def sources(self):
		"""Where the workspace's game data, names and maps come from, for `project show` and the checks."""
		refs = self.references
		return {
			"database": str(self.database) if self.database else "bundled", "database_from": self.database_from,
			"language": self.language, "language_from": "the project file" if self.config.get("language") else "the app's settings (data/settings.ini)",
			"references": [str(ref.path) for ref in refs.files],
			"references_from": "the project file" if refs.path is None else f"the app's reference list ({refs.path})",
		}

	def _open(self, key, empty):
		path = self.path(key)
		if path is None:
			return Document(empty)
		if not path.is_file():
			return Document(empty, path)
		try:
			return Document.open(path)
		except (OSError, ValueError) as e:
			raise ProjectError(f"Can't read {path}: {e}") from e

	def documents(self):
		return [(key, doc) for key, doc in (("quests", self.quests), ("locale", self.locale), ("assort", self.assort), ("questassort", self.questassort)) if doc is not None]

	def save(self):
		"""Write the files that changed; returns their paths. A file the project doesn't name can't be written."""
		written = []
		for key, doc in self.documents():
			if not doc.dirty:
				continue
			if doc.path is None:
				raise ProjectError(f"The project names no {key} file, so the changes to it can't be saved.")
			doc.path.parent.mkdir(parents=True, exist_ok=True)
			doc.save()
			written.append(str(doc.path))
		return written

	@property
	def trader_id(self):
		"""The project's trader as an id ('' when there is none). A name is looked up among the known traders."""
		value = self.config.get("trader") or ""
		if not value:
			return ""
		traders = self.gamedata.all_traders()
		if value in traders:
			return value
		for trader_id, name in traders.items():
			if name.lower() == str(value).lower():
				return trader_id
		return value

	# --- zones -----------------------------------------------------------------------------------------
	def zone_file_paths(self):
		"""The custom zone files the project names (its new-zones file and the files in its zone_files)."""
		found = []
		new = self.path("zones")
		if new is not None and new.is_file():
			found.append(new)
		for value in self.config.get("zone_files") or []:
			path = Path(value)
			path = path if path.is_absolute() or self.project_path is None else self.project_path.parent / path
			if path.is_dir():
				found += sorted(path.glob("*.json"))
			elif path.is_file():
				found.append(path)
		return list(dict.fromkeys(p.resolve() for p in found))

	def zone_index(self):
		"""Every zone known: the imported maps', the project's zone files' and the reference zone files'."""
		if self._zones is None:
			index = ZoneIndex(self.maps_dir) if self.maps_dir else ZoneIndex()
			for path in self.zone_file_paths():
				index.add_file(path)
			named = {p.name for p in self.zone_file_paths()}
			for records, name in self.references.zone_files():
				if name not in named:
					index.add_records(records, name)
			self._zones = index
		return self._zones

	def forget_zones(self):
		self._zones = None
