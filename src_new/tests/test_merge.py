"""Importing: merging other files into what is open (core/merge.py)."""

import copy
import json

import pytest

from core import merge as M
from schema import assort as A
from schema import locale as L

Q1, Q2, T1, T2 = "a" * 24, "b" * 24, "c" * 24, "d" * 24
OFFER1, OFFER2 = "e" * 24, "f" * 24
ITEM = "1" * 24


def quest(quest_id, name, task_id):
	return {
		"_id": quest_id, "QuestName": name, "name": f"{quest_id} name", "description": f"{quest_id} description",
		"conditions": {"AvailableForStart": [], "Fail": [], "AvailableForFinish": [{"id": task_id, "conditionType": "Level", "value": 5, "compareMethod": ">="}]},
		"rewards": {"Success": [], "Started": [], "Fail": []},
	}


def offer(offer_id, tpl=ITEM):
	return [{"_id": offer_id, "_tpl": tpl, "parentId": "hideout", "slotId": "hideout", "upd": {}}], [[{"count": 5, "_tpl": A.MONEY["roubles"]}]], 2


def assort_with(*offer_ids):
	data = A.empty_assort()
	for offer_id in offer_ids:
		A.add_offer(data, *offer(offer_id))
	return data


# --- quests ---------------------------------------------------------------------------------

def test_new_quests_are_added_and_identical_ones_skipped():
	current = {Q1: quest(Q1, "One", T1)}
	merged, counts, ids, touched = M.merge_quests(current, {Q1: quest(Q1, "One", T1), Q2: quest(Q2, "Two", T2)})
	assert set(merged) == {Q1, Q2} and (counts.new, counts.same, counts.conflicts) == (1, 1, 0)
	assert touched == [Q2] and ids == {}
	assert set(current) == {Q1}  # (the inputs are not changed)


@pytest.mark.parametrize("policy,names", [(M.KEEP, ["One"]), (M.REPLACE, ["Changed"]), (M.BOTH, ["One", "Changed (imported)"])])
def test_a_quest_with_the_same_id_follows_the_policy(policy, names):
	current = {Q1: quest(Q1, "One", T1)}
	merged, counts, ids, touched = M.merge_quests(current, {Q1: quest(Q1, "Changed", T2)}, policy)
	assert counts.conflicts == 1 and sorted(q["QuestName"] for q in merged.values()) == sorted(names)
	if policy == M.BOTH:
		copy_id = next(k for k in merged if k != Q1)
		assert ids[Q1] == copy_id and ids[T2] != T2  # the copy has a new id and new task ids
		assert merged[copy_id]["name"] == f"{copy_id} name" and touched == [copy_id]
	assert current[Q1]["QuestName"] == "One"


# --- locale ---------------------------------------------------------------------------------

def test_locale_adds_new_entries_skips_blank_and_identical_ones():
	merged, counts = M.merge_locale({"a": "x", "b": ""}, {"a": "x", "b": "filled", "c": "new", "d": "  ", "e": 5})
	assert merged == {"a": "x", "b": "filled", "c": "new"} and (counts.new, counts.same, counts.conflicts) == (2, 1, 0)


@pytest.mark.parametrize("policy,expected", [(M.KEEP, "mine"), (M.REPLACE, "theirs"), (M.BOTH, "mine")])
def test_a_locale_clash_follows_the_policy(policy, expected):
	merged, counts = M.merge_locale({"k": "mine"}, {"k": "theirs"}, policy)
	assert merged["k"] == expected and counts.conflicts == 1


def test_locale_can_be_limited_to_some_keys_and_follows_renamed_quests():
	incoming = {f"{Q1} name": "N", f"{T1}": "task", "other": "x"}
	merged, _ = M.merge_locale({}, incoming, only_keys={f"{Q1} name", T1})
	assert merged == {f"{Q1} name": "N", T1: "task"}
	merged, _ = M.merge_locale({f"{Q1} name": "mine"}, incoming, id_map={Q1: Q2, T1: T2})
	assert merged == {f"{Q1} name": "mine", f"{Q2} name": "N", T2: "task", "other": "x"}


