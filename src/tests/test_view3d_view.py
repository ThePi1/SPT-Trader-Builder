"""The 3D view with the mouse (clicks and drags go through the camera and the picking, so no OpenGL is needed), and
one real drawing in a process of its own (skipped where there is no OpenGL at all)."""

import os
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from maps import geometry as G
from maps.navmesh import NavMesh
from maps.triangles import Triangles
from ui.view3d import handles as H
from ui.view3d.view import GAME, MapView, ViewZone

SRC = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def app():
	return QApplication.instance() or QApplication([])


@pytest.fixture
def view(app):
	view = MapView()
	view.resize(800, 600)
	view.set_floor(Triangles.from_navmesh(NavMesh([(0, 0, 0), (40, 0, 0), (40, 0, 40), (0, 0, 40)], [((0, 3, 2, 1), 0)])))
	view.camera.target, view.camera.distance, view.camera.top_down = (20.0, 0.0, 20.0), 30.0, True
	yield view
	view.deleteLater()


def _signal(signal):
	got = []
	signal.connect(got.append)
	return got


def test_a_click_while_placing_gives_the_spot_on_the_floor(view):
	placed = _signal(view.place_requested)
	view.set_placing(True)
	QTest.mouseClick(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(400, 300))
	assert placed and placed[0] == pytest.approx((20, 0, 20), abs=0.1)
	east = view.camera.project((25, 0, 20), 800, 600)
	QTest.mouseClick(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(round(east[0]), round(east[1])))
	assert placed[-1] == pytest.approx((25, 0, 20), abs=0.1)


def test_a_click_selects_the_smallest_zone_there(view):
	view.set_zones([
		(ViewZone("big", "big", "visit", G.Box((20, 1, 20), (30, 2, 30))), GAME),
		(ViewZone("small", "small", "placeitem", G.Box((20, 1, 20), (2, 2, 2))), GAME),
	])
	clicked = _signal(view.zone_clicked)
	QTest.mouseClick(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(400, 300))
	far = view.camera.project((30, 2, 30), 800, 600)
	QTest.mouseClick(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(round(far[0]), round(far[1])))
	edge = view.camera.project((38, 2, 38), 800, 600)
	QTest.mouseClick(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(round(edge[0]), round(edge[1])))
	assert clicked == ["small", "big", None]


def test_dragging_a_face_handle_resizes_the_zone(view):
	box = G.Box((20, 1, 20), (4, 2, 4))
	view.set_selected("mine", box, "visit", editable=True)
	changing, edited = _signal(view.box_changing), _signal(view.box_edited)
	east = next(h for h in H.handles(box) if h.kind == H.SIZE and h.axis == 0 and h.side == 1)
	start = view.camera.project(east.position, 800, 600)
	end = view.camera.project((25, 1, 20), 800, 600)
	QTest.mousePress(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(round(start[0]), round(start[1])))
	QTest.mouseMove(view, QPoint(round(start[0]) + 10, round(start[1])))
	_move(view, end, Qt.MouseButton.LeftButton)
	QTest.mouseRelease(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(round(end[0]), round(end[1])))
	assert changing and edited and edited[0].size[0] == pytest.approx(7, abs=0.1) and edited[0].center[0] == pytest.approx(21.5, abs=0.05)


def test_dragging_elsewhere_pans_the_top_down_view(view):
	before = view.camera.target
	QTest.mousePress(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(400, 300))
	_move(view, (500, 300), Qt.MouseButton.LeftButton)
	QTest.mouseRelease(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(500, 300))
	assert view.camera.target[0] < before[0] and view.camera.target[2] == pytest.approx(before[2])


def test_zooming_out_keeps_the_view_on_the_map(view):
	"""However far it zooms out with the mouse over a spot, what the view looks at stays over the floor and at its height."""
	from PySide6.QtCore import QPointF
	from PySide6.QtGui import QWheelEvent

	view.set_top_down(False)
	view.camera.pitch, view.camera.distance = 30.0, 20.0
	spot = QPointF(400, 120)  # (the far part of the floor)
	for _ in range(30):
		QApplication.sendEvent(view, QWheelEvent(spot, view.mapToGlobal(spot), QPoint(), QPoint(0, -120), Qt.MouseButton.NoButton,
			Qt.KeyboardModifier.NoModifier, Qt.ScrollPhase.NoScrollPhase, False))
	x, y, z = view.camera.target
	assert y == pytest.approx(0.0) and -50 <= x <= 90 and -50 <= z <= 90
	view.camera.target = (500.0, -300.0, 20.0)  # (a camera from before, gone astray)
	view.keep_on_map()
	assert view.camera.target == pytest.approx((90.0, 0.0, 20.0))


def _move(view, spot, button):
	"""A mouse move with the button held (QTest.mouseMove sends none held)."""
	from PySide6.QtCore import QPointF
	from PySide6.QtGui import QMouseEvent

	point = QPointF(spot[0], spot[1])
	event = QMouseEvent(QMouseEvent.Type.MouseMove, point, view.mapToGlobal(point), Qt.MouseButton.NoButton, button, Qt.KeyboardModifier.NoModifier)
	QApplication.sendEvent(view, event)


