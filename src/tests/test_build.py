"""The build script puts LICENSE next to the built program (the build itself is run by hand), and LICENSE says what it must."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import build


def license_text():
	return (ROOT / "LICENSE").read_bytes().decode("utf-8").replace("\r\n", "\n")


def test_the_license_file_is_in_the_root_of_the_repository_and_there_is_no_separate_notice():
	assert build.LICENSE_FILE == ROOT / "LICENSE" and build.LICENSE_FILE.is_file()
	assert not (ROOT / "NOTICE.txt").exists()


def test_add_license_copies_it_next_to_the_program(tmp_path):
	build.add_license(tmp_path)
	assert (tmp_path / "LICENSE").read_bytes() == build.LICENSE_FILE.read_bytes()


def test_a_missing_license_stops_the_build(tmp_path, monkeypatch):
	monkeypatch.setattr(build, "LICENSE_FILE", tmp_path / "gone" / "LICENSE")
	with pytest.raises(FileNotFoundError):
		build.add_license(tmp_path)
	with pytest.raises(SystemExit):
		build.main()  # (it checks before it starts PyInstaller)


def test_the_license_has_the_mit_text_and_then_the_spt_section():
	text = license_text()
	assert text.startswith('Unless otherwise specified in the "SPT data files" section below, this software is licensed under the MIT')
	mit, spt = text.index("MIT License\n"), text.index("SPT data files\n", 10)
	assert 0 < mit < text.index("Permission is hereby granted") < text.index("THE SOFTWARE IS PROVIDED") < spt  # (MIT first, whole)
	section = text[spt:]
	for needed in (
		"CC BY-NC-SA 4.0", "src/data/database/", "src/schema/server_models.json", "src/schema/vanilla_profile.json", "src/tests/fixtures/",
		"Single Player Tarkov", "Refringing", "https://github.com/sp-tarkov/server-csharp", "modified",
		"https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.txt", "is not associated with the SPT project",
		"UNLESS OTHERWISE SEPARATELY UNDERTAKEN BY THE LICENSOR", "absolute disclaimer and\n     waiver of all liability.",
	):
		assert needed in section, needed


def test_every_path_the_license_names_exists():
	text = license_text()
	paths = [line.strip() for line in text[text.index("\nSPT data files\n"):].splitlines() if line.startswith("  src/")]
	assert len(paths) == 4
	for path in paths:
		assert (ROOT / path).exists(), path
