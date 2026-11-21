"""The walls, floors, stairs and roofs a player bumps into, from the game's own colliders, for the 3D view.

The game stops a player with the colliders on a few layers: the "player collision test" mask of its
LayersMaskController is LowPolyCollider, DoorLowPolyCollider, Terrain and Player. The import reads every enabled,
solid mesh, box and terrain collider of a map's scenes on the first three (a mesh collider's shape is a Mesh in the
level's shared assets, its corners in the .resS file beside it; see maps.unity.read_mesh). A terrain's ground is its
heightmap (maps.unity.read_heightmap), drawn with as few triangles as keep within 10 cm of it (terrain_shape): it is
the ground outside where bots walk too, such as all round Interchange's mall. The AI scenes' copies of the terrains
are on another layer (Grass), so they are left out.

A map's walls are kept as each distinct mesh once plus where each copy of it goes (a 3 x 4 matrix), in
``<location>.walls.npz`` beside the map's other files: Customs is about 1 900 meshes placed 47 000 times (box colliders included), and two
terrains: 2.8 million triangles once placed. ``load`` places them. Uses numpy. No Qt.
"""

import mmap
from pathlib import Path

import numpy as np

from core import jsonio
from maps import geometry as G
from maps import unity as U

FORMAT = 1
WALLS_SUFFIX = ".walls.npz"
WALL_LAYERS = ("LowPolyCollider", "DoorLowPolyCollider", "Terrain")  # (LayersMaskController.PlayerCollisionTestMask, less Player)
BOX = ("box", 0)  # the key of the unit cube every solid box collider is a copy of
READ_SHARE = 0.2  # of load's time: reading the file (the rest is placing the copies)

_CUBE = np.array([[x, y, z] for x in (-0.5, 0.5) for y in (-0.5, 0.5) for z in (-0.5, 0.5)], dtype=np.float32)
_CUBE_TRIANGLES = np.array([  # (corners numbered x * 4 + y * 2 + z, as maps.triangles numbers a box's)
	(0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5), (0, 4, 5), (0, 5, 1), (2, 3, 7), (2, 7, 6), (0, 2, 6), (0, 6, 4), (1, 5, 7), (1, 7, 3),
], dtype=np.int32)


def wall_layers(globalgamemanagers):
	"""The layer numbers of WALL_LAYERS."""
	names = U.read_layer_names(globalgamemanagers)
	return {i for i, name in enumerate(names) if name in WALL_LAYERS}


class Meshes:
	"""The meshes the walls use, read once each from the files they are in (other scenes' shared assets, and the
	.resS files beside them)."""

	def __init__(self, data_dir):
		self.data_dir = Path(data_dir)
		self.shapes = {BOX: (_CUBE, _CUBE_TRIANGLES)}  # {key: (corners, triangles)}
		self.problems = {}  # {key: why it couldn't be read}
		self._files = {}
		self._resources = {}

	def _file(self, name):
		if name not in self._files:
			path = self.data_dir / name
			try:
				self._files[name] = U.SerializedFile(path) if path.is_file() else None
			except U.FormatError:
				self._files[name] = None
		return self._files[name]

	def _resource(self, name, offset, size):
		if name not in self._resources:
			path = self.data_dir / name
			if not path.is_file():
				raise U.FormatError(f"no {name}")
			handle = open(path, "rb")
			self._resources[name] = (handle, mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ))
		return self._resources[name][1][offset:offset + size]

	def key(self, sf, pointer):
		"""(file name, path id) of the mesh a pointer in sf points at."""
		file_index, path_id = pointer
		return (sf.path.name if file_index == 0 else sf.external_name(file_index), path_id)

	def get(self, sf, pointer, class_id=U.MESH):
		"""The key of the mesh (or with class_id TERRAIN_DATA, of a terrain's ground: terrain_shape), read if it wasn't
		yet; None if it can't be read."""
		key = self.key(sf, pointer)
		if key in self.shapes:
			return key
		if key in self.problems:
			return None
		target = sf if pointer[0] == 0 else self._file(key[0])
		try:
			if target is None or key[1] not in target.objects or target.class_id(key[1]) != class_id:
				raise U.FormatError(f"not a {'mesh' if class_id == U.MESH else 'terrain'}")
			if class_id == U.MESH:
				self.shapes[key] = U.mesh_shape(U.read_mesh(target, key[1]), self._resource)
			else:
				self.shapes[key] = terrain_shape(U.read_heightmap(target, key[1]))
		except (U.FormatError, ValueError, IndexError, KeyError) as e:
			self.problems[key] = str(e)
			return None
		return key

	def close(self):
		for sf in self._files.values():
			if sf is not None:
				sf.close()
		for handle, data in self._resources.values():
			data.close()
			handle.close()
		self._files, self._resources = {}, {}


