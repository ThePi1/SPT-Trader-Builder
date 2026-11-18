"""The command line (python -m cli): quest specs built into quest JSON and back, the project's files, the checks, and
the zone commands. It runs with the program's default settings and no reference or saved items."""

import copy
import gzip
import json

import pytest

from cli import main as cli_main
from cli import spec as S
from cli.workspace import Workspace
from maps import mapdata as M
from core.settings import Settings

BOLTS, ROUBLES, PRAPOR, MARKER = "57347c5b245977448d35f6e1", "5449016a4bdc2d6f028b456f", "54cb50c76803fa8b248b4571", "5991b51486f77447b112d44f"


@pytest.fixture(autouse=True)
def plain_program(tmp_path, monkeypatch):
	"""The program's defaults, not the settings, saved items or maps of the computer the tests run on."""
	monkeypatch.setattr("cli.workspace.Settings.load", classmethod(lambda cls, path=None: cls()))
	monkeypatch.setattr("core.library.LIBRARY_FILE", tmp_path / "no_items.json")


@pytest.fixture
def project(tmp_path):
	path = tmp_path / "project.json"
	path.write_text(json.dumps({
		"quests": "quests.json", "locale": "en.json", "assort": "assort.json", "questassort": "questassort.json",
		"trader": "Prapor", "zones": "zones/new.json",
	}), encoding="utf-8")
	return path


@pytest.fixture
def maps(tmp_path):
	"""A made-up imported Customs: a 40 x 40 m floor at 1 m, one game visit zone and one placeitem zone."""
	folder = tmp_path / "maps"
	folder.mkdir()
	(folder / "bigmap.json").write_text(json.dumps({"format": M.FORMAT, "location": "bigmap", "areas": [], "zones": [
		{"id": "game_room", "kind": "visit", "class": "ExperienceTrigger", "object": "x", "active": True, "scene": "s", "boxes": [{"center": [5, 2, 5], "size": [4, 3, 4], "rotation": [0, 0, 0, 1]}]},
		{"id": "game_mark", "kind": "placeitem", "class": "PlaceItemTrigger", "object": "x", "active": True, "scene": "s", "boxes": [{"center": [30, 2, 30], "size": [2, 3, 2], "rotation": [0, 0, 0, 1]}]},
	]}), encoding="utf-8")
	with gzip.open(folder / f"bigmap{M.NAVMESH_SUFFIX}", "wt", encoding="utf-8") as f:
		json.dump({"format": M.FORMAT, "vertices": [0, 1, 0, 40, 1, 0, 40, 1, 40, 0, 1, 40], "polygons": [[0, 1, 2, 3]]}, f)
	return folder


def run(capsys, *argv):
	code = cli_main.main([str(a) for a in argv])
	return code, json.loads(capsys.readouterr().out)


SUPPLY_RUN = {
	"name": "Supply run",
	"trader": "Prapor",
	"location": "Customs",
	"text": {"description": "Bring me bolts.", "successMessageText": "Thanks."},
	"start": [{"kind": "Level", "value": 5}],
	"finish": [
		{"kind": "HandoverItem", "target": ["Bolts"], "value": 5, "onlyFoundInRaid": True, "text": "auto"},
		{"kind": "CounterCreator", "type": "Elimination", "value": 3, "text": "Kill Scavs on Customs",
			"conditions": [{"kind": "Kills", "target": "Scavs", "distance": 50}, {"kind": "Location", "target": ["Customs"]}]},
	],
	"rewards": {"success": [
		{"kind": "Experience", "value": 5000},
		{"kind": "Item", "items": [{"item": "Roubles", "count": 20000}, {"item": "Bolts", "count": 2}]},
		{"kind": "AssortmentUnlock", "item": "Bolts", "price": 12000, "loyaltyLevel": 2},
	]},
}


# --- building quests from specs ---------------------------------------------------------------------------

def test_every_vanilla_quest_is_described_and_built_again_unchanged():
	ws = Workspace(settings=Settings())
	vanilla = ws.gamedata.vanilla_quests
	ws.quests.data.update(copy.deepcopy(vanilla))
	resolver = S.Resolver(ws)
	for quest_id, quest in vanilla.items():
		spec = json.loads(json.dumps(S.describe_quest(quest, ws)))
		built, _texts, _locks = S.build_quest(spec, ws, resolver, quest_id)
		assert built == quest, quest["QuestName"]


