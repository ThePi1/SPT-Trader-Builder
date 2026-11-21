"""The height slider beside the 3D view: where it stops for each storey, dragging (snapping to them, or free with
Shift), the wheel and the keys, and the heights its track spans (the map's, wherever the view looks)."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from ui.view3d.cut_slider import CutSlider


@pytest.fixture(scope="module")
def app():
	return QApplication.instance() or QApplication([])


@pytest.fixture
def slider(app):
	slider = CutSlider()
	slider.resize(58, 400)
	slider.set_range(-5.0, 20.0)
	slider.set_storeys([0.0, 3.0, 6.0])
	yield slider
	slider.deleteLater()


def _changes(slider):
	got = []
	slider.cut_changed.connect(got.append)
	return got


def test_it_stops_above_each_storey(slider):
	assert slider.stops() == pytest.approx([2.2, 5.2, 8.2])
	slider.set_storeys([0.0, 1.5])  # (a storey nearer than 2.2 m: it stops just under it)
	assert slider.stops() == pytest.approx([1.2, 3.7])
	slider.set_storeys([-10.0, 0.0, 19.0])  # (stops off the track are left out)
	assert slider.stops() == pytest.approx([2.2])


def test_the_keys_and_the_wheel_go_a_storey_at_a_time(slider):
	got = _changes(slider)
	for _ in range(4):
		QTest.keyClick(slider, Qt.Key.Key_Down)
	assert got == pytest.approx([8.2, 5.2, 2.2])  # (it stays at the lowest)
	QTest.keyClick(slider, Qt.Key.Key_Up)
	QTest.keyClick(slider, Qt.Key.Key_Home)
	QTest.keyClick(slider, Qt.Key.Key_End)
	assert got[3:] == [pytest.approx(5.2), None, pytest.approx(2.2)]
	for notches in (1, 1, 1):
		middle = QPointF(29, 200)
		event = QWheelEvent(middle, slider.mapToGlobal(middle), QPoint(), QPoint(0, 120 * notches), Qt.MouseButton.NoButton,
			Qt.KeyboardModifier.NoModifier, Qt.ScrollPhase.NoScrollPhase, False)
		QApplication.sendEvent(slider, event)
	assert got[6:] == [pytest.approx(5.2), pytest.approx(8.2), None]  # (up from the top storey shows everything)


def test_dragging_lands_on_a_storey_near_it_unless_shift_is_held(slider):
	near = round(slider.y_of(5.2) + 6)
	QTest.mousePress(slider, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(29, near))
	QTest.mouseRelease(slider, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(29, near))
	assert slider.value() == pytest.approx(5.2)
	QTest.mousePress(slider, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ShiftModifier, QPoint(29, near))
	QTest.mouseRelease(slider, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ShiftModifier, QPoint(29, near))
	assert slider.value() == pytest.approx(slider.height_at(near, free=True), abs=0.01) and slider.value() < 5.1
	QTest.mousePress(slider, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(29, 4))  # (the top: everything)
	assert slider.value() is None
	slider.set_value(2.2)
	QTest.mouseDClick(slider, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(29, 300))
	assert slider.value() is None


def test_with_no_storeys_it_goes_a_metre_at_a_time_from_the_top(slider):
	slider.set_storeys([])
	got = _changes(slider)
	slider.step(False)
	slider.step(False)
	slider.step(True)
	slider.step(True)
	assert got == [pytest.approx(20.0), pytest.approx(19.0), pytest.approx(20.0), None]


def test_the_track_and_the_height_chosen_stay_when_the_view_moves(slider):
	slider.set_value(5.2)
	slider.set_storeys([10.0, 13.0])  # (another building: other ticks, the same track and cut)
	assert slider.value() == pytest.approx(5.2) and (slider.low, slider.high) == (-5.0, 20.0)
