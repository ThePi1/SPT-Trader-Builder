"""The files that were open when the program was last closed (for the "Load last files on open" setting).

Kept in data/last_files.json as {"quests": path or null, "locale": ..., "assort": ..., "locks": ...}. Files that were
imported are not part of it: only the file each section was opened from or saved to. No Qt.
"""

import logging
from pathlib import Path

from core import jsonio
from core.paths import LAST_FILES_FILE

log = logging.getLogger(__name__)
KEYS = ("quests", "locale", "assort", "locks")


class LastFiles:
	def __init__(self, path=None):
		self.path = Path(path) if path else LAST_FILES_FILE

	def read(self):
		"""{section: path} of the files that were open (a section with none is left out)."""
		try:
			data = jsonio.read_json(self.path) if self.path.is_file() else {}
		except (OSError, ValueError):
			return {}
		if not isinstance(data, dict):
			return {}
		return {key: data[key] for key in KEYS if isinstance(data.get(key), str) and data[key]}

	def write(self, paths):
		"""Remember {section: path or None}. A file that can't be written is not worth stopping for."""
		try:
			jsonio.write_json(self.path, {key: paths.get(key) for key in KEYS})
		except OSError as e:
			log.warning(f"Could not remember the open files in {self.path}: {e}")
