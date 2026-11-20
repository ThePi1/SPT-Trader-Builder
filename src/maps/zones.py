"""Quest zones: the boxes on a map that conditions point at by id (Visit zone, Place marker, Leave items at
location, Inside zone, Launch a flare).

There are the game's own zones (imported from the game's files, see maps.mapdata) and custom ones, which a mod adds
with WTT-CommonLib's quest zone files (CustomQuestZones: a JSON list of zones, numbers written as text). This module
reads and writes those files, knows which zone kinds each condition can use, checks quests and zone files, and
makes new zones that sit on the floor. No Qt.

What the game does with each kind (from the client's code, EFT.Interactive):
- visit (ExperienceTrigger): Visit zone. It also counts as "inside" for Inside zone.
- placeitem (PlaceItemTrigger): Place marker, Leave items at location. It never counts as "inside": it doesn't add
  itself to the zones the player is in.
- trigger (TriggerWithId, QuestTrigger; WTT's botkillzone): Inside zone, including in kill and damage counters.
- flarezone: Launch a flare. The game's own (FlareShootDetectorZone) isn't a trigger zone, so it never counts as
  "inside"; WTT's custom one is both.
- salvage (WTT only): counts as "inside".
"""

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

from core import jsonio
from maps import geometry as G
from maps.mapdata import FLAREZONE, LOCATIONS, PLACEITEM, SALVAGE, TRIGGER, VISIT, MapData, imported, location_key, maps_dir
from core.gamedata import location_ids  # (also used from here by the command line)
from schema.issues import ERROR, WARNING, Issue

GAME = "game"  # Zone.source of the game's own zones

# WTT-CommonLib's ZoneType values -> the kinds above
CUSTOM_KINDS = {"visit": VISIT, "placeitem": PLACEITEM, "botkillzone": TRIGGER, "flarezone": FLAREZONE, "salvage": SALVAGE}
CUSTOM_TYPE = {VISIT: "visit", PLACEITEM: "placeitem", TRIGGER: "botkillzone", FLAREZONE: "flarezone", SALVAGE: "salvage"}

# The colour (red, green, blue) each kind is drawn in, on the map pictures and in the 3D view
KIND_COLOURS = {VISIT: (40, 140, 255), PLACEITEM: (255, 150, 0), TRIGGER: (200, 60, 220), FLAREZONE: (255, 60, 60), SALVAGE: (0, 180, 120)}
NEW_COLOUR = (0, 230, 60)  # a zone being made

PLAYER_HEIGHT = 1.8  # metres: a player standing on the floor reaches this high
SINK = 0.25  # metres: how far a new zone reaches below the floor, so standing on the floor is surely inside


@dataclass
class Zone:
	id: str
	location: str  # the location id (bigmap, factory4_day, ...)
	kind: str  # VISIT, PLACEITEM, TRIGGER, FLAREZONE or SALVAGE
	box: G.Box
	source: str = GAME  # GAME, or the custom zone file it is in
	name: str = ""  # the object's name (game) or ZoneName (custom)
	active: bool = True
	custom_class: str = ""  # the game component (ExperienceTrigger, ...) or the custom ZoneType
	record: dict = field(default=None, repr=False)  # a custom zone's entry as it is in its file

	@property
	def counts_inside(self):
		"""True if standing in it counts for Inside zone (and the kill / damage / exit counters that check zones)."""
		if self.kind == PLACEITEM:
			return False
		if self.kind == FLAREZONE:
			return self.source != GAME
		return True

	def summary(self):
		c = self.box.center
		s = self.box.size
		where = "the game" if self.source == GAME else self.source
		return f"{self.id} ({self.kind}, {self.location}) at {c[0]:.1f}, {c[1]:.1f}, {c[2]:.1f}, {s[0]:.1f} x {s[1]:.1f} x {s[2]:.1f} m, from {where}"

	def as_dict(self):
		return {
			"id": self.id, "location": self.location, "kind": self.kind, "source": self.source, "name": self.name, "active": self.active,
			"center": [round(v, 3) for v in self.box.center], "size": [round(v, 3) for v in self.box.size],
			"rotation": [round(v, 5) for v in self.box.rotation], "yaw": round(G.yaw_of(self.box.rotation), 1),
		}


