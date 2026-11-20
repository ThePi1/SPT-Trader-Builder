"""The walls: reading mesh colliders and meshes with the 2022 layout (on a serialized file built here), placing them,
the walls file, the floors on their tops, and the navmesh's height inside a polygon that isn't flat."""

import struct

import numpy as np
import pytest

from maps import geometry as G
from maps import unity as U
from maps import walls as W
from maps.mapdata import Floors
from maps.navmesh import NavMesh
from maps.triangles import Triangles
from tests.test_map_geometry import _serialized, _string

LOW_POLY = 18


def _pptr(path_id, file_index=0):
	return struct.pack("<iq", file_index, path_id)


def _game_object(components, layer, name, active=True):
	return struct.pack("<i", len(components)) + b"".join(_pptr(c) for c in components) + struct.pack("<I", layer) + _string(name) + struct.pack("<HB", 0, 1 if active else 0)


def _transform(game_object, position=(0, 0, 0), rotation=(0, 0, 0, 1), scale=(1, 1, 1)):
	return _pptr(game_object) + struct.pack("<4f", *rotation) + struct.pack("<3f", *position) + struct.pack("<3f", *scale) + struct.pack("<i", 0) + _pptr(0)


def _collider_start(game_object, trigger=False, enabled=True):
	return _pptr(game_object) + _pptr(0) + struct.pack("<IIi", 0, 0, 0) + bytes([1 if trigger else 0, 0, 0, 0, 1 if enabled else 0, 0, 0, 0])


def _mesh_collider(game_object, mesh, trigger=False):
	return _collider_start(game_object, trigger) + bytes([0, 0, 0, 0]) + struct.pack("<i", 30) + _pptr(mesh)


def _box_collider(game_object, size, center=(0, 0, 0)):
	return _collider_start(game_object) + struct.pack("<3f", *size) + struct.pack("<3f", *center)


def _mesh(name, corners, indexes, resource=None):
	"""A Mesh with the 2022 layout: corners (float x, y, z, then a float normal: 24 bytes a corner) kept in the mesh, or
	in a .resS file when resource is (file name, offset)."""
	index_bytes = struct.pack(f"<{len(indexes)}H", *indexes)
	vertex_bytes = b"".join(struct.pack("<6f", *c, 0, 1, 0) for c in corners)
	blob = _string(name) + struct.pack("<i", 1) + struct.pack("<IIiIII", 0, len(indexes), 0, 0, 0, len(corners)) + bytes(24)
	blob += struct.pack("<9i", 0, 0, 0, 0, 0, 0, 0, 0, 0)  # (blend shapes: 4 lists, bind poses, bone hashes, root bone, bone boxes, weights)
	blob += bytes([0, 1, 1, 1]) + struct.pack("<i", 0)  # (not compressed, readable; 16-bit indexes)
	blob += struct.pack("<i", len(index_bytes)) + index_bytes + bytes((-len(index_bytes)) % 4)
	blob += struct.pack("<I", len(corners)) + struct.pack("<i", 2) + bytes([0, 0, 0, 3]) + bytes([0, 12, 0, 3])
	inline = b"" if resource else vertex_bytes
	blob += struct.pack("<i", len(inline)) + inline + bytes((-len(inline)) % 4)
	floats, ints = struct.pack("<Iffi", 0, 0, 0, 0) + bytes(4), struct.pack("<Ii", 0, 0) + bytes(4)
	blob += floats * 4 + ints * 3 + floats + ints * 2 + struct.pack("<I", 0)  # (the empty compressed mesh, and its UV info)
	blob += bytes(24) + struct.pack("<ii", 0, 30) + struct.pack("<ii", 0, 0) + bytes(8)  # (box, usage, cooking, baked meshes, metrics)
	offset = resource[1] if resource else 0
	blob += struct.pack("<QI", offset, len(vertex_bytes) if resource else 0) + _string(resource[0] if resource else "")
	return blob, vertex_bytes


SQUARE = [(0, 0, 0), (0, 0, 2), (2, 0, 2), (2, 0, 0)]  # (a 2 x 2 m floor, going round so that it faces up)
SQUARE_TRIANGLES = [0, 1, 2, 0, 2, 3]


