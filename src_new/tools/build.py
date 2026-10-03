"""Build the Windows program:  python tools/build.py   (needs: pip install pyinstaller)

Makes dist/SPTQuestBuilder/ with the program and a data/ folder next to it (settings.ini, the bundled
game data, your saved items). Run tools/bundle_database.py first to include the game data.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = "SPTQuestBuilder"


def main():
	subprocess.check_call([
		sys.executable, "-m", "PyInstaller", "--noconfirm", "--windowed", "--name", NAME,
		"--paths", str(ROOT), "--distpath", str(ROOT / "dist"), "--workpath", str(ROOT / "build"),
		"--specpath", str(ROOT / "build"),
		# the schema's two JSON files are read next to the schema code
		"--add-data", f"{ROOT / 'schema' / 'server_models.json'}{os.pathsep}schema",
		"--add-data", f"{ROOT / 'schema' / 'vanilla_profile.json'}{os.pathsep}schema",
		str(ROOT / "main.py"),
	])
	out = ROOT / "dist" / NAME
	data = out / "data"
	if data.exists():
		shutil.rmtree(data)
	shutil.copytree(ROOT / "data", data, ignore=shutil.ignore_patterns("my_items.json"))
	print(f"Built {out}")


if __name__ == "__main__":
	main()
