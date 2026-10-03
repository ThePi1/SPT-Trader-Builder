"""The user's saved composite items (a weapon with its mods, ...), kept inside the app in data/my_items.json.

Each entry is ``{"name": ..., "items": [parts]}`` stored under its own id. The vanilla composite items
(globals.json ItemPresets) are read separately from the game data and are never stored here.
"""

from pathlib import Path

from core import jsonio
from core.ids import new_id
from core.paths import LIBRARY_FILE
from schema import assort as assort_schema
from schema.copying import with_new_ids


class Library:
	def __init__(self, path=None):
		self.path = Path(path) if path else LIBRARY_FILE
		self.entries = {}
		if self.path.is_file():
			try:
				data = jsonio.read_json(self.path)
			except (OSError, ValueError):
				data = {}
			if isinstance(data, dict):
				self.entries = {k: v for k, v in data.items() if isinstance(v, dict) and isinstance(v.get("items"), list)}

	def save(self):
		jsonio.write_json(self.path, self.entries)

	def add(self, name, parts):
		"""Save a copy of these parts as a new entry; returns its id."""
		entry_id = new_id()
		self.entries[entry_id] = assort_schema.new_composite(name, with_new_ids(parts))
		self.save()
		return entry_id

	def update(self, entry_id, name=None, parts=None):
		entry = self.entries[entry_id]
		if name is not None:
			entry["name"] = name
		if parts is not None:
			entry["items"] = parts
		self.save()

	def remove(self, entry_id):
		self.entries.pop(entry_id, None)
		self.save()

	def names(self):
		"""[(id, name)] sorted by name."""
		return sorted(((i, e.get("name", "")) for i, e in self.entries.items()), key=lambda x: x[1].lower())

	def parts_of(self, entry_id):
		"""A copy of an entry's parts with new ids, ready to put in a reward or an assort offer."""
		return with_new_ids(self.entries[entry_id]["items"])


def preset_parts(preset):
	"""A copy, with new ids, of the parts of a vanilla composite item (globals.json ItemPresets entry)."""
	parts = [{k: v for k, v in p.items() if k in ("_id", "_tpl", "parentId", "slotId", "upd")} for p in preset.get("_items", [])]
	return with_new_ids(parts)
