"""The item database (items.json): the included one by default, a different one if chosen in Settings.

One items.json is loaded at startup from the items_file setting and used everywhere (the ID Lookup tab,
the child-item finder, Settings).
"""

import json

import pytest
from PySide6.QtWidgets import QMessageBox

from modules import state as state_module
from modules.config import DEFAULT_ITEMS_FILE, load_config, resolve_items_path
from modules.paths import APP_DIR, DATA_DIR
from modules.state import AppState
from modules.windows import main_window as mw
from modules.windows import settings as settings_module
from modules.windows.main_window import Gui_MainWindow
from modules.windows.settings import Gui_SettingsDlg

ITEMS = {
	"0123456789abcdef01234567": {"_name": "modded_blaster", "_parent": "root"},
	"89abcdef0123456789abcdef": {"_name": "modded_helmet", "_parent": "root"},
}

INCLUDED = DATA_DIR / "items.json"
PROMPT = "No items.json loaded - import items in Settings."


def reload_config(config):
	return load_config(config.settings_path, config.settings_path.with_name("box_fields.json"))


def set_items_file(config, value):
	config.update_settings({**config.settings(), "items_file": str(value)})


@pytest.fixture
def items_file(tmp_path):
	path = tmp_path / "my items.json"
	path.write_text(json.dumps(ITEMS), encoding="utf-8")
	return path


@pytest.fixture
def boxes(monkeypatch):
	shown = {"warning": [], "critical": []}
	for kind in shown:
		monkeypatch.setattr(
			QMessageBox, kind, staticmethod(lambda parent, title, text, _k=kind: shown[_k].append(text))
		)
	return shown


def choose(monkeypatch, path):
	"""Make the file dialogs (the main window's and Settings') return path, or cancel when None."""
	answer = (str(path), True) if path is not None else (None, False)
	monkeypatch.setattr(mw, "safe_file_dialog", lambda method, title: answer)
	monkeypatch.setattr(settings_module, "safe_file_dialog", lambda method, title: answer)


@pytest.fixture
def window_for(qapp, fixed_ids):
	"""Build a main window the way startup does, from whatever the config says."""
	made = []

	def build(config):
		win = Gui_MainWindow(AppState.load(config))
		made.append(win)
		return win

	yield build
	for win in made:
		win.close()


@pytest.fixture
def dialog(main_window):
	return main_window.spawnWindow("SettingsWindow")


def status(win):
	return win.ui.lbl_items_status.text()


# --- the setting -------------------------------------------------------------------------------------


def test_the_included_file_is_the_default():
	assert load_config().items_file == DEFAULT_ITEMS_FILE == "data/items.json"
	assert load_config().items_path() == INCLUDED


def test_a_relative_path_is_relative_to_the_program_folder():
	assert resolve_items_path("data/items.json") == APP_DIR / "data" / "items.json"
	assert resolve_items_path("elsewhere/items.json") == APP_DIR / "elsewhere" / "items.json"


def test_an_absolute_path_is_used_as_it_is(tmp_path):
	assert resolve_items_path(str(tmp_path / "x.json")) == tmp_path / "x.json"


@pytest.mark.parametrize("empty", ["", "   ", None])
def test_empty_means_the_included_file(empty):
	assert resolve_items_path(empty) == INCLUDED


def test_a_settings_file_without_the_entry_uses_the_included_file(config):
	text = config.settings_path.read_text(encoding="utf-8").replace("items_file = data/items.json", "")
	config.settings_path.write_text(text, encoding="utf-8")
	assert reload_config(config).items_file == DEFAULT_ITEMS_FILE


def test_an_empty_entry_uses_the_included_file(config):
	text = config.settings_path.read_text(encoding="utf-8").replace("items_file = data/items.json", "items_file =")
	config.settings_path.write_text(text, encoding="utf-8")
	assert reload_config(config).items_file == DEFAULT_ITEMS_FILE


def test_the_path_is_saved_and_read_back(config):
	set_items_file(config, "C:/games/SPT/items.json")
	assert reload_config(config).items_file == "C:/games/SPT/items.json"


def test_a_windows_path_with_backslashes_and_spaces_survives(config):
	path = r"C:\Games\SPT 3.9\SPT_Data\Server\database\templates\items.json"
	set_items_file(config, path)
	assert reload_config(config).items_file == path


def test_a_path_with_russian_letters_survives(config):
	set_items_file(config, "C:/Игры/SPT/items.json")
	assert reload_config(config).items_file == "C:/Игры/SPT/items.json"


