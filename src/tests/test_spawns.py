"""Item spawn files (WTT-CommonLib's CustomLootspawns): reading and writing their entries, the map names WTT finds,
and the checks (maps.spawns). No Qt, no game files."""

import json
from types import SimpleNamespace

import pytest

from core import references as R
from maps import spawns as S

TPL = "5449016a4bdc2d6f028b456f"  # (Roubles in the game; here any id)


def _rtt2_entry():
	"""A forced spawn written as rtt2's files write theirs: Position in capitals, the locationId spaced, a Root that
	isn't the item's id."""
	return {
		"locationId": "(12.73149 1.813608 38.12542)",
		"probability": 1.0,
		"template": {
			"Id": "Q6 (Quest) [86663233-25bb-4e2a-a616-e67848115ac3]", "IsContainer": False, "useGravity": False, "randomRotation": False,
			"Position": {"X": 12.73149, "Y": 1.813608, "Z": 38.12542}, "Rotation": {"x": 0, "y": 0, "z": 0},
			"IsGroupPosition": False, "GroupPositions": [], "IsAlwaysSpawn": True, "Root": "67cd7b7345b0c8b5f47878ae",
			"Items": [{"_id": "69d190cef9d004063c3dd70a", "_tpl": "69b4d0c58cef59c5c553c4be", "upd": {"StackObjectsCount": 1}}],
		},
		"itemDistribution": [{"composedKey": {"key": "69b4d0c58cef59c5c553c4be"}, "relativeProbability": 1}],
	}


class _Floors:
	"""A floor map with the given heights everywhere (as maps.mapdata.Floors.floors_at gives them)."""

	def __init__(self, *heights):
		self.heights = sorted(heights)

	def floors_at(self, x, z):
		return list(self.heights)


def test_a_spawn_file_is_read_with_each_spawns_item_place_and_how_it_spawns():
	data = {"factory4_day": [_rtt2_entry()], "sandbox": []}
	assert S.is_spawn_file(data) and S.is_spawn_file({"sandbox": []}) and not S.is_spawn_file({"x": [1]}) and not S.is_spawn_file([])
	assert R.detect_kind(data) == R.SPAWNS
	(spawn,), broken = S.read_spawns(data, "factory4_day_forced.json", forced=True)
	assert broken == {}
	assert (spawn.map_name, spawn.index, spawn.location, spawn.item, spawn.count) == ("factory4_day", 0, "factory4_day", "69b4d0c58cef59c5c553c4be", 1)
	assert spawn.position == pytest.approx((12.73149, 1.813608, 38.12542)) and spawn.capitals
	assert spawn.forced and spawn.always and not spawn.gravity and spawn.source == "factory4_day_forced.json"
	loose = _rtt2_entry()
	loose["template"]["IsAlwaysSpawn"] = False
	loose["probability"] = 0.25
	(chance,), _ = S.read_spawns({"bigmap": [loose, {"template": {}}]}, forced=False)
	assert not chance.always and chance.probability == 0.25
	assert S.read_spawns({"bigmap": [loose, {"template": {}}]}, forced=False)[1] == {("bigmap", 1): "a number can't be read (Position is missing)"}


def test_a_files_folder_says_whether_its_spawns_are_forced():
	assert S.file_forced("C:/mod/db/CustomLootspawns/CustomSpawnpointsForced/x.json") is True
	assert S.file_forced("C:/mod/db/CustomLootspawns/customspawnpoints/sub/x.json") is False
	assert S.file_forced("C:/elsewhere/woods_forced.json") is True and S.file_forced("C:/elsewhere/x.json") is None and S.file_forced(None) is None


