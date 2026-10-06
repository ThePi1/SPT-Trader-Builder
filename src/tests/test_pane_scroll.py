"""The right-hand panes of the Trader and Composite tabs scroll when the window is small, so nothing is squeezed into
the border of the list above (the item row used to overlap the parts list when the window was shrunk as far as it goes)."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication, QScrollArea

from core.documents import Document
from schema import assort as A
from ui.assort_tab import AssortTab
from ui.composite_tab import CompositeTab
from ui.parts_editor import PartsEditor

TRADER = "5a7c2eca46aef81a7ca2145d"
QID = "a" * 24
GUN, MAG = "1" * 24, "2" * 24


@pytest.fixture(scope="module")
def app():
	return QApplication.instance() or QApplication([])


def gap_between_list_and_details(owner):
	"""How many pixels there are between the bottom of the parts list and the top of the details under it."""
	editor = owner.findChild(PartsEditor)
	tree, details = editor.tree, editor.detail
	return details.mapTo(owner, details.rect().topLeft()).y() - (tree.mapTo(owner, tree.rect().topLeft()).y() + tree.height())


def test_the_trader_tab_scrolls_instead_of_squeezing_the_item_into_the_list(app):
	parts = [
		{"_id": "p" + "0" * 23, "_tpl": GUN, "parentId": "hideout", "slotId": "hideout"},
		{"_id": "p1" + "0" * 22, "_tpl": MAG, "parentId": "p" + "0" * 23, "slotId": "mod_magazine"},
	]
	items, barter, level = A.new_offer_from_parts(parts)
	offer = items[0]["_id"]
	assort = Document({"items": items, "barter_scheme": {offer: barter}, "loyal_level_items": {offer: level}})
	locks = Document(A.empty_questassort())
	locks.data["success"][offer] = QID  # (its quest text wraps, so the pane's height depends on its width)
	quests = Document({QID: {"_id": QID, "QuestName": "A quest with a long enough name to make its line wrap", "rewards": {"Success": [], "Started": [], "Fail": []}}})
	tab = AssortTab(assort, locks, None, None, None, lambda: quests.data, lambda: quests)
	tab.trader.setEditText(TRADER)
	tab._trader_changed()
	tab.refresh(offer)
	assert isinstance(tab.rightScroll, QScrollArea) and tab.rightScroll.widget() is tab.right and tab.rightScroll.widgetResizable()
	for height in (900, 400, 200):
		tab.resize(900, height)
		tab.show()
		app.processEvents()
		assert gap_between_list_and_details(tab.right) >= 0, height
	assert tab.rightScroll.verticalScrollBar().maximum() > 0  # (what does not fit is scrolled to)


def test_the_composite_tab_scrolls_too(app, tmp_path):
	from core.library import Library

	library = Library(tmp_path / "my_items.json")
	library.add("My gun", [{"_id": "p" + "0" * 23, "_tpl": GUN, "parentId": "hideout", "slotId": "hideout"}])
	tab = CompositeTab(library, None, None)
	tab.mine.setCurrentRow(0)
	assert isinstance(tab.rightScroll, QScrollArea) and tab.rightScroll.widget() is tab.right
	for height in (700, 250):
		tab.resize(800, height)
		tab.show()
		app.processEvents()
		assert gap_between_list_and_details(tab.right) >= 0, height
