"""The optional debug log file: the setting, the dialog checkbox, and where the file goes."""

import logging
import subprocess
import sys

import pytest
from PySide6.QtWidgets import QMessageBox

from modules import config as config_module
from modules import utils
from conftest import SRC
from modules.config import ConfigError, load_config, update_ini_text, validate_settings
from modules.windows.settings import Gui_SettingsDlg

probe = logging.getLogger("test_debug_logging")


@pytest.fixture(autouse=True)
def _no_log_file_left_behind():
	utils.set_debug_logging(False)
	yield
	utils.set_debug_logging(False)


def _write_ini(config, text):
	config.settings_path.write_text(text, encoding="utf-8")
	return load_config(config.settings_path, config.settings_path.with_name("box_fields.json"))


def _log_text(path):
	for handler in logging.getLogger().handlers:
		handler.flush()
	return path.read_text(encoding="utf-8") if path.exists() else ""


# --- turning the log file on and off ----------------------------------------------------


def test_nothing_is_written_until_it_is_turned_on(tmp_path):
	log_file = tmp_path / "debug.log"
	probe.debug("before")
	assert not log_file.exists()


def test_enabled_logging_records_debug_messages(tmp_path):
	log_file = tmp_path / "debug.log"
	utils.set_debug_logging(True, log_file)
	probe.debug("a detailed message")
	probe.info("an info message")
	text = _log_text(log_file)
	assert "a detailed message" in text and "an info message" in text
	assert "DEBUG" in text and "test_debug_logging" in text


def test_turning_it_off_stops_writing_and_releases_the_file(tmp_path):
	log_file = tmp_path / "debug.log"
	utils.set_debug_logging(True, log_file)
	probe.debug("while on")
	utils.set_debug_logging(False)
	probe.debug("while off")
	text = _log_text(log_file)
	assert "while on" in text and "while off" not in text
	log_file.unlink()  # (on Windows this fails if the file is still held open)
	assert not log_file.exists()


def test_it_can_be_turned_on_again(tmp_path):
	log_file = tmp_path / "debug.log"
	utils.set_debug_logging(True, log_file)
	utils.set_debug_logging(False)
	utils.set_debug_logging(True, log_file)
	probe.debug("second time")
	assert "second time" in _log_text(log_file)


def test_enabling_twice_does_not_duplicate_lines(tmp_path):
	log_file = tmp_path / "debug.log"
	utils.set_debug_logging(True, log_file)
	utils.set_debug_logging(True, log_file)
	probe.debug("only once please")
	assert _log_text(log_file).count("only once please") == 1


def test_switching_to_a_different_file_moves_the_log(tmp_path):
	first, second = tmp_path / "one.log", tmp_path / "two.log"
	utils.set_debug_logging(True, first)
	utils.set_debug_logging(True, second)
	probe.debug("after the switch")
	assert "after the switch" in _log_text(second)
	assert "after the switch" not in _log_text(first)


def test_a_log_file_that_cannot_be_opened_raises_and_changes_nothing(tmp_path):
	handlers_before = list(logging.getLogger().handlers)
	with pytest.raises(OSError):
		utils.set_debug_logging(True, tmp_path / "no_such_folder" / "debug.log")
	assert list(logging.getLogger().handlers) == handlers_before


def test_turning_off_when_it_was_never_on_is_harmless():
	utils.set_debug_logging(False)
	utils.set_debug_logging(False)


# --- where the file goes (including in the packaged app) -----------------------------------


def test_from_source_the_log_is_next_to_the_program_files():
	assert utils.LOG_FILE == SRC / "trader_builder.log"


def test_packaged_the_log_is_next_to_the_exe_not_in_the_temp_folder(tmp_path):
	# Simulate a PyInstaller build: sys.frozen is set and sys.executable is the .exe.
	# (In a one-file build the modules are unpacked into a temporary folder, so a path
	# built from the module's own location would be lost when the app exits.)
	fake_exe = tmp_path / "app" / "trader_builder.exe"
	fake_exe.parent.mkdir()
	code = (
		"import sys; sys.frozen = True; sys.executable = sys.argv[1]; "
		"from modules import paths, utils; print(utils.LOG_FILE); print(paths.APP_DIR)"
	)
	out = subprocess.run(
		[sys.executable, "-c", code, str(fake_exe)], cwd=SRC, capture_output=True, text=True, check=True
	).stdout.splitlines()
	assert out[0] == str(fake_exe.parent / "trader_builder.log")
	assert out[1] == str(fake_exe.parent)


# --- the setting ----------------------------------------------------------------------------


def test_debug_logging_is_off_in_the_shipped_settings():
	assert load_config().debug_logging is False


def test_a_settings_file_without_the_entry_means_off(config):
	text = config.settings_path.read_text(encoding="utf-8").replace("debug_logging = false", "")
	assert "debug_logging" not in text.replace("# Write a detailed log", "")
	assert _write_ini(config, text).debug_logging is False


