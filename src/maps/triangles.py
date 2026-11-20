"""Triangles in map space (Unity's axes: x east, y up, z north), for drawing a map in 3D and finding what a click hits.

The 3D view draws the floor (the navmesh's polygons, cut into triangles) and, when they have been imported, the walls
(see maps.walls) as Triangles, and asks them which triangle a ray from the camera hits first. Uses numpy. No Qt.
"""

from dataclasses import dataclass

import numpy as np

from maps import geometry as G

EPSILON = 1e-7
CELL = 8.0  # metres: the squares (seen from above) triangles are filed under, for picking among many
CELLS_FROM = 150_000  # triangles: from this many, a ray only looks at the triangles filed under the squares it crosses
WIDE = 64  # a triangle over more squares than this is looked at by every ray instead
LEVEL = 0.7  # how far up a surface's normal must point to be stood on (about 45 degrees of slope at most)
CHUNK = 12  # squares looked at together
BATCH = 2_000_000  # points times triangles worked out at once when looking for floors (memory, about 16 MB an array)
FLOOR_GAP, FEW_ABOVE = 10.0, 0.04  # floor_range leaves out floors above a 10 m band with none, holding under 4% of the floor


@dataclass(frozen=True)
class Hit:
	"""Where a ray hit: how far along it, the point (x, y, z), and the triangle's index (or the box's, see ray_box)."""

	distance: float
	point: tuple
	index: int


