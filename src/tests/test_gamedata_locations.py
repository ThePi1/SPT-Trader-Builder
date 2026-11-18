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


def test_location_conditions_name_maps_by_key():
	"""The game compares a Location condition's targets with the raid's map key (bigmap), so that is what the field offers."""
	from schema import registry

	data = GameData(None, "en", BUNDLED_DATABASE_DIR)
	keys = dict(choices.get("map_keys", data))
	assert keys["bigmap"] == "Customs" and keys["factory4_night"] == "Factory (night)"
	assert keys["Sandbox"] != keys["Sandbox_high"]  # (one map, two keys)
	assert registry.spec_for("subtask", "Location").field("target").choices == "map_keys"


def test_a_location_condition_with_a_map_id_is_an_error():
	from schema import registry, validate
	from schema.issues import ERROR

	task = registry.new_item("task", "CounterCreator")
	for kind, target in (("Kills", None), ("Location", ["56f40101d2720b2a4d8b45d6", "bigmap"])):
		sub = registry.new_item("subtask", kind)
		if target:
			sub["target"] = target
		task["counter"]["conditions"].append(sub)
	quest = {"_id": "q1", "QuestName": "Test", "conditions": {"AvailableForFinish": [task], "AvailableForStart": [], "Fail": []}, "rewards": {}}
	issues = [i for i in validate.validate_quests({"q1": quest}) if i.path[-1:] == ("target",)]
	assert len(issues) == 1 and issues[0].level == ERROR and "'bigmap'" in issues[0].message
	sandbox = dict(quest)
	task["counter"]["conditions"][1]["target"] = ["653e6760052c01c1c805532f"]
	message = [i for i in validate.validate_quests({"q1": sandbox}) if i.path[-1:] == ("target",)][0].message
	assert "'Sandbox' or 'Sandbox_high'" in message
