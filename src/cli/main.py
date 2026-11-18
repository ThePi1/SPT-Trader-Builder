"""The command line: make and check quests, look things up, import the maps and make quest zones, without the window.

Run from the src folder: ``python -m cli <command> ...`` (``python -m cli --help`` lists the commands). Every command
prints JSON. A command that fails prints {"error": ...} and exits with 1. Commands that change files only write
them with --write (otherwise they say what they would do). See cli/README.md.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

from core import lookup
from core import mapdata as M
from core import zones as Z
from core.jsonio import read_json, write_json
from schema import assort as A
from schema import choices, registry, validate
from schema.common import Names
from schema.fields import REWARD_ITEMS
from schema.issues import ERROR

PROJECT_ENV = "TB_PROJECT"


class CommandError(Exception):
	pass


def out(data):
	sys.stdout.write(json.dumps(data, indent=1, ensure_ascii=False) + "\n")


def _workspace(args):
	from cli.workspace import ProjectError, Workspace

	project = args.project or os.environ.get(PROJECT_ENV)
	try:
		return Workspace(project, maps_dir=args.maps)
	except ProjectError as e:
		raise CommandError(str(e)) from e


def _read_spec(path):
	try:
		return json.load(sys.stdin) if path == "-" else read_json(path)
	except (OSError, ValueError) as e:
		raise CommandError(f"Can't read the spec {path}: {e}") from e


# --- looking things up ----------------------------------------------------------------------------------

def cmd_find(args):
	ws = _workspace(args)
	kinds = None
	if args.kind:
		wanted = {k.strip() for k in args.kind.split(",")}
		aliases = {"map": lookup.MAP, "maps": lookup.MAP, "items": lookup.ITEM, "category": lookup.CATEGORY, "composite": lookup.PRESET, "my_composite": lookup.MINE}
		kinds = {aliases.get(k, k) for k in wanted}
		if "item" in wanted:
			kinds |= {lookup.REF_ITEM}
		if "quest" in wanted:
			kinds |= {lookup.REF_QUEST}
		if "trader" in wanted:
			kinds |= {lookup.REF_TRADER}
		bad = kinds - set(lookup.KIND_LABEL)
		if bad:
			raise CommandError(f"Unknown kind {', '.join(sorted(bad))}. Kinds: {', '.join(lookup.KIND_LABEL)}")
	rows = lookup.build_rows(ws.gamedata, quests=ws.quests.data, library=ws.library, references=ws.references)
	found = lookup.search(rows, args.text, kinds=kinds, limit=args.limit)
	out([{"id": r.id, "name": r.name, "kind": r.kind, "detail": r.detail} for r in found])


def _shorthands(kind=None):
	from cli.spec import SHORTHAND_SHARED, SHORTHANDS

	if kind is None:
		return [{"kind": k, "note": v["note"]} for k, v in SHORTHANDS.items()]
	if kind not in SHORTHANDS:
		raise CommandError(f"{kind} isn't a shorthand. Shorthands: {', '.join(SHORTHANDS)}")
	return {"kind": kind, "note": SHORTHANDS[kind]["note"], "keys": {**SHORTHANDS[kind]["keys"], **SHORTHAND_SHARED}}


def cmd_kinds(args):
	ws = _workspace(args)
	if args.group == "shorthand":
		out(_shorthands(args.kind))
		return
	if args.group and args.group not in registry.GROUPS and args.group != "quest":
		raise CommandError(f"The group must be one of: quest, shorthand, {', '.join(registry.GROUPS)}")
	if not args.group:
		found = {group: [{"kind": s.kind, "label": s.label, "common": s.common, "note": s.note} for s in registry.kinds(group)] for group in registry.GROUPS}
		found["shorthand"] = _shorthands()
		out(found)
		return
	if not args.kind and args.group != "quest":
		out([{"kind": s.kind, "label": s.label, "common": s.common, "used_in": list(s.vanilla_timing_use), "note": s.note} for s in registry.kinds(args.group)])
		return
	spec = registry.spec_for(args.group, args.kind or "quest")
	if args.group != "quest" and args.kind not in registry.GROUPS[args.group]:
		raise CommandError(f"{args.kind} isn't a {args.group} kind. Kinds: {', '.join(registry.GROUPS[args.group])}")
	out({
		"kind": spec.kind, "label": spec.label, "note": spec.note, "used_in": list(spec.vanilla_timing_use),
		"fields": [_field_info(f, ws.gamedata) for f in spec.fields],
		"defaults": {k: v for k, v in spec.base.items() if k not in spec.managed},
		"zones": _zone_note(args.group, spec.kind),
	})


def _field_info(field, gamedata):
	info = {"key": field.key, "label": field.label, "kind": field.kind}
	for name in ("default", "ref", "minimum", "maximum", "help"):
		value = getattr(field, name)
		if value not in (None, "", ()):
			info[name] = value
	if field.required:
		info["required"] = True
	if field.advanced:
		info["advanced"] = True
	if field.categories:
		info["categories"] = True
	if field.choices and field.choices not in ("locations", "traders"):
		pairs = choices.resolve(field.choices, gamedata)
		info["choices"] = [v if str(v) == str(l) else {"value": v, "label": l} for v, l in pairs[:80]]
		if field.open:
			info["open"] = True
	elif field.choices == "locations":
		info["choices"] = "a map: its name (Customs) or key (bigmap); see `maps list`"
	if field.fields:
		info["fields"] = [_field_info(f, gamedata) for f in field.fields]
	if field.kind == REWARD_ITEMS:
		info["spec"] = "\"items\": [{\"item\": name or id, \"count\": n, \"foundInRaid\": bool}], or \"composite\": a composite item's name, or \"parts\": raw parts with \"target\""
	return info


def _zone_note(group, kind):
	rule = Z.accepts(group, kind)
	return None if rule is None else {"key": rule[0], "needs": rule[2]}


def cmd_usage(args):
	from cli import usage as U
	from cli.spec import _name_of

	ws = _workspace(args)
	if args.group not in ("task", "subtask", "reward", "quest"):
		raise CommandError("The group must be task, subtask, reward or quest.")
	kind = args.kind or "quest"
	if args.group != "quest" and kind not in registry.GROUPS[args.group]:
		raise CommandError(f"{kind} isn't a {args.group} kind. Kinds: {', '.join(registry.GROUPS[args.group])}")
	pairs = U.items_of(ws.gamedata.vanilla_quests, args.group, kind)
	wheres = [U.parse_where(w) for w in args.where or []]
	pairs = U.keep(pairs, wheres, args.group, kind)
	result = {"group": args.group, "kind": kind, "found": len(pairs), "in": "the base game's quests"}
	if wheres:
		result["where"] = args.where
	if not args.field:
		result["fields"] = U.fields(pairs, args.group, kind)
		pseudo = {name: words for (g, k, name), (_f, words) in U.PSEUDO.items() if (g, k) == (args.group, kind)}
		if pseudo:
			result["worked_out"] = pseudo
		result["note"] = "Give a field (a dotted path like counter.conditions.0.target) for all its values and quests that use them."
		out(result)
		return
	rows, missing, distinct = U.histogram(pairs, args.field, args.group, kind, args.limit)
	names = Names(ws.gamedata)
	for row in rows:
		value = row["value"]
		if isinstance(value, str) and value:
			name = _name_of(value, names, ws)
			if name:
				row["name"] = name
		elif isinstance(value, list) and value and all(isinstance(v, str) for v in value):
			found = [_name_of(v, names, ws) for v in value]
			if any(found):
				row["names"] = [n or v for n, v in zip(found, value)]
	result.update(field=args.field, values=distinct, without=missing, top=rows)
	out(result)


# --- quests ---------------------------------------------------------------------------------------------

def _find_quest(ws, text):
	quests = ws.quests.data
	if text in quests:
		return text
	named = [qid for qid, q in quests.items() if isinstance(q, dict) and q.get("QuestName", "").lower() == text.lower()]
	if len(named) == 1:
		return named[0]
	if named:
		raise CommandError(f"{len(named)} quests are called '{text}': {', '.join(named)}. Use the id.")
	raise CommandError(f"The quests file has no quest '{text}'.")


def cmd_quest_list(args):
	ws = _workspace(args)
	names = Names(ws.gamedata)
	rows = []
	for qid, q in ws.quests.data.items():
		if not isinstance(q, dict):
			continue
		rows.append({
			"id": qid, "name": q.get("QuestName", ""), "title": ws.locale.data.get(f"{qid} name", ""),
			"trader": names.trader(q.get("traderId", "")), "location": names.location(q.get("location", "")),
			"conditions": sum(len(v) for v in (q.get("conditions") or {}).values() if isinstance(v, list)),
			"rewards": sum(len(v) for v in (q.get("rewards") or {}).values() if isinstance(v, list)),
		})
	out(rows)


def cmd_quest_show(args):
	from cli.spec import describe_quest

	ws = _workspace(args)
	try:
		quest_id = _find_quest(ws, args.quest)
		quest, locale, source = ws.quests.data[quest_id], None, "the quests file"
	except CommandError:
		quest_id, quest, locale, source = _other_quest(ws, args.quest)
	shown = quest if args.raw else describe_quest(quest, ws, locale)
	if not args.raw and source != "the quests file":
		shown = {"from": source, **shown}
	if args.out:
		write_json(args.out, shown)  # (UTF-8, as `quest update` reads it: a shell redirect may write another encoding)
		out({"written": str(Path(args.out).resolve()), "id": quest_id})
	else:
		out(shown)


def _other_quest(ws, text):
	"""(id, quest, its text, where it is from) of a base-game or reference quest, by id or name, to read: for looking at
	how a quest like the one being made is put together."""
	found = {}
	for qid, quest in ws.gamedata.vanilla_quests.items():
		found[qid] = (quest, ws.gamedata.locale, "the base game", ws.gamedata.quest_name(qid))
	reference_text = {k: v for k, (v, _f) in ws.references.locale_entries().items()}
	for qid, (quest, name) in ws.references.quest_data().items():
		found.setdefault(qid, (quest, reference_text, f"the reference file {name}", quest.get("QuestName", "")))
	if text in found:
		quest, locale, source, _n = found[text]
		return text, quest, locale, source
	named = [qid for qid, (quest, _l, _s, title) in found.items() if text.lower() in (title.lower(), str(quest.get("QuestName", "")).lower())]
	if len(named) == 1:
		quest, locale, source, _n = found[named[0]]
		return named[0], quest, locale, source
	if named:
		raise CommandError(f"{len(named)} quests are called '{text}': {', '.join(named)}. Use the id.")
	raise CommandError(f"No quest '{text}' in the quests file, the base game or the reference files.")


def _specs(data):
	if isinstance(data, dict) and isinstance(data.get("quests"), list):
		return data["quests"]
	return data if isinstance(data, list) else [data]


def cmd_quest_add(args, replace=False):
	from cli.spec import Resolver, SpecError, apply_quest, build_quest
	from core.ids import new_id

	ws = _workspace(args)
	specs = _specs(_read_spec(args.spec))
	if not all(isinstance(s, dict) for s in specs):
		raise CommandError("A spec file holds a quest spec (an object), a list of them, or {\"quests\": [...]}.")
	if replace:
		missing = [s.get("id") for s in specs if s.get("id") not in ws.quests.data]
		if missing:
			raise CommandError(f"quest update changes quests that are in the quests file; not there: {', '.join(str(m) for m in missing)}")
	ids = [s.get("id") or new_id() for s in specs]
	resolver = Resolver(ws, batch=[(qid, s.get("name", "")) for qid, s in zip(ids, specs)])
	built, problems = [], []
	for qid, spec in zip(ids, specs):
		try:
			built.append(build_quest(spec, ws, resolver, qid))
		except SpecError as e:
			label = spec.get("name") or qid
			problems += [f"{label}: {p}" for p in e.problems]
	if problems:
		out({"error": "The spec has problems; nothing was changed.", "problems": problems})
		return 1
	try:
		for quest, texts, locks in built:
			apply_quest(ws, quest, texts, locks, replace=replace)
	except SpecError as e:
		raise CommandError("; ".join(e.problems)) from e
	result = {"quests": [{"id": q["_id"], "name": q.get("QuestName", "")} for q, _t, _l in built]}
	result["problems"] = _issues(ws, only={q["_id"] for q, _t, _l in built})
	locks = [{"section": s, "offer": o, "quest": q} for _q, _t, ls in built for s, o, q in ls]
	if locks:
		result["locks"] = locks
	result["written"] = ws.save() if args.write else []
	if not args.write:
		result["note"] = "Nothing was written: run it again with --write to save."
		if args.show:
			from schema import locale as L

			result["json"] = {q["_id"]: q for q, _t, _l in built}
			result["locale"] = {k: ws.locale.data[k] for q, _t, _l in built for k, _w in L.keys_for_quest(q, optional=True) if k in ws.locale.data}
	return _finish(result)


def cmd_quest_update(args):
	return cmd_quest_add(args, replace=True)


def cmd_quest_remove(args):
	ws = _workspace(args)
	quest_id = _find_quest(ws, args.quest)
	quest = ws.quests.data[quest_id]
	ws.quests.change("Remove quest", lambda data: data.pop(quest_id))
	removed_text = []
	if args.text:
		from schema import locale as L

		keys = [k for k, _w in L.keys_for_quest(quest, optional=True)]
		removed_text = [k for k in keys if k in ws.locale.data]
		ws.locale.change("Remove text", lambda data: [data.pop(k) for k in removed_text])
	removed_locks = []
	if ws.questassort is not None:
		for section in A.QUEST_LOCKS:
			for offer, qid in list((ws.questassort.data.get(section) or {}).items()):
				if qid == quest_id:
					removed_locks.append({"section": section, "offer": offer})
		ws.questassort.change("Remove locks", lambda data: [data[l["section"]].pop(l["offer"]) for l in removed_locks])
	result = {"removed": quest_id, "text": removed_text, "locks": removed_locks, "written": ws.save() if args.write else []}
	if not args.write:
		result["note"] = "Nothing was written: run it again with --write to save."
	return _finish(result)


# --- checking -------------------------------------------------------------------------------------------

def _issues(ws, only=None):
	"""Every problem in the workspace's files as dicts: {level, file, where, path, message}."""
	zones = ws.zone_index()
	found = []
	names = Names(ws.gamedata, {qid: q.get("QuestName", "") for qid, q in ws.quests.data.items() if isinstance(q, dict)})
	for issue in validate.validate_quests(ws.quests.data, ws.locale.data, ws.gamedata, zones):
		if only is not None and (not issue.path or issue.path[0] not in only):
			continue
		found.append(_issue(issue, "quests", _where(ws, issue.path, names)))
	if only is None:
		if ws.assort is not None:
			found += [_issue(i, "assort") for i in A.validate_assort(ws.assort.data)]
		if ws.questassort is not None:
			known = set(ws.quests.data)
			found += [_issue(i, "questassort") for i in A.validate_questassort(
				ws.questassort.data, ws.assort.data if ws.assort is not None else None, known,
				lambda q: q in known or ws.gamedata.knows_quest(q),
			)]
			if ws.assort is not None:
				found += [_issue(i, "questassort") for i in A.lock_problems(ws.quests.data, ws.questassort.data, ws.assort.data, ws.trader_id or None)]
	elif ws.questassort is not None and ws.assort is not None:
		found += [
			_issue(i, "questassort") for i in A.lock_problems(ws.quests.data, ws.questassort.data, ws.assort.data, ws.trader_id or None)
			if len(i.path) > 1 and (i.path[1] in only or ws.questassort.data.get(i.path[0], {}).get(i.path[1]) in only)
		]
	return found