# --- the game's zones ------------------------------------------------------------------------------------

def zones_of_map(mapdata):
	"""A Zone per box of the game's zones on an imported map (a zone with several boxes is several Zones)."""
	zones = []
	for record in mapdata.zones:
		for box in record.get("boxes", []):
			zones.append(Zone(
				record["id"], mapdata.location, record["kind"], G.Box(box["center"], box["size"], box["rotation"]),
				GAME, record.get("object", ""), record.get("active", True), record.get("class", ""),
			))
	return zones


# --- custom zone files (WTT-CommonLib) ---------------------------------------------------------------------

def _number(value):
	number = float(value)
	if not math.isfinite(number):
		raise ValueError(value)
	return number


def _vector(record, key, size, default=None):
	part = record.get(key)
	if part is None and default is not None:
		return default
	if not isinstance(part, dict):
		raise ValueError(f"{key} is missing")
	return tuple(_number(part.get(axis)) for axis in "XYZW"[:size])


def zone_from_record(record, source=""):
	"""A Zone from one entry of a custom zone file. Raises ValueError (saying what is wrong) for a broken entry."""
	if not isinstance(record, dict):
		raise ValueError("an entry must be an object")
	zone_id = record.get("ZoneId")
	if not isinstance(zone_id, str) or not zone_id:
		raise ValueError("ZoneId is missing")
	kind = CUSTOM_KINDS.get(str(record.get("ZoneType", "")).lower())
	if kind is None:
		raise ValueError(f"ZoneType {record.get('ZoneType')!r} isn't one WTT-CommonLib knows ({', '.join(CUSTOM_KINDS)})")
	try:
		center = _vector(record, "Position", 3)
		size = _vector(record, "Scale", 3)
		rotation = _vector(record, "Rotation", 4, G.IDENTITY)
	except (TypeError, ValueError) as e:
		raise ValueError(f"a position, rotation or scale isn't a number ({e})") from e
	location = str(record.get("ZoneLocation", ""))
	return Zone(
		zone_id, location_key(location) or location, kind, G.Box(center, size, rotation), source,
		str(record.get("ZoneName") or ""), True, str(record.get("ZoneType", "")), record,
	)


def read_zone_file(path):
	"""(zones, problems) of a custom zone file: problems are Issues for the entries that can't be used."""
	path = Path(path)
	data = jsonio.read_json(path)
	records = data if isinstance(data, list) else [data] if isinstance(data, dict) and "ZoneId" in data else None
	if records is None:
		return [], [Issue(ERROR, (), "A quest zone file must be a list of zones.")]
	zones, problems = [], []
	for i, record in enumerate(records):
		try:
			zones.append(zone_from_record(record, path.name))
		except ValueError as e:
			problems.append(Issue(ERROR, (i,), f"{e}."))
	return zones, problems


def is_zone_file(data):
	"""True if the data looks like a custom quest zone file."""
	return isinstance(data, list) and bool(data) and all(isinstance(r, dict) and "ZoneId" in r and "ZoneType" in r for r in data[:20])


def _text(value):
	"""A number as WTT-CommonLib's files write it: plain text, no exponent, no trailing zeros."""
	text = f"{value:.6f}".rstrip("0").rstrip(".")
	return "0" if text in ("-0", "") else text


def zone_record(zone_id, location, kind, box, name=None, flare_type=""):
	"""A custom zone file entry (WTT-CommonLib's CustomQuestZone)."""
	c, s, r = box.center, box.size, box.rotation
	return {
		"ZoneId": zone_id,
		"ZoneName": name or zone_id,
		"ZoneLocation": location,
		"ZoneType": CUSTOM_TYPE[kind],
		"FlareType": flare_type,
		"Position": {"X": _text(c[0]), "Y": _text(c[1]), "Z": _text(c[2]), "W": "0"},
		"Rotation": {"X": _text(r[0]), "Y": _text(r[1]), "Z": _text(r[2]), "W": _text(r[3])},
		"Scale": {"X": _text(s[0]), "Y": _text(s[1]), "Z": _text(s[2]), "W": "0"},
	}


