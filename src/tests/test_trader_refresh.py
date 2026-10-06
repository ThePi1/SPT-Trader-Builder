"""The Trader tab keeps the list, the note under it and the quest box in step with the offer after an edit or a removal."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication, QLabel, QMessageBox, QPushButton

from core.documents import Document
from schema import assort as A
from ui.assort_tab import AssortTab
from ui.parts_editor import PartsEditor

TRADER = "5a7c2eca46aef81a7ca2145d"
QID = "a" * 24
GUN, MAG, OTHER = "1" * 24, "2" * 24, "3" * 24


@pytest.fixture(scope="module")
def app():
	return QApplication.instance() or QApplication([])


def gun_parts():
	return [
		{"_id": "p" + "0" * 23, "_tpl": GUN, "parentId": "hideout", "slotId": "hideout"},
		{"_id": "p1" + "0" * 22, "_tpl": MAG, "parentId": "p" + "0" * 23, "slotId": "mod_magazine"},
	]


def make():
	"""A locked gun offer and a plain one; the gun's quest has a matching preview."""
	assort = A.empty_assort()
	for parts in (gun_parts(), [{"_id": "q" + "0" * 23, "_tpl": OTHER, "parentId": "hideout", "slotId": "hideout"}]):
		items, barter, level = A.new_offer_from_parts(parts)
		A.add_offer(assort, items, barter, level)
	gun_offer, plain_offer = A.offer_ids(assort)
	locks = A.empty_questassort()
	locks["success"][gun_offer] = QID
	preview = A.unlock_reward(assort, gun_offer, TRADER)
	quest = {"_id": QID, "QuestName": "Test Quest", "rewards": {"Success": [preview], "Started": [], "Fail": []}}
	quests = Document({QID: quest})
	tab = AssortTab(Document(assort), Document(locks), None, None, None, lambda: quests.data, lambda: quests)
	tab.trader.setEditText(TRADER)
	tab._trader_changed()
	tab.refresh(gun_offer)
	return tab, gun_offer, plain_offer


def labels(tab):
	return [w.text() for w in tab.right.findChildren(QLabel)]


def buttons(tab):
	return {b.text(): b for b in tab.right.findChildren(QPushButton)}


def test_removing_the_main_item_deletes_the_offer_and_everything_shown_follows(app, monkeypatch):
	tab, gun_offer, plain_offer = make()
	assert tab.note.text() == "2 of 2 offers." and tab.current_id() == gun_offer
	monkeypatch.setattr("ui.assort_tab.QMessageBox.question", lambda *a, **k: QMessageBox.StandardButton.Yes)
	editor = tab.right.findChild(PartsEditor)
	editor.tree.setCurrentItem(editor.tree.topLevelItem(0))  # (the gun itself)
	editor.remove_selected()
	data, locks = tab.doc.data, tab.locks.data
	assert A.offer_ids(data) == [plain_offer] and gun_offer not in data["barter_scheme"] and gun_offer not in data["loyal_level_items"]
	assert locks["success"] == {} and not A.validate_assort(data)
	assert tab.list.count() == 1 and tab.current_id() == plain_offer  # (the list, and the offer shown, are the ones that are left)
	assert tab.note.text() == "1 of 1 offers. 1 quest unlock(s) to check."  # (the quest now unlocks an item that no offer has)
	assert 'The quest "Test Quest" unlocks an item here, but no offer for it is locked to the quest.' in tab.note.toolTip()
	assert "Linked quest" not in " ".join(labels(tab))  # (the quest status of the removed offer is gone)


def test_saying_no_keeps_the_offer_and_puts_the_item_back(app, monkeypatch):
	tab, gun_offer, plain_offer = make()
	monkeypatch.setattr("ui.assort_tab.QMessageBox.question", lambda *a, **k: QMessageBox.StandardButton.No)
	editor = tab.right.findChild(PartsEditor)
	editor.tree.setCurrentItem(editor.tree.topLevelItem(0))
	editor.remove_selected()
	assert A.offer_ids(tab.doc.data) == [gun_offer, plain_offer] and tab.locks.data["success"] == {gun_offer: QID}
	assert tab.note.text() == "2 of 2 offers." and tab.right.findChild(PartsEditor).tree.topLevelItemCount() == 1
	assert len(A.offer_parts(tab.doc.data, gun_offer)) == 2


def test_removing_a_mod_updates_the_quest_box_and_the_list(app):
	tab, gun_offer, _plain = make()
	assert any(t.endswith("It is the same as the offer.") for t in labels(tab)) and "Update preview" not in buttons(tab)
	editor = tab.right.findChild(PartsEditor)
	mod = editor.tree.topLevelItem(0).child(0)
	editor.tree.setCurrentItem(mod)
	editor.remove_selected()
	assert len(A.offer_parts(tab.doc.data, gun_offer)) == 1
	text = next(t for t in labels(tab) if t.startswith('Linked quest "Test Quest"'))
	assert "It differs from the offer: 2 parts in the preview, 1 part in the offer." in text  # (without leaving the offer)
	assert "Update preview" in buttons(tab)
	buttons(tab)["Update preview"].click()
	assert any(t.endswith("It is the same as the offer.") for t in labels(tab))


def test_changing_the_price_or_level_updates_the_row_in_the_list(app):
	tab, gun_offer, _plain = make()
	assert "1 Roubles" in tab.list.item(0).text() and "level 1" in tab.list.item(0).text()
	tab._add_price(gun_offer, [A.MONEY["dollars"]])
	assert "Dollars" in tab.list.item(0).text()
	tab._edit("Change level", lambda d: d["loyal_level_items"].__setitem__(gun_offer, 3))
	assert "level 3" in tab.list.item(0).text() and tab.list.item(0).text().endswith("[quest]")
