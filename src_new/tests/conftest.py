import json
import os
from pathlib import Path

import pytest

# Where the base game's data is, for the tests that check against it. Set SPT_SAMPLES to a folder
# holding quests.json and en.json (and optionally assort.json / questassort.json); tests that
# need them are skipped when they can't be found.
_CANDIDATES = [
	os.environ.get("SPT_SAMPLES"),
	str(Path(__file__).resolve().parents[2] / "local_dev" / "samples"),
	"/mnt/user-data/uploads/SPT-Trader-Builder/local_dev/samples",
]


def _samples_dir():
	for candidate in _CANDIDATES:
		if candidate and (Path(candidate) / "quests.json").is_file():
			return Path(candidate)
	return None


def _load(name):
	folder = _samples_dir()
	if folder is None or not (folder / name).is_file():
		pytest.skip(f"sample {name} not found (set SPT_SAMPLES)")
	return json.loads((folder / name).read_bytes().decode("utf-8-sig"))


@pytest.fixture(scope="session")
def vanilla_quests():
	return _load("quests.json")


@pytest.fixture(scope="session")
def vanilla_locale():
	return _load("en.json")


@pytest.fixture(scope="session")
def vanilla_assort():
	return _load("assort.json")
