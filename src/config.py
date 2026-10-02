"""Loads settings.ini (real settings) and box_fields.json (dropdown lists).

settings.ini can be edited from the Settings dialog: ``Config.update_settings`` validates
the new values, rewrites only the changed lines of the file (comments are kept), and
applies them to the running app.
"""

import json
import os
import re
from configparser import ConfigParser, Error as ConfigParserError
from pathlib import Path

from paths import APP_DIR, DATA_DIR
from utils import read_json

# Every value in settings.ini, in file order, as (section, key). Key names are unique,
# so a settings dict is just {key: value}.
SETTINGS_KEYS = (
	("general", "debug_logging"),
	("general", "merge_locales_on_export"),
	("filepaths", "version_file"),
	("filepaths", "version_url"),
	("filepaths", "project_url"),
	("filepaths", "items_file"),
	("defaults", "default_questicon"),
)
SETTING_NAMES = tuple(key for _, key in SETTINGS_KEYS)

# Settings that are true/false. In a settings dict they are the text "true" / "false";
# on the Config object they are real booleans.
BOOL_SETTING_NAMES = ("debug_logging", "merge_locales_on_export")

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

# The item database the program uses unless another one is chosen in Settings: the items.json
# that ships with the program (relative paths are relative to the program folder).
DEFAULT_ITEMS_FILE = "data/items.json"


def resolve_items_path(text):
	"""The full path of an items_file setting. Empty means the included file; relative paths are
	relative to the program folder."""
	path = Path((text or "").strip() or DEFAULT_ITEMS_FILE)
	return path if path.is_absolute() else APP_DIR / path


# Changing any of these means the update check should be run again
UPDATE_SETTING_NAMES = ("version_file", "version_url", "project_url")

# Every list the GUI expects to find in data/box_fields.json
BOX_FIELD_KEYS = (
	"default_tf",
	"default_ft",
	"default_skills",
	"default_compare",
	"reward_timing",
	"qb_box_avail_faction",
	"qb_box_quest_type_label",
	"qb_box_location",
	"ab_box_loyalty_level",
	"ab_box_condition_req",
	"ab_box_modslot",
	"tb_elim_box_target",
	"tb_elim_box_targetrole",
	"tb_elim_box_bodypart",
	"tb_elim_box_weapons",
	"tb_handover_box_cond_type",
	"tb_exitstatus",
	"tb_queststatus",
	"tb_finishfail",
	"tb_any",
	"tb_effect",
	"tb_buff",
)


class ConfigError(Exception):
	"""A settings file is missing, unreadable, or has a bad/missing entry.

	The message is written to be shown to the user as-is.
	"""


class Config:
	"""App configuration. Dropdown lists are available as attributes, e.g. ``config.default_tf``."""

	def __init__(
		self,
		version_file,
		version_url,
		project_url,
		default_questicon,
		box_fields,
		settings_path=None,
		debug_logging=False,
		items_file=DEFAULT_ITEMS_FILE,
		merge_locales_on_export=True,
	):
		self.settings_path = settings_path
		self.items_file = items_file
		self.debug_logging = debug_logging
		self.merge_locales_on_export = merge_locales_on_export
		self.version_file = version_file
		self.version_url = version_url
		self.project_url = project_url
		self.default_questicon = default_questicon
		self.box_fields = box_fields

	def items_path(self):
		"""Where the item database is: the file chosen in Settings, or the included data/items.json."""
		return resolve_items_path(self.items_file)

	def settings(self):
		"""The current value of everything in settings.ini, as {key: text}."""
		return {
			name: (("true" if getattr(self, name) else "false") if name in BOOL_SETTING_NAMES else getattr(self, name))
			for name in SETTING_NAMES
		}

	def update_settings(self, values):
		"""Save new settings to settings.ini and apply them to this running config.

		Raises ValueError if a value is invalid (nothing is saved), and OSError if the
		file can't be written (the running config is left unchanged).
		"""
		values = {name: values[name].strip() for name in SETTING_NAMES}
		errors = validate_settings(values)
		if errors:
			raise ValueError("; ".join(f"{name}: {msg}" for name, msg in errors.items()))
		if self.settings_path is None:
			raise OSError("This configuration was not loaded from a settings file.")
		save_settings(self.settings_path, values)
		for name, value in values.items():
			setattr(self, name, parse_bool(value) if name in BOOL_SETTING_NAMES else value)

	def __getattr__(self, name):
		# only called when normal lookup fails; lets config.default_tf work
		box_fields = self.__dict__.get("box_fields", {})
		if name in box_fields:
			return box_fields[name]
		raise AttributeError(name)