def add_to_zone_file(path, record, replace=False):
	"""Add an entry to a custom zone file (made if it isn't there). An entry with the same ZoneId and ZoneLocation is
	an error unless replace is True, when it takes that entry's place."""
	path = Path(path)
	records = jsonio.read_json(path) if path.is_file() else []
	if not isinstance(records, list):
		raise ValueError(f"{path.name} isn't a list of zones")
	same = [i for i, r in enumerate(records) if isinstance(r, dict) and r.get("ZoneId") == record["ZoneId"] and str(r.get("ZoneLocation", "")).lower() == record["ZoneLocation"].lower()]
	if same and not replace:
		raise ValueError(f"{path.name} already has the zone {record['ZoneId']} on {record['ZoneLocation']}")
	if same:
		records[same[0]] = record
	else:
		records.append(record)
	path.parent.mkdir(parents=True, exist_ok=True)
	jsonio.write_json(path, records)
	return path


# --- every zone known --------------------------------------------------------------------------------------

class ZoneIndex:
	"""The game's zones (from the imported maps) and the zones in custom zone files, by id."""

	def __init__(self, folder=None, files=(), with_game=True):
		self.maps_dir = maps_dir(folder)
		self.zones = []
		self.problems = {}  # {file name: [Issue]} for the custom zone files' broken entries
		self.game_maps = imported(self.maps_dir) if with_game else []
		self._maps = {}
		for location in self.game_maps:
			self.zones += zones_of_map(self.map(location))
		for path in files:
			self.add_file(path)

	def add_file(self, path):
		zones, problems = read_zone_file(path)
		self.zones += zones
		if problems:
			self.problems[Path(path).name] = problems
		return zones

	def add_records(self, records, source):
		"""Add the entries of a custom zone file already read (the broken ones are left out)."""
		for record in records if isinstance(records, list) else []:
			try:
				self.zones.append(zone_from_record(record, source))
			except ValueError:
				continue

	def add(self, zones):
		self.zones += list(zones)

	def map(self, location):
		"""The imported map (maps.mapdata.MapData), read once."""
		key = location_key(location) or location
		if key not in self._maps:
			self._maps[key] = MapData.load(key, self.maps_dir)
		return self._maps[key]

	@property
	def knows_game_zones(self):
		return bool(self.game_maps)

	def by_id(self, zone_id):
		return [z for z in self.zones if z.id == zone_id]

	def on(self, location):
		key = location_key(location) or location
		return [z for z in self.zones if z.location == key]

	def ids(self):
		return sorted({z.id for z in self.zones})


# --- what each condition can use ---------------------------------------------------------------------------

# (group, condition kind) -> (the key holding the zone id or ids, a test of a zone, what it needs in words)
ZONE_FIELDS = {
	("task", "PlaceBeacon"): ("zoneId", lambda z: z.kind == PLACEITEM, "a placeitem zone"),
	("task", "LeaveItemAtLocation"): ("zoneId", lambda z: z.kind == PLACEITEM, "a placeitem zone"),
	("task", "VisitPlace"): ("target", lambda z: z.kind == VISIT, "a visit zone"),
	("subtask", "VisitPlace"): ("target", lambda z: z.kind == VISIT, "a visit zone"),
	("subtask", "InZone"): ("zoneIds", lambda z: z.counts_inside, "a zone that counts as inside (visit, botkillzone / trigger, salvage or a custom flarezone; never placeitem)"),
	("subtask", "LaunchFlare"): ("target", lambda z: z.kind == FLAREZONE, "a flarezone"),
}

# The location ids quests give for maps that hold no quest zones of their own
_ANY_MAP = {"any", "marathon", ""}