# --- which file is loaded at startup --------------------------------------------------------------------------


def test_by_default_the_included_file_is_loaded(config):
	state = AppState.load(config)
	assert state.items_path == str(INCLUDED) and state.items_error is None
	assert len(state.items) > 4000 and state.loaded_items is state.items


def test_a_chosen_file_is_loaded_instead_of_the_included_one(config, items_file):
	set_items_file(config, items_file)
	state = AppState.load(config)
	assert state.items == ITEMS and state.items_path == str(items_file) and state.items_error is None


def test_a_missing_chosen_file_falls_back_to_the_included_one(config, tmp_path):
	set_items_file(config, tmp_path / "gone.json")
	state = AppState.load(config)
	assert state.items_path == str(INCLUDED) and len(state.items) > 4000
	assert "gone.json" in state.items_error


def test_a_damaged_chosen_file_falls_back_to_the_included_one(config, tmp_path):
	bad = tmp_path / "bad.json"
	bad.write_text("{ nope", encoding="utf-8")
	set_items_file(config, bad)
	state = AppState.load(config)
	assert state.items_path == str(INCLUDED) and "bad.json" in state.items_error


def test_a_chosen_file_that_is_not_an_items_file_falls_back(config, tmp_path):
	wrong = tmp_path / "list.json"
	wrong.write_text('["not", "items"]', encoding="utf-8")
	set_items_file(config, wrong)
	state = AppState.load(config)
	assert state.items_path == str(INCLUDED) and "list.json" in state.items_error


def test_if_nothing_can_be_loaded_there_are_no_items_but_the_program_still_starts(config, tmp_path, monkeypatch):
	missing_included = tmp_path / "no_included_file.json"
	monkeypatch.setattr(state_module, "resolve_items_path", lambda text: missing_included)
	set_items_file(config, tmp_path / "gone.json")  # (the chosen file is missing too)
	state = AppState.load(config)  # must not raise
	assert state.items == {} and state.loaded_items is None and state.items_path is None
	assert "gone.json" in state.items_error and "no_included_file.json" in state.items_error


def test_a_missing_included_file_with_the_default_setting_reports_it(config, tmp_path, monkeypatch):
	missing = tmp_path / "no_included_file.json"
	monkeypatch.setattr(state_module, "resolve_items_path", lambda text: missing)
	monkeypatch.setattr(type(config), "items_path", lambda self: missing)
	state = AppState.load(config)
	assert state.loaded_items is None and state.items_error


def test_a_russian_code_page_items_file_loads(config, tmp_path):
	path = tmp_path / "Предметы.json"
	path.write_bytes(json.dumps({"a" * 24: {"_name": "Привет"}}, ensure_ascii=False).encode("cp866"))
	set_items_file(config, path)
	assert AppState.load(config).items["a" * 24]["_name"] == "Привет"


def test_set_items_replaces_everything_about_the_database(config):
	state = AppState.load(config)
	state.set_items(ITEMS, "x.json", "some error")
	assert (state.items, state.items_path, state.items_error) == (ITEMS, "x.json", "some error")
	state.set_items({}, None, None)
	assert state.loaded_items is None


# --- the line on the ID Lookup tab ------------------------------------------------------------------------------


def test_normally_the_tab_does_not_ask_for_an_items_file(main_window):
	assert "import items in Settings" not in status(main_window)
	assert status(main_window).startswith("items.json loaded (")
	assert main_window.ui.lbl_items_status.toolTip() == str(INCLUDED)


def test_the_tab_shows_how_many_items_are_loaded(main_window):
	assert status(main_window) == f"items.json loaded ({len(main_window.state.items)} items)."


def test_with_no_items_the_tab_asks_for_an_items_file(main_window):
	main_window.apply_items(None)
	assert status(main_window) == PROMPT and "Settings" in status(main_window)


def test_the_prompt_goes_away_again_when_items_are_loaded(main_window):
	main_window.apply_items(None)
	main_window.apply_items(ITEMS, "x.json")
	assert status(main_window) == "items.json loaded (2 items)." and main_window.ui.lbl_items_status.toolTip() == "x.json"


