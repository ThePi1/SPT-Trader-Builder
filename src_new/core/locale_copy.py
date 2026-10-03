"""Copying text into the other languages' locale files, so a client in another language shows the
text instead of the raw keys.

A mod has one locale file per language in a folder (en.json, ru.json, ...). When the text is saved,
this adds it to each of the other files. Nothing a file already has is ever changed, so a
translation made by hand is safe, and blank text is not copied.
"""

import logging
from pathlib import Path

from core.jsonio import read_json, write_json

log = logging.getLogger(__name__)


def copy_to_other_languages(entries, folder, own_name, languages):
	"""Add entries ({key: text}) to <folder>/<language code>.json for every language but the one whose
	file is own_name (the file the text was just saved to). languages is {code: name}.

	A file that doesn't exist is created. Returns (changed, failed): the names of the files that were
	written, and {file name: reason} for those that couldn't be read or written.
	"""
	texts = {key: text for key, text in entries.items() if isinstance(text, str) and text.strip()}
	changed, failed = [], {}
	if not texts:
		return changed, failed
	folder = Path(folder)
	for code in languages:
		name = f"{code}.json"
		if name.lower() == own_name.lower():
			continue
		path = folder / name
		try:
			existing = read_json(path) if path.is_file() else {}
			if not isinstance(existing, dict):
				failed[name] = "this doesn't look like a text file"
				continue
			merged = dict(existing)
			for key, text in texts.items():
				merged.setdefault(key, text)
			if merged == existing and path.is_file():
				continue
			write_json(path, merged)
			changed.append(name)
		except (OSError, ValueError) as e:
			log.warning(f"Could not add the text to {path}: {e}")
			failed[name] = str(e)
	return changed, failed
