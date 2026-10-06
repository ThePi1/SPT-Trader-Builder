"""Importing: adding the contents of other files to what the program already holds.

Nothing here changes its inputs. Each ``merge_*`` returns the merged data and a ``Counts``, so the
import window can show what would happen before anything is applied.

When something in an imported file clashes with what is already there (same quest id, same offer id,
same locale key with other text) the *policy* says what to do:
  KEEP     keep what is there, skip the imported one
  REPLACE  use the imported one
  BOTH     keep both: the imported quest or offer gets new ids (its text and locks follow it)
Items that are identical to what is already there are not clashes; they are skipped ("same").
"""

import copy
import re
from dataclasses import dataclass, field
from pathlib import Path

from core import jsonio
from schema import assort as assort_schema
from schema import explorer
from schema import locale as locale_schema
from schema.copying import copy_quest, with_new_ids

KEEP, REPLACE, BOTH = "keep", "replace", "both"
POLICIES = (KEEP, REPLACE, BOTH)

QUESTS, LOCALE, ASSORT, LOCKS = "quests", "locale", "assort", "questassort"  # the kinds (explorer.detect_kind)
KIND_LABEL = {QUESTS: "Quests", LOCALE: "Locale", ASSORT: "Trader assort", LOCKS: "Quest assort"}
ORDER = (QUESTS, ASSORT, LOCKS, LOCALE)  # the order files are merged in (the locale last: it needs the quests)


@dataclass
class Counts:
	new: int = 0  # added
	conflicts: int = 0  # clash with what is there (dealt with by the policy)
	same: int = 0  # already there, identical

	def __iadd__(self, other):
		self.new += other.new
		self.conflicts += other.conflicts
		self.same += other.same
		return self


# --- quests ---------------------------------------------------------------------------------

def merge_quests(current, incoming, policy=KEEP):
	"""(merged quests, Counts, id_map, touched). id_map is {old id: new id} for the quests (and their tasks)
	that were kept as copies (policy BOTH); touched lists the ids of the quests that now hold imported data."""
	merged = dict(current)
	counts, id_map, touched = Counts(), {}, []
	for quest_id, quest in incoming.items():
		if not isinstance(quest, dict):
			continue
		if quest_id not in current:
			merged[quest_id] = copy.deepcopy(quest)
			counts.new += 1
			touched.append(quest_id)
		elif current[quest_id] == quest:
			counts.same += 1
		else:
			counts.conflicts += 1
			if policy == REPLACE:
				merged[quest_id] = copy.deepcopy(quest)
				touched.append(quest_id)
			elif policy == BOTH:
				clone, ids = copy_quest(quest)
				clone["QuestName"] = f"{clone.get('QuestName', 'Quest')} (imported)"
				merged[clone["_id"]] = clone
				id_map.update(ids)
				touched.append(clone["_id"])
	return merged, counts, id_map, touched


# --- locale ---------------------------------------------------------------------------------

def _renamed(key, id_map):
	"""The locale key for a quest that was imported as a copy (its text keys follow the new ids)."""
	parts = locale_schema.split_quest_key(key)
	if parts and parts[0] in id_map:
		return locale_schema.quest_key(id_map[parts[0]], parts[1])
	return id_map.get(key, key)


def merge_locale(current, incoming, policy=KEEP, id_map=None, only_keys=None):
	"""(merged locale, Counts). only_keys limits the imported entries to those keys (None: all of them).
	id_map renames the keys of quests imported as copies. Blank imported text is skipped. A clash is
	decided by the policy, except that BOTH keeps the text that is already there."""
	merged = dict(current)
	counts = Counts()
	id_map = id_map or {}
	for key, text in incoming.items():
		if not isinstance(text, str) or not text.strip():
			continue
		if only_keys is not None and key not in only_keys:
			continue
		key = _renamed(key, id_map)
		there = merged.get(key)
		if not there:
			merged[key] = text
			counts.new += 1
		elif there == text:
			counts.same += 1
		else:
			counts.conflicts += 1
			if policy == REPLACE:
				merged[key] = text
	return merged, counts


# --- trader assort --------------------------------------------------------------------------

def _offer_snapshot(assort, offer_id):
	return (
		assort_schema.offer_parts(assort, offer_id),
		assort.get("barter_scheme", {}).get(offer_id),
		assort.get("loyal_level_items", {}).get(offer_id),
	)


def merge_assort(current, incoming, policy=KEEP):
	"""(merged assort, Counts, offer_map, touched). offer_map is {old offer id: new} for offers kept as copies."""
	merged = copy.deepcopy(current)
	for key, empty in assort_schema.empty_assort().items():
		merged.setdefault(key, copy.deepcopy(empty))
	counts, offer_map, touched = Counts(), {}, []
	there = set(assort_schema.offer_ids(current))
	for offer_id in assort_schema.offer_ids(incoming):
		parts, barter, level = _offer_snapshot(incoming, offer_id)
		if offer_id in there and _offer_snapshot(current, offer_id) == (parts, barter, level):
			counts.same += 1
			continue
		if offer_id in there:
			counts.conflicts += 1
			if policy == KEEP:
				continue
			if policy == REPLACE:
				assort_schema.remove_offer(merged, offer_id)
				new_parts = copy.deepcopy(parts)
			else:
				new_parts = with_new_ids(parts)
				offer_map[offer_id] = new_parts[0]["_id"]
		else:
			counts.new += 1
			new_parts = copy.deepcopy(parts)
		new_id = new_parts[0]["_id"]
		merged["items"].extend(new_parts)
		merged["barter_scheme"][new_id] = copy.deepcopy(barter if barter is not None else [[]])
		merged["loyal_level_items"][new_id] = level if level is not None else 1
		touched.append(new_id)
	return merged, counts, offer_map, touched


