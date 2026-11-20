"""The walls, floors, stairs and roofs a player bumps into, from the game's own colliders, for the 3D view.

The game stops a player with the colliders on a few layers: the "player collision test" mask of its
LayersMaskController is LowPolyCollider, DoorLowPolyCollider, Terrain and Player. The import reads every enabled,
solid mesh collider and box collider of a map's scenes on the first three (a mesh collider's shape is a Mesh in the
level's shared assets, its corners in the .resS file beside it; see maps.unity.read_mesh). Ground made with Unity's
terrain isn't read: the floor map (the navmesh) covers the ground players walk on.

A map's walls are kept as each distinct mesh once plus where each copy of it goes (a 3 x 4 matrix), in
``<location>.walls.npz`` beside the map's other files: Customs is about 1 900 meshes placed 47 000 times (box colliders included), 2.3 million
triangles once placed. ``load`` places them. Uses numpy. No Qt.
"""

import mmap
from pathlib import Path

import numpy as np

from maps import geometry as G
from maps import unity as U

FORMAT = 1
WALLS_SUFFIX = ".walls.npz"
WALL_LAYERS = ("LowPolyCollider", "DoorLowPolyCollider", "Terrain")  # (LayersMaskController.PlayerCollisionTestMask, less Player)
BOX = ("box", 0)  # the key of the unit cube every solid box collider is a copy of

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

	def get(self, sf, pointer):
		"""The key of the mesh, read if it wasn't yet; None if it can't be read."""
		key = self.key(sf, pointer)
		if key in self.shapes:
			return key
		if key in self.problems:
			return None
		target = sf if pointer[0] == 0 else self._file(key[0])
		try:
			if target is None or key[1] not in target.objects or target.class_id(key[1]) != U.MESH:
				raise U.FormatError("not a mesh")
			self.shapes[key] = U.mesh_shape(U.read_mesh(target, key[1]), self._resource)
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
	"""The walls of one scene file: [(mesh key, 3 x 4 matrix)], for its enabled solid mesh and box colliders whose
	object is active and on one of `layers`."""
	transforms = U.TransformCache(sf)
	found = []
	for class_id in (U.MESH_COLLIDER, U.BOX_COLLIDER):
		for path_id in sf.of_class(class_id):
			try:
				collider = U.read_mesh_collider(sf, path_id) if class_id == U.MESH_COLLIDER else U.read_box_collider(sf, path_id)
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
				else:
					found.append((BOX, _matrix(rotation, position, scale, collider.size, collider.center)))
			except (U.FormatError, KeyError, IndexError, StopIteration, ValueError):
				continue
	return found


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
	np.savez_compressed(
		path, format=np.int32(FORMAT),
		corners=np.concatenate(corners).astype(np.float32) if corners else np.zeros((0, 3), np.float32),
		triangles=np.concatenate(triangles).astype(np.int32) if triangles else np.zeros((0, 3), np.int32),
		ranges=np.asarray(ranges, dtype=np.int64).reshape(-1, 2),
		matrices=np.asarray([m for _k, m in placed], dtype=np.float32).reshape(-1, 3, 4),
		mesh_of=np.asarray([order[k] for k, _m in placed], dtype=np.int32),
	)
	return sum(ranges[order[k]][1] for k, _m in placed)


def path_of(mapdata):
	return mapdata.path.with_name(f"{mapdata.location}{WALLS_SUFFIX}") if mapdata.path else None


def load(mapdata):
	"""The map's walls placed, as triangle corners (n, 3, 3) float32, each going round so that a floor's normal
	(cross(b - a, c - a)) points up; None when they haven't been imported."""
	path = path_of(mapdata)
	if path is None or not path.is_file():
		return None
	with np.load(path) as data:
		if int(data["format"]) != FORMAT:
			return None
		corners, triangles, ranges = data["corners"], data["triangles"], data["ranges"]
		matrices, mesh_of = data["matrices"], data["mesh_of"]
	parts = []
	for mesh in np.unique(mesh_of):
		start, count = ranges[mesh]
		tri = corners[triangles[start:start + count]]  # (count, 3, 3)
		m = matrices[mesh_of == mesh]  # (copies, 3, 4)
		placed = np.einsum("kij,tcj->ktci", m[:, :, :3], tri) + m[:, None, None, :, 3]
		mirrored = np.linalg.det(m[:, :, :3]) < 0
		if mirrored.any():  # (a mirrored copy's triangles go round the other way: put them back, so floors face up)
			placed[mirrored] = placed[mirrored][:, :, [0, 2, 1]]
		parts.append(placed.reshape(-1, 3, 3))
	return np.concatenate(parts).astype(np.float32) if parts else np.zeros((0, 3, 3), np.float32)
