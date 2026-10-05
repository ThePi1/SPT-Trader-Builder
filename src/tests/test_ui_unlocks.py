"""The link between a trader's quest locks and the quests' unlock rewards, in the Trader tab."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication, QLabel, QMessageBox, QPushButton

from core.documents import Document
from schema import assort as A
from ui.assort_tab import AssortTab

TRADER = "5a7c2eca46aef81a7ca2145d"
QID = "a" * 24
TPL = "5449016a4bdc2d6f028b456f"


@pytest.fixture(scope="module")
def app():
	return QApplication.instance() or QApplication([])


def quest(rewards=None):
	return {"_id": QID, "QuestName": "Test Quest", "rewards": {"Success": list(rewards or []), "Started": [], "Fail": []}}


def make(lock=None, quest_data=None):
	items, barter, level = A.new_offer(TPL, level=2)
	assort_doc = Document({"items": items, "barter_scheme": {items[0]["_id"]: barter}, "loyal_level_items": {items[0]["_id"]: level}})
	locks = Document(A.empty_questassort())
	if lock:
		locks.data[lock][items[0]["_id"]] = QID
	quests_doc = Document({QID: quest_data if quest_data is not None else quest()})
	tab = AssortTab(assort_doc, locks, None, None, None, lambda: quests_doc.data, lambda: quests_doc)
	return tab, assort_doc, locks, quests_doc, items[0]["_id"]


def buttons(tab):
	return {b.text(): b for b in tab.right.findChildren(QPushButton)}


def labels(tab):
	return [w.text() for w in tab.right.findChildren(QLabel)]


def set_trader(tab, trader_id=TRADER):
	tab.trader.setEditText(trader_id)
	tab._trader_changed()


def test_a_locked_offer_whose_quest_has_no_unlock_offers_to_add_it(app):
	tab, assort_doc, locks, quests_doc, offer = make(lock="success")
	set_trader(tab)
	assert "The quest doesn't unlock this item yet." in labels(tab)
	assert "Add unlock to the quest" in buttons(tab)
	assert "1 quest unlock(s) to check." in tab.note.text()


def test_adding_the_unlock_puts_a_matching_reward_in_the_quest(app):
	tab, assort_doc, locks, quests_doc, offer = make(lock="success")
	set_trader(tab)
	buttons(tab)["Add unlock to the quest"].click()
	(reward,) = quests_doc.data[QID]["rewards"]["Success"]
	assert reward["type"] == "AssortmentUnlock" and reward["traderId"] == TRADER and reward["loyaltyLevel"] == 2
	assert A.reward_root(reward)["_tpl"] == TPL
	assert A.lock_problems(quests_doc.data, locks.data, assort_doc.data, TRADER) == []
	assert any(text.startswith('Linked quest "Test Quest" gives this unlock.') and text.endswith("It is the same as the offer.") for text in labels(tab))
	assert "Add unlock to the quest" not in buttons(tab) and "Update preview" not in buttons(tab)
	assert "to check" not in tab.note.text()
	quests_doc.undo()  # (one step in the quests' undo history)
	assert quests_doc.data[QID]["rewards"]["Success"] == []


def test_a_started_lock_adds_the_reward_to_the_started_list(app):
	tab, assort_doc, locks, quests_doc, offer = make(lock="started")
	set_trader(tab)
	buttons(tab)["Add unlock to the quest"].click()
	assert len(quests_doc.data[QID]["rewards"]["Started"]) == 1 and quests_doc.data[QID]["rewards"]["Success"] == []


def test_adding_an_unlock_needs_a_trader(app, monkeypatch):
	shown = []
	monkeypatch.setattr("ui.assort_tab.QMessageBox.information", lambda *args: shown.append(args[2]))
	tab, assort_doc, locks, quests_doc, offer = make(lock="success")
	buttons(tab)["Add unlock to the quest"].click()
	assert shown and "trader" in shown[0].lower()
	assert quests_doc.data[QID]["rewards"]["Success"] == []


def test_a_pasted_trader_id_is_used_and_nonsense_is_not(app):
	tab, *_ = make()
	set_trader(tab, TRADER.upper())
	assert tab.trader_id == TRADER.upper()
	set_trader(tab, "not an id")
	assert tab.trader_id == ""


def test_a_quest_that_unlocks_the_item_can_be_used_as_its_lock(app):
	unlock = A.unlock_reward({"items": [{"_id": "9" * 24, "_tpl": TPL, "parentId": "hideout", "slotId": "hideout"}], "loyal_level_items": {"9" * 24: 2}}, "9" * 24, TRADER)
	tab, assort_doc, locks, quests_doc, offer = make(quest_data=quest([unlock]))
	assert "Lock this offer to it" not in buttons(tab)  # (without a trader it can't tell whose unlock it is)
	set_trader(tab)
	assert "Lock this offer to it" in buttons(tab)
	assert any("Test Quest" in text and "completed" in text for text in labels(tab))
	assert "1 quest unlock(s) to check." in tab.note.text()
	buttons(tab)["Lock this offer to it"].click()
	assert locks.data["success"] == {offer: QID}
	assert A.lock_problems(quests_doc.data, locks.data, assort_doc.data, TRADER) == []


def test_nothing_is_said_without_open_quests(app):
	items, barter, level = A.new_offer(TPL)
	assort_doc = Document({"items": items, "barter_scheme": {items[0]["_id"]: barter}, "loyal_level_items": {items[0]["_id"]: level}})
	locks = Document(A.empty_questassort())
	locks.data["success"][items[0]["_id"]] = QID
	tab = AssortTab(assort_doc, locks)
	assert "quest unlock" not in tab.note.text() and "unlocks this item" not in " ".join(labels(tab))


def test_a_lock_to_a_quest_that_is_not_open_says_so(app):
	tab, assort_doc, locks, quests_doc, offer = make(lock="success")
	locks.data["success"][offer] = "b" * 24
	tab.refresh(offer)
	assert "That quest isn't in the open quest file." in labels(tab)


def test_a_fail_lock_has_no_unlock_to_add(app):
	tab, assort_doc, locks, quests_doc, offer = make(lock="fail")
	set_trader(tab)
	assert "Add unlock to the quest" not in buttons(tab)


def test_a_quest_with_no_name_is_shown_by_its_id(app):
	tab, assort_doc, locks, quests_doc, offer = make(lock="success")
	set_trader(tab)
	buttons(tab)["Add unlock to the quest"].click()
	quests_doc.data[QID].pop("QuestName")
	tab.refresh(offer)
	assert any(text.startswith(f'Linked quest "{QID}" gives this unlock.') for text in labels(tab))
