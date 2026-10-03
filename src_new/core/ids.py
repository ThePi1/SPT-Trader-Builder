"""Ids in SPT data: 24-character hex strings, the same shape as a Mongo ObjectId."""

import re
import secrets

_ID_RE = re.compile(r"[0-9a-fA-F]{24}")


def new_id():
	"""A new random id."""
	return secrets.token_hex(12)


def is_id(value):
	"""True if value is a string SPT accepts as an id (24 hex characters, any case)."""
	return isinstance(value, str) and _ID_RE.fullmatch(value) is not None
