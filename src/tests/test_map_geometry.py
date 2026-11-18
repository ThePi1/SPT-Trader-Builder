"""Boxes, the floor map (navmesh) and reading the game's Unity files: the pieces quest zones are checked and made with."""

import struct

import pytest

from core import geometry as G
from core import unity as U
from core.navmesh import NavMesh, merge_tiles


# --- boxes ------------------------------------------------------------------------------------------------

def test_a_box_holds_what_is_inside_it_turned_with_it():
	box = G.Box((10, 0, 10), (4, 2, 2), G.yaw_rotation(90))  # (4 m long east-west before the turn: north-south after)
	assert box.contains((10, 0, 11.9)) and not box.contains((11.9, 0, 10))
	assert box.contains((10, 0.9, 10)) and not box.contains((10, 1.1, 10))
	assert box.distance_to((10, 0, 14)) == pytest.approx(2.0)


def test_a_turn_is_clockwise_from_north_seen_from_above():
	assert G.yaw_of(G.yaw_rotation(10)) == pytest.approx(10)
	forward = G.rotate(G.yaw_rotation(90), (0, 0, 1))
	assert forward == pytest.approx((1, 0, 0), abs=1e-9)  # (north turned 90 degrees points east)
	assert G.is_upright(G.yaw_rotation(33)) and not G.is_upright((0.3, 0, 0, 0.95))


def test_boxes_overlap_only_when_they_share_space():
	a = G.Box((0, 0, 0), (2, 2, 2))
	assert a.overlaps(G.Box((1.5, 0, 0), (2, 2, 2)))
	assert not a.overlaps(G.Box((2.5, 0, 0), (2, 2, 2)))
	assert not a.overlaps(G.Box((2.2, 0, 2.2), (2, 2, 2), G.yaw_rotation(45)))  # (a diamond whose point stops short of the corner)
	assert a.overlaps(G.Box((1.9, 0, 0), (2, 2, 2), G.yaw_rotation(45)))


def test_the_footprint_is_the_outline_seen_from_above():
	corners = G.Box((0, 5, 0), (2, 1, 4)).footprint()
	assert sorted(corners) == [(-1, -2), (-1, 2), (1, -2), (1, 2)]


# --- the floor map ----------------------------------------------------------------------------------------

def _two_storeys():
	"""A 10 x 10 m ground floor at 0 m, and an upstairs over half of it at 4 m."""
	vertices = [(0, 0, 0), (10, 0, 0), (10, 0, 10), (0, 0, 10), (0, 4, 0), (5, 4, 0), (5, 4, 10), (0, 4, 10)]
	return NavMesh(vertices, [((0, 1, 2, 3), 0), ((4, 5, 6, 7), 0)])


def test_the_floors_at_a_spot_are_every_storey_there():
	nav = _two_storeys()
	assert nav.floors_at(2, 5) == [0.0, 4.0]
	assert nav.floors_at(8, 5) == [0.0]
	assert nav.floors_at(12, 5) == []
	assert nav.floor_near(2, 3.5, 5) == 4.0 and nav.floor_near(2, 0.5, 5) == 0.0


def test_a_sloping_floor_gives_the_height_where_you_stand():
	nav = NavMesh([(0, 0, 0), (10, 5, 0), (10, 5, 10), (0, 0, 10)], [((0, 1, 2, 3), 0)])
	assert nav.floors_at(4, 5) == [pytest.approx(2.0)]


def _tile(vertices, polygons):
	"""A navmesh tile as the game stores it: 'VAND' version 16, a 72-byte header, the vertices, then 32-byte polygons."""
	header = bytearray(72)
	header[0:4] = b"VAND"
	struct.pack_into("<i", header, 4, 16)
	struct.pack_into("<2i", header, 20, len(polygons), len(vertices))
	body = b"".join(struct.pack("<3f", *v) for v in vertices)
	for indexes in polygons:
		padded = list(indexes) + [0] * (6 - len(indexes))
		body += struct.pack("<6H6HIBBH", *padded, *([0] * 6), 1, len(indexes), 0, 0)
	return bytes(header) + body


def test_a_navmesh_tile_is_read_into_vertices_and_polygons():
	data = _tile([(0, 1, 0), (2, 1, 0), (2, 1, 2), (0, 1, 2)], [(0, 1, 2), (0, 2, 3)])
	tile = U.parse_nav_tile(data)
	assert tile.vertices[2] == pytest.approx((2, 1, 2))
	assert [p[0] for p in tile.polygons] == [(0, 1, 2), (0, 2, 3)]
	nav = merge_tiles([tile, U.parse_nav_tile(_tile([(5, 0, 0), (6, 0, 0), (6, 0, 1)], [(0, 1, 2)]))])
	assert nav.polygons[2][0] == (4, 5, 6)  # (the second tile's vertices follow the first's)
	assert nav.floors_at(1, 1.5) == [1.0]