def _issue(issue, file, where=""):
	entry = {"level": issue.level, "file": file, "path": list(issue.path), "message": issue.message}
	if where:
		entry["where"] = where
	return entry


def _where(ws, path, names):
	"""Words for where in the quests a problem is: the quest's name > the condition or reward > the field."""
	if not path or path[0] not in ws.quests.data:
		return ""
	quest = ws.quests.data[path[0]]
	words = [quest.get("QuestName", path[0]) if isinstance(quest, dict) else str(path[0])]
	node, group = quest, None
	for i, part in enumerate(path[1:], 1):
		try:
			node = node[part]
		except (KeyError, IndexError, TypeError):
			break
		if path[i - 1:i] == ("conditions",) or (i >= 2 and path[i - 2] == "conditions"):
			group = "task"
		if i >= 2 and path[i - 2] == "rewards":
			group = "reward"
		if i >= 2 and path[i - 2] == "counter":
			group = "subtask"
		if isinstance(node, dict) and group and isinstance(part, int):
			spec = registry.spec_of(node, group)
			words.append(spec.summary(node, names) if spec.summary else spec.label)
	return " > ".join(words)


def _all_problems(ws, server=False, spt=None):
	"""(problems, zone files, the server check's report or None) for every file of the project."""
	found = _issues(ws)
	zone_files = []
	index = ws.zone_index()
	for path in ws.zone_file_paths():
		zone_files.append(str(path))
		for problem in index.problems.get(path.name, []):
			found.append({"level": problem.level, "file": path.name, "path": list(problem.path), "message": problem.message})
		for zone in [z for z in index.zones if z.source == path.name]:
			errors, warnings = Z.check_zone(zone, index)
			for level, texts in ((ERROR, errors), ("warning", warnings)):
				for text in texts:
					found.append({"level": level, "file": path.name, "where": f"zone {zone.id} ({zone.location})", "message": text})
	report = None
	if server:
		from cli import servercheck

		quests_path = ws.path("quests")
		if quests_path is None or not quests_path.is_file():
			raise CommandError("--server checks the saved quests file: the project names none, or it hasn't been written yet.")
		runtime = servercheck.find_runtime(ws, spt)
		if runtime is None:
			raise CommandError(
				"--server needs an SPT install's SPT_Runtime folder (with SPTarkov.Server.Core.dll): give --spt, set \"spt\" or "
				"\"game\" in the project file, or set SPT_RUNTIME."
			)
		report = servercheck.run(quests_path, ws.path("locale"), runtime)
		report["runtime"] = str(runtime)
		found += servercheck.problems(report)
	return found, zone_files, report


