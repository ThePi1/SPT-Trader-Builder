"""Editing settings.ini: the file rewriting, validation, the dialog, and the menu wiring."""

import os

import pytest

import config as config_module
import updates
from config import (
	BOOL_SETTING_NAMES,
	SETTING_NAMES,
	load_config,
	save_settings,
	update_ini_text,
	validate_settings,
)
from paths import DATA_DIR
from windows.settings import ERROR_STYLE, Gui_SettingsDlg

GOOD = {
	"debug_logging": "false",
	"merge_locales_on_export": "false",
	"version_file": "data/version.txt",
	"version_url": "https://example.com/version.txt",
	"project_url": "https://example.com/project",
	"items_file": "C:/games/SPT/items.json",
	"default_questicon": "/files/quest/icon/abc.jpg",
}

SAMPLE = """# top comment

[general]
debug_logging = true
merge_locales_on_export = true

[filepaths]
# comment about the version file
version_file = data/version.txt
version_url = https://old.example/version.txt
project_url = https://old.example/project
items_file = /old/items.json

[defaults]
default_questicon = /old.jpg
"""


# --- rewriting the ini text ---------------------------------------------------------


def test_only_the_changed_lines_are_touched():
	new = update_ini_text(SAMPLE, {"version_url": "https://new.example/v.txt"})
	assert new == SAMPLE.replace("https://old.example/version.txt", "https://new.example/v.txt")


def test_all_settings_can_be_changed_and_comments_survive():
	new = update_ini_text(SAMPLE, GOOD)
	assert new.startswith(
		"# top comment\n\n[general]\ndebug_logging = false\nmerge_locales_on_export = false\n\n"
		"[filepaths]\n# comment about the version file\n"
	)
	assert "old" not in new
	for name, value in GOOD.items():
		assert f"{name} = {value}\n" in new


def test_line_endings_are_kept():
	crlf = SAMPLE.replace("\n", "\r\n")
	new = update_ini_text(crlf, GOOD)
	assert "\n" not in new.replace("\r\n", "")
	assert new.count("\r\n") == crlf.count("\r\n")


def test_separator_style_is_kept():
	new = update_ini_text("[defaults]\ndefault_questicon: old\n", {"default_questicon": "new"})
	assert new == "[defaults]\ndefault_questicon: new\n"


def test_a_missing_key_is_added_to_the_end_of_its_section():
	text = "[filepaths]\nversion_file = a\n# trailing comment\n\n[defaults]\n# nothing yet\n"
	new = update_ini_text(text, {"project_url": "https://x.y", "default_questicon": "hi"})
	assert new == (
		"[filepaths]\nversion_file = a\n# trailing comment\nproject_url = https://x.y\n\n"
		"[defaults]\n# nothing yet\ndefault_questicon = hi\n"
	)


def test_a_missing_section_is_created():
	new = update_ini_text("[filepaths]\nversion_file = a", {"default_questicon": "hi"})
	assert new == "[filepaths]\nversion_file = a\n\n[defaults]\ndefault_questicon = hi\n"


def test_a_key_in_the_wrong_section_is_not_touched():
	text = "[other]\ndefault_questicon = keep me\n\n[defaults]\ndefault_questicon = old\n"
	assert update_ini_text(text, {"default_questicon": "new"}) == (
		"[other]\ndefault_questicon = keep me\n\n[defaults]\ndefault_questicon = new\n"
	)


def test_continuation_lines_of_the_old_value_are_dropped():
	text = "[defaults]\ndefault_questicon = first\n  second line\nother = q\n"
	new = update_ini_text(text, {"default_questicon": "one line"})
	assert new == "[defaults]\ndefault_questicon = one line\nother = q\n"


def test_multiline_values_are_rejected():
	with pytest.raises(ValueError):
		update_ini_text(SAMPLE, {"default_questicon": "two\nlines"})


# --- saving to disk -----------------------------------------------------------------


def test_save_settings_round_trips_through_load_config(config):
	save_settings(config.settings_path, GOOD)
	reloaded = load_config(config.settings_path, config.settings_path.with_name("box_fields.json"))
	assert reloaded.settings() == GOOD


def test_save_leaves_no_temp_file_and_keeps_comments(config):
	save_settings(config.settings_path, GOOD)
	assert not config.settings_path.with_name("settings.ini.tmp").exists()
	assert "# Settings" in config.settings_path.read_text(encoding="utf-8")


