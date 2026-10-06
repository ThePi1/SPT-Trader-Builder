"""The Quest Graph tab: the drawing, the filters, the selected quest, finding a quest, and how it keeps up with the window."""

import json
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from core import questgraph as G
from core import references as R
from core.gamedata import GameData
from core.paths import BUNDLED_DATABASE_DIR
from ui.quest_graph_tab import AROUND, EVERYTHING, QuestGraphTab, Sources
from tests.test_questgraph import quest


@pytest.fixture(scope="module")
def app():
	return QApplication.instance() or QApplication([])


def mine():
	return {
		"a": quest("Alpha"), "b": quest("Bravo", [("a", (4,), 0)]), "c": quest("Charlie", [("b", (4,), 0)], trader="t2", level=5),
		"d": quest("Delta", [("c", (4,), 0)], fails_with=[("x", (4,))]), "lone": quest("Lonely", trader="t2"),
	}


def make(tmp_path, with_reference=True):
	references = R.References(tmp_path / "list.json")
	if with_reference:
		path = tmp_path / "mod.json"
		path.write_text(json.dumps({"r1": quest("Reference one", [("a", (4,), 0), ("missing", (4,), 0)]), "x": quest("Xray", trader="t2")}), encoding="utf-8")
		references.add([path])
	data = {"sources": Sources(
		open_quests=mine(), imported={"b": "bravo.json"}, references=references, game={"g1": quest("Game one", [("a", (4,), 0)], trader="t1")},
		trader_names={"t1": "Prapor", "t2": "Skier"}, game_name=lambda quest_id: "",
	)}
	tab = QuestGraphTab(lambda: data["sources"])
	tab.data = data
	tab.gameBox.setChecked(True)  # (off when the tab opens)
	tab.resize(1000, 700)
	tab.show()
	tab.refresh()
	return tab


def drawn(tab):
	return set(tab.view.graph_scene.items_by_id)


def test_the_base_game_is_not_drawn_until_it_is_asked_for(app, tmp_path):
	tab = QuestGraphTab(lambda: Sources(open_quests=mine(), game={"g1": quest("Game one")}))
	assert not tab.gameBox.isChecked() and tab.openBox.isChecked() and tab.referenceBox.isChecked()
	tab.refresh()
	assert "g1" not in drawn(tab) and "a" in drawn(tab)
	tab.gameBox.setChecked(True)
	assert "g1" in drawn(tab)
	tab.close()


def test_every_quest_known_is_drawn_and_the_summary_says_how_many(app, tmp_path):
	tab = make(tmp_path)
	assert drawn(tab) == {"a", "b", "c", "d", "lone", "r1", "x", "g1", "missing"}
	assert tab.graph.nodes["b"].source_name == "bravo.json" and tab.graph.nodes["r1"].source == G.REFERENCE
	assert "9 quests drawn of 9 quests, 7 links." in tab.info.text() and "1 quest that a link names but no file has" in tab.info.text()
	assert [tab.traderBox.itemText(i) for i in range(tab.traderBox.count())][0] == "All traders" and "Prapor" in tab.traderBox.itemText(1)
	assert tab.view.graph_scene.items_by_id["missing"].node.source == G.UNKNOWN  # (the quest nobody has is drawn, dotted)
	tab.close()


def test_the_sources_and_the_trader_filters_choose_what_is_drawn(app, tmp_path):
	tab = make(tmp_path)
	tab.gameBox.setChecked(False)
	assert "g1" not in drawn(tab) and "a" in drawn(tab)
	tab.referenceBox.setChecked(False)
	assert drawn(tab) == {"a", "b", "c", "d", "lone"}  # (the quest nobody has goes with the reference quest that named it)
	tab.openBox.setChecked(False)
	assert drawn(tab) == set()
	tab.openBox.setChecked(True)
	tab.traderBox.setCurrentIndex(tab.traderBox.findData("t2"))
	assert drawn(tab) == {"c", "lone"}  # (Skier's quests among the ones still shown)
	tab.close()


def test_lanes_give_each_trader_rows_of_its_own(app, tmp_path):
	tab = make(tmp_path)
	tab.lanesBox.setChecked(True)
	assert {trader for trader, _first, _last in tab.layout_.lanes} == {"t1", "t2", ""}  # (and one for the quest nobody has)
	tab.lanesBox.setChecked(False)
	assert tab.layout_.lanes == []
	tab.close()


