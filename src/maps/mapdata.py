"""The maps' quest zones and floors, imported from the game's own files.

``import_maps`` reads the game client's scenes (see maps.unity) and writes three files per map into the maps folder:
``<location>.json`` with the quest zones the game has (their id, kind and box) and the map's areas (where its places,
such as the dorms, are), ``<location>.navmesh.json.gz`` with the walkable floor (the navigation mesh), and
``<location>.objects.json.gz`` with every named object and where it is (for finding places by name) and
``<location>.walls.npz`` with the walls and floors players bump into (maps.walls, for the 3D view). That data comes
from the game, so it stays on the user's computer (the folder is not part of the repository).
``MapData.load`` reads a map back. No Qt.
"""

import gzip
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path

from maps import geometry as G
from core import jsonio
from maps import unity as U
from maps.navmesh import NavMesh, merge_tiles
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
	"multiscene", "quests", "loot", "levelborders", "borders", "combined", "portals",  # (not "old": custom_AZS_old is the old gas station)
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


# The copies a model has for its levels of detail, shadow, ballistics and colliders (Door_LOD0, Door_COLLIDER, ...):
# left out of the object index, where they would only repeat the model's own name
_COPY_NAMES = re.compile(r"(_LOD\d+|_SHADOW(_LOD\d+)?|_BALLISTIC.*|_COLLIDER.*)$", re.IGNORECASE)


def scene_objects(sf):
	"""Every named object in a scene file and where it is: [(name, (x, y, z))], leaving out the level-of-detail,
	shadow, ballistic and collider copies of models."""
	transforms = U.TransformCache(sf)
	found = []
	for path_id in sf.of_class(U.TRANSFORM) + sf.of_class(U.RECT_TRANSFORM):
		try:
			transform = U.read_transform(sf, path_id)
			if transform.game_object[0] != 0 or transform.game_object[1] not in sf.objects:
				continue
			name = U.read_game_object(sf, transform.game_object[1]).name
			if not name or _COPY_NAMES.search(name):
				continue
			found.append((name, transforms.world(path_id)[1]))
		except (U.FormatError, KeyError, IndexError):
			continue
	return found


def find_objects(game_dir, location, text, limit=50):
	"""Objects in a map's scenes whose name contains every word of text (case-insensitive), straight from the game's
	files: [{name, scene, position: [x, y, z]}]. Slow (it reads the map's scenes): an imported map's object index
	(MapData.objects) answers the same question at once."""
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
	"""The largest navigation mesh in a scene's shared assets, as tiles (maps.unity.NavTile), or []."""
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
	from maps import walls as W  # (numpy)

	with U.SerializedFile(data_dir / "globalgamemanagers") as ggm:
		scenes = U.read_scene_list(ggm)
		unity_version = ggm.unity_version
		try:
			layers = W.wall_layers(ggm)
		except U.FormatError:
			layers = set()
	wanted = [loc for loc in (locations or LOCATIONS) if loc in LOCATIONS]
	out_dir = maps_dir(out_dir)
	out_dir.mkdir(parents=True, exist_ok=True)
	scripts = _Scripts(data_dir)
	meshes = W.Meshes(data_dir)
	scene_cache, nav_cache, summary = {}, {}, {}
	last_use = {}  # {scene index: the last map that uses it}, to let go of a scene's objects once no map needs them
	for location in wanted:
		for index, scene in enumerate(scenes):
			if LOCATIONS[location].has(scene):
				last_use[index] = location
	try:
		for location in wanted:
			spec = LOCATIONS[location]
			mine = [(i, s) for i, s in enumerate(scenes) if spec.has(s)]
			zones, areas, tiles, objects, placed = [], [], [], {}, []
			for index, scene in mine:
				if index not in scene_cache:
					say(f"{location}: {scene.rsplit('/', 1)[-1]}")
					scene_cache[index] = _read_scene(
						data_dir / f"level{index}",
						lambda sf: (scene_zones(sf, scripts, scene), scene_area(sf, scene), scene_objects(sf), W.scene_walls(sf, meshes, layers)),
						([], None, [], []),
					)
				found_zones, area, found_objects, found_walls = scene_cache[index]
				placed += found_walls
				zones += found_zones
				if area:
					areas.append(area)
				stem = _stem(scene)
				for name, position in found_objects:
					objects.setdefault((name, *(round(c, 1) for c in position)), (stem, position))
				if scene.endswith(("_AI.unity", "_AI_high.unity")):
					if index not in nav_cache:
						nav_cache[index] = _read_scene(data_dir / f"sharedassets{index}.assets", scene_navmesh, [])
					tiles += nav_cache[index]
			for index, _scene in mine:
				if last_use.get(index) == location:
					scene_cache.pop(index, None)
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
			_write_objects(out_dir / f"{location}{OBJECTS_SUFFIX}", objects)
			wall_triangles = W.write(out_dir / f"{location}{W.WALLS_SUFFIX}", placed, meshes)
			summary[location] = {
				"zones": len(zones), "areas": len(areas), "polygons": len(navmesh), "objects": len(objects), "wall_triangles": wall_triangles,
				"file": str(path),
			}
	finally:
		scripts.close()
		meshes.close()
	return summary


def _stem(scene):
	name = scene.rsplit("/", 1)[-1]
	return name[:-len(".unity")] if name.endswith(".unity") else name


def _write_objects(path, objects):
	"""The object index: {format, scenes, names, objects: flat [name index, scene index, x, y, z in centimetres, ...]}."""
	names, scenes, flat = {}, {}, []
	for (name, *_rounded), (stem, position) in objects.items():
		flat += [names.setdefault(name, len(names)), scenes.setdefault(stem, len(scenes)), *(round(c * 100) for c in position)]
	with gzip.open(path, "wt", encoding="utf-8") as f:
		json.dump({"format": FORMAT, "scenes": list(scenes), "names": list(names), "objects": flat}, f, separators=(",", ":"))


