"""Reference files: files with ids worth knowing about (another mod's quests, its custom items, its trader)
that are only looked at. They are never edited, merged, saved or exported; they just let the program
recognise and name what the open files point at. The list of files is kept in data/references.json and
the files are read the first time something is looked up. No Qt.
"""

from dataclasses import dataclass
from pathlib import Path

from core import jsonio
from core.paths import REFERENCES_FILE
from maps.zones import is_zone_file
from schema import assort as assort_schema
from schema import explorer

QUESTS, LOCALE, ASSORT, ITEMS, TRADER, ZONES = "quests", "locale", "assort", "items", "trader", "zones"
CUSTOM_ITEMS = "custom_items"  # (WTT-CommonLib's CustomItems files: {id: {itemTplToClone, parentId, locales: {en: {name, ...}}, ...}})
KIND_LABEL = {
	QUESTS: "Quests", LOCALE: "Locale", ASSORT: "Trader assort", ITEMS: "Item templates", TRADER: "Trader", ZONES: "Quest zones",
	CUSTOM_ITEMS: "Custom items (WTT)",
}
NO_IDS = "questassort"  # (a quest assort file has no ids of its own, so there is nothing to look up in it)
LIMIT = 200  # the most files read from the folders that are added at once


def detect_kind(data):
	"""What a loaded file is, for a reference: quests, locale, assort, items (item templates), custom_items (a
	WTT-CommonLib CustomItems file), trader (a trader's base.json), zones (a WTT-CommonLib quest zone file),
	"questassort" (nothing to look up) or None."""
	if is_zone_file(data):
		return ZONES
	if not isinstance(data, dict):
		return None
	if isinstance(data.get("_id"), str) and ("nickname" in data or "name" in data) and ("loyaltyLevels" in data or "currency" in data):
		return TRADER
	values = list(data.values())[:20]
	if values and all(isinstance(v, dict) and "_id" in v and "_parent" in v for v in values):
		return ITEMS
	if values and all(isinstance(v, dict) and "itemTplToClone" in v for v in values):
		return CUSTOM_ITEMS
	kind = explorer.detect_kind(data)
	return {"quests": QUESTS, "locale": LOCALE, "assort": ASSORT}.get(kind, kind)


@dataclass
class Reference:
	"""One reference file: where it is, what it holds (None: not read yet, or not recognised) and its data."""

	path: Path
	kind: str = None
	data: object = None
	error: str = ""
	read: bool = False

	@property
	def name(self):
		return self.path.name

	@property
	def where(self):
		"""The full path, worked out once (to compare with the files open for editing)."""
		if getattr(self, "_where", None) is None:
			self._where = self.path.resolve()
		return self._where

	@property
	def count(self):
		"""How many ids it knows about."""
		data = self.data
		if self.kind == ASSORT:
			return len(assort_schema.offer_ids(data))
		if self.kind == TRADER:
			return 1
		return len(data) if isinstance(data, (dict, list)) else 0


def _read(ref):
	ref.read, ref.kind, ref.data, ref.error = True, None, None, ""
	try:
		data = jsonio.read_json(ref.path)
	except (OSError, ValueError) as e:
		ref.error = f"Couldn't be read: {e}"
		return ref
	kind = detect_kind(data)
	if kind is None:
		ref.error = "Not a quest, locale, trader assort, item template, custom item, trader or quest zone file."
	elif kind == NO_IDS:
		ref.error = "A quest assort file has no ids of its own, so there is nothing to look up in it."
	else:
		ref.kind, ref.data = kind, data
	return ref