@pytest.fixture
def level(tmp_path):
	"""A scene with a floor mesh (in the scene, at 10, 1, 0, turned a quarter), the same mesh kept in a .resS file (at
	0, 5, 0, mirrored), a solid box, a trigger and a mesh on another layer."""
	inline, _ = _mesh("floor", SQUARE, SQUARE_TRIANGLES)
	stored, vertex_bytes = _mesh("floor stored", SQUARE, SQUARE_TRIANGLES, resource=("level1.resS", 16))
	(tmp_path / "level1.resS").write_bytes(bytes(16) + vertex_bytes)
	objects = [
		(1, U.GAME_OBJECT, _game_object([2, 3], LOW_POLY, "floor")),
		(2, U.TRANSFORM, _transform(1, (10, 1, 0), G.yaw_rotation(90))),
		(3, U.MESH_COLLIDER, _mesh_collider(1, 20)),
		(4, U.GAME_OBJECT, _game_object([5, 6], LOW_POLY, "mirrored")),
		(5, U.TRANSFORM, _transform(4, (0, 5, 0), scale=(-1, 1, 1))),
		(6, U.MESH_COLLIDER, _mesh_collider(4, 21)),
		(7, U.GAME_OBJECT, _game_object([8, 9], LOW_POLY, "box")),
		(8, U.TRANSFORM, _transform(7, (0, 0, 20))),
		(9, U.BOX_COLLIDER, _box_collider(7, (4, 1, 2), (0, 0.5, 0))),
		(10, U.GAME_OBJECT, _game_object([11, 12], LOW_POLY, "trigger")),
		(11, U.TRANSFORM, _transform(10)),
		(12, U.MESH_COLLIDER, _mesh_collider(10, 20, trigger=True)),
		(13, U.GAME_OBJECT, _game_object([14, 15], 12, "bullets only")),
		(14, U.TRANSFORM, _transform(13)),
		(15, U.MESH_COLLIDER, _mesh_collider(13, 20)),
		(20, U.MESH, inline),
		(21, U.MESH, stored),
	]
	path = tmp_path / "level1"
	path.write_bytes(_serialized(objects))
	return path


def test_mesh_colliders_and_meshes_are_read_with_the_2022_layout(level):
	with U.SerializedFile(level) as sf:
		collider = U.read_mesh_collider(sf, 3)
		assert collider.game_object == (0, 1) and collider.mesh == (0, 20) and collider.enabled and not collider.is_trigger
		mesh = U.read_mesh(sf, 20)
		assert mesh.name == "floor" and mesh.vertex_count == 4 and mesh.submeshes == [(0, 6, 0, 0)]
		corners, triangles = U.mesh_shape(mesh, lambda *a: pytest.fail("the corners are in the mesh"))
		assert corners.tolist() == [list(map(float, c)) for c in SQUARE] and triangles.tolist() == [[0, 1, 2], [0, 2, 3]]
		stored = U.read_mesh(sf, 21)
		assert stored.vertex_bytes == b"" and stored.stream[2] == "level1.resS" and stored.stream[0] == 16


def test_the_walls_of_a_scene_are_its_solid_colliders_on_the_wall_layers_placed(level):
	meshes = W.Meshes(level.parent)
	try:
		with U.SerializedFile(level) as sf:
			placed = W.scene_walls(sf, meshes, {LOW_POLY})
		assert [key for key, _m in placed] == [(level.name, 20), (level.name, 21), W.BOX]  # (no trigger, nothing on another layer)
		path = level.parent / "map.walls.npz"
		assert W.write(path, placed, meshes) == 2 + 2 + 12
	finally:
		meshes.close()

	class Map:
		location = "map"

	m = Map()
	m.path = level.parent / "map.json"
	corners = W.load(m)
	tri = Triangles(corners)
	assert tri.floors_at(11, -1) == [1.0]  # (the turned floor: x 10 to 12, z -2 to 0)
	assert tri.floors_at(11, 1) == [] and tri.floors_at(10.5, -1.5) == [1.0]
	assert tri.floors_at(-1, 1) == [5.0]  # (the mirrored one, x -2 to 0, still facing up)
	assert tri.floors_at(0, 20) == [1.0]  # (the box's top; its bottom faces down)
	box = corners[-12:].reshape(-1, 3)
	assert box.min(axis=0).tolist() == [-2, 0, 19] and box.max(axis=0).tolist() == [2, 1, 21]