def test_when_nothing_could_be_loaded_at_startup_the_prompt_shows(config, tmp_path, monkeypatch, window_for):
	monkeypatch.setattr(state_module, "resolve_items_path", lambda text: tmp_path / "no_included_file.json")
	set_items_file(config, tmp_path / "gone.json")
	win = window_for(config)
	assert status(win) == PROMPT and "gone.json" in win.ui.lbl_items_status.toolTip()
	assert "gone.json" in win.statusBar().currentMessage()


def test_when_the_chosen_file_could_not_be_used_the_tab_says_so(config, tmp_path, window_for):
	set_items_file(config, tmp_path / "gone.json")
	win = window_for(config)
	assert "could not be used" in status(win) and "included file is in use" in status(win)
	assert "gone.json" in win.ui.lbl_items_status.toolTip()
	assert "gone.json" in win.statusBar().currentMessage()  # (and it says so when the program starts)


def test_a_good_start_leaves_the_status_bar_quiet(main_window):
	assert main_window.statusBar().currentMessage() == ""


def test_the_status_line_is_on_the_id_lookup_tab(main_window):
	tab = main_window.ui.main_tab.widget(main_window.ui.main_tab.indexOf(main_window.ui.tab))
	assert main_window.ui.lbl_items_status.parent() is tab
	assert main_window.ui.main_tab.tabText(main_window.ui.main_tab.indexOf(tab)) == "ID Lookup"


def test_loading_items_refreshes_a_search_that_is_showing(main_window):
	main_window.ui.fld_idlookup.setText("modded")
	assert main_window.ui.id_table.rowCount() == 0
	main_window.apply_items(ITEMS, "x.json")
	assert main_window.ui.id_table.rowCount() == 2
	main_window.apply_items(None)
	assert main_window.ui.id_table.rowCount() == 0


def test_loading_items_does_not_fill_the_table_when_nobody_searched(main_window):
	main_window.apply_items(ITEMS, "x.json")
	assert main_window.ui.id_table.rowCount() == 0


# --- one database, used everywhere -------------------------------------------------------------------------------------


def test_the_lookup_and_the_finder_use_the_same_loaded_items(main_window):
	state = main_window.state
	assert state.items is state.loaded_items
	finder = main_window.getAllChildrenCalc()
	assert f"({len(state.items)} items)" in finder.ui.lbl_items_status.text()
	assert "No items.json" not in finder.ui.lbl_items_status.text()


def test_the_finder_works_on_the_included_items_straight_away(main_window):
	items = main_window.state.items
	parent_id = next(item["_parent"] for item in items.values() if item.get("_parent") in items)
	finder = main_window.getAllChildrenCalc()
	finder.ui.fld_parent_id.setText(parent_id)
	finder.ui.pb_find.click()
	assert not finder.ui.lbl_result.text().startswith("0 items")


def test_changing_the_items_changes_them_for_the_finder_too(main_window):
	main_window.apply_items(ITEMS, "x.json")
	finder = main_window.getAllChildrenCalc()
	finder.ui.fld_parent_id.setText("root")
	finder.ui.pb_find.click()
	assert finder.ui.lbl_result.text().startswith("2 items found")


def test_the_lookup_searches_whatever_items_are_in_use(main_window):
	main_window.apply_items(ITEMS, "x.json")
	main_window.ui.fld_idlookup.setText("^eft_item$")
	assert main_window.ui.id_table.rowCount() == 2


def test_loading_from_the_finder_replaces_the_items_everywhere_and_is_remembered(main_window, monkeypatch, items_file):
	choose(monkeypatch, items_file)
	assert main_window.loadItemsJSON() is True
	assert main_window.state.items == ITEMS and main_window.state.items_path == str(items_file)
	assert status(main_window) == "items.json loaded (2 items)."
	assert reload_config(main_window.state.config).items_file == str(items_file)


def test_a_failed_load_from_the_finder_changes_nothing(main_window, monkeypatch, boxes, tmp_path):
	before = main_window.state.items
	bad = tmp_path / "bad.json"
	bad.write_text("{ nope", encoding="utf-8")
	choose(monkeypatch, bad)
	assert main_window.loadItemsJSON() is False
	assert main_window.state.items is before
	assert reload_config(main_window.state.config).items_file == DEFAULT_ITEMS_FILE


def test_a_settings_file_that_cannot_be_written_warns_but_the_items_still_load(main_window, monkeypatch, boxes, items_file):
	from modules import config as config_module

	def boom(path, values):
		raise OSError("read-only")

	monkeypatch.setattr(config_module, "save_settings", boom)
	choose(monkeypatch, items_file)
	assert main_window.loadItemsJSON() is True
	assert main_window.state.items == ITEMS
	assert len(boxes["warning"]) == 1 and "remembered" in boxes["warning"][0]