def cmd_check(args):
	ws = _workspace(args)
	found, zone_files, report = _all_problems(ws, args.server, args.spt)
	index = ws.zone_index()
	summary = {
		"errors": sum(1 for f in found if f["level"] == ERROR), "warnings": sum(1 for f in found if f["level"] != ERROR),
		"maps_imported": index.game_maps, "zone_files": zone_files,
	}
	if report is not None:
		summary["server"] = {k: report[k] for k in ("ok", "quests", "locale_entries", "runtime") if k in report}
	if not index.game_maps:
		summary["note"] = "No maps imported, so zone ids that aren't in a zone file aren't checked: run `maps import`."
	out({"summary": summary, "problems": found[: args.limit] if args.limit else found})
	return 1 if args.strict and summary["errors"] else 0


def cmd_package(args):
	from cli import package as P

	ws = _workspace(args)
	if not ws.quests.data:
		raise CommandError("The project's quests file has no quests to package.")
	found, _zone_files, _report = _all_problems(ws)
	errors = [f for f in found if f["level"] == ERROR]
	files, zones, notes = P.plan(ws, args.out)
	result = {
		"folder": str(Path(args.out).resolve()), "files": [str(p) for p in files], "zones": zones, "notes": notes,
		"errors": len(errors), "warnings": len(found) - len(errors),
	}
	if errors and not args.force:
		result["problems"] = errors[:20]
		result["note"] = "The project has errors (see `check`), so nothing was written: fix them, or add --force."
		out(result)
		return 1
	if args.write:
		for path, data in files.items():
			path.parent.mkdir(parents=True, exist_ok=True)
			write_json(path, data)
		result["written"] = True
	else:
		result["note"] = "Nothing was written: run it again with --write to write these files."
	out(result)
	return 0