def test_floors_on_the_walls_tops_leave_out_ceilings_and_steep_slopes():
	floor = [(0, 0, 0), (0, 0, 4), (4, 0, 4), (0, 0, 0), (4, 0, 4), (4, 0, 0)]
	ceiling = [(0, 3, 0), (4, 3, 4), (0, 3, 4)]  # (facing down)
	steep = [(0, 1, 0), (0, 8, 4), (4, 8, 4)]  # (60 degrees)
	tri = Triangles(np.array(floor + ceiling + steep, dtype=np.float32).reshape(-1, 3, 3))
	assert tri.floors_at(1, 2) == [0.0]
	assert Triangles(np.array(floor * 30000, dtype=np.float32).reshape(-1, 3, 3), cells_from=1).floors_at(1, 2) == [0.0]


def test_floors_at_many_points_at_once_are_those_found_one_at_a_time():
	"""Looked up together (square by square when there are many triangles, with a wide one over many squares), the
	floors are the same as one point at a time, and the same whichever way they are looked up."""
	rng = np.random.default_rng(3)
	low = rng.uniform(0, 60, (400, 1, 3)) * [1, 0.1, 1]
	slabs = (low + rng.uniform(-3, 3, (400, 3, 3)) * [1, 0.2, 1]).astype(np.float32)  # (small tilted triangles, some facing down)
	wide = np.array([[(-100, -1, -100), (-100, -1, 400), (400, -1, -100)]], dtype=np.float32)  # (over hundreds of 8 m squares)
	corners = np.concatenate([slabs, wide])
	points = rng.uniform(-5, 65, (300, 2))
	one_by_one = [Triangles(corners).floors_at(x, z) for x, z in points]
	assert sum(map(len, one_by_one)) > 300  # (the wide one is under every point, the others under some)
	for tri in (Triangles(corners), Triangles(corners, cells_from=1)):
		assert tri.floors_at_points(points) == one_by_one
		assert [tri.floors_at(x, z) for x, z in points] == one_by_one


def test_the_floors_join_the_floor_map_and_the_walls_tops():
	navmesh = NavMesh([(0, 0.1, 0), (10, 0.1, 0), (10, 0.1, 10), (0, 0.1, 10)], [((0, 3, 2, 1), 0)])
	slabs = []
	for y in (0.0, 3.0, -99.5):  # (the ground floor, a storey bots never walk, and a plane far under the map)
		slabs += [(0, y, 0), (0, y, 10), (10, y, 10), (0, y, 0), (10, y, 10), (10, y, 0)]
	floors = Floors(navmesh, Triangles(np.array(slabs, dtype=np.float32).reshape(-1, 3, 3)))
	assert floors.floors_at(5, 5) == pytest.approx([0.1, 3.0])  # (the wall's top at 0 is the floor map's 0.1)
	assert floors.floor_near(5, 2.5, 5) == pytest.approx(3.0) and Floors(navmesh).floors_at(5, 5) == pytest.approx([0.1])
	points = [(5, 5), (0.5, 9.5), (20, 20)]
	assert floors.floors_at_points(points) == [floors.floors_at(x, z) for x, z in points]
	assert floors.floors_at_points(points)[2] == []


def test_the_navmesh_height_comes_from_the_part_of_the_polygon_under_the_point():
	"""Its first three corners make a sliver whose plane is metres off at the far corner (as on Factory at 0, 0)."""
	corners = [(-10.4, 0.35, 0.0), (-10.9, 0.4, 1.1), (-10.7, 0.05, 1.3), (-4.5, 0.05, 2.6), (-4.2, 0.05, 2.6), (0.0, 0.05, 0.0)]
	navmesh = NavMesh(corners, [((0, 1, 2, 3, 4, 5), 0)])
	assert navmesh.floors_at(-0.5, 0.2) == pytest.approx([0.05], abs=0.02)


def test_the_layer_names_are_read(tmp_path):
	names = ["Default", "TransparentFX"] + [""] * 16 + ["LowPolyCollider"] + [""] * 13
	blob = struct.pack("<i", 1) + _string("tag") + struct.pack("<i", 32) + b"".join(_string(n) for n in names)
	path = tmp_path / "globalgamemanagers"
	path.write_bytes(_serialized([(1, U.TAG_MANAGER, blob)]))
	with U.SerializedFile(path) as sf:
		assert U.read_layer_names(sf)[18] == "LowPolyCollider"
		assert W.wall_layers(sf) == {18}