# --- assort and locks -----------------------------------------------------------------------

def test_offers_are_added_skipped_replaced_or_kept_as_copies():
	current = assort_with(OFFER1)
	changed = assort_with(OFFER1)
	changed["barter_scheme"][OFFER1][0][0]["count"] = 99
	incoming = copy.deepcopy(changed)
	A.add_offer(incoming, *offer(OFFER2))
	merged, counts, offer_map, touched = M.merge_assort(current, incoming, M.KEEP)
	assert A.offer_ids(merged) == [OFFER1, OFFER2] and (counts.new, counts.conflicts) == (1, 1)
	assert merged["barter_scheme"][OFFER1][0][0]["count"] == 5
	merged, counts, _, _ = M.merge_assort(current, incoming, M.REPLACE)
	assert merged["barter_scheme"][OFFER1][0][0]["count"] == 99 and len(A.offer_ids(merged)) == 2
	merged, counts, offer_map, touched = M.merge_assort(current, incoming, M.BOTH)
	assert len(A.offer_ids(merged)) == 3 and offer_map[OFFER1] in A.offer_ids(merged) and offer_map[OFFER1] != OFFER1
	assert merged["loyal_level_items"][offer_map[OFFER1]] == 2
	same, counts, _, _ = M.merge_assort(current, copy.deepcopy(current))
	assert same == current and counts.same == 1 and counts.new == 0
	assert A.validate_assort(merged) == []


def test_locks_follow_copied_offers_and_quests():
	current = {"started": {}, "success": {OFFER1: Q1}, "fail": {}}
	incoming = {"started": {OFFER2: Q2}, "success": {OFFER1: Q2}, "fail": {}}
	merged, counts = M.merge_locks(current, incoming, M.KEEP)
	assert merged["success"] == {OFFER1: Q1} and merged["started"] == {OFFER2: Q2} and counts.conflicts == 1
	merged, _ = M.merge_locks(current, incoming, M.REPLACE)
	assert merged["success"] == {OFFER1: Q2}
	merged, _ = M.merge_locks(current, incoming, M.BOTH, offer_map={OFFER2: "9" * 24}, quest_map={Q2: "8" * 24})
	assert merged["started"] == {"9" * 24: "8" * 24}


# --- planning an import ---------------------------------------------------------------------

def workspace(quests=None, locale=None, assort=None, locks=None):
	return {M.QUESTS: quests or {}, M.LOCALE: locale or {}, M.ASSORT: assort or A.empty_assort(), M.LOCKS: locks or A.empty_questassort()}


def test_five_files_merge_into_one_workspace_with_sources():
	items = [
		M.Item("a.json", M.QUESTS, {Q1: quest(Q1, "One", T1)}),
		M.Item("b.json", M.QUESTS, {Q2: quest(Q2, "Two", T2)}),
		M.Item("text.json", M.LOCALE, {f"{Q1} name": "One", f"{T2}": "do it", "vanilla": "ignore me"}),
		M.Item("offers.json", M.ASSORT, assort_with(OFFER1)),
		M.Item("locks.json", M.LOCKS, {"started": {}, "success": {OFFER1: Q1}, "fail": {}}),
	]
	plan = M.plan_import(items, workspace())
	assert plan.changed == {M.QUESTS, M.LOCALE, M.ASSORT, M.LOCKS}
	assert set(plan.data[M.QUESTS]) == {Q1, Q2} and plan.sources == {Q1: "a.json", Q2: "b.json"}
	assert plan.data[M.LOCALE] == {f"{Q1} name": "One", T2: "do it"}  # (only the text of the quests)
	assert [c.new for c in plan.counts] == [1, 1, 2, 1, 1]
	everything = M.plan_import(items, workspace(), everything=True)
	assert "vanilla" in everything.data[M.LOCALE]


