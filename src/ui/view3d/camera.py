"""The 3D view's camera: where it looks from, the matrices the graphics card draws with, and the ray under a pixel.

Everything is in map space (Unity's axes: x east, y up, z north, left-handed). The camera builds its view from its
own right, up and forward directions, so nothing is mirrored and no axis is flipped on the way to the screen. No Qt.
"""

import math
from dataclasses import dataclass

import numpy as np

TOP_DOWN_HEIGHT = 1500.0  # metres above the target the top-down camera looks from (above every map)


@dataclass
class Camera:
	target: tuple = (0.0, 0.0, 0.0)  # the point it looks at and turns around
	yaw: float = 0.0  # degrees, clockwise seen from above: 0 looks north
	pitch: float = 50.0  # degrees down from level: 90 looks straight down
	distance: float = 80.0  # metres from the target (in the top-down view: how much it shows)
	fov: float = 50.0  # the view's height, in degrees
	top_down: bool = False  # straight down, with no perspective (a map)

	# --- where it looks ---------------------------------------------------------------------------
	def basis(self):
		"""(right, up, forward) unit vectors."""
		pitch = math.radians(90.0 if self.top_down else self.pitch)
		yaw = math.radians(self.yaw)
		cp, sp, cy, sy = math.cos(pitch), math.sin(pitch), math.cos(yaw), math.sin(yaw)
		forward = np.array([cp * sy, -sp, cp * cy])
		right = np.array([cy, 0.0, -sy])
		up = np.cross(forward, right)
		return right, up / np.linalg.norm(up), forward

	def eye(self):
		_right, _up, forward = self.basis()
		back = TOP_DOWN_HEIGHT if self.top_down else self.distance
		return np.asarray(self.target, dtype=np.float64) - forward * back

	def half_height(self):
		"""Half the height of what it shows at the target, in metres."""
		return self.distance * math.tan(math.radians(self.fov) / 2)

	def clip(self):
		"""(near, far) distances it draws between."""
		if self.top_down:
			return 1.0, TOP_DOWN_HEIGHT * 2 + 500.0
		return min(max(self.distance * 0.005, 0.05), 20.0), self.distance + 4000.0

	# --- matrices (row-major numpy 4 x 4) -------------------------------------------------------------
	def view_matrix(self):
		right, up, forward = self.basis()
		eye = self.eye()
		m = np.identity(4)
		m[0, :3], m[1, :3], m[2, :3] = right, up, forward
		m[:3, 3] = -m[:3, :3] @ eye
		return m

	def projection(self, aspect):
		near, far = self.clip()
		m = np.zeros((4, 4))
		if self.top_down:
			half = self.half_height()
			m[0, 0], m[1, 1] = 1.0 / (half * aspect), 1.0 / half
			m[2, 2], m[2, 3], m[3, 3] = 2.0 / (far - near), -(far + near) / (far - near), 1.0
		else:
			f = 1.0 / math.tan(math.radians(self.fov) / 2)
			m[0, 0], m[1, 1] = f / aspect, f
			m[2, 2], m[2, 3], m[3, 2] = (far + near) / (far - near), -2.0 * far * near / (far - near), 1.0
		return m

	def matrix(self, aspect):
		"""Map space to the screen (projection times view)."""
		return self.projection(aspect) @ self.view_matrix()

	# --- pixels -------------------------------------------------------------------------------------------
	def ray(self, px, py, width, height):
		"""(origin, direction) of the ray through the pixel (px, py) of a view width x height pixels."""
		right, up, forward = self.basis()
		nx, ny = 2.0 * px / max(width, 1) - 1.0, 1.0 - 2.0 * py / max(height, 1)
		half = self.half_height()
		aspect = width / max(height, 1)
		if self.top_down:
			origin = self.eye() + right * nx * half * aspect + up * ny * half
			return tuple(origin), tuple(forward)
		f = 1.0 / math.tan(math.radians(self.fov) / 2)
		direction = forward + right * nx * aspect / f + up * ny / f
		return tuple(self.eye()), tuple(direction / np.linalg.norm(direction))

	def project(self, point, width, height):
		"""(x, y) pixel of a point in map space, or None when it is behind the camera."""
		pixels, front = self.project_many([point], width, height)
		return (float(pixels[0, 0]), float(pixels[0, 1])) if front[0] else None

	def project_many(self, points, width, height):
		"""The pixels (n, 2) of many points in map space at once, and which of them are in front of the camera (n,)."""
		p = np.asarray(points, dtype=np.float64).reshape(-1, 3)
		clip = np.c_[p, np.ones(len(p))] @ self.matrix(width / max(height, 1)).T
		front = clip[:, 3] > 1e-9
		w = np.where(front, clip[:, 3], 1.0)
		return np.c_[(clip[:, 0] / w + 1.0) * width / 2.0, (1.0 - clip[:, 1] / w) * height / 2.0], front

	def metres_per_pixel(self, height):
		"""How many metres one pixel is at the target."""
		return 2.0 * self.half_height() / max(height, 1)

	# --- moving -------------------------------------------------------------------------------------------
	def orbit(self, d_yaw, d_pitch):
		self.yaw = (self.yaw + d_yaw) % 360.0
		self.pitch = min(89.5, max(-10.0, self.pitch + d_pitch))

	def pan(self, dx, dy, height):
		"""Move what it looks at by a drag of (dx, dy) pixels, keeping the target's height: the map follows the mouse."""
		right, up, forward = self.basis()
		scale = self.metres_per_pixel(height)
		if self.top_down:
			ahead = up
		else:
			ahead = np.array([forward[0], 0.0, forward[2]])
			length = np.linalg.norm(ahead)
			ahead = ahead / length if length > 1e-9 else np.array([math.sin(math.radians(self.yaw)), 0.0, math.cos(math.radians(self.yaw))])
		move = -right * dx * scale + ahead * dy * scale
		self.target = tuple(float(v) for v in np.asarray(self.target) + np.array([move[0], 0.0, move[2]]))

	def zoom(self, factor, toward=None):
		"""Come closer (factor < 1) or go back, toward a point (the one under the mouse) if given. Going back keeps the
		target's height: moving away from a point above or below it would send the target ever further up or down."""
		factor = min(max(factor, 0.05), 20.0)
		new = min(max(self.distance * factor, 0.5), 5000.0)
		factor = new / self.distance
		if toward is not None:
			target = np.asarray(self.target, dtype=np.float64)
			moved = np.asarray(toward) + (target - np.asarray(toward)) * factor
			if factor > 1.0:
				moved[1] = target[1]
			self.target = tuple(float(v) for v in moved)
		self.distance = new

	def frame(self, low, high, margin=1.3):
		"""Look at the box from low to high (x, y, z) so all of it shows."""
		low, high = np.asarray(low, dtype=np.float64), np.asarray(high, dtype=np.float64)
		self.target = tuple(float(v) for v in (low + high) / 2)
		radius = max(float(np.linalg.norm(high - low)) / 2, 2.0)
		self.distance = min(max(radius * margin / math.tan(math.radians(self.fov) / 2), 3.0), 5000.0)
