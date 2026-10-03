import json

from schema import assort
from schema.issues import ERROR, errors


def test_new_offer_is_clean():
	a = assort.empty_assort()
	oid = assort.add_offer(a, *assort.new_offer("588226ef24597767af46e39c", 500, level=2))
	assert not assort.validate_assort(a)
	assert assort.offer_ids(a) == [oid]
	assort.remove_offer(a, oid)
	assert a == assort.empty_assort()


def test_vanilla_assort_has_no_errors(vanilla_assort):
	assert not errors(assort.validate_assort(vanilla_assort))


def test_vanilla_assort_round_trips(vanilla_assort):
	assert json.loads(json.dumps(vanilla_assort)) == vanilla_assort


def test_offer_parts_follow_parents():
	a = assort.empty_assort()
	items, barter, level = assort.new_offer("a" * 24)
	items.append({"_id": "b" * 24, "_tpl": "c" * 24, "parentId": items[0]["_id"], "slotId": "mod_x"})
	oid = assort.add_offer(a, items, barter, level)
	assert len(assort.offer_parts(a, oid)) == 2
	assort.remove_offer(a, oid)
	assert not a["items"]


def test_missing_price_and_bad_level_are_warned():
	a = assort.empty_assort()
	oid = assort.add_offer(a, *assort.new_offer("a" * 24))
	del a["barter_scheme"][oid]
	a["loyal_level_items"][oid] = 9
	assert len(assort.validate_assort(a)) == 2
	assert not errors(assort.validate_assort(a))


def test_questassort():
	a = assort.empty_assort()
	oid = assort.add_offer(a, *assort.new_offer("a" * 24))
	good = {"started": {}, "success": {oid: "b" * 24}, "fail": {}}
	assert not assort.validate_questassort(good, a)
	bad = {"started": {}, "success": {"c" * 24: "b" * 24}, "fail": {}}
	assert len(assort.validate_questassort(bad, a)) == 1
	assert assort.validate_questassort({"success": {"zz": "b" * 24}})[0].level == ERROR


def test_composite():
	part = {"_id": "a" * 24, "_tpl": "b" * 24}
	assert not assort.validate_composite(assort.new_composite("Gun", [part]))
	assert assort.validate_composite(assort.new_composite("Empty", []))[0].level == ERROR


def test_every_vanilla_quest_lock_file_is_valid(vanilla_questassorts, vanilla_quests):
	assert len(vanilla_questassorts) >= 8
	for trader_id, locks in vanilla_questassorts.items():
		assert not errors(assort.validate_questassort(locks, None, set(vanilla_quests))), trader_id