# --- maps and zones -------------------------------------------------------------------------------------

def _maps_dir(args):
	return M.maps_dir(args.maps)


def cmd_maps_import(args):
	game = args.game
	if not game:
		ws = _workspace(args)
		game = str(ws.path("game") or "") or None
	if not game:
		raise CommandError("Give the game's folder (the one with EscapeFromTarkov_Data), or set \"game\" in the project file.")
	locations = [M.location_key(l) or l for l in args.only.split(",")] if args.only else None
	progress = (lambda text: sys.stderr.write(text + "\n")) if args.verbose else None
	try:
		summary = M.import_maps(game, _maps_dir(args), locations, progress)
	except (FileNotFoundError, OSError) as e:
		raise CommandError(str(e)) from e
	out({"imported": summary, "folder": str(_maps_dir(args))})


def cmd_maps_verify(args):
	"""Check the imported maps against the game's own quests and achievements: every zone they use should be found, on
	the quest's map and of the kind its condition needs. Run after importing a new game version."""
	from core.gamedata import GameData
	from core.paths import BUNDLED_DATABASE_DIR

	folder = Path(args.database) if args.database else None
	if folder is None:
		from core.settings import Settings

		folder = Settings.load().resolve("database_folder")
	gamedata = GameData(folder, "en", BUNDLED_DATABASE_DIR if folder is None else None)
	index = Z.ZoneIndex(_maps_dir(args))
	if not index.game_maps:
		raise CommandError("No maps are imported: run `maps import` first.")
	quests = gamedata.vanilla_quests
	achievements = gamedata.achievements or []
	as_quests = {}
	for entry in achievements if isinstance(achievements, list) else []:
		conditions = entry.get("conditions") or {}
		as_quests[entry.get("id", "")] = {
			"_id": entry.get("id", ""), "QuestName": entry.get("id", ""), "location": "any",
			"conditions": {"AvailableForFinish": conditions.get("availableForFinish") or [], "AvailableForStart": [], "Fail": conditions.get("fail") or []},
		}
	found = []
	for source, data in (("quest", quests), ("achievement", as_quests)):
		for issue in Z.zone_issues(data, index):
			item = data.get(issue.path[0], {})
			found.append({"level": issue.level, source: item.get("QuestName", issue.path[0]), "message": issue.message})
	uses = sum(_zone_uses(q) for q in list(quests.values()) + list(as_quests.values()))
	out({
		"database": str(folder or BUNDLED_DATABASE_DIR), "maps": index.game_maps, "zone_uses": uses,
		"problems": found, "note": "A few base-game quests name zones the game itself doesn't have; they show up here too.",
	})
	return 1 if args.strict and any(f["level"] == ERROR for f in found) else 0


def _zone_uses(quest):
	count = 0
	for tasks in (quest.get("conditions") or {}).values():
		for task in tasks if isinstance(tasks, list) else []:
			for item, group in [(task, "task")] + [(s, "subtask") for s in (task.get("counter") or {}).get("conditions") or []]:
				rule = Z.accepts(group, item.get("conditionType"))
				if rule:
					value = item.get(rule[0])
					count += len(value) if isinstance(value, list) else (1 if value else 0)
	return count


