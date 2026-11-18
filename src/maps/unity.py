"""Reading the game's Unity files, read-only: the built-in scenes (``EscapeFromTarkov_Data/levelN``) and their shared
assets (``sharedassetsN.assets``).

EFT's client is built with Unity 2022.3 without type trees, so each kind of object is read with its layout written
out here. Only what the map import needs is read: game objects, transforms, box colliders, the start of a
MonoBehaviour and its script's name, the build's scene list and the navigation mesh. Nothing is ever written.
No Qt.
"""

import mmap
import struct
from collections import namedtuple
from pathlib import Path

from maps import geometry as G

# Unity class ids
GAME_OBJECT, TRANSFORM, BOX_COLLIDER, MONO_BEHAVIOUR, MONO_SCRIPT, BUILD_SETTINGS, NAV_MESH_DATA, RECT_TRANSFORM = 1, 4, 65, 114, 115, 141, 238, 224


class FormatError(Exception):
	"""A file isn't laid out the way this reader expects (another Unity version, or not a Unity file)."""


class Reader:
	"""Reads values one after another from bytes (or a memory-mapped file), starting at pos."""

	def __init__(self, data, little=True, pos=0):
		self.data, self.pos = data, pos
		self._e = "<" if little else ">"

	def _unpack(self, fmt, size):
		value = struct.unpack_from(self._e + fmt, self.data, self.pos)
		self.pos += size
		return value

	def u8(self):
		value = self.data[self.pos]
		self.pos += 1
		return value

	def i16(self):
		return self._unpack("h", 2)[0]

	def u16(self):
		return self._unpack("H", 2)[0]

	def i32(self):
		return self._unpack("i", 4)[0]

	def u32(self):
		return self._unpack("I", 4)[0]

	def i64(self):
		return self._unpack("q", 8)[0]

	def f32(self):
		return self._unpack("f", 4)[0]

	def vec3(self):
		return self._unpack("3f", 12)

	def quat(self):
		return self._unpack("4f", 16)

	def raw(self, size):
		value = bytes(self.data[self.pos:self.pos + size])
		self.pos += size
		return value

	def cstr(self):
		end = self.data.find(b"\0", self.pos)
		if end < 0:
			raise FormatError("unterminated string")
		value = bytes(self.data[self.pos:end]).decode("utf-8", "replace")
		self.pos = end + 1
		return value

	def align(self):
		self.pos = (self.pos + 3) & ~3

	def string(self):
		"""A Unity string: its length, the UTF-8 bytes, then padding to 4 bytes."""
		size = self.i32()
		if size < 0 or self.pos + size > len(self.data):
			raise FormatError("bad string length")
		value = bytes(self.data[self.pos:self.pos + size]).decode("utf-8", "replace")
		self.pos += size
		self.align()
		return value

	def pptr(self):
		"""A reference to another object: (file index, path id). File 0 is this file; n is the file's nth external."""
		return (self.i32(), self.i64())


class SerializedFile:
	"""One Unity serialized file (format 22, Unity 2022): its object table, scripts and the files it refers to."""

	def __init__(self, path):
		self.path = Path(path)
		self._file = open(self.path, "rb")
		try:
			self.data = mmap.mmap(self._file.fileno(), 0, access=mmap.ACCESS_READ)
		except ValueError as e:  # (an empty file)
			self._file.close()
			raise FormatError(f"{self.path.name}: empty file") from e
		try:
			self._read_header()
		except (struct.error, IndexError, FormatError) as e:
			self.close()
			raise FormatError(f"{self.path.name}: not a Unity 2022 serialized file ({e})") from e

	def _read_header(self):
		head = Reader(self.data, little=False)
		head.u32()
		head.u32()
		self.version = head.u32()
		head.u32()
		if self.version < 22:
			raise FormatError(f"format {self.version}")
		little = head.u8() == 0
		head.pos += 3
		head.u32()
		head.i64()
		self.data_offset = head.i64()
		head.i64()
		self.little = little
		r = Reader(self.data, little, head.pos)
		self.unity_version = r.cstr()
		self.platform = r.i32()
		if r.u8():
			raise FormatError("has type trees (a different build of the game?)")
		self.types = []  # [(class id, script index)]
		for _ in range(r.i32()):
			class_id = r.i32()
			r.u8()
			script_index = r.i16()
			if class_id == MONO_BEHAVIOUR:
				r.raw(16)
			r.raw(16)
			self.types.append((class_id, script_index))
		self.objects = {}  # {path id: (start, size, type index)}
		for _ in range(r.i32()):
			r.align()
			path_id = r.i64()
			start = r.i64()
			size = r.u32()
			type_index = r.i32()
			self.objects[path_id] = (start, size, type_index)
		self.scripts = []  # [(file index, path id)] of the MonoScripts the MonoBehaviours use
		for _ in range(r.i32()):
			file_index = r.i32()
			r.align()
			self.scripts.append((file_index, r.i64()))
		self.externals = []  # the names of the files this one refers to (file index n is externals[n - 1])
		for _ in range(r.i32()):
			r.cstr()
			r.raw(16)
			r.i32()
			self.externals.append(r.cstr())

	def close(self):
		try:
			self.data.close()
		finally:
			self._file.close()

	def __enter__(self):
		return self

	def __exit__(self, *exc):
		self.close()

	def reader(self, path_id):
		start, _size, _type = self.objects[path_id]
		return Reader(self.data, self.little, self.data_offset + start)

	def class_id(self, path_id):
		return self.types[self.objects[path_id][2]][0]

	def script_index(self, path_id):
		return self.types[self.objects[path_id][2]][1]

	def of_class(self, class_id):
		return [pid for pid, (_s, _z, t) in self.objects.items() if self.types[t][0] == class_id]

	def external_name(self, file_index):
		return None if file_index == 0 else self.externals[file_index - 1]


