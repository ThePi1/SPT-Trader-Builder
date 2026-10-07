"""An Assort unlock reward's item is only a preview: the real offer is in the trader assort, linked by the quest assort file."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication, QLabel, QPushButton

from core.documents import Document
from schema import assort as A
from schema import fields as F
from schema import rewards
from ui import forms
from ui.help_mark import HelpMark
from ui.quest_outline import QuestOutline
from ui.unlock_panel import UnlockOfferPanel

TRADER = "5a7c2eca46aef81a7ca2145d"
QID = "a" * 24
GUN, MAG, STOCK, OTHER = "1" * 24, "2" * 24, "3" * 24, "4" * 24
HELP_TEXT = (
	"The item in the assort unlock reward (in the quest JSON) only controls the preview for the item. "
	"The actual assort is stored in the trader assort file, and linked to the quest through the quest assort file."
)


@pytest.fixture(scope="module")
def app():
	return QApplication.instance() or QApplication([])


def gun(mods=(MAG, STOCK)):
	parts = [{"_id": "p" + "0" * 23, "_tpl": GUN, "parentId": "hideout", "slotId": "hideout"}]
	for number, tpl in enumerate(mods, start=1):
		parts.append({"_id": f"p{number}" + "0" * 22, "_tpl": tpl, "parentId": parts[0]["_id"], "slotId": f"mod_{number}"})
	return parts


def assort_with(*offers, level=2):
	assort = A.empty_assort()
	for parts in offers:
		items, barter, _level = A.new_offer_from_parts(parts, level=level)
		A.add_offer(assort, items, barter, level)
	return assort


def quest(rewards=()):
	return {"_id": QID, "QuestName": "Test Quest", "rewards": {"Success": list(rewards), "Started": [], "Fail": []}}


# --- the comparison ---------------------------------------------------------------------------

def test_a_preview_matches_an_offer_by_shape_not_by_id():
	assort = assort_with(gun(), gun((MAG,)))
	full, short_gun = A.offer_ids(assort)
	reward = A.unlock_reward(assort, full, TRADER)
	assert {p["_id"] for p in reward["items"]}.isdisjoint({p["_id"] for p in assort["items"]})  # (ids of its own)
	assert A.offers_matching(assort, reward) == ([full], [short_gun])
	bare = {"items": [{"_id": "z" * 24, "_tpl": GUN}], "target": "z" * 24, "loyaltyLevel": 2, "traderId": TRADER}
	assert A.offers_matching(assort, bare) == ([], [full, short_gun])
	other = {"items": [{"_id": "z" * 24, "_tpl": OTHER}], "target": "z" * 24}
	assert A.offers_matching(assort, other) == ([], [])


def test_how_a_preview_differs_from_the_offer():
	assort = assort_with(gun(), gun((MAG,)))
	full, _short = A.offer_ids(assort)
	reward = A.unlock_reward(assort, full, TRADER)
	assert A.preview_differences(assort, full, reward, TRADER) == []
	reward["loyaltyLevel"] = 3
	assert A.preview_differences(assort, full, reward, TRADER) == ["level 3 in the quest, 2 in the offer"]
	reward["items"] = reward["items"][:1]
	assert A.preview_differences(assort, full, reward) == ["1 part in the preview, 3 parts in the offer", "level 3 in the quest, 2 in the offer"]
	assert A.preview_differences(assort, full, A.unlock_reward(assort, full, TRADER), "9" * 24) == ["another trader"]


def test_refreshing_a_preview_copies_the_offer_and_keeps_the_rest():
	assort = assort_with(gun())
	(offer,) = A.offer_ids(assort)
	reward = {"id": "r" * 24, "type": "AssortmentUnlock", "gameMode": ["pve"], "items": [{"_id": "z" * 24, "_tpl": GUN}], "target": "z" * 24, "loyaltyLevel": 1, "traderId": ""}
	A.refresh_unlock(reward, assort, offer, TRADER)
	assert len(reward["items"]) == 3 and reward["loyaltyLevel"] == 2 and reward["traderId"] == TRADER
	assert reward["target"] == reward["items"][0]["_id"] and reward["id"] == "r" * 24 and reward["gameMode"] == ["pve"]
	assert A.preview_differences(assort, offer, reward, TRADER) == []


def test_what_the_assort_says_about_a_preview():
	assort = assort_with(gun())
	(offer,) = A.offer_ids(assort)
	locks = A.empty_questassort()
	reward = A.unlock_reward(assort, offer, TRADER)
	state = lambda r=reward, timing="Success": A.unlock_state(assort, locks, QID, timing, r, TRADER)
	assert A.unlock_state(A.empty_assort(), locks, QID, "Success", reward)[0:2] == ("note", "No trader assort is open, so the preview can't be compared with an offer.")
	tone, message, owner, differs = state()
	assert (tone, owner, differs) == ("note", offer, False) and "not locked to this quest" in message  # (an offer exists, no lock yet)
	locks["success"][offer] = QID
	assert state() == ("ok", "The preview is the same as the offer locked to this quest.", offer, False)
	reward["loyaltyLevel"] = 4
	tone, message, owner, differs = state()
	assert (tone, owner, differs) == ("note", offer, True) and "level 4 in the quest, 2 in the offer" in message
	bare = {"items": [{"_id": "z" * 24, "_tpl": GUN}], "target": "z" * 24, "loyaltyLevel": 2, "traderId": TRADER}
	tone, message, owner, differs = state(bare)
	assert (tone, owner, differs) == ("note", offer, True) and "1 part in the preview, 3 parts in the offer" in message
	locks["success"].clear()
	tone, message, owner, differs = state(bare)
	assert tone == "note" and "different parts" in message and owner == offer
	none = {"items": [{"_id": "z" * 24, "_tpl": OTHER}], "target": "z" * 24, "loyaltyLevel": 2, "traderId": TRADER}
	assert state(none)[0] == "warn" and "no offer for this item" in state(none)[1]


# --- the "?" next to Item ---------------------------------------------------------------------

def test_the_item_of_an_assort_unlock_has_a_question_mark_with_the_explanation(app):
	field = rewards.REWARDS["AssortmentUnlock"].field("items")
	assert field.help == HELP_TEXT == rewards.UNLOCK_ITEM_HELP
	others = [f for kind, spec in rewards.REWARDS.items() for f in spec.fields if f.help and not (kind == "AssortmentUnlock" and f.key == "items")]
	assert not others  # (only that field has one)
	form = forms.FormWidget(rewards.REWARDS["AssortmentUnlock"])
	marks = form.findChildren(HelpMark)
	assert [m.help_text for m in marks] == [HELP_TEXT]
	mark = marks[0]
	mark.show()
	assert mark.text() == "?"
	mark.show_help()
	assert mark.popup.isVisible() and mark.popup.text() == HELP_TEXT and mark.popup.wordWrap()
	mark.hide_help()
	assert not mark.popup.isVisible()
	assert not forms.FormWidget(rewards.REWARDS["Experience"]).findChildren(HelpMark)  # (other forms have none)


# --- the Quests tab -----------------------------------------------------------------------------

def outline_for(assort, locks, reward):
	quests = Document({QID: quest([reward])})
	outline = QuestOutline()
	outline.set_document(quests)
	outline.assort_source = lambda: (assort, locks, TRADER)
	outline._select_key(("reward", (QID, "rewards", "Success", 0)))
	return outline, quests


def panel(outline):
	return outline.pane.findChild(UnlockOfferPanel)


def test_the_quests_tab_shows_what_the_assort_says_and_can_fill_or_update_the_preview(app):
	assort = assort_with(gun())
	(offer,) = A.offer_ids(assort)
	locks = A.empty_questassort()
	locks["success"][offer] = QID
	reward = A.unlock_reward(assort, offer, TRADER)
	reward["loyaltyLevel"] = 4
	outline, quests = outline_for(assort, locks, reward)
	box = panel(outline)
	assert box is not None and "level 4 in the quest, 2 in the offer" in box.status.text()
	assert not box.updateButton.isHidden()
	box.updateButton.click()
	assert quests.data[QID]["rewards"]["Success"][0]["loyaltyLevel"] == 2 and quests.undo_label == "Update the preview"
	assert "same as the offer locked" in panel(outline).status.text() and panel(outline).updateButton.isHidden()
	quests.undo()
	assert quests.data[QID]["rewards"]["Success"][0]["loyaltyLevel"] == 4


def test_the_panel_follows_the_preview_as_its_fields_are_edited(app):
	assort = assort_with(gun(), gun((OTHER,)))
	first, second = A.offer_ids(assort)
	locks = A.empty_questassort()
	locks["success"][first] = QID
	reward = A.unlock_reward(assort, first, TRADER)
	outline, quests = outline_for(assort, locks, reward)
	box = panel(outline)
	assert "same as the offer locked" in box.status.text() and box.updateButton.isHidden()
	form = outline.pane.findChild(forms.FormWidget)
	level = next(c for c in form.controls if c.field.key == "loyaltyLevel")
	level.edited.emit(4)  # (the quest's level is changed in the form)
	assert panel(outline) is box and "level 4 in the quest, 2 in the offer" in box.status.text() and not box.updateButton.isHidden()
	level.edited.emit(2)
	assert "same as the offer locked" in box.status.text() and box.updateButton.isHidden()
	items = next(c for c in form.controls if c.field.key == "items")
	items.edited.emit(A.offer_parts(assort, second))  # (another item as the preview)
	assert panel(outline) is box and "differs" in box.status.text() and "same as the offer locked" not in box.status.text()
	box.updateButton.click()  # (still brings the preview in line with the offer it belongs to)
	assert quests.data[QID]["rewards"]["Success"][0]["items"][0]["_tpl"] == GUN


def test_filling_the_preview_from_any_offer_of_the_open_assort(app):
	assort = assort_with(gun(), gun((OTHER,)))
	first, second = A.offer_ids(assort)
	blank = {"id": "r" * 24, "type": "AssortmentUnlock", "items": [], "target": "", "loyaltyLevel": 1, "traderId": ""}
	outline, quests = outline_for(assort, A.empty_questassort(), blank)
	box = panel(outline)
	assert box.combo.count() == 2 and box.fillButton.isEnabled()
	box.combo.setCurrentIndex(1)
	box.fillButton.click()
	reward = quests.data[QID]["rewards"]["Success"][0]
	assert [p["_tpl"] for p in reward["items"]] == [GUN, OTHER] and reward["traderId"] == TRADER and reward["loyaltyLevel"] == 2
	assert reward["target"] == reward["items"][0]["_id"] and reward["items"][0]["_id"] != second


def test_no_panel_without_an_assort_to_look_in(app):
	reward = {"id": "r" * 24, "type": "AssortmentUnlock", "items": [], "target": "", "loyaltyLevel": 1, "traderId": ""}
	quests = Document({QID: quest([reward])})
	outline = QuestOutline()
	outline.set_document(quests)
	outline._select_key(("reward", (QID, "rewards", "Success", 0)))
	assert panel(outline) is None  # (no assort_source: the form is just the form)


# --- the Trader tab -------------------------------------------------------------------------------

def tab_for(assort, locks, quests):
	from ui.assort_tab import AssortTab

	quests_doc = Document(quests)
	tab = AssortTab(Document(assort), Document(locks), None, None, None, lambda: quests_doc.data, lambda: quests_doc)
	tab.trader.setEditText(TRADER)
	tab._trader_changed()
	return tab, quests_doc


def labels(tab):
	return [w.text() for w in tab.right.findChildren(QLabel)]


def buttons(tab):
	return {b.text(): b for b in tab.right.findChildren(QPushButton)}


def test_the_trader_tab_describes_the_preview_and_updates_it(app):
	assort = assort_with(gun())
	(offer,) = A.offer_ids(assort)
	locks = A.empty_questassort()
	locks["success"][offer] = QID
	reward = A.unlock_reward(assort, offer, TRADER)
	reward["items"] = reward["items"][:1]  # (only the main item, as some base game previews)
	reward["loyaltyLevel"] = 3
	tab, quests_doc = tab_for(assort, locks, {QID: quest([reward])})
	tab.refresh(offer)
	text = next(t for t in labels(tab) if t.startswith('Linked quest "Test Quest"'))
	assert "Preview in the quest:" in text and "level 3" in text and "(1 part)" in text
	assert "It differs from the offer: 1 part in the preview, 3 parts in the offer; level 3 in the quest, 2 in the offer." in text
	buttons(tab)["Update preview"].click()
	new = quests_doc.data[QID]["rewards"]["Success"][0]
	assert len(new["items"]) == 3 and new["loyaltyLevel"] == 2 and new["id"] == reward["id"] and quests_doc.undo_label == "Update preview"
	assert "Update preview" not in buttons(tab) and any(t.endswith("It is the same as the offer.") for t in labels(tab))


def test_locking_an_offer_gives_the_quest_its_unlock_preview_when_it_has_none(app):
	assort = assort_with(gun())
	(offer,) = A.offer_ids(assort)
	tab, quests_doc = tab_for(assort, A.empty_questassort(), {QID: quest()})
	tab.refresh(offer)
	tab._set_lock(offer, "success", QID)
	(reward,) = quests_doc.data[QID]["rewards"]["Success"]
	assert reward["type"] == "AssortmentUnlock" and reward["traderId"] == TRADER and len(reward["items"]) == 3
	assert tab.locks.data["success"] == {offer: QID}
	tab._set_lock(offer, "success", QID)  # (again: no second reward)
	assert len(quests_doc.data[QID]["rewards"]["Success"]) == 1
	tab._set_lock(offer, "fail", QID)  # (a fail lock has no reward to go with it)
	assert len(quests_doc.data[QID]["rewards"]["Success"]) == 1 and not quests_doc.data[QID]["rewards"]["Fail"]


def test_an_item_rewards_found_in_raid_box_has_a_question_mark_saying_it_is_ignored_except_for_money(app):
	from schema import registry
	from ui.parts_editor import PartsEditor

	form = forms.FormWidget(rewards.REWARDS["Item"])
	form.bind(registry.new_item("reward", "Item"))
	editor = form.findChild(PartsEditor)
	marks = editor.detail.findChildren(HelpMark)
	assert [m.help_text for m in marks] == ["This is ignored except for RUB/USD/EUR rewards."]
	assert editor.detail.layout().labelForField(marks[0].parentWidget()).text() == "Found in raid"  # (next to that box)
	# the other places that edit parts have no "?" there: a trader offer, a composite item, the preview of an Assort unlock
	assert not PartsEditor([], forms.Context()).detail.findChildren(HelpMark)
	assert not PartsEditor([], forms.Context(), offer=True).detail.findChildren(HelpMark)
	unlock = forms.FormWidget(rewards.REWARDS["AssortmentUnlock"])
	unlock.bind(registry.new_item("reward", "AssortmentUnlock"))
	assert not unlock.findChild(PartsEditor).detail.findChildren(HelpMark)