@pytest.mark.parametrize("word, expected", [("true", True), ("True", True), ("on", True), ("yes", True), ("1", True), ("false", False), ("Off", False), ("no", False), ("0", False)])
def test_true_and_false_words_are_understood(config, word, expected):
	text = config.settings_path.read_text(encoding="utf-8").replace("debug_logging = false", f"debug_logging = {word}")
	assert _write_ini(config, text).debug_logging is expected


def test_a_value_that_is_not_true_or_false_is_reported(config):
	text = config.settings_path.read_text(encoding="utf-8").replace("debug_logging = false", "debug_logging = maybe")
	config.settings_path.write_text(text, encoding="utf-8")
	with pytest.raises(ConfigError, match="boolean|problem with the settings"):
		load_config(config.settings_path, config.settings_path.with_name("box_fields.json"))


def test_settings_report_it_as_text(config):
	assert config.settings()["debug_logging"] == "false"
	config.update_settings({**config.settings(), "debug_logging": "true"})
	assert config.settings()["debug_logging"] == "true"


def test_saving_it_turns_the_config_value_into_a_real_boolean_and_writes_the_file(config):
	config.update_settings({**config.settings(), "debug_logging": "true"})
	assert config.debug_logging is True
	assert "debug_logging = true\n" in config.settings_path.read_text(encoding="utf-8")
	reloaded = load_config(config.settings_path, config.settings_path.with_name("box_fields.json"))
	assert reloaded.debug_logging is True


def test_a_bad_value_is_rejected(config):
	assert "debug_logging" in validate_settings({**config.settings(), "debug_logging": "maybe"})
	with pytest.raises(ValueError):
		config.update_settings({**config.settings(), "debug_logging": "maybe"})
	assert config.debug_logging is False


def test_the_entry_is_added_under_general_when_the_file_lacks_it():
	text = "[general]\n\n[filepaths]\nversion_file = a\n"
	new = update_ini_text(text, {"debug_logging": "true"})
	assert new == "[general]\ndebug_logging = true\n\n[filepaths]\nversion_file = a\n"


# --- the dialog -------------------------------------------------------------------------------


def test_the_checkbox_starts_unticked(qapp, config):
	dlg = Gui_SettingsDlg(config)
	assert dlg.checkbox("debug_logging").isChecked() is False


def test_the_checkbox_shows_the_current_setting(qapp, config):
	config.update_settings({**config.settings(), "debug_logging": "true"})
	assert Gui_SettingsDlg(config).checkbox("debug_logging").isChecked() is True


def test_ticking_the_box_and_saving_turns_the_setting_on(qapp, config):
	dlg = Gui_SettingsDlg(config)
	dlg.checkbox("debug_logging").setChecked(True)
	assert dlg.values()["debug_logging"] == "true"
	dlg.save()
	assert dlg.result() == dlg.DialogCode.Accepted
	assert config.debug_logging is True


def test_cancelling_leaves_it_off(qapp, config):
	dlg = Gui_SettingsDlg(config)
	dlg.checkbox("debug_logging").setChecked(True)
	dlg.ui.buttonBox.rejected.emit()
	assert config.debug_logging is False


def test_the_tooltip_says_where_the_log_goes(qapp, config):
	assert str(utils.LOG_FILE) in Gui_SettingsDlg(config).ui.chk_debug_logging.toolTip()


# --- the menu: the log really starts and stops ----------------------------------------------


def _save_with(monkeypatch, value):
	def fake_exec(self):
		self.config.update_settings({**self.config.settings(), "debug_logging": value})
		return 1

	monkeypatch.setattr(Gui_SettingsDlg, "exec", fake_exec)


def test_saving_the_setting_starts_and_stops_the_log_file(main_window, monkeypatch, tmp_path):
	log_file = tmp_path / "debug.log"
	monkeypatch.setattr(utils, "LOG_FILE", log_file)

	_save_with(monkeypatch, "true")
	main_window.onSettings()
	probe.debug("logged while on")
	assert "logged while on" in _log_text(log_file)

	_save_with(monkeypatch, "false")
	main_window.onSettings()
	probe.debug("logged while off")
	assert "logged while off" not in _log_text(log_file)


def test_a_log_file_that_cannot_be_created_warns_instead_of_crashing(main_window, monkeypatch, tmp_path):
	bad = tmp_path / "no_such_folder" / "debug.log"
	monkeypatch.setattr(utils, "LOG_FILE", bad)
	warnings = []
	monkeypatch.setattr(QMessageBox, "warning", staticmethod(lambda parent, title, text: warnings.append(text)))
	_save_with(monkeypatch, "true")
	main_window.onSettings()  # must not raise
	assert len(warnings) == 1 and "no_such_folder" in warnings[0]
	assert not bad.exists()


def test_the_other_settings_do_not_touch_the_log(main_window, monkeypatch, tmp_path):
	monkeypatch.setattr(utils, "LOG_FILE", tmp_path / "debug.log")

	def fake_exec(self):
		self.config.update_settings({**self.config.settings(), "default_questicon": "/other.jpg"})
		return 1

	monkeypatch.setattr(Gui_SettingsDlg, "exec", fake_exec)
	main_window.onSettings()
	assert not (tmp_path / "debug.log").exists()
