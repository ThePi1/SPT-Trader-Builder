"""Quest zones: WTT-CommonLib's zone files, which zones each condition can use, the checks of quests and zone files,
and making a zone that stands on the floor. The maps are small made-up ones; one test reads the real game when it is
installed where the 4.1.6 test copy lives."""

import gzip
import json
import os
from pathlib import Path

import pytest

from maps import geometry as G
from maps import mapdata as M
from maps import zones as Z
from schema import registry, validate
from schema.issues import ERROR, WARNING

GAME = Path(os.environ.get("SPT_GAME", r"I:\Games\SPT-4-1-6-testing"))  # (an SPT 4.1 game folder; the live import test is skipped without one)


def _record(zone_id, kind="placeitem", where="bigmap", position=(5, 1, 5), scale=(2, 2, 2), rotation=(0, 0, 0, 1)):
	return {
		"ZoneId": zone_id, "ZoneName": zone_id, "ZoneLocation": where, "ZoneType": kind, "FlareType": "",
		"Position": {"X": str(position[0]), "Y": str(position[1]), "Z": str(position[2]), "W": "0"},
		"Rotation": {"X": str(rotation[0]), "Y": str(rotation[1]), "Z": str(rotation[2]), "W": str(rotation[3])},
		"Scale": {"X": str(scale[0]), "Y": str(scale[1]), "Z": str(scale[2]), "W": "0"},
	}


def _map(folder, location="bigmap", zones=(), floors=((0, 0, 0, 20, 20),)):
	"""An imported map in folder: game zones [(id, kind, center, size)] and square floors (x0, z0, height, x1, z1)."""
	record = {
		"format": M.FORMAT, "location": location, "zones": [
			{"id": i, "kind": k, "class": "x", "object": i, "active": True, "scene": "s", "boxes": [{"center": list(c), "size": list(s), "rotation": [0, 0, 0, 1]}]}
			for i, k, c, s in zones
		], "areas": [{"name": "Dorms", "scene": "custom_Dorms", "min": [0, 0, 0], "max": [10, 5, 10], "objects": 99}],
	}
	(folder / f"{location}.json").write_text(json.dumps(record), encoding="utf-8")
	vertices, polygons = [], []
	for x0, z0, h, x1, z1 in floors:
		base = len(vertices) // 3
		vertices += [x0, h, z0, x1, h, z0, x1, h, z1, x0, h, z1]
		polygons.append([base, base + 1, base + 2, base + 3])
	with gzip.open(folder / f"{location}{M.NAVMESH_SUFFIX}", "wt", encoding="utf-8") as f:
		json.dump({"format": M.FORMAT, "vertices": vertices, "polygons": polygons}, f)
	return folder


def _quest(finish):
	return {"q1": {"_id": "q1", "QuestName": "Test", "location": "any", "conditions": {"AvailableForFinish": finish, "AvailableForStart": [], "Fail": []}, "rewards": {}}}


def _task(kind, **keys):
	item = registry.new_item("task", kind)
	item.update(keys)
	return item


def _counter(*steps):
	item = registry.new_item("task", "CounterCreator")
	for kind, keys in steps:
		sub = registry.new_item("subtask", kind)
		sub.update(keys)
		item["counter"]["conditions"].append(sub)
	return item


# --- zone files ---------------------------------------------------------------------------------------------

def test_a_zone_file_entry_becomes_a_box_and_back(tmp_path):
	record = _record("Z1", "visit", "BigMap", (1.5, 2, -3), (4, 3, 2), G.yaw_rotation(30))
	zone = Z.zone_from_record(record, "a.json")
	assert zone.location == "bigmap" and zone.kind == Z.VISIT and zone.box.size == (4, 3, 2)
	again = Z.zone_record("Z1", "bigmap", Z.VISIT, zone.box)
	assert again["Position"] == {"X": "1.5", "Y": "2", "Z": "-3", "W": "0"} and again["ZoneType"] == "visit"
	assert float(again["Rotation"]["Y"]) == pytest.approx(G.yaw_rotation(30)[1], abs=1e-6)
	assert Z.CUSTOM_KINDS["botkillzone"] == Z.TRIGGER