def accepts(group, kind):
	"""(key, test, words) for a condition kind that points at zones, else None."""
	return ZONE_FIELDS.get((group, kind))


def _quest_maps(quest, map_ids):
	"""The location keys a quest is set on ({} for any)."""
	location = quest.get("location", "")
	if location in _ANY_MAP:
		return set()
	keys = {key for key, lid in map_ids.items() if lid == location}
	return keys or {location_key(location) or location}


def _counter_maps(task):
	maps = set()
	for sub in (task.get("counter") or {}).get("conditions") or []:
		if isinstance(sub, dict) and sub.get("conditionType") == "Location":
			maps |= {location_key(t) or t for t in sub.get("target") or [] if isinstance(t, str)}
	return maps


def zone_issues(quests, index, map_ids=None):
	"""Problems with the zones the quests point at: a zone no file has (a warning, as it may come from a file the
	program isn't told about), a zone of the wrong kind for its condition (an error: the condition can't be done), and
	a zone only on another map than the condition's (a warning). map_ids is {location key: location _id}
	(data/locations.json), for the quest's own map."""
	issues = []
	if not isinstance(quests, dict):
		return issues
	map_ids = map_ids if map_ids is not None else location_ids()
	for quest_id, quest in quests.items():
		if not isinstance(quest, dict):
			continue
		quest_maps = _quest_maps(quest, map_ids)
		for list_key, tasks in (quest.get("conditions") or {}).items():
			for i, task in enumerate(tasks if isinstance(tasks, list) else []):
				if not isinstance(task, dict):
					continue
				path = (quest_id, "conditions", list_key, i)
				issues += _check_zone_field(task, "task", path, index, quest_maps)
				subs = (task.get("counter") or {}).get("conditions") or []
				maps = _counter_maps(task) or quest_maps
				for k, sub in enumerate(subs if isinstance(subs, list) else []):
					if isinstance(sub, dict):
						issues += _check_zone_field(sub, "subtask", path + ("counter", "conditions", k), index, maps)
	return issues


def _check_zone_field(item, group, path, index, maps):
	rule = accepts(group, item.get("conditionType"))
	if rule is None:
		return []
	key, test, words = rule
	value = item.get(key)
	ids = value if isinstance(value, list) else [value]
	issues = []
	for zone_id in ids:
		if not isinstance(zone_id, str) or not zone_id:
			continue
		found = index.by_id(zone_id)
		if not found:
			if index.knows_game_zones:
				issues.append(Issue(WARNING, path + (key,), f"No map or zone file has a zone '{zone_id}'."))
			continue
		if not any(test(z) for z in found):
			kinds = ", ".join(sorted({z.kind for z in found}))
			issues.append(Issue(ERROR, path + (key,), f"The zone '{zone_id}' is {kinds}, but this condition needs {words}, so it can't be completed."))
			continue
		if maps and not any(test(z) and z.location in maps for z in found):
			where = ", ".join(sorted({z.location for z in found if test(z)}))
			issues.append(Issue(WARNING, path + (key,), f"The zone '{zone_id}' is on {where}, not on {', '.join(sorted(maps))}."))
	return issues


# --- checking zone files, and making zones -----------------------------------------------------------------