# --- the objects ---------------------------------------------------------------------------------------

GameObject = namedtuple("GameObject", "components layer name active")
Transform = namedtuple("Transform", "game_object rotation position scale children father")
BoxCollider = namedtuple("BoxCollider", "game_object is_trigger enabled size center")
Behaviour = namedtuple("Behaviour", "game_object enabled script name reader")


def read_game_object(sf, path_id):
	r = sf.reader(path_id)
	components = [r.pptr() for _ in range(r.i32())]
	layer = r.u32()
	name = r.string()
	r.u16()
	active = bool(r.u8())
	return GameObject(components, layer, name, active)


def read_transform(sf, path_id):
	"""A Transform (or RectTransform, which starts the same way)."""
	r = sf.reader(path_id)
	game_object = r.pptr()
	rotation, position, size = r.quat(), r.vec3(), r.vec3()
	children = [r.pptr() for _ in range(r.i32())]
	father = r.pptr()
	return Transform(game_object, rotation, position, size, children, father)


def read_box_collider(sf, path_id):
	r = sf.reader(path_id)
	game_object = r.pptr()
	r.pptr()  # m_Material
	r.u32()  # m_IncludeLayers
	r.u32()  # m_ExcludeLayers
	r.i32()  # m_LayerOverridePriority
	is_trigger = bool(r.u8())
	r.u8()  # m_ProvidesContacts
	r.align()
	enabled = bool(r.u8())
	r.align()
	size, center = r.vec3(), r.vec3()
	return BoxCollider(game_object, is_trigger, enabled, size, center)


def read_behaviour(sf, path_id):
	"""The part every MonoBehaviour starts with; reader is left at the script's own fields."""
	r = sf.reader(path_id)
	game_object = r.pptr()
	enabled = bool(r.u8())
	r.align()
	script = r.pptr()
	name = r.string()
	return Behaviour(game_object, enabled, script, name, r)


def read_mono_script(sf, path_id):
	"""(namespace, class name, assembly) of a script."""
	r = sf.reader(path_id)
	r.string()  # m_Name
	r.i32()  # m_ExecutionOrder
	r.raw(16)  # m_PropertiesHash
	class_name = r.string()
	namespace = r.string()
	assembly = r.string()
	return namespace, class_name, assembly


def read_scene_list(globalgamemanagers):
	"""The scenes of the build in order: scene n is the file levelN."""
	settings = globalgamemanagers.of_class(BUILD_SETTINGS)
	if not settings:
		raise FormatError("no build settings")
	r = globalgamemanagers.reader(settings[0])
	return [r.string() for _ in range(r.i32())]


class TransformCache:
	"""World positions of the transforms of one file (each parent is worked out once)."""

	def __init__(self, sf):
		self.sf = sf
		self._world = {}

	def local(self, path_id):
		return read_transform(self.sf, path_id)

	def world(self, path_id):
		"""(rotation, position, lossy scale) in the world."""
		found = self._world.get(path_id)
		if found is not None:
			return found
		t = read_transform(self.sf, path_id)
		if t.father[1] == 0 or t.father[0] != 0 or t.father[1] not in self.sf.objects:
			found = (t.rotation, t.position, t.scale)
		else:
			p_rot, p_pos, p_scale = self.world(t.father[1])
			position = G.add(p_pos, G.rotate(p_rot, G.scale(t.position, p_scale)))
			found = (G.q_mul(p_rot, t.rotation), position, G.scale(t.scale, p_scale))
		self._world[path_id] = found
		return found


# --- the navigation mesh -----------------------------------------------------------------------------

NavTile = namedtuple("NavTile", "vertices polygons")  # vertices [(x, y, z)], polygons [(vertex indexes, area)]

_TILE_MAGIC = b"VAND"  # ('DNAV' written little-endian)
_TILE_VERSION = 16
_HEADER = 72
_POLY_SIZE = 32


def read_navmesh_tiles(sf, path_id):
	"""The tiles of a NavMeshData object, as raw bytes each."""
	r = sf.reader(path_id)
	r.string()  # m_Name
	tiles = []
	for _ in range(r.i32()):
		size = r.i32()
		tiles.append(r.raw(size))
		r.align()
		r.raw(16)  # m_Hash
	return tiles


def parse_nav_tile(data):
	"""The vertices and walkable polygons of one tile (Unity's navmesh tile: a Detour tile without links).
	An empty tile has none."""
	if len(data) < _HEADER or data[:4] != _TILE_MAGIC:
		raise FormatError("not a navmesh tile")
	version = struct.unpack_from("<i", data, 4)[0]
	if version != _TILE_VERSION:
		raise FormatError(f"navmesh tile version {version}")
	poly_count, vert_count = struct.unpack_from("<2i", data, 20)
	if poly_count <= 0 or vert_count <= 0:
		return NavTile([], [])
	end = _HEADER + vert_count * 12 + poly_count * _POLY_SIZE
	if end > len(data):
		raise FormatError("navmesh tile too short")
	flat = struct.unpack_from(f"<{vert_count * 3}f", data, _HEADER)
	vertices = [flat[i:i + 3] for i in range(0, len(flat), 3)]
	polygons = []
	base = _HEADER + vert_count * 12
	for i in range(poly_count):
		at = base + i * _POLY_SIZE
		indexes = struct.unpack_from("<6H", data, at)
		count, area = data[at + 28], data[at + 29]
		if 3 <= count <= 6:
			polygons.append((indexes[:count], area))
	return NavTile(vertices, polygons)
