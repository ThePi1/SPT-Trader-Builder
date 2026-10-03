"""The app's settings, kept in data/settings.ini.

Every setting is declared once in ``SETTINGS``. ``Settings.save`` rewrites only the lines of
values that changed, so comments and the order of the file are kept.
"""

import os
import re
from configparser import ConfigParser, Error as ConfigParserError
from dataclasses import dataclass
from pathlib import Path

from core.paths import APP_DIR, SETTINGS_FILE

_TRUE_WORDS = ("1", "yes", "true", "on")
_FALSE_WORDS = ("0", "no", "false", "off")


def parse_bool(text):
	"""'true'/'on'/'yes'/'1' -> True and 'false'/'off'/'no'/'0' -> False (any case), else ValueError."""
	word = str(text).strip().lower()
	if word in _TRUE_WORDS:
		return True
	if word in _FALSE_WORDS:
		return False
	raise ValueError(f"not a true/false value: {text!r}")


@dataclass(frozen=True)
class Setting:
	section: str
	key: str
	kind: str  # "bool", "text", "path" (a file or folder; relative means relative to the program folder), "url"
	default: object


SETTINGS = (
	Setting("general", "debug_logging", "bool", False),
	Setting("general", "merge_locales_on_export", "bool", True),
	Setting("general", "copy_locale_to_all_languages", "bool", False),
	Setting("data", "database_folder", "path", ""),
	Setting("data", "language", "text", "en"),
	Setting("defaults", "quest_icon", "text", "/files/quest/icon/6137505384aedf00fa17b651.jpg"),
	Setting("defaults", "side", "text", "Pmc"),
	Setting("defaults", "trader", "text", ""),
	Setting("display", "show_all_fields", "bool", False),
	Setting("display", "show_json_preview", "bool", False),
	Setting("display", "problems_collapsed", "bool", False),  # (set by the Problems header, not in the dialog)
	Setting("updates", "version_file", "path", "data/version.txt"),
	Setting("updates", "version_url", "url", "https://raw.githubusercontent.com/ThePi1/SPT-Trader-Builder/main/src/data/version.txt"),
	Setting("updates", "project_url", "url", "https://github.com/ThePi1/SPT-Trader-Builder"),
)
BY_KEY = {s.key: s for s in SETTINGS}


class SettingsError(Exception):
	"""settings.ini is unreadable or has a bad entry. The message can be shown to the user as-is."""


class Settings:
	"""The current settings. Each one is an attribute: ``settings.debug_logging`` (a bool),
	``settings.database_folder`` (text), ...  A missing entry has its default."""

	def __init__(self, values=None, path=None):
		self.path = path
		for setting in SETTINGS:
			setattr(self, setting.key, setting.default)
		for key, value in (values or {}).items():
			setattr(self, key, value)

	@classmethod
	def load(cls, path=None):
		path = Path(path or SETTINGS_FILE)
		parser = ConfigParser(interpolation=None)  # (a % in a URL is not a reference)
		try:
			read = parser.read(path, encoding="utf-8")
		except ConfigParserError as e:
			raise SettingsError(f"There is a problem with the settings file:\n{path}\n\n{e}") from e
		if not read:
			return cls(path=path)  # no file yet: every setting has its default
		values = {}
		for setting in SETTINGS:
			text = parser.get(setting.section, setting.key, fallback=None)
			if text is None:
				continue
			try:
				values[setting.key] = parse_bool(text) if setting.kind == "bool" else text.strip()
			except ValueError as e:
				raise SettingsError(f"There is a problem with the settings file:\n{path}\n\n{setting.key}: {e}") from e
		return cls(values, path=path)

	def values(self):
		"""Every setting as {key: value}."""
		return {s.key: getattr(self, s.key) for s in SETTINGS}

	def resolve(self, key):
		"""The full path of a path setting (relative paths are relative to the program folder), or None if empty."""
		text = str(getattr(self, key) or "").strip()
		if not text:
			return None
		path = Path(text)
		return path if path.is_absolute() else APP_DIR / path

	def update(self, values):
		"""Check new {key: value} settings, save them to the file and apply them.

		Raises ValueError (nothing changed) if a value is bad, OSError if the file can't be written.
		"""
		errors = validate(values)
		if errors:
			raise ValueError("; ".join(f"{key}: {message}" for key, message in errors.items()))
		changed = {key: value for key, value in values.items() if getattr(self, key) != value}
		if self.path is not None and changed:
			save(self.path, changed)
		for key, value in changed.items():
			setattr(self, key, value)
		return changed


