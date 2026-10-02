"""Small helpers shared by the GUI and the entry point."""

import json
import logging
import os
import secrets
from logging.handlers import RotatingFileHandler
from pathlib import Path

from modules.paths import APP_DIR

# Next to the program: src/ when running from source, next to the .exe when packaged
# (APP_DIR knows the difference; the folder this file is in would be a temporary
# folder in a one-file PyInstaller build).
LOG_FILE = APP_DIR / "trader_builder.log"

_LOG_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"


def new_id():
	"""A new 24-character hex ID, the same shape as a Mongo ObjectId (what SPT expects)."""
	return secrets.token_hex(12)


# JSON files are read as UTF-8 (what SPT and the mods write). Files with Russian text have
# also turned up in the legacy DOS code page, so that is tried if UTF-8 doesn't fit; it can
# decode any byte, so it always works as a last resort.
_JSON_ENCODINGS = ("utf-8-sig", "cp866")


def read_json(path):
	"""Load a JSON file, whatever (UTF-8 or Russian code page) encoding it was saved in.

	Raises OSError if it can't be read and json.JSONDecodeError if it isn't valid JSON.
	"""
	data = Path(path).read_bytes()
	for encoding in _JSON_ENCODINGS:
		try:
			text = data.decode(encoding)
		except UnicodeDecodeError:
			continue
		if encoding != _JSON_ENCODINGS[0]:
			logging.getLogger(__name__).warning(f"{path} is not UTF-8; read it as {encoding}")
		return json.loads(text)  # (a decode that worked but isn't valid JSON is just bad JSON)


def write_json(path, data, indent=2):
	"""Save data as UTF-8 JSON, keeping non-English text (e.g. Russian) readable in the file."""
	text = json.dumps(data, indent=indent, ensure_ascii=False)  # (before opening, so an error can't leave a half-written file)
	with open(path, "w", encoding="utf-8") as f:
		f.write(text)


def is_true(val):
	"""Parse a string like 'true', 'on', 'no', '0' into a boolean."""
	val = val.lower()
	if val in ("y", "yes", "t", "true", "on", "1"):
		return True
	elif val in ("n", "no", "f", "false", "off", "0"):
		return False
	else:
		raise ValueError("invalid truth value %r" % (val,))


def val_field(value, emptyval, defaultval, expectclass):
	"""Convert a field's text to expectclass, falling back to a default when empty or invalid."""
	if value == emptyval:
		return defaultval
	else:
		try:
			convert_val = expectclass(value)
			return convert_val
		except Exception:
			if expectclass == int:
				return 0
			if expectclass == float:
				return 0.0
			if expectclass == list:
				return []
			if expectclass == dict:
				return {}
			return ""


def setup_logging():
	"""Log INFO and above to the console. Safe to call more than once.

	The detailed log file is separate and optional: see set_debug_logging.
	"""
	root = logging.getLogger()
	if getattr(root, "_trader_builder_configured", False):
		return
	root.setLevel(logging.DEBUG)
	console = logging.StreamHandler()
	console.setLevel(logging.INFO)
	console.setFormatter(logging.Formatter(_LOG_FORMAT))
	root.addHandler(console)
	root._trader_builder_configured = True


def set_debug_logging(enabled, log_file=None):
	"""Turn the detailed (DEBUG and above) log file on or off.

	The file is a rotating log (about 500 KB, 2 older copies kept). Enabling is safe to
	repeat; if the file can't be opened an OSError is raised and nothing is changed.
	"""
	root = logging.getLogger()
	current = getattr(root, "_trader_builder_file_handler", None)
	if not enabled:
		if current is not None:
			root.removeHandler(current)
			current.close()
			root._trader_builder_file_handler = None
		return
	log_file = log_file or LOG_FILE
	if current is not None and current.baseFilename == os.path.abspath(log_file):
		return  # already writing there
	root.setLevel(logging.DEBUG)  # (so debug messages reach the file whatever was set up before)
	handler = RotatingFileHandler(log_file, maxBytes=512_000, backupCount=2, encoding="utf-8")
	handler.setLevel(logging.DEBUG)
	handler.setFormatter(logging.Formatter(_LOG_FORMAT))
	if current is not None:  # (switching to a different file)
		root.removeHandler(current)
		current.close()
	root.addHandler(handler)
	root._trader_builder_file_handler = handler
	logging.getLogger(__name__).info(f"Debug logging to {log_file}")
