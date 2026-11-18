"""The maps' quest zones and floors, imported from the game's own files.

``import_maps`` reads the game client's scenes (see core.unity) and writes two files per map into the maps folder:
``<location>.json`` with the quest zones the game has (their id, kind and box) and the map's areas (where its places,
such as the dorms, are), and ``<location>.navmesh.json.gz`` with the walkable floor (the navigation mesh). That data
comes from the game, so it stays on the user's computer (the folder is not part of the repository).
``MapData.load`` reads a map back. No Qt.
"""

import gzip
import json
import time
from dataclasses import dataclass
from pathlib import Path

from core import geometry as G
from core import jsonio
from core import unity as U
from core.navmesh import NavMesh, merge_tiles
from core.paths import DATA_DIR

FORMAT = 1
MAPS_DIR = DATA_DIR / "maps"  # (read when used, so tests can point it elsewhere)


def maps_dir(folder=None):
	"""The folder of imported maps: folder if given, else MAPS_DIR."""
	return Path(folder) if folder else MAPS_DIR

# Zone kinds, as the quest zone files of WTT-CommonLib name them
VISIT, PLACEITEM, TRIGGER, FLAREZONE, SALVAGE = "visit", "placeitem", "trigger", "flarezone", "salvage"
ZONE_KINDS = (VISIT, PLACEITEM, TRIGGER, FLAREZONE, SALVAGE)

# The game's zone components and the kind each one is (EFT.Interactive)
TRIGGER_CLASSES = {
	"ExperienceTrigger": VISIT,  # VisitPlace: the player walks in
	"PlaceItemTrigger": PLACEITEM,  # PlaceBeacon, LeaveItemAtLocation: the player plants an item in it
	"QuestTrigger": TRIGGER,  # InZone: the player is inside
	"TriggerWithId": TRIGGER,
}
FLARE_CLASS = "FlareShootDetectorZone"  # LaunchFlare: a flare fired inside it


@dataclass(frozen=True)
class MapScenes:
	"""Which of the game's scenes make up a map: the scenes under Assets/Content/Locations/<folder>/, without any
	whose name contains one of `skip`."""

	folder: str
	skip: tuple = ()

	def has(self, scene):
		prefix = f"Assets/Content/Locations/{self.folder}/"
		return scene.startswith(prefix) and not any(s in scene[len(prefix):] for s in self.skip)


# {location id (as quests and zone files name it): its scenes}. Checked against every zone the base game's quests use.
LOCATIONS = {
	"bigmap": MapScenes("Custom"),
	"factory4_day": MapScenes("Factory_Rework", ("Night",)),
	"factory4_night": MapScenes("Factory_Rework", ("_Day", "Factory_Rework_Quests.unity")),
	"Woods": MapScenes("Woods"),
	"Shoreline": MapScenes("shorline"),
	"Interchange": MapScenes("Shopping_Mall"),
	"RezervBase": MapScenes("Reserve_Base"),
	"laboratory": MapScenes("Laboratory"),
	"Lighthouse": MapScenes("Lighthouse"),
	"TarkovStreets": MapScenes("City"),
	"Sandbox": MapScenes("Sandbox", ("_high",)),
	"Sandbox_high": MapScenes("Sandbox", ("Sandbox_AI.unity",)),
	"Labyrinth": MapScenes("Labyrinth"),
}


def location_key(location):
	"""The location id as written in LOCATIONS for any spelling ('BigMap' -> 'bigmap'), or None."""
	lowered = str(location).lower()
	return next((key for key in LOCATIONS if key.lower() == lowered), None)


# --- importing -----------------------------------------------------------------------------------------

