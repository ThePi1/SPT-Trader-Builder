"""The Zones tab: making and changing your zones on a map, with undo, the checks and the zone file. The map is a
made-up one (a 20 x 20 m floor with a 6 x 6 m upper floor 4 m above it), so the tests don't need the game."""

import gzip
import json
import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication, QMainWindow

from core.documents import Document
from maps import geometry as G
from maps import zones as Z
from tests.test_zones import fake_game
from ui.zones_tab import OWN, ZonesTab

MAP = "bigmap"


@pytest.fixture(scope="module")
def app():
	return QApplication.instance() or QApplication([])


def _write_map(folder, location=MAP, game_version=None, source=None):
	"""An imported map, made up: a 20 x 20 m floor with a 6 x 6 m upper floor 4 m above it, and one game zone."""
	record = {
		"format": 1, "location": location, "game_version": game_version, "source": source and str(source), "imported": "2026-11-20 10:00:00", "scenes": [], "areas": [{"name": "Yard", "scene": "yard", "min": [0, -1, 0], "max": [20, 8, 20], "objects": 0}],
		"zones": [{"id": "game_spot", "kind": "visit", "class": "ExperienceTrigger", "object": "spot", "active": True, "scene": "x.unity",
			"boxes": [{"center": [15, 1, 15], "size": [2, 2, 2], "rotation": [0, 0, 0, 1]}]}],
	}
	(folder / f"{location}.json").write_text(json.dumps(record), encoding="utf-8")
	vertices = [0, 0, 0, 20, 0, 0, 20, 0, 20, 0, 0, 20, 2, 4, 2, 8, 4, 2, 8, 4, 8, 2, 4, 8]
	with gzip.open(folder / f"{location}.navmesh.json.gz", "wt", encoding="utf-8") as f:
		json.dump({"format": 1, "vertices": vertices, "polygons": [[0, 3, 2, 1], [4, 7, 6, 5]]}, f)


@pytest.fixture
def maps(tmp_path):
	"""A maps folder with one imported map: Customs, made up."""
	folder = tmp_path / "maps"
	folder.mkdir()
	_write_map(folder)
	return folder


@pytest.fixture
def tab(app, maps):
	window = QMainWindow()  # (hosted, never shown on its own: see test_no_stray_windows)
	tab = ZonesTab(maps_folder=maps)
	window.setCentralWidget(tab)
	tab.load()
	yield tab
	window.deleteLater()


def test_the_map_its_floor_and_the_games_zones_are_shown(tab):
	assert tab.mapBox.count() == 1 and tab.location == MAP
	assert len(tab.view.floor) == 4  # (two squares, two triangles each)
	ids = [tab.zoneList.topLevelItem(i).text(0) for i in range(tab.zoneList.topLevelItemCount())]
	assert ids == ["game_spot"]
	assert tab.importButton.isVisibleTo(tab) and tab.importButton.text() == "Import the maps again..."  # (after a game update)
	assert not tab.versionLabel.isVisibleTo(tab)  # (the version the map is from wasn't kept: nothing to tell)


def test_a_notice_says_when_the_maps_arent_from_the_game_as_it_is_now(app, tmp_path):
	game = fake_game(tmp_path / "game", "0.16.9.40743")
	maps = tmp_path / "maps"
	maps.mkdir()
	_write_map(maps, game_version="0.16.9.40087", source=game)  # (imported before the game was updated)
	window = QMainWindow()
	tab = ZonesTab(maps_folder=maps)
	window.setCentralWidget(tab)
	tab.load()
	assert tab.versionLabel.isVisibleTo(tab)
	text = tab.versionLabel.text()
	assert "0.16.9.40087" in text and "0.16.9.40743" in text and str(game) in text
	asked = []
	tab.import_maps = asked.append
	tab.versionLabel.linkActivated.emit("import")
	assert asked == [game]  # (from that game, without asking which)
	tab.versionLabel.linkActivated.emit("hide")
	assert not tab.versionLabel.isVisibleTo(tab)
	other = fake_game(tmp_path / "other" / "game", "0.16.9.40087")
	tab.settings = SimpleNamespace(database_folder=str(other / "SPT" / "SPT_Data" / "database"))  # (your SPT database: in another game)
	tab.check_maps_version()
	assert not tab.versionLabel.isVisibleTo(tab)  # (that game is the maps' version)
	tab.game_dir = game  # (given: `zones edit` gives the project's game)
	tab.check_maps_version()
	assert tab.versionLabel.isVisibleTo(tab)
	window.deleteLater()


