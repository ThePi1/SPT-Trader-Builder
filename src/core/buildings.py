"""The building at a spot on an imported map: its outline, storeys and rooms, and a quest zone that covers all of it.

Worked out from two things the map import keeps (core.mapdata):

- the floor map (the bots' navigation mesh). A building's upper storeys and roofs are floor well above the ground
  around it, so the connected patch of such floor nearest the spot is the building, and the smallest turned rectangle
  around it is its outline. A building with no upper floor the bots walk can't be outlined this way.
- the named objects. Many buildings name their rooms and storeys (Floor_2_Room_1, stairs_f3, Roof_2), which finds
  storeys the bots never walk: the floor map has no floor where bots don't go.

Walls aren't read (they are mesh colliders), so the outline is the upper floors' and a zone gets a margin. No Qt.
"""

import math
import re
import statistics

from core.zones import SINK

UP = 2.0  # metres above the ground around a building: floor this high is an upper storey or a roof
STEP = 0.75  # metres between the floor samples
STOREY_GAP = 1.2  # metres: floor heights further apart than this are different storeys
MIN_STOREY = 10.0  # square metres: less floor than this at one height is a stair or a ledge, not a storey
REACH_ABOVE = 2.5  # metres: how far above the top storey a covering zone reaches (a player's height, and some)

