"""The builders are plain functions: no Qt, no windows, no files."""

import json
import subprocess
import sys

import pytest

from builders import assort, conditions, locale, quests, rewards
from conftest import GOLDEN, SRC


def test_builders_do_not_import_qt():
	code = (
		"import builders.assort, builders.conditions, builders.locale, "
		"builders.quests, builders.rewards, sys; "
		"assert not any(m.startswith('PySide6') for m in sys.modules)"
	)
	subprocess.run([sys.executable, "-c", code], cwd=SRC, check=True)


# --- conditions ---------------------------------------------------------------------


def test_visit_place():
	assert conditions.visit_place("c1", "zone") == {
		"conditionType": "VisitPlace",
		"dynamicLocale": False,
		"globalQuestCounterId": "",
		"id": "c1",
		"target": "zone",
		"value": 1,
	}


def _kills(**overrides):
	args = dict(
		weapon_ids=["w1"],
		target="Savage",
		target_roles=["bossBully"],
		body_parts=["Head"],
		mods_inclusive=["m1", "m2"],
		mods_exclusive=["m3"],
		distance=50,
		distance_compare=">=",
		time_from=1,
		time_to=2,
		reset_on_session_end=True,
	)
	args.update(overrides)
	return conditions.kills("k1", **args)


def test_kills_wraps_each_mod_in_its_own_list():
	cond = _kills()
	assert cond["weaponModsInclusive"] == [["m1"], ["m2"]]
	assert cond["weaponModsExclusive"] == [["m3"]]
	assert cond["distance"] == {"compareMethod": ">=", "distance": 50}
	assert cond["daytime"] == {"from": 1, "to": 2}
	assert cond["weapon"] == ["w1"] and cond["savageRole"] == ["bossBully"]


def test_shots_uses_value_for_distance_and_does_not_wrap_mods():
	cond = conditions.shots(
		"s1",
		weapon_ids=["w1"],
		body_parts=[],
		target_roles=[],
		mods_inclusive=["m1"],
		mods_exclusive=[],
		distance=10,
		distance_compare="<=",
		time_from=0,
		time_to=0,
		value=5,
		target="Any",
		reset_on_session_end=False,
	)
	assert cond["distance"] == {"compareMethod": "<=", "value": 10}
	assert cond["weaponModsInclusive"] == ["m1"]
	assert cond["value"] == 5 and cond["conditionType"] == "Shots"
	assert cond["weapon"] == ["w1"]


def test_equipment_groups_items_by_or_group_in_order():
	cond = conditions.equipment(
		"e1",
		inclusive=[
			{"id": "a", "org": "g1"},
			{"id": "b", "org": "g2"},
			{"id": "c", "org": "g1"},
		],
		exclusive=[],
		include_not_equipped=True,
	)
	assert cond["equipmentInclusive"] == [["a", "c"], ["b"]]
	assert cond["equipmentExclusive"] == []
	assert cond["IncludeNotEquippedItems"] is True


def test_simple_counter_creator_subconditions():
	assert conditions.exit_status("x", ["Survived"])["status"] == ["Survived"]
	assert conditions.exit_name("x", "Exit1")["exitName"] == "Exit1"
	assert conditions.location("x", ["bigmap"])["target"] == ["bigmap"]
	assert conditions.health_buff("x", ["Buffs_L1"])["target"] == ["Buffs_L1"]
	assert conditions.launch_flare("x", "zone")["target"] == "zone"
	assert conditions.in_zone("x", ["z1"])["zoneIds"] == ["z1"]


def test_health_effect():
	cond = conditions.health_effect(
		"h1",
		body_parts=["Head"],
		effects=["Pain"],
		energy=1,
		energy_compare=">=",
		hydration=2,
		hydration_compare="<=",
		time=3,
		time_compare=">=",
	)
	assert cond["bodyPartsWithEffects"] == [{"bodyParts": ["Head"], "effects": ["Pain"]}]
	assert cond["hydration"] == {"compareMethod": "<=", "value": 2}


def test_counter_creator_nests_subconditions_under_its_own_counter_id():
	sub = conditions.visit_place("sub1", "zone")
	cond = conditions.counter_creator(
		"cc1",
		counter_id="counter1",
		sub_conditions=[sub],
		parent_id="",
		quest_type="Exploration",
		value=2,
		visibility_conditions=["v1"],
	)
	assert cond["id"] == "cc1"
	assert cond["counter"] == {"conditions": [sub], "id": "counter1"}
	assert cond["type"] == "Exploration" and cond["value"] == 2
	assert cond["visibilityConditions"] == ["v1"]


_ITEM_ARGS = dict(
	parent_id="",
	targets=["t1"],
	value=3,
	min_durability=0,
	max_durability=100,
	only_found_in_raid=True,
	visibility_conditions=[],
)