def test_a_spec_names_things_and_the_quest_gets_their_ids(project):
	ws = Workspace(project)
	quest, texts, locks = S.build_quest(SUPPLY_RUN, ws, S.Resolver(ws))
	assert quest["traderId"] == PRAPOR and quest["location"] == "56f40101d2720b2a4d8b45d6"
	hand_over, counter = quest["conditions"]["AvailableForFinish"]
	assert hand_over["target"] == [BOLTS] and texts[hand_over["id"]] == "Hand over Bolts"
	kills, location = counter["counter"]["conditions"]
	assert kills["target"] == "Savage" and kills["distance"] == {"compareMethod": ">=", "value": 50}
	assert location["target"] == ["bigmap"]  # (Location conditions name the map by key: the game compares that)
	experience, items, unlock = quest["rewards"]["Success"]
	assert items["value"] == 20002 and items["target"] == items["items"][0]["_id"]
	assert items["items"][0]["upd"] == {"StackObjectsCount": 20000} and items["items"][1]["upd"] == {"SpawnedInSession": True, "StackObjectsCount": 2}
	offer = locks[0][1]
	assert locks == [("success", offer, quest["_id"])] and unlock["loyaltyLevel"] == 2 and unlock["items"][0]["_tpl"] == BOLTS
	assert ws.assort.data["barter_scheme"][offer] == [[{"count": 12000, "_tpl": ROUBLES}]] and ws.assort.data["loyal_level_items"][offer] == 2


def test_every_problem_in_a_spec_is_reported_at_once(project):
	ws = Workspace(project)
	spec = {
		"name": "Broken",
		"color": "red",
		"finish": [
			{"kind": "Teleport"},
			{"kind": "HandoverItem", "target": ["Drawer"], "value": "five"},
			{"kind": "FindItem", "target": ["No such thing at all"], "colour": 1},
			{"kind": "CounterCreator", "conditions": [{"kind": "Location", "target": ["Atlantis"]}]},
		],
		"rewards": {"later": [], "success": [{"kind": "Item", "items": [{"item": "Bolts", "count": 0}]}]},
	}
	with pytest.raises(S.SpecError) as raised:
		S.build_quest(spec, ws, S.Resolver(ws))
	text = "\n".join(raised.value.problems)
	for expected in ("color", "Teleport", "is the name of 2 items", "value: must be a whole number", "no item is called 'No such thing at all'",
	                 "'colour' isn't a key of FindItem", "Atlantis' isn't a map", "rewards.later", "count: must be a whole number"):
		assert expected in text, expected


def test_quests_in_one_spec_can_point_at_each_other_by_name(project):
	ws = Workspace(project)
	resolver = S.Resolver(ws, batch=[("a" * 24, "First"), ("b" * 24, "Second")])
	second, _t, _l = S.build_quest({"name": "Second", "trader": "Prapor", "start": [{"kind": "Quest", "target": "First", "status": ["Completed"]}]}, ws, resolver, "b" * 24)
	assert second["conditions"]["AvailableForStart"][0]["target"] == "a" * 24 and second["conditions"]["AvailableForStart"][0]["status"] == [4]


# --- the commands -----------------------------------------------------------------------------------------

def test_quest_add_only_writes_with_write(project, capsys, tmp_path):
	spec = tmp_path / "spec.json"
	spec.write_text(json.dumps(SUPPLY_RUN), encoding="utf-8")
	code, result = run(capsys, "--project", project, "quest", "add", spec)
	assert code == 0 and result["written"] == [] and not (tmp_path / "quests.json").exists()
	code, result = run(capsys, "--project", project, "quest", "add", spec, "--write")
	quest_id = result["quests"][0]["id"]
	assert code == 0 and len(result["written"]) == 4 and result["locks"][0]["quest"] == quest_id
	quests = json.loads((tmp_path / "quests.json").read_text(encoding="utf-8"))
	locale = json.loads((tmp_path / "en.json").read_text(encoding="utf-8"))
	assert quest_id in quests and locale[f"{quest_id} name"] == "Supply run" and locale[f"{quest_id} description"] == "Bring me bolts."
	assert json.loads((tmp_path / "questassort.json").read_text(encoding="utf-8"))["success"] == {result["locks"][0]["offer"]: quest_id}


