"""Custom item spawns: items a mod puts on a map. WTT-CommonLib reads them from the mod's db/CustomLootspawns folder
(WTT-ServerCommonLib's WTTCustomLootspawnService). Each file is a JSON object {map name: [spawn point, ...]}, each
spawn point shaped like the base game's (locations/<map>/looseLoot.json). This module reads and writes those entries,
makes new ones and checks them. No Qt.

What happens to them (WTT-ServerCommonLib 2.0.15, SPT 4.1.6's LocationLootGenerator; SPT 4.0.13 reads them the same):
- A file in CustomSpawnpointsForced adds its spawns to the map's forced spawns (looseLoot.json "spawnpointsForced",
  where the base game's quest items are): they spawn every raid. One whose locationId the map has already (the game's,
  or one read before it) is skipped.
- A file in CustomSpawnpoints adds them to the map's loose loot ("spawnpoints"). One with IsAlwaysSpawn spawns every
  raid, like a forced one. Any other is one of the points the server draws a raid's loose loot from: probability 1
  always, else weighted by its probability against the map's own points. One whose locationId the map has already is
  merged into that point (its items added, its probability taken).
- Spawns that come every raid and share a template Id are alternatives: the server picks one of them each raid,
  weighted by their probability (LocationLootGenerator.ChooseForcedPositions).
- The map is found by its name with LocationTable.GetMappedKey, which knows only SERVER_MAP_NAMES (bigmap or Bigmap,
  sandbox_high or SandboxHigh, ...): the spawns under any other name are dropped without a word.
- Position and Rotation are read as x, y, z in small letters (4.0's XYZ, 4.1's Vector3; the server's JSON is case
  sensitive): written X, Y, Z they aren't read. Rotation is Unity's Euler angles in degrees.
- The item is made anew each raid (new ids; Root becomes the new root's id). A spawn that comes every raid spawns the
  first entry of Items, with its children; loose loot picks an entry whose composedKey is in itemDistribution, by their
  relativeProbability. Money and ammo get a random stack (the item's StackMinRandom to StackMaxRandom), whatever the
  count written; ammo boxes and magazines are filled by the server.
"""

import math
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from core.ids import new_id
from maps import geometry as G
from maps.mapdata import location_key

FORCED_FOLDER, LOOSE_FOLDER = "CustomSpawnpointsForced", "CustomSpawnpoints"
SPAWN = "spawn"  # the kind a spawn is drawn as in the 3D view
SPAWN_COLOUR = (70, 215, 235)
MARK = 0.3  # metres: the side of the box a spawn is drawn as, centred on its position
LIFT = 0.1  # metres above the spot clicked that a new spawn goes (it falls onto it: gravity is on)
FALLS_FAR = 1.5  # metres: a fall further than this is warned about
HANGS = 0.5  # metres: an item without gravity this far above the floor is warned about
SUNK = 0.15  # metres: ... and this far under it
MONEY, AMMO = "543be5dd4bdc2deb348b4569", "5485a8684bdc2da71d8b4567"  # the item categories that get a random stack

# LocationTable._locationMappings: the map names GetMappedKey knows, and the server's own name for each
SERVER_MAP_NAMES = {
	"factory4_day": "Factory4Day", "bigmap": "Bigmap", "develop": "Develop", "factory4_night": "Factory4Night", "hideout": "Hideout",
	"interchange": "Interchange", "laboratory": "Laboratory", "lighthouse": "Lighthouse", "privatearea": "PrivateArea",
	"rezervbase": "RezervBase", "shoreline": "Shoreline", "suburbs": "Suburbs", "tarkovstreets": "TarkovStreets", "labyrinth": "Labyrinth",
	"terminal": "Terminal", "town": "Town", "woods": "Woods", "sandbox": "Sandbox", "sandbox_high": "SandboxHigh",
}
_JSON_NAME = {own: name for name, own in SERVER_MAP_NAMES.items()}


def server_map(name):
	"""The server's name for the map a spawn file names (Bigmap for bigmap), or None if WTT won't find it."""
	if name in SERVER_MAP_NAMES:
		return SERVER_MAP_NAMES[name]
	return name if name in _JSON_NAME else None


