"""Logging: INFO to the console, and an optional detailed log file for troubleshooting."""

import logging
import os
from logging.handlers import RotatingFileHandler

from core.paths import APP_DIR

# Next to the program: src/ when running from source, next to the .exe when packaged
LOG_FILE = APP_DIR / "spt_trader_builder.log"

_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"


def setup_logging():
	"""Log INFO and above to the console. Safe to call more than once."""
	root = logging.getLogger()
	if getattr(root, "_spt_trader_builder_configured", False):
		return
	root.setLevel(logging.DEBUG)
	console = logging.StreamHandler()
	console.setLevel(logging.INFO)
	console.setFormatter(logging.Formatter(_FORMAT))
	root.addHandler(console)
	root._spt_trader_builder_configured = True


def set_debug_logging(enabled, log_file=None):
	"""Turn the detailed (DEBUG and above) log file on or off.

	The file is a rotating log (about 500 KB, 2 older copies kept). Enabling is safe to
	repeat; if the file can't be opened an OSError is raised and nothing is changed.
	"""
	root = logging.getLogger()
	current = getattr(root, "_spt_trader_builder_file_handler", None)
	if not enabled:
		if current is not None:
			root.removeHandler(current)
			current.close()
			root._spt_trader_builder_file_handler = None
		return
	log_file = log_file or LOG_FILE
	if current is not None and current.baseFilename == os.path.abspath(log_file):
		return  # already writing there
	root.setLevel(logging.DEBUG)
	handler = RotatingFileHandler(log_file, maxBytes=512_000, backupCount=2, encoding="utf-8")
	handler.setLevel(logging.DEBUG)
	handler.setFormatter(logging.Formatter(_FORMAT))
	if current is not None:
		root.removeHandler(current)
		current.close()
	root.addHandler(handler)
	root._spt_trader_builder_file_handler = handler
	logging.getLogger(__name__).info(f"Debug logging to {log_file}")
