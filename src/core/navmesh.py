"""Where a player can stand on a map: the game's navigation mesh (the floor the bots walk on), as polygons.

Used to put a quest zone on the floor and to check that a player can walk into it. The mesh is a little smaller
than the real floor (it keeps about half a metre from walls) and leaves out spots only a player can reach by
jumping, so a zone a few metres wide is always checked by sampling, never one point. No Qt.
"""

from core.geometry import add, point_in_polygon, rotate

CELL = 8.0  # metres: the size of the squares the polygons are filed under, for finding them quickly


class NavMesh:
	"""vertices: [(x, y, z)]; polygons: [(vertex indexes, area)]. Area 1 is usually "not walkable" in Unity, but EFT's
	areas are its own, so every polygon counts as floor."""

	def __init__(self, vertices, polygons):
		self.vertices = [tuple(v) for v in vertices]
		self.polygons = [(tuple(p[0]), p[1] if len(p) > 1 else 0) for p in polygons]
		self._outline = []  # per polygon: [(x, z)], (min x, min z, max x, max z), plane (a, b, c, d) or None
		self._grid = {}
		for index, (verts, _area) in enumerate(self.polygons):
			points = [self.vertices[v] for v in verts]
			flat = [(p[0], p[2]) for p in points]
			xs, zs = [p[0] for p in flat], [p[1] for p in flat]
			bounds = (min(xs), min(zs), max(xs), max(zs))
			self._outline.append((flat, bounds, _plane(points)))
			for gx in range(int(bounds[0] // CELL), int(bounds[2] // CELL) + 1):
				for gz in range(int(bounds[1] // CELL), int(bounds[3] // CELL) + 1):
					self._grid.setdefault((gx, gz), []).append(index)

	def __len__(self):
		return len(self.polygons)

	def bounds(self):
		"""((min x, min y, min z), (max x, max y, max z)) of the whole mesh."""
		if not self.vertices:
			return (0, 0, 0), (0, 0, 0)
		return tuple(min(v[i] for v in self.vertices) for i in range(3)), tuple(max(v[i] for v in self.vertices) for i in range(3))

	def floors_at(self, x, z):
		"""The heights of every floor at this spot, lowest first (several in a building with storeys)."""
		heights = []
		for index in self._grid.get((int(x // CELL), int(z // CELL)), ()):
			flat, (x0, z0, x1, z1), plane = self._outline[index]
			if x0 <= x <= x1 and z0 <= z <= z1 and point_in_polygon(x, z, flat):
				heights.append(self._height(index, x, z, plane))
		return sorted(set(round(h, 3) for h in heights))

	def floor_near(self, x, y, z, below=3.0, above=1.0):
		"""The floor at (x, z) closest to height y, looking down to `below` metres and up to `above` metres; None if there is none."""
		best = None
		for h in self.floors_at(x, z):
			if y - below <= h <= y + above and (best is None or abs(h - y) < abs(best - y)):
				best = h
		return best

	def _height(self, index, x, z, plane):
		if plane is None:  # (an upright polygon: take its average height)
			verts = self.polygons[index][0]
			return sum(self.vertices[v][1] for v in verts) / len(verts)
		a, b, c, d = plane
		return -(a * x + c * z + d) / b

	def polygons_near(self, x0, z0, x1, z1):
		"""The indexes of the polygons whose outline may reach into this rectangle (seen from above)."""
		found = set()
		for gx in range(int(x0 // CELL), int(x1 // CELL) + 1):
			for gz in range(int(z0 // CELL), int(z1 // CELL) + 1):
				for index in self._grid.get((gx, gz), ()):
					px0, pz0, px1, pz1 = self._outline[index][1]
					if px1 >= x0 and px0 <= x1 and pz1 >= z0 and pz0 <= z1:
						found.add(index)
		return sorted(found)

	def outline(self, index):
		"""A polygon as [(x, y, z)] corners."""
		return [self.vertices[v] for v in self.polygons[index][0]]

	def floor_in_box(self, box, step=0.5):
		"""Sample the box's footprint every `step` metres: (spots with floor inside the box's height, spots in all,
		[floor heights found inside]). A spot counts when a floor sits between the box's bottom and top."""
		bottom, top = box.center[1] - box.size[1] / 2, box.center[1] + box.size[1] / 2
		hits, total, heights = 0, 0, []
		nx, nz = max(1, round(box.size[0] / step)), max(1, round(box.size[2] / step))
		for i in range(nx):
			for k in range(nz):
				local = (-box.size[0] / 2 + (i + 0.5) * box.size[0] / nx, 0.0, -box.size[2] / 2 + (k + 0.5) * box.size[2] / nz)
				px, _py, pz = add(box.center, rotate(box.rotation, local))
				total += 1
				inside = [h for h in self.floors_at(px, pz) if bottom - 0.05 <= h <= top]
				if inside:
					hits += 1
					heights.extend(inside)
		return hits, total, heights


def _plane(points):
	"""(a, b, c, d) of the plane a*x + b*y + c*z + d = 0 through a polygon's first three corners, or None if it stands
	upright (b near 0)."""
	if len(points) < 3:
		return None
	(x1, y1, z1), (x2, y2, z2), (x3, y3, z3) = points[0], points[1], points[2]
	ux, uy, uz = x2 - x1, y2 - y1, z2 - z1
	vx, vy, vz = x3 - x1, y3 - y1, z3 - z1
	a, b, c = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
	if abs(b) < 1e-9:
		return None
	return a, b, c, -(a * x1 + b * y1 + c * z1)


def merge_tiles(tiles):
	"""One NavMesh from navmesh tiles (core.unity.NavTile): their vertices joined in one list."""
	vertices, polygons = [], []
	for tile in tiles:
		base = len(vertices)
		vertices.extend(tile.vertices)
		polygons.extend((tuple(base + v for v in verts), area) for verts, area in tile.polygons)
	return NavMesh(vertices, polygons)