def test_show_then_update_changes_a_quest_in_place(project, capsys, tmp_path):
	spec = tmp_path / "spec.json"
	spec.write_text(json.dumps(SUPPLY_RUN), encoding="utf-8")
	_code, added = run(capsys, "--project", project, "quest", "add", spec, "--write")
	quest_id = added["quests"][0]["id"]
	_code, shown = run(capsys, "--project", project, "quest", "show", "Supply run")
	assert shown["id"] == quest_id and shown["names"][BOLTS] == "Bolts" and shown["rewards"]["success"][2]["offer"] == added["locks"][0]["offer"]
	shown["finish"][0]["value"] = 8
	shown["text"]["description"] = "Bring me more bolts."
	spec.write_text(json.dumps(shown), encoding="utf-8")
	code, result = run(capsys, "--project", project, "quest", "update", spec, "--write")
	assert code == 0, result
	quests = json.loads((tmp_path / "quests.json").read_text(encoding="utf-8"))
	assert list(quests) == [quest_id] and quests[quest_id]["conditions"]["AvailableForFinish"][0]["value"] == 8
	assert json.loads((tmp_path / "en.json").read_text(encoding="utf-8"))[f"{quest_id} description"] == "Bring me more bolts."
	assert len(json.loads((tmp_path / "assort.json").read_text(encoding="utf-8"))["items"]) == 1  # (the offer isn't made twice)
	code, result = run(capsys, "--project", project, "quest", "add", spec)
	assert code == 1 and "already" in result["error"]


def test_a_spec_with_problems_changes_nothing(project, capsys, tmp_path):
	spec = tmp_path / "spec.json"
	spec.write_text(json.dumps({"name": "x", "finish": [{"kind": "Nope"}]}), encoding="utf-8")
	code, result = run(capsys, "--project", project, "quest", "add", spec, "--write")
	assert code == 1 and "nothing was changed" in result["error"] and any("Nope" in p for p in result["problems"])
	assert not (tmp_path / "quests.json").exists()


def test_quest_remove_takes_its_text_and_locks(project, capsys, tmp_path):
	spec = tmp_path / "spec.json"
	spec.write_text(json.dumps(SUPPLY_RUN), encoding="utf-8")
	_code, added = run(capsys, "--project", project, "quest", "add", spec, "--write")
	code, result = run(capsys, "--project", project, "quest", "remove", "Supply run", "--text", "--write")
	assert code == 0 and result["locks"] and result["text"]
	assert json.loads((tmp_path / "quests.json").read_text(encoding="utf-8")) == {}
	assert json.loads((tmp_path / "questassort.json").read_text(encoding="utf-8"))["success"] == {}


def test_find_and_kinds(project, capsys):
	_code, found = run(capsys, "--project", project, "find", "bolts", "--kind", "item")
	assert found[0]["id"] == BOLTS
	_code, kinds = run(capsys, "--project", project, "kinds", "task", "PlaceBeacon")
	assert kinds["zones"]["key"] == "zoneId" and "placeitem" in kinds["zones"]["needs"]
	assert any(f["key"] == "plantTime" for f in kinds["fields"])


def test_check_finds_zones_of_the_wrong_kind_and_broken_zone_files(project, capsys, tmp_path, maps):
	(tmp_path / "zones").mkdir()
	(tmp_path / "zones" / "new.json").write_text(json.dumps([{"ZoneId": "bad", "ZoneType": "visit"}]), encoding="utf-8")
	spec = tmp_path / "spec.json"
	spec.write_text(json.dumps({"name": "Zones", "trader": "Prapor", "text": {"description": "d", "successMessageText": "s"}, "finish": [
		{"kind": "CounterCreator", "type": "Exploration", "text": "Be in it", "conditions": [{"kind": "InZone", "zoneIds": ["game_mark"]}]},
		{"kind": "PlaceBeacon", "zoneId": "game_mark", "text": "Mark it"},
	]}), encoding="utf-8")
	run(capsys, "--project", project, "--maps", maps, "quest", "add", spec, "--write")
	code, result = run(capsys, "--project", project, "--maps", maps, "check", "--strict")
	assert code == 1 and result["summary"]["maps_imported"] == ["bigmap"]
	errors = [p for p in result["problems"] if p["level"] == "error"]
	assert any("game_mark" in p["message"] and "placeitem" in p["message"] for p in errors)
	assert any(p["file"] == "new.json" for p in errors)  # (the zone entry with no position)
	assert not any("PlaceBeacon" in p.get("where", "") for p in errors)