def _add_walls(folder, location=MAP):
	"""A 6 x 6 m slab whose top is at 8 m over (15, 15), where the floor map has nothing: a roof bots never walk."""
	from maps import walls as W

	class Shapes:
		shapes = {W.BOX: (W._CUBE, W._CUBE_TRIANGLES)}

	W.write(folder / f"{location}.walls.npz", [(W.BOX, W._matrix(G.IDENTITY, (15, 7.5, 15), (1, 1, 1), (6, 1, 6)))], Shapes())


def test_a_zone_placed_on_a_roof_only_the_walls_know_sits_on_it(app, maps):
	_add_walls(maps)
	window = QMainWindow()
	tab = ZonesTab(maps_folder=maps)
	window.setCentralWidget(tab)
	tab.load()
	assert tab.view.walls is not None and len(tab.view.walls) == 12 and tab.wallsBox.isEnabled()
	tab.place_at((15.0, 8.0, 15.0))
	assert tab.mine[0].box.center[1] == pytest.approx(8 - Z.SINK + 1.5)
	assert tab.checksList.item(0).text() == "No problems found."  # (the roof counts as floor for the checks too)
	window.deleteLater()


def test_the_height_slider_hides_what_is_above_a_storey_of_what_the_view_looks_at(tab):
	from ui.view3d.view import NO_CUT

	tab.view.camera.target = (5.0, 0.0, 5.0)  # (over the upper floor)
	tab.view.view_moved.emit(tab.view.camera.target)
	slider = tab.cutSlider
	assert slider.storeys == pytest.approx([0.0, 4.0])
	slider.step(False)
	assert tab.view.cut == pytest.approx(6.2)  # (the upper storey, and 2.2 m of its walls)
	slider.step(False)
	assert tab.view.cut == pytest.approx(2.2)  # (the ground floor: the upper one is hidden)
	tab.view.camera.target = (15.0, 0.0, 15.0)
	tab.view.view_moved.emit(tab.view.camera.target)
	assert slider.storeys == pytest.approx([0.0]) and tab.view.cut == pytest.approx(2.2)  # (the cut stays where it was)
	slider.set_value(None)
	assert tab.view.cut >= NO_CUT
	tab.view.camera.target = (30.0, -300.0, 30.0)  # (off the floor, far below it: no storeys there)
	tab.view.view_moved.emit(tab.view.camera.target)
	assert slider.storeys == [] and (slider.low, slider.high) == pytest.approx((0.0, 6.2))  # (the map's floors, to 2.2 m above the top one)


def test_only_the_last_few_maps_walls_are_kept_in_memory(app, maps):
	from ui.zones_tab import KEEP_WALLS

	keys = [MAP, "Woods", "Shoreline", "Interchange"]
	for key in keys:
		if key != MAP:
			_write_map(maps, key)
		_add_walls(maps, key)
	window = QMainWindow()
	tab = ZonesTab(maps_folder=maps)
	window.setCentralWidget(tab)
	tab.load()
	for key in keys:
		tab.set_map(key)
	assert [key for key in keys if tab.index.map(key)._walls is not None] == keys[-KEEP_WALLS:]
	tab.set_map(MAP)  # (going back reads them again, and lets go of the oldest kept)
	assert tab.view.walls is not None and len(tab.view.walls) == 12
	assert tab.index.map(keys[1])._walls is None
	window.deleteLater()


def test_reading_a_map_says_how_far_along_it_is_and_a_map_in_memory_says_nothing(app, maps):
	_add_walls(maps)
	_write_map(maps, "Woods")
	_add_walls(maps, "Woods")
	window = QMainWindow()
	tab = ZonesTab(maps_folder=maps)
	window.setCentralWidget(tab)
	said = []
	panel_say = tab.loadingPanel.say
	tab.loadingPanel.say = lambda text, fraction: (said.append((text, fraction)), panel_say(text, fraction))
	tab.load()  # (shows Customs first)
	assert list(dict.fromkeys(text for text, _f in said)) == ["Reading the floor map", "Reading the walls", "Working out where players can stand"]
	fractions = [f for _t, f in said]
	assert fractions[0] == 0.0 and fractions[-1] == pytest.approx(1.0) and fractions == sorted(fractions)
	assert tab.loadingPanel.isHidden() and tab.view.walls is not None
	said.clear()
	tab.set_map("Woods")
	assert said and tab.loadingPanel.isHidden()
	said.clear()
	tab.set_map(MAP)  # (still in memory: nothing to read, no panel)
	assert said == []
	window.deleteLater()