def location_of(name):
	"""The location id (as maps.mapdata.LOCATIONS) of a map named in a spawn file, in any spelling; else the name."""
	return location_key(_JSON_NAME.get(name, name)) or location_key(str(name).replace("High", "_high")) or name


def file_name_of(location):
	"""The name a spawn file gives a map: its location id in small letters, which WTT always finds."""
	return str(location).lower()


def euler_rotation(x, y, z):
	"""Unity's Quaternion.Euler (degrees): turned about z, then x, then y."""
	def about(axis, degrees):
		half = math.radians(degrees) / 2
		q = [0.0, 0.0, 0.0, math.cos(half)]
		q[axis] = math.sin(half)
		return tuple(q)

	return G.q_mul(about(1, y), G.q_mul(about(0, x), about(2, z)))


def _number(value):
	number = float(value)
	if not math.isfinite(number):
		raise ValueError(value)
	return number


def _short(value):
	"""A number with no more digits than it needs (to 4 decimals)."""
	value = round(float(value), 4)
	return int(value) if value == int(value) else value


def location_id(position):
	"""A spawn point's locationId, as the base game makes them: its position, "(x, y, z)"."""
	return "(" + ", ".join(str(_short(v)) for v in position) + ")"


def _vector(part, what):
	"""(x, y, z) of a Position or Rotation, and True if it is written in capitals (which the server doesn't read)."""
	if not isinstance(part, dict):
		raise ValueError(f"{what} is missing")
	if all(axis in part for axis in "xyz"):
		return tuple(_number(part[axis]) for axis in "xyz"), False
	if all(axis in part for axis in "XYZ"):
		return tuple(_number(part[axis]) for axis in "XYZ"), True
	raise ValueError(f"{what} needs x, y and z")


@dataclass
class Spawn:
	map_name: str  # the map's name as the file writes it
	index: int  # its place in that map's list
	location: str  # the location id (as maps.mapdata.LOCATIONS), or the map's name when it is no map
	id: str  # the template's Id
	position: tuple
	rotation: tuple  # Unity's Euler angles, degrees
	item: str  # the item's template id (the root item's _tpl)
	count: int
	forced: bool  # in a file of forced spawns (CustomSpawnpointsForced)
	always: bool  # spawns every raid (forced, or IsAlwaysSpawn)
	probability: float
	gravity: bool
	random_rotation: bool
	location_id: str
	source: str = ""  # the file it is in
	capitals: bool = False  # Position or Rotation written X, Y, Z
	record: dict = field(default=None, repr=False)

	@property
	def yaw(self):
		return self.rotation[1] % 360.0

	@property
	def box(self):
		"""The box the 3D view draws it as: MARK across, centred on its position, turned like it about the up axis."""
		return G.Box(self.position, (MARK, MARK, MARK), G.yaw_rotation(self.yaw))

	def same_entry(self, other):
		"""True if both are the same entry of the same file (one may be a copy moved by a drag)."""
		return other is self or (other.source == self.source and other.map_name == self.map_name and other.index == self.index)

	def chance_text(self):
		if self.always:
			return "every raid"
		return f"by chance ({self.probability:g})"

	def summary(self, item_name=""):
		x, y, z = self.position
		what = f"{item_name or self.item}{f' x{self.count}' if self.count != 1 else ''}"
		return f"{what} ({self.chance_text()}, {self.location}) at {x:.2f}, {y:.2f}, {z:.2f}, from {self.source or 'your file'}: {self.id}"


def _items(template):
	items = template.get("Items")
	if not isinstance(items, list):
		return []
	return [i for i in items if isinstance(i, dict)]


def root_item(record):
	"""The entry of Items the server spawns (for a spawn every raid: the first), or None."""
	items = _items(record.get("template") or {})
	return items[0] if items else None


