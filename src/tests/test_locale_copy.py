import json

from core.locale_copy import copy_to_other_languages

LANGUAGES = {"en": "English", "ru": "Russian", "fr": "French"}


def write(path, data):
	path.write_text(json.dumps(data), encoding="utf-8")


def read(path):
	return json.loads(path.read_text(encoding="utf-8"))


def test_creates_the_other_languages_files_and_skips_its_own(tmp_path):
	changed, failed = copy_to_other_languages({"a": "text", "b": "more"}, tmp_path, "en.json", LANGUAGES)
	assert sorted(changed) == ["fr.json", "ru.json"] and failed == {}
	assert read(tmp_path / "ru.json") == {"a": "text", "b": "more"}
	assert not (tmp_path / "en.json").exists()


def test_a_file_named_something_else_is_copied_to_every_language(tmp_path):
	changed, _ = copy_to_other_languages({"a": "text"}, tmp_path, "my text.json", LANGUAGES)
	assert sorted(changed) == ["en.json", "fr.json", "ru.json"]


def test_existing_entries_are_kept(tmp_path):
	write(tmp_path / "ru.json", {"a": "translated by hand", "other": "x"})
	copy_to_other_languages({"a": "text", "b": "more"}, tmp_path, "en.json", LANGUAGES)
	assert read(tmp_path / "ru.json") == {"a": "translated by hand", "other": "x", "b": "more"}


def test_blank_text_is_not_copied_and_nothing_is_written_for_nothing(tmp_path):
	assert copy_to_other_languages({"a": "", "b": "   "}, tmp_path, "en.json", LANGUAGES) == ([], {})
	assert list(tmp_path.iterdir()) == []


def test_a_file_that_already_has_everything_is_not_rewritten(tmp_path):
	write(tmp_path / "ru.json", {"a": "x"})
	changed, _ = copy_to_other_languages({"a": "text"}, tmp_path, "en.json", {"ru": "Russian"})
	assert changed == []


def test_a_file_that_is_not_a_text_file_is_reported_and_left_alone(tmp_path):
	(tmp_path / "ru.json").write_text("[1, 2]", encoding="utf-8")
	(tmp_path / "fr.json").write_text("not json", encoding="utf-8")
	changed, failed = copy_to_other_languages({"a": "text"}, tmp_path, "en.json", LANGUAGES)
	assert changed == [] and set(failed) == {"ru.json", "fr.json"}
	assert (tmp_path / "ru.json").read_text(encoding="utf-8") == "[1, 2]"


def test_russian_text_stays_readable(tmp_path):
	copy_to_other_languages({"a": "Привет"}, tmp_path, "en.json", {"ru": "Russian"})
	assert "Привет" in (tmp_path / "ru.json").read_text(encoding="utf-8")
