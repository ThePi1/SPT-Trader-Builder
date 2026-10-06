"""In the Trader tab the main item of an offer can be swapped (New root item...), and items are added as children."""

import json
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication, QLabel, QMessageBox, QPushButton

from core.documents import Document
from core.gamedata import GameData
from schema import assort as A
from ui.assort_tab import AssortTab
from ui.parts_editor import PartsEditor

TRADER = "5a7c2eca46aef81a7ca2145d"
QID = "a" * 24
GUN_A, GUN_B, GUN_C, MAG, STOCK = "1" * 24, "2" * 24, "3" * 24, "4" * 24, "5" * 24


@pytest.fixture(scope="module")
def app():
	return QApplication.instance() or QApplication([])


def slot(name, allowed):
	return {"_name": name, "_props": {"filters": [{"Filter": [allowed]}]}}


def game(tmp_path):
	"""Three guns: A and C take a magazine, B takes only a stock."""
	(tmp_path / "templates").mkdir()
	(tmp_path / "locales" / "global").mkdir(parents=True)
	items = {
		GUN_A: {"_id": GUN_A, "_name": "gun_a", "_parent": "p", "_type": "Item", "_props": {"Slots": [slot("mod_magazine", MAG)]}},
		GUN_B: {"_id": GUN_B, "_name": "gun_b", "_parent": "p", "_type": "Item", "_props": {"Slots": [slot("mod_stock", STOCK)]}},
		GUN_C: {"_id": GUN_C, "_name": "gun_c", "_parent": "p", "_type": "Item", "_props": {"Slots": [slot("mod_magazine", MAG)]}},
		MAG: {"_id": MAG, "_name": "mag", "_parent": "p", "_type": "Item", "_props": {}},
		STOCK: {"_id": STOCK, "_name": "stock", "_parent": "p", "_type": "Item", "_props": {}},
	}
	(tmp_path / "templates" / "items.json").write_text(json.dumps(items), encoding="utf-8")
	(tmp_path / "locales" / "global" / "en.json").write_text(json.dumps({f"{GUN_A} Name": "Gun A", f"{GUN_B} Name": "Gun B", f"{GUN_C} Name": "Gun C", f"{MAG} Name": "Magazine"}), encoding="utf-8")
	return GameData(tmp_path, "en", None)


def make(tmp_path, picked=(), library=None):
	"""A locked offer for gun A (with a magazine and a stack of 5) and a quest whose preview is that gun; picks come from `picked`."""
	parts = [
		{"_id": "p" + "0" * 23, "_tpl": GUN_A, "parentId": "hideout", "slotId": "hideout", "upd": {"StackObjectsCount": 5, "UnlimitedCount": False}},
		{"_id": "p1" + "0" * 22, "_tpl": MAG, "parentId": "p" + "0" * 23, "slotId": "mod_magazine"},
	]
	assort = A.empty_assort()
	items, barter, _level = A.new_offer_from_parts(parts, price=777, level=3)
	items[0]["upd"]["StackObjectsCount"] = 5
	A.add_offer(assort, items, barter, 3)
	(offer,) = A.offer_ids(assort)
	locks = A.empty_questassort()
	locks["success"][offer] = QID
	preview = A.unlock_reward(assort, offer, TRADER)
	quests = Document({QID: {"_id": QID, "QuestName": "Test Quest", "rewards": {"Success": [preview], "Started": [], "Fail": []}}})
	picks = list(picked)
	asked = []

	def picker(ref, multi, parent):
		asked.append(ref)
		return [picks.pop(0)] if picks else []

	tab = AssortTab(Document(assort), Document(locks), game(tmp_path), picker, library, lambda: quests.data, lambda: quests)
	tab.trader.setEditText(TRADER)
	tab._trader_changed()
	tab.refresh(offer)
	tab.asked = asked
	return tab, offer, quests


def labels(tab):
	return [w.text() for w in tab.right.findChildren(QLabel)]


def buttons(tab):
	return {b.text(): b for b in tab.right.findChildren(QPushButton)}