def test_zones_make_puts_a_checked_zone_on_the_floor_and_into_the_projects_file(project, capsys, tmp_path, maps):
	code, result = run(capsys, "--project", project, "--maps", maps, "zones", "make", "--map", "Customs", "--id", "my_mark", "--kind", "placeitem",
	                   "--at", "20,20", "--size", "3,2,3", "--yaw", "15", "--write", "--picture", tmp_path / "zone.png")
	assert code == 0 and result["errors"] == [] and result["warnings"] == []
	zone = result["zone"]
	assert zone["ZoneLocation"] == "bigmap" and float(zone["Position"]["Y"]) == pytest.approx(1 - 0.25 + 1)
	saved = json.loads((tmp_path / "zones" / "new.json").read_text(encoding="utf-8"))
	assert [z["ZoneId"] for z in saved] == ["my_mark"] and (tmp_path / "zone.png").stat().st_size > 1000
	code, result = run(capsys, "--project", project, "--maps", maps, "zones", "make", "--map", "bigmap", "--id", "over", "--kind", "placeitem", "--at", "30,30")
	assert code == 0 and "game_mark" in result["warnings"][0]  # (placeitem zones on top of each other)
	code, result = run(capsys, "--project", project, "--maps", maps, "zones", "check")
	assert code == 0 and result["results"] == []
	code, result = run(capsys, "--project", project, "--maps", maps, "zones", "at", "--map", "bigmap", "5,5")
	assert result["floors"] == [1.0] and [z["id"] for z in result["inside"]] == ["game_room"]
	code, result = run(capsys, "--project", project, "--maps", maps, "zones", "list", "--map", "bigmap", "--source", "custom")
	assert [z["id"] for z in result] == ["my_mark"]



def test_show_can_write_the_spec_to_a_file_that_update_reads(project, capsys, tmp_path):
	spec = tmp_path / "spec.json"
	spec.write_text(json.dumps(dict(SUPPLY_RUN, text={"name": "Ration de survie", "description": "Été", "successMessageText": "Merci."})), encoding="utf-8")
	run(capsys, "--project", project, "quest", "add", spec, "--write")
	shown = tmp_path / "shown.json"
	code, result = run(capsys, "--project", project, "quest", "show", "Supply run", "--out", shown)
	assert code == 0 and result["written"] == str(shown.resolve())
	assert json.loads(shown.read_text(encoding="utf-8"))["text"]["description"] == "Été"
	code, result = run(capsys, "--project", project, "quest", "update", shown)
	assert code == 0 and result["problems"] == []


def test_maps_verify_checks_the_game_quests_against_the_imported_maps(capsys, maps):
	code, result = run(capsys, "--maps", maps, "maps", "verify")
	assert code == 0 and result["maps"] == ["bigmap"] and result["zone_uses"] > 400
	assert any("No map or zone file has a zone" in p["message"] for p in result["problems"])
	code, result = run(capsys, "--maps", maps.parent / "nothing", "maps", "verify")
	assert code == 1 and "maps import" in result["error"]


def test_show_also_reads_base_game_quests_to_learn_from(project, capsys):
	code, shown = run(capsys, "--project", project, "quest", "show", "Debut")
	assert code == 0 and shown["from"] == "the base game" and shown["text"]["name"] == "Debut"
	assert shown["finish"][0]["kind"] == "CounterCreator" and shown["names"][PRAPOR] == "Prapor"
	code, result = run(capsys, "--project", project, "quest", "show", "No such quest at all")
	assert code == 1 and "base game" in result["error"]


# --- shorthands, money, usage, packaging, the server check -------------------------------------------------

