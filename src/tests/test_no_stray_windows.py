"""Widgets must never open as windows of their own.

A widget with no parent is a window, so showing one before it has a parent (or removing a visible
widget by giving it no parent) makes a window flash on screen. These tests watch for any widget that is
shown as a top-level window while the program is used; only the real windows and dialogs may be.
"""

import itertools
import os
from contextlib import contextmanager

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtCore import QEvent, QObject
from PySide6.QtWidgets import QApplication, QDialog, QMainWindow, QMenu

from core.documents import Document
from core.gamedata import GameData
from core.paths import BUNDLED_DATABASE_DIR
from core.settings import Settings
from schema import assort as A
from ui import updates
from ui.assort_tab import AssortTab
from ui.main_window import MainWindow
from ui.quest_outline import QuestOutline


@pytest.fixture(scope="module")
def app():
	return QApplication.instance() or QApplication([])


class _Watcher(QObject):
	def __init__(self):
		super().__init__()
		self.shown = []

	def eventFilter(self, obj, event):
		if event.type() == QEvent.Type.Show and obj.isWidgetType() and obj.isWindow() and not isinstance(obj, (QMainWindow, QDialog, QMenu)):
			self.shown.append(type(obj).__name__)
		return False


@contextmanager
def watching(app):
	watcher = _Watcher()
	app.installEventFilter(watcher)
	try:
		yield watcher.shown
	finally:
		app.removeEventFilter(watcher)


def hosted(widget):
	"""Show a widget inside a window of its own, as the program does (a widget with no parent that is shown
	would itself count as a stray window)."""
	window = QMainWindow()
	window.setCentralWidget(widget)
	window.show()
	return window


def walk(item):
	yield item
	for i in range(item.childCount()):
		yield from walk(item.child(i))


def test_the_watcher_notices_a_widget_shown_without_a_parent(app):
	from PySide6.QtWidgets import QPushButton

	with watching(app) as shown:
		button = QPushButton("stray")
		button.setVisible(True)
		app.processEvents()
		button.close()
	assert shown == ["QPushButton"]


def test_selecting_and_adding_in_the_quest_outline_opens_no_stray_windows(app, vanilla_quests):
	with watching(app) as shown:
		outline = QuestOutline(None, Settings({"show_json_preview": True}))
		outline.set_document(Document(dict(itertools.islice(vanilla_quests.items(), 6))))
		window = hosted(outline)
		app.processEvents()
		for top in range(outline.tree.topLevelItemCount()):
			for item in walk(outline.tree.topLevelItem(top)):
				outline.tree.setCurrentItem(item)  # (builds the form for every kind of node)
				app.processEvents()
		outline.add_quest()
		for kind in ("HandoverItem", "CounterCreator", "Level"):
			outline.add_item("task", kind)
		outline.add_item("reward", "Item")
		outline.add_item("reward", "AssortmentUnlock")
		app.processEvents()
		outline.settings.show_json_preview = False
		outline.apply_settings()
		app.processEvents()
	assert shown == []


def test_opening_the_more_options_of_a_form_opens_no_stray_windows(app):
	from PySide6.QtWidgets import QPushButton

	with watching(app) as shown:
		outline = QuestOutline(None, Settings())
		outline.set_document(Document({}))
		window = hosted(outline)
		outline.add_quest()
		app.processEvents()
		for button in outline.pane.findChildren(QPushButton):
			if button.isCheckable():
				button.click()
				app.processEvents()
	assert shown == []


def test_the_trader_tab_opens_no_stray_windows(app, vanilla_assort):
	with watching(app) as shown:
		tab = AssortTab(Document(vanilla_assort), Document(A.empty_questassort()))
		window = hosted(tab)
		app.processEvents()
		for row in range(min(tab.list.count(), 15)):
			tab.list.setCurrentRow(row)
			app.processEvents()
	assert shown == []


def test_the_main_window_opens_no_stray_windows(app, vanilla_quests, vanilla_locale, tmp_path, monkeypatch):
	monkeypatch.setattr(updates, "fetch_remote_version", lambda config: None)

	with watching(app) as shown:
		window = MainWindow(Settings(), GameData(None, "en", BUNDLED_DATABASE_DIR))
		window.show()
		window._set_quests(Document(dict(itertools.islice(vanilla_quests.items(), 4))))
		window._set_locale(Document(dict(itertools.islice(vanilla_locale.items(), 400))))
		for index in range(window.tabs.count()):
			window.tabs.setCurrentIndex(index)
			app.processEvents()
		window.close()
	assert shown == []


def test_the_assort_unlock_panel_opens_no_stray_windows_in_any_of_its_states(app):
	"""Its Update preview button is only shown when the preview differs; it used to be shown before it had a parent."""
	from ui.unlock_panel import UnlockOfferPanel

	gun, mag, other = "1" * 24, "2" * 24, "3" * 24
	parts = [
		{"_id": "p" + "0" * 23, "_tpl": gun, "parentId": "hideout", "slotId": "hideout"},
		{"_id": "p1" + "0" * 22, "_tpl": mag, "parentId": "p" + "0" * 23, "slotId": "mod_magazine"},
	]
	assort = A.empty_assort()
	items, barter, level = A.new_offer_from_parts(parts)
	A.add_offer(assort, items, barter, level)
	(offer,) = A.offer_ids(assort)
	locks = A.empty_questassort()
	locks["success"][offer] = "a" * 24
	exact = A.unlock_reward(assort, offer, "t" * 24)
	different = A.unlock_reward(assort, offer, "t" * 24)
	different["items"] = different["items"][:1]  # (only the main item)
	stale_level = A.unlock_reward(assort, offer, "t" * 24)
	stale_level["loyaltyLevel"] = 4
	elsewhere = {"items": [{"_id": "z" * 24, "_tpl": other}], "target": "z" * 24, "loyaltyLevel": 1, "traderId": "t" * 24}
	with watching(app) as shown:
		for reward, locked in ((exact, True), (different, True), (different, False), (stale_level, True), (elsewhere, False), (exact, False)):
			quests = Document({"a" * 24: {"_id": "a" * 24, "QuestName": "Q", "rewards": {"Success": [dict(reward, type="AssortmentUnlock", id="r" * 24)], "Started": [], "Fail": []}}})
			outline = QuestOutline()
			outline.set_document(quests)
			outline.assort_source = lambda: (assort, locks if locked else A.empty_questassort(), "t" * 24)
			window = hosted(outline)
			outline._select_key(("reward", ("a" * 24, "rewards", "Success", 0)))
			app.processEvents()
			assert outline.pane.findChild(UnlockOfferPanel) is not None
			window.close()
	assert shown == []