def test_the_item_box_of_an_offer_has_add_child_item_and_new_root_item(app, tmp_path):
	tab, offer, _quests = make(tmp_path)
	assert "Add child item..." in buttons(tab) and "New root item..." in buttons(tab) and "Add item..." not in buttons(tab)
	# (other places that edit items keep "Add item...", and have no main item to swap)
	from schema import rewards
	from ui import forms

	from schema import registry

	form = forms.FormWidget(rewards.REWARDS["Item"])
	form.bind(registry.new_item("reward", "Item"))
	names = [b.text() for b in form.findChildren(QPushButton)]
	assert "Add item..." in names and "New root item..." not in names and "Add child item..." not in names


def test_swapping_the_root_keeps_everything_else_and_follows_the_quest(app, tmp_path):
	tab, offer, quests = make(tmp_path, picked=[GUN_C])
	before = [p["_id"] for p in A.offer_parts(tab.doc.data, offer)]
	assert any(t.endswith("It is the same as the offer.") for t in labels(tab))
	buttons(tab)["New root item..."].click()
	assert tab.asked == ["part"]  # (the search lists items and composite items)
	data = tab.doc.data
	root = A.offer_parts(data, offer)[0]
	assert root["_id"] == offer and root["_tpl"] == GUN_C and root["upd"]["StackObjectsCount"] == 5  # (same id, same stack)
	assert [p["_id"] for p in A.offer_parts(data, offer)] == before and A.offer_parts(data, offer)[1]["_tpl"] == MAG  # (the magazine fits Gun C)
	assert data["barter_scheme"][offer][0][0]["count"] == 777 and data["loyal_level_items"][offer] == 3
	assert tab.locks.data["success"] == {offer: QID}
	assert tab.current_id() == offer and "Gun C" in tab.list.item(0).text() and "level 3" in tab.list.item(0).text()
	assert "<b>Gun C</b>" in labels(tab)  # (the title of the offer)
	assert tab.problemsToggle.text() == "▶ 2 quest unlock(s) to check"  # (the offer's quest has no unlock for Gun C, and its unlock is for Gun A)
	assert "The quest's unlock preview shows another item (Gun A), not this one." in labels(tab)
	assert not A.validate_assort(data)
	buttons(tab)["Update preview"].click()  # (the quest's preview follows the offer)
	(reward,) = quests.data[QID]["rewards"]["Success"]
	assert A.reward_root(reward)["_tpl"] == GUN_C and len(reward["items"]) == 2 and reward["loyaltyLevel"] == 3
	assert any(t.endswith("It is the same as the offer.") for t in labels(tab)) and tab.note.text() == "1 of 1 offers."


def test_mods_that_do_not_fit_the_new_root_are_removed_after_asking(app, tmp_path, monkeypatch):
	tab, offer, _quests = make(tmp_path, picked=[GUN_B, GUN_B])
	asked = []
	monkeypatch.setattr("ui.parts_editor.QMessageBox.question", lambda parent, title, text, *a: asked.append(text) or QMessageBox.StandardButton.No)
	buttons(tab)["New root item..."].click()
	assert len(asked) == 1 and "Magazine" in asked[0] and "Gun B" in asked[0]
	assert A.offer_parts(tab.doc.data, offer)[0]["_tpl"] == GUN_A and len(A.offer_parts(tab.doc.data, offer)) == 2  # (No: nothing changed)
	monkeypatch.setattr("ui.parts_editor.QMessageBox.question", lambda *a, **k: QMessageBox.StandardButton.Yes)
	buttons(tab)["New root item..."].click()
	parts = A.offer_parts(tab.doc.data, offer)
	assert [p["_tpl"] for p in parts] == [GUN_B] and parts[0]["_id"] == offer and tab.doc.data["loyal_level_items"][offer] == 3


