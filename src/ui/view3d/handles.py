"""Changing a zone's box with the mouse: the handles the 3D view puts on the selected box, and what dragging one does.

A drag turns the ray under the mouse into a new box: MOVE slides the box across the floor (its height stays), LIFT
raises or lowers it, SIZE pushes one face out or in (the face across from it stays where it is) and TURN turns it
about the up axis. No Qt.
"""

import math
from dataclasses import dataclass

from maps import geometry as G

MOVE, LIFT, SIZE, TURN = "move", "lift", "size", "turn"
SMALLEST = 0.2  # metres: no side gets shorter than this
LIFT_ABOVE = 1.2  # metres above the box's top that the lift handle is
TURN_BEYOND = 1.5  # metres in front of the box's front face that the turn handle is
SNAP_STEP, SNAP_DEGREES = 0.25, 15.0  # what Shift snaps to


@dataclass(frozen=True)
class Handle:
	kind: str
	position: tuple  # (x, y, z) in map space
	axis: int = -1  # SIZE: the box's own axis (0 x, 1 y, 2 z) the face is across
	side: int = 0  # SIZE: +1 or -1, which face along that axis


def handles(box):
	"""The handles of a box: a face handle in the middle of each side face and of the top, one above the top to lift
	it and, for a level box, one in front of it to turn it."""
	hx, hy, hz = (s / 2 for s in box.size)
	at = lambda local: G.add(box.center, G.rotate(box.rotation, local))
	found = [
		Handle(SIZE, at((hx, 0.0, 0.0)), 0, 1), Handle(SIZE, at((-hx, 0.0, 0.0)), 0, -1),
		Handle(SIZE, at((0.0, 0.0, hz)), 2, 1), Handle(SIZE, at((0.0, 0.0, -hz)), 2, -1),
		Handle(SIZE, at((0.0, hy, 0.0)), 1, 1),
		Handle(LIFT, at((0.0, hy + LIFT_ABOVE, 0.0))),
	]
	if G.is_upright(box.rotation):
		found.append(Handle(TURN, at((0.0, -hy, hz + TURN_BEYOND))))
	return found


def _dot(a, b):
	return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _unit(v):
	length = math.sqrt(_dot(v, v))
	return (v[0] / length, v[1] / length, v[2] / length) if length > 1e-12 else (0.0, 0.0, 0.0)


def on_line(origin, direction, point, along):
	"""How far along the line through point (in the unit direction `along`) the ray comes closest to it, or None when
	the ray runs along the line."""
	d = _unit(direction)
	w = G.sub(point, origin)
	b = _dot(along, d)
	denom = 1.0 - b * b
	if denom < 1e-6:
		return None
	return (b * _dot(d, w) - _dot(along, w)) / denom


def on_level(origin, direction, height):
	"""Where the ray crosses the level plane at this height, as (x, y, z), or None when it doesn't (or only behind)."""
	if abs(direction[1]) < 1e-9:
		return None
	t = (height - origin[1]) / direction[1]
	if t <= 0:
		return None
	return (origin[0] + t * direction[0], height, origin[2] + t * direction[2])


def _snap(value, step):
	return round(value / step) * step


class Drag:
	"""One drag of a handle, or of the box itself (MOVE): start(), then box_at() for each mouse move."""

	def __init__(self, box, kind, origin, direction, handle=None, grab=None):
		"""grab: for MOVE, the point on the box the mouse went down on."""
		self.box, self.kind, self.handle = box, kind, handle
		self.start = None
		if kind == MOVE:
			self.height = (grab or box.center)[1]
			self.start = on_level(origin, direction, self.height)
		elif kind == LIFT:
			self.start = on_line(origin, direction, handle.position, (0.0, 1.0, 0.0))
		elif kind == SIZE:
			local = [0.0, 0.0, 0.0]
			local[handle.axis] = float(handle.side)
			self.normal = _unit(G.rotate(box.rotation, tuple(local)))
			self.start = on_line(origin, direction, handle.position, self.normal)
		elif kind == TURN:
			self.height = handle.position[1]
			self.yaw = G.yaw_of(box.rotation)
			point = on_level(origin, direction, self.height)
			self.start = None if point is None else self._angle(point)

	@property
	def ok(self):
		return self.start is not None

	def _angle(self, point):
		return math.degrees(math.atan2(point[0] - self.box.center[0], point[2] - self.box.center[2]))

	def box_at(self, origin, direction, snap=False):
		"""The box after dragging to where the ray is; the box as it was when the ray can't be used."""
		box = self.box
		if not self.ok:
			return box
		if self.kind == MOVE:
			point = on_level(origin, direction, self.height)
			if point is None:
				return box
			dx, dz = point[0] - self.start[0], point[2] - self.start[2]
			x, z = box.center[0] + dx, box.center[2] + dz
			if snap:
				x, z = _snap(x, SNAP_STEP), _snap(z, SNAP_STEP)
			return G.Box((x, box.center[1], z), box.size, box.rotation)
		if self.kind == LIFT:
			s = on_line(origin, direction, self.handle.position, (0.0, 1.0, 0.0))
			if s is None:
				return box
			y = box.center[1] + s - self.start
			if snap:
				bottom = _snap(y - box.size[1] / 2, SNAP_STEP)
				y = bottom + box.size[1] / 2
			return G.Box((box.center[0], y, box.center[2]), box.size, box.rotation)
		if self.kind == SIZE:
			s = on_line(origin, direction, self.handle.position, self.normal)
			if s is None:
				return box
			axis = self.handle.axis
			length = box.size[axis] + s - self.start
			if snap:
				length = _snap(length, SNAP_STEP)
			length = max(length, SMALLEST)
			grow = length - box.size[axis]
			size = list(box.size)
			size[axis] = length
			center = G.add(box.center, tuple(n * grow / 2 for n in self.normal))
			return G.Box(center, tuple(size), box.rotation)
		if self.kind == TURN:
			point = on_level(origin, direction, self.height)
			if point is None:
				return box
			yaw = (self.yaw + self._angle(point) - self.start) % 360.0
			if snap:
				yaw = _snap(yaw, SNAP_DEGREES) % 360.0
			return G.Box(box.center, box.size, G.yaw_rotation(yaw))
		return box
