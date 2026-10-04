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


# --- quest locks and unlock rewards -------------------------------------------------------------

MECHANIC = "5a7c2eca46aef81a7ca2145d"


def test_every_vanilla_mechanic_lock_has_its_unlock_reward_and_the_other_way_round(vanilla_quests, vanilla_assort, vanilla_questassort):
	assert assort.lock_problems(vanilla_quests, vanilla_questassort, vanilla_assort) == []
	assert assort.lock_problems(vanilla_quests, vanilla_questassort, vanilla_assort, MECHANIC) == []
	assert sum(len(v) for v in vanilla_questassort.values()) >= 50


def test_a_lock_whose_quest_does_not_unlock_the_item_is_flagged(vanilla_quests, vanilla_assort, vanilla_questassort):
	locks = {k: dict(v) for k, v in vanilla_questassort.items()}
	offer, quest_id = next(iter(locks["success"].items()))
	locks["success"][offer] = next(q for q in vanilla_quests if q != quest_id and not assort.unlocks({"x": vanilla_quests[q]}, MECHANIC))
	issues = assort.lock_problems(vanilla_quests, locks, vanilla_assort)
	assert [i.path for i in issues] == [("success", offer)]
	assert "no reward that unlocks" in issues[0].message


def test_a_reward_no_lock_matches_is_flagged_only_for_that_trader(vanilla_quests, vanilla_assort, vanilla_questassort):
	locks = {k: dict(v) for k, v in vanilla_questassort.items()}
	offer, quest_id = next(iter(locks["success"].items()))
	del locks["success"][offer]
	assert assort.lock_problems(vanilla_quests, locks, vanilla_assort) == []  # (no trader: the reverse check is off)
	issues = assort.lock_problems(vanilla_quests, locks, vanilla_assort, MECHANIC)
	assert len(issues) == 1 and issues[0].path[:2] == ("unlock", quest_id)
	other = assort.lock_problems(vanilla_quests, locks, vanilla_assort, "f" * 24)  # (another trader's unlocks aren't ours)
	assert not [i for i in other if i.path[0] == "unlock"]


def test_matching_is_by_item_not_by_id(vanilla_quests, vanilla_assort, vanilla_questassort):
	offer, quest_id = next(iter(vanilla_questassort["success"].items()))
	reward = assort.find_unlock(vanilla_quests[quest_id], "success", assort.offer_tpl(vanilla_assort, offer), MECHANIC)
	assert reward is not None and assort.reward_root(reward)["_id"] != offer  # (the reward's parts have their own ids)
	assert assort.find_unlock(vanilla_quests[quest_id], "fail", assort.offer_tpl(vanilla_assort, offer)) is None


def test_a_new_unlock_reward_matches_its_offer(vanilla_assort):
	offer = next(o for o in assort.offer_ids(vanilla_assort) if len(assort.offer_parts(vanilla_assort, o)) > 3)
	reward = assort.unlock_reward(vanilla_assort, offer, MECHANIC)
	parts = assort.offer_parts(vanilla_assort, offer)
	assert reward["type"] == "AssortmentUnlock" and reward["traderId"] == MECHANIC
	assert reward["loyaltyLevel"] == vanilla_assort["loyal_level_items"][offer]
	assert reward["target"] == reward["items"][0]["_id"] and [p["_tpl"] for p in reward["items"]] == [p["_tpl"] for p in parts]
	assert not {p["_id"] for p in reward["items"]} & {p["_id"] for p in parts}  # (new ids all through)
	ids = {p["_id"] for p in reward["items"]}
	assert all(p.get("parentId") in ids for p in reward["items"][1:]) and set(reward["items"][0]) == {"_id", "_tpl"}
	quests = {"q" * 24: {"QuestName": "Q", "rewards": {"Success": [reward], "Started": [], "Fail": []}}}
	locks = {"started": {}, "success": {offer: "q" * 24}, "fail": {}}
	assert assort.lock_problems(quests, locks, vanilla_assort, MECHANIC) == []


def test_a_fail_lock_has_no_reward_to_match(vanilla_quests, vanilla_assort):
	offer = assort.offer_ids(vanilla_assort)[0]
	quest_id = next(iter(vanilla_quests))
	locks = {"started": {}, "success": {}, "fail": {offer: quest_id}}
	assert assort.lock_problems(vanilla_quests, locks, vanilla_assort) == []