def check_zone(zone, index):
	"""Problems with one custom zone, as plain sentences: (errors, warnings). Uses the map's floor when the map has
	been imported."""
	errors, warnings = [], []
	if zone.location not in LOCATIONS:
		errors.append(f"ZoneLocation '{zone.location}' isn't a map WTT-CommonLib can load it on ({', '.join(LOCATIONS)}).")
		return errors, warnings
	if min(zone.box.size) <= 0:
		errors.append("Its Scale has a zero side, so it has no room inside.")
		return errors, warnings
	if not G.is_upright(zone.box.rotation):
		warnings.append("It is tilted (its rotation turns it about more than the up axis).")
	for other in index.zones:
		if other is zone or other.location != zone.location:
			continue
		if other.id == zone.id and other.source != GAME and other.source == zone.source and other.record is not zone.record:
			errors.append(f"Its ZoneId is used twice in {zone.source}.")
		elif other.id == zone.id and other.source == GAME:
			warnings.append("The game has a zone with this id on this map too: both count.")
		elif zone.kind == PLACEITEM and other.kind == PLACEITEM and other.id != zone.id and other.box.overlaps(zone.box):
			warnings.append(
				f"It overlaps the placeitem zone '{other.id}' ({'the game' if other.source == GAME else other.source}). The game only "
				"remembers the last placeitem zone the player walked into and forgets it when they leave either one, so where they "
				"overlap the player may not be offered to place the item."
			)
	if zone.location in index.game_maps:
		errors_, warnings_ = floor_report(zone.box, index.map(zone.location).navmesh)
		errors += errors_
		warnings += warnings_
	return list(dict.fromkeys(errors)), list(dict.fromkeys(warnings))


FAR_OFF = 3.0  # metres: a box this far above or below every floor around it can't be reached
LOOK_AROUND = 6.0  # metres: how far around a box with no floor inside to look for one


def floor_report(box, navmesh):
	"""(errors, warnings) about whether a player can get into a box. A trigger fires when the player's body touches it,
	so a player standing on a floor reaches a box whose bottom is below their head and whose top is above their feet.

	The game's floor map (the bots' navigation mesh) leaves out some spots a player can reach (rooms and upper floors
	the bots never enter, the tops of crates, and half a metre along every wall), so everything found here is a warning:
	even some of the game's own zones are where the map has no floor. (errors is always empty; it is there so this
	reads like the other checks.)"""
	errors, warnings = [], []
	bottom, top = box.center[1] - box.size[1] / 2, box.center[1] + box.size[1] / 2
	hits, _total, heights = _reach_samples(box, navmesh, lambda h: bottom - PLAYER_HEIGHT <= h <= top)
	if hits:
		storeys = _storeys(heights)
		if len(storeys) > 1:
			warnings.append(
				f"A player on any of {len(storeys)} floors here is inside it (floors at {', '.join(f'{h:.1f}' for h in storeys)} m): "
				"make it shorter if it's meant for one of them."
			)
		return errors, warnings
	around = floors_around(navmesh, box.center[0], box.center[2])
	if not around:
		warnings.append(
			f"No walkable floor is mapped in it or within {LOOK_AROUND:.0f} m. The game's floor map leaves out some spots players "
			"can reach (rooms bots never enter, the tops of objects), so check this one in game."
		)
		return errors, warnings
	gap = min(bottom - PLAYER_HEIGHT - h if h < bottom - PLAYER_HEIGHT else h - top for h in around)
	nearest = min(around, key=lambda h: abs(h - box.center[1]))
	if gap > FAR_OFF:
		where = "above" if nearest < bottom else "below"
		warnings.append(
			f"It is {gap:.1f} m {where} the reach of a player on the mapped floors around it (the nearest is at {nearest:.1f} m; the box "
			f"spans {bottom:.1f} to {top:.1f} m). The floor map leaves out floors bots never walk (upper rooms, catwalks), so if it isn't "
			"on one of those, move it."
		)
	else:
		warnings.append(
			f"No walkable floor is mapped inside it, though there is floor nearby at {nearest:.1f} m. The game's floor map leaves out "
			"some spots players can reach, so check it in game."
		)
	return errors, warnings


def floors_around(navmesh, x, z, radius=LOOK_AROUND):
	"""The floor heights at (x, z) and at points around it (2 m apart, out to radius metres)."""
	found = list(navmesh.floors_at(x, z))
	r = 2.0
	while r <= radius + 1e-6:
		for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1), (0.7, 0.7), (-0.7, 0.7), (0.7, -0.7), (-0.7, -0.7)):
			found += navmesh.floors_at(x + dx * r, z + dz * r)
		r += 2.0
	return found