def _matrix(rotation, position, scale, size=(1.0, 1.0, 1.0), center=(0.0, 0.0, 0.0)):
	"""The 3 x 4 matrix that puts a mesh's corner c at position + rotation(scale * (center + size * c))."""
	m = np.zeros((3, 4), dtype=np.float64)
	for axis in range(3):
		unit = [0.0, 0.0, 0.0]
		unit[axis] = 1.0
		m[:, axis] = np.asarray(G.rotate(rotation, tuple(unit))) * scale[axis] * size[axis]
	m[:, 3] = G.add(position, G.rotate(rotation, G.scale(center, scale)))
	return m


def scene_walls(sf, meshes, layers):
	"""The walls of one scene file: [(mesh key, 3 x 4 matrix)], for its enabled solid mesh, box and terrain colliders
	whose object is active and on one of `layers`."""
	transforms = U.TransformCache(sf)
	readers = {U.MESH_COLLIDER: U.read_mesh_collider, U.BOX_COLLIDER: U.read_box_collider, U.TERRAIN_COLLIDER: U.read_terrain_collider}
	found = []
	for class_id, read in readers.items():
		for path_id in sf.of_class(class_id):
			try:
				collider = read(sf, path_id)
				if collider.is_trigger or not collider.enabled or collider.game_object[0] != 0:
					continue
				game_object = U.read_game_object(sf, collider.game_object[1])
				if game_object.layer not in layers or not game_object.active:
					continue
				transform = next(
					c for f, c in game_object.components if f == 0 and c in sf.objects and sf.class_id(c) in (U.TRANSFORM, U.RECT_TRANSFORM)
				)
				rotation, position, scale = transforms.world(transform)
				if class_id == U.MESH_COLLIDER:
					key = meshes.get(sf, collider.mesh)
					if key is not None:
						found.append((key, _matrix(rotation, position, scale)))
				elif class_id == U.TERRAIN_COLLIDER:  # (a terrain is never turned or scaled: only its position counts)
					key = meshes.get(sf, collider.terrain_data, U.TERRAIN_DATA)
					if key is not None:
						found.append((key, _matrix(G.IDENTITY, position, (1.0, 1.0, 1.0))))
				else:
					found.append((BOX, _matrix(rotation, position, scale, collider.size, collider.center)))
			except (U.FormatError, KeyError, IndexError, StopIteration, ValueError):
				continue
	return found


TERRAIN_TOLERANCE = 0.1  # metres: how far the ground drawn may be from the terrain's own heights
_LARGEST_BLOCK = 64  # heights: the largest square of the terrain drawn as two triangles


def terrain_shape(heightmap, tolerance=TERRAIN_TOLERANCE):
	"""A terrain's ground as (corners, triangles), in metres from the terrain's position. A full-detail grid is 2 million
	triangles a terrain (Interchange has four), so it is cut into squares of up to 64 x 64 heights, each split in four
	until its two triangles are within `tolerance` of every height inside it (flat ground stays in big squares, slopes
	and edges get every height); holes are left open. A square's edges may not meet its smaller neighbour's corners
	exactly, but are within the tolerance of them."""
	n = heightmap.resolution - 1
	heights = np.frombuffer(heightmap.heights, dtype="<i2").reshape(n + 1, n + 1).astype(np.float32)
	y = heights * np.float32(heightmap.scale[1] / U.HEIGHT_TOP)
	hole = None if heightmap.holes is None else np.frombuffer(heightmap.holes, dtype=np.uint8).reshape(n, n) == 0
	size = min(_LARGEST_BLOCK, n)
	if n & (n - 1) or n % size:
		raise U.FormatError(f"a terrain {n + 1} heights wide")
	quads = []  # [(z, x, size)] in heights
	split = None
	while size >= 1:
		blocks = n // size
		exists = np.ones((blocks, blocks), bool) if split is None else np.kron(split, np.ones((2, 2), bool))
		error = _block_errors(y, size)
		if hole is not None:
			error[hole.reshape(blocks, size, blocks, size).any(axis=(1, 3))] = np.inf
		leaf = exists & (error <= tolerance) if size > 1 else exists & (error < np.inf)
		z, x = np.nonzero(leaf)
		quads.append(np.stack([z * size, x * size, np.full_like(z, size)], axis=1))
		split = exists & ~leaf
		size //= 2
	quads = np.concatenate(quads)
	z0, x0, s = quads[:, 0], quads[:, 1], quads[:, 2]
	ids = np.stack([z0 * (n + 1) + x0, (z0 + s) * (n + 1) + x0, (z0 + s) * (n + 1) + x0 + s, z0 * (n + 1) + x0 + s], axis=1)
	used, index = np.unique(ids, return_inverse=True)
	index = index.reshape(-1, 4)
	zs, xs = np.divmod(used, n + 1)
	corners = np.stack([xs * heightmap.scale[0], y.reshape(-1)[used], zs * heightmap.scale[2]], axis=1).astype(np.float32)
	a, b, c, d = index.T  # (each square's corners going round from its own corner: +z, then +x and +z, then +x)
	triangles = np.concatenate([np.stack([a, b, c], axis=1), np.stack([a, c, d], axis=1)]).astype(np.int32)
	return corners, triangles


