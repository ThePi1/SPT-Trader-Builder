"""Exporting a selection of quests with their text, offers and locks (core/export.py)."""

from core import merge as M
from core.export import export_selection
from schema import assort as A
from tests.test_merge import ITEM, OFFER1, OFFER2, Q1, Q2, T1, T2, assort_with, quest


def workspace():
	quests = {Q1: quest(Q1, "One", T1), Q2: quest(Q2, "Two", T2)}
	locale = {f"{Q1} name": "One", f"{Q2} name": "Two", T1: "do one", T2: "do two", "vanilla": "x", f"{Q1} description": ""}
	assort = assort_with(OFFER1, OFFER2)
	locks = {"started": {}, "success": {OFFER1: Q1, OFFER2: Q2}, "fail": {}}
	return quests, locale, assort, locks


def test_an_export_takes_only_the_selected_quests_and_what_belongs_to_them():
	result = export_selection([Q1], *workspace())
	assert list(result.quests) == [Q1]
	assert result.locale == {f"{Q1} name": "One", T1: "do one"}  # (no other quest's text, no blank text)
	assert A.offer_ids(result.assort) == [OFFER1] and result.offer_count() == 1
	assert result.locks == {"started": {}, "success": {OFFER1: Q1}, "fail": {}} and result.lock_count() == 1
	assert A.validate_assort(result.assort) == []


def test_nothing_to_export_alongside_when_the_quests_have_no_offers_or_text():
	quests, _locale, assort, locks = workspace()
	result = export_selection([Q1], quests, {}, A.empty_assort(), A.empty_questassort())
	assert result.locale == {} and result.assort == {} and result.locks == {} and result.offer_count() == 0 and result.lock_count() == 0
	result = export_selection([Q1], quests, {}, assort, {"started": {}, "success": {OFFER2: Q2}, "fail": {}})
	assert result.assort == {} and result.locks == {}


def test_unknown_ids_are_ignored_and_the_inputs_are_not_changed():
	quests, locale, assort, locks = workspace()
	result = export_selection([Q1, "z" * 24], quests, locale, assort, locks)
	result.quests[Q1]["QuestName"] = "changed"
	result.assort["items"].clear()
	assert list(result.quests) == [Q1] and quests[Q1]["QuestName"] == "One" and len(assort["items"]) == 2


def test_an_export_can_be_imported_again_without_loss():
	quests, locale, assort, locks = workspace()
	result = export_selection([Q1, Q2], quests, locale, assort, locks)
	items = [M.Item("q.json", M.QUESTS, result.quests), M.Item("t.json", M.LOCALE, result.locale), M.Item("a.json", M.ASSORT, result.assort), M.Item("l.json", M.LOCKS, result.locks)]
	empty = {M.QUESTS: {}, M.LOCALE: {}, M.ASSORT: A.empty_assort(), M.LOCKS: A.empty_questassort()}
	plan = M.plan_import(items, empty)
	assert plan.data[M.QUESTS] == quests and plan.data[M.LOCALE] == {k: v for k, v in locale.items() if v and k != "vanilla"}
	assert A.offer_ids(plan.data[M.ASSORT]) == [OFFER1, OFFER2] and plan.data[M.LOCKS] == locks
	assert ITEM  # (the offers sell this item)