def test_a_new_spawn_is_written_as_the_games_own_are_and_reads_back_the_same():
	record = S.spawn_record(TPL, (1.23456, 0.1, -3.0), yaw=450, count=5, always=False, probability=0.3, name="Roubles")
	template = record["template"]
	assert record["locationId"] == "(1.2346, 0.1, -3)" and record["probability"] == 0.3
	assert template["Position"] == {"x": 1.2346, "y": 0.1, "z": -3} and template["Rotation"] == {"x": 0, "y": 90, "z": 0}
	assert template["Id"].startswith("Roubles [") and template["useGravity"] and not template["IsAlwaysSpawn"]
	(item,) = template["Items"]
	assert template["Root"] == item["_id"] == item["composedKey"] == record["itemDistribution"][0]["composedKey"]["key"]
	assert item["_tpl"] == TPL and item["upd"] == {"StackObjectsCount": 5}
	spawn = S.spawn_from_record(json.loads(json.dumps(record)), "bigmap", 0, forced=False)
	assert (spawn.item, spawn.count, spawn.yaw, spawn.probability, spawn.always, spawn.capitals) == (TPL, 5, 90, 0.3, False, False)
	assert S.check_spawn(spawn) == ([], [], [])
	again = S.spawn_record(TPL, (0, 0, 0))
	assert again["template"]["Id"] != S.spawn_record(TPL, (0, 0, 0))["template"]["Id"]  # (each its own spawn, not alternatives)


def test_a_change_keeps_the_rest_of_the_entry_and_writes_its_position_in_small_letters():
	old = _rtt2_entry()
	old["template"]["extra"] = {"kept": True}
	moved = S.changed_record(old, position=(1, 2, 3))
	assert moved["template"]["Position"] == {"x": 1, "y": 2, "z": 3} and moved["template"]["extra"] == {"kept": True}
	assert moved["locationId"] == old["locationId"]  # (written by hand, not its position: kept)
	assert old["template"]["Position"] == {"X": 12.73149, "Y": 1.813608, "Z": 38.12542}  # (the old entry is left as it was)
	counted = S.changed_record(old, count=3)
	assert counted["template"]["Position"] == {"x": 12.7315, "y": 1.8136, "z": 38.1254}  # (any change fixes the capitals)
	assert counted["template"]["Items"][0]["upd"] == {"StackObjectsCount": 3}
	new = S.spawn_record(TPL, (5, 0, 5))
	assert S.changed_record(new, position=(6, 0, 5))["locationId"] == "(6, 0, 5)"  # (its position: it follows)
	assert S.changed_record(new, yaw=-30)["template"]["Rotation"] == {"x": 0, "y": 330, "z": 0}
	gun = S.spawn_record(TPL, (0, 0, 0))
	gun["template"]["Items"].append({"_id": "child", "_tpl": "x", "parentId": gun["template"]["Root"], "slotId": "mod_magazine"})
	swapped = S.changed_record(gun, item="other")
	assert [i["_tpl"] for i in swapped["template"]["Items"]] == ["other"]  # (another item's parts don't fit it)
	assert S.changed_record(gun, count=2)["template"]["Items"][1]["_id"] == "child"


def test_the_map_names_wtt_finds():
	assert S.server_map("bigmap") == S.server_map("Bigmap") == "Bigmap" and S.server_map("SandboxHigh") == "SandboxHigh"
	assert S.server_map("Sandbox_high") is None and S.server_map("BigMap") is None  # (GetMappedKey knows exact names only)
	assert S.location_of("SandboxHigh") == S.location_of("sandbox_high") == S.location_of("Sandbox_high") == "Sandbox_high"
	assert S.location_of("TarkovStreets") == "TarkovStreets" and S.location_of("rezervbase") == "RezervBase"
	assert all(S.server_map(S.file_name_of(key)) for key in ("bigmap", "factory4_day", "Woods", "RezervBase", "TarkovStreets", "Sandbox_high", "Labyrinth"))
	data = {"TarkovStreets": [], "Sandbox_high": []}
	assert S.add_spawn(data, "TarkovStreets", {"a": 1}) == ("TarkovStreets", 0)  # (the name the file uses, which WTT finds)
	assert S.add_spawn(data, "Sandbox_high", {"b": 1}) == ("Sandbox_high", 0)  # (only that name for the map: kept, and checked)
	assert S.add_spawn(data, "bigmap", {"c": 1}) == ("bigmap", 0)


def _spawn(record=None, map_name="bigmap", index=0, source="", forced=True):
	return S.spawn_from_record(record or S.spawn_record(TPL, (5, 0.1, 5)), map_name, index, source, forced)