def _block_errors(y, size):
	"""For each size x size square of heights y: the furthest any height inside it is from its two triangles (split
	from its corner to the opposite one, as terrain_shape draws it)."""
	from numpy.lib.stride_tricks import as_strided

	blocks = (y.shape[0] - 1) // size
	step = np.arange(size + 1, dtype=np.float32) / size
	v, u = step[:, None], step[None, :]  # (along z, along x)
	corners = [y[dz::size, dx::size][:blocks, :blocks, None, None] for dz, dx in ((0, 0), (size, 0), (size, size), (0, size))]
	c00, c10, c11, c01 = corners
	toward_z = c00 + v * (c10 - c00) + u * (c11 - c10)  # (the triangle on the +z side of the diagonal)
	toward_x = c00 + u * (c01 - c00) + v * (c11 - c01)
	inside = as_strided(y, shape=(blocks, blocks, size + 1, size + 1), strides=(y.strides[0] * size, y.strides[1] * size, *y.strides), writeable=False)
	return np.abs(np.where(v >= u, toward_z, toward_x) - inside).max(axis=(2, 3))


def write(path, placed, meshes):
	"""Write a map's walls: placed is [(mesh key, matrix)] (see scene_walls)."""
	order = {}
	for key, _m in placed:
		order.setdefault(key, len(order))
	corners, triangles, ranges = [], [], []
	start_corner = start_triangle = 0
	for key in order:
		c, t = meshes.shapes[key]
		corners.append(c)
		triangles.append(t + start_corner)
		ranges.append((start_triangle, len(t)))
		start_corner += len(c)
		start_triangle += len(t)
	with jsonio.replacing(path) as f:  # (swapped in when written: the tab may read it meanwhile)
		np.savez_compressed(
			f, format=np.int32(FORMAT),
			corners=np.concatenate(corners).astype(np.float32) if corners else np.zeros((0, 3), np.float32),
			triangles=np.concatenate(triangles).astype(np.int32) if triangles else np.zeros((0, 3), np.int32),
			ranges=np.asarray(ranges, dtype=np.int64).reshape(-1, 2),
			matrices=np.asarray([m for _k, m in placed], dtype=np.float32).reshape(-1, 3, 4),
			mesh_of=np.asarray([order[k] for k, _m in placed], dtype=np.int32),
		)
	return sum(ranges[order[k]][1] for k, _m in placed)


def path_of(mapdata):
	return mapdata.path.with_name(f"{mapdata.location}{WALLS_SUFFIX}") if mapdata.path else None


def load(mapdata, progress=None):
	"""The map's walls placed, as triangle corners (n, 3, 3) float32, each going round so that a floor's normal
	(cross(b - a, c - a)) points up; None when they haven't been imported. progress(fraction) is told how far along it
	is (by the triangles placed)."""
	path = path_of(mapdata)
	if path is None or not path.is_file():
		return None
	with np.load(path) as data:
		if int(data["format"]) != FORMAT:
			return None
		corners, triangles, ranges = data["corners"], data["triangles"], data["ranges"]
		matrices, mesh_of = data["matrices"], data["mesh_of"]
	order = np.argsort(mesh_of, kind="stable")  # (each mesh's copies together, in the file's order)
	meshes, starts, copies = np.unique(mesh_of[order], return_index=True, return_counts=True)
	work = ranges[meshes, 1] * copies
	done = np.cumsum(work) / max(1, int(work.sum()))
	if progress:
		progress(READ_SHARE)
	parts = []
	for i, mesh in enumerate(meshes):
		start, count = ranges[mesh]
		tri = corners[triangles[start:start + count]]  # (count, 3, 3)
		m = matrices[order[starts[i]:starts[i] + copies[i]]]  # (copies, 3, 4)
		placed = np.einsum("kij,tcj->ktci", m[:, :, :3], tri) + m[:, None, None, :, 3]
		mirrored = np.linalg.det(m[:, :, :3]) < 0
		if mirrored.any():  # (a mirrored copy's triangles go round the other way: put them back, so floors face up)
			placed[mirrored] = placed[mirrored][:, :, [0, 2, 1]]
		parts.append(placed.reshape(-1, 3, 3))
		if progress:
			progress(READ_SHARE + (1 - READ_SHARE) * float(done[i]))
	return np.concatenate(parts).astype(np.float32, copy=False) if parts else np.zeros((0, 3, 3), np.float32)