def validate(values):
	"""{key: message} for each bad value in a {key: value} dict (empty if all are fine)."""
	errors = {}
	for key, value in values.items():
		setting = BY_KEY.get(key)
		if setting is None:
			errors[key] = "Unknown setting."
		elif setting.kind == "bool":
			if not isinstance(value, bool):
				errors[key] = "Must be true or false."
		elif "\n" in str(value) or "\r" in str(value):
			errors[key] = "Must be a single line."
		elif setting.kind == "url" and not re.fullmatch(r"https?://\S+", str(value).strip()):
			errors[key] = "Must be a web address starting with http:// or https://"
	return errors


def to_text(key, value):
	return ("true" if value else "false") if BY_KEY[key].kind == "bool" else str(value)


# --- writing settings.ini without losing its comments ---------------------------------

_SECTION_RE = re.compile(r"^\s*\[([^\]]+)\]\s*$")
_KEY_RE = re.compile(r"^(?P<key>[^=:\s#;\[][^=:]*?)(?P<sep>\s*[=:]\s*)(?P<value>.*)$")


def update_ini_text(text, values):
	"""settings.ini text with the given {key: value} settings changed.

	Only the lines of the changed keys are touched: comments, blank lines, other entries and
	the file's line endings stay as they are. A key that isn't in the file yet is added at the
	end of its section (creating the section if needed).
	"""
	eol = "\r\n" if "\r\n" in text else "\n"
	pending = {key: to_text(key, value) for key, value in values.items()}
	out = []
	section = None
	skipping_continuation = False
	for line in text.splitlines(keepends=True):
		if skipping_continuation:
			# an indented line after a value continues it: drop it along with the old value
			if line.strip() and line[0] in " \t":
				continue
			skipping_continuation = False
		body = line.rstrip("\r\n")
		ending = line[len(body) :]
		m = _SECTION_RE.match(body)
		if m:
			section = m.group(1)
		else:
			m = _KEY_RE.match(body)
			if m:
				key = m.group("key").strip().lower()
				if key in pending and BY_KEY[key].section == section:
					line = f"{m.group('key')}{m.group('sep')}{pending.pop(key)}{ending or eol}"
					skipping_continuation = True
		out.append(line)

	for key in [s.key for s in SETTINGS if s.key in pending]:
		want = BY_KEY[key].section
		start = None
		for i, line in enumerate(out):
			m = _SECTION_RE.match(line.rstrip("\r\n"))
			if m and m.group(1) == want:
				start = i
		if start is None:
			if out and not out[-1].endswith(("\n", "\r")):
				out[-1] += eol
			out += [eol, f"[{want}]{eol}"]
			start = len(out) - 1
		end = start  # (the last non-blank line of the section)
		for i in range(start + 1, len(out)):
			if _SECTION_RE.match(out[i].rstrip("\r\n")):
				break
			if out[i].strip():
				end = i
		if not out[end].endswith(("\n", "\r")):
			out[end] += eol
		out.insert(end + 1, f"{key} = {pending.pop(key)}{eol}")
	return "".join(out)


def save(path, values):
	"""Write {key: value} settings into the settings file (see update_ini_text)."""
	path = Path(path)
	try:
		with open(path, encoding="utf-8", newline="") as f:
			text = f.read()
	except FileNotFoundError:
		text = ""
	new_text = update_ini_text(text, values)
	tmp_path = path.with_name(path.name + ".tmp")
	try:
		with open(tmp_path, "w", encoding="utf-8", newline="") as f:
			f.write(new_text)
		os.replace(tmp_path, path)
	finally:
		if tmp_path.exists():
			tmp_path.unlink()
