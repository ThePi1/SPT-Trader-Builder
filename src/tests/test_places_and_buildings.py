"""Finding places by the names players use (maps.places), the building at a spot (maps.buildings), the imported
maps' object index (maps.mapdata.ObjectIndex), and the commands built on them. The maps are small made-up ones."""

import gzip
import json

import pytest

from cli import main as cli_main
from maps import buildings as B
from maps import geometry as G
from maps import mapdata as M
from maps import places as P
from maps.navmesh import NavMesh
from maps.zones import ZoneIndex

CENTER, SIZE, YAW = (50.0, 50.0), (20.0, 30.0), 20.0


@pytest.fixture(autouse=True)
def plain_program(tmp_path, monkeypatch):
	"""The program's defaults, not the settings or saved items of the computer the tests run on."""
	monkeypatch.setattr("cli.workspace.Settings.load", classmethod(lambda cls, path=None: cls()))
	monkeypatch.setattr("core.library.LIBRARY_FILE", tmp_path / "no_items.json")


def _rect(center, size, yaw, height):
	"""A floor polygon: (vertices [(x, y, z)], [0, 1, 2, 3])."""
	return [(x, height, z) for x, z in B.corners(center, size, yaw)]


def _floors():
	"""Ground 100 x 100 m at 0; a building turned 20 degrees with a storey at 4 m and its roof at 11 m; a tunnel at -8 m
	under it."""
	return [
		[(0, 0, 0), (100, 0, 0), (100, 0, 100), (0, 0, 100)],
		_rect(CENTER, SIZE, YAW, 4.0),
		_rect(CENTER, (12.0, 14.0), YAW, 11.0),
		_rect((52.0, 50.0), (8.0, 8.0), 0.0, -8.0),
	]


OBJECTS = [
	("Floor_1_Room_1", (50.0, 0.5, 50.0)), ("Floor_2_Room_1", (52.0, 4.4, 48.0)), ("Floor_3_Room_2", (50.0, 7.8, 52.0)),
	("stairs_f3", (48.0, 7.6, 51.0)), ("Broom_03", (51.0, 0.3, 49.0)), ("Floor_1_Room_9", (5.0, 0.5, 5.0)),
	("white_horse", (80.0, -20.0, 20.0)), ("String_light_lamp_white", (10.0, 3.0, 90.0)), ("dorms_outdoor", (20.0, 1.0, 20.0)),
]


def _write_map(folder, location="RezervBase", floors=None, objects=OBJECTS, areas=()):
	folder.mkdir(exist_ok=True)
	(folder / f"{location}.json").write_text(json.dumps({"format": M.FORMAT, "location": location, "zones": [], "areas": list(areas)}), encoding="utf-8")
	vertices, polygons = [], []
	for corners in floors if floors is not None else _floors():
		base = len(vertices)
		vertices += corners
		polygons.append(list(range(base, base + len(corners))))
	with gzip.open(folder / f"{location}{M.NAVMESH_SUFFIX}", "wt", encoding="utf-8") as f:
		json.dump({"format": M.FORMAT, "vertices": [c for v in vertices for c in v], "polygons": polygons}, f)
	if objects is not None:
		M._write_objects(folder / f"{location}{M.OBJECTS_SUFFIX}", {(n, *p): ("Scene_" + n[:3], p) for n, p in objects})
	return folder


def run(capsys, *argv):
	code = cli_main.main([str(a) for a in argv])
	return code, json.loads(capsys.readouterr().out)


# --- the object index ------------------------------------------------------------------------------------

def test_the_object_index_is_searched_by_name_and_by_place(tmp_path):
	m = M.MapData.load("RezervBase", _write_map(tmp_path / "maps"))
	assert len(m.objects) == len(OBJECTS)
	assert m.objects.search("white HORSE") == [{"name": "white_horse", "scene": "Scene_whi.unity", "position": [80.0, -20.0, 20.0]}]
	box = G.Box((50, 4, 50), (6, 10, 6))
	assert {n for n, _s, _p in m.objects.inside(box)} == {"Floor_1_Room_1", "Floor_2_Room_1", "Floor_3_Room_2", "stairs_f3", "Broom_03"}