def spawn_from_record(record, map_name, index, source="", forced=True):
	"""A Spawn from one entry of a spawn file. Raises ValueError (saying what is wrong) for a broken entry."""
	if not isinstance(record, dict):
		raise ValueError("an entry must be an object")
	template = record.get("template")
	if not isinstance(template, dict):
		raise ValueError("template is missing")
	try:
		position, capitals = _vector(template.get("Position"), "Position")
		rotation, turned_capitals = _vector(template.get("Rotation"), "Rotation") if template.get("Rotation") is not None else ((0.0, 0.0, 0.0), False)
		probability = _number(record.get("probability", 1))
	except (TypeError, ValueError) as e:
		raise ValueError(f"a number can't be read ({e})") from None
	root = root_item(record) or {}
	try:
		count = int((root.get("upd") or {}).get("StackObjectsCount", 1))
	except (TypeError, ValueError):
		count = 1
	always = forced or template.get("IsAlwaysSpawn") is True
	return Spawn(
		str(map_name), index, location_of(map_name), str(template.get("Id") or ""), position, rotation, str(root.get("_tpl") or ""),
		count, forced, always, probability, template.get("useGravity") is True, template.get("randomRotation") is True,
		str(record.get("locationId") or ""), source, capitals or turned_capitals, record,
	)


def read_spawns(data, source="", forced=True):
	"""([Spawn], {(map name, index): why it can't be read}) of a spawn file's data."""
	found, broken = [], {}
	if not isinstance(data, dict):
		return found, broken
	for map_name, entries in data.items():
		if not isinstance(entries, list):
			broken[(map_name, 0)] = f"{map_name} must hold a list of spawns"
			continue
		for i, record in enumerate(entries):
			try:
				found.append(spawn_from_record(record, map_name, i, source, forced))
			except ValueError as e:
				broken[(map_name, i)] = str(e)
	return found, broken


def is_spawn_file(data):
	"""True if the data looks like a WTT-CommonLib loot spawn file: {map name: [spawn points]}."""
	if not isinstance(data, dict) or not data or not all(isinstance(v, list) for v in data.values()):
		return False
	entries = [e for v in data.values() for e in v][:20]
	if entries:
		return all(isinstance(e, dict) and "template" in e and "locationId" in e for e in entries)
	return all(server_map(k) or location_key(k) for k in data)  # (only empty lists: the names must be maps)


def file_forced(path):
	"""True if a spawn file at path holds forced spawns (it is in a CustomSpawnpointsForced folder), False if loose
	loot (CustomSpawnpoints), None if its folder doesn't say (then a name with "forced" in it counts as forced)."""
	if path is None:
		return None
	path = Path(path)
	for parent in path.parents:
		if parent.name.lower() == FORCED_FOLDER.lower():
			return True
		if parent.name.lower() == LOOSE_FOLDER.lower():
			return False
	return True if "forced" in path.stem.lower() else None


def vector(values):
	return {"x": _short(values[0]), "y": _short(values[1]), "z": _short(values[2])}


def spawn_record(item, position, yaw=0.0, count=1, always=True, probability=1.0, name="", gravity=True, random_rotation=False):
	"""A new spawn file entry: one item (template id) at position (x, y, z), turned yaw degrees about the up axis."""
	item_id = new_id()
	return {
		"locationId": location_id(position),
		"probability": _short(probability),
		"template": {
			"Id": f"{name or item} [{uuid.uuid4()}]",
			"IsContainer": False,
			"useGravity": bool(gravity),
			"randomRotation": bool(random_rotation),
			"Position": vector(position),
			"Rotation": vector((0.0, yaw % 360.0, 0.0)),
			"IsGroupPosition": False,
			"GroupPositions": [],
			"IsAlwaysSpawn": bool(always),
			"Root": item_id,
			"Items": [{"_id": item_id, "_tpl": item, "upd": {"StackObjectsCount": int(count)}, "composedKey": item_id}],
		},
		"itemDistribution": [{"composedKey": {"key": item_id}, "relativeProbability": 1}],
	}