def test_selecting_a_quest_describes_it_and_follows_its_chain(app, tmp_path):
	tab = make(tmp_path)
	scene = tab.view.graph_scene
	tab.view.select("c")
	text = tab.details.text()
	assert "Charlie" in text and "Skier" in text and "level 5" in text and "Bravo (completed)" in text and "Opens 1: Delta" in text
	assert not tab.openButton.isHidden()  # (it is one of yours)
	assert {i for i, item in tab.view.graph_scene.items_by_id.items() if item.opacity() == 1.0} == {"a", "b", "c", "d"}  # (the chain: the rest is dimmed)
	tab.view.select("r1")
	assert tab.openButton.isHidden() and "reference file mod.json" in tab.details.text()
	tab.view.select("missing")
	assert "No file the program has holds this quest" in tab.details.text()
	scene.clearSelection()
	assert all(item.opacity() == 1.0 for item in tab.view.graph_scene.items_by_id.values()) and "Thick border: your quest" in tab.details.text()
	tab.close()


def test_double_clicking_one_of_your_quests_asks_for_it_to_be_opened(app, tmp_path):
	tab = make(tmp_path)
	asked = []
	tab.open_requested.connect(asked.append)
	tab.view.node_activated.emit("r1")  # (a reference quest can't be opened: it is only looked at)
	tab.view.node_activated.emit("g1")
	tab.view.node_activated.emit("b")
	tab.view.select("a")
	tab.openButton.click()
	assert asked == ["b", "a"]
	tab.close()


def test_around_the_selected_quest_draws_only_its_neighbours(app, tmp_path):
	tab = make(tmp_path)
	draws = []
	original = tab.view.show_graph
	tab.view.show_graph = lambda *a, **k: draws.append(1) or original(*a, **k)
	tab.modeBox.setCurrentIndex(tab.modeBox.findData(AROUND))
	draws.clear()
	tab.view.select("b")
	assert drawn(tab) == {"a", "b", "c"} and len(draws) == 1  # (one step each way; drawn once, not again for the selection it makes itself)
	tab.view.select("c")  # (one that is drawn: the picture moves on to what is around it)
	assert drawn(tab) == {"b", "c", "d"} and "Charlie" in tab.details.text()
	tab.view.select("d")
	assert drawn(tab) == {"c", "d", "x"} and "Delta" in tab.details.text()  # (x fails d: always shown with it)
	tab.stepsBox.setValue(0)
	tab.view.select("c")  # (0: all the way)
	assert {"a", "b", "c", "d"} <= drawn(tab) and "lone" not in drawn(tab)
	tab.modeBox.setCurrentIndex(tab.modeBox.findData(EVERYTHING))
	assert "lone" in drawn(tab)
	tab.close()


def test_the_link_filters_hide_links_without_drawing_the_quests_again(app, tmp_path):
	tab = make(tmp_path)
	fails = [e for e in tab.view.graph_scene.edge_items if e.edge.kind == G.FAILS]
	assert fails and all(e.isVisible() for e in fails)
	tab.failsBox.setChecked(False)
	assert not any(e.isVisible() for e in fails) and all(e.isVisible() for e in tab.view.graph_scene.edge_items if e.edge.kind != G.FAILS)
	tab.failsBox.setChecked(True)
	assert all(e.isVisible() for e in fails)
	tab.close()


def test_finding_a_quest_goes_to_it_even_when_it_is_filtered_out(app, tmp_path):
	tab = make(tmp_path)
	assert tab.matches("charlie") == ["c"] and tab.matches("reference one") + tab.matches("game one") == ["r1", "g1"] and tab.matches("") == []  # (yours first, then the reference files, then the game)
	tab.traderBox.setCurrentIndex(tab.traderBox.findData("t1"))
	assert "c" not in drawn(tab)
	tab.search.setText("charlie")
	assert tab.go_to_match() == "c" and "c" in drawn(tab) and tab._current_id() == "c" and tab.traderBox.currentData() == ""
	tab.search.setText("zzz")
	assert tab.go_to_match() is None and tab.info.text() == "No quest matches that."
	tab.close()