def footprint_points(box, step=0.5):
	"""(x, z) of the spots the checks look at under a box: its footprint sampled every `step` metres."""
	nx, nz = max(1, round(box.size[0] / step)), max(1, round(box.size[2] / step))
	for i in range(nx):
		for k in range(nz):
			local = (-box.size[0] / 2 + (i + 0.5) * box.size[0] / nx, 0.0, -box.size[2] / 2 + (k + 0.5) * box.size[2] / nz)
			px, _py, pz = G.add(box.center, G.rotate(box.rotation, local))
			yield px, pz


def _reach_samples(box, navmesh, reach, step=0.5):
	"""(spots where a player on a floor would touch the box, spots in all, those floors' heights), sampling the box's
	footprint every step metres."""
	hits, total, heights = 0, 0, []
	for px, pz in footprint_points(box, step):
		total += 1
		found = [h for h in navmesh.floors_at(px, pz) if reach(h)]
		if found:
			hits += 1
			heights += found
	return hits, total, heights


def reach_samples(box, navmesh, step=0.5):
	"""What floor_report looks at, spot by spot, to draw it: [((x, y, z), reached)]. reached is True where a player
	standing on a mapped floor touches the box (y is that floor); elsewhere y is the floor nearest the box's bottom, or
	the bottom itself where no floor is mapped."""
	bottom, top = box.center[1] - box.size[1] / 2, box.center[1] + box.size[1] / 2
	found = []
	for px, pz in footprint_points(box, step):
		floors = navmesh.floors_at(px, pz)
		inside = [h for h in floors if bottom - PLAYER_HEIGHT <= h <= top]
		if inside:
			found.append(((px, max(inside), pz), True))
		else:
			y = min(floors, key=lambda h: abs(h - bottom)) if floors else bottom
			found.append(((px, y, pz), False))
	return found


def _storeys(heights, gap=2.5, share=0.15):
	"""The floor heights that are storeys apart (more than gap metres), each holding at least `share` of the heights."""
	clusters = []
	for h in sorted(heights):
		if clusters and h - clusters[-1][-1] <= gap:
			clusters[-1].append(h)
		else:
			clusters.append([h])
	big = [c for c in clusters if len(c) >= share * len(heights)]
	return [round(sum(c) / len(c), 1) for c in big]


STEP_DOWN = 1.6  # metres: floor samples side by side less than this apart in height are one walk (the floor map draws stairs in coarse steps)


def walkable_span(navmesh, box, start, step=0.5):
	"""(lowest, highest) floor a player walks to inside the box's footprint from height `start` near its middle,
	going from sample to sample (`step` metres apart) up or down less than STEP_DOWN: the whole flight of stairs or ramp
	under a zone. (start, start) when there is no floor at that height near the middle."""
	nx, nz = max(1, round(box.size[0] / step)), max(1, round(box.size[2] / step))
	samples = {}
	for i in range(nx):
		for k in range(nz):
			local = (-box.size[0] / 2 + (i + 0.5) * box.size[0] / nx, 0.0, -box.size[2] / 2 + (k + 0.5) * box.size[2] / nz)
			px, _py, pz = G.add(box.center, G.rotate(box.rotation, local))
			samples[(i, k)] = navmesh.floors_at(px, pz)
	middle = ((nx - 1) / 2, (nz - 1) / 2)
	starts = sorted(
		((i, k, h) for (i, k), floors in samples.items() for h in floors if abs(h - start) <= 0.5),
		key=lambda s: (s[0] - middle[0]) ** 2 + (s[1] - middle[1]) ** 2,
	)
	if not starts:
		return start, start
	seen = {starts[0]}
	todo = [starts[0]]
	while todo:
		i, k, h = todo.pop()
		for n in ((i + 1, k), (i - 1, k), (i, k + 1), (i, k - 1)):
			for h2 in samples.get(n, ()):
				state = (n[0], n[1], h2)
				if abs(h2 - h) < STEP_DOWN and state not in seen:
					seen.add(state)
					todo.append(state)
	heights = [h for _i, _k, h in seen]
	return min(heights), max(heights)


