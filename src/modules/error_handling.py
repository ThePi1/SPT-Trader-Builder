"""Make unexpected errors visible.

The packaged program has no console, so an error nobody catches (a failure while starting,
or inside a button's handler) would otherwise vanish. Everything that reaches
``sys.excepthook`` is logged and shown to the user in a dialog with the full details.
"""

import logging
import sys
import traceback

from PySide6.QtWidgets import QApplication, QMessageBox

log = logging.getLogger(__name__)

_showing_dialog = False  # (an error while showing an error must not stack up dialogs)


def report_exception(exc_type, exc_value, exc_tb, title="Trader Builder - unexpected error"):
	"""Log an unexpected error, and show it with the full details the user can copy."""
	log.error("Unexpected error", exc_info=(exc_type, exc_value, exc_tb))
	global _showing_dialog
	if _showing_dialog or QApplication.instance() is None:
		return
	_showing_dialog = True
	try:
		box = QMessageBox(
			QMessageBox.Icon.Critical,
			title,
			f"Something went wrong:\n\n{exc_type.__name__}: {exc_value}",
			QMessageBox.StandardButton.Ok,
		)
		box.setInformativeText(
			"Your work may be unaffected, but if anything looks wrong, save what you can "
			"and restart the program. Open Show Details for the full error to include in a bug report."
		)
		box.setDetailedText("".join(traceback.format_exception(exc_type, exc_value, exc_tb)))
		box.exec()
	finally:
		_showing_dialog = False


def install_excepthook():
	"""Send every uncaught error (including those raised inside Qt handlers) to report_exception."""

	def hook(exc_type, exc_value, exc_tb):
		if issubclass(exc_type, (KeyboardInterrupt, SystemExit)):
			sys.__excepthook__(exc_type, exc_value, exc_tb)
			return
		report_exception(exc_type, exc_value, exc_tb)

	sys.excepthook = hook