def test_a_map_imported_before_objects_were_indexed_has_none(tmp_path):
	assert M.MapData.load("RezervBase", _write_map(tmp_path / "maps", objects=None)).objects is None


# --- named places ---------------------------------------------------------------------------------------------

def test_words_are_also_tried_as_their_synonyms():
	synonyms = {"knight": ["horse"], "gas station": ["azs"]}
	assert P.terms("White  Knight", synonyms) == [{"white"}, {"knight", "horse"}]
	assert P.terms("the gas station", synonyms) == [{"gasstation", "gas_station", "azs"}, {"the"}]
	assert P.matches("white_horse", P.terms("white knight", synonyms)) == (True, 2)
	assert P.matches("String_light_lamp_white", P.terms("white knight", synonyms)) == (False, 0)


def test_find_ranks_named_places_then_areas_then_objects(tmp_path):
	folder = _write_map(tmp_path / "maps", areas=[{"name": "Obshezhitie", "scene": "custom_Obshezhitie", "min": [0, 0, 0], "max": [40, 10, 40], "objects": 99}])
	places = tmp_path / "places.json"
	places.write_text(json.dumps({"synonyms": {"knight": ["horse"], "dorms": ["obshezhitie"]}, "places": [
		{"map": "RezervBase", "name": "White Knight", "aka": ["PTOR2"], "at": [50, 50], "objects": "white_horse", "note": "checked"},
		{"map": "RezervBase", "name": "Gone", "objects": "no_such_object"},
	]}), encoding="utf-8")
	index = ZoneIndex(folder)
	found = P.find(index, "white knight", path=places)
	assert found[0] == {"kind": "place", "map": "RezervBase", "name": "White Knight", "aka": ["PTOR2"], "note": "checked", "anchors": 1, "at": [50, 50]}
	assert found[1]["kind"] == "objects" and found[1]["names"] == ["white_horse"] and found[1]["at"] == [80.0, -20.0, 20.0]
	assert len(found) == 2  # (the lamp has "white" but not "knight" or "horse")
	dorms = P.find(index, "dorms", path=places)
	assert [f["kind"] for f in dorms] == ["area", "objects"] and dorms[0]["name"] == "Obshezhitie"
	gone = P.find(index, "gone", path=places)
	assert "warning" in gone[0] and "at" not in gone[0]


# --- buildings --------------------------------------------------------------------------------------------------

def test_a_name_says_whether_it_is_a_room_and_its_storey():
	assert B.is_room("Floor_1_Room_3") and B.is_room("rem_block_01_stairs_f1") and B.is_room("ServerRoom_main") and B.is_room("Roof_2")
	assert not B.is_room("Broom_03") and not B.is_room("office_Folders_FloorSet2") and not B.is_room("Toilet_01")
	assert not B.is_room("AudioPortal_FROM_room_TO_stairs")
	assert [B.floor_number(n) for n in ("Floor_2_Room_1", "stairs_f3", "PTOR2_Floor_1", "2nd_floor_hall", "Roof_2")] == [2, 3, 1, 2, None]


def test_the_outline_is_the_smallest_turned_rectangle():
	points = [(x, z) for x, z in (B.corners(CENTER, SIZE, YAW))]
	inside = [c for u in range(-9, 10, 3) for v in range(-14, 15, 4) for c in B.corners(CENTER, (abs(u) * 2 or 1, abs(v) * 2 or 1), YAW)]
	center, size, yaw = B.outline(points + inside, trim=0.0)
	assert center == pytest.approx(CENTER, abs=0.3) and yaw == pytest.approx(YAW, abs=0.6)
	assert size == pytest.approx((SIZE[0] + B.STEP, SIZE[1] + B.STEP), abs=0.3)