def cmd_maps_list(args):
	folder = _maps_dir(args)
	rows = []
	from core.gamedata import location_ids

	ids = location_ids()
	for location in M.LOCATIONS:
		row = {"map": location, "id": ids.get(location, ""), "imported": False}
		if location in M.imported(folder):
			m = M.MapData.load(location, folder)
			row.update(imported=True, zones=len(m.zones), areas=len(m.areas), when=m.record.get("imported"), source=m.record.get("source"))
		rows.append(row)
	out(rows)


def _point(text, size=2):
	try:
		values = [float(v) for v in text.split(",")]
	except ValueError as e:
		raise CommandError(f"'{text}' isn't numbers separated by commas") from e
	if len(values) < size:
		raise CommandError(f"'{text}' needs {size} numbers (x,z{',y' if size == 3 else ''})")
	return values


def _index(args, ws=None):
	ws = ws or _workspace(args)
	return ws, ws.zone_index()


def _map_of(args, ws):
	"""The map's key (bigmap) for --map given as a key or a name (Customs)."""
	from cli.spec import Resolver

	try:
		return Resolver(ws).map_key(args.map)
	except ValueError as e:
		raise CommandError(str(e)) from e


def cmd_zones_list(args):
	ws, index = _index(args)
	zones = index.on(_map_of(args, ws)) if args.map else list(index.zones)
	if args.kind:
		zones = [z for z in zones if z.kind == args.kind]
	if args.source:
		zones = [z for z in zones if (z.source == Z.GAME) == (args.source == "game")]
	if args.id:
		zones = [z for z in zones if args.id.lower() in z.id.lower()]
	if args.near:
		x, z = _point(args.near)[:2]
		zones = [zone for zone in zones if ((zone.box.center[0] - x) ** 2 + (zone.box.center[2] - z) ** 2) ** 0.5 <= args.radius]
	out([z.as_dict() for z in zones[: args.limit]])


def cmd_zones_at(args):
	ws, index = _index(args)
	key = _map_of(args, ws)
	x, z = _point(args.point)[:2]
	result = {"map": key, "x": x, "z": z}
	if key in index.game_maps:
		m = index.map(key)
		floors = m.navmesh.floors_at(x, z)
		result["floors"] = floors
		if not floors:
			result["floors_nearby"] = sorted(set(round(h, 2) for h in Z.floors_around(m.navmesh, x, z)))
		result["areas"] = [a["name"] for a in m.areas if a["min"][0] <= x <= a["max"][0] and a["min"][2] <= z <= a["max"][2]]
	else:
		result["note"] = f"{key} hasn't been imported: run `maps import` for floors and the game's zones."
	y = args.y if args.y is not None else (result.get("floors") or [0.0])[0]
	result["inside"] = [zone.as_dict() for zone in index.on(key) if zone.box.contains((x, y + 1.0, z), margin=0.9)]
	result["nearby"] = [dict(zone.as_dict(), distance=d) for d, zone in Z.nearby(index, key, (x, y + 1.0, z), args.radius)][: args.limit]
	out(result)


def _imported(index, key):
	if key not in index.game_maps:
		raise CommandError(f"{key} hasn't been imported: run `maps import` first.")
	return index.map(key)


def _spot(args, index, key):
	"""(x, z) from --at, or from --place (the best match of `zones find` on the map)."""
	if getattr(args, "place", None):
		from core import places as P

		found = P.find(index, args.place, key, limit=1)
		if not found:
			raise CommandError(f"No place called '{args.place}' is known on {key}: try `zones find`.")
		at = found[0]["at"]
		return (at[0], at[-1])
	if not args.at:
		raise CommandError("Give --at x,z or --place <name>.")
	return tuple(_point(args.at)[:2])


def _next_step(found):
	at = found.get("at")
	if not at:
		return None
	return f"zones building --map {found['map']} --at={at[0]},{at[-1]}"


def cmd_zones_find(args):
	from core import places as P

	ws, index = _index(args)
	key = _map_of(args, ws) if args.map else None
	if not index.game_maps:
		raise CommandError("No maps are imported: run `maps import` first.")
	found = P.find(index, args.text, key, args.limit)
	for f in found:
		step = _next_step(f)
		if step:
			f["next"] = step
	result = {"found": found}
	maps = [key] if key else index.game_maps
	if any(index.map(k).objects is None for k in maps):
		result["note"] = "Some maps were imported before objects were indexed, so only their areas and the named places are searched: run `maps import` again."
	if not found:
		result["note"] = "Nothing matches. Try another word (the game often names places in transliterated Russian: `zones areas`), or `zones objects`."
	out(result)


def cmd_zones_building(args):
	from core import buildings as B

	ws, index = _index(args)
	key = _map_of(args, ws)
	m = _imported(index, key)
	x, z = _spot(args, index, key)
	result = B.building_at(m, x, z, args.radius, args.margin)
	if "zone" in result:
		zone = result["zone"]
		result["zone"]["command"] = (
			f"zones make --map {key} --id <id> --kind visit --at={zone['at']} --size {zone['size']} --yaw {zone['yaw']}"
			f"  (or: zones make --map {key} --id <id> --kind visit --at={x},{z} --building)"
		)
	if args.picture:
		from cli.render import render
		from core import geometry as G

		shown = list(index.on(key))
		center, radius = (x, z), args.radius / 2
		if "outline" in result:
			o, zone = result["outline"], result["zone"]
			size = [float(v) for v in zone["size"].split(",")]
			box = G.Box((o["center"][0], (zone["bottom"] + zone["top"]) / 2, o["center"][1]), size, G.yaw_rotation(zone["yaw"]))
			shown.append(Z.Zone("building", key, M.VISIT, box, "(new)"))
			center, radius = tuple(o["center"]), max(size[0], size[2]) / 2 + 8
		render(args.picture, m.navmesh, shown, center, radius, floor=args.floor, areas=m.areas)
		result["picture"] = str(Path(args.picture).resolve())
	out(result)


