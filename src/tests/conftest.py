"""Shared test data: the base game's own files, which are known to be valid.

The quests and the English text come from the game data bundled with the app (data/database,
copied from SPT 4.0.13 by tools/bundle_database.py). The trader files are fixtures: Mechanic's assort
(589 offers) and every trader's quest locks (tests/fixtures/questassort), because the bundle does not
hold the trader folders.
"""

import json
from pathlib import Path

import pytest

DATABASE = Path(__file__).resolve().parents[1] / "data" / "database"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
MECHANIC = "5a7c2eca46aef81a7ca2145d"


def _load(path):
	return json.loads(Path(path).read_bytes().decode("utf-8-sig"))


@pytest.fixture(autouse=True)
def no_real_reference_files(tmp_path, monkeypatch):
	"""The reference files the user has added to the program are not part of any test: every test starts with none."""
	monkeypatch.setattr("core.references.REFERENCES_FILE", tmp_path / "no_references.json")


@pytest.fixture(scope="session")
def vanilla_quests():
	return _load(DATABASE / "templates" / "quests.json")


@pytest.fixture(scope="session")
def vanilla_locale():
	return _load(DATABASE / "locales" / "global" / "en.json")


@pytest.fixture(scope="session")
def vanilla_assort():
	return _load(FIXTURES / "assort_mechanic.json")


@pytest.fixture(scope="session")
def vanilla_questassort():
	"""Mechanic's quest locks: {started, success, fail: {offer id: quest id}}."""
	return _load(FIXTURES / "questassort" / f"{MECHANIC}.json")


@pytest.fixture(scope="session")
def vanilla_questassorts():
	"""Every trader's quest locks in tests/fixtures/questassort: {trader id: {started, success, fail}}."""
	return {path.stem: _load(path) for path in sorted((FIXTURES / "questassort").glob("*.json"))}
