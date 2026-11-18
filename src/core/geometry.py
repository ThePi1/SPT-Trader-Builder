"""Small 3D helpers for map positions: vectors are (x, y, z) tuples, rotations are (x, y, z, w) quaternions, as Unity
stores them. Unity's axes: x is east, y is up, z is north. No Qt."""

import math

IDENTITY = (0.0, 0.0, 0.0, 1.0)


def add(a, b):
	return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a, b):
	return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def scale(a, s):
	return (a[0] * s[0], a[1] * s[1], a[2] * s[2])


def q_mul(a, b):
	"""The rotation b, then a (a * b)."""
	ax, ay, az, aw = a
	bx, by, bz, bw = b
	return (
		aw * bx + ax * bw + ay * bz - az * by,
		aw * by - ax * bz + ay * bw + az * bx,
		aw * bz + ax * by - ay * bx + az * bw,
		aw * bw - ax * bx - ay * by - az * bz,
	)


def q_conj(q):
	return (-q[0], -q[1], -q[2], q[3])


def q_normalize(q):
	length = math.sqrt(sum(c * c for c in q))
	return IDENTITY if length < 1e-9 else tuple(c / length for c in q)


def rotate(q, v):
	"""The vector v turned by the rotation q."""
	x, y, z, w = q
	vx, vy, vz = v
	cx, cy, cz = y * vz - z * vy, z * vx - x * vz, x * vy - y * vx
	dx, dy, dz = y * cz - z * cy, z * cx - x * cz, x * cy - y * cx
	return (vx + 2 * (w * cx + dx), vy + 2 * (w * cy + dy), vz + 2 * (w * cz + dz))


def yaw_rotation(degrees):
	"""A turn about the up axis, clockwise seen from above (as Unity's y rotation)."""
	half = math.radians(degrees) / 2
	return (0.0, math.sin(half), 0.0, math.cos(half))


def yaw_of(q):
	"""The turn about the up axis (degrees, 0..360) of a rotation: where it points the box's forward (z) axis."""
	fx, _fy, fz = rotate(q, (0.0, 0.0, 1.0))
	return math.degrees(math.atan2(fx, fz)) % 360


def is_upright(q, tolerance=1e-3):
	"""True if the rotation only turns about the up axis (the box stays level)."""
	ux, uy, uz = rotate(q, (0.0, 1.0, 0.0))
	return abs(ux) < tolerance and abs(uz) < tolerance and uy > 0


class Box:
	"""A box turned by a rotation: center, size (full lengths along its own axes) and rotation. A quest zone is one."""

	def __init__(self, center, size, rotation=IDENTITY):
		self.center = tuple(float(c) for c in center)
		self.size = tuple(abs(float(s)) for s in size)
		self.rotation = q_normalize(tuple(float(c) for c in rotation))
		self._inverse = q_conj(self.rotation)

	def local(self, point):
		"""The point in the box's own axes, relative to its center."""
		return rotate(self._inverse, sub(point, self.center))

	def contains(self, point, margin=0.0):
		lx, ly, lz = self.local(point)
		hx, hy, hz = (s / 2 + margin for s in self.size)
		return abs(lx) <= hx and abs(ly) <= hy and abs(lz) <= hz

	def corners(self):
		hx, hy, hz = (s / 2 for s in self.size)
		return [
			add(self.center, rotate(self.rotation, (sx * hx, sy * hy, sz * hz)))
			for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)
		]

	def bounds(self):
		"""(lowest corner, highest corner) of the axis-aligned box around it."""
		points = self.corners()
		return tuple(min(p[i] for p in points) for i in range(3)), tuple(max(p[i] for p in points) for i in range(3))

	def footprint(self):
		"""The four corners of its outline seen from above, as (x, z), for a level box (its bottom face)."""
		hx, hz = self.size[0] / 2, self.size[2] / 2
		return [
			(p[0], p[2]) for p in (
				add(self.center, rotate(self.rotation, (sx * hx, 0.0, sz * hz))) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))
			)
		]

	def overlaps(self, other):
		"""True if the two boxes share any space (separating axis test)."""
		axes = [rotate(self.rotation, a) for a in ((1, 0, 0), (0, 1, 0), (0, 0, 1))]
		axes += [rotate(other.rotation, a) for a in ((1, 0, 0), (0, 1, 0), (0, 0, 1))]
		for a in list(axes[:3]):
			for b in list(axes[3:6]):
				cross = (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
				if sum(c * c for c in cross) > 1e-9:
					axes.append(cross)
		mine, theirs = self.corners(), other.corners()
		for axis in axes:
			p1 = [sum(p[i] * axis[i] for i in range(3)) for p in mine]
			p2 = [sum(p[i] * axis[i] for i in range(3)) for p in theirs]
			if max(p1) < min(p2) - 1e-6 or max(p2) < min(p1) - 1e-6:
				return False
		return True

	def distance_to(self, point):
		"""How far a point is from the box (0 inside)."""
		lx, ly, lz = self.local(point)
		hx, hy, hz = (s / 2 for s in self.size)
		dx, dy, dz = max(abs(lx) - hx, 0.0), max(abs(ly) - hy, 0.0), max(abs(lz) - hz, 0.0)
		return math.sqrt(dx * dx + dy * dy + dz * dz)


def point_in_polygon(x, z, polygon):
	"""True if (x, z) is inside the polygon [(x, z), ...] (its edge counts as inside)."""
	inside = False
	n = len(polygon)
	for i in range(n):
		x1, z1 = polygon[i]
		x2, z2 = polygon[(i + 1) % n]
		if (z1 > z) != (z2 > z):
			cross_x = x1 + (z - z1) * (x2 - x1) / (z2 - z1)
			if x <= cross_x:
				inside = not inside
	return inside