def test_a_failed_save_leaves_the_original_file(config, monkeypatch):
	original = config.settings_path.read_text(encoding="utf-8")

	def boom(*args):
		raise OSError("disk full")

	monkeypatch.setattr(os, "replace", boom)
	with pytest.raises(OSError):
		save_settings(config.settings_path, GOOD)
	assert config.settings_path.read_text(encoding="utf-8") == original
	assert not config.settings_path.with_name("settings.ini.tmp").exists()


def test_percent_signs_are_kept_literally(config):
	url = "https://example.com/a%20b?x=1%2"
	config.update_settings({**GOOD, "project_url": url})
	assert load_config(config.settings_path, config.settings_path.with_name("box_fields.json")).project_url == url


# --- validation ---------------------------------------------------------------------


def test_good_settings_are_valid():
	assert validate_settings(GOOD) == {}


def test_the_real_settings_file_is_valid():
	assert validate_settings(load_config().settings()) == {}


@pytest.mark.parametrize("name", ["version_url", "project_url"])
@pytest.mark.parametrize("bad", ["", "example.com", "ftp://example.com", "http://", "https://a b"])
def test_urls_must_be_web_addresses(name, bad):
	assert name in validate_settings({**GOOD, name: bad})


@pytest.mark.parametrize("name", ["version_file", "default_questicon"])
def test_required_fields_cannot_be_blank(name):
	assert validate_settings({**GOOD, name: "  "}) == {name: "Required."}


def test_values_must_be_single_lines():
	assert "default_questicon" in validate_settings({**GOOD, "default_questicon": "a\nb"})


# --- Config.update_settings ---------------------------------------------------------


def test_update_settings_saves_and_applies(config):
	config.update_settings({**GOOD, "default_questicon": "  padded  "})
	assert config.default_questicon == "padded"
	assert config.settings() == {**GOOD, "default_questicon": "padded"}
	assert "default_questicon = padded\n" in config.settings_path.read_text(encoding="utf-8")


def test_invalid_settings_change_nothing(config):
	before = config.settings()
	text = config.settings_path.read_text(encoding="utf-8")
	with pytest.raises(ValueError):
		config.update_settings({**GOOD, "version_url": "nope"})
	assert config.settings() == before
	assert config.settings_path.read_text(encoding="utf-8") == text


def test_a_failed_write_does_not_change_the_running_config(config, monkeypatch):
	before = config.settings()

	def boom(path, values):
		raise OSError("read-only")

	monkeypatch.setattr(config_module, "save_settings", boom)
	with pytest.raises(OSError):
		config.update_settings(GOOD)
	assert config.settings() == before


def test_the_real_settings_file_is_never_written_by_these_tests(config):
	assert config.settings_path.parent != DATA_DIR


# --- the dialog ---------------------------------------------------------------------


def test_dialog_shows_the_current_settings(qapp, config):
	dlg = Gui_SettingsDlg(config)
	assert dlg.values() == config.settings()
	assert not dlg.ui.lbl_error.isVisible()


def test_saving_valid_values(qapp, config):
	dlg = Gui_SettingsDlg(config)
	for name, value in GOOD.items():
		if name in BOOL_SETTING_NAMES:
			dlg.checkbox(name).setChecked(value == "true")
		else:
			dlg.field(name).setText(value)
	dlg.save()
	assert dlg.result() == dlg.DialogCode.Accepted
	assert config.settings() == GOOD
	assert load_config(config.settings_path, config.settings_path.with_name("box_fields.json")).settings() == GOOD


def test_invalid_values_are_marked_and_nothing_is_saved(qapp, config):
	original = config.settings_path.read_text(encoding="utf-8")
	dlg = Gui_SettingsDlg(config)
	dlg.ui.fld_version_url.setText("not a url")
	dlg.ui.fld_default_questicon.setText("")
	dlg.save()
	assert dlg.result() != dlg.DialogCode.Accepted
	assert dlg.ui.fld_version_url.styleSheet() == ERROR_STYLE
	assert dlg.ui.fld_default_questicon.styleSheet() == ERROR_STYLE
	assert dlg.ui.fld_project_url.styleSheet() == ""
	text = dlg.ui.lbl_error.text()
	assert "Latest version URL" in text and "Default quest icon" in text
	assert config.settings_path.read_text(encoding="utf-8") == original