DRAW = r'''
import os, sys
os.environ["QT_OPENGL"] = "software"
os.environ.pop("QT_QPA_PLATFORM", None)
sys.path.insert(0, sys.argv[1])
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication
app = QApplication([])
from maps import geometry as G
from maps.navmesh import NavMesh
from maps.triangles import Triangles
from ui.view3d.view import MapView, ViewZone, MINE
view = MapView()
view.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen)
view.resize(300, 200)
view.set_floor(Triangles.from_navmesh(NavMesh([(0, 0, 0), (40, 0, 0), (40, 0, 40), (0, 0, 40)], [((0, 3, 2, 1), 0)])))
view.set_zones([(ViewZone("z", "z", "placeitem", G.Box((10, 1, 20), (6, 2, 6))), MINE)])
view.camera.target, view.camera.distance, view.camera.top_down = (20.0, 0.0, 20.0), 25.0, True
view.show()
def done():
	if view.gl_problem:
		print("NOGL", view.gl_problem)
	else:
		image = view.grabFramebuffer()
		print("PIXELS", hex(image.pixel(150, 100)), hex(image.pixel(2, 2)), hex(image.pixel(round(view.camera.project((10, 2, 20), 300, 200)[0]), 100)))
	app.quit()
QTimer.singleShot(200, done)
app.exec()
'''


def _draw(tmp_path, source):
	"""Run a drawing script in a process of its own (software OpenGL) and give its PIXELS numbers; skip without OpenGL."""
	script = tmp_path / "draw.py"
	script.write_text(source, encoding="utf-8")
	env = dict(os.environ)
	env.pop("QT_QPA_PLATFORM", None)
	result = subprocess.run([sys.executable, str(script), str(SRC)], capture_output=True, text=True, timeout=60, env=env)
	line = next((l for l in result.stdout.splitlines() if l.startswith(("PIXELS", "NOGL"))), "")
	if not line or line.startswith("NOGL"):
		pytest.skip(f"no OpenGL here: {line or result.stderr[-300:]}")
	return [int(v, 16) for v in line.split()[1:]]


def test_the_view_really_draws_the_floor_and_the_zones(tmp_path):
	middle, corner, zone = _draw(tmp_path, DRAW)
	background = 0xFF1C1F24
	assert middle != background and corner != background  # (the floor covers the view)
	assert (zone >> 16 & 0xFF) > (zone & 0xFF)  # (the orange placeitem zone tints the floor there)


DRAW_CUT = r'''
import os, sys
os.environ["QT_OPENGL"] = "software"
os.environ.pop("QT_QPA_PLATFORM", None)
sys.path.insert(0, sys.argv[1])
import numpy as np
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication
app = QApplication([])
from maps import walls as W
from maps.navmesh import NavMesh
from maps.triangles import Triangles
from ui.view3d.view import MapView
view = MapView()
view.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen)
view.resize(300, 200)
view.set_floor(Triangles.from_navmesh(NavMesh([(0, 0, 0), (40, 0, 0), (40, 0, 40), (0, 0, 40)], [((0, 3, 2, 1), 0)])))
closed = W._CUBE[W._CUBE_TRIANGLES] * [8, 4, 8] + [24, 3, 20]  # (from 1 to 5 m up)
open_ = (W._CUBE[W._CUBE_TRIANGLES] * [6, 4, 6] + [10, 3, 20])[[i for i in range(12) if i not in (4, 5)]]  # (no bottom, as most of the game's walls)
view.set_walls(Triangles(np.concatenate([closed, open_])))
view.camera.target, view.camera.distance, view.camera.top_down = (17.0, 0.0, 20.0), 30.0, True
view.show()
def pixel(image, point):
	x, y = view.camera.project(point, 300, 200)
	return image.pixel(round(x), round(y))
def done():
	if view.gl_problem:
		print("NOGL", view.gl_problem)
	else:
		whole = view.grabFramebuffer()
		view.set_cut(3.0)
		cut = view.grabFramebuffer()
		x, y = view.camera.project((7, 3, 20), 300, 200)  # (the open box's west wall)
		edge = [cut.pixel(round(x) + dx, round(y) + dy) for dx in range(-2, 3) for dy in range(-2, 3)]
		print("PIXELS", hex(pixel(whole, (24, 5, 20))), hex(pixel(cut, (24, 1, 20))), hex(pixel(cut, (10, 0, 20))), *[hex(p) for p in edge])
	app.quit()
QTimer.singleShot(200, done)
app.exec()
'''


def test_a_cut_draws_the_walls_it_slices_through_as_solid(tmp_path):
	"""From straight above: a closed box's inside is the cap colour; a box open at the bottom shows the floor inside,
	and its walls' outline at the cut."""
	from ui.view3d.view import CAP_COLOUR

	top, inside, open_inside, *edge = _draw(tmp_path, DRAW_CUT)
	cap = tuple(round(c * 255) for c in CAP_COLOUR)

	def is_cap(p):
		return all(abs(a - b) <= 8 for a, b in zip(((p >> 16) & 0xFF, (p >> 8) & 0xFF, p & 0xFF), cap))

	assert not is_cap(top) and is_cap(inside)  # (uncut, the box's top; cut, its inside)
	assert not is_cap(open_inside) and any(is_cap(p) for p in edge)
