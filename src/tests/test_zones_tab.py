"""The Zones tab: making and changing your zones on a map, with undo, the checks and the zone file. The map is a
made-up one (a 20 x 20 m floor with a 6 x 6 m upper floor 4 m above it), so the tests don't need the game."""

import gzip
import json
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication, QMainWindow

from core.documents import Document
from maps import geometry as G
from maps import zones as Z
from ui.zones_tab import OWN, ZonesTab

MAP = "bigmap"


@pytest.fixture(scope="module")
def app():
	return QApplication.instance() or QApplication([])


@pytest.fixture
def maps(tmp_path):
	"""A maps folder with one imported map: Customs, made up."""
	folder = tmp_path / "maps"
	folder.mkdir()
	record = {
		"format": 1, "location": MAP, "scenes": [], "areas": [{"name": "Yard", "scene": "yard", "min": [0, -1, 0], "max": [20, 8, 20], "objects": 0}],
		"zones": [{"id": "game_spot", "kind": "visit", "class": "ExperienceTrigger", "object": "spot", "active": True, "scene": "x.unity",
			"boxes": [{"center": [15, 1, 15], "size": [2, 2, 2], "rotation": [0, 0, 0, 1]}]}],
	}
	(folder / f"{MAP}.json").write_text(json.dumps(record), encoding="utf-8")
	vertices = [0, 0, 0, 20, 0, 0, 20, 0, 20, 0, 0, 20, 2, 4, 2, 8, 4, 2, 8, 4, 8, 2, 4, 8]
	with gzip.open(folder / f"{MAP}.navmesh.json.gz", "wt", encoding="utf-8") as f:
		json.dump({"format": 1, "vertices": vertices, "polygons": [[0, 3, 2, 1], [4, 7, 6, 5]]}, f)
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
	assert not tab.importButton.isVisibleTo(tab)


def _add_walls(folder):
	"""A 6 x 6 m slab whose top is at 8 m over (15, 15), where the floor map has nothing: a roof bots never walk."""
	from maps import walls as W

	class Shapes:
		shapes = {W.BOX: (W._CUBE, W._CUBE_TRIANGLES)}

	W.write(folder / f"{MAP}.walls.npz", [(W.BOX, W._matrix(G.IDENTITY, (15, 7.5, 15), (1, 1, 1), (6, 1, 6)))], Shapes())


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