def test_broken_entries_are_reported_and_the_rest_read(tmp_path):
	path = tmp_path / "zones.json"
	bad = _record("B", "nonsense")
	path.write_text(json.dumps([_record("A"), bad, {"ZoneId": "C", "ZoneType": "visit", "Position": {"X": "x"}}]), encoding="utf-8")
	zones, problems = Z.read_zone_file(path)
	assert [z.id for z in zones] == ["A"]
	assert [p.path for p in problems] == [(1,), (2,)] and all(p.level == ERROR for p in problems)
	assert Z.is_zone_file(json.loads(path.read_text())) and not Z.is_zone_file({"a": 1})


def test_adding_to_a_zone_file_keeps_what_is_there_and_refuses_a_second_copy(tmp_path):
	path = tmp_path / "sub" / "new.json"
	Z.add_to_zone_file(path, _record("A"))
	Z.add_to_zone_file(path, _record("B"))
	with pytest.raises(ValueError):
		Z.add_to_zone_file(path, _record("A"))
	Z.add_to_zone_file(path, _record("A", scale=(9, 9, 9)), replace=True)
	data = json.loads(path.read_text(encoding="utf-8"))
	assert [r["ZoneId"] for r in data] == ["A", "B"] and data[0]["Scale"]["X"] == "9"


# --- which zones a condition can use -------------------------------------------------------------------------

def _index(tmp_path, zones=(), files=()):
	return Z.ZoneIndex(_map(tmp_path, zones=zones), files)


def test_a_placeitem_zone_can_never_count_as_inside(tmp_path):
	index = _index(tmp_path, [("mark", "placeitem", (5, 1, 5), (2, 2, 2)), ("room", "visit", (5, 1, 5), (2, 2, 2))])
	quests = _quest([_counter(("InZone", {"zoneIds": ["mark"]})), _counter(("InZone", {"zoneIds": ["room"]}))])
	issues = Z.zone_issues(quests, index, {})
	assert [(i.level, i.path[3]) for i in issues] == [(ERROR, 0)]
	assert "placeitem" in issues[0].message and "can't be completed" in issues[0].message


def test_each_condition_needs_its_kind_of_zone(tmp_path):
	index = _index(tmp_path, [("v", "visit", (1, 1, 1), (2, 2, 2)), ("p", "placeitem", (1, 1, 1), (2, 2, 2))])
	quests = _quest([
		_task("PlaceBeacon", zoneId="p"), _task("PlaceBeacon", zoneId="v"),
		_task("LeaveItemAtLocation", zoneId="v"), _counter(("VisitPlace", {"target": "v"})), _counter(("VisitPlace", {"target": "p"})),
	])
	bad = [i.path[3] for i in Z.zone_issues(quests, index, {}) if i.level == ERROR]
	assert bad == [1, 2, 4]


def test_a_zone_id_nobody_has_is_a_warning_only_once_maps_are_known(tmp_path):
	quests = _quest([_task("PlaceBeacon", zoneId="nowhere")])
	assert [i.level for i in Z.zone_issues(quests, _index(tmp_path), {})] == [WARNING]
	no_maps = Z.ZoneIndex(tmp_path / "empty")
	assert Z.zone_issues(quests, no_maps, {}) == []  # (without the game's zones, an unknown id may well be the game's)


def test_a_zone_on_another_map_than_the_condition_is_a_warning(tmp_path):
	index = _index(tmp_path, [("room", "visit", (1, 1, 1), (2, 2, 2))])
	quests = _quest([_counter(("VisitPlace", {"target": "room"}), ("Location", {"target": ["Woods"]}))])
	issues = Z.zone_issues(quests, index, {})
	assert [i.level for i in issues] == [WARNING] and "bigmap" in issues[0].message
	same = _quest([_counter(("VisitPlace", {"target": "room"}), ("Location", {"target": ["bigmap"]}))])
	assert Z.zone_issues(same, index, {}) == []
	by_quest = _quest([_task("PlaceBeacon", zoneId="x")])
	by_quest["q1"]["location"] = "5704e3c2d2720bac5b8b4567"  # (Woods)
	index.add_records([_record("x")], "mine.json")
	assert "bigmap" in Z.zone_issues(by_quest, index)[0].message  # (the quest's own map, from data/locations.json)


