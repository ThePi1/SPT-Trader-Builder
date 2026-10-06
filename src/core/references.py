"""Reference files: files with ids worth knowing about (another mod's quests, its custom items, its trader)
that are only looked at. They are never edited, merged, saved or exported; they just let the program
recognise and name what the open files point at. The list of files is kept in data/references.json and
the files are read the first time something is looked up. No Qt.
"""

from dataclasses import dataclass
from pathlib import Path

from core import jsonio
from core.paths import REFERENCES_FILE
from schema import assort as assort_schema
from schema import explorer

QUESTS, LOCALE, ASSORT, ITEMS, TRADER = "quests", "locale", "assort", "items", "trader"
KIND_LABEL = {QUESTS: "Quests", LOCALE: "Locale", ASSORT: "Trader assort", ITEMS: "Item templates", TRADER: "Trader"}
NO_IDS = "questassort"  # (a quest assort file has no ids of its own, so there is nothing to look up in it)
LIMIT = 200  # the most files read from the folders that are added at once


def detect_kind(data):
	"""What a loaded file is, for a reference: quests, locale, assort, items (item templates), trader (a trader's
	base.json), "questassort" (nothing to look up) or None."""
	if not isinstance(data, dict):
		return None
	if isinstance(data.get("_id"), str) and ("nickname" in data or "name" in data) and ("loyaltyLevels" in data or "currency" in data):
		return TRADER
	values = list(data.values())[:20]
	if values and all(isinstance(v, dict) and "_id" in v and "_parent" in v for v in values):
		return ITEMS
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
	def count(self):
		"""How many ids it knows about."""
		data = self.data
		if self.kind == ASSORT:
			return len(assort_schema.offer_ids(data))
		if self.kind == TRADER:
			return 1
		return len(data) if isinstance(data, dict) else 0


def _read(ref):
	ref.read, ref.kind, ref.data, ref.error = True, None, None, ""
	try:
		data = jsonio.read_json(ref.path)
	except (OSError, ValueError) as e:
		ref.error = f"Couldn't be read: {e}"
		return ref
	kind = detect_kind(data)
	if kind is None:
		ref.error = "Not a quest, locale, trader assort, item template or trader file."
	elif kind == NO_IDS:
		ref.error = "A quest assort file has no ids of its own, so there is nothing to look up in it."
	else:
		ref.kind, ref.data = kind, data
	return ref


class References:
	"""The reference files. path is the file the list of them is kept in; language picks which locale file names are read from."""

	def __init__(self, path=None, language="en"):
		self.path = Path(path) if path else REFERENCES_FILE
		self.language = language or "en"
		self.files = []
		self._index = None
		self._load_list()

	# --- the list --------------------------------------------------------------------------
	def _load_list(self):
		try:
			listed = jsonio.read_json(self.path) if self.path.is_file() else {}
		except (OSError, ValueError):
			listed = {}
		paths = listed.get("files") if isinstance(listed, dict) else None
		self.files = [Reference(Path(p)) for p in paths or [] if isinstance(p, str) and p]

	def save(self):
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

	# --- what the files know ---------------------------------------------------------------
	@property
	def index(self):
		if self._index is None:
			self.read_all()
			self._index = self._build()
		return self._index

	def _build(self):
		ranked = sorted(
			(ref for ref in self.files if ref.kind == LOCALE),
			key=lambda ref: 0 if ref.path.stem == self.language else 1 if ref.path.stem == "en" else 2,
		)
		locale = {}
		for ref in ranked:
			for key, text in ref.data.items():
				if isinstance(text, str) and key not in locale:
					locale[key] = text
		quests, templates, assort_tpls, offers, traders = {}, {}, {}, [], {}
		for ref in self.files:
			if ref.kind == QUESTS:
				for quest_id, quest in ref.data.items():
					if isinstance(quest, dict) and quest_id not in quests:
						quests[quest_id] = (quest.get("QuestName") or "", ref.name)
			elif ref.kind == ITEMS:
				for tpl, item in ref.data.items():
					if isinstance(item, dict) and tpl not in templates:
						templates[tpl] = (item.get("_name") or "", ref.name)
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

	def locale_entries(self):
		"""{key: (text, the file it is in)} of every locale file in the list (the file in the chosen language first, then English, then the rest;
		the first file with a key wins)."""
		self.read_all()
		found = {}
		for ref in sorted(
			(ref for ref in self.files if ref.kind == LOCALE),
			key=lambda ref: 0 if ref.path.stem == self.language else 1 if ref.path.stem == "en" else 2,
		):
			for key, text in ref.data.items():
				if isinstance(text, str) and key not in found:
					found[key] = (text, ref.name)
		return found

	def quest_data(self):
		"""{quest id: (the quest, the file it is in)} of every quest in the reference files (the first file wins)."""
		self.read_all()
		found = {}
		for ref in self.files:
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