def test_the_building_at_a_spot_has_its_outline_storeys_rooms_and_a_zone(tmp_path):
	m = M.MapData.load("RezervBase", _write_map(tmp_path / "maps"))
	found = B.building_at(m, 52.0, 47.0)
	outline = found["outline"]
	assert found["ground"] == 0.0
	assert outline["center"] == pytest.approx(CENTER, abs=0.6) and outline["yaw"] == pytest.approx(YAW, abs=1.0)
	assert outline["size"] == pytest.approx(SIZE, abs=1.5)
	heights = [(s["height"], s["source"].split(" ")[0]) for s in found["storeys"]]
	assert heights == [(-8.0, "floor"), (0.0, "floor"), (4.0, "floor"), (7.4, "named"), (11.0, "floor")]  # (storey 3: its rooms at 7.6 and 7.8 m, less 0.3)
	assert found["storeys"][0]["below_ground"] and any("below the ground" in n for n in found["notes"])
	assert [r["name"] for r in found["rooms"]] == ["Floor_1_Room_1", "Floor_2_Room_1", "stairs_f3", "Floor_3_Room_2"]
	assert set(found["floors_named"]) == {1, 2, 3}
	zone = found["zone"]
	assert zone["bottom"] == -0.25 and zone["top"] == 11.0 + B.REACH_ABOVE  # (the tunnel under it is left out)
	width, height, depth = (float(v) for v in zone["size"].split(","))
	assert width == pytest.approx(outline["size"][0] + 2, abs=0.11) and height == pytest.approx(13.75, abs=0.11)


def test_a_spot_with_no_upper_floor_has_no_outline(tmp_path):
	m = M.MapData.load("RezervBase", _write_map(tmp_path / "maps", floors=_floors()[:1]))
	found = B.building_at(m, 50.0, 50.0)
	assert "outline" not in found and "zone" not in found and "upper floor" in found["notes"][0]
	assert [r["name"] for r in found["rooms"]][:1] == ["Floor_1_Room_1"]


# --- the commands -------------------------------------------------------------------------------------------------

def test_zones_find_building_make_and_check_rooms(capsys, tmp_path, monkeypatch):
	maps = _write_map(tmp_path / "maps")
	places = tmp_path / "places.json"
	places.write_text(json.dumps({"synonyms": {}, "places": [{"map": "RezervBase", "name": "Tower", "at": [51, 49]}]}), encoding="utf-8")
	monkeypatch.setattr(P, "PLACES_FILE", places)
	project = tmp_path / "project.json"
	project.write_text(json.dumps({"quests": "quests.json", "locale": "en.json", "zones": "zones/new.json"}), encoding="utf-8")
	code, result = run(capsys, "--maps", maps, "zones", "find", "tower")
	assert code == 0 and result["found"][0]["next"] == "zones building --map RezervBase --at=51,49"
	code, result = run(capsys, "--maps", maps, "zones", "building", "--map", "Reserve", "--place", "Tower", "--picture", tmp_path / "b.png")
	assert code == 0 and result["outline"]["yaw"] == pytest.approx(YAW, abs=1.0) and (tmp_path / "b.png").stat().st_size > 1000
	code, result = run(capsys, "--project", project, "--maps", maps, "zones", "make", "--map", "Reserve", "--id", "tower", "--kind", "visit",
	                   "--at", "52,47", "--building", "--write")
	assert code == 0 and result["errors"] == [], result
	saved = json.loads((tmp_path / "zones" / "new.json").read_text(encoding="utf-8"))[0]
	assert float(saved["Position"]["Y"]) - float(saved["Scale"]["Y"]) / 2 == pytest.approx(-0.25)
	assert G.yaw_of(tuple(float(saved["Rotation"][k]) for k in "XYZW")) == pytest.approx(YAW, abs=1.0)
	code, result = run(capsys, "--project", project, "--maps", maps, "zones", "check", "--rooms")
	covers = result["results"][0]["covers"]
	assert covers["storeys_named"] == [1, 2, 3] and "Floor_3_Room_2" in covers["rooms"] and "Broom_03" not in covers["rooms"]
	assert covers["floors"] == [0.0, 4.0, 11.0]
	code, result = run(capsys, "--maps", maps, "zones", "objects", "--map", "Reserve", "horse")
	assert code == 0 and result[0]["name"] == "white_horse"


