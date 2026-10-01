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
