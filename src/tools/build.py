"""Build the Windows program:  python tools/build.py   (needs: pip install pyinstaller)

Makes dist/SPTTraderBuilder/ with the program, a lib/ folder (Python and Qt; PyInstaller calls it _internal
unless told otherwise), a data/ folder next to it (settings.ini, the bundled game data, your saved items) and
LICENSE (the MIT License and the notice for the SPT files; it must go with the program).
Run tools/bundle_database.py first to include the game data.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = "SPTTraderBuilder"
CONTENTS_DIR = "lib"  # the folder for everything but the .exe and our own data/ (PyInstaller's default is _internal)
LICENSE_FILE = ROOT.parent / "LICENSE"  # in the root of the repository


def add_license(out):
	"""Copy LICENSE next to the built program. Raises FileNotFoundError if there is no LICENSE."""
	shutil.copyfile(LICENSE_FILE, Path(out) / LICENSE_FILE.name)


def main():
	if not LICENSE_FILE.is_file():
		sys.exit(f"{LICENSE_FILE} is missing: the build has to include it.")
	subprocess.check_call([
		sys.executable, "-m", "PyInstaller", "--noconfirm", "--windowed", "--name", NAME,
		"--contents-directory", CONTENTS_DIR,
		"--paths", str(ROOT), "--distpath", str(ROOT / "dist"), "--workpath", str(ROOT / "build"),
		"--specpath", str(ROOT / "build"), "--icon", str(ROOT / "data" / "icon.ico"),
		# the schema's two JSON files are read next to the schema code
		"--add-data", f"{ROOT / 'schema' / 'server_models.json'}{os.pathsep}schema",
		"--add-data", f"{ROOT / 'schema' / 'vanilla_profile.json'}{os.pathsep}schema",
		# and the places found by name next to the maps code
		"--add-data", f"{ROOT / 'maps' / 'places.json'}{os.pathsep}maps",
		str(ROOT / "main.py"),
	])
	out = ROOT / "dist" / NAME
	data = out / "data"
	if data.exists():
		shutil.rmtree(data)
	shutil.copytree(ROOT / "data", data, ignore=_left_out)
	add_license(out)
	print(f"Built {out}")


LEFT_OUT = {"my_items.json", "references.json", "last_files.json"}  # yours, in data/
LEFT_OUT_FOLDERS = {"maps"}  # data/maps: the maps imported from your game (the game's own data: never shared)


def _left_out(folder, names):
	"""What of data/ isn't copied into the program's data/ folder."""
	top = Path(folder) == ROOT / "data"
	return [n for n in names if top and (n in LEFT_OUT or n in LEFT_OUT_FOLDERS)]


if __name__ == "__main__":
	main()