def test_shorthands_write_the_base_games_patterns_and_after_names_conditions(project):
	ws = Workspace(project)
	spec = {"name": "Patrol", "trader": "Prapor", "location": "Woods", "finish": [
		{"kind": "Visit", "ref": "seen", "zone": "my_place", "text": "Find it"},
		{"kind": "Kill", "ref": "kills", "count": 3, "target": "Any PMC", "zone": "my_place", "distance": 40, "after": "seen", "text": "Kill"},
		{"kind": "SurviveAndExtract", "after": ["seen", "kills"]},
		{"kind": "HandoverItem", "target": ["Bolts"], "value": 1, "after": ["kills"], "text": "auto"},
	]}
	quest, texts, _locks = S.build_quest(spec, ws, S.Resolver(ws))
	visit, kill, survive, hand_over = quest["conditions"]["AvailableForFinish"]
	assert visit["conditionType"] == "CounterCreator" and visit["type"] == "Exploration" and visit["value"] == 1
	assert [(s["conditionType"], s.get("target")) for s in visit["counter"]["conditions"]] == [("VisitPlace", "my_place")]
	assert kill["type"] == "Elimination" and kill["value"] == 3
	kills, inside, location = kill["counter"]["conditions"]
	assert kills["target"] == "AnyPmc" and kills["distance"] == {"compareMethod": ">=", "value": 40}
	assert inside["zoneIds"] == ["my_place"] and location["target"] == ["Woods"]  # (the quest's map)
	assert [v["target"] for v in kill["visibilityConditions"]] == [visit["id"]]
	assert survive["type"] == "Completion" and texts[survive["id"]] == "Survive and extract from the location"
	assert [s["conditionType"] for s in survive["counter"]["conditions"]] == ["ExitStatus", "Location"]
	assert survive["counter"]["conditions"][0]["status"] == ["Survived", "Transit"]
	assert [v["target"] for v in survive["visibilityConditions"]] == [visit["id"], kill["id"]]
	assert [v["target"] for v in hand_over["visibilityConditions"]] == [kill["id"]]
	with pytest.raises(S.SpecError) as raised:
		S.build_quest({"name": "x", "trader": "Prapor", "finish": [
			{"kind": "Visit"}, {"kind": "Kill", "colour": 1}, {"kind": "Level", "value": 2, "after": "nope"},
			{"kind": "Visit", "zone": "a", "ref": "same"}, {"kind": "Visit", "zone": "b", "ref": "same"},
		]}, ws, S.Resolver(ws))
	text = "\n".join(raised.value.problems)
	for expected in ('a Visit needs "zone"', "colour isn't a key of a Kill", "no condition has the ref 'nope'", "'same' names two conditions"):
		assert expected in text, expected


def test_money_rewards_are_not_found_in_raid_unless_asked(project):
	ws = Workspace(project)
	spec = {"name": "Pay", "trader": "Prapor", "rewards": {"success": [
		{"kind": "Item", "items": [{"item": "Roubles", "count": 1000}]},
		{"kind": "Item", "items": [{"item": "Dollars", "count": 10}], "findInRaid": True},
		{"kind": "Item", "items": [{"item": "Bolts", "count": 1}]},
	]}}
	quest, _t, _l = S.build_quest(spec, ws, S.Resolver(ws))
	assert [r["findInRaid"] for r in quest["rewards"]["Success"]] == [False, True, True]
	assert quest["rewards"]["Success"][1]["items"][0]["_tpl"] == "5696686a4bdc2da3298b456a"  # (the game's dollars)
	described = S.describe_quest(quest, ws)["rewards"]["success"]
	assert "findInRaid" not in described[0] and described[1]["findInRaid"] is True
	again, _t, _l = S.build_quest(json.loads(json.dumps(S.describe_quest(quest, ws))), ws, S.Resolver(ws), quest["_id"])
	assert again == quest


def test_usage_tells_how_the_base_game_fills_a_field(capsys):
	code, result = run(capsys, "usage", "subtask", "ExitStatus", "status")
	assert code == 0 and result["top"][0]["value"] == ["Survived", "Transit"] and result["top"][0]["examples"]
	code, result = run(capsys, "usage", "task", "CounterCreator", "type", "--where", 'steps=["ExitStatus", "Location"]')
	assert result["top"][0]["value"] == "Completion"
	code, result = run(capsys, "usage", "reward", "Item", "findInRaid", "--where", "money=true")
	assert result["top"][0]["value"] is False
	code, result = run(capsys, "usage", "task", "FindItem", "target", "--limit", "1")
	assert result["top"][0]["names"]
	code, result = run(capsys, "usage", "subtask", "Kills")
	assert code == 0 and "savageRole" in result["fields"] and result["found"] > 100
	code, result = run(capsys, "usage", "subtask", "Teleport")
	assert code == 1