def test_the_picture_follows_the_quests_when_the_tab_is_shown_again(app, tmp_path):
	tab = make(tmp_path)
	tab.hide()
	tab.data["sources"].open_quests["new"] = quest("Brand new", [("d", (4,), 0)])
	tab.invalidate()
	assert "new" not in drawn(tab)  # (not showing: nothing is drawn until it is shown)
	tab.show()
	assert "new" in drawn(tab) and any(e.source == "d" and e.target == "new" for e in tab.graph.edges)
	tab.data["sources"].open_quests["newer"] = quest("Newer")
	tab.invalidate()  # (showing: a moment later)
	assert tab._timer.isActive()
	tab._timer.stop()
	tab.refresh()
	assert "newer" in drawn(tab)
	tab.close()


def test_the_drawing_has_a_picture_at_every_zoom(app, tmp_path):
	tab = make(tmp_path)
	view = tab.view
	view.fit()
	assert 0.02 <= view.zoom() <= 1.0
	for zoom in (0.03, 0.2, 0.4, 0.8, 2.0):
		view.resetTransform()
		view.scale(zoom, zoom)
		assert not view.viewport().grab().isNull()  # (a dot, a bar, a card: it paints)
	view.zoom_by(1000)
	assert view.zoom() == pytest.approx(2.5)
	view.zoom_by(1e-9)
	assert view.zoom() == pytest.approx(0.02)
	tab.close()


# --- the mouse ------------------------------------------------------------------------------------------------------------

def screen_point(view, scene_point):
	return view.mapFromScene(QPointF(*scene_point))


def zoomed_in(tab, zoom=1.0):
	view = tab.view
	view.resetTransform()
	view.scale(zoom, zoom)
	view.centerOn(view.graph_scene.items_by_id["b"])
	return view


def test_only_the_card_itself_can_be_hit_not_the_room_around_it(app, tmp_path):
	tab = make(tmp_path)
	view = zoomed_in(tab)
	item = view.graph_scene.items_by_id["b"]
	x, y = item.pos().x(), item.pos().y()
	assert view.itemAt(screen_point(view, (x + 20, y + 20))) is item
	assert view.itemAt(screen_point(view, (x - 40, y + 20))) is not item  # (beside it)
	assert view.itemAt(screen_point(view, (x + 20, y + 60))) is not item  # (below it)
	assert view.itemAt(screen_point(view, (x + 95, y - 25))) is not item  # (above it)
	view.resetTransform()
	view.scale(0.1, 0.1)  # (far out it is a dot: only the dot is hit)
	view.centerOn(item)
	assert view.itemAt(screen_point(view, (x + 95, y + 23))) is item
	assert view.itemAt(screen_point(view, (x + 95 + 400, y + 23))) is not item
	tab.close()


def test_clicking_a_card_selects_it_and_clicking_the_background_does_not_keep_it(app, tmp_path):
	tab = make(tmp_path)
	view = zoomed_in(tab)
	item = view.graph_scene.items_by_id["b"]
	QTest.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=screen_point(view, (item.pos().x() + 20, item.pos().y() + 20)))
	assert item.isSelected() and tab._current_id() == "b"
	QTest.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=screen_point(view, (item.pos().x() - 60, item.pos().y() - 30)))
	assert not item.isSelected()
	tab.close()


def test_dragging_always_moves_the_view_even_from_a_card_and_selects_nothing(app, tmp_path):
	tab = make(tmp_path)
	view = zoomed_in(tab, 1.5)
	item = view.graph_scene.items_by_id["b"]
	start = screen_point(view, (item.pos().x() + 20, item.pos().y() + 20))
	before = (view.horizontalScrollBar().value(), view.verticalScrollBar().value())
	QTest.mousePress(view.viewport(), Qt.MouseButton.LeftButton, pos=start)
	QTest.mouseMove(view.viewport(), start + QPoint(-60, -30))
	QTest.mouseMove(view.viewport(), start + QPoint(-80, -40))
	QTest.mouseRelease(view.viewport(), Qt.MouseButton.LeftButton, pos=start + QPoint(-80, -40))
	after = (view.horizontalScrollBar().value(), view.verticalScrollBar().value())
	assert after == (before[0] + 80, before[1] + 40) and not item.isSelected()
	view.ITEMS_BLOCK_PANNING = True  # (the switch to change it)
	start = screen_point(view, (item.pos().x() + 20, item.pos().y() + 20))
	QTest.mousePress(view.viewport(), Qt.MouseButton.LeftButton, pos=start)
	assert item.isSelected()
	QTest.mouseRelease(view.viewport(), Qt.MouseButton.LeftButton, pos=start)
	tab.close()


