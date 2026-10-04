"""The window icon."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication

from core import paths
from core.gamedata import GameData
from core.paths import BUNDLED_DATABASE_DIR, ICON_FILE
from core.settings import Settings
from ui import main_window, updates
from ui.main_window import MainWindow, app_icon


@pytest.fixture(scope="module")
def app():
	return QApplication.instance() or QApplication([])


def test_the_icon_file_ships_in_the_data_folder_and_is_a_real_icon(app):
	assert ICON_FILE == paths.DATA_DIR / "icon.ico" and ICON_FILE.is_file()
	icon = app_icon()
	assert not icon.isNull() and not icon.pixmap(32, 32).isNull()


def test_the_main_window_uses_it(app, tmp_path, monkeypatch):
	monkeypatch.setattr(updates, "fetch_remote_version", lambda config: None)
	window = MainWindow(Settings(path=tmp_path / "settings.ini"), GameData(None, "en", BUNDLED_DATABASE_DIR))
	assert not window.windowIcon().isNull()


def test_a_missing_icon_file_means_no_icon_not_a_crash(app, tmp_path, monkeypatch):
	monkeypatch.setattr(main_window, "ICON_FILE", tmp_path / "gone.ico")
	assert app_icon().isNull()
