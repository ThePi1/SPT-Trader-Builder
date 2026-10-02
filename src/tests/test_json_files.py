"""Reading and writing JSON files: Russian text in any common encoding, and clear errors for bad files."""

import json

import pytest

import utils
from utils import read_json, write_json

RUSSIAN = "Привет, Прапор! Задание №1"


# --- read_json -------------------------------------------------------------------------


def test_reads_plain_utf8(tmp_path):
	f = tmp_path / "a.json"
	f.write_text(json.dumps({"name": RUSSIAN}, ensure_ascii=False), encoding="utf-8")
	assert read_json(f) == {"name": RUSSIAN}


def test_reads_utf8_with_a_byte_order_mark(tmp_path):
	f = tmp_path / "a.json"
	f.write_bytes(b"\xef\xbb\xbf" + json.dumps({"name": RUSSIAN}, ensure_ascii=False).encode("utf-8"))
	assert read_json(f) == {"name": RUSSIAN}


def test_reads_a_file_saved_in_the_russian_dos_code_page(tmp_path):
	f = tmp_path / "a.json"
	f.write_bytes(json.dumps({"name": RUSSIAN}, ensure_ascii=False).encode("cp866"))
	assert read_json(f) == {"name": RUSSIAN}


def test_ascii_escaped_files_read_fine(tmp_path):
	f = tmp_path / "a.json"
	f.write_text(json.dumps({"name": RUSSIAN}), encoding="ascii")  # (П... escapes)
	assert read_json(f) == {"name": RUSSIAN}


def test_the_fallback_is_noted_in_the_log(tmp_path, caplog):
	f = tmp_path / "a.json"
	f.write_bytes(json.dumps({"name": RUSSIAN}, ensure_ascii=False).encode("cp866"))
	read_json(f)
	assert "cp866" in caplog.text


def test_utf8_files_do_not_log_a_fallback(tmp_path, caplog):
	f = tmp_path / "a.json"
	f.write_text('{"a": 1}', encoding="utf-8")
	read_json(f)
	assert "cp866" not in caplog.text


def test_invalid_json_is_reported_as_such_not_as_an_encoding_problem(tmp_path):
	f = tmp_path / "a.json"
	f.write_text("{ not json", encoding="utf-8")
	with pytest.raises(json.JSONDecodeError):
		read_json(f)


def test_a_missing_file_raises_oserror(tmp_path):
	with pytest.raises(OSError):
		read_json(tmp_path / "nope.json")


def test_text_with_no_valid_encoding_still_loads(tmp_path):
	f = tmp_path / "a.json"
	f.write_bytes(b'{"x": "\xff\xfe\x80"}')  # not UTF-8 text at all
	assert "x" in read_json(f)


# --- write_json ------------------------------------------------------------------------


def test_writes_utf8_and_keeps_russian_readable(tmp_path):
	f = tmp_path / "out.json"
	write_json(f, {"name": RUSSIAN})
	raw = f.read_bytes().decode("utf-8")
	assert RUSSIAN in raw and "\\u04" not in raw
	assert read_json(f) == {"name": RUSSIAN}


def test_indent_is_applied(tmp_path):
	f = tmp_path / "out.json"
	write_json(f, {"a": [1]}, indent=4)
	assert f.read_text(encoding="utf-8") == '{\n    "a": [\n        1\n    ]\n}'


def test_compact_output_when_indent_is_none(tmp_path):
	f = tmp_path / "out.json"
	write_json(f, {"a": 1}, indent=None)
	assert f.read_text(encoding="utf-8") == '{"a": 1}'


def test_data_that_cannot_be_saved_leaves_the_file_alone(tmp_path):
	f = tmp_path / "out.json"
	f.write_text("original", encoding="utf-8")
	with pytest.raises(TypeError):
		write_json(f, {"bad": {1, 2}})  # a set isn't JSON
	assert f.read_text(encoding="utf-8") == "original"


def test_data_that_cannot_be_saved_does_not_create_a_file(tmp_path):
	f = tmp_path / "out.json"
	with pytest.raises(TypeError):
		write_json(f, {"bad": object()})
	assert not f.exists()


def _source_lines():
	from pathlib import Path

	src = Path(utils.__file__).parent
	for path in sorted(list(src.glob("*.py")) + list((src / "windows").glob("*.py"))):
		for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
			yield path, number, line.split("#")[0]


def test_json_is_only_read_through_read_json():
	"""No code path reads JSON with json.load (which leaves the encoding to the caller)."""
	offenders = [
		f"{path.name}:{n}: {code.strip()}"
		for path, n, code in _source_lines()
		if path.name != "utils.py" and "json.load(" in code
	]
	assert offenders == []


def test_every_file_is_opened_with_an_explicit_encoding():
	"""open() without encoding= uses the platform default (cp1252 on Windows), which breaks Russian text."""
	offenders = [
		f"{path.name}:{n}: {code.strip()}"
		for path, n, code in _source_lines()
		if " open(" in code and "encoding=" not in code
	]
	assert offenders == []


def test_no_leftover_russian_code_page_hack():
	offenders = [
		f"{path.name}:{n}"
		for path, n, code in _source_lines()
		if path.name != "utils.py" and "cp866" in code
	]
	assert offenders == []  # (only read_json knows about the fallback)