def test_coordinates_can_start_with_a_minus(capsys, tmp_path):
	maps = _write_map(tmp_path / "maps", floors=[[(-20, 1, -20), (0, 1, -20), (0, 1, 0), (-20, 1, 0)]])
	code, result = run(capsys, "--maps", maps, "zones", "at", "--map", "Reserve", "-5,-5")
	assert code == 0 and result["x"] == -5.0 and result["floors"] == [1.0]
	code, result = run(capsys, "--maps", maps, "zones", "render", "--map", "Reserve", "--at", "-5.5,-5", "--radius", "5", "--out", tmp_path / "r.png")
	assert code == 0 and result["center"] == [-5.5, -5.0]


def test_a_zone_on_stairs_reaches_down_the_whole_flight_only_when_asked(tmp_path):
	from maps import zones as Z

	floors = [
		[(0, 0, 0), (20, 0, 0), (20, 0, 10), (0, 0, 10)],  # the ground floor
		[(5, 0, 10), (7, 0, 10), (7, -3, 16), (5, -3, 16)],  # stairs down
		[(0, -3, 16), (20, -3, 16), (20, -3, 26), (0, -3, 26)],  # the basement
		[(10, 3.5, 0), (20, 3.5, 0), (20, 3.5, 10), (10, 3.5, 10)],  # a storey above part of the ground floor
	]
	index = ZoneIndex(_write_map(tmp_path / "maps", "bigmap", floors, objects=None))
	_record, plain, notes = Z.make_zone(index, "stairs", "bigmap", "visit", 6, 13, None, (1.6, 5, 7))
	assert plain.box.center[1] - 2.5 == pytest.approx(-1.5 - Z.SINK) and "--slope" in notes[-1]
	_record, sloped, notes = Z.make_zone(index, "stairs", "bigmap", "visit", 6, 13, None, (1.6, 5, 7), slope=True)
	assert sloped.box.center[1] - 2.5 == pytest.approx(-3 - Z.SINK) and "from -3.00 to 0.00 m" in notes[-1]
	_record, upstairs, notes = Z.make_zone(index, "room", "bigmap", "visit", 15, 5, 3.5, (4, 3, 4))
	assert upstairs.box.center[1] - 1.5 == pytest.approx(3.5 - Z.SINK) and len(notes) == 1  # (the storey below isn't part of its walk)


def test_objects_in_a_scene_named_after_the_place_come_before_lighting_groups(tmp_path):
	folder = _write_map(tmp_path / "maps", "bigmap", objects=None)
	objects = {("AZS_old", 228, -14, -57): ("custom_Light", (228.0, -14.0, -57.0))}
	for i in range(6):
		objects[(f"P.ZoneOldAZS Patrol {i}", 315 + i, 1, -171)] = ("custom_AZS_old", (315.0 + i, 1.0, -171.0))
	M._write_objects(folder / f"bigmap{M.OBJECTS_SUFFIX}", objects)
	places = tmp_path / "places.json"
	places.write_text(json.dumps({"synonyms": {"gas station": ["azs"]}, "places": []}), encoding="utf-8")
	found = P.find(ZoneIndex(folder), "old gas station", path=places)
	assert [f["scenes"] for f in found] == [["custom_AZS_old"], ["custom_Light"]]