def cmd_zones_make(args):
	ws, index = _index(args)
	key = _map_of(args, ws)
	point = _point(args.at)
	x, z = point[0], point[1]
	y = point[2] if len(point) > 2 else args.y
	size = _point(args.size, 3) if args.size else (4.0, 3.0, 4.0)
	yaw = args.yaw if args.yaw is not None else 0.0
	building = None
	if args.building:
		from core import buildings as B

		building = B.building_at(_imported(index, key), x, z, margin=args.margin)
		if "zone" not in building:
			raise CommandError("No building outline was found here: " + " ".join(building.get("notes", [])))
		bx, bz, by = (float(v) for v in building["zone"]["at"].split(","))
		x, z, y = bx, bz, by if y is None else y
		size = _point(args.size, 3) if args.size else [float(v) for v in building["zone"]["size"].split(",")]
		yaw = args.yaw if args.yaw is not None else building["zone"]["yaw"]
	try:
		record, zone, notes = Z.make_zone(index, args.id, key, args.kind, x, z, y, size, yaw, args.name)
	except ValueError as e:
		raise CommandError(str(e)) from e
	index.add([zone])
	errors, warnings = Z.check_zone(zone, index)
	result = {"zone": record, "notes": notes, "errors": errors, "warnings": warnings}
	if building is not None:
		result["building"] = {k: building[k] for k in ("outline", "storeys") if k in building}
		result["notes"] = notes + [n for n in building.get("notes", []) if "below the ground" in n]
	if args.picture:
		from cli.render import render

		m = index.map(zone.location)
		standing = zone.box.center[1] - zone.box.size[1] / 2 + Z.SINK  # (the floor it stands on)
		radius = args.radius if not args.building else max(args.radius, max(zone.box.size[0], zone.box.size[2]) / 2 + 8)
		render(args.picture, m.navmesh, index.on(zone.location), (x, z), radius, highlight=(zone.id,), areas=m.areas, floor=standing if args.one_floor else None)
		result["picture"] = str(Path(args.picture).resolve())
	if args.write:
		path = Path(args.file) if args.file else ws.path("zones")
		if path is None:
			raise CommandError("Say which zone file to write to: --file, or \"zones\" in the project file.")
		if errors and not args.force:
			raise CommandError("The zone has errors, so it wasn't written (add --force to write it anyway): " + "; ".join(errors))
		try:
			Z.add_to_zone_file(path, record, replace=args.replace)
		except ValueError as e:
			raise CommandError(str(e)) from e
		result["written"] = str(path)
	else:
		result["note"] = "Nothing was written: add --write to add it to the project's zone file (or --file)."
	out(result)


def cmd_zones_check(args):
	ws, index = _index(args)
	files = [Path(f) for f in args.files] if args.files else ws.zone_file_paths()
	if not files:
		raise CommandError("No zone files: give some, or set \"zones\" / \"zone_files\" in the project file.")
	results = []
	for path in files:
		if path.name not in {Path(p).name for p in ws.zone_file_paths()}:
			index.add_file(path)
		for problem in index.problems.get(path.name, []):
			results.append({"file": path.name, "level": problem.level, "where": list(problem.path), "message": problem.message})
		for zone in [z for z in index.zones if z.source == path.name]:
			errors, warnings = Z.check_zone(zone, index)
			if errors or warnings or args.all or args.rooms:
				entry = {"file": path.name, "zone": zone.id, "map": zone.location, "errors": errors, "warnings": warnings}
				if args.rooms:
					entry["covers"] = _covers(index, zone)
				results.append(entry)
	out({"maps_imported": index.game_maps, "results": results})


def _covers(index, zone):
	"""The rooms (named objects) inside a zone, and the floor heights it spans, for `zones check --rooms`."""
	from core import buildings as B

	if zone.location not in index.game_maps:
		return {"note": f"{zone.location} isn't imported."}
	m = index.map(zone.location)
	rooms = B.rooms_covered(m.objects, zone.box)
	_hits, _total, heights = m.navmesh.floor_in_box(zone.box)
	smallest = min(B.MIN_STOREY, zone.box.size[0] * zone.box.size[2] * 0.3)  # (a small zone's floor is all one storey)
	covers = {"floors": [s["height"] for s in B.storeys_of(heights, 0.25, smallest)]}
	if rooms is None:
		covers["note"] = "The map was imported before objects were indexed: run `maps import` again for its rooms."
	else:
		covers["storeys_named"] = sorted({r["floor"] for r in rooms if r["floor"] is not None})
		covers["rooms"] = [r["name"] for r in rooms][:60]
	return covers


def cmd_zones_render(args):
	ws, index = _index(args)
	key = _map_of(args, ws)
	if key not in index.game_maps:
		raise CommandError(f"{key} hasn't been imported: run `maps import` first.")
	from cli.render import render

	m = index.map(key)
	if args.at:
		x, z = _point(args.at)[:2]
	elif args.zone:
		found = [zone for zone in index.on(key) if zone.id == args.zone]
		if not found:
			raise CommandError(f"No zone '{args.zone}' on {key}.")
		x, z = found[0].box.center[0], found[0].box.center[2]
	else:
		(x0, _y0, z0), (x1, _y1, z1) = m.navmesh.bounds()
		x, z = (x0 + x1) / 2, (z0 + z1) / 2
	highlight = tuple(args.highlight.split(",")) if args.highlight else ((args.zone,) if args.zone else ())
	path = render(args.out, m.navmesh, index.on(key), (x, z), args.radius, args.size, args.floor, highlight, not args.no_labels, m.areas)
	out({"picture": str(Path(path).resolve()), "center": [x, z], "radius": args.radius})