class Triangles:
	"""corners: an array of shape (n, 3, 3), the three corners (x, y, z) of each triangle."""

	def __init__(self, corners, cells_from=CELLS_FROM):
		self.corners = np.ascontiguousarray(np.asarray(corners, dtype=np.float32).reshape(-1, 3, 3))
		self._bounds = None
		self._cells = None
		self._cells_from = cells_from
		self._level = {}  # {level: which triangles are level enough to stand on}
		self._section = None  # (steep, lowest corners, highest corners, which are steep): see section

	@classmethod
	def from_navmesh(cls, navmesh):
		"""The navmesh's polygons (convex, as Unity makes them) cut into fans of triangles."""
		vertices = np.asarray(navmesh.vertices, dtype=np.float32).reshape(-1, 3)
		picks = []
		for verts, _area in navmesh.polygons:
			for i in range(1, len(verts) - 1):
				picks.append((verts[0], verts[i], verts[i + 1]))
		if not picks:
			return cls(np.zeros((0, 3, 3), dtype=np.float32))
		return cls(vertices[np.asarray(picks, dtype=np.int64)])

	def __len__(self):
		return len(self.corners)

	def bounds(self):
		"""((min x, y, z), (max x, y, z)) of all the triangles; zeros when there are none."""
		if not len(self):
			return (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
		if self._bounds is None:
			flat = self.corners.reshape(-1, 3)
			self._bounds = tuple(float(v) for v in flat.min(axis=0)), tuple(float(v) for v in flat.max(axis=0))
		return self._bounds

	def heights(self):
		"""The heights of all the corners (a view, not a copy)."""
		return self.corners[:, :, 1].ravel()

	def normals(self):
		"""Each triangle's unit normal (n, 3), pointing up for a floor seen from above (a zero vector for a sliver)."""
		a, b, c = self.corners[:, 0], self.corners[:, 1], self.corners[:, 2]
		n = np.cross(b - a, c - a)  # (the navmesh's polygons go round so that this points up for a floor)
		length = np.linalg.norm(n, axis=1, keepdims=True)
		return np.divide(n, length, out=np.zeros_like(n), where=length > 1e-12)

	def vertex_array(self):
		"""What the graphics card draws: the corners, (n * 3, 3) float32 (the view works out each triangle's slope
		itself). The same memory as corners, not a copy."""
		return self.corners.reshape(-1, 3)

	def pick(self, origin, direction, below=None):
		"""The first triangle the ray from origin along direction hits (a Hit), or None. below (a height) leaves out
		whatever is above it, as the view does when it cuts the map at a height."""
		if not len(self):
			return None
		o = np.asarray(origin, dtype=np.float64)
		d = np.asarray(direction, dtype=np.float64)
		if len(self) >= self._cells_from:
			return self._pick_by_cells(o, d, below)
		return self._pick_among(np.arange(len(self)), o, d, below)

	def _pick_among(self, index, o, d, below):
		"""The nearest hit among the triangles numbered in index (a box test first, then the triangles left)."""
		if not len(index):
			return None
		tri = self.corners[index]
		low, high = tri.min(axis=1), tri.max(axis=1)
		safe = np.where(np.abs(d) < 1e-12, 1e-12, d)
		with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
			t1 = (low - o) / safe
			t2 = (high - o) / safe
		near = np.minimum(t1, t2).max(axis=1)
		far = np.maximum(t1, t2).min(axis=1)
		candidates = far >= np.maximum(near, 0.0)
		if below is not None:
			candidates &= low[:, 1] <= below
		index = index[candidates]
		if not len(index):
			return None
		t, ok = _ray_triangles(o, d, tri[candidates].astype(np.float64))
		if below is not None:
			ok &= o[1] + t * d[1] <= below + 1e-4
		if not ok.any():
			return None
		best = np.argmin(np.where(ok, t, np.inf))
		distance = float(t[best])
		return Hit(distance, tuple(float(v) for v in o + distance * d), int(index[best]))

	def floors_at(self, x, z, level=LEVEL):
		"""The heights of the triangles over or under (x, z) that face up and are level enough to stand on (their normal
		at least `level` up), lowest first. Ceilings (facing down) and steep slopes are left out."""
		return self.floors_at_points([(x, z)], level)[0]

	def floors_at_points(self, points, level=LEVEL):
		"""floors_at for many (x, z) points at once, [heights] for each: the points in one square are looked at
		together, so a zone's whole footprint costs about as much as a few single points."""
		pts = np.asarray(points, dtype=np.float64).reshape(-1, 2)
		found = [[] for _ in range(len(pts))]
		if not len(self) or not len(pts):
			return found
		standable = self._standable(level)
		if len(self) >= self._cells_from or len(self) * len(pts) > BATCH:
			if self._cells is None:
				self._file_cells()
			unique, starts, filed, wide = self._cells
			wide = wide[standable[wide]]
			keys = _key(np.floor(pts[:, 0] / CELL), np.floor(pts[:, 1] / CELL))
			order = np.argsort(keys, kind="stable")
			groups, group_starts = np.unique(keys[order], return_index=True)
			group_starts = np.append(group_starts, len(order))
			for g, key in enumerate(groups):
				which = order[group_starts[g]:group_starts[g + 1]]
				at = np.searchsorted(unique, key)
				index = filed[starts[at]:starts[at + 1]] if at < len(unique) and unique[at] == key else filed[:0]
				index = index[standable[index]]
				self._heights_over(np.concatenate([index, wide]) if len(wide) else index, pts, which, found)
		else:
			self._heights_over(np.nonzero(standable)[0], pts, np.arange(len(pts)), found)
		return [sorted(set(heights)) for heights in found]

	def floor_range(self, gap=FLOOR_GAP, few=FEW_ABOVE):
		"""(lowest, highest) height of these floors (the navmesh's), leaving out floors high above the rest: those above
		a band of `gap` metres with no floor, holding less than `few` of the floor's area. Ground Zero's tall buildings
		have floors on their roofs, from 82 m up to 347 m (3% of its floor); the rest of it is below 66 m."""
		if not len(self):
			return 0.0, 0.0
		c = self.corners.astype(np.float64)
		area = 0.5 * np.linalg.norm(np.cross(c[:, 1] - c[:, 0], c[:, 2] - c[:, 0]), axis=1)
		order = np.argsort(c[:, :, 1].mean(axis=1), kind="stable")
		middle, area = c[order, :, 1].mean(axis=1), area[order]
		above = area.sum() - np.cumsum(area)
		lowest = float(c[:, :, 1].min())
		for i in np.nonzero(np.diff(middle) >= gap)[0]:
			if above[i] < few * area.sum():
				return lowest, float(c[order[:i + 1], :, 1].max())
		return lowest, float(c[:, :, 1].max())

	def section(self, height, steep=LEVEL):
		"""Where the steep triangles (walls: a normal less than `steep` up or down) cross the level `height`: line
		segments (n, 2, 3), float32. Drawn at a cut, they outline every wall it slices through, as on a floor plan."""
		if not len(self):
			return np.zeros((0, 2, 3), np.float32)
		low, high, walls = self._spans(steep)
		index = np.nonzero((low < height) & (high > height) & walls)[0]
		tri = self.corners[index].astype(np.float64)
		y = tri[:, :, 1] - height
		y[y == 0] = 1e-6  # (a corner right at the height counts as above it)
		points, crossed = [], []
		with np.errstate(divide="ignore", invalid="ignore"):
			for i, j in ((0, 1), (1, 2), (2, 0)):
				t = y[:, i] / (y[:, i] - y[:, j])
				points.append(tri[:, i] + t[:, None] * (tri[:, j] - tri[:, i]))
				crossed.append((y[:, i] < 0) != (y[:, j] < 0))
		points, crossed = np.stack(points, axis=1), np.stack(crossed, axis=1)  # (n, 3 edges, 3), (n, 3): two edges cross
		rows = np.arange(len(index))
		first, last = np.argmax(crossed, axis=1), 2 - np.argmax(crossed[:, ::-1], axis=1)
		return np.stack([points[rows, first], points[rows, last]], axis=1).astype(np.float32)

	def _spans(self, steep):
		"""(lowest corner, highest corner, steep or not) of every triangle, kept for section."""
		if self._section is None or self._section[0] != steep:
			low, high = np.zeros(len(self), dtype=np.float32), np.zeros(len(self), dtype=np.float32)
			walls = np.zeros(len(self), dtype=bool)
			for s in range(0, len(self), 1 << 20):
				tri = self.corners[s:s + (1 << 20)]
				low[s:s + len(tri)], high[s:s + len(tri)] = tri[:, :, 1].min(axis=1), tri[:, :, 1].max(axis=1)
				t = tri.astype(np.float64)
				n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
				walls[s:s + len(tri)] = np.abs(n[:, 1]) < steep * np.linalg.norm(n, axis=1)
			self._section = (steep, low, high, walls)
		return self._section[1:]

	def _standable(self, level):
		"""Which triangles face up and are level enough to stand on (kept for each level asked about)."""
		if level not in self._level:
			mask = np.zeros(len(self), dtype=bool)
			for s in range(0, len(self), 1 << 20):  # (in parts: Lighthouse's walls are 6 million triangles)
				tri = self.corners[s:s + (1 << 20)].astype(np.float64)
				n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
				length = np.linalg.norm(n, axis=1)
				mask[s:s + len(tri)] = (length > 0) & (n[:, 1] >= level * length)
			self._level[level] = mask
		return self._level[level]

	def _heights_over(self, index, pts, which, found):
		"""Add to found[w] the height of each triangle in index over or under the point pts[w], for w in which."""
		if not len(index) or not len(which):
			return
		tri = self.corners[index].astype(np.float64)
		a, b, c = tri[:, 0], tri[:, 1], tri[:, 2]
		v0x, v0z, v1x, v1z = c[:, 0] - a[:, 0], c[:, 2] - a[:, 2], b[:, 0] - a[:, 0], b[:, 2] - a[:, 2]
		det = v0x * v1z - v1x * v0z
		flat = np.abs(det) > 1e-12
		safe = np.where(flat, det, 1.0)
		step = max(1, BATCH // len(index))
		for s in range(0, len(which), step):
			part = which[s:s + step]
			x, z = pts[part, 0:1], pts[part, 1:2]  # (points, 1) against (triangles,)
			v2x, v2z = x - a[:, 0], z - a[:, 2]
			u = (v2x * v1z - v1x * v2z) / safe
			v = (v0x * v2z - v2x * v0z) / safe
			p, t = np.nonzero(flat & (u >= -1e-6) & (v >= -1e-6) & (u + v <= 1 + 1e-6))
			heights = a[t, 1] + u[p, t] * (c[t, 1] - a[t, 1]) + v[p, t] * (b[t, 1] - a[t, 1])
			for w, h in zip(part[p].tolist(), heights.tolist()):
				found[w].append(round(h, 3))

	# --- many triangles: filed under squares ---------------------------------------------------------------
	def _file_cells(self):
		"""(sorted square keys, where each square's triangles start, the triangles square by square, wide triangles)."""
		xz = self.corners[:, :, [0, 2]]
		c0 = np.floor(xz.min(axis=1) / CELL).astype(np.int64)
		c1 = np.floor(xz.max(axis=1) / CELL).astype(np.int64)
		del xz
		span = c1 - c0 + 1
		count = span[:, 0] * span[:, 1]
		wide = np.nonzero(count > WIDE)[0]
		narrow = np.nonzero(count <= WIDE)[0]
		n = count[narrow]
		triangle = np.repeat(narrow, n)
		k = np.arange(int(n.sum())) - np.repeat(np.cumsum(n) - n, n)
		sx = span[triangle, 0]
		cx = c0[triangle, 0] + k % sx
		cz = c0[triangle, 1] + k // sx
		keys = _key(cx, cz)
		order = np.argsort(keys, kind="stable")
		keys, triangle = keys[order], triangle[order]
		unique, starts = np.unique(keys, return_index=True)
		self._cells = (unique, np.append(starts, len(keys)), triangle, wide)

	def _pick_by_cells(self, o, d, below):
		if self._cells is None:
			self._file_cells()
		unique, starts, filed, wide = self._cells
		low, high = (np.asarray(b, dtype=np.float64) for b in self.bounds())
		safe = np.where(np.abs(d) < 1e-12, 1e-12, d)
		t1, t2 = (low - 1e-3 - o) / safe, (high + 1e-3 - o) / safe
		enter, leave = max(float(np.minimum(t1, t2).max()), 0.0), float(np.maximum(t1, t2).min())
		if leave < enter:
			return None
		best = self._pick_among(wide, o, d, below) if len(wide) else None
		group, group_leave = [], enter
		for cx, cz, out in _squares(o, d, enter, leave):
			at = np.searchsorted(unique, _key(cx, cz))
			if at < len(unique) and unique[at] == _key(cx, cz):
				group.append(filed[starts[at]:starts[at + 1]])
			group_leave = out
			if len(group) >= CHUNK:
				best = _nearer(best, self._pick_among(np.unique(np.concatenate(group)), o, d, below))
				group = []
				if best is not None and best.distance <= group_leave:
					return best
		if group:
			best = _nearer(best, self._pick_among(np.unique(np.concatenate(group)), o, d, below))
		return best


def _key(cx, cz):
	return (np.asarray(cx, dtype=np.int64) + (1 << 20)) * (1 << 21) + (np.asarray(cz, dtype=np.int64) + (1 << 20))


def _nearer(a, b):
	if a is None:
		return b
	return a if b is None or a.distance <= b.distance else b


def _squares(o, d, enter, leave):
	"""The squares (seen from above) the ray crosses between distances enter and leave, nearest first:
	(square x, square z, the distance where the ray leaves it)."""
	x, z = o[0] + enter * d[0], o[2] + enter * d[2]
	cx, cz = int(np.floor(x / CELL)), int(np.floor(z / CELL))
	step_x, step_z = (1 if d[0] > 0 else -1), (1 if d[2] > 0 else -1)
	next_x = ((cx + (d[0] > 0)) * CELL - o[0]) / d[0] if abs(d[0]) > 1e-12 else np.inf
	next_z = ((cz + (d[2] > 0)) * CELL - o[2]) / d[2] if abs(d[2]) > 1e-12 else np.inf
	delta_x = CELL / abs(d[0]) if abs(d[0]) > 1e-12 else np.inf
	delta_z = CELL / abs(d[2]) if abs(d[2]) > 1e-12 else np.inf
	for _ in range(100_000):
		out = min(next_x, next_z, leave)
		yield cx, cz, out
		if out >= leave:
			return
		if next_x < next_z:
			cx += step_x
			next_x += delta_x
		else:
			cz += step_z
			next_z += delta_z


def _ray_triangles(o, d, tri):
	"""Möller-Trumbore for many triangles at once: (distance along the ray, whether it hits) per triangle."""
	a, b, c = tri[:, 0], tri[:, 1], tri[:, 2]
	e1, e2 = b - a, c - a
	p = np.cross(d, e2)
	det = np.einsum("ij,ij->i", e1, p)
	ok = np.abs(det) > EPSILON
	inv = np.divide(1.0, det, out=np.zeros_like(det), where=ok)
	s = o - a
	u = np.einsum("ij,ij->i", s, p) * inv
	q = np.cross(s, e1)
	v = (q @ d) * inv
	t = np.einsum("ij,ij->i", e2, q) * inv
	ok &= (u >= -1e-6) & (v >= -1e-6) & (u + v <= 1 + 1e-6) & (t > 1e-6)
	return t, ok


# --- boxes (quest zones) --------------------------------------------------------------------------------------

# The corners of maps.geometry.Box.corners() are numbered (x side) * 4 + (y side) * 2 + (z side), 0 for the low side.
_FACES = (  # each face as two triangles of corner numbers, and its outward normal in the box's own axes
	((0, 1, 3), (0, 3, 2), (-1, 0, 0)), ((4, 6, 7), (4, 7, 5), (1, 0, 0)),
	((0, 4, 5), (0, 5, 1), (0, -1, 0)), ((2, 3, 7), (2, 7, 6), (0, 1, 0)),
	((0, 2, 6), (0, 6, 4), (0, 0, -1)), ((1, 5, 7), (1, 7, 3), (0, 0, 1)),
)
_EDGES = ((0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (1, 3), (4, 6), (5, 7), (0, 4), (1, 5), (2, 6), (3, 7))


def box_faces(box):
	"""The box's six faces as 12 triangles: (36, 3) float32 corners, like Triangles.vertex_array()."""
	corners = box.corners()
	return np.asarray([corners[i] for first, second, _normal in _FACES for triangle in (first, second) for i in triangle], dtype=np.float32)


def box_edges(box):
	"""The box's twelve edges: (24, 3) float32, two points per edge."""
	corners = box.corners()
	return np.asarray([corners[i] for edge in _EDGES for i in edge], dtype=np.float32)


def ray_box(origin, direction, box):
	"""How far along the ray it enters the box (0 if it starts inside), or None if it misses."""
	o = box.local(origin)
	d = G.rotate(G.q_conj(box.rotation), direction)
	near, far = -np.inf, np.inf
	for axis in range(3):
		half = box.size[axis] / 2
		if abs(d[axis]) < 1e-12:
			if abs(o[axis]) > half:
				return None
			continue
		t1, t2 = (-half - o[axis]) / d[axis], (half - o[axis]) / d[axis]
		near, far = max(near, min(t1, t2)), min(far, max(t1, t2))
	if far < max(near, 0.0):
		return None
	return float(max(near, 0.0))


def pick_box(origin, direction, boxes):
	"""The first of boxes ([maps.geometry.Box]) the ray enters, as a Hit (index into boxes), or None."""
	best = None
	for i, box in enumerate(boxes):
		t = ray_box(origin, direction, box)
		if t is not None and (best is None or t < best.distance):
			point = tuple(o + t * d for o, d in zip(origin, direction))
			best = Hit(t, point, i)
	return best
