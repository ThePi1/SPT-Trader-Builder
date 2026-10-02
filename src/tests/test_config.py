import json

import pytest

from config import BOX_FIELD_KEYS, ConfigError, load_config
from paths import DATA_DIR


def test_real_config_loads():
	config = load_config()
	assert config.project_url.startswith("http")
	for key in BOX_FIELD_KEYS:
		assert isinstance(getattr(config, key), list) and getattr(config, key), key
	assert config.default_tf == ["true", "false"]


def _copy_settings(tmp_path, box_fields=None):
	settings = tmp_path / "settings.ini"
	settings.write_text((DATA_DIR / "settings.ini").read_text(encoding="utf-8"), encoding="utf-8")
	fields = tmp_path / "box_fields.json"
	if box_fields is None:
		box_fields = json.loads((DATA_DIR / "box_fields.json").read_text(encoding="utf-8"))
	fields.write_text(json.dumps(box_fields), encoding="utf-8")
	return settings, fields


def test_missing_box_field_is_reported(tmp_path):
	data = json.loads((DATA_DIR / "box_fields.json").read_text(encoding="utf-8"))
	del data["tb_buff"]
	settings, fields = _copy_settings(tmp_path, data)
	with pytest.raises(ConfigError, match="tb_buff"):
		load_config(settings, fields)


def test_bad_json_is_reported(tmp_path):
	settings, fields = _copy_settings(tmp_path)
	fields.write_text("{ not json", encoding="utf-8")
	with pytest.raises(ConfigError, match="not valid JSON"):
		load_config(settings, fields)


def test_missing_settings_file_is_reported(tmp_path):
	_, fields = _copy_settings(tmp_path)
	with pytest.raises(ConfigError, match="settings file"):
		load_config(tmp_path / "nope.ini", fields)


def test_missing_ini_entry_is_reported(tmp_path):
	settings, fields = _copy_settings(tmp_path)
	settings.write_text("[filepaths]\nversion_file = x\n", encoding="utf-8")
	with pytest.raises(ConfigError, match="problem with the settings file"):
		load_config(settings, fields)


def test_the_dropdown_lists_file_has_nothing_the_program_does_not_use():
	import json

	shipped = json.loads((DATA_DIR / "box_fields.json").read_text(encoding="utf-8"))
	assert sorted(shipped) == sorted(BOX_FIELD_KEYS)


def test_every_required_dropdown_list_is_used_by_the_program():
	from pathlib import Path

	src = Path(DATA_DIR).parent
	code = "\n".join(
		"\n".join(line.split("#")[0] for line in path.read_text(encoding="utf-8").splitlines())
		for path in list(src.glob("*.py")) + list((src / "windows").glob("*.py"))
		if path.name != "config.py"
	)
	unused = [key for key in BOX_FIELD_KEYS if key not in code]
	assert unused == []
