"""Using the command line on another mod: project files written for a WTT-CommonLib mod (`project init`), what a
project takes from itself rather than from the app (game data, language, references), WTT custom items as
references, and `project show`. The mod is a small made-up one."""

import json

import pytest

from cli import main as cli_main
from cli.workspace import ProjectError, Workspace
from core import references as R

TRADER, OTHER, ITEM = "a" * 24, "b" * 24, "c" * 24


@pytest.fixture(autouse=True)
def plain_program(tmp_path, monkeypatch):
	"""The program's defaults, not the settings or saved items of the computer the tests run on."""
	monkeypatch.setattr("cli.workspace.Settings.load", classmethod(lambda cls, path=None: cls()))
	monkeypatch.setattr("core.library.LIBRARY_FILE", tmp_path / "no_items.json")


def _write(path, data):
	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_text(json.dumps(data), encoding="utf-8")
	return path


@pytest.fixture
def mod(tmp_path):
	"""A WTT-CommonLib mod with two traders' quests, a custom item, a zone file and one trader's base and assort."""
	root = tmp_path / "MyMod"
	quest = {"_id": "d" * 24, "QuestName": "Errand", "traderId": TRADER, "conditions": {}, "rewards": {}}
	_write(root / "db" / "CustomQuests" / TRADER / "Quests" / "quest_definitions.json", {"d" * 24: quest})
	_write(root / "db" / "CustomQuests" / TRADER / "Locales" / "en.json", {f"{'d' * 24} name": "Errand"})
	_write(root / "db" / "CustomQuests" / TRADER / "QuestAssort" / "assort.json", {"started": {}, "success": {}, "fail": {}})
	_write(root / "db" / "CustomQuests" / OTHER / "Quests" / "quests.json", {"e" * 24: dict(quest, _id="e" * 24, QuestName="Other", traderId=OTHER)})
	_write(root / "db" / "CustomItems" / "Questitems.json", {ITEM: {"itemTplToClone": "5ac620eb86f7743a8e6e0da0", "parentId": "5448ecbe4bdc2d60728b4568", "locales": {"en": {"name": "Wrapped Parcel", "shortName": "Parcel"}}}})
	_write(root / "db" / "CustomQuestZones" / "zones.json", [{"ZoneId": "z", "ZoneType": "visit", "ZoneLocation": "bigmap", "Position": {"X": "0", "Y": "0", "Z": "0"}, "Scale": {"X": "1", "Y": "1", "Z": "1"}}])
	_write(root / "data" / "aa-base.json", {"_id": TRADER, "nickname": "Courier", "currency": "RUB", "loyaltyLevels": []})
	_write(root / "data" / "aa-assort.json", {"items": [], "barter_scheme": {}, "loyal_level_items": {}})
	return root


def run(capsys, *argv):
	code = cli_main.main([str(a) for a in argv])
	return code, json.loads(capsys.readouterr().out)


def test_wtt_custom_items_are_references_with_their_names(mod):
	refs = R.References.of([mod / "db" / "CustomItems"])
	assert [r.kind for r in (R._read(f) for f in refs.files)] == [R.CUSTOM_ITEMS]
	assert refs.item_name(ITEM) == "Wrapped Parcel" and refs.knows_item(ITEM)
	assert refs.path is None
	refs.save()  # (a list given directly is kept in no file)


def test_project_init_writes_a_project_per_trader(mod, capsys, tmp_path):
	out_dir = mod / "projects"
	code, result = run(capsys, "project", "init", "--mod", mod, "--out", out_dir)
	assert code == 0 and not out_dir.exists() and "Courier" in result["notes"][0]
	by_file = {p["file"].rsplit("\\", 1)[-1].rsplit("/", 1)[-1]: p for p in result["projects"]}
	assert set(by_file) == {"project.courier.json", f"project.{OTHER}.json"}
	courier = by_file["project.courier.json"]["config"]
	assert courier["quests"] == f"../db/CustomQuests/{TRADER}/Quests/quest_definitions.json"  # (kept in the mod: relative)
	assert courier["assort"] == "../data/aa-assort.json" and courier["zones"] == "../db/CustomQuestZones/zones.json"
	assert f"../db/CustomQuests/{OTHER}/Quests/quests.json" in courier["references"] and "../db/CustomItems" in courier["references"]
	assert any("Locales/en.json" in n for n in by_file[f"project.{OTHER}.json"]["notes"])  # (it has no text file yet)
	code, result = run(capsys, "project", "init", "--mod", mod, "--out", out_dir, "--write")
	assert code == 0 and len(result["written"]) == 2
	code, result = run(capsys, "project", "init", "--mod", mod, "--out", out_dir, "--write")
	assert result["written"] == [] and len(result["kept"]) == 2
	elsewhere = tmp_path / "elsewhere"
	_code, result = run(capsys, "project", "init", "--mod", mod, "--out", elsewhere)
	assert result["projects"][0]["config"]["quests"].startswith(mod.resolve().as_posix())  # (kept outside the mod: absolute)
	code, result = run(capsys, "project", "init", "--mod", tmp_path / "empty", "--out", elsewhere)
	assert code == 1 and "--trader" in result["error"]


def test_a_project_uses_its_own_game_data_language_and_references(mod, capsys, tmp_path, monkeypatch):
	run(capsys, "project", "init", "--mod", mod, "--out", mod, "--write")
	project = mod / "project.courier.json"
	code, shown = run(capsys, "--project", project, "project", "show")
	assert code == 0 and shown["trader"] == TRADER and shown["files"]["quests"]["exists"]
	assert shown["references_from"] == "the project file" and shown["reference_kinds"] == {"quests": 1, "custom_items": 1, "trader": 1}
	assert shown["database"] == "bundled" and "bundled" in shown["database_from"]
	code, found = run(capsys, "--project", project, "find", "wrapped parcel", "--kind", "item")
	assert found[0]["id"] == ITEM
	code, found = run(capsys, "--project", project, "find", "Courier", "--kind", "trader")
	assert any(f["id"] == TRADER for f in found)
	game = tmp_path / "game"
	(game / "SPT_Runtime" / "SPT_Data" / "database").mkdir(parents=True)
	config = json.loads(project.read_text(encoding="utf-8"))
	project.write_text(json.dumps(dict(config, game=str(game), language="fr")), encoding="utf-8")
	ws = Workspace(project)
	assert ws.database == game / "SPT_Runtime" / "SPT_Data" / "database" and ws.database_from == "the game folder" and ws.language == "fr"
	project.write_text(json.dumps(dict(config, database=str(tmp_path / "nowhere"))), encoding="utf-8")
	with pytest.raises(ProjectError):
		Workspace(project)
	app_list = _write(tmp_path / "app_references.json", {"files": [str(mod / "db" / "CustomItems")]})
	monkeypatch.setattr("core.references.REFERENCES_FILE", app_list)
	project.write_text(json.dumps({k: v for k, v in config.items() if k != "references"}), encoding="utf-8")
	assert Workspace(project).sources()["references_from"].startswith("the app's reference list")