def test_find_item_and_handover_item_differ_only_in_type_and_count_in_raid():
	find = conditions.find_item("i1", **_ITEM_ARGS)
	handover = conditions.handover_item("i1", **_ITEM_ARGS)
	assert find["conditionType"] == "FindItem" and handover["conditionType"] == "HandoverItem"
	assert find.pop("countInRaid") is False
	find.pop("conditionType")
	handover.pop("conditionType")
	assert find == handover


def test_place_beacon_always_targets_the_ms2000_marker():
	cond = conditions.place_beacon(
		"p1", parent_id="", plant_time=10, value=1, zone_id="z", visibility_conditions=[]
	)
	assert cond["target"] == [conditions.MS2000_MARKER_TPL]


def test_start_only_conditions_have_no_visibility_conditions():
	assert conditions.level("l1", compare_method=">=", value=5)["visibilityConditions"] == []
	cond = conditions.quest_status("q1", available_after=0, status_ids=[4], target="quest")
	assert cond["status"] == [4] and cond["conditionType"] == "Quest"
	cond = conditions.trader_standing("t1", compare_method=">=", trader_id="trader", value=2)
	assert cond["target"] == "trader" and cond["value"] == 2


def test_leave_item_and_skill_and_loyalty():
	leave = conditions.leave_item_at_location(
		"l1",
		parent_id="",
		targets=["t"],
		value=1,
		plant_time=5,
		min_durability=0,
		max_durability=100,
		only_found_in_raid=False,
		zone_id="zone",
		visibility_conditions=[],
	)
	assert leave["zoneId"] == "zone" and leave["plantTime"] == 5
	skill = conditions.skill(
		"s1", compare_method=">=", parent_id="", target="Strength", value=10, visibility_conditions=[]
	)
	assert skill["target"] == "Strength"
	loyalty = conditions.trader_loyalty(
		"t1", compare_method=">=", parent_id="", trader_id="tr", value=2, visibility_conditions=[]
	)
	assert loyalty["target"] == "tr"


def test_weapon_assembly_is_still_a_placeholder():
	assert "weapon_assembly_placeholder" in conditions.weapon_assembly()


# --- rewards ------------------------------------------------------------------------


def test_reward_item_leaves_out_unset_fields():
	assert rewards.reward_item("i1", "tpl") == {"_id": "i1", "_tpl": "tpl"}


def test_reward_item_with_everything_set():
	item = rewards.reward_item(
		"i1", "tpl", stack_count=5, spawned_in_session=True, parent_id="p", slot_id="s"
	)
	assert item == {
		"_id": "i1",
		"_tpl": "tpl",
		"upd": {"StackObjectsCount": 5, "SpawnedInSession": True},
		"parentId": "p",
		"slotId": "s",
	}


def test_reward_item_upd_only_when_needed():
	assert "upd" not in rewards.reward_item("i", "t", parent_id="p")
	assert rewards.reward_item("i", "t", spawned_in_session=True)["upd"] == {
		"SpawnedInSession": True
	}


@pytest.mark.parametrize(
	"items, expected",
	[(None, ""), ([], ""), ([{}], ""), ([{"_id": "first"}, {"_id": "second"}], "first")],
)
def test_first_item_id(items, expected):
	assert rewards.first_item_id(items) == expected


def test_every_reward_type_reports_its_type_and_id():
	built = [
		rewards.achievement("r", target="a", unknown=False),
		rewards.assortment_unlock(
			"r", items=[], loyalty_level=2, target="t", trader_id="tr", unknown=False
		),
		rewards.experience("r", unknown=False, value=1),
		rewards.item("r", find_in_raid=True, items=[], target="t", unknown=False, value=1),
		rewards.skill("r", target="Strength", unknown=False, value=1),
		rewards.stash_rows("r", unknown=False, value=1),
		rewards.trader_standing("r", target="tr", unknown=False, value=0.05),
		rewards.trader_unlock("r", target="tr", unknown=False),
	]
	assert [r["type"] for r in built] == [
		"Achievement",
		"AssortmentUnlock",
		"Experience",
		"Item",
		"Skill",
		"StashRows",
		"TraderStanding",
		"TraderUnlock",
	]
	assert all(r["id"] == "r" and r["index"] == 0 for r in built)


# --- quests -------------------------------------------------------------------------


def _quest(quest_id="q1", **overrides):
	args = dict(
		name="My Quest",
		can_show_notifications=True,
		finish_conditions=[{"id": "f1"}],
		start_conditions=[{"id": "s1"}],
		fail_conditions=[],
		image="/img.jpg",
		instant_complete=False,
		location="any",
		restartable=False,
		rewards={"Fail": [], "Started": [], "Success": []},
		secret_quest=False,
		side="pmc",
		trader_id="trader",
		quest_type="Completion",
	)
	args.update(overrides)
	return quests.quest(quest_id, **args)


