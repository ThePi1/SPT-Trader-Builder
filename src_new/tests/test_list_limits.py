"""The settings for how many entries a list shows, and the Locale tab / menu names."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from core import settings as S
from core.settings import Settings, SettingsError

LIMIT_KEYS = ("locale_max_entries", "lookup_max_rows", "problems_max_shown", "explorer_max_problems")


def ini(tmp_path, text="[general]\ndebug_logging = false\n"):
	path = tmp_path / "settings.ini"
	path.write_text(text, encoding="utf-8")
	return path


# --- the settings themselves ----------------------------------------------------------------


def test_every_limit_has_a_default_and_loads_from_the_file(tmp_path):
	settings = Settings.load(ini(tmp_path))
	assert [getattr(settings, k) for k in LIMIT_KEYS] == [5000, 400, 300, 500]
	settings = Settings.load(ini(tmp_path, "[lists]\nlocale_max_entries = 12\nlookup_max_rows = 99999\n"))
	assert (settings.locale_max_entries, settings.lookup_max_rows) == (12, 99999)


@pytest.mark.parametrize("bad", ["lots", "5", "0", "-20", "100001", "1.5", ""])
def test_a_bad_limit_in_the_file_is_reported(tmp_path, bad):
	with pytest.raises(SettingsError, match="locale_max_entries"):
		Settings.load(ini(tmp_path, f"[lists]\nlocale_max_entries = {bad}\n"))


def test_update_validates_and_saves_limits_keeping_the_comments(tmp_path):
	path = ini(tmp_path, "# keep me\n[lists]\n# the locale tab\nlocale_max_entries = 5000\n")
	settings = Settings.load(path)
	with pytest.raises(ValueError):
		settings.update({"lookup_max_rows": 3})
	with pytest.raises(ValueError):
		settings.update({"lookup_max_rows": True})
	assert settings.lookup_max_rows == 400
	settings.update({"locale_max_entries": 250, "lookup_max_rows": 50})
	text = path.read_text(encoding="utf-8")
	assert "# keep me" in text and "# the locale tab" in text and "locale_max_entries = 250" in text and "lookup_max_rows = 50" in text
	assert Settings.load(path).locale_max_entries == 250


def test_limit_falls_back_to_the_default_for_missing_or_odd_settings():
	assert S.limit(None, "locale_max_entries") == 5000

	class Odd:
		lookup_max_rows = 0

	assert S.limit(Odd(), "lookup_max_rows") == 400
	assert S.limit(Settings({"lookup_max_rows": 7}), "lookup_max_rows") == 7


def test_the_shipped_settings_file_lists_every_limit_with_its_default():
	shipped = Settings.load(S.SETTINGS_FILE)
	for key in LIMIT_KEYS:
		assert getattr(shipped, key) == S.BY_KEY[key].default


# --- the lists and the window -----------------------------------------------------------------

pytest.importorskip("PySide6")
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QSpinBox

from core.documents import Document
from core.gamedata import GameData
from core.paths import BUNDLED_DATABASE_DIR
from schema.issues import ERROR, Issue
from ui import updates
from ui.dialogs import SettingsDialog
from ui.explorer_tab import CheckPage
from ui.locale_tab import LocaleTab
from ui.lookup_view import LookupView
from ui.main_window import MainWindow
from ui.problems import ProblemsPanel
from core import lookup  # noqa: E402


@pytest.fixture(scope="module")
def app():
	return QApplication.instance() or QApplication([])


def settings_with(tmp_path, **values):
	settings = Settings.load(ini(tmp_path))
	for key, value in values.items():
		setattr(settings, key, value)
	return settings


def test_the_locale_tab_shows_no_more_than_the_limit(app, tmp_path):
	locale = Document({f"key{i}": f"text {i}" for i in range(30)})
	tab = LocaleTab(locale, Document({}), settings_with(tmp_path, locale_max_entries=12))
	assert len(tab.model.keys) == 12 and "first 12 of 30" in tab.note.text()
	tab.model.settings.locale_max_entries = 40
	tab.refresh()
	assert len(tab.model.keys) == 30 and tab.note.text() == "30 entries."


def test_find_ids_shows_no_more_than_the_limit(app, tmp_path):
	rows = [lookup.Row(id=f"{i:024x}", name=f"Thing {i}", kind="item", detail="") for i in range(30)]
	view = LookupView(rows, settings=settings_with(tmp_path, lookup_max_rows=10))
	assert view.table.rowCount() == 10 and "first 10 of 30" in view.note.text()
	view.settings.lookup_max_rows = 100
	view.refresh()
	assert view.table.rowCount() == 30


def test_the_problems_list_shows_no_more_than_the_limit_and_says_how_many_are_left(app, tmp_path):
	panel = ProblemsPanel(settings_with(tmp_path, problems_max_shown=10))
	panel.show_issues([Issue(ERROR, ("q",), f"bad {i}") for i in range(25)], lambda path: "")
	assert panel.list.count() == 11 and "15 more" in panel.list.item(10).text()
	assert "25 to fix" in panel.header.text()  # (the header always has the real total)
	panel.show_issues([Issue(ERROR, ("q",), "bad")] * 3, lambda path: "")
	assert panel.list.count() == 3


def test_the_file_check_shows_no_more_than_the_limit(app, tmp_path, monkeypatch):
	monkeypatch.setattr("ui.explorer_tab.explorer.check", lambda *args: [Issue(ERROR, ("k",), f"bad {i}") for i in range(30)])
	page = CheckPage(lambda: {}, lambda: {}, None, settings_with(tmp_path, explorer_max_problems=10))
	path = tmp_path / "locale.json"
	path.write_text('{"a": "b"}', encoding="utf-8")
	page.load(str(path))
	assert page.list.count() == 11 and "20 more" in page.list.item(10).text()
	assert "30 to fix" in page.summary.text()


def test_the_settings_dialog_edits_the_limits(app, tmp_path):
	settings = settings_with(tmp_path)
	dialog = SettingsDialog(settings, None)
	spins = {key: dialog.controls[key] for key in LIMIT_KEYS}
	assert all(isinstance(spin, QSpinBox) for spin in spins.values())
	assert [spin.value() for spin in spins.values()] == [5000, 400, 300, 500]
	spins["lookup_max_rows"].setValue(150)
	dialog.accept()
	assert settings.lookup_max_rows == 150
	assert Settings.load(tmp_path / "settings.ini").lookup_max_rows == 150


def window(tmp_path, monkeypatch, **values):
	monkeypatch.setattr(updates, "fetch_remote_version", lambda config: None)
	return MainWindow(settings_with(tmp_path, **values), GameData(None, "en", BUNDLED_DATABASE_DIR))


def test_changing_a_limit_in_the_settings_window_updates_the_open_lists(app, tmp_path, monkeypatch):
	win = window(tmp_path, monkeypatch)
	win._set_locale(Document({f"key{i}": "x" for i in range(30)}))
	assert len(win.locale_tab.model.keys) == 30
	win.settings.locale_max_entries = 20
	win.locale_tab.refresh()
	assert len(win.locale_tab.model.keys) == 20


def test_the_picker_uses_the_limit(app, tmp_path, monkeypatch):
	win = window(tmp_path, monkeypatch, lookup_max_rows=10)
	seen = []
	monkeypatch.setattr("ui.main_window.PickerDialog.exec", lambda self: seen.append(self.view.settings) or 0)
	win.pick("item")
	assert seen == [win.settings]


# --- Locale, not Text ----------------------------------------------------------------------------


def test_the_tab_and_the_file_menu_say_locale(app, tmp_path, monkeypatch):
	win = window(tmp_path, monkeypatch)
	tabs = [win.tabs.tabText(i) for i in range(win.tabs.count())]
	assert "Locale" in tabs and "Text" not in tabs
	assert win.menuLocale.title().replace("&", "") == "Locale"
	entries = [a.text().replace("&", "") for a in win.findChildren(QAction) if a.text()]
	assert not [e for e in entries if "text" in e.lower()]


def test_the_locale_file_dialogs_say_locale(app, tmp_path, monkeypatch):
	win = window(tmp_path, monkeypatch)
	titles = []
	monkeypatch.setattr("ui.main_window.QFileDialog.getOpenFileName", lambda parent, title, *a: titles.append(title) or ("", ""))
	monkeypatch.setattr("ui.main_window.QFileDialog.getSaveFileName", lambda parent, title, start, *a: titles.append((title, start)) or ("", ""))
	win.open_locale()
	win.save_locale()
	assert titles == ["Open locale file", ("Save locale file", "en.json")]