def load_config(settings_path=None, box_fields_path=None):
	settings_path = settings_path or DATA_DIR / "settings.ini"
	box_fields_path = box_fields_path or DATA_DIR / "box_fields.json"

	# interpolation=None: values are literal, so a % in a URL isn't treated as a reference
	parser = ConfigParser(interpolation=None)
	if not parser.read(settings_path, encoding="utf-8"):
		raise ConfigError(f"Could not read the settings file:\n{settings_path}")
	try:
		version_file = parser.get("filepaths", "version_file")
		version_url = parser.get("filepaths", "version_url")
		project_url = parser.get("filepaths", "project_url")
		default_questicon = parser.get("defaults", "default_questicon")
		# (optional: a settings file from before this existed simply has it off)
		debug_logging = parser.getboolean("general", "debug_logging", fallback=False)
		# (optional too: missing means on, which is what exporting quests always did)
		merge_locales_on_export = parser.getboolean("general", "merge_locales_on_export", fallback=True)
		# (optional too: which items.json to use; missing or empty means the included one)
		items_file = parser.get("filepaths", "items_file", fallback="").strip() or DEFAULT_ITEMS_FILE
	except (ConfigParserError, ValueError) as e:
		raise ConfigError(
			f"There is a problem with the settings file:\n{settings_path}\n\n{e}"
		) from e

	try:
		box_fields = read_json(box_fields_path)
	except OSError as e:
		raise ConfigError(f"Could not read the dropdown lists file:\n{box_fields_path}\n\n{e}") from e
	except json.JSONDecodeError as e:
		raise ConfigError(
			f"The dropdown lists file is not valid JSON:\n{box_fields_path}\n\n{e}"
		) from e

	missing = [k for k in BOX_FIELD_KEYS if k not in box_fields]
	if missing:
		raise ConfigError(
			f"The dropdown lists file is missing these entries:\n{box_fields_path}\n\n"
			+ ", ".join(missing)
		)
	bad = [k for k in BOX_FIELD_KEYS if not isinstance(box_fields[k], list)]
	if bad:
		raise ConfigError(
			f"These entries in {box_fields_path} must be lists:\n\n" + ", ".join(bad)
		)

	return Config(
		version_file=version_file,
		version_url=version_url,
		project_url=project_url,
		default_questicon=default_questicon,
		box_fields=box_fields,
		settings_path=settings_path,
		debug_logging=debug_logging,
		items_file=items_file,
		merge_locales_on_export=merge_locales_on_export,
	)


# --- editing settings.ini ------------------------------------------------------------


def validate_settings(values):
	"""Check a {key: value} dict of settings.

	Returns {key: message} for each bad value (empty if everything is fine).
	"""
	errors = {}
	for name in SETTING_NAMES:
		value = values.get(name, "")
		if "\n" in value or "\r" in value:
			errors[name] = "Must be a single line."
	for name in BOOL_SETTING_NAMES:
		if name not in errors:
			try:
				parse_bool(values.get(name, ""))
			except ValueError:
				errors[name] = "Must be true or false."
	for name in ("version_file", "default_questicon"):
		if name not in errors and not values.get(name, "").strip():
			errors[name] = "Required."
	for name in ("version_url", "project_url"):
		if name not in errors and not re.fullmatch(r"https?://\S+", values.get(name, "").strip()):
			errors[name] = "Must be a web address starting with http:// or https://"
	return errors


_SECTION_RE = re.compile(r"^\s*\[([^\]]+)\]\s*$")
_KEY_RE = re.compile(r"^(?P<key>[^=:\s#;\[][^=:]*?)(?P<sep>\s*[=:]\s*)(?P<value>.*)$")


def _is_section_line(line):
	return _SECTION_RE.match(line.rstrip("\r\n")) is not None


def update_ini_text(text, values):
	"""Return settings.ini text with the given {key: value} settings changed.

	Only the lines of the changed keys are touched: comments, blank lines, other
	entries and the file's line endings stay as they are. A key that isn't in the
	file yet is added at the end of its section (creating the section if needed).
	"""
	for name, value in values.items():
		if "\n" in value or "\r" in value:
			raise ValueError(f"{name} must be a single line")
	section_of = {key: section for section, key in SETTINGS_KEYS}
	eol = "\r\n" if "\r\n" in text else "\n"
	pending = dict(values)

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
				if key in pending and section_of.get(key) == section:
					line = f"{m.group('key')}{m.group('sep')}{pending.pop(key)}{ending or eol}"
					skipping_continuation = True
		out.append(line)

	# keys that weren't in the file: add them to the end of their section
	for name in [n for n in SETTING_NAMES if n in pending]:
		want = section_of[name]
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
		# the last non-blank line of the section
		end = start
		for i in range(start + 1, len(out)):
			if _is_section_line(out[i]):
				break
			if out[i].strip():
				end = i
		if not out[end].endswith(("\n", "\r")):
			out[end] += eol
		out.insert(end + 1, f"{name} = {pending.pop(name)}{eol}")
	return "".join(out)


def save_settings(settings_path, values):
	"""Write {key: value} settings into settings.ini (see update_ini_text)."""
	settings_path = Path(settings_path)
	with open(settings_path, encoding="utf-8", newline="") as f:
		text = f.read()
	new_text = update_ini_text(text, values)
	# write a temp file and swap it in, so a failure can't leave a half-written settings file
	tmp_path = settings_path.with_name(settings_path.name + ".tmp")
	try:
		with open(tmp_path, "w", encoding="utf-8", newline="") as f:
			f.write(new_text)
		os.replace(tmp_path, settings_path)
	finally:
		if tmp_path.exists():
			tmp_path.unlink()