def test_without_any_quests_a_locale_import_takes_everything_and_left_out_files_do_nothing():
	items = [M.Item("text.json", M.LOCALE, {"a": "x", "b": "y"}), M.Item("skip.json", M.QUESTS, {Q1: quest(Q1, "One", T1)}, include=False), M.Item("bad.json")]
	plan = M.plan_import(items, workspace())
	assert plan.data == {M.LOCALE: {"a": "x", "b": "y"}} and plan.counts[1] is None and plan.counts[2] is None


def test_importing_the_same_files_again_changes_nothing():
	items = [M.Item("a.json", M.QUESTS, {Q1: quest(Q1, "One", T1)}), M.Item("t.json", M.LOCALE, {f"{Q1} name": "One"})]
	first = M.plan_import(items, workspace())
	again = M.plan_import(items, workspace(first.data[M.QUESTS], first.data[M.LOCALE]))
	assert again.changed == set() and again.total[M.QUESTS].same == 1


def test_a_copied_quest_brings_its_text_and_lock_along():
	mine = {Q1: quest(Q1, "One", T1)}
	theirs = {Q1: quest(Q1, "Different", T2)}
	items = [
		M.Item("q.json", M.QUESTS, theirs), M.Item("t.json", M.LOCALE, {f"{Q1} name": "Theirs", T2: "their task"}),
		M.Item("l.json", M.LOCKS, {"started": {}, "success": {OFFER1: Q1}, "fail": {}}),
	]
	plan = M.plan_import(items, workspace(mine, {f"{Q1} name": "Mine"}, locks=A.empty_questassort()), M.BOTH)
	copy_id = next(k for k in plan.data[M.QUESTS] if k != Q1)
	assert plan.data[M.LOCALE][f"{Q1} name"] == "Mine" and plan.data[M.LOCALE][f"{copy_id} name"] == "Theirs"
	assert plan.data[M.LOCKS]["success"] == {OFFER1: copy_id}
	assert plan.sources == {copy_id: "q.json"}
	assert L.missing_keys({copy_id: plan.data[M.QUESTS][copy_id]}, plan.data[M.LOCALE]).get(f"{copy_id} name") is None


def test_loading_files_and_folders(tmp_path):
	(tmp_path / "mod").mkdir()
	(tmp_path / "mod" / "quests.json").write_text(json.dumps({Q1: quest(Q1, "One", T1)}), encoding="utf-8")
	(tmp_path / "mod" / "en.json").write_text(json.dumps({"a": "b"}), encoding="utf-8")
	(tmp_path / "mod" / "broken.json").write_text("{nope", encoding="utf-8")
	(tmp_path / "mod" / "notes.json").write_text(json.dumps({"x": [1, 2]}), encoding="utf-8")
	items = {i.name: i for i in M.load_items([tmp_path / "mod"])}
	assert items["quests.json"].kind == M.QUESTS and items["en.json"].kind == M.LOCALE
	assert items["broken.json"].error.startswith("Couldn't be read") and not items["broken.json"].include
	assert items["notes.json"].kind is None and items["notes.json"].error and not items["notes.json"].include
	single = M.load_items([tmp_path / "mod" / "en.json"])
	assert [i.name for i in single] == ["en.json"]


def test_vanilla_quests_merge_with_their_own_text(vanilla_quests, vanilla_locale):
	items = [M.Item("quests.json", M.QUESTS, vanilla_quests), M.Item("en.json", M.LOCALE, vanilla_locale)]
	plan = M.plan_import(items, workspace())
	assert len(plan.data[M.QUESTS]) == len(vanilla_quests)
	assert set(L.missing_keys(plan.data[M.QUESTS], plan.data[M.LOCALE])) == set(L.missing_keys(vanilla_quests, vanilla_locale))  # (all the quests' text came along)
	assert len(plan.data[M.LOCALE]) < len(vanilla_locale)  # (and not the rest of the game's text)
