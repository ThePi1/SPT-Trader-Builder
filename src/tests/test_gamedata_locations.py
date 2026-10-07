"""The map list: the game calls both Factory maps 'Factory', so they must be told apart."""

from core.gamedata import GameData
from core.paths import BUNDLED_DATABASE_DIR
from schema import choices

DAY, NIGHT = "55f2d3fd4bdc2d5f408b4567", "59fc81d786f774390775787e"


def test_the_two_factory_maps_have_names_that_tell_them_apart():
	locations = GameData(None, "en", BUNDLED_DATABASE_DIR).locations
	assert locations[DAY] == "Factory (day)" and locations[NIGHT] == "Factory (night)"
	assert locations["56f40101d2720b2a4d8b45d6"] == "Customs" and locations["any"] == "Any"  # (the others keep the game's name)
	assert len(set(locations.values())) == len(locations)  # (no two maps share a name)


def test_the_map_choices_and_labels_use_those_names():
	data = GameData(None, "en", BUNDLED_DATABASE_DIR)
	assert choices.label_of("locations", NIGHT, data) == "Factory (night)"
	assert (DAY, "Factory (day)") in choices.get("locations", data)


def test_the_outline_says_the_name_of_the_map_not_its_id():
	from schema import registry
	from schema.common import PLAIN, Names

	task = registry.new_item("subtask", "Location")
	task["target"] = [DAY, NIGHT, "custom-map"]
	spec = registry.spec_of(task, "subtask")
	data = GameData(None, "en", BUNDLED_DATABASE_DIR)
	assert spec.summary(task, Names(data)) == "On Factory (day), Factory (night), custom-map"  # (a map nobody knows keeps what the file says)
	assert spec.summary(task, PLAIN) == f"On {DAY}, {NIGHT}, custom-map"  # (no game data: the ids)
