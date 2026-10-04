"""The trader list comes from the app's own data/traders.json, not from any trader folders."""

import json

from core.gamedata import GameData
from core.paths import BUNDLED_DATABASE_DIR, DATA_DIR

OWN = json.loads((DATA_DIR / "traders.json").read_text(encoding="utf-8"))


def test_the_trader_list_is_the_one_in_traders_json():
	traders = GameData(None, "en", BUNDLED_DATABASE_DIR).traders
	assert set(traders) == set(OWN.values()) and len(traders) == len(OWN)
	assert traders[OWN["Prapor"]] == "Prapor" and traders[OWN["Mechanic"]] == "Mechanic"


def test_a_traders_folder_is_never_read(tmp_path):
	folder = tmp_path / "database"
	(folder / "traders" / ("a" * 24)).mkdir(parents=True)
	(folder / "traders" / ("a" * 24) / "base.json").write_text(json.dumps({"nickname": "Modded"}), encoding="utf-8")
	(folder / "locales" / "global").mkdir(parents=True)
	(folder / "locales" / "global" / "en.json").write_text(json.dumps({("a" * 24) + " Nickname": "Modded"}), encoding="utf-8")
	data = GameData(folder, "en", BUNDLED_DATABASE_DIR)
	assert "a" * 24 not in data.traders and set(data.traders) == set(OWN.values())


def test_names_follow_the_chosen_language_when_the_locale_has_them(tmp_path):
	folder = tmp_path / "database"
	(folder / "locales" / "global").mkdir(parents=True)
	prapor = OWN["Prapor"]
	(folder / "locales" / "global" / "ru.json").write_text(json.dumps({f"{prapor} Nickname": "Праспор"}, ensure_ascii=False), encoding="utf-8")
	data = GameData(folder, "ru", BUNDLED_DATABASE_DIR)
	assert data.traders[prapor] == "Праспор"  # (the language's own name)
	assert data.traders[OWN["Therapist"]] == "Therapist"  # (no name in that locale: the name in traders.json)


def test_the_app_runs_with_no_trader_files_in_the_bundle():
	assert not (BUNDLED_DATABASE_DIR / "traders").exists()
	data = GameData(None, "en", BUNDLED_DATABASE_DIR)
	assert data.trader_name(OWN["Skier"]) and data.trader_name("0" * 24) == ""