def cmd_areas(args):
	ws, index = _index(args)
	key = _map_of(args, ws)
	if key not in index.game_maps:
		raise CommandError(f"{key} hasn't been imported: run `maps import` first.")
	areas = index.map(key).areas
	if args.text:
		areas = [a for a in areas if args.text.lower() in a["name"].lower()]
	out([dict(a, center=[round((a["min"][i] + a["max"][i]) / 2, 1) for i in range(3)]) for a in areas])


def cmd_objects(args):
	ws, index = _index(args)
	key = _map_of(args, ws)
	if not args.live and key in index.game_maps and index.map(key).objects is not None:
		out(index.map(key).objects.search(args.text, args.limit))
		return
	game = args.game or str(ws.path("game") or "") or (index.map(key).record.get("source") if key in index.game_maps else None)
	if not game:
		raise CommandError("Give --game (the game's folder) or import the map first.")
	out(M.find_objects(game, key, args.text, args.limit))


# --- the parser -----------------------------------------------------------------------------------------

class _Parser(argparse.ArgumentParser):
	"""argparse, taking coordinates that start with a minus (--at -60,-20) as values rather than as unknown options."""

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._negative_number_matcher = re.compile(r"^-\d+$|^-\d*\.\d+$|^-?\d*\.?\d+(,-?\d*\.?\d+)+$")


