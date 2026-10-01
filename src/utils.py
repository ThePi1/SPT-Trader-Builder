"""Small helpers shared by the GUI and the entry point."""

import logging
import secrets
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FILE = Path(__file__).parent / "trader_builder.log"


def new_id():
	"""A new 24-character hex ID, the same shape as a Mongo ObjectId (what SPT expects)."""
	return secrets.token_hex(12)


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


def setup_logging(log_file=LOG_FILE):
	"""Log INFO and above to the console, and everything (DEBUG+) to a rotating log file.

	Safe to call more than once.
	"""
	root = logging.getLogger()
	if getattr(root, "_trader_builder_configured", False):
		return
	root.setLevel(logging.DEBUG)
	fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s")

	console = logging.StreamHandler()
	console.setLevel(logging.INFO)
	console.setFormatter(fmt)
	root.addHandler(console)

	try:
		file_handler = RotatingFileHandler(
			log_file, maxBytes=512_000, backupCount=2, encoding="utf-8"
		)
		file_handler.setLevel(logging.DEBUG)
		file_handler.setFormatter(fmt)
		root.addHandler(file_handler)
	except OSError as e:
		root.warning("Could not open log file %s: %s", log_file, e)
	root._trader_builder_configured = True