def _read_scene(path, read, default):
	if not path.is_file():
		return default
	with U.SerializedFile(path) as sf:
		return read(sf)


# --- reading it back -----------------------------------------------------------------------------------

NAVMESH_SUFFIX = ".navmesh.json.gz"
OBJECTS_SUFFIX = ".objects.json.gz"


class ObjectIndex:
	"""The named objects of an imported map (see scene_objects): looked up by name, or by where they are."""

	def __init__(self, record):
		self.scenes = record.get("scenes", [])
		self.names = record.get("names", [])
		self._flat = record.get("objects", [])

	def __len__(self):
		return len(self._flat) // 5

	def rows(self, names=None):
		"""(name, scene, (x, y, z)) of every object, or of those whose name's index is in the set `names`."""
		flat = self._flat
		for i in range(0, len(flat), 5):
			n = flat[i]
			if names is None or n in names:
				yield self.names[n], self.scenes[flat[i + 1]], (flat[i + 2] / 100, flat[i + 3] / 100, flat[i + 4] / 100)

	def name_indexes(self, test):
		"""The indexes of the names test(name) accepts."""
		return {i for i, name in enumerate(self.names) if test(name)}

	def search(self, text, limit=50):
		"""Objects whose name holds every word of text (any case), as find_objects gives them."""
		words = text.lower().split()
		wanted = self.name_indexes(lambda name: all(w in name.lower() for w in words))
		found = []
		for name, scene, position in self.rows(wanted):
			found.append({"name": name, "scene": scene + ".unity", "position": _round(position, 2)})
			if len(found) >= limit:
				break
		return found

	def inside(self, box, margin=0.0, names=None):
		"""(name, scene, position) of the objects inside a box (maps.geometry.Box)."""
		(x0, y0, z0), (x1, y1, z1) = box.bounds()
		for name, scene, (x, y, z) in self.rows(names):
			if x0 - margin <= x <= x1 + margin and z0 - margin <= z <= z1 + margin and y0 - margin <= y <= y1 + margin:
				if box.contains((x, y, z), margin):
					yield name, scene, (x, y, z)


class MapData:
	"""One imported map: its zones ([dict], see scene_zones), its areas (see scene_area), its floor (navmesh) and its
	named objects (objects); the last two are read from their own files when first used."""

	def __init__(self, record, path=None):
		self.record = record
		self.path = Path(path) if path else None
		self.location = record.get("location", "")
		self.zones = record.get("zones", [])
		self.areas = record.get("areas", [])
		self._navmesh = None
		self._objects = None
		self._walls = None
		self._floors = None

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

	@property
	def objects(self):
		"""The map's named objects (ObjectIndex), or None when it was imported before objects were indexed."""
		if self._objects is None:
			path = self.path.with_name(f"{self.location}{OBJECTS_SUFFIX}") if self.path else None
			if path is None or not path.is_file():
				return None
			with gzip.open(path, "rt", encoding="utf-8") as f:
				self._objects = ObjectIndex(json.load(f))
		return self._objects


	@property
	def walls(self):
		"""The walls, floors and stairs players bump into (maps.triangles.Triangles), or None when the map was imported
		without them."""
		if self._walls is None:
			from maps import walls as W
			from maps.triangles import Triangles

			corners = W.load(self)
			self._walls = Triangles(corners) if corners is not None else False
		return self._walls or None

	@property
	def floors(self):
		"""Where a player can stand (Floors): the floor map and, when they were imported, the tops of the walls."""
		if self._floors is None:
			self._floors = Floors(self.navmesh, self.walls)
		return self._floors


class Floors:
	"""The floor map (the navmesh) and the level tops of the walls together: floors_at gives both, a wall's top within
	SAME metres of a floor of the floor map counting as that floor. The walls know the floors bots never walk (upstairs
	rooms, roofs, catwalks) and the steps of stairs. Wall tops more than DEEP metres below the floor map's lowest point
	are left out: some maps have a plane far under everything (Customs and Reserve at -99.5 m) to catch what falls."""

	SAME = 0.4
	DEEP = 15.0

	def __init__(self, navmesh, walls=None):
		self.navmesh, self.walls = navmesh, walls
		self._lowest = navmesh.bounds()[0][1] - self.DEEP if len(navmesh) else -1e9

	def floors_at(self, x, z):
		return self.floors_at_points([(x, z)])[0]

	def floors_at_points(self, points):
		"""floors_at for many (x, z) points at once (the walls' tops are looked up together: see Triangles)."""
		points = [(float(x), float(z)) for x, z in points]
		mapped = [list(self.navmesh.floors_at(x, z)) for x, z in points]
		if self.walls is None:
			return [sorted(heights) for heights in mapped]
		tops = self.walls.floors_at_points(points)
		return [
			sorted(here + [h for h in top if h >= self._lowest and all(abs(h - g) > self.SAME for g in here)])
			for here, top in zip(mapped, tops)
		]

	def floor_near(self, x, y, z, below=3.0, above=1.0):
		"""The floor at (x, z) closest to height y, looking down to `below` metres and up to `above` metres; None if there is none."""
		found = [h for h in self.floors_at(x, z) if y - below <= h <= y + above]
		return min(found, key=lambda h: abs(h - y)) if found else None


def imported(folder=None):
	"""The locations that have been imported, in the order of LOCATIONS."""
	folder = maps_dir(folder)
	return [loc for loc in LOCATIONS if (folder / f"{loc}.json").is_file()]