def test_dragging_from_the_background_moves_the_view_too(app, tmp_path):
	tab = make(tmp_path)
	view = zoomed_in(tab, 1.5)
	item = view.graph_scene.items_by_id["b"]
	start = screen_point(view, (item.pos().x() - 60, item.pos().y() - 40))
	before = view.horizontalScrollBar().value()
	QTest.mousePress(view.viewport(), Qt.MouseButton.LeftButton, pos=start)
	QTest.mouseMove(view.viewport(), start + QPoint(-50, 0))
	QTest.mouseRelease(view.viewport(), Qt.MouseButton.LeftButton, pos=start + QPoint(-50, 0))
	assert view.horizontalScrollBar().value() == before + 50
	tab.close()


# --- in the window ----------------------------------------------------------------------------------------------------

@pytest.fixture
def window(app, tmp_path, monkeypatch):
	from PySide6.QtWidgets import QMessageBox

	from core.settings import Settings
	from ui import updates
	from ui.main_window import MainWindow

	monkeypatch.setattr("core.references.REFERENCES_FILE", tmp_path / "references.json")
	monkeypatch.setattr(updates, "fetch_remote_version", lambda config: None)
	monkeypatch.setattr("ui.main_window.QMessageBox.question", lambda *a, **k: QMessageBox.StandardButton.Discard)
	win = MainWindow(Settings(), GameData(None, "en", BUNDLED_DATABASE_DIR))
	win.resize(1100, 760)
	yield win
	win.close()


def test_the_quest_graph_tab_is_in_the_window_and_knows_every_source(window, tmp_path):
	from core.documents import Document

	titles = [window.tabs.tabText(i) for i in range(window.tabs.count())]
	assert titles[titles.index("Quest Graph") - 1] == "Composite items" and titles[titles.index("Quest Graph") + 1] == "Find IDs"
	reference = tmp_path / "mod.json"
	reference.write_text(json.dumps({"r1": quest("Ref quest")}), encoding="utf-8")
	window.add_references([str(reference)])
	window._set_quests(Document({"mine": quest("My quest", [("r1", (4,), 0)])}))
	window.show()
	window.tabs.setCurrentWidget(window.graph_tab)
	graph = window.graph_tab.graph
	sources = {graph.nodes[i].source for i in ("mine", "r1", "5936d90786f7742b1420ba5b")}
	assert sources == {G.OPEN, G.REFERENCE, G.GAME} and len(graph.nodes) > 550  # (the base game's quests are in it)
	assert any(e.source == "r1" and e.target == "mine" for e in graph.edges)


def test_changes_in_the_window_reach_the_graph_and_double_clicking_opens_the_quest(window, tmp_path):
	from core.documents import Document

	window._set_quests(Document({"mine": quest("My quest")}))
	window.show()
	window.tabs.setCurrentWidget(window.graph_tab)
	assert "mine" in window.graph_tab.view.graph_scene.items_by_id
	window.tabs.setCurrentWidget(window.quest_outline)
	window.quests.set_value("Edit", ("mine", "QuestName"), "Renamed")
	assert window.graph_tab._stale
	window.tabs.setCurrentWidget(window.graph_tab)
	assert window.graph_tab.graph.nodes["mine"].name == "Renamed" and not window.graph_tab._stale
	window.graph_tab.view.node_activated.emit("mine")
	assert window.tabs.currentWidget() is window.quest_outline and window.quest_outline._current().path[0] == "mine"
	window.tabs.setCurrentWidget(window.graph_tab)
	window.references.add([])  # (nothing)
	window._references_changed()
	assert window.graph_tab._stale or window.graph_tab._timer.isActive()


def test_the_whole_base_game_is_drawn_quickly(app, vanilla_quests):
	import time

	tab = QuestGraphTab(lambda: Sources(game=vanilla_quests, trader_names={"54cb50c76803fa8b248b4571": "Prapor"}))
	tab.gameBox.setChecked(True)  # (off when the tab opens)
	tab.resize(1200, 800)
	tab.show()
	started = time.perf_counter()
	tab.refresh()
	assert time.perf_counter() - started < 5
	assert len(drawn(tab)) == len(vanilla_quests)
	tab.close()
