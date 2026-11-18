"""Project files for a mod that already has quests (`python -m cli project init`), and what a project uses
(`project show`).

A WTT-CommonLib mod keeps each trader's quests in db/CustomQuests/<trader id>/ (Quests/*.json, Locales/<lang>.json,
QuestAssort/*.json), its quest zones in db/CustomQuestZones/ and its items in db/CustomItems/ (see cli/package.py).
A project file names one quests file and one text file, so `init` writes one project per trader folder: its own
files to work on, the other traders' quests and text, the custom items and the mod's trader files as references (so
their names are known), and the zone folder. A trader's base.json in the mod, found by its id, names the trader and
gives its assort (the file beside it called *assort*.json). No Qt.
"""

import os
import re
from pathlib import Path

from core import jsonio
from core import references as R

SKIP = {"bin", "obj", "node_modules", ".git", ".vs", "bundles"}  # (folders with no data files)
MOST_FILES = 400  # the most .json files looked at for trader files
BIGGEST = 5_000_000  # bytes: a bigger .json file isn't opened to see if it is a trader file


def _jsons(folder):
	return sorted(p for p in folder.glob("*.json") if p.is_file()) if folder.is_dir() else []


def _trader_files(mod):
	"""{trader id: (base.json path, its name)} of the trader base files in the mod (outside db/CustomQuests)."""
	found, seen = {}, 0
	for dirpath, dirnames, filenames in os.walk(mod):
		dirnames[:] = sorted(d for d in dirnames if d not in SKIP and not (Path(dirpath) / d).match("db/CustomQuests"))
		for name in sorted(filenames):
			path = Path(dirpath) / name
			if not name.endswith(".json") or path.stat().st_size > BIGGEST:
				continue
			seen += 1
			if seen > MOST_FILES:
				return found
			try:
				data = jsonio.read_json(path)
			except (OSError, ValueError):
				continue
			if R.detect_kind(data) == R.TRADER and isinstance(data.get("_id"), str):
				found.setdefault(data["_id"], (path, data.get("nickname") or data.get("name") or ""))
	return found


def _assort_beside(base):
	"""The assort file beside a trader's base.json: the same name with "base" as "assort" (at-base.json ->
	at-assort.json), if it is a trader assort."""
	candidate = base.with_name(re.sub("base", "assort", base.name, count=1, flags=re.IGNORECASE))
	if candidate == base or not candidate.is_file():
		return None
	try:
		return candidate if R.detect_kind(jsonio.read_json(candidate)) == R.ASSORT else None
	except (OSError, ValueError):
		return None


def _relative(path, folder, mod=None):
	"""path as the project file in folder writes it: relative to folder when the project files are kept in the mod
	(so they move with it), else absolute."""
	path = Path(path).resolve()
	if mod is not None and not folder.is_relative_to(mod):
		return path.as_posix()
	try:
		return Path(os.path.relpath(path, folder)).as_posix()
	except ValueError:  # (on another drive)
		return path.as_posix()


def _label(trader_id, name):
	text = re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_").lower()
	return text or trader_id


def init(mod, out_dir, language="en", game=None, trader_names=None, new_trader=None):
	"""{project file path: (config, notes)} for each trader of a WTT-CommonLib mod, and notes about the mod.
	new_trader (an id) adds a project for a trader the mod has no quests for yet. trader_names(id) names a known
	trader (the game's, say)."""
	mod, out_dir = Path(mod).resolve(), Path(out_dir).resolve()
	quests_root = mod / "db" / "CustomQuests"
	folders = sorted(p for p in quests_root.iterdir() if p.is_dir()) if quests_root.is_dir() else []
	if new_trader and not any(f.name == new_trader for f in folders):
		folders.append(quests_root / new_trader)
	if not folders:
		raise ValueError(
			f"{mod} has no db/CustomQuests/<trader> folders, so it isn't a WTT-CommonLib quest mod yet: give --trader <id> "
			"to start one for a trader."
		)
	traders = _trader_files(mod)
	zones_dir = mod / "db" / "CustomQuestZones"
	items_dir = mod / "db" / "CustomItems"
	mod_notes = []
	if traders:
		mod_notes.append(f"Trader files found: {', '.join(f'{name or tid} ({_relative(path, mod)})' for tid, (path, name) in traders.items())}.")
	projects = {}
	for folder in folders:
		trader_id, notes = folder.name, []
		quests = _jsons(folder / "Quests")
		locales = _jsons(folder / "Locales")
		locks = _jsons(folder / "QuestAssort")
		quest_file = quests[0] if quests else folder / "Quests" / "quests.json"
		if len(quests) > 1:
			notes.append(f"Quests has {len(quests)} files; this project works on {quest_file.name}, and the others are references.")
		locale_file = next((p for p in locales if p.stem == language), None) or (folder / "Locales" / f"{language}.json")
		if not locales or locale_file not in locales:
			notes.append(f"No Locales/{language}.json yet: it is made when quests are written.")
		lock_file = locks[0] if locks else folder / "QuestAssort" / "assort.json"
		config = {"quests": quest_file, "locale": locale_file, "questassort": lock_file, "trader": trader_id}
		base = traders.get(trader_id)
		name = (base[1] if base else "") or (trader_names(trader_id) if trader_names else "")
		if base:
			assort = _assort_beside(base[0])
			if assort is not None:
				config["assort"] = assort
			else:
				notes.append(f"No trader assort was found beside {base[0].name}, so assort unlocks can't be checked: add \"assort\" by hand.")
		if zones_dir.is_dir():
			zone_files = _jsons(zones_dir)
			config["zones"] = zone_files[0] if len(zone_files) == 1 else zones_dir / "new_zones.json"
			config["zone_files"] = [zones_dir]
		else:
			config["zones"] = zones_dir / "new_zones.json"
		refs = [p for p in quests if p != quest_file]
		for other in folders:
			if other != folder:
				refs += _jsons(other / "Quests") + _jsons(other / "Locales")
		if items_dir.is_dir():
			refs.append(items_dir)
		refs += [path for tid, (path, _n) in traders.items()]
		config["references"] = refs
		config["language"] = language
		if game:
			config["game"] = Path(game).resolve().as_posix()
		path = out_dir / f"project.{_label(trader_id, name)}.json"
		written = {}
		for key, value in config.items():
			if isinstance(value, list):
				written[key] = [_relative(v, out_dir, mod) for v in value]
			elif isinstance(value, Path):
				written[key] = _relative(value, out_dir, mod)
			else:
				written[key] = value
		projects[path] = (written, [f"Trader: {name or trader_id}."] + notes)
	return projects, mod_notes