class _Scripts:
	"""The class names of the scripts behind MonoBehaviours, read once per script."""

	def __init__(self, data_dir):
		self.data_dir = data_dir
		self._files = {}
		self._names = {}

	def _file(self, name):
		if name not in self._files:
			path = self.data_dir / name
			try:
				self._files[name] = U.SerializedFile(path) if path.is_file() else None
			except U.FormatError:
				self._files[name] = None
		return self._files[name]

	def class_of(self, sf, script_index):
		if script_index < 0 or script_index >= len(sf.scripts):
			return None
		file_index, path_id = sf.scripts[script_index]
		where = sf.external_name(file_index)
		key = (where or str(sf.path), path_id)
		if key not in self._names:
			target = sf if file_index == 0 else self._file(where)
			try:
				self._names[key] = U.read_mono_script(target, path_id)[1] if target is not None and path_id in target.objects else None
			except (U.FormatError, IndexError, ValueError):
				self._names[key] = None
		return self._names[key]

	def close(self):
		for sf in self._files.values():
			if sf is not None:
				sf.close()


def _box_of(transforms, sf, collider_id):
	"""A box collider in world space: (center, size, rotation)."""
	box = U.read_box_collider(sf, collider_id)
	rotation, position, lossy = transforms.world(_transform_of(sf, box.game_object[1]))
	center = G.add(position, G.rotate(rotation, G.scale(box.center, lossy)))
	size = tuple(abs(s * l) for s, l in zip(box.size, lossy))
	return center, size, G.q_normalize(rotation), box


def _transform_of(sf, game_object_id):
	for file_index, component in U.read_game_object(sf, game_object_id).components:
		if file_index == 0 and component in sf.objects and sf.class_id(component) in (U.TRANSFORM, U.RECT_TRANSFORM):
			return component
	raise U.FormatError("game object without a transform")


def _colliders(sf, game_object_id):
	return [
		component for file_index, component in U.read_game_object(sf, game_object_id).components
		if file_index == 0 and component in sf.objects and sf.class_id(component) == U.BOX_COLLIDER
	]


def _zone_boxes(sf, transforms, game_object_id):
	boxes = []
	for collider in _colliders(sf, game_object_id):
		center, size, rotation, _box = _box_of(transforms, sf, collider)
		boxes.append({"center": _round(center), "size": _round(size), "rotation": _round(rotation, 5)})
	return boxes


def _round(values, digits=3):
	return [round(v, digits) for v in values]


def scene_zones(sf, scripts, scene):
	"""Every quest zone in one scene file: [{id, kind, class, object, active, scene, boxes: [{center, size, rotation}]}]."""
	zones = []
	transforms = U.TransformCache(sf)
	for path_id in sf.of_class(U.MONO_BEHAVIOUR):
		name = scripts.class_of(sf, sf.script_index(path_id))
		if name not in TRIGGER_CLASSES and name != FLARE_CLASS:
			continue
		behaviour = U.read_behaviour(sf, path_id)
		zone_id = behaviour.reader.string()
		game_object_id = behaviour.game_object[1]
		holders = [game_object_id]
		if name == FLARE_CLASS:  # (its colliders can sit on the objects of its trigger handlers)
			r = behaviour.reader
			r.i32()  # flareTypeForHandle
			for _ in range(r.i32()):
				file_index, handler = r.pptr()
				if file_index == 0 and handler in sf.objects:
					holders.append(U.read_behaviour(sf, handler).game_object[1])
		game_object = U.read_game_object(sf, game_object_id)
		boxes = []
		for holder in dict.fromkeys(holders):
			boxes += _zone_boxes(sf, transforms, holder)
		zones.append({
			"id": zone_id,
			"kind": TRIGGER_CLASSES.get(name, FLAREZONE),
			"class": name,
			"object": game_object.name,
			"active": bool(game_object.active and behaviour.enabled),
			"scene": scene.rsplit("/", 1)[-1],
			"boxes": boxes,
		})
	return zones


# Words in the names of the scenes that hold a map's lighting, sound, bots and so on rather than a place
_NOT_AREAS = {
	"ai", "high", "light", "sound", "culling", "scripts", "design", "designmain", "designstuff", "stuff", "terrain", "background",
	"multiscene", "quests", "loot", "levelborders", "borders", "old", "combined", "portals",
}


