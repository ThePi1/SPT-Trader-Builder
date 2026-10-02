"""Unexpected errors are shown to the user instead of vanishing (the packaged program has no console)."""

import logging
import sys

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton

from modules import error_handling
import trader_builder
from modules.config import ConfigError
from modules.error_handling import install_excepthook, report_exception


@pytest.fixture(autouse=True)
def _restore_hook():
	original = sys.excepthook
	yield
	sys.excepthook = original
	error_handling._showing_dialog = False


@pytest.fixture
def boxes(monkeypatch):
	"""Record the error dialogs instead of showing them (their exec() would wait for a click)."""
	shown = []

	def fake_exec(self):
		shown.append(
			{
				"title": self.windowTitle(),
				"text": self.text(),
				"info": self.informativeText(),
				"details": self.detailedText(),
				"icon": self.icon(),
			}
		)
		return QMessageBox.StandardButton.Ok

	monkeypatch.setattr(QMessageBox, "exec", fake_exec)
	return shown


def raised(exc):
	try:
		raise exc
	except type(exc):
		return sys.exc_info()


# --- the report -------------------------------------------------------------------------------


def test_an_error_is_shown_with_its_type_and_message(qapp, boxes):
	report_exception(*raised(ValueError("the value was wrong")))
	(box,) = boxes
	assert "ValueError: the value was wrong" in box["text"]
	assert box["icon"] == QMessageBox.Icon.Critical


def test_the_full_traceback_is_in_the_details(qapp, boxes):
	report_exception(*raised(KeyError("some_key")))
	assert "Traceback (most recent call last)" in boxes[0]["details"]
	assert "KeyError" in boxes[0]["details"] and "test_error_handling.py" in boxes[0]["details"]


def test_the_dialog_tells_the_user_what_to_do(qapp, boxes):
	report_exception(*raised(RuntimeError("x")))
	assert "restart" in boxes[0]["info"] and "bug report" in boxes[0]["info"]


def test_a_custom_title_can_be_given(qapp, boxes):
	report_exception(*raised(RuntimeError("x")), title="Could not start")
	assert boxes[0]["title"] == "Could not start"


def test_the_error_is_logged_with_its_traceback(qapp, boxes, caplog):
	with caplog.at_level(logging.ERROR):
		report_exception(*raised(RuntimeError("logged please")))
	assert "Unexpected error" in caplog.text and "logged please" in caplog.text


def test_an_error_during_the_dialog_does_not_stack_more_dialogs(qapp, monkeypatch):
	shown = []

	def exec_that_fails_again(self):
		shown.append(1)
		report_exception(*raised(RuntimeError("an error while showing an error")))

	monkeypatch.setattr(QMessageBox, "exec", exec_that_fails_again)
	report_exception(*raised(RuntimeError("first")))
	assert shown == [1]
	assert error_handling._showing_dialog is False  # and it can be used again afterwards


def test_without_an_application_it_only_logs(monkeypatch, caplog):
	monkeypatch.setattr(QApplication, "instance", staticmethod(lambda: None))
	with caplog.at_level(logging.ERROR):
		report_exception(*raised(RuntimeError("no gui yet")))  # must not raise
	assert "no gui yet" in caplog.text


# --- the hook ------------------------------------------------------------------------------------


def test_installing_the_hook_replaces_the_default(qapp):
	install_excepthook()
	assert sys.excepthook is not sys.__excepthook__


def test_an_error_in_a_button_handler_is_shown(qapp, boxes):
	install_excepthook()
	button = QPushButton("go")

	def handler():
		raise ValueError("raised inside a click handler")

	button.clicked.connect(handler)
	button.click()
	assert len(boxes) == 1 and "raised inside a click handler" in boxes[0]["text"]


def test_an_uncaught_error_at_the_top_level_is_shown(qapp, boxes):
	install_excepthook()
	sys.excepthook(*raised(OSError("disk on fire")))
	assert "disk on fire" in boxes[0]["text"]


@pytest.mark.parametrize("exc", [KeyboardInterrupt(), SystemExit(0)])
def test_exiting_is_not_reported_as_an_error(qapp, boxes, monkeypatch, exc):
	passed_on = []
	monkeypatch.setattr(sys, "__excepthook__", lambda *a: passed_on.append(a[0]))
	install_excepthook()
	sys.excepthook(*raised(exc))
	assert boxes == [] and passed_on == [type(exc)]


# --- starting the program -----------------------------------------------------------------------------


@pytest.fixture
def start(qapp, monkeypatch, boxes):
	"""Call trader_builder.main() with the event loop and the Windows-only taskbar call stubbed out."""
	monkeypatch.setattr(QApplication, "exec", lambda self: 0)
	monkeypatch.setattr(trader_builder, "fix_win_taskbar", lambda: None)

	def run():
		with pytest.raises(SystemExit) as stop:
			trader_builder.main()
		return stop.value.code

	return run


def test_a_normal_start_runs_the_event_loop(start, boxes):
	assert start() == 0
	assert boxes == []


def test_a_missing_data_file_shows_a_dialog_and_exits(start, boxes, monkeypatch):
	def missing(config):
		raise FileNotFoundError("data/items.json is missing")

	monkeypatch.setattr(trader_builder.AppState, "load", staticmethod(missing))
	assert start() == 1
	(box,) = boxes
	assert box["title"] == "Trader Builder - could not start"
	assert "data/items.json is missing" in box["text"]


def test_a_damaged_data_file_shows_a_dialog_and_exits(start, boxes, monkeypatch):
	import json

	def damaged(config):
		raise json.JSONDecodeError("Expecting value", "{", 1)

	monkeypatch.setattr(trader_builder.AppState, "load", staticmethod(damaged))
	assert start() == 1
	assert "JSONDecodeError" in boxes[0]["text"]


def test_a_settings_error_still_gets_its_own_dialog(start, monkeypatch):
	shown = []
	monkeypatch.setattr(QMessageBox, "critical", staticmethod(lambda parent, title, text: shown.append((title, text))))

	def bad_settings():
		raise ConfigError("the settings file is broken")

	monkeypatch.setattr(trader_builder, "load_config", bad_settings)
	assert start() == 1
	assert shown == [("Trader Builder - settings error", "the settings file is broken")]


def test_starting_installs_the_error_hook(start):
	start()
	assert sys.excepthook is not sys.__excepthook__


def test_the_program_can_start_when_an_application_already_exists(start, qapp):
	# (main() reuses a running QApplication instead of failing to create a second one)
	assert QApplication.instance() is qapp
	assert start() == 0