def test_a_mark_clears_when_the_field_is_edited(qapp, config):
	dlg = Gui_SettingsDlg(config)
	dlg.ui.fld_version_url.setText("nope")
	dlg.save()
	assert dlg.ui.fld_version_url.styleSheet() == ERROR_STYLE
	dlg.ui.fld_version_url.textEdited.emit("https://x.y")
	assert dlg.ui.fld_version_url.styleSheet() == ""


def test_a_write_error_is_shown_not_raised(qapp, config, monkeypatch):
	def boom(path, values):
		raise OSError("access denied")

	monkeypatch.setattr(config_module, "save_settings", boom)
	dlg = Gui_SettingsDlg(config)
	dlg.ui.fld_default_questicon.setText("changed")
	dlg.save()
	assert "access denied" in dlg.ui.lbl_error.text()
	assert dlg.result() != dlg.DialogCode.Accepted


def test_cancel_changes_nothing(qapp, config):
	before = config.settings()
	text = config.settings_path.read_text(encoding="utf-8")
	dlg = Gui_SettingsDlg(config)
	dlg.ui.fld_default_questicon.setText("edited then cancelled")
	dlg.ui.buttonBox.rejected.emit()
	assert config.settings() == before
	assert config.settings_path.read_text(encoding="utf-8") == text


def test_every_setting_has_a_field(qapp, config):
	dlg = Gui_SettingsDlg(config)
	for name in SETTING_NAMES:
		widget = dlg.checkbox(name) if name in BOOL_SETTING_NAMES else dlg.field(name)
		assert widget is not None, name


# --- the menu -----------------------------------------------------------------------


def _save_via_dialog(monkeypatch, new_values):
	"""Make the (modal) dialog save new_values instead of waiting for a user."""

	def fake_exec(self):
		self.config.update_settings({**self.config.settings(), **new_values})
		return 1

	monkeypatch.setattr(Gui_SettingsDlg, "exec", fake_exec)


def test_the_settings_menu_item_opens_the_dialog(main_window, monkeypatch):
	opened = []
	monkeypatch.setattr(Gui_SettingsDlg, "exec", lambda self: opened.append(self) or 0)
	main_window.ui.actionSettingsMenu.trigger()
	assert len(opened) == 1 and isinstance(opened[0], Gui_SettingsDlg)
	assert opened[0].parent() is main_window


def test_changing_update_settings_restarts_the_update_check(main_window, monkeypatch):
	checks = []
	monkeypatch.setattr(main_window, "start_update_check", lambda: checks.append(1))
	_save_via_dialog(monkeypatch, {"version_url": "https://new.example/v.txt"})
	main_window.update_status = updates.UpdateStatus("1", "2", updates.OUTDATED, "u")
	main_window.onSettings()
	assert checks == [1]
	assert main_window.update_status.state == updates.CHECKING


def test_changing_only_quest_defaults_does_not_recheck(main_window, monkeypatch):
	checks = []
	monkeypatch.setattr(main_window, "start_update_check", lambda: checks.append(1))
	_save_via_dialog(monkeypatch, {"default_questicon": "/other.jpg"})
	main_window.onSettings()
	assert checks == []


def test_cancelling_does_not_recheck(main_window, monkeypatch):
	checks = []
	monkeypatch.setattr(main_window, "start_update_check", lambda: checks.append(1))
	monkeypatch.setattr(Gui_SettingsDlg, "exec", lambda self: 0)
	main_window.onSettings()
	assert checks == []


def test_new_quest_windows_use_the_new_default_icon(main_window, monkeypatch):
	_save_via_dialog(monkeypatch, {"default_questicon": "/files/quest/icon/new.jpg"})
	main_window.onSettings()
	quest = main_window.spawnWindow("QuestBuilder")
	assert quest.ui.fld_image_name.text() == "/files/quest/icon/new.jpg"


def test_an_older_update_check_does_not_overwrite_a_newer_one(qapp, config, monkeypatch):
	monkeypatch.setattr(updates, "check_for_updates", lambda c: "result")
	results = []
	stale = updates.UpdateCheckWorker(config)
	stale.signals.finished.connect(results.append)
	stale.stale = True
	stale.run()
	fresh = updates.UpdateCheckWorker(config)
	fresh.signals.finished.connect(results.append)
	fresh.run()
	assert results == ["result"]