def test_a_composite_item_becomes_the_new_root_with_its_own_mods(app, tmp_path, monkeypatch):
	from core.library import Library

	library = Library(tmp_path / "my_items.json")
	built = library.add("Built C", [
		{"_id": "c" * 24, "_tpl": GUN_C, "parentId": "hideout", "slotId": "hideout", "upd": {"StackObjectsCount": 1, "FireMode": {"FireMode": "single"}}},
		{"_id": "d" * 24, "_tpl": STOCK, "parentId": "c" * 24, "slotId": "mod_stock"},
		{"_id": "e" * 24, "_tpl": MAG, "parentId": "d" * 24, "slotId": "mod_on_stock"},
	])
	tab, offer, quests = make(tmp_path, picked=[built], library=library)
	asked = []
	monkeypatch.setattr("ui.parts_editor.QMessageBox.question", lambda parent, title, text, *a: asked.append(text) or QMessageBox.StandardButton.Yes)
	old_mag = A.offer_parts(tab.doc.data, offer)[1]["_id"]
	buttons(tab)["New root item..."].click()
	assert len(asked) == 1 and "replaces the main item and its 1 part" in asked[0]  # (the magazine it had)
	parts = A.offer_parts(tab.doc.data, offer)
	assert [p["_tpl"] for p in parts] == [GUN_C, STOCK, MAG]
	assert parts[0]["_id"] == offer and parts[0]["parentId"] == "hideout" and parts[0]["slotId"] == "hideout"
	assert parts[0]["upd"]["StackObjectsCount"] == 5 and parts[0]["upd"]["FireMode"] == {"FireMode": "single"}  # (our stack, its fire mode)
	assert parts[1]["parentId"] == offer and parts[2]["parentId"] == parts[1]["_id"] and old_mag not in {p["_id"] for p in parts}
	assert all(p["_id"] not in ("c" * 24, "d" * 24, "e" * 24) for p in parts)  # (new ids: the saved item is untouched)
	assert tab.doc.data["barter_scheme"][offer][0][0]["count"] == 777 and tab.doc.data["loyal_level_items"][offer] == 3
	assert tab.locks.data["success"] == {offer: QID} and not A.validate_assort(tab.doc.data)
	assert "Gun C" in tab.list.item(0).text() and "The quest's unlock preview shows another item (Gun A), not this one." in labels(tab)
	assert len(library.entries[built]["items"]) == 3


def test_choosing_the_same_item_or_nothing_changes_nothing(app, tmp_path):
	tab, offer, _quests = make(tmp_path, picked=[GUN_A])
	before = json.dumps(tab.doc.data, sort_keys=True)
	buttons(tab)["New root item..."].click()  # (the same item)
	buttons(tab)["New root item..."].click()  # (cancelled)
	assert json.dumps(tab.doc.data, sort_keys=True) == before and tab.doc.undo_label is None


def test_without_item_templates_every_mod_is_kept(app, tmp_path):
	tab, offer, _quests = make(tmp_path, picked=["9" * 24])
	tab.gamedata = None  # (nothing to say what fits)
	editor = tab.right.findChild(PartsEditor)
	editor.ctx.gamedata = None
	buttons(tab)["New root item..."].click()
	parts = A.offer_parts(tab.doc.data, offer)
	assert [p["_tpl"] for p in parts] == ["9" * 24, MAG]


def test_add_child_item_with_nothing_selected_goes_on_the_main_item(app, tmp_path):
	tab, offer, _quests = make(tmp_path, picked=[STOCK])
	editor = tab.right.findChild(PartsEditor)
	editor.tree.setCurrentItem(None)
	editor._ask_slot = lambda parent, tpl: "mod_stock"  # (Gun A has no slot for it: it would ask)
	editor.add_item()
	parts = A.offer_parts(tab.doc.data, offer)
	new = next(p for p in parts if p["_tpl"] == STOCK)
	assert new["parentId"] == offer and new["slotId"] == "mod_stock" and tab.asked[-1] == "item"
	assert len([p for p in tab.doc.data["items"] if A.is_root(p)]) == 1 and not A.validate_assort(tab.doc.data)
