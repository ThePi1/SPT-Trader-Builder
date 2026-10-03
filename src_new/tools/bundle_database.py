"""Copy the game data the app reads from an SPT database folder into data/database, so the
app can show item and trader names without the user choosing a folder.

    python tools/bundle_database.py "I:\\Games\\SPT-4-0-13-BASE-COPY\\SPT\\SPT_Data\\database" [--languages en,ru]

The source folder is only read. The locations folder is never touched. globals.json is cut down
to the composite items (ItemPresets).
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.gamedata import (  # noqa: E402
	ACHIEVEMENTS, CUSTOMIZATION, EQUIPMENT_PRESETS, GLOBALS, HANDBOOK, HIDEOUT_AREAS, ITEMS, LANGUAGES, QUESTS, locale_file,
)
from core.jsonio import read_json, write_json  # noqa: E402
from core.paths import BUNDLED_DATABASE_DIR  # noqa: E402

PLAIN_FILES = (ITEMS, QUESTS, HANDBOOK, ACHIEVEMENTS, CUSTOMIZATION, EQUIPMENT_PRESETS, HIDEOUT_AREAS, LANGUAGES)


def bundle(source, target, languages):
	source, target = Path(source), Path(target)
	copied = []
	for relative in PLAIN_FILES + tuple(locale_file(lang) for lang in languages):
		src = source / relative
		if not src.is_file():
			print(f"missing, skipped: {relative}")
			continue
		(target / relative).parent.mkdir(parents=True, exist_ok=True)
		shutil.copyfile(src, target / relative)
		copied.append(relative)
	globals_file = source / GLOBALS
	if globals_file.is_file():
		(target / GLOBALS).parent.mkdir(parents=True, exist_ok=True)
		write_json(target / GLOBALS, {"ItemPresets": read_json(globals_file).get("ItemPresets", {})})
		copied.append(GLOBALS)
	for base in sorted((source / "traders").glob("*/base.json")):
		out = target / "traders" / base.parent.name / "base.json"
		out.parent.mkdir(parents=True, exist_ok=True)
		shutil.copyfile(base, out)
		copied.append(str(out.relative_to(target)))
	return copied


def main():
	parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
	parser.add_argument("source", help="the SPT_Data/database folder")
	parser.add_argument("--languages", default="en", help="comma separated language codes to include (default en)")
	parser.add_argument("--target", default=str(BUNDLED_DATABASE_DIR))
	args = parser.parse_args()
	copied = bundle(args.source, args.target, [x.strip() for x in args.languages.split(",") if x.strip()])
	print(f"Copied {len(copied)} files into {args.target}")


if __name__ == "__main__":
	main()