def scene_area(sf, scene):
	"""Where a scene's objects are (the scenes of a map are mostly its places: the dorms, the gas station, ...):
	{name, scene, min: [x, y, z], max: [x, y, z]} around the middle 96% of its objects, or None for a scene that
	isn't a place."""
	stem = scene.rsplit("/", 1)[-1][:-len(".unity")] if scene.endswith(".unity") else scene.rsplit("/", 1)[-1]
	if any(word.lower() in _NOT_AREAS for word in stem.split("_")):
		return None
	transforms = U.TransformCache(sf)
	points = []
	for path_id in sf.of_class(U.TRANSFORM):
		try:
			points.append(transforms.world(path_id)[1])
		except (U.FormatError, KeyError, IndexError):
			continue
	if len(points) < 10:
		return None
	low, high = [], []
	for axis in range(3):
		values = sorted(p[axis] for p in points)
		cut = len(values) // 50
		low.append(round(values[cut], 1))
		high.append(round(values[-1 - cut], 1))
	name = stem.split("_", 1)[1] if "_" in stem else stem
	return {"name": name, "scene": stem, "min": low, "max": high, "objects": len(points)}


def find_objects(game_dir, location, text, limit=50):
	"""Objects in a map's scenes whose name contains every word of text (case-insensitive), straight from the game's
	files: [{name, scene, position: [x, y, z]}]. Slow-ish (it reads the map's scenes), so it is only done on request."""
	words = text.lower().split()
	data_dir = Path(game_dir) / "EscapeFromTarkov_Data"
	with U.SerializedFile(data_dir / "globalgamemanagers") as ggm:
		scenes = U.read_scene_list(ggm)
	spec = LOCATIONS[location_key(location) or location]
	found = []
	for index, scene in enumerate(scenes):
		if not spec.has(scene) or not (data_dir / f"level{index}").is_file():
			continue
		with U.SerializedFile(data_dir / f"level{index}") as sf:
			transforms = U.TransformCache(sf)
			for path_id in sf.of_class(U.GAME_OBJECT):
				game_object = U.read_game_object(sf, path_id)
				lowered = game_object.name.lower()
				if not all(w in lowered for w in words):
					continue
				try:
					position = transforms.world(_transform_of(sf, path_id))[1]
				except (U.FormatError, KeyError, IndexError):
					continue
				found.append({"name": game_object.name, "scene": scene.rsplit("/", 1)[-1], "position": _round(position, 2)})
				if len(found) >= limit:
					return found
	return found


def scene_navmesh(sf):
	"""The largest navigation mesh in a scene's shared assets, as tiles (core.unity.NavTile), or []."""
	meshes = sf.of_class(U.NAV_MESH_DATA)
	if not meshes:
		return []
	biggest = max(meshes, key=lambda pid: sf.objects[pid][1])
	return [U.parse_nav_tile(data) for data in U.read_navmesh_tiles(sf, biggest)]