def test_factory_by_day_is_shown_first(app, maps):
	_write_map(maps, "factory4_day")
	window = QMainWindow()
	tab = ZonesTab(maps_folder=maps)
	window.setCentralWidget(tab)
	tab.load()
	assert tab.location == "factory4_day"  # (not Customs: it comes first in the list, but takes seconds to read)
	window.deleteLater()


def test_the_map_box_is_as_wide_as_its_longest_name(app, maps):
	_write_map(maps, "Sandbox")
	window = QMainWindow()
	tab = ZonesTab(map_names={MAP: "Customs", "Sandbox": "Ground Zero (Sandbox)"}, maps_folder=maps)
	window.setCentralWidget(tab)
	tab.load()
	assert tab.mapBox.sizeHint().width() > tab.mapBox.fontMetrics().horizontalAdvance("Ground Zero (Sandbox)")  # (and its list, as wide)
	window.deleteLater()


def test_the_maps_are_read_once_the_tab_is_drawn_so_the_loading_panel_shows(app, maps):
	window = QMainWindow()
	tab = ZonesTab(maps_folder=maps)
	window.setCentralWidget(tab)
	shown = []
	panel_say = tab.loadingPanel.say
	tab.loadingPanel.say = lambda text, fraction: (panel_say(text, fraction), shown.append(tab.loadingPanel.isVisible()))
	window.show()
	assert tab.location is None  # (not in the show event: the window doesn't draw the tab until the show is over)
	for _ in range(3):
		QApplication.processEvents()
	assert tab.location == MAP and shown and all(shown) and tab.loadingPanel.isHidden()
	window.close()
	window.deleteLater()


def test_placing_a_zone_puts_it_on_the_floor_clicked(tab):
	record = tab.place_at((5.0, 0.0, 5.0))
	assert record["ZoneLocation"] == MAP and record["ZoneType"] == "visit"
	assert tab.doc.data == [record] and tab.selected == (OWN, 0)
	box = tab.mine[0].box
	assert box.center == pytest.approx((5, -Z.SINK + 1.5, 5)) and box.size == (4, 3, 4)
	assert tab.xSpin.value() == pytest.approx(5) and tab.idEdit.text() == record["ZoneId"]
	assert tab.checksList.item(0).text() == "No problems found."
	assert tab.view.samples and all(ok for _p, ok in tab.view.samples)
	upper = tab.place_at((5.0, 4.0, 5.0))  # (on the upper floor: the floor nearest the spot clicked)
	assert tab.mine[1].box.center[1] == pytest.approx(4 - Z.SINK + 1.5) and upper["ZoneId"] != record["ZoneId"]


def test_the_form_changes_the_zone_and_typing_in_one_field_is_one_undo_step(tab):
	tab.place_at((5.0, 0.0, 5.0))
	for value in (6.0, 7.0, 8.0):
		tab.xSpin.setValue(value)
	assert tab.doc.data[0]["Position"]["X"] == "8"
	tab.widthSpin.setValue(6.0)
	assert tab.doc.data[0]["Scale"]["X"] == "6"
	tab.idEdit.setText("my_zone")
	tab.idEdit.textEdited.emit("my_zone")
	assert tab.doc.data[0]["ZoneId"] == "my_zone"
	tab.doc.undo()  # (the id)
	tab.doc.undo()  # (the width)
	tab.doc.undo()  # (all three x values)
	assert tab.doc.data[0]["Position"]["X"] == "5" and tab.xSpin.value() == pytest.approx(5)


def test_dragging_in_the_view_changes_the_zone_when_the_drag_ends(tab):
	tab.place_at((5.0, 0.0, 5.0))
	moved = G.Box((9, 1.25, 9), (4, 3, 4), G.yaw_rotation(30))
	tab.view.box_changing.emit(moved)
	assert tab.xSpin.value() == pytest.approx(9) and tab.doc.data[0]["Position"]["X"] == "5"  # (the file waits for the end)
	tab.view.box_edited.emit(moved)
	assert tab.doc.data[0]["Position"]["X"] == "9" and G.yaw_of(tab.mine[0].box.rotation) == pytest.approx(30)
	assert tab.doc.undo_label == "Move zone"


def test_sit_on_floor_and_cover_the_slope(tab):
	tab.place_at((5.0, 0.0, 5.0))
	tab.ySpin.setValue(2.0)
	tab.sit_on_floor()
	assert tab.mine[0].box.center[1] == pytest.approx(-Z.SINK + 1.5)
	tab.cover_slope()  # (the floor under it is level)
	assert "level" in tab.statusLabel.text()