def test_an_empty_tile_or_another_format_is_handled():
	empty = bytearray(72)
	empty[0:4] = b"VAND"
	struct.pack_into("<i", empty, 4, 16)
	assert U.parse_nav_tile(bytes(empty)).polygons == []
	with pytest.raises(U.FormatError):
		U.parse_nav_tile(b"DNAV" + bytes(68))


# --- Unity serialized files --------------------------------------------------------------------------------

def _serialized(objects):
	"""A minimal Unity 2022 serialized file (format 22, no type trees) holding objects: [(path id, class id, bytes)]."""
	classes = sorted({c for _p, c, _d in objects})
	meta = bytearray(b"2022.3.43f1\0") + struct.pack("<i", 19) + b"\0"
	meta += struct.pack("<i", len(classes))
	for class_id in classes:
		meta += struct.pack("<iBh", class_id, 0, -1) + (bytes(16) if class_id == U.MONO_BEHAVIOUR else b"") + bytes(16)
	meta += struct.pack("<i", len(objects))
	data, offsets = bytearray(), []
	for _path_id, _class_id, blob in objects:
		offsets.append(len(data))
		data += blob + bytes((-len(blob)) % 8)
	header_size = 48
	for (path_id, class_id, blob), offset in zip(objects, offsets):
		while (header_size + len(meta)) % 4:
			meta += b"\0"
		meta += struct.pack("<qqIi", path_id, offset, len(blob), classes.index(class_id))
	meta += struct.pack("<i", 0) + struct.pack("<i", 0)  # (no scripts, no externals)
	data_offset = (header_size + len(meta) + 15) & ~15
	head = struct.pack(">IIII", 0, 0, 22, 0) + b"\0\0\0\0" + struct.pack(">IqqQ", len(meta), data_offset + len(data), data_offset, 0)
	assert len(head) == header_size
	return head + bytes(meta) + bytes(data_offset - header_size - len(meta)) + bytes(data)


def _string(text):
	raw = text.encode()
	return struct.pack("<i", len(raw)) + raw + bytes((-len(raw)) % 4)


def test_game_objects_transforms_and_box_colliders_are_read_with_the_2022_layout(tmp_path):
	go = struct.pack("<i", 2) + struct.pack("<iq", 0, 2) + struct.pack("<iq", 0, 3) + struct.pack("<I", 0) + _string("zone") + struct.pack("<HB", 0, 1)
	parent = struct.pack("<iq", 0, 0) + struct.pack("<4f", *G.yaw_rotation(90)) + struct.pack("<3f", 100, 0, 0) + struct.pack("<3f", 2, 2, 2) + struct.pack("<i", 0) + struct.pack("<iq", 0, 0)
	child = struct.pack("<iq", 0, 1) + struct.pack("<4f", 0, 0, 0, 1) + struct.pack("<3f", 0, 0, 5) + struct.pack("<3f", 1, 1, 1) + struct.pack("<i", 0) + struct.pack("<iq", 0, 4)
	box = struct.pack("<iq", 0, 1) + struct.pack("<iq", 0, 0) + struct.pack("<IIi", 0, 0, 0) + bytes([1, 0, 0, 0, 1, 0, 0, 0]) + struct.pack("<3f", 3, 4, 5) + struct.pack("<3f", 0, 1, 0)
	path = tmp_path / "level1"
	path.write_bytes(_serialized([(1, U.GAME_OBJECT, go), (2, U.TRANSFORM, child), (3, U.BOX_COLLIDER, box), (4, U.TRANSFORM, parent)]))
	with U.SerializedFile(path) as sf:
		assert sf.unity_version == "2022.3.43f1" and sf.of_class(U.TRANSFORM) == [2, 4]
		game_object = U.read_game_object(sf, 1)
		assert game_object.name == "zone" and game_object.active and game_object.components == [(0, 2), (0, 3)]
		collider = U.read_box_collider(sf, 3)
		assert collider.is_trigger and collider.enabled and collider.size == (3, 4, 5) and collider.center == (0, 1, 0)
		rotation, position, scale = U.TransformCache(sf).world(2)
		assert position == pytest.approx((110, 0, 0), abs=1e-4)  # (5 m north, doubled by the parent's scale and turned east)
		assert scale == (2, 2, 2) and G.yaw_of(rotation) == pytest.approx(90)


def test_a_file_that_isnt_a_2022_scene_is_refused(tmp_path):
	path = tmp_path / "level0"
	path.write_bytes(struct.pack(">IIII", 0, 0, 17, 0) + bytes(64))
	with pytest.raises(U.FormatError):
		U.SerializedFile(path)