ROOM_WORDS = {"room", "rooms", "corridor", "corrid", "hall", "hangar", "stairs", "stair", "staircase", "roof", "basement", "attic", "lobby"}
NOT_ROOMS = re.compile(r"(?i)^(audioportal|reverb)")
NOT_ROOM_SCENES = re.compile(r"(?i)light")  # (a map's lighting scene names its light groups Floor1, Floor2, ...)
FLOOR_NUMBER = (  # (tried in turn: "Floor_2", "f2" or "level 2"; then "2nd floor"; then "2F")
	re.compile(r"(?i)(?:floor[_ ]?|(?<![a-z])f|level[_ ]?)(\d{1,2})(?![0-9])"),
	re.compile(r"(?i)(?<![0-9])(\d)(?:st|nd|rd|th)[_ ]?fl(?:oor)?(?![a-z])"),
	re.compile(r"(?i)(?<![0-9a-z])(\d)f(?![a-z])"),
)
_WORDS = re.compile(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+")


def floor_number(name):
	"""The storey a name says it is on (Floor_2_Room_1 -> 2, stairs_f3 -> 3, 2nd_floor -> 2), else None."""
	for pattern in FLOOR_NUMBER:
		match = pattern.search(name)
		if match:
			return int(match.group(1))
	return None


def words(name):
	"""A name's words, split at underscores, spaces, digits and capitals: ServerRoom_main -> server, room, main."""
	return [w.lower() for w in _WORDS.findall(name)]


def is_room(name):
	"""True for a name of a room, corridor, stairs, roof or storey (Floor_1_Room_3, stairs_f2, Roof_1), not of a prop
	that is named after one (Broom_03, office_Folders_FloorSet2)."""
	if NOT_ROOMS.search(name):
		return False
	found = set(words(name))
	return bool(found & ROOM_WORDS) or ("floor" in found and floor_number(name) is not None)


def ground_around(navmesh, x, z, radius):
	"""The ground height around a spot: the middle of the lowest floors on rings around it."""
	lows = []
	for r in (radius * 0.6, radius * 0.8, radius):
		for i in range(16):
			a = i * math.pi / 8
			floors = navmesh.floors_at(x + r * math.sin(a), z + r * math.cos(a))
			if floors:
				lows.append(floors[0])
	if not lows:
		floors = navmesh.floors_at(x, z)
		return floors[0] if floors else None
	return statistics.median(lows)


def _upper_patch(navmesh, x, z, ground, radius):
	"""The (x, z) samples of the connected patch of upper floor nearest the spot, or []."""
	n = int(radius / STEP)
	cells = set()
	for i in range(-n, n + 1):
		for k in range(-n, n + 1):
			if any(h > ground + UP for h in navmesh.floors_at(x + i * STEP, z + k * STEP)):
				cells.add((i, k))
	if not cells:
		return []
	start = min(cells, key=lambda c: c[0] * c[0] + c[1] * c[1])
	if math.hypot(*start) * STEP > radius / 2:
		return []
	patch, todo = {start}, [start]
	while todo:
		i, k = todo.pop()
		for di in (-1, 0, 1):
			for dk in (-1, 0, 1):
				c = (i + di, k + dk)
				if c in cells and c not in patch:
					patch.add(c)
					todo.append(c)
	return [(x + i * STEP, z + k * STEP) for i, k in patch]


def _quantile(values, q):
	ordered = sorted(values)
	return ordered[min(len(ordered) - 1, max(0, int(q * (len(ordered) - 1))))]


def outline(points, trim=0.002):
	"""The smallest turned rectangle around points [(x, z)], ignoring the outermost `trim` share on each side (a few
	stray samples; more would cut the corners off and turn the rectangle):
	(center (x, z), size (width, depth), yaw in degrees 0..90, clockwise from north), as a zone's box takes them."""
	best = None
	for step in range(180):
		yaw = step * 0.5
		c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
		u = [px * c - pz * s for px, pz in points]  # along the box's own x (width)
		v = [px * s + pz * c for px, pz in points]  # along its own z (depth)
		u0, u1, v0, v1 = _quantile(u, trim), _quantile(u, 1 - trim), _quantile(v, trim), _quantile(v, 1 - trim)
		area = (u1 - u0) * (v1 - v0)
		if best is None or area < best[0]:
			best = (area, yaw, u0, u1, v0, v1)
	_area, yaw, u0, u1, v0, v1 = best
	c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
	uc, vc = (u0 + u1) / 2, (v0 + v1) / 2
	center = (uc * c + vc * s, -uc * s + vc * c)
	return center, (u1 - u0 + STEP, v1 - v0 + STEP), yaw


def corners(center, size, yaw):
	c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
	found = []
	for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
		u, v = su * size[0] / 2, sv * size[1] / 2
		found.append((round(center[0] + u * c + v * s, 2), round(center[1] - u * s + v * c, 2)))
	return found


def _inside(center, size, yaw, px, pz, margin=0.0):
	c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
	dx, dz = px - center[0], pz - center[1]
	u, v = dx * c - dz * s, dx * s + dz * c
	return abs(u) <= size[0] / 2 + margin and abs(v) <= size[1] / 2 + margin


def storeys(navmesh, center, size, yaw):
	"""The floor heights inside the outline that are big enough to be storeys: [{height, area_m2}], lowest first.
	Storeys are the heights where much floor lies (stairs and ramps between them hold little), at least STOREY_GAP
	metres apart."""
	c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
	heights = []
	nu, nv = int(size[0] / STEP), int(size[1] / STEP)
	for i in range(nu + 1):
		for k in range(nv + 1):
			u, v = -size[0] / 2 + i * STEP, -size[1] / 2 + k * STEP
			heights += navmesh.floors_at(center[0] + u * c + v * s, center[1] - u * s + v * c)
	return storeys_of(heights, STEP * STEP)


def storeys_of(heights, cell, smallest=MIN_STOREY):
	"""The storeys among floor heights sampled `cell` square metres apart: [{height, area_m2}], lowest first."""
	bins = {}
	for h in heights:
		bins.setdefault(round(h * 4), []).append(h)  # (quarter-metre bins)
	found = []
	for key in sorted(bins, key=lambda b: -len(bins[b])):
		near = [h for b in range(key - 2, key + 3) for h in bins.get(b, [])]
		if len(near) * cell < smallest or any(abs(key / 4 - f["height"]) < STOREY_GAP + 0.6 for f in found):
			continue
		found.append({"height": round(statistics.median(near), 2), "area_m2": round(len(near) * cell)})
	return sorted(found, key=lambda f: f["height"])


def rooms_in(objects, center, size, yaw, low, high, margin=1.0):
	"""The room-like objects (rooms, corridors, stairs, floors, roofs) inside the outline between two heights:
	[{name, at, floor}] with floor the storey number the name gives, if any."""
	if objects is None:
		return []
	wanted = objects.name_indexes(is_room)
	found = {}
	for name, scene, (x, y, z) in objects.rows(wanted):
		if NOT_ROOM_SCENES.search(scene):
			continue
		if low - 1.0 <= y <= high + 1.0 and _inside(center, size, yaw, x, z, margin) and name not in found:
			found[name] = {"name": name, "at": [round(x, 2), round(y, 2), round(z, 2)], "floor": floor_number(name), "scene": scene}
	return sorted(found.values(), key=lambda r: (r["at"][1], r["name"]))


def named_floors(rooms):
	"""{storey number: {about: height, rooms: [names]}} from rooms whose names give their storey."""
	by_floor = {}
	for room in rooms:
		if room["floor"] is not None:
			by_floor.setdefault(room["floor"], []).append(room)
	return {
		n: {"about": round(statistics.median(r["at"][1] for r in rs), 1), "rooms": [r["name"] for r in rs][:12]}
		for n, rs in sorted(by_floor.items())
	}


def building_at(mapdata, x, z, radius=40.0, margin=1.0):
	"""What is known of the building at (x, z) on an imported map (core.mapdata.MapData), as a dict: its outline
	(center, size, yaw, corners), the ground around it, its storeys (from the floor map and from named rooms), its rooms,
	and a zone that covers every storey with `margin` metres to spare (as `zones make` arguments)."""
	navmesh, objects = mapdata.navmesh, mapdata.objects
	result = {"map": mapdata.location, "at": [x, z]}
	notes = []
	ground = ground_around(navmesh, x, z, radius)
	if ground is None:
		result["notes"] = [f"No floor is mapped around {x:.1f}, {z:.1f}."]
		return result
	result["ground"] = round(ground, 2)
	patch = _upper_patch(navmesh, x, z, ground, radius)
	if not patch:
		notes.append(
			"No upper floor is mapped near here (bots don't walk this building's upper storeys, or it has none), so its outline "
			"can't be worked out from the floor map: the rooms below are those within 15 m."
		)
		near = rooms_in(objects, (x, z), (30.0, 30.0), 0.0, ground - 10, ground + 30, 0.0)
		result.update(rooms=near[:60], floors_named=named_floors(near), notes=notes)
		return result
	center, size, yaw = outline(patch)
	result["outline"] = {
		"center": [round(center[0], 2), round(center[1], 2)], "size": [round(size[0], 2), round(size[1], 2)],
		"yaw": round(yaw, 1), "corners": [list(c) for c in corners(center, size, yaw)],
	}
	found = storeys(navmesh, center, size, yaw)
	for s in found:
		s["source"] = "floor map"
		if s["height"] < ground - UP:
			s["below_ground"] = True
	levels = [s["height"] for s in found]
	rooms = rooms_in(objects, center, size, yaw, min(levels), max(levels) + 6.0)
	named = named_floors(rooms)
	for number, info in named.items():
		guess = round(info["about"] - 0.3, 1)  # (a room's object sits a little above its floor)
		if all(abs(guess - h) > STOREY_GAP for h in levels):
			found.append({"height": guess, "source": f"named rooms of storey {number} (not on the floor map: bots don't go there)"})
			levels.append(guess)
	result["storeys"] = sorted(found, key=lambda s: s["height"])
	result["floors_named"] = named
	result["rooms"] = rooms[:80]
	under = [s["height"] for s in found if s.get("below_ground")]
	if under:
		notes.append(
			f"Floor {', '.join(f'{h:.1f}' for h in under)} m is more than {UP:.0f} m below the ground around the building: a basement, or "
			"a tunnel or bunker under it. The zone leaves it out; add it by hand if it is part of the building."
		)
	levels = [h for h in levels if h not in under] or levels
	bottom = min(levels) - SINK
	top = max(levels) + REACH_ABOVE
	width, depth = size[0] + 2 * margin, size[1] + 2 * margin
	result["zone"] = {
		"at": f"{center[0]:.2f},{center[1]:.2f},{min(levels):.2f}", "size": f"{width:.1f},{top - bottom:.1f},{depth:.1f}",
		"yaw": round(yaw, 1), "bottom": round(bottom, 2), "top": round(top, 2),
	}
	if objects is None:
		notes.append("The map was imported before objects were indexed, so rooms and named storeys are missing: run `maps import` again.")
	notes.append(
		"The outline is the upper floors' (walls aren't read), and the floor map leaves out what bots never walk: "
		"check the picture (--picture) and the rooms list before using the zone."
	)
	result["notes"] = notes
	return result


def rooms_covered(objects, box):
	"""The room-like objects inside a zone's box (core.geometry.Box): [{name, floor}]."""
	if objects is None:
		return None
	found = {}
	for name, scene, _position in objects.inside(box, 0.0, objects.name_indexes(is_room)):
		if not NOT_ROOM_SCENES.search(scene):
			found.setdefault(name, {"name": name, "floor": floor_number(name)})
	return sorted(found.values(), key=lambda r: (r["floor"] is None, r["floor"] or 0, r["name"]))