class References:
	"""The reference files. path is the file the list of them is kept in; language picks which locale file names are read from.
	References.of(paths) is a list given directly (files, and the .json files in folders), kept in no file (the
	command line's project files name theirs).

	A reference file that is also open for editing is left out of every lookup while it is open (see set_open): the open
	copy is the one being changed, and the reference copy is what was on disk when it was read."""

	def __init__(self, path=None, language="en"):
		self.path = Path(path) if path else REFERENCES_FILE
		self.language = language or "en"
		self.files = []
		self._index = None
		self._open = {}  # who has files open -> (the paths given, the same resolved)
		self._load_list()

	@classmethod
	def of(cls, paths, language="en", limit=LIMIT):
		refs = cls.__new__(cls)
		refs.path, refs.language, refs.files, refs._index, refs._open = None, language or "en", [], None, {}
		found = []
		for path in map(Path, paths):
			found.extend(sorted(path.rglob("*.json"))[:limit] if path.is_dir() else [path])
		refs.files = [Reference(p) for p in dict.fromkeys(found)]
		return refs

	# --- the list --------------------------------------------------------------------------
	def _load_list(self):
		try:
			listed = jsonio.read_json(self.path) if self.path.is_file() else {}
		except (OSError, ValueError):
			listed = {}
		paths = listed.get("files") if isinstance(listed, dict) else None
		self.files = [Reference(Path(p)) for p in paths or [] if isinstance(p, str) and p]

	def save(self):
		if self.path is not None:  # (a list given directly is kept in no file)
			jsonio.write_json(self.path, {"files": [str(ref.path) for ref in self.files]})

	def read_all(self):
		"""Read the files that have not been read yet."""
		for ref in self.files:
			if not ref.read:
				_read(ref)

	def add(self, paths, limit=LIMIT):
		"""Add files (and the .json files inside folders) as references. Returns (added, skipped): the Reference
		objects now in the list, and [(file name, why)] for what was left out (already there, unreadable, not a kind
		of file that has ids). The list is saved."""
		found = []
		for path in map(Path, paths):
			found.extend(sorted(path.rglob("*.json")) if path.is_dir() else [path])
		have = {ref.path.resolve() for ref in self.files}
		added, skipped = [], []
		for path in found[:limit]:
			if path.resolve() in have:
				skipped.append((path.name, "Already added."))
				continue
			ref = _read(Reference(path))
			if ref.kind is None:
				skipped.append((path.name, ref.error))
				continue
			have.add(path.resolve())
			self.files.append(ref)
			added.append(ref)
		if len(found) > limit:
			skipped.append((f"{len(found) - limit} more files", f"Only the first {limit} files of a folder are added."))
		if added:
			self._index = None
			self.save()
		return added, skipped

	def remove(self, refs):
		gone = {id(ref) for ref in refs}
		self.files = [ref for ref in self.files if id(ref) not in gone]
		self._index = None
		self.save()

	def reload(self):
		"""Read every file again (they may have changed on disk)."""
		for ref in self.files:
			_read(ref)
		self._index = None

	def set_language(self, language):
		self.language = language or "en"
		self._index = None

	# --- the files open for editing ----------------------------------------------------------
	def set_open(self, owner, paths):
		"""The files owner (any name: the main window's files, the Zones tab's) has open now; paths that are None (a file
		not saved yet) are skipped. Those files are left out of the lookups until owner names others. True if that changed
		which reference files are used (names, checks and lists then have to look again); opening a file that isn't a
		reference changes nothing."""
		given = tuple(str(p) for p in paths if p)
		if self._open.get(owner, ((),))[0] == given:
			return False
		before = self._skipped()
		self._open[owner] = (given, frozenset(Path(p).resolve() for p in given))
		if self._skipped() == before:
			return False
		self._index = None
		return True

	def _left_out(self):
		return frozenset().union(*(resolved for _given, resolved in self._open.values()))

	def _skipped(self):
		"""The reference files open for editing (by their full paths)."""
		left_out = self._left_out()
		return frozenset(ref.where for ref in self.files if ref.where in left_out) if left_out else frozenset()

	def is_open(self, ref):
		"""True if this reference file is open for editing (and so left out)."""
		return ref.where in self._left_out()

	def _active(self):
		"""The reference files the lookups use: all but the ones open for editing."""
		left_out = self._left_out()
		if not left_out:
			return self.files
		return [ref for ref in self.files if ref.where not in left_out]

	# --- what the files know ---------------------------------------------------------------
	@property
	def index(self):
		if self._index is None:
			self.read_all()
			self._index = self._build()
		return self._index

	def _build(self):
		ranked = sorted(
			(ref for ref in self._active() if ref.kind == LOCALE),
			key=lambda ref: 0 if ref.path.stem == self.language else 1 if ref.path.stem == "en" else 2,
		)
		locale = {}
		for ref in ranked:
			for key, text in ref.data.items():
				if isinstance(text, str) and key not in locale:
					locale[key] = text
		quests, templates, assort_tpls, offers, traders = {}, {}, {}, [], {}
		for ref in self._active():
			if ref.kind == QUESTS:
				for quest_id, quest in ref.data.items():
					if isinstance(quest, dict) and quest_id not in quests:
						quests[quest_id] = (quest.get("QuestName") or "", ref.name)
			elif ref.kind == ITEMS:
				for tpl, item in ref.data.items():
					if isinstance(item, dict) and tpl not in templates:
						templates[tpl] = (item.get("_name") or "", ref.name)
			elif ref.kind == CUSTOM_ITEMS:
				for tpl, item in ref.data.items():
					if isinstance(item, dict) and tpl not in templates:
						templates[tpl] = (self._custom_item_name(item), ref.name)
			elif ref.kind == ASSORT:
				for part in ref.data.get("items", []):
					if not isinstance(part, dict):
						continue
					tpl = part.get("_tpl")
					if isinstance(tpl, str) and tpl and tpl not in assort_tpls:
						assort_tpls[tpl] = ref.name
					if assort_schema.is_root(part) and isinstance(part.get("_id"), str):
						offers.append((part["_id"], tpl or "", ref.name))
			elif ref.kind == TRADER:
				trader_id = ref.data.get("_id")
				if isinstance(trader_id, str) and trader_id not in traders:
					traders[trader_id] = (ref.data.get("nickname") or ref.data.get("name") or "", ref.name)
		return {"locale": locale, "quests": quests, "templates": templates, "assort_tpls": assort_tpls, "offers": offers, "traders": traders}

	def _custom_item_name(self, item):
		"""A WTT custom item's name in the chosen language, else English, else any."""
		locales = item.get("locales") if isinstance(item.get("locales"), dict) else {}
		for text in [locales.get(self.language), locales.get("en"), *locales.values()]:
			if isinstance(text, dict) and isinstance(text.get("name"), str) and text["name"]:
				return text["name"]
		return ""

	def locale_entries(self):
		"""{key: (text, the file it is in)} of every locale file in the list (the file in the chosen language first, then English, then the rest;
		the first file with a key wins)."""
		self.read_all()
		found = {}
		for ref in sorted(
			(ref for ref in self._active() if ref.kind == LOCALE),
			key=lambda ref: 0 if ref.path.stem == self.language else 1 if ref.path.stem == "en" else 2,
		):
			for key, text in ref.data.items():
				if isinstance(text, str) and key not in found:
					found[key] = (text, ref.name)
		return found

	def zone_files(self):
		"""[(entries, file name)] of the quest zone files in the list."""
		self.read_all()
		return [(ref.data, ref.name) for ref in self._active() if ref.kind == ZONES]

	def quest_data(self):
		"""{quest id: (the quest, the file it is in)} of every quest in the reference files (the first file wins)."""
		self.read_all()
		found = {}
		for ref in self._active():
			if ref.kind == QUESTS:
				for quest_id, quest in ref.data.items():
					if isinstance(quest, dict) and quest_id not in found:
						found[quest_id] = (quest, ref.name)
		return found

	# names and "do you know this id"
	def quest_name(self, quest_id):
		index = self.index
		return index["locale"].get(f"{quest_id} name") or index["quests"].get(quest_id, ("",))[0]

	def knows_quest(self, quest_id):
		return quest_id in self.index["quests"]

	def item_name(self, tpl):
		index = self.index
		return index["locale"].get(f"{tpl} Name") or index["templates"].get(tpl, ("",))[0]

	def knows_item(self, tpl):
		index = self.index
		return tpl in index["templates"] or tpl in index["assort_tpls"]

	def trader_name(self, trader_id):
		index = self.index
		return index["locale"].get(f"{trader_id} Nickname") or index["traders"].get(trader_id, ("",))[0]

	def knows_trader(self, trader_id):
		return trader_id in self.index["traders"]

	# everything, for the lists
	def quest_rows(self):
		"""[(id, name, file)]"""
		return [(quest_id, self.quest_name(quest_id), source) for quest_id, (_name, source) in self.index["quests"].items()]

	def item_rows(self):
		index = self.index
		rows = [(tpl, self.item_name(tpl), source) for tpl, (_name, source) in index["templates"].items()]
		rows += [(tpl, self.item_name(tpl), source) for tpl, source in index["assort_tpls"].items() if tpl not in index["templates"]]
		return rows

	def trader_rows(self):
		return [(trader_id, self.trader_name(trader_id), source) for trader_id, (_name, source) in self.index["traders"].items()]

	def offer_rows(self):
		"""[(offer id, the item's name, file)]"""
		return [(offer_id, self.item_name(tpl), source) for offer_id, tpl, source in self.index["offers"]]