def test_the_checks_say_what_the_server_and_wtt_would_do_with_it():
	errors, warnings, _notes = S.check_spawn(_spawn(map_name="Sandbox_high"))
	assert errors == ["WTT won't find the map 'Sandbox_high': name it sandbox_high (the spawn is dropped otherwise)"]
	assert "small letters" in S.check_spawn(_spawn(_rtt2_entry(), "factory4_day"))[1][0]
	chance = S.spawn_record(TPL, (5, 0.1, 5), always=False, probability=0)
	chance["itemDistribution"] = [{"composedKey": {"key": "nothing"}, "relativeProbability": 1}]
	assert S.check_spawn(_spawn(chance, forced=False))[0] == [
		"No item of it is in its itemDistribution (by composedKey): the server finds nothing to spawn.", "Its probability is 0: it never spawns.",
	]
	empty = S.spawn_record("", (5, 0.1, 5))
	assert S.check_spawn(_spawn(empty))[0] == ["It has no item."]


def test_the_checks_know_quest_items_money_and_items_nobody_knows():
	gamedata = SimpleNamespace(
		items={TPL: {"_parent": S.MONEY, "_props": {}}, S.MONEY: {"_parent": ""}, "quest": {"_parent": "x", "_props": {"QuestItem": True}}},
		item_name=lambda tpl: {TPL: "Roubles"}.get(tpl, ""), knows_item=lambda tpl: tpl in (TPL, "quest", S.MONEY),
	)
	facts = S.ItemFacts(gamedata, {"custom": {"itemTplToClone": "quest", "parentId": S.MONEY}})
	assert facts.name(TPL) == "Roubles" and facts.name("custom") == "custom" and facts.is_quest_item("custom") and facts.is_under("custom", S.MONEY)
	money = _spawn(S.spawn_record(TPL, (5, 0.1, 5), count=500))
	assert S.check_spawn(money, items=facts)[2] == ["Money and ammo get a random stack from the server: the count isn't used."]
	by_chance = _spawn(S.spawn_record("quest", (5, 0.1, 5), always=False, probability=0.5), forced=False)
	assert "A quest item that spawns only by chance" in S.check_spawn(by_chance, items=facts)[1][0]
	assert S.check_spawn(_spawn(S.spawn_record("unknown", (5, 0.1, 5))), items=facts)[1] == ["The item unknown isn't one the game or your reference files know."]
	assert S.check_spawn(_spawn(S.spawn_record("custom", (5, 0.1, 5))), items=facts) == ([], [], [])


def test_two_spawns_at_one_locationid_clash_and_spawns_sharing_an_id_are_alternatives():
	mine = _spawn(source="mine.json")
	other = _spawn(S.spawn_record(TPL, (5, 0.1, 5)), source="theirs.json")
	assert mine.location_id == other.location_id
	assert "WTT keeps only the one it reads first" in S.check_spawn(mine, [mine, other])[0][0]
	loose = [_spawn(S.spawn_record(TPL, (5, 0.1, 5)), source=s, forced=False) for s in ("a.json", "b.json")]
	assert "WTT merges them into one point" in S.check_spawn(loose[0], loose)[1][0]
	moved = S.spawn_from_record(S.changed_record(mine.record, position=(9, 0.1, 9)), "bigmap", 0, "mine.json")
	assert S.check_spawn(moved, [mine]) == ([], [], [])  # (the same entry, moved: no clash with itself)
	twin = S.changed_record(S.spawn_record(TPL, (7, 0.1, 7)), spawn_id=mine.id)
	notes = S.check_spawn(mine, [mine, _spawn(twin, source="mine.json", index=1)])[2]
	assert notes == [f"2 spawns that come every raid have the id {mine.id}: the server spawns one of them each raid, picked by their probability."]


def test_the_floor_check_knows_items_that_hang_fall_or_sink():
	def warnings(y, *floors, gravity=True):
		record = S.spawn_record(TPL, (5, y, 5), gravity=gravity)
		return S.check_spawn(_spawn(record), floors=_Floors(*floors))[1]

	assert warnings(0.1, 0.0) == [] and warnings(0.1, 0.0, gravity=False) == []
	assert warnings(3.0, 0.0) == ["It falls 3.0 m to the floor under it."]
	assert warnings(1.0, 0.0, gravity=False) == ["It hangs 1.00 m above the floor (gravity is off, so it stays there)."]
	assert warnings(-0.3, 0.0) == ["It is 0.30 m under the floor."]
	assert warnings(0.1, 0.0, 0.5, gravity=False) == []  # (on the floor, under a table: fine)
	assert warnings(0.1) == ["No floor is mapped under it. It may fall through the map."]