# --- quest locks ----------------------------------------------------------------------------

def merge_locks(current, incoming, policy=KEEP, offer_map=None, quest_map=None):
	"""(merged quest locks, Counts). offer_map / quest_map point locks at offers and quests that were imported as
	copies. A clash (the offer is locked to another quest) is decided by the policy; BOTH keeps what is there."""
	merged = copy.deepcopy(current)
	for status in assort_schema.QUEST_LOCKS:
		merged.setdefault(status, {})
	counts = Counts()
	offer_map, quest_map = offer_map or {}, quest_map or {}
	for status in assort_schema.QUEST_LOCKS:
		for offer_id, quest_id in (incoming.get(status) or {}).items():
			offer_id, quest_id = offer_map.get(offer_id, offer_id), quest_map.get(quest_id, quest_id)
			there = merged[status].get(offer_id)
			if there is None:
				merged[status][offer_id] = quest_id
				counts.new += 1
			elif there == quest_id:
				counts.same += 1
			else:
				counts.conflicts += 1
				if policy == REPLACE:
					merged[status][offer_id] = quest_id
	return merged, counts


# --- reading files and planning an import ---------------------------------------------------

@dataclass
class Item:
	"""One file to import: its name, what kind of file it is (None: not recognised), and its data."""

	name: str
	kind: str = None
	data: object = None
	path: Path = None
	error: str = ""
	include: bool = True


_ID = re.compile(r"[0-9a-fA-F]{24}")


def load_items(paths, limit=200):
	"""Read the files (and the .json files inside folders) as Items; one that can't be read has an error."""
	files = []
	for path in map(Path, paths):
		if path.is_dir():
			files.extend(sorted(path.rglob("*.json")))
		else:
			files.append(path)
	items = []
	for path in files[:limit]:
		try:
			data = jsonio.read_json(path)
		except (OSError, ValueError) as e:
			items.append(Item(path.name, path=path, error=f"Couldn't be read: {e}", include=False))
			continue
		kind = explorer.detect_kind(data)
		items.append(Item(path.name, kind, data, path, "" if kind else "Not a quest, locale, trader assort or quest assort file.", include=bool(kind)))
	return items


def guess_trader(path, known=()):
	"""The id of the trader a file probably belongs to, from where it is: the base.json next to it, or a folder named with a
	trader's id (traders/<id>/assort.json, a mod's <id> folder). One of the known ids is preferred. '' if there is no clue."""
	path = Path(path)
	try:
		base = jsonio.read_json(path.parent / "base.json") if (path.parent / "base.json").is_file() else None
	except (OSError, ValueError):
		base = None
	if isinstance(base, dict) and isinstance(base.get("_id"), str) and _ID.fullmatch(base["_id"]):
		return base["_id"]
	ids = [folder.name for folder in list(path.parents)[:4] if _ID.fullmatch(folder.name)]
	return next((i for i in ids if i in known), ids[0] if ids else "")


@dataclass
class Plan:
	"""What an import would do: the merged data per kind, and a Counts per item."""

	data: dict = field(default_factory=dict)  # kind -> merged data (only kinds that change)
	counts: list = field(default_factory=list)  # per item, in order: Counts or None (left out)
	sources: dict = field(default_factory=dict)  # quest id -> file name, for the quests that were imported
	changed: set = field(default_factory=set)
	total: dict = field(default_factory=dict)  # kind -> Counts over all its files

	def adds(self, kind):
		return self.total.get(kind, Counts()).new


def plan_import(items, workspace, policy=KEEP, everything=False):
	"""Work out an import. workspace: {kind: data} of what is open now. items: [Item]; the ones with include False
	or no kind are left out. everything=False imports only the locale text that belongs to the quests (the open
	ones and the imported ones; all of it when there are no quests at all)."""
	plan = Plan(counts=[None] * len(items))
	state = {kind: workspace[kind] for kind in ORDER}
	quest_map, offer_map = {}, {}
	imported_quests = {}
	for kind in ORDER:
		for index, item in enumerate(items):
			if item.kind != kind or not item.include or not isinstance(item.data, dict):
				continue
			if kind == QUESTS:
				merged, counts, ids, touched = merge_quests(state[kind], item.data, policy)
				quest_map.update({k: v for k, v in ids.items()})
				imported_quests.update(item.data)
				for quest_id in touched:
					plan.sources[quest_id] = item.name
			elif kind == ASSORT:
				merged, counts, ids, _touched = merge_assort(state[kind], item.data, policy)
				offer_map.update(ids)
			elif kind == LOCKS:
				merged, counts = merge_locks(state[kind], item.data, policy, offer_map, quest_map)
			else:
				allowed = None
				if not everything and (state[QUESTS] or imported_quests):
					allowed = set(locale_schema.key_owners(state[QUESTS])) | set(locale_schema.key_owners(imported_quests))
				merged, counts = merge_locale(state[kind], item.data, policy, quest_map, allowed)
			state[kind] = merged
			plan.counts[index] = counts
			plan.total.setdefault(kind, Counts())
			plan.total[kind] += counts
	plan.changed = {kind for kind in ORDER if state[kind] != workspace[kind]}
	plan.data = {kind: state[kind] for kind in plan.changed}
	return plan