def test_a_zone_far_above_the_floor_is_warned_about(tab):
	tab.place_at((15.0, 0.0, 5.0))
	tab.ySpin.setValue(20.0)
	texts = [tab.checksList.item(i).text() for i in range(tab.checksList.count())]
	assert any(t.startswith("Warning: ") and "above the reach" in t for t in texts)
	assert not all(ok for _p, ok in tab.view.samples)


def test_a_game_zone_is_read_only_and_can_be_copied(tab):
	tab.select(("base", 0))
	assert not tab.idEdit.isEnabled() and tab.copyButton.isEnabled() and not tab.deleteButton.isEnabled()
	record = tab.copy_selected()
	assert record["ZoneId"] == "game_spot_copy" and record["Position"]["X"] == "15"
	assert tab.selected == (OWN, 0) and tab.idEdit.isEnabled()


def test_deleting_and_undoing(tab):
	tab.place_at((5.0, 0.0, 5.0))
	tab.delete_selected()
	assert tab.doc.data == [] and tab.selected is None
	tab.doc.undo()
	assert len(tab.doc.data) == 1


def test_finding_a_zone_selects_it(tab):
	found = tab.find("game_spot")
	assert found[0]["kind"] == "zone" and tab.selected == ("base", 0)


def test_the_file_is_saved_as_a_zone_file_and_opened_again(tab, tmp_path):
	tab.place_at((5.0, 0.0, 5.0))
	path = tmp_path / "zones.json"
	tab.doc.save(path)
	zones, problems = Z.read_zone_file(path)
	assert len(zones) == 1 and not problems
	tab.set_document(Document([]))
	tab.open_file(path)
	assert len(tab.mine) == 1 and not tab.doc.dirty


def test_entries_that_cant_be_read_are_listed_not_dropped(tab):
	tab.set_document(Document([{"ZoneId": "broken", "ZoneType": "nonsense"}]))
	assert 0 in tab.broken and not tab.mine
	assert "(entry 1)" in [tab.zoneList.topLevelItem(i).text(0) for i in range(tab.zoneList.topLevelItemCount())]


def test_a_reference_zone_file_opened_here_is_listed_once_and_its_ids_arent_used_twice(app, maps, tmp_path):
	from core.references import References

	path = tmp_path / "my_zones.json"
	path.write_text(json.dumps([Z.zone_record("my_spot", MAP, Z.VISIT, G.Box((5, 1, 5), (2, 2, 2)))]), encoding="utf-8")
	refs = References.of([path])
	window = QMainWindow()
	tab = ZonesTab(references=refs, maps_folder=maps)
	window.setCentralWidget(tab)
	tab.load()
	listed = lambda: sorted((tab.zoneList.topLevelItem(i).text(0), tab.zoneList.topLevelItem(i).text(2)) for i in range(tab.zoneList.topLevelItemCount()))
	assert listed() == [("game_spot", "the game"), ("my_spot", "my_zones.json")]  # (a reference: read only)
	tab.open_file(path)
	assert listed() == [("game_spot", "the game"), ("my_spot", "your file")] and not refs.zone_files()
	tab.doc.change("Move", lambda data: data[0]["Position"].update(X="7"))
	assert tab.mine[0].box.center[0] == 7
	tab.select((OWN, 0))
	assert [tab.checksList.item(i).text() for i in range(tab.checksList.count())] == ["No problems found."]
	tab.set_document(Document([]))  # (another file in its place: the one on disk is a reference again)
	assert listed() == [("game_spot", "the game"), ("my_spot", "my_zones.json")]
	window.deleteLater()


def test_the_main_windows_quest_checks_know_the_zones_made_in_the_tab(app, tmp_path, monkeypatch):
	from core.gamedata import GameData
	from core.paths import BUNDLED_DATABASE_DIR
	from core.settings import Settings
	from ui import updates
	from ui.main_window import MainWindow

	monkeypatch.setattr(updates, "fetch_remote_version", lambda config: None)
	window = MainWindow(Settings.load(tmp_path / "none.ini"), GameData(None, "en", BUNDLED_DATABASE_DIR))
	record = Z.zone_record("tab_zone", MAP, Z.VISIT, G.Box((1, 1, 1), (2, 2, 2)))
	window.zones_tab.doc.change("Add zone", lambda data: data.append(record))
	assert window.zone_index().by_id("tab_zone")
	assert window.zones_tab.doc in window._docs() and window.windowTitle().endswith("*")
	window.undo()
	assert window.zones_tab.doc.data == []