def changed_record(record, position=None, yaw=None, item=None, count=None, always=None, probability=None, gravity=None, random_rotation=None, spawn_id=None):
	"""The entry with some of its parts changed; everything else in it kept. Position and Rotation are written in small
	letters (as the server reads them), and the locationId follows the position when it was the old one (as new spawns'
	are)."""
	new = dict(record)
	template = dict(new.get("template") or {})
	new["template"] = template
	for key in ("Position", "Rotation"):
		part = template.get(key)
		if isinstance(part, dict) and not all(axis in part for axis in "xyz"):
			try:
				template[key] = vector(_vector(part, key)[0])
			except (TypeError, ValueError):
				pass
	if position is not None:
		old = template.get("Position")
		try:
			was = location_id(_vector(old, "Position")[0])
		except (TypeError, ValueError):
			was = None
		template["Position"] = vector(position)
		if was is None or new.get("locationId") in (was, None, ""):
			new["locationId"] = location_id(position)
	if yaw is not None:
		try:
			rx, _ry, rz = _vector(template.get("Rotation"), "Rotation")[0]
		except (TypeError, ValueError):
			rx = rz = 0.0
		template["Rotation"] = vector((rx, yaw % 360.0, rz))
	if spawn_id is not None:
		template["Id"] = spawn_id
	if gravity is not None:
		template["useGravity"] = bool(gravity)
	if random_rotation is not None:
		template["randomRotation"] = bool(random_rotation)
	if always is not None:
		template["IsAlwaysSpawn"] = bool(always)
	if probability is not None:
		new["probability"] = _short(probability)
	if item is not None or count is not None:
		items = [dict(i) for i in _items(template)]
		if not items:
			item_id = new_id()
			items = [{"_id": item_id, "_tpl": item or "", "composedKey": item_id}]
			template["Root"] = item_id
			new["itemDistribution"] = [{"composedKey": {"key": item_id}, "relativeProbability": 1}]
		root = items[0]
		if item is not None and item != root.get("_tpl"):
			root["_tpl"] = item
			children = _children(items, root.get("_id"))
			items = [i for i in items if i.get("_id") not in children]  # (another item's parts don't fit it)
		if count is not None:
			upd = dict(root.get("upd") or {})
			upd["StackObjectsCount"] = int(count)
			root["upd"] = upd
		items[0] = root
		template["Items"] = items
	return new


def _children(items, parent_id):
	"""The ids of every item under parent_id, at any depth."""
	below, found = {parent_id}, set()
	grew = True
	while grew:
		grew = False
		for i in items:
			if i.get("parentId") in below and i.get("_id") not in found:
				found.add(i.get("_id"))
				below.add(i.get("_id"))
				grew = True
	return found


def add_spawn(data, location, record):
	"""Put a new entry in a spawn file's data under the map's name (the name it already uses for that map, if WTT
	finds it, else file_name_of). Returns (map name, index)."""
	names = [name for name in data if location_of(name) == location]
	name = next((n for n in names if server_map(n)), names[0] if names else file_name_of(location))
	data.setdefault(name, []).append(record)
	return name, len(data[name]) - 1


class ItemFacts:
	"""What the checks know of items: the game's templates (core.gamedata.GameData, whose names and items include the
	references') and WTT custom items ({id: entry}, from core.references.References.custom_items)."""

	def __init__(self, gamedata=None, custom=None):
		self.gamedata = gamedata
		self.custom = dict(custom or {})

	def _template(self, tpl):
		return self.gamedata.items.get(tpl) if self.gamedata is not None else None

	def name(self, tpl):
		if not tpl:
			return ""
		name = self.gamedata.item_name(tpl) if self.gamedata is not None else ""
		return name or tpl

	def known(self, tpl):
		if self.gamedata is None:
			return True  # (nothing to tell by)
		return self.gamedata.knows_item(tpl) or tpl in self.custom

	def is_quest_item(self, tpl):
		entry = self.custom.get(tpl)
		if isinstance(entry, dict):
			props = entry.get("overrideProperties") or {}
			if "QuestItem" in props:
				return props["QuestItem"] is True
			tpl = entry.get("itemTplToClone") or tpl
		template = self._template(tpl) or {}
		return (template.get("_props") or {}).get("QuestItem") is True

	def is_under(self, tpl, category):
		entry = self.custom.get(tpl)
		if isinstance(entry, dict):
			tpl = entry.get("parentId") or entry.get("itemTplToClone") or tpl
		seen = set()
		while tpl and tpl not in seen:
			if tpl == category:
				return True
			seen.add(tpl)
			tpl = (self._template(tpl) or {}).get("_parent")
		return False