def test_the_validator_checks_zones_when_it_is_given_them(tmp_path):
	index = _index(tmp_path, [("p", "placeitem", (1, 1, 1), (2, 2, 2))])
	quests = _quest([_counter(("InZone", {"zoneIds": ["p"]}))])
	assert any("placeitem" in i.message for i in validate.validate_quests(quests, zones=index))
	assert not any("placeitem" in i.message for i in validate.validate_quests(quests))


def test_zone_files_can_be_reference_files(tmp_path):
	from core.references import ZONES, References

	path = tmp_path / "zones.json"
	path.write_text(json.dumps([{"ZoneId": "a", "ZoneType": "visit", "ZoneLocation": "bigmap", "Position": {"X": "1", "Y": "1", "Z": "1"}, "Scale": {"X": "1", "Y": "1", "Z": "1"}}]), encoding="utf-8")
	refs = References(tmp_path / "refs.json")
	added, skipped = refs.add([str(path)])
	assert not skipped and added[0].kind == ZONES and added[0].count == 1
	assert refs.zone_files()[0][1] == "zones.json"


# --- checking zone files --------------------------------------------------------------------------------------

def test_zone_file_checks(tmp_path):
	folder = _map(tmp_path, zones=[("game_mark", "placeitem", (15, 1, 15), (2, 2, 2))], floors=((0, 0, 0, 20, 20), (0, 0, 4, 10, 10)))
	records = [
		_record("fine", "visit", position=(18, 1, 5)),
		_record("overlap", "placeitem", position=(15.5, 1, 15)),
		_record("twice", position=(18, 1, 18)), _record("twice", position=(18, 1, 18)),
		_record("storeys", "visit", position=(5, 2, 5), scale=(4, 6, 4)),
		_record("in the air", "visit", position=(18, 30, 18)),
		_record("tilted", "visit", position=(18, 1, 2), rotation=(0.3, 0, 0, 0.954)),
		_record("lost", "visit", where="Atlantis"),
	]
	path = tmp_path / "mine.json"
	path.write_text(json.dumps(records), encoding="utf-8")
	index = Z.ZoneIndex(folder, [path])
	found = {}
	for zone in index.zones:
		if zone.source != Z.GAME:
			found.setdefault(zone.id, Z.check_zone(zone, index))
	assert found["fine"] == ([], [])
	assert "game_mark" in found["overlap"][1][0]
	assert found["twice"][0] and "twice" in found["twice"][0][0].lower()
	assert "2 floors" in found["storeys"][1][0]
	assert not found["in the air"][0] and "reach" in found["in the air"][1][0]  # (only a warning: the floor map misses some floors)
	assert "tilted" in found["tilted"][1][0]
	assert found["lost"][0] and "Atlantis" in found["lost"][0][0]


def test_the_checks_look_at_fewer_spots_under_a_big_zone():
	"""Every 0.5 m under a small zone; under a 100 m one, about MOST_SAMPLES spots (every 2 m), all inside it."""
	small = Z.footprint_points(G.Box((0, 0, 0), (4, 2, 3)))
	assert len(small) == 8 * 6
	big = G.Box((115, 1, 187), (100, 50, 100), G.yaw_rotation(30))
	spots = Z.footprint_points(big)
	assert len(spots) == Z.MOST_SAMPLES
	assert all(big.contains((x, 1, z)) for x, z in spots)
	long = Z.footprint_points(G.Box((0, 0, 0), (400, 2, 1)))  # (a long thin one: still every 0.5 m along it)
	assert len(long) == 800 * 2