def test_kinds_lists_the_shorthands(capsys):
	_code, kinds = run(capsys, "kinds")
	assert [k["kind"] for k in kinds["shorthand"]] == ["Visit", "Kill", "SurviveAndExtract"]
	_code, kill = run(capsys, "kinds", "shorthand", "Kill")
	assert "zone" in kill["keys"] and "after" in kill["keys"]


def test_package_writes_the_layout_wtt_reads(project, capsys, tmp_path, maps):
	(tmp_path / "zones").mkdir()
	zone = {"ZoneId": "my_mark", "ZoneName": "my_mark", "ZoneLocation": "bigmap", "ZoneType": "placeitem", "FlareType": "",
	        "Position": {"X": "20", "Y": "1.5", "Z": "20", "W": "0"}, "Rotation": {"X": "0", "Y": "0", "Z": "0", "W": "1"}, "Scale": {"X": "2", "Y": "2", "Z": "2", "W": "0"}}
	(tmp_path / "zones" / "new.json").write_text(json.dumps([zone]), encoding="utf-8")
	spec = tmp_path / "spec.json"
	spec.write_text(json.dumps(dict(SUPPLY_RUN, finish=SUPPLY_RUN["finish"] + [{"kind": "PlaceBeacon", "zoneId": "my_mark", "text": "Mark it"}])), encoding="utf-8")
	_code, added = run(capsys, "--project", project, "--maps", maps, "quest", "add", spec, "--write")
	quest_id = added["quests"][0]["id"]
	out_dir = tmp_path / "mod"
	code, result = run(capsys, "--project", project, "--maps", maps, "package", "--out", out_dir)
	assert code == 0 and not out_dir.exists() and result["zones"] == ["my_mark"]
	code, result = run(capsys, "--project", project, "--maps", maps, "package", "--out", out_dir, "--write")
	trader = out_dir / "db" / "CustomQuests" / PRAPOR
	assert code == 0 and result["written"] and any("offers" in n for n in result["notes"])
	assert list(json.loads((trader / "Quests" / "quests.json").read_text(encoding="utf-8"))) == [quest_id]
	assert json.loads((trader / "Locales" / "en.json").read_text(encoding="utf-8"))[f"{quest_id} name"] == "Supply run"
	assert json.loads((trader / "QuestAssort" / "quests.json").read_text(encoding="utf-8"))["success"] == {added["locks"][0]["offer"]: quest_id}
	assert json.loads((out_dir / "db" / "CustomQuestZones" / "quests.json").read_text(encoding="utf-8")) == [zone]


def test_the_server_check_is_found_run_and_read(project, capsys, tmp_path, monkeypatch):
	from cli import servercheck

	runtime = tmp_path / "SPT" / "SPT_Runtime"
	runtime.mkdir(parents=True)
	(runtime / servercheck.CORE_DLL).write_bytes(b"")
	monkeypatch.delenv("SPT_RUNTIME", raising=False)
	ws = Workspace(project)
	assert servercheck.find_runtime(ws) is None
	assert servercheck.find_runtime(ws, tmp_path / "SPT") == runtime and servercheck.find_runtime(ws, runtime) == runtime
	report = servercheck.parse('building...\n{"ok": true, "quests": 2, "dropped": ["q.x = 1"], "changed": [], "unknown": ["q.extra"]}\n')
	assert report["quests"] == 2
	assert [p["level"] for p in servercheck.problems(report)] == ["error", "warning"]
	assert servercheck.parse("error CS1002: ; expected", "", 1)["ok"] is False
	spec = tmp_path / "spec.json"
	spec.write_text(json.dumps(SUPPLY_RUN), encoding="utf-8")
	run(capsys, "--project", project, "quest", "add", spec, "--write")
	code, result = run(capsys, "--project", project, "check", "--server")
	assert code == 1 and "SPT_Runtime" in result["error"]
	monkeypatch.setattr(servercheck, "run", lambda q, l, r: {"ok": True, "quests": 1, "dropped": [], "changed": ["q.value: 1 -> 2"], "unknown": []})
	code, result = run(capsys, "--project", project, "check", "--server", "--spt", runtime)
	assert result["summary"]["server"]["ok"] and any(p["file"] == "server" and "differently" in p["message"] for p in result["problems"])