def check_spawn(spawn, others=(), floors=None, items=None):
	"""(errors, warnings, notes) for one spawn. others: the other spawns known (your file's and the references'), for
	clashes; floors: its map's maps.mapdata.Floors (None: no floor check); items: an ItemFacts (None: no item checks)."""
	errors, warnings, notes = [], [], []
	if server_map(spawn.map_name) is None:
		errors.append(f"WTT won't find the map '{spawn.map_name}': name it {file_name_of(spawn.location)} (the spawn is dropped otherwise)")
	if spawn.capitals:
		warnings.append(
			"Its Position or Rotation is written X, Y, Z: the SPT server reads only x, y, z (it passes capitals on unread). "
			"Any change made here writes them in small letters, as the game's own files are."
		)
	record = spawn.record or {}
	root = root_item(record)
	if not spawn.item:
		errors.append("It has no item.")
	elif root is not None and root.get("parentId"):
		errors.append("The first entry of its Items is part of another item: the server spawns the first entry.")
	if not spawn.always:
		keys = {i.get("composedKey") for i in _items(record.get("template") or {}) if i.get("composedKey")}
		drawn = [d for d in record.get("itemDistribution") or [] if isinstance(d, dict) and (d.get("composedKey") or {}).get("key") in keys]
		if not drawn:
			errors.append("No item of it is in its itemDistribution (by composedKey): the server finds nothing to spawn.")
		if spawn.probability <= 0:
			errors.append("Its probability is 0: it never spawns.")
	if items is not None and spawn.item:
		if not items.known(spawn.item):
			warnings.append(f"The item {spawn.item} isn't one the game or your reference files know.")
		elif not spawn.always and items.is_quest_item(spawn.item):
			warnings.append("A quest item that spawns only by chance: a quest needs it there every raid. Tick Every raid, or put it in a forced file.")
		if spawn.count != 1 and (items.is_under(spawn.item, MONEY) or items.is_under(spawn.item, AMMO)):
			notes.append("Money and ammo get a random stack from the server: the count isn't used.")
	same_map = [o for o in others if o.location == spawn.location and not o.same_entry(spawn)]
	for other in same_map:
		if other.location_id and other.location_id == spawn.location_id and other.forced == spawn.forced:
			where = other.source or "your file"
			if spawn.forced:
				errors.append(f"Another forced spawn on this map has its locationId {spawn.location_id} ({where}): WTT keeps only the one it reads first.")
			else:
				warnings.append(f"Another loose loot spawn on this map has its locationId {spawn.location_id} ({where}): WTT merges them into one point.")
			break
	if spawn.always and spawn.id:
		group = [o for o in same_map if o.always and o.id == spawn.id]
		if group:
			notes.append(f"{len(group) + 1} spawns that come every raid have the id {spawn.id}: the server spawns one of them each raid, picked by their probability.")
	if floors is not None:
		warnings += _floor_warnings(spawn, floors)
	return errors, warnings, notes


def _floor_warnings(spawn, floors):
	"""Whether the item lies on a floor: the floor map's, or a wall's top (a table, a shelf) when the walls are read."""
	x, y, z = spawn.position
	heights = floors.floors_at(x, z)
	below = [h for h in heights if h <= y + SUNK]
	gap = y - max(below) if below else None
	sunk = [h for h in heights if y + SUNK < h <= y + 0.5]
	if sunk and (gap is None or gap > 0.3):  # (just under a floor, and not lying on one below it: a table over an item is fine)
		return [f"It is {min(sunk) - y:.2f} m under the floor."]
	if gap is None:
		return ["No floor is mapped under it." + (" It may fall through the map." if spawn.gravity else "")]
	if spawn.gravity and gap > FALLS_FAR:
		return [f"It falls {gap:.1f} m to the floor under it."]
	if not spawn.gravity and gap > HANGS:
		return [f"It hangs {gap:.2f} m above the floor (gravity is off, so it stays there)."]
	return []