def test_a_box_beside_the_mapped_floor_is_only_a_warning(tmp_path):
	index = Z.ZoneIndex(_map(tmp_path))
	errors, warnings = Z.floor_report(G.Box((22, 1, 5), (2, 2, 2)), index.map("bigmap").navmesh)
	assert not errors and "nearby" in warnings[0]


# --- making zones -------------------------------------------------------------------------------------------

def test_a_new_zone_stands_on_the_floor_it_is_given(tmp_path):
	index = Z.ZoneIndex(_map(tmp_path, floors=((0, 0, 0, 20, 20), (0, 0, 4, 10, 10))))
	record, zone, notes = Z.make_zone(index, "new", "Customs" if False else "bigmap", Z.PLACEITEM, 5, 5, size=(3, 2.5, 3), yaw=10)
	assert zone.box.center[1] - zone.box.size[1] / 2 == pytest.approx(-Z.SINK)  # (the lowest floor, sunk a little)
	assert "2 floors" in notes[0] and record["ZoneType"] == "placeitem"
	_r, upstairs, _n = Z.make_zone(index, "up", "bigmap", Z.VISIT, 5, 5, y=4.2)
	assert upstairs.box.center[1] - upstairs.box.size[1] / 2 == pytest.approx(4 - Z.SINK)
	assert Z.check_zone(zone, index) == ([], [])


def test_a_new_zone_off_the_floor_map_uses_the_floor_nearby_or_the_height_given(tmp_path):
	index = Z.ZoneIndex(_map(tmp_path))
	_r, zone, notes = Z.make_zone(index, "near", "bigmap", Z.VISIT, 22, 5)
	assert zone.box.center[1] - zone.box.size[1] / 2 == pytest.approx(-Z.SINK) and "nearby" in notes[0]
	_r, zone, _n = Z.make_zone(index, "given", "bigmap", Z.VISIT, 22, 5, y=7)
	assert zone.box.center[1] - zone.box.size[1] / 2 == pytest.approx(7 - Z.SINK)
	with pytest.raises(ValueError):
		Z.make_zone(index, "far", "bigmap", Z.VISIT, 90, 90)
	with pytest.raises(ValueError):
		Z.make_zone(index, "x", "Woods", Z.VISIT, 1, 1)  # (not imported)


# --- the real game ------------------------------------------------------------------------------------------

@pytest.mark.skipif(not (GAME / "EscapeFromTarkov_Data" / "globalgamemanagers").is_file(), reason="no SPT 4.1 game folder (set SPT_GAME)")
def test_importing_a_real_map_finds_its_zones_and_floor(tmp_path):
	summary = M.import_maps(GAME, tmp_path, ["Labyrinth"])
	assert summary["Labyrinth"]["zones"] >= 5 and summary["Labyrinth"]["polygons"] > 1000
	data = M.MapData.load("labyrinth", tmp_path)
	zones = Z.zones_of_map(data)
	assert {z.kind for z in zones} >= {Z.VISIT, Z.PLACEITEM}
	on_floor = [z for z in zones if data.navmesh.floor_near(z.box.center[0], z.box.center[1], z.box.center[2], 3, 3) is not None]
	assert on_floor
	for zone in on_floor:  # (a player standing on the floor under a zone touches it: the zones and the floor line up)
		floor = data.navmesh.floor_near(zone.box.center[0], zone.box.center[1], zone.box.center[2], 3, 3)
		assert zone.box.center[1] - zone.box.size[1] / 2 - Z.PLAYER_HEIGHT <= floor <= zone.box.center[1] + zone.box.size[1] / 2
	assert M.imported(tmp_path) == ["Labyrinth"]
	objects = data.objects  # (every named object, without the copies models have for levels of detail)
	assert summary["Labyrinth"]["objects"] == len(objects) > 1000
	assert not any(name.endswith(("_LOD0", "_LOD1")) for name in objects.names)
	zone_object = next(z for z in data.zones if z["object"])
	assert objects.search(zone_object["object"])