def import_maps(game_dir, out_dir=None, locations=None, progress=None):
	"""Read the game's maps and write a file per map into out_dir. game_dir is the game's folder (the one with
	EscapeFromTarkov_Data). Returns {location: {zones, polygons, file}}. progress(text) is told what is being read."""
	say = progress or (lambda text: None)
	data_dir = Path(game_dir) / "EscapeFromTarkov_Data"
	if not (data_dir / "globalgamemanagers").is_file():
		raise FileNotFoundError(f"No EscapeFromTarkov_Data\\globalgamemanagers in {game_dir}: is this the game's folder?")
	with U.SerializedFile(data_dir / "globalgamemanagers") as ggm:
		scenes = U.read_scene_list(ggm)
		unity_version = ggm.unity_version
	wanted = [loc for loc in (locations or LOCATIONS) if loc in LOCATIONS]
	out_dir = maps_dir(out_dir)
	out_dir.mkdir(parents=True, exist_ok=True)
	scripts = _Scripts(data_dir)
	scene_cache, nav_cache, summary = {}, {}, {}
	try:
		for location in wanted:
			spec = LOCATIONS[location]
			mine = [(i, s) for i, s in enumerate(scenes) if spec.has(s)]
			zones, areas, tiles = [], [], []
			for index, scene in mine:
				if index not in scene_cache:
					say(f"{location}: {scene.rsplit('/', 1)[-1]}")
					scene_cache[index] = _read_scene(
						data_dir / f"level{index}", lambda sf: (scene_zones(sf, scripts, scene), scene_area(sf, scene)), ([], None),
					)
				found_zones, area = scene_cache[index]
				zones += found_zones
				if area:
					areas.append(area)
				if scene.endswith(("_AI.unity", "_AI_high.unity")):
					if index not in nav_cache:
						nav_cache[index] = _read_scene(data_dir / f"sharedassets{index}.assets", scene_navmesh, [])
					tiles += nav_cache[index]
			navmesh = merge_tiles(tiles)
			record = {
				"format": FORMAT,
				"location": location,
				"unity": unity_version,
				"source": str(Path(game_dir)),
				"imported": time.strftime("%Y-%m-%d %H:%M:%S"),
				"scenes": [s for _i, s in mine],
				"zones": zones,
				"areas": areas,
			}
			path = out_dir / f"{location}.json"
			jsonio.write_json(path, record, indent=None)
			with gzip.open(out_dir / f"{location}{NAVMESH_SUFFIX}", "wt", encoding="utf-8") as f:
				json.dump({
					"format": FORMAT,
					"vertices": [round(c, 3) for v in navmesh.vertices for c in v],
					"polygons": [list(verts) for verts, _area in navmesh.polygons],
				}, f, separators=(",", ":"))
			summary[location] = {"zones": len(zones), "areas": len(areas), "polygons": len(navmesh), "file": str(path)}
	finally:
		scripts.close()
	return summary


def _read_scene(path, read, default):
	if not path.is_file():
		return default
	with U.SerializedFile(path) as sf:
		return read(sf)


# --- reading it back -----------------------------------------------------------------------------------

NAVMESH_SUFFIX = ".navmesh.json.gz"


class MapData:
	"""One imported map: its zones ([dict], see scene_zones), its areas (see scene_area) and its floor (navmesh, read
	from its own file when first used)."""

	def __init__(self, record, path=None):
		self.record = record
		self.path = Path(path) if path else None
		self.location = record.get("location", "")
		self.zones = record.get("zones", [])
		self.areas = record.get("areas", [])
		self._navmesh = None

	@classmethod
	def load(cls, location, folder=None):
		key = location_key(location) or location
		path = maps_dir(folder) / f"{key}.json"
		if not path.is_file():
			raise FileNotFoundError(f"The map {location} hasn't been imported (no {path}).")
		record = jsonio.read_json(path)
		if record.get("format") != FORMAT:
			raise ValueError(f"{path} was imported by another version of this program: import the maps again.")
		return cls(record, path)

	@property
	def navmesh(self):
		if self._navmesh is None:
			nav = {}
			path = self.path.with_name(f"{self.location}{NAVMESH_SUFFIX}") if self.path else None
			if path is not None and path.is_file():
				with gzip.open(path, "rt", encoding="utf-8") as f:
					nav = json.load(f)
			flat = nav.get("vertices", [])
			vertices = [tuple(flat[i:i + 3]) for i in range(0, len(flat), 3)]
			self._navmesh = NavMesh(vertices, [(tuple(p), 0) for p in nav.get("polygons", [])])
		return self._navmesh


def imported(folder=None):
	"""The locations that have been imported, in the order of LOCATIONS."""
	folder = maps_dir(folder)
	return [loc for loc in LOCATIONS if (folder / f"{loc}.json").is_file()]