# --- the Settings dialog -------------------------------------------------------------------------------------------------


def test_the_section_is_shown_when_the_dialog_is_connected(dialog):
	dialog.show()
	assert dialog.ui.grp_items.isVisible() and dialog.ui.fld_items_file.isReadOnly()


def test_the_section_is_hidden_when_the_dialog_is_not_connected(qapp, config):
	dlg = Gui_SettingsDlg(config)
	dlg.show()
	assert not dlg.ui.grp_items.isVisible()


def test_it_starts_on_the_included_file(dialog, main_window):
	assert dialog.ui.fld_items_file.text() == "data/items.json"
	assert dialog.ui.lbl_items_status.text() == f"Using the included items.json ({len(main_window.state.items)} items)."
	assert not dialog.ui.pb_default_items.isEnabled()  # (already using it)


def test_choosing_a_file_loads_it_for_a_preview_only(dialog, main_window, monkeypatch, items_file):
	before = main_window.state.items
	choose(monkeypatch, items_file)
	dialog.ui.pb_load_items.click()
	assert dialog.ui.fld_items_file.text() == str(items_file)
	assert dialog.ui.lbl_items_status.text() == "2 items ready. Press Save to use them."
	assert dialog.ui.pb_default_items.isEnabled()
	assert main_window.state.items is before  # (not used until Save)


def test_save_switches_to_it_everywhere_and_remembers_it(dialog, main_window, monkeypatch, items_file):
	choose(monkeypatch, items_file)
	dialog.ui.pb_load_items.click()
	dialog.save()
	assert dialog.result() == dialog.DialogCode.Accepted
	assert main_window.state.items == ITEMS and main_window.state.items_path == str(items_file)
	assert main_window.state.config.items_file == str(items_file)
	assert reload_config(main_window.state.config).items_file == str(items_file)
	assert status(main_window) == "items.json loaded (2 items)."


def test_cancel_throws_the_choice_away(dialog, main_window, monkeypatch, items_file):
	before = main_window.state.items
	choose(monkeypatch, items_file)
	dialog.ui.pb_load_items.click()
	dialog.ui.buttonBox.rejected.emit()
	assert main_window.state.items is before
	assert main_window.state.config.items_file == DEFAULT_ITEMS_FILE
	assert reload_config(main_window.state.config).items_file == DEFAULT_ITEMS_FILE


def test_a_bad_file_shows_an_error_and_changes_nothing(dialog, monkeypatch, tmp_path):
	bad = tmp_path / "bad.json"
	bad.write_text("{ nope", encoding="utf-8")
	choose(monkeypatch, bad)
	dialog.ui.pb_load_items.click()
	assert dialog.ui.lbl_error.isVisibleTo(dialog) and "bad.json" in dialog.ui.lbl_error.text()
	assert dialog.ui.fld_items_file.text() == "data/items.json"
	assert dialog.pending_items is None and not dialog.items_changed


def test_a_file_that_is_not_an_items_file_is_refused(dialog, monkeypatch, tmp_path):
	not_items = tmp_path / "list.json"
	not_items.write_text("[1, 2, 3]", encoding="utf-8")
	choose(monkeypatch, not_items)
	dialog.ui.pb_load_items.click()
	assert dialog.ui.lbl_error.isVisibleTo(dialog) and dialog.ui.fld_items_file.text() == "data/items.json"


def test_cancelling_the_file_dialog_changes_nothing(dialog, monkeypatch):
	choose(monkeypatch, None)
	dialog.ui.pb_load_items.click()
	assert dialog.ui.fld_items_file.text() == "data/items.json" and not dialog.items_changed


def test_a_good_choice_after_a_bad_one_clears_the_error(dialog, monkeypatch, tmp_path, items_file):
	bad = tmp_path / "bad.json"
	bad.write_text("{ nope", encoding="utf-8")
	choose(monkeypatch, bad)
	dialog.ui.pb_load_items.click()
	choose(monkeypatch, items_file)
	dialog.ui.pb_load_items.click()
	assert not dialog.ui.lbl_error.isVisibleTo(dialog)


def test_a_bad_file_does_not_replace_the_one_in_use(dialog, main_window, monkeypatch, tmp_path):
	before = main_window.state.items
	bad = tmp_path / "bad.json"
	bad.write_text("{ nope", encoding="utf-8")
	choose(monkeypatch, bad)
	dialog.ui.pb_load_items.click()
	dialog.save()
	assert main_window.state.items is before