def test_quest_text_fields_are_locale_keys_of_the_quest_id():
	q = _quest("abc")
	for field in quests.LOCALE_FIELDS:
		assert q[field] == f"abc {field}"
	assert q["QuestName"] == "My Quest" and q["_id"] == "abc"


def test_quest_conditions_land_in_the_right_lists():
	q = _quest()
	assert q["conditions"] == {
		"AvailableForFinish": [{"id": "f1"}],
		"AvailableForStart": [{"id": "s1"}],
		"Fail": [],
	}


# --- locale -------------------------------------------------------------------------


def test_locale_keys_cover_text_fields_and_condition_ids():
	keys = locale.locale_keys({"q1": _quest("q1")})
	assert "q1 name" in keys and "q1 successMessageText" in keys
	assert "f1" in keys and "s1" in keys


def test_locale_keys_skip_collector():
	assert locale.locale_keys({"q1": _quest("q1", name="Collector")}) == []


def test_merge_locale_keeps_existing_values_and_adds_blank_entries():
	merged = locale.merge_locale({"a": "kept", "b": "x"}, ["b", "c"])
	assert merged == {"a": "kept", "b": "x", "c": ""}


def test_merge_locale_does_not_modify_its_input():
	base = {"a": "1"}
	locale.merge_locale(base, ["new"])
	assert base == {"a": "1"}


def test_locale_keys_match_the_golden_export():
	exported_quests = json.loads((GOLDEN / "quest_export.json").read_text(encoding="utf-8"))
	exported_locale = json.loads((GOLDEN / "locale_export.json").read_text(encoding="utf-8"))
	generated = locale.merge_locale({"existing key": "existing value"}, locale.locale_keys(exported_quests))
	assert generated == exported_locale


# --- assort -------------------------------------------------------------------------


def test_assort_item_with_a_quantity():
	item = assort.assort_item("i1", "tpl", unlimited=False, quantity="10")
	assert item == {
		"_id": "i1",
		"_tpl": "tpl",
		"parentId": "hideout",
		"slotId": "hideout",
		"upd": {"UnlimitedCount": False, "StackObjectsCount": 10},
	}


def test_assort_item_unlimited_ignores_quantity():
	item = assort.assort_item("i1", "tpl", unlimited=True, quantity="")
	assert item["upd"] == {"UnlimitedCount": True, "StackObjectsCount": 9999}


def test_assort_item_buy_restriction_and_quest_lock():
	item = assort.assort_item(
		"i1", "tpl", unlimited=False, quantity="1", buy_restriction="3", quest_id="q"
	)
	assert item["upd"]["BuyRestrictionMax"] == 3 and item["upd"]["BuyRestrictionCurrent"] == 0
	assert item["unlockedOn"] == "success" and item["questID"] == "q"


def test_weapon_part_item_and_ammo():
	assert assort.weapon_part_item("i", "tpl", "parent", "mod_stock") == {
		"_id": "i",
		"_tpl": "tpl",
		"parentId": "parent",
		"slotId": "mod_stock",
	}
	ammo = assort.weapon_part_item("i", "tpl", "parent", "mod_magazine", ammo_count="30")
	assert ammo["slotId"] == "cartridges" and ammo["location"] == 0
	assert ammo["upd"] == {"StackObjectsCount": "30"}


@pytest.mark.parametrize(
	"currency, tpl",
	[
		("Roubles", assort.ROUBLES_TPL),
		("USD", assort.USD_TPL),
		("Euros", assort.EUROS_TPL),
	],
)
def test_barter_scheme_currencies(currency, tpl):
	assert assort.barter_scheme("i1", "500", currency=currency) == {
		"i1": [[{"count": 500, "_tpl": tpl}]]
	}


def test_barter_scheme_for_an_item_trade():
	scheme = assort.barter_scheme("i1", "2", currency="Item", barter_item_tpl="someitem")
	assert scheme == {"i1": [[{"count": 2, "_tpl": "someitem"}]]}


def test_currency_name_defaults_to_euro():
	assert assort.currency_name(assort.ROUBLES_TPL) == "Roubles"
	assert assort.currency_name(assort.USD_TPL) == "USD"
	assert assort.currency_name("anything else") == "Euro"


def test_weapon_preset_parts():
	base = assort.weapon_preset_part("i", "tpl", "", "", is_base=True)
	assert base["parentId"] == "hideout" and base["upd"] == {}
	mod = assort.weapon_preset_part("i", "tpl", "parent", "mod_stock", is_base=False)
	assert mod == {"_id": "i", "_tpl": "tpl", "parentId": "parent", "slotId": "mod_stock"}
