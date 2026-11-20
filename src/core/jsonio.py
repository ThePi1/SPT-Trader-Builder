"""Reading and writing JSON files the way SPT and its mods expect them."""

import json
import logging
import os
from contextlib import contextmanager
from pathlib import Path

log = logging.getLogger(__name__)

# JSON files are read as UTF-8 (what SPT and the mods write). Files with Russian text have
# also turned up in the legacy DOS code page, so that is tried if UTF-8 doesn't fit; it can
# decode any byte, so it always works as a last resort.
_ENCODINGS = ("utf-8-sig", "cp866")

# SPT's own files are indented with 4 spaces
INDENT = 4


def read_json(path):
	"""Load a JSON file, whatever (UTF-8 or Russian code page) encoding it was saved in.

	Raises OSError if it can't be read and json.JSONDecodeError if it isn't valid JSON.
	"""
	data = Path(path).read_bytes()
	for encoding in _ENCODINGS:
		try:
			text = data.decode(encoding)
		except UnicodeDecodeError:
			continue
		if encoding != _ENCODINGS[0]:
			log.warning(f"{path} is not UTF-8; read it as {encoding}")
		return json.loads(text)  # (a decode that worked but isn't valid JSON is just bad JSON)
	raise AssertionError("unreachable: the last encoding decodes anything")


def dumps(data, indent=INDENT):
	"""data as JSON text, keeping non-English text (e.g. Russian) readable."""
	return json.dumps(data, indent=indent, ensure_ascii=False)


def write_json(path, data, indent=INDENT):
	"""Save data as UTF-8 JSON, swapped in when written (see replacing)."""
	text = dumps(data, indent)
	with replacing(path, "w", encoding="utf-8", newline="\n") as f:
		f.write(text)
		f.write("\n")


@contextmanager
def replacing(path, mode="wb", **options):
	"""Open a file to write in place of path. It is written under a temporary name and swapped in when done, so a
	failure can't leave a half-written file, and whoever reads path meanwhile gets the old file or the new one."""
	path = Path(path)
	tmp_path = path.with_name(path.name + ".tmp")
	try:
		with open(tmp_path, mode, **options) as f:
			yield f
		os.replace(tmp_path, path)
	finally:
		if tmp_path.exists():
			tmp_path.unlink()