def test_use_included_file_goes_back_to_the_included_items(dialog, main_window, monkeypatch, items_file):
	included_count = len(main_window.state.items)
	choose(monkeypatch, items_file)
	dialog.ui.pb_load_items.click()
	dialog.save()
	assert len(main_window.state.items) == 2

	again = main_window.spawnWindow("SettingsWindow")
	assert again.ui.fld_items_file.text() == str(items_file) and again.ui.pb_default_items.isEnabled()
	again.ui.pb_default_items.click()
	assert again.ui.fld_items_file.text() == "data/items.json"
	assert not again.ui.pb_default_items.isEnabled()
	again.save()
	assert len(main_window.state.items) == included_count
	assert main_window.state.items_path == str(INCLUDED)
	assert reload_config(main_window.state.config).items_file == "data/items.json"
	assert status(main_window) == f"items.json loaded ({included_count} items)."


def test_use_included_file_then_cancel_keeps_the_current_one(main_window, monkeypatch, items_file):
	choose(monkeypatch, items_file)
	first = main_window.spawnWindow("SettingsWindow")
	first.ui.pb_load_items.click()
	first.save()
	second = main_window.spawnWindow("SettingsWindow")
	second.ui.pb_default_items.click()
	second.ui.buttonBox.rejected.emit()
	assert main_window.state.items == ITEMS


def test_a_chosen_file_that_could_not_be_used_is_explained_and_can_be_replaced(config, tmp_path, window_for):
	set_items_file(config, tmp_path / "gone.json")
	win = window_for(config)
	dlg = win.spawnWindow("SettingsWindow")
	assert dlg.ui.fld_items_file.text() == str(tmp_path / "gone.json")
	assert "Using the included items.json" in dlg.ui.lbl_items_status.text()
	assert "could not be read" in dlg.ui.lbl_items_status.text()
	assert dlg.ui.pb_default_items.isEnabled()

	dlg.ui.pb_default_items.click()
	dlg.save()
	assert win.state.items_error is None
	assert reload_config(config).items_file == "data/items.json"
	assert "could not be used" not in status(win)


def test_saving_other_settings_leaves_the_items_alone(dialog, main_window):
	before = main_window.state.items
	dialog.ui.fld_default_questicon.setText("/other.jpg")
	dialog.save()
	assert main_window.state.items is before
	assert main_window.state.config.default_questicon == "/other.jpg"
	assert main_window.state.config.items_file == DEFAULT_ITEMS_FILE


def test_choosing_a_different_file_replaces_the_first_choice(dialog, main_window, monkeypatch, tmp_path, items_file):
	second = tmp_path / "second.json"
	second.write_text(json.dumps({"x" * 24: {"_name": "only"}}), encoding="utf-8")
	choose(monkeypatch, items_file)
	dialog.ui.pb_load_items.click()
	choose(monkeypatch, second)
	dialog.ui.pb_load_items.click()
	dialog.save()
	assert set(main_window.state.items) == {"x" * 24} and main_window.state.items_path == str(second)


def test_the_window_is_tall_enough_for_everything_in_it(dialog):
	dialog.show()
	needed = dialog.minimumSizeHint()
	assert needed.height() <= dialog.height() and needed.width() <= dialog.width()
	assert dialog.minimumHeight() >= needed.height()  # (it can't be shrunk below what fits)


# --- what is gone ------------------------------------------------------------------------------------------------------------


def test_there_is_no_second_copy_of_the_items(main_window):
	main_window.apply_items(ITEMS, "x.json")  # (a second copy could only appear once items are applied)
	assert main_window.state.items == ITEMS
	for old_name in ("itemsJSON", "items_file_path", "items_load_error", "load_saved_items"):
		assert not hasattr(main_window, old_name), old_name
	assert not hasattr(main_window.state, "item_id_name")


def test_the_included_file_is_still_the_one_that_ships(config):
	assert INCLUDED.exists() and INCLUDED.stat().st_size > 1_000_000
	assert config.items_path() == INCLUDED


def test_the_error_for_a_missing_file_is_readable_not_a_python_repr(config, tmp_path):
	set_items_file(config, tmp_path / "gone.json")
	error = AppState.load(config).items_error
	assert "gone.json" in error and "No such file or directory" in error and "Errno" not in error
