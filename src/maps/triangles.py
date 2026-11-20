"""Triangles in map space (Unity's axes: x east, y up, z north), for drawing a map in 3D and finding what a click hits.

The 3D view draws the floor (the navmesh's polygons, cut into triangles) and, when they have been imported, the walls
(see maps.walls) as Triangles, and asks them which triangle a ray from the camera hits first. Uses numpy. No Qt.
"""

from dataclasses import dataclass

import numpy as np

from maps import geometry as G

EPSILON = 1e-7


@dataclass(frozen=True)
class Hit:
	"""Where a ray hit: how far along it, the point (x, y, z), and the triangle's index (or the box's, see ray_box)."""

	distance: float
	point: tuple
	index: int


class Triangles:
	"""corners: an array of shape (n, 3, 3), the three corners (x, y, z) of each triangle."""

	def __init__(self, corners):
		self.corners = np.ascontiguousarray(np.asarray(corners, dtype=np.float32).reshape(-1, 3, 3))
		self.low = self.corners.min(axis=1)
		self.high = self.corners.max(axis=1)

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
		return tuple(float(v) for v in self.low.min(axis=0)), tuple(float(v) for v in self.high.max(axis=0))

	def normals(self):
		"""Each triangle's unit normal (n, 3), pointing up for a floor seen from above (a zero vector for a sliver)."""
		a, b, c = self.corners[:, 0], self.corners[:, 1], self.corners[:, 2]
		n = np.cross(b - a, c - a)  # (the navmesh's polygons go round so that this points up for a floor)
		length = np.linalg.norm(n, axis=1, keepdims=True)
		return np.divide(n, length, out=np.zeros_like(n), where=length > 1e-12)

	def vertex_array(self):
		"""What the graphics card draws: per corner its position and its triangle's normal, (n * 3, 6) float32."""
		normals = np.repeat(self.normals(), 3, axis=0)
		return np.ascontiguousarray(np.hstack([self.corners.reshape(-1, 3), normals]).astype(np.float32))

	def pick(self, origin, direction, below=None):
		"""The first triangle the ray from origin along direction hits (a Hit), or None. below (a height) leaves out
		whatever is above it, as the view does when it cuts the map at a height."""
		if not len(self):
			return None
		o = np.asarray(origin, dtype=np.float64)
		d = np.asarray(direction, dtype=np.float64)
		d = np.where(np.abs(d) < 1e-12, 1e-12, d)
		with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
			t1 = (self.low - o) / d
			t2 = (self.high - o) / d
		near = np.minimum(t1, t2).max(axis=1)
		far = np.maximum(t1, t2).min(axis=1)
		candidates = far >= np.maximum(near, 0.0)
		if below is not None:
			candidates &= self.low[:, 1] <= below
		index = np.nonzero(candidates)[0]
		if not len(index):
			return None
		tri = self.corners[index].astype(np.float64)
		t, ok = _ray_triangles(o, np.asarray(direction, dtype=np.float64), tri)
		if below is not None:
			ok &= o[1] + t * direction[1] <= below + 1e-4
		if not ok.any():
			return None
		best = np.argmin(np.where(ok, t, np.inf))
		distance = float(t[best])
		point = tuple(float(v) for v in o + distance * np.asarray(direction, dtype=np.float64))
		return Hit(distance, point, int(index[best]))


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
	"""The box's six faces as 12 triangles: (36, 6) float32 of position and normal, like Triangles.vertex_array()."""
	corners = box.corners()
	rows = []
	for first, second, normal in _FACES:
		n = G.rotate(box.rotation, normal)
		for triangle in (first, second):
			rows += [(*corners[i], *n) for i in triangle]
	return np.asarray(rows, dtype=np.float32)


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
