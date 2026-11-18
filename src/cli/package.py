"""The project's quests as a mod's data folder for WTT-CommonLib (`python -m cli package`).

WTT-CommonLib's CustomQuestService reads, next to the mod's DLL:

    db/CustomQuests/<trader id>/Quests/*.json        the quests ({quest id: quest}), per trader
    db/CustomQuests/<trader id>/Locales/<lang>.json  their text
    db/CustomQuests/<trader id>/QuestAssort/*.json   the trader offers they unlock ({started, success, fail})
    db/CustomQuestZones/*.json                       custom quest zones (CustomQuestZoneService)

(the layout rtt2-traders uses, and the folder names in WTT-ServerCommonLib). The mod's own code calls
CreateCustomQuests and CreateCustomQuestZones. No Qt.
"""

from pathlib import Path

from core import zones as Z
from schema import assort as A
from schema import locale as L

EMPTY_LOCKS = {"started": {}, "success": {}, "fail": {}}


def zone_ids(quest):
	"""The zone ids a quest's conditions point at."""
	found = []
	for tasks in (quest.get("conditions") or {}).values():
		for task in tasks if isinstance(tasks, list) else []:
			if not isinstance(task, dict):
				continue
			for item, group in [(task, "task")] + [(s, "subtask") for s in (task.get("counter") or {}).get("conditions") or [] if isinstance(s, dict)]:
				rule = Z.accepts(group, item.get("conditionType"))
				if rule:
					value = item.get(rule[0])
					found += [v for v in (value if isinstance(value, list) else [value]) if isinstance(v, str) and v]
	return list(dict.fromkeys(found))


def language(ws):
	stem = ws.path("locale").stem if ws.path("locale") is not None else ""
	return stem if stem in (ws.gamedata.languages or {}) else ws.settings.language


def plan(ws, out_dir):
	"""({path: data} of the files to write, [zone ids packaged], [notes]) for the project's quests."""
	out_dir = Path(out_dir)
	quests = {qid: q for qid, q in ws.quests.data.items() if isinstance(q, dict)}
	stem = ws.path("quests").stem if ws.path("quests") is not None else "quests"
	lang = language(ws)
	files, notes = {}, []
	by_trader = {}
	for qid, quest in quests.items():
		by_trader.setdefault(quest.get("traderId") or "no_trader", {})[qid] = quest
	locks = ws.questassort.data if ws.questassort is not None else None
	for trader, mine in by_trader.items():
		base = out_dir / "db" / "CustomQuests" / trader
		files[base / "Quests" / f"{stem}.json"] = mine
		text = {}
		for quest in mine.values():
			for key, _what in L.keys_for_quest(quest, optional=True):
				if key in ws.locale.data:
					text[key] = ws.locale.data[key]
		files[base / "Locales" / f"{lang}.json"] = text
		trader_locks = {section: {} for section in A.QUEST_LOCKS}
		if locks is not None and (not ws.trader_id or ws.trader_id == trader):
			for section in A.QUEST_LOCKS:
				trader_locks[section] = {offer: q for offer, q in (locks.get(section) or {}).items() if q in mine}
		files[base / "QuestAssort" / f"{stem}.json"] = trader_locks
	index = ws.zone_index()
	records, packaged = [], []
	for qid, quest in quests.items():
		for zone_id in zone_ids(quest):
			found = index.by_id(zone_id)
			custom = [z for z in found if z.source != Z.GAME and z.record is not None]
			if custom:
				for zone in custom:
					if zone.record not in records:
						records.append(zone.record)
				packaged.append(zone_id)
			elif not found:
				notes.append(f"{quest.get('QuestName', qid)} uses the zone '{zone_id}', which no zone file or imported map has: it isn't packaged.")
	if records:
		files[out_dir / "db" / "CustomQuestZones" / f"{stem}.json"] = records
	if any(r.get("type") == "AssortmentUnlock" for q in quests.values() for rs in (q.get("rewards") or {}).values() for r in rs or []):
		notes.append(
			"Some quests unlock trader offers. The quest locks are in QuestAssort, but the offers themselves (the project's assort "
			"file) aren't packaged: a base-game trader's new offers must be added by the mod (WTT's assort tools or its own code)."
		)
	notes.append(
		"The mod's server code loads these with WTT-CommonLib: CustomQuestService.CreateCustomQuests(assembly) and "
		"CustomQuestZoneService.CreateCustomQuestZones(assembly), which read the db folder next to the mod's DLL."
	)
	return files, list(dict.fromkeys(packaged)), notes
