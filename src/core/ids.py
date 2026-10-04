"""Ids in SPT data: 24-character hex strings laid out like a Mongo ObjectId (what SPT's MongoIds are).

An ObjectId is 12 bytes: 4 of the time (seconds since 1970), 5 random bytes that stay the same for one run
of the program, and a 3-byte counter that goes up by one for each id. That is what pymongo's bson.ObjectId
makes; it is done here in a few lines so the program needs no extra library. Ids made one after another
are different (the counter), and they sort roughly by when they were made.
"""

import itertools
import os
import re
import secrets
import time

_ID_RE = re.compile(r"[0-9a-fA-F]{24}")
_process = {"pid": None, "random": b"", "counter": None}


def _reseed():
	"""New random bytes and a new counter start (also after the process changed, as bson does)."""
	_process["pid"] = os.getpid()
	_process["random"] = secrets.token_bytes(5)
	_process["counter"] = itertools.count(secrets.randbits(24))


def new_id():
	"""A new id: time (4 bytes) + random for this run (5 bytes) + counter (3 bytes), as 24 hex characters."""
	if _process["pid"] != os.getpid():
		_reseed()
	stamp = (int(time.time()) & 0xFFFFFFFF).to_bytes(4, "big")
	count = (next(_process["counter"]) & 0xFFFFFF).to_bytes(3, "big")
	return (stamp + _process["random"] + count).hex()


def is_id(value):
	"""True if value is a string SPT accepts as an id (24 hex characters, any case)."""
	return isinstance(value, str) and _ID_RE.fullmatch(value) is not None
