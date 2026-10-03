"""Shared test data: the base game's own files, which are known to be valid.

The quests, the English text and the quest locks come from the game data bundled with the app
(data/database, copied from SPT 4.0.13 by tools/bundle_database.py). The one trader assort
(Mechanic's, 589 offers) is a fixture, because the bundle leaves the big assort files out.
"""

import json
from pathlib import Path

import pytest

DATABASE = Path(__file__).resolve().parents[1] / "data" / "database"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
MECHANIC = "5a7c2eca46aef81a7ca2145d"


def _load(path):
	return json.loads(Path(path).read_bytes().decode("utf-8-sig"))


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
	return _load(DATABASE / "traders" / MECHANIC / "questassort.json")


@pytest.fixture(scope="session")
def vanilla_questassorts():
	"""Every trader's quest locks that the bundle has: {trader id: {started, success, fail}}."""
	return {path.parent.name: _load(path) for path in sorted((DATABASE / "traders").glob("*/questassort.json"))}