def parser():
	p = _Parser(prog="python -m cli", description="Make and check SPT quests and quest zones. Prints JSON.")
	p.add_argument("--project", help=f"the project file (JSON) naming the files to work on; default: ${PROJECT_ENV}")
	p.add_argument("--maps", help="the folder of imported maps (default: data/maps)")
	sub = p.add_subparsers(dest="command", required=True)

	c = sub.add_parser("find", help="search items, traders, quests, maps, categories, composite items by name or id")
	c.add_argument("text")
	c.add_argument("--kind", help="comma-separated: item, category, trader, quest, map, achievement, customization, composite, my_composite")
	c.add_argument("--limit", type=int, default=20)
	c.set_defaults(run=cmd_find)

	c = sub.add_parser("kinds", help="the condition / reward kinds and spec shorthands, or the fields of one kind")
	c.add_argument("group", nargs="?", help="task, subtask, reward, quest or shorthand")
	c.add_argument("kind", nargs="?")
	c.set_defaults(run=cmd_kinds)

	c = sub.add_parser("usage", help="how the base game's quests fill in a kind's fields, with quests that use each value")
	c.add_argument("group", help="task, subtask, reward or quest")
	c.add_argument("kind", nargs="?", help="the condition or reward kind (none for quest)")
	c.add_argument("field", nargs="?", help="a field, or dotted path (counter.conditions.0.target); none for a summary of every field")
	c.add_argument("--where", action="append", help="only items with path=value (value as JSON: 5, true, \"Survived\"), or with path at all; repeatable")
	c.add_argument("--limit", type=int, default=15)
	c.set_defaults(run=cmd_usage)

	q = sub.add_parser("quest", help="list, show, add, update or remove quests").add_subparsers(dest="action", required=True)
	c = q.add_parser("list")
	c.set_defaults(run=cmd_quest_list)
	c = q.add_parser("show", help="a quest as a spec (or --raw JSON); also base-game and reference quests, to read")
	c.add_argument("quest", help="its id or name")
	c.add_argument("--raw", action="store_true")
	c.add_argument("--out", help="write it to this file (UTF-8) instead of printing it")
	c.set_defaults(run=cmd_quest_show)
	for name, run, text in (("add", cmd_quest_add, "add quests from a spec file (- reads stdin)"), ("update", cmd_quest_update, "replace quests (by the spec's id) from a spec file")):
		c = q.add_parser(name, help=text)
		c.add_argument("spec")
		c.add_argument("--write", action="store_true", help="save the files (otherwise nothing is written)")
		c.add_argument("--show", action="store_true", help="also print the quest JSON that would be written")
		c.set_defaults(run=run)
	c = q.add_parser("remove")
	c.add_argument("quest")
	c.add_argument("--text", action="store_true", help="also remove its text from the locale")
	c.add_argument("--write", action="store_true")
	c.set_defaults(run=cmd_quest_remove)

	c = sub.add_parser("check", help="every problem in the project's files (quests, text, assort, locks, zones)")
	c.add_argument("--limit", type=int, default=0)
	c.add_argument("--strict", action="store_true", help="exit with 1 when there are errors")
	c.add_argument("--server", action="store_true", help="also load the saved quests and text with the SPT server's own code (needs dotnet)")
	c.add_argument("--spt", help="for --server: the SPT install's SPT_Runtime folder, or the folder holding it")
	c.set_defaults(run=cmd_check)

	c = sub.add_parser("package", help="write the project's quests, text, locks and zones as a mod's db folder for WTT-CommonLib")
	c.add_argument("--out", required=True, help="the mod's folder (db/CustomQuests and db/CustomQuestZones go in it)")
	c.add_argument("--write", action="store_true")
	c.add_argument("--force", action="store_true", help="write it even when the project has errors")
	c.set_defaults(run=cmd_package)

	m = sub.add_parser("maps", help="import the game's maps, or list them").add_subparsers(dest="action", required=True)
	c = m.add_parser("import", help="read the game's maps (zones, floors, areas) into data/maps")
	c.add_argument("game", nargs="?", help="the game's folder (default: \"game\" in the project file)")
	c.add_argument("--only", help="comma-separated maps")
	c.add_argument("--verbose", action="store_true")
	c.set_defaults(run=cmd_maps_import)
	c = m.add_parser("list")
	c.set_defaults(run=cmd_maps_list)
	c = m.add_parser("verify", help="check the imported maps against the game's own quests and achievements")
	c.add_argument("database", nargs="?", help="an SPT_Data/database folder (default: the one in Settings, else the bundled copy)")
	c.add_argument("--strict", action="store_true", help="exit with 1 when there are errors")
	c.set_defaults(run=cmd_maps_verify)

	z = sub.add_parser("zones", help="list, look up, make, check and draw quest zones").add_subparsers(dest="action", required=True)
	c = z.add_parser("list")
	c.add_argument("--map")
	c.add_argument("--kind", choices=M.ZONE_KINDS)
	c.add_argument("--source", choices=("game", "custom"))
	c.add_argument("--id", help="part of the id")
	c.add_argument("--near", help="x,z")
	c.add_argument("--radius", type=float, default=50.0)
	c.add_argument("--limit", type=int, default=200)
	c.set_defaults(run=cmd_zones_list)
	c = z.add_parser("at", help="the floors, areas and zones at a spot")
	c.add_argument("--map", required=True)
	c.add_argument("point", help="x,z")
	c.add_argument("--y", type=float, help="the height to look at (default: the lowest floor)")
	c.add_argument("--radius", type=float, default=20.0)
	c.add_argument("--limit", type=int, default=15)
	c.set_defaults(run=cmd_zones_at)
	c = z.add_parser("find", help="places by the name players use (White Knight, dorms, gas station): named places, areas, objects")
	c.add_argument("text")
	c.add_argument("--map", help="only this map (default: every imported map)")
	c.add_argument("--limit", type=int, default=10)
	c.set_defaults(run=cmd_zones_find)
	c = z.add_parser("building", help="the building at a spot: outline, angle, storeys, rooms, and a zone covering it")
	c.add_argument("--map", required=True)
	c.add_argument("--at", help="x,z of a spot in or near the building")
	c.add_argument("--place", help="instead of --at: a place's name (as `zones find` takes it)")
	c.add_argument("--radius", type=float, default=40.0, help="how far around the spot to look (metres)")
	c.add_argument("--margin", type=float, default=1.0, help="metres the suggested zone reaches past the outline")
	c.add_argument("--picture", help="also draw it to this PNG (the suggested zone in green)")
	c.add_argument("--floor", type=float, help="for --picture: only the floor near this height")
	c.set_defaults(run=cmd_zones_building)
	c = z.add_parser("make", help="a new custom zone standing on the floor, checked")
	c.add_argument("--map", required=True)
	c.add_argument("--id", required=True)
	c.add_argument("--kind", required=True, choices=tuple(Z.CUSTOM_TYPE))
	c.add_argument("--at", required=True, help="x,z or x,z,y (y picks the floor nearest that height)")
	c.add_argument("--y", type=float)
	c.add_argument("--size", help="width,height,depth in metres (default 4,3,4)")
	c.add_argument("--yaw", type=float, help="turn in degrees, clockwise from north (default 0)")
	c.add_argument("--building", action="store_true", help="cover the whole building at --at: its outline, angle and every storey (see `zones building`)")
	c.add_argument("--margin", type=float, default=1.0, help="for --building: metres past the outline")
	c.add_argument("--name", help="ZoneName (default: the id)")
	c.add_argument("--picture", help="also draw it to this PNG")
	c.add_argument("--radius", type=float, default=25.0, help="for --picture")
	c.add_argument("--one-floor", action="store_true", help="for --picture: only the floor near the zone")
	c.add_argument("--write", action="store_true")
	c.add_argument("--file", help="the zone file to add it to (default: \"zones\" in the project file)")
	c.add_argument("--replace", action="store_true", help="replace a zone with the same id on the same map")
	c.add_argument("--force", action="store_true", help="write it even with errors")
	c.set_defaults(run=cmd_zones_make)
	c = z.add_parser("check", help="check custom zone files")
	c.add_argument("files", nargs="*")
	c.add_argument("--all", action="store_true", help="list zones without problems too")
	c.add_argument("--rooms", action="store_true", help="also list the rooms (named objects) and floors inside each zone")
	c.set_defaults(run=cmd_zones_check)
	c = z.add_parser("render", help="draw part of a map to a PNG")
	c.add_argument("--map", required=True)
	c.add_argument("--out", required=True)
	c.add_argument("--at", help="x,z of the middle (default: the middle of the map)")
	c.add_argument("--zone", help="centre on this zone")
	c.add_argument("--radius", type=float, default=40.0)
	c.add_argument("--size", type=int, default=900)
	c.add_argument("--floor", type=float, help="only show the floor within 2.5 m of this height")
	c.add_argument("--highlight", help="comma-separated zone ids to draw thicker")
	c.add_argument("--no-labels", action="store_true")
	c.set_defaults(run=cmd_zones_render)
	c = z.add_parser("areas", help="the map's areas (its places: dorms, gas station, ...)")
	c.add_argument("--map", required=True)
	c.add_argument("text", nargs="?")
	c.set_defaults(run=cmd_areas)
	c = z.add_parser("objects", help="find objects by name (in the imported map's object index; --live reads the game's files)")
	c.add_argument("--map", required=True)
	c.add_argument("text")
	c.add_argument("--game")
	c.add_argument("--live", action="store_true", help="read the game's files instead of the index (slow)")
	c.add_argument("--limit", type=int, default=50)
	c.set_defaults(run=cmd_objects)
	return p


def _finish(result):
	out(result)
	return 0


def main(argv=None):
	if hasattr(sys.stdout, "reconfigure"):
		sys.stdout.reconfigure(encoding="utf-8")
	args = parser().parse_args(argv)
	try:
		code = args.run(args)
	except CommandError as e:
		out({"error": str(e)})
		return 1
	return code or 0
