"""Loads settings.ini (real settings) and box_fields.json (dropdown lists)."""

import json
from configparser import ConfigParser, Error as ConfigParserError

from paths import DATA_DIR

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
	"qb_box_reward",
	"qb_box_status",
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
		default_locale,
		box_fields,
	):
		self.version_file = version_file
		self.version_url = version_url
		self.project_url = project_url
		self.default_questicon = default_questicon
		self.default_locale = default_locale
		self.box_fields = box_fields

	def __getattr__(self, name):
		# only called when normal lookup fails; lets config.default_tf work
		box_fields = self.__dict__.get("box_fields", {})
		if name in box_fields:
			return box_fields[name]
		raise AttributeError(name)


def load_config(settings_path=None, box_fields_path=None):
	settings_path = settings_path or DATA_DIR / "settings.ini"
	box_fields_path = box_fields_path or DATA_DIR / "box_fields.json"

	parser = ConfigParser()
	if not parser.read(settings_path, encoding="utf-8"):
		raise ConfigError(f"Could not read the settings file:\n{settings_path}")
	try:
		version_file = parser.get("filepaths", "version_file")
		version_url = parser.get("filepaths", "version_url")
		project_url = parser.get("filepaths", "project_url")
		default_questicon = parser.get("defaults", "default_questicon")
		default_locale = parser.get("defaults", "default_locale")
	except ConfigParserError as e:
		raise ConfigError(
			f"There is a problem with the settings file:\n{settings_path}\n\n{e}"
		) from e

	try:
		with open(box_fields_path, encoding="utf-8") as f:
			box_fields = json.load(f)
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
		default_locale=default_locale,
		box_fields=box_fields,
	)