def make_zone(index, zone_id, location, kind, x, z, y=None, size=(4.0, 3.0, 4.0), yaw=0.0, name=None, slope=False):
	"""A new zone standing on the floor at (x, z): its bottom SINK metres below the floor (the floor nearest to height y
	if given, else the lowest), turned `yaw` degrees. size is (width, height, depth) in metres. Returns (record for the
	zone file, Zone, notes) where notes say which floor was used. Where the floor map has no floor at (x, z), the height
	y is used as the floor if given, else the nearest floor within a few metres. slope=True is for a zone on stairs or a
	ramp: its bottom goes down to the lowest floor of the walk under it (walkable_span), not the floor at its middle.
	Raises ValueError if the map isn't imported, or there is no floor to go by."""
	key = location_key(location)
	if key is None:
		raise ValueError(f"'{location}' isn't a map ({', '.join(LOCATIONS)}).")
	if key not in index.game_maps:
		raise ValueError(f"The map {key} hasn't been imported: run the maps import first.")
	if kind not in CUSTOM_TYPE:
		raise ValueError(f"The kind must be one of {', '.join(CUSTOM_TYPE)}.")
	if min(size) <= 0:
		raise ValueError("Every side of the zone must be longer than 0.")
	navmesh = index.map(key).navmesh
	floors = navmesh.floors_at(x, z)
	if floors:
		floor = min(floors, key=lambda h: abs(h - y)) if y is not None else floors[0]
		notes = [f"Floor at {floor:.2f} m" + (f" (of {len(floors)} floors here: {', '.join(f'{h:.1f}' for h in floors)})." if len(floors) > 1 else ".")]
	elif y is not None:
		floor = float(y)
		notes = [f"No floor is mapped at {x:.1f}, {z:.1f}, so the height you gave ({floor:.2f} m) is used as the floor: check it in game."]
	else:
		around = floors_around(navmesh, x, z)
		if not around:
			raise ValueError(
				f"No walkable floor is mapped at {x:.1f}, {z:.1f} on {key} or within {LOOK_AROUND:.0f} m. Give the floor's height (y) "
				"if a player can stand there, or pick another spot."
			)
		floor = min(around)
		notes = [f"No floor is mapped exactly here, so the lowest floor nearby ({floor:.2f} m) is used: give y to choose another."]
	box = G.Box((float(x), floor, float(z)), (float(size[0]), float(size[1]), float(size[2])), G.yaw_rotation(yaw))
	low, high = walkable_span(navmesh, box, floor)
	if slope:
		top = low - SINK + float(size[1])
		notes.append(f"On a slope: the walk under it goes from {low:.2f} to {high:.2f} m, so its bottom is at the lowest.")
		if top < high + 0.5:
			notes.append(f"Its top ({top:.2f} m) is less than half a metre above the highest floor under it: make it taller.")
		floor = low
	elif low < floor - 0.5:
		notes.append(
			f"The floor under it goes down to {low:.2f} m (stairs or a ramp), below its bottom: add --slope if it is meant to cover "
			"the whole slope."
		)
	center = (float(x), floor - SINK + float(size[1]) / 2, float(z))
	box = G.Box(center, (float(size[0]), float(size[1]), float(size[2])), G.yaw_rotation(yaw))
	record = zone_record(zone_id, key, kind, box, name)
	zone = zone_from_record(record, "(new)")
	return record, zone, notes


def nearby(index, location, point, radius=30.0, kinds=None):
	"""The zones on a map within radius metres of a point, nearest first: [(distance, Zone)]."""
	found = []
	for zone in index.on(location):
		if kinds and zone.kind not in kinds:
			continue
		distance = zone.box.distance_to(point)
		if distance <= radius:
			found.append((round(distance, 1), zone))
	return sorted(found, key=lambda pair: pair[0])


def dumps_zones(zones):
	return json.dumps([z.as_dict() for z in zones], indent=1)
