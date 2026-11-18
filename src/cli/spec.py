"""Quest specs: a short way to write a quest in JSON, turned into the quest JSON the game reads (``build``), and a
quest turned back into one (``describe``).

A spec names things the way a person would ("trader": "Prapor", "items": ["Bolts"], "location": "Customs") and
leaves out everything that has its usual value; ids, defaults, the locale keys and the item reward's value are
filled in. The same field names as the quest JSON are used, so anything the schema knows can be set. See
cli/README.md for the format. No Qt.
"""

import copy

from core import lookup
from core.ids import is_id, new_id
from core.mapdata import location_key
from core.gamedata import location_ids
from schema import assort as A
from schema import choices, registry
from schema import locale as L
from schema.common import Names
from schema.copying import with_new_ids
from schema.fields import (
	BODY_EFFECTS, BOOL, CHOICE, GROUPS, IDLIST, INT, JSON, LIST, MULTILINE, NUMBER, OBJECT, REF, REWARD_ITEMS, TEXT, VISIBILITY,
)
from schema.quest import BASE as QUEST_BASE
from schema.quest import QUEST, make_quest
from schema.rewards import item_count

TASK_LISTS = {"start": "AvailableForStart", "finish": "AvailableForFinish", "fail": "Fail"}
REWARD_LISTS = {"success": "Success", "started": "Started", "fail": "Fail"}
LOCK_OF = {"Success": "success", "Started": "started"}  # the quest assort section an unlock reward in this list goes with
MONEY = set(A.MONEY.values())
CURRENCIES = {"roubles": A.MONEY["roubles"], "rub": A.MONEY["roubles"], "dollars": A.MONEY["dollars"], "usd": A.MONEY["dollars"], "euros": A.MONEY["euros"], "eur": A.MONEY["euros"]}
QUEST_KEYS = ("id", "name", "trader", "text", "start", "finish", "fail", "rewards", "extra", "omit", "names")  # (names: what describe tells; ignored)
OTHER_MAPS = ("develop",)  # maps the base game's Location conditions name that aren't raid maps

# Short ways to write the conditions the base game builds the same way every time. Each becomes a CounterCreator.
SHORTHANDS = {
	"Visit": {
		"note": "Go to a place: an Exploration counter with a VisitPlace step, as the base game's \"Locate ...\" tasks.",
		"keys": {"zone": "the visit zone's id (required)", "map": "optional: also require this map (a Location step)"},
	},
	"Kill": {
		"note": "Kill enemies: an Elimination counter with a Kills step, and InZone and Location steps when asked.",
		"keys": {
			"count": "how many (default 1)", "target": "who: Any, Scavs (Savage), Any PMC (AnyPmc), ... (default Any)",
			"zone": "optional: only kills made inside this zone (or list of zones); it must count as inside (visit, botkillzone, ...)",
			"map": "the map (default: the quest's location; \"any\" for none)",
			"...": "any field of a Kills step (savageRole, weapon, distance, bodyPart, ...) is passed on to it",
		},
	},
	"SurviveAndExtract": {
		"note": "Survive and extract: a Completion counter with ExitStatus and Location steps, as the base game ends kill tasks.",
		"keys": {
			"map": "the map (default: the quest's location)", "status": "exit statuses that count (default [\"Survived\", \"Transit\"])",
			"exit": "optional: only this exit (an ExitName step)", "text": "default \"Survive and extract from the location\"",
		},
	},
}
SHORTHAND_SHARED = {
	"ref": "a name for the condition, for other conditions' \"after\" (any condition can have one)",
	"after": "the ref names (or ids) of conditions to complete first: the condition is shown only then (visibilityConditions)",
}
_KILL_FIELDS = (
	"savageRole", "weapon", "weaponCaliber", "weaponModsInclusive", "weaponModsExclusive", "bodyPart", "distance", "daytime",
	"enemyEquipmentInclusive", "enemyEquipmentExclusive", "enemyHealthEffects", "resetOnSessionEnd",
)
_COUNTER_KEYS = (
	"id", "text", "counterId", "index", "parentId", "visibilityConditions", "oneSessionOnly", "isResetOnConditionFailed",
	"isNecessary", "doNotResetIfCounterCompleted", "completeInSeconds", "globalQuestCounterId", "extra", "omit",
)


class SpecError(Exception):
	"""What is wrong with a spec: every problem found, one per line, each starting with where it is."""

	def __init__(self, problems):
		self.problems = list(problems)
		super().__init__("\n".join(self.problems))


class _Problems:
	def __init__(self):
		self.found = []

	def add(self, where, text):
		self.found.append(f"{where}: {text}")

	def raise_any(self):
		if self.found:
			raise SpecError(self.found)


# --- finding ids by name -------------------------------------------------------------------------------

class Resolver:
	"""Turns names into ids: items, item categories, traders, quests, maps, achievements, clothing and composite items.
	An id is kept as it is. A name must match exactly (any case); when it matches more than one, or none, the
	problem lists the closest ones with their ids."""

	def __init__(self, ws, batch=()):
		self.ws = ws
		self.gamedata = ws.gamedata
		self.batch = {}  # {name (lower case): quest id} of the quests being added together
		for quest_id, name in batch:
			self.batch.setdefault(name.lower(), quest_id)
		self._rows = None
		self._by_name = {}

	def rows(self):
		if self._rows is None:
			self._rows = lookup.build_rows(self.gamedata, quests=self.ws.quests.data, library=self.ws.library, references=self.ws.references)
		return self._rows

	def _index(self, kinds):
		key = tuple(sorted(kinds))
		if key not in self._by_name:
			ids, names = {}, {}
			for row in self.rows():
				if row.kind not in kinds:
					continue
				ids.setdefault(row.id, row)
				names.setdefault(row.name.lower(), []).append(row)
				if row.kind == lookup.ITEM:
					short = self.gamedata.locale.get(f"{row.id} ShortName")
					if short and short.lower() != row.name.lower():
						names.setdefault(short.lower(), []).append(row)
			self._by_name[key] = (ids, names)
		return self._by_name[key]

	def find(self, value, kinds, what):
		"""The id for value among rows of these kinds. Raises ValueError saying what's wrong."""
		if not isinstance(value, str) or not value.strip():
			raise ValueError(f"{what} must be a name or an id, not {value!r}")
		ids, names = self._index(kinds)
		if value in ids:
			return value
		found = list({row.id: row for row in names.get(value.strip().lower(), [])}.values())
		if len(found) == 1:
			return found[0].id
		if found:
			listed = "; ".join(f"{r.id} ({r.name}{', ' + r.detail if r.detail else ''})" for r in found[:8])
			raise ValueError(f"'{value}' is the name of {len(found)} {what}s: {listed}. Use the id")
		if is_id(value):
			return value  # (an id the program doesn't know: a custom item or quest from another file)
		close = lookup.search(self.rows(), value, kinds=kinds, limit=6)
		hint = "; ".join(f"{r.name} ({r.id})" for r in close)
		raise ValueError(f"no {what} is called '{value}'" + (f". Close: {hint}" if hint else ""))

	def item(self, value, categories=False):
		kinds = {lookup.ITEM, lookup.REF_ITEM} | ({lookup.CATEGORY} if categories else set())
		return self.find(value, kinds, "item or category" if categories else "item")

	def trader(self, value):
		return self.find(value, {lookup.TRADER, lookup.REF_TRADER}, "trader")

	def quest(self, value):
		if isinstance(value, str) and value.lower() in self.batch:
			return self.batch[value.lower()]
		return self.find(value, {lookup.QUEST, lookup.REF_QUEST}, "quest")

	def achievement(self, value):
		return self.find(value, {lookup.ACHIEVEMENT}, "achievement")

	def customization(self, value):
		return self.find(value, {lookup.CUSTOMIZATION}, "clothing item")

	def quest_location(self, value):
		"""A quest's "location": a map's _id, or "any"."""
		ids = location_ids()
		if value in ("any", "marathon") or value in ids.values():
			return value
		key = self.map_key(value)
		if key in ids:
			return ids[key]
		raise ValueError(f"'{value}' isn't a map")

	def map_key(self, value):
		"""A map as Location conditions and zone files name it (bigmap, factory4_day, ...)."""
		if not isinstance(value, str):
			raise ValueError(f"a map must be a name, not {value!r}")
		key = location_key(value)
		if key:
			return key
		ids = location_ids()
		for k, location_id in ids.items():
			if value == location_id:
				return k
		named = [k for k, location_id in ids.items() if self.gamedata.locale.get(f"{location_id} Name", "").lower() == value.lower()]
		if len(named) == 1:
			return named[0]
		if value.lower() == "any":
			return "Any"
		if value in OTHER_MAPS:
			return value
		raise ValueError(f"'{value}' isn't a map. Maps: {', '.join(f'{k} ({self.gamedata.locations.get(i, k)})' for k, i in ids.items())}")

	def composite(self, value):
		"""A copy (new ids) of the parts of a saved or vanilla composite item, by name or id."""
		row_id = self.find(value, {lookup.MINE, lookup.PRESET}, "composite item")
		if row_id in self.ws.library.entries:
			return self.ws.library.parts_of(row_id)
		from core.library import preset_parts

		preset = self.gamedata.item_presets.get(row_id)
		if preset is None:
			raise ValueError(f"no composite item has the id {row_id}")
		return preset_parts(preset)


# --- field values ---------------------------------------------------------------------------------------

def _choice(value, field, gamedata):
	"""A value of a choice field: one of its values, or its label (any case). A field that also takes other values
	keeps a value in another case as it is written."""
	pairs = choices.resolve(field.choices, gamedata)
	if any(value == v for v, _label in pairs):
		return value
	lowered = value.lower() if isinstance(value, str) else None
	for v, label in pairs:
		if lowered is not None and isinstance(v, str) and lowered == v.lower():
			return value if field.open else v
		if lowered is not None and isinstance(label, str) and lowered == label.lower():
			return v
	if field.open:
		return value
	raise ValueError(f"{value!r} isn't one of: {', '.join(f'{v} ({l})' if str(v) != str(l) else str(v) for v, l in pairs)}")


def convert(field, value, resolver, group=None, kind=None):
	"""A spec's value for a field, as the quest JSON has it. Raises ValueError saying what's wrong."""
	k = field.kind
	gamedata = resolver.gamedata
	if k in (TEXT, MULTILINE):
		if not isinstance(value, str):
			raise ValueError("must be text")
		return value
	if k == INT:
		if isinstance(value, bool) or not isinstance(value, (int, float)) or int(value) != value:
			raise ValueError("must be a whole number")
		value = int(value)
		_bounds(field, value)
		return value
	if k == NUMBER:
		if isinstance(value, bool) or not isinstance(value, (int, float)):
			raise ValueError("must be a number")
		_bounds(field, value)
		return value
	if k == BOOL:
		if not isinstance(value, bool):
			raise ValueError("must be true or false")
		return value
	if k == CHOICE:
		if field.choices == "locations":
			return resolver.quest_location(value)
		return _choice(value, field, gamedata)
	if k == LIST:
		values = value if isinstance(value, list) else [value]
		if (group, kind, field.key) == ("subtask", "Location", "target"):
			return [resolver.map_key(v) for v in values]
		if field.choices:
			return [_choice(v, field, gamedata) for v in values]
		return list(values)
	if k == REF:
		return _ref(field.ref, value, resolver, field)
	if k == IDLIST:
		values = value if isinstance(value, list) else [value]
		return [_ref(field.ref, v, resolver, field) for v in values]
	if k == GROUPS:
		if not isinstance(value, list):
			raise ValueError("must be a list of lists")
		return [[_ref(field.ref, v, resolver, field) for v in (group_ if isinstance(group_, list) else [group_])] for group_ in value]
	if k == OBJECT:
		subfields = {f.key: f for f in field.fields}
		if isinstance(value, (int, float)) and not isinstance(value, bool) and {"compareMethod", "value"} <= set(subfields):
			value = {"compareMethod": ">=", "value": value}
		if not isinstance(value, dict):
			raise ValueError("must be an object" + (" or a number (meaning 'at least')" if "compareMethod" in subfields else ""))
		out = {}
		for key, sub in value.items():
			if key in subfields:
				out[key] = convert(subfields[key], sub, resolver)
			else:
				out[key] = sub
		return out
	if k in (VISIBILITY, BODY_EFFECTS, JSON):
		return copy.deepcopy(value)
	return copy.deepcopy(value)


def _bounds(field, value):
	if field.minimum is not None and value < field.minimum:
		raise ValueError(f"must be at least {field.minimum}")
	if field.maximum is not None and value > field.maximum:
		raise ValueError(f"must be at most {field.maximum}")


def _ref(ref, value, resolver, field):
	if ref == "item":
		return resolver.item(value, categories=field.categories)
	if ref == "trader":
		return resolver.trader(value)
	if ref == "quest":
		return resolver.quest(value)
	if ref == "achievement":
		return resolver.achievement(value)
	if ref == "customization":
		return resolver.customization(value)
	if ref == "location":
		return resolver.quest_location(value)
	return value  # (ids inside the quest, recipe items, ...: kept as given)


# --- shorthands, ref and after ---------------------------------------------------------------------------

def _quest_map(quest_spec):
	location = quest_spec.get("location")
	return None if not location or str(location).lower() in ("any", "marathon") else location


def _maps(value):
	if value is None or (isinstance(value, str) and value.lower() in ("", "any")):
		return None
	return value if isinstance(value, list) else [value]


def _counter(item, kind, counter_type, value, steps, where, problems):
	"""A CounterCreator spec from a shorthand's remaining keys (only a counter's own keys may remain)."""
	unknown = sorted(set(item) - set(_COUNTER_KEYS) - {"kind"})
	if unknown:
		has = [k for k in SHORTHANDS[kind]["keys"] if k != "..."] + (list(_KILL_FIELDS) if kind == "Kill" else []) + list(SHORTHAND_SHARED) + ["text", "id"]
		problems.add(where, f"{', '.join(unknown)} isn't a key of a {kind}. It has: {', '.join(has)} (and a counter's own keys)")
	counter = {k: v for k, v in item.items() if k in _COUNTER_KEYS}
	counter.update(kind="CounterCreator", type=counter_type, value=value, conditions=steps)
	return counter


def _visit(item, quest_spec, where, problems):
	zone = item.pop("zone", None)
	if not isinstance(zone, str) or not zone:
		problems.add(f"{where}.zone", "a Visit needs \"zone\": the id of a visit zone")
		zone = ""
	steps = [{"kind": "VisitPlace", "target": zone}]
	maps = _maps(item.pop("map", None))
	if maps:
		steps.append({"kind": "Location", "target": maps})
	return _counter(item, "Visit", "Exploration", 1, steps, where, problems)


def _kill(item, quest_spec, where, problems):
	count = item.pop("count", 1)
	kills = {"kind": "Kills", "target": item.pop("target", "Any")}
	for key in _KILL_FIELDS:
		if key in item:
			kills[key] = item.pop(key)
	steps = [kills]
	zone = item.pop("zone", None)
	if zone:
		steps.append({"kind": "InZone", "zoneIds": zone if isinstance(zone, list) else [zone]})
	maps = _maps(item.pop("map", _quest_map(quest_spec)))
	if maps:
		steps.append({"kind": "Location", "target": maps})
	return _counter(item, "Kill", "Elimination", count, steps, where, problems)


def _survive(item, quest_spec, where, problems):
	steps = [{"kind": "ExitStatus", "status": item.pop("status", ["Survived", "Transit"])}]
	exit_name = item.pop("exit", None)
	if exit_name:
		steps.append({"kind": "ExitName", "exitName": exit_name})
	maps = _maps(item.pop("map", _quest_map(quest_spec)))
	if maps:
		steps.append({"kind": "Location", "target": maps})
	item.setdefault("text", "Survive and extract from the location")
	return _counter(item, "SurviveAndExtract", "Completion", 1, steps, where, problems)


_EXPAND = {"Visit": _visit, "Kill": _kill, "SurviveAndExtract": _survive}


def expand(lists, quest_spec, problems):
	"""The condition lists {start, finish, fail: [spec]} with shorthands (SHORTHANDS) written out, each "ref" given
	an id, and each "after" turned into visibilityConditions on the conditions it names."""
	labels = {}
	for list_name, items in lists.items():
		for i, item in enumerate(items):
			if isinstance(item, dict) and "ref" in item:
				label = item["ref"]
				if not isinstance(label, str) or not label:
					problems.add(f"{list_name}[{i}].ref", "must be a name for the condition, for other conditions' \"after\"")
				elif label in labels:
					problems.add(f"{list_name}[{i}].ref", f"'{label}' names two conditions")
				else:
					labels[label] = item.get("id") or new_id()
	expanded = {}
	for list_name, items in lists.items():
		out = []
		for i, item in enumerate(items):
			where = f"{list_name}[{i}]"
			if not isinstance(item, dict):
				out.append(item)
				continue
			item = copy.deepcopy(item)
			label = item.pop("ref", None)
			if label in labels:
				item["id"] = labels[label]
			after = item.pop("after", None)
			if item.get("kind") in _EXPAND:
				item = _EXPAND[item["kind"]](item, quest_spec, where, problems)
			if after is not None:
				shown = list(item.get("visibilityConditions") or [])
				for target in after if isinstance(after, list) else [after]:
					if isinstance(target, str) and target in labels:
						shown.append({"conditionType": "CompleteCondition", "id": new_id(), "target": labels[target]})
					elif isinstance(target, str) and is_id(target):
						shown.append({"conditionType": "CompleteCondition", "id": new_id(), "target": target})
					else:
						known = ", ".join(labels) or "none"
						problems.add(f"{where}.after", f"no condition has the ref {target!r} (refs: {known})")
				item["visibilityConditions"] = shown
			out.append(item)
		expanded[list_name] = out
	return expanded


# --- building quests ------------------------------------------------------------------------------------

def _apply_fields(item, spec, group, kind, resolver, where, problems, skip=()):
	"""Set the spec's keys on a new item: fields are converted, other keys the kind has are set as given."""
	s = registry.spec_for(group, kind)
	for key, value in spec.items():
		if key in skip:
			continue
		field = s.field(key)
		if field is None:
			if key in s.base or key in ("index", "parentId", "visibilityConditions"):
				item[key] = copy.deepcopy(value)
				continue
			allowed = sorted({f.key for f in s.fields} | set(s.base) - set(s.managed) - {"conditionType", "type"})
			problems.add(where, f"'{key}' isn't a key of {kind}. It can have: {', '.join(allowed)} (put anything else under \"extra\")")
			continue
		try:
			item[key] = convert(field, value, resolver, group, kind)
		except ValueError as e:
			problems.add(f"{where}.{key}", str(e))
	extra = spec.get("extra")
	if extra is not None:
		if isinstance(extra, dict):
			item.update(copy.deepcopy(extra))
		else:
			problems.add(f"{where}.extra", "must be an object of keys to set as they are")
	_omit(item, spec, where, problems)


def _omit(item, spec, where, problems):
	"""Leave out the keys the spec's "omit" lists (keys a new item has that the described one didn't)."""
	omit = spec.get("omit") or []
	if not isinstance(omit, list):
		problems.add(f"{where}.omit", "must be a list of keys")
		return
	for key in omit:
		item.pop(key, None)


def build_condition(spec, group, resolver, where, problems, texts):
	"""A task (group 'task') or subtask ('subtask') from its spec; its text, if any, goes into texts {id: text}."""
	if not isinstance(spec, dict):
		problems.add(where, "a condition must be an object with a 'kind'")
		return None
	kind = spec.get("kind") or spec.get("conditionType")
	known = registry.GROUPS[group]
	if kind not in known:
		short = f"; or a shorthand: {', '.join(SHORTHANDS)}" if group == "task" else ""
		problems.add(f"{where}.kind", f"{kind!r} isn't a {'condition' if group == 'task' else 'counter step'} kind. Kinds: {', '.join(known)}{short}")
		return None
	item = registry.new_item(group, kind)
	if spec.get("id"):
		item["id"] = spec["id"]
	skip = ("kind", "conditionType", "id", "text", "extra", "omit", "conditions", "counterId")
	_apply_fields(item, spec, group, kind, resolver, where, problems, skip)
	if kind == "CounterCreator":
		steps = spec.get("conditions") or []
		if not isinstance(steps, list) or not steps:
			problems.add(f"{where}.conditions", "a CounterCreator needs a list of steps (Kills, Location, InZone, ...)")
		built = [build_condition(step, "subtask", resolver, f"{where}.conditions[{i}]", problems, texts) for i, step in enumerate(steps if isinstance(steps, list) else [])]
		item["counter"]["conditions"] = [b for b in built if b is not None]
		if spec.get("counterId"):
			item["counter"]["id"] = spec["counterId"]
	elif "conditions" in spec:
		problems.add(f"{where}.conditions", "only a CounterCreator has steps")
	text = spec.get("text")
	if text is not None:
		if text == "auto":
			text = L.generated_task_text(item, Names(resolver.gamedata))
			if not text:
				problems.add(f"{where}.text", "\"auto\" text is only made for FindItem, HandoverItem and Skill: write the text")
		if not isinstance(text, str):
			problems.add(f"{where}.text", "must be text")
		elif group == "subtask":
			problems.add(f"{where}.text", "a counter step has no text of its own: give the CounterCreator the text")
		else:
			texts[item["id"]] = text
	return item


def _parts_from(spec, resolver, where, problems, find_in_raid=True):
	"""The parts of an item reward or offer from a spec's "items" (simple items), "composite" or "parts" (raw)."""
	if "parts" in spec:
		parts = spec["parts"]
		if not isinstance(parts, list) or not all(isinstance(p, dict) and p.get("_tpl") for p in parts):
			problems.add(f"{where}.parts", "must be a list of item parts, each with an _id and a _tpl")
			return []
		parts = copy.deepcopy(parts)
		for part in parts:
			part.setdefault("_id", new_id())
		return parts
	if "composite" in spec:
		try:
			parts = resolver.composite(spec["composite"])
		except ValueError as e:
			problems.add(f"{where}.composite", str(e))
			return []
		count = spec.get("count", 1)
		for _ in range(max(0, int(count) - 1) if isinstance(count, int) else 0):
			parts += resolver.composite(spec["composite"])
		return parts
	entries = spec.get("items")
	if entries is None:
		problems.add(where, "needs \"items\" (a list of {\"item\": name, \"count\": n}), \"composite\" (a composite item's name) or \"parts\" (raw parts)")
		return []
	parts = []
	for i, entry in enumerate(entries if isinstance(entries, list) else [entries]):
		here = f"{where}.items[{i}]"
		if isinstance(entry, str):
			entry = {"item": entry}
		if not isinstance(entry, dict) or "item" not in entry:
			problems.add(here, "must be an item name or {\"item\": name, \"count\": n, \"foundInRaid\": true/false}")
			continue
		unknown = set(entry) - {"item", "count", "foundInRaid", "id"}
		if unknown:
			problems.add(here, f"unknown keys {', '.join(sorted(unknown))} (an entry has item, count, foundInRaid and id)")
		try:
			tpl = resolver.item(entry["item"])
		except ValueError as e:
			problems.add(f"{here}.item", str(e))
			continue
		count = entry.get("count", 1)
		if isinstance(count, bool) or not isinstance(count, int) or count < 1:
			problems.add(f"{here}.count", "must be a whole number of at least 1")
			continue
		upd = {"StackObjectsCount": count}
		fir = entry.get("foundInRaid", None if tpl in MONEY else find_in_raid)
		if fir is not None:
			upd["SpawnedInSession"] = bool(fir)
		parts.append({"_id": entry.get("id") or new_id(), "_tpl": tpl, "upd": dict(sorted(upd.items()))})
	return parts


def build_reward(spec, list_key, resolver, ws, quest_id, where, problems, locks):
	"""A reward from its spec. An unlock reward also gives the quest lock it needs, added to locks as
	(section, offer id, quest id); a new offer is added to the open assort."""
	if not isinstance(spec, dict):
		problems.add(where, "a reward must be an object with a 'kind'")
		return None
	kind = spec.get("kind") or spec.get("type")
	if kind not in registry.GROUPS["reward"]:
		problems.add(f"{where}.kind", f"{kind!r} isn't a reward kind. Kinds: {', '.join(registry.GROUPS['reward'])}")
		return None
	if kind == "AssortmentUnlock":
		return _build_unlock(spec, list_key, resolver, ws, quest_id, where, problems, locks)
	reward = registry.new_item("reward", kind)
	if spec.get("id"):
		reward["id"] = spec["id"]
	if kind == "Item" and "findInRaid" not in spec and _gives_only_money(spec, resolver):
		reward["findInRaid"] = False  # (as the base game gives money: 431 of its 456 money rewards)
	skip = ("kind", "type", "id", "extra", "omit", "items", "composite", "parts")
	_apply_fields(reward, spec, "reward", kind, resolver, where, problems, skip)
	if kind in ("Item", "ProductionScheme"):
		if any(k in spec for k in ("items", "composite", "parts")) or kind == "Item":
			parts = _parts_from(spec, resolver, where, problems, reward.get("findInRaid", True))
			reward["items"] = parts
			roots = [p for p in parts if not p.get("parentId")]
			if not spec.get("target") and roots:
				reward["target"] = roots[0]["_id"]
			if kind == "Item":
				reward["value"] = item_count(parts) or 1
	return reward


def _gives_only_money(spec, resolver):
	"""True for an item reward spec whose items are all money (named or by id)."""
	if "parts" in spec:
		roots = [p for p in spec["parts"] if isinstance(p, dict) and not p.get("parentId")] if isinstance(spec["parts"], list) else []
		return bool(roots) and all(p.get("_tpl") in MONEY for p in roots)
	entries = spec.get("items")
	entries = entries if isinstance(entries, list) else [entries] if entries else []
	if not entries:
		return False
	for entry in entries:
		name = entry.get("item") if isinstance(entry, dict) else entry
		try:
			if resolver.item(name) not in MONEY:
				return False
		except ValueError:
			return False
	return True


def _only_money(parts):
	roots = [p for p in parts or [] if isinstance(p, dict) and not p.get("parentId")]
	return bool(roots) and all(p.get("_tpl") in MONEY for p in roots)


def _build_unlock(spec, list_key, resolver, ws, quest_id, where, problems, locks):
	trader = spec.get("traderId") or spec.get("trader") or ws.trader_id
	try:
		trader = resolver.trader(trader) if trader else ""
	except ValueError as e:
		problems.add(f"{where}.traderId", str(e))
		trader = ""
	if not trader:
		problems.add(where, "an AssortmentUnlock needs a trader: give \"traderId\" or set \"trader\" in the project file")
	unknown = set(spec) - {"kind", "type", "id", "extra", "offer", "item", "items", "composite", "parts", "target", "traderId", "trader", "loyaltyLevel", "price", "currency", "barter", "stack", "buyLimit", "unknown", "isHidden", "gameMode", "availableInGameEditions", "index", "illustrationConfig", "omit"}
	if unknown:
		problems.add(where, f"unknown keys for an AssortmentUnlock: {', '.join(sorted(unknown))}")
	assort = ws.assort.data if ws.assort is not None else None
	offer = spec.get("offer")
	new_offer = any(k in spec for k in ("item", "composite")) or ("parts" in spec and not offer and "price" in spec)
	if (offer or new_offer) and assort is None:
		problems.add(where, "the project has no trader assort file, so the offer can't be found or made")
		return None
	level = spec.get("loyaltyLevel")
	if new_offer:
		item_spec = {"items": [{"item": spec["item"], "count": 1}]} if "item" in spec else {k: spec[k] for k in ("composite", "parts") if k in spec}
		parts = _parts_from(item_spec, resolver, where, problems, None)  # (an offer's items aren't found in raid)
		if not parts:
			return None
		barter = _barter(spec, resolver, where, problems)
		stack = spec.get("stack", 9999999)
		items, scheme, offer_level = A.new_offer_from_parts(parts, level=level or 1, stack=stack)
		items[0]["upd"]["StackObjectsCount"] = stack
		if spec.get("buyLimit"):
			items[0]["upd"].update(BuyRestrictionMax=spec["buyLimit"], BuyRestrictionCurrent=0)
		offer = A.add_offer(assort, items, barter or scheme, offer_level)
	if offer:
		if offer not in A.offer_ids(assort):
			problems.add(f"{where}.offer", f"the trader assort has no offer {offer}")
			return None
		if "parts" in spec and not new_offer:
			reward = registry.new_item("reward", "AssortmentUnlock")
			reward.update(traderId=trader, loyaltyLevel=level or assort.get("loyal_level_items", {}).get(offer, 1), items=copy.deepcopy(spec["parts"]), target=spec.get("target") or spec["parts"][0].get("_id"))
		else:
			reward = A.unlock_reward(assort, offer, trader, level)
		section = LOCK_OF.get(list_key)
		if section is None:
			problems.add(where, "an unlock in the Fail rewards has no quest lock (locks are for Success and Started)")
		else:
			locks.append((section, offer, quest_id))
	elif "parts" in spec:
		reward = registry.new_item("reward", "AssortmentUnlock")
		reward.update(traderId=trader, loyaltyLevel=level or 1, items=copy.deepcopy(spec["parts"]), target=spec.get("target") or spec["parts"][0].get("_id"))
	else:
		problems.add(where, "an AssortmentUnlock needs \"offer\" (an offer id in the trader assort), or \"item\" / \"composite\" with \"price\" to make a new offer")
		return None
	if spec.get("id"):
		reward["id"] = spec["id"]
	for key in ("unknown", "isHidden", "gameMode", "availableInGameEditions", "index", "illustrationConfig"):
		if key in spec:
			reward[key] = copy.deepcopy(spec[key])
	if isinstance(spec.get("extra"), dict):
		reward.update(copy.deepcopy(spec["extra"]))
	_omit(reward, spec, where, problems)
	return reward


def _barter(spec, resolver, where, problems):
	"""The price of a new offer: "price" with "currency" (roubles, dollars, euros), or "barter": [{item, count}]."""
	if "barter" in spec:
		scheme = []
		for i, entry in enumerate(spec["barter"] if isinstance(spec["barter"], list) else []):
			try:
				scheme.append({"count": entry.get("count", 1), "_tpl": resolver.item(entry["item"])})
			except (ValueError, KeyError, AttributeError) as e:
				problems.add(f"{where}.barter[{i}]", f"must be {{\"item\": name, \"count\": n}} ({e})")
		return [scheme] if scheme else None
	price = spec.get("price")
	if price is None:
		problems.add(where, "a new offer needs a \"price\" (with \"currency\": roubles, dollars or euros) or a \"barter\"")
		return None
	currency = CURRENCIES.get(str(spec.get("currency", "roubles")).lower())
	if currency is None:
		problems.add(f"{where}.currency", "must be roubles, dollars or euros")
		return None
	return [[{"count": price, "_tpl": currency}]]


def build_quest(spec, ws, resolver, quest_id=None):
	"""(quest, locale entries {key: text}, quest locks [(section, offer, quest id)]) from a quest spec. Raises
	SpecError with every problem found. The assort may get new offers (for unlocks of items it doesn't sell yet)."""
	problems = _Problems()
	if not isinstance(spec, dict):
		raise SpecError(["the quest spec must be a JSON object"])
	quest_id = quest_id or spec.get("id") or new_id()
	settings = ws.settings
	quest = make_quest(quest_id, spec.get("name") or "New quest", "", {"image": settings.quest_icon, "side": settings.side})
	if not spec.get("name"):
		problems.add("name", "every quest needs a name (its QuestName, for you; the player sees text.name)")
	trader = spec.get("trader") or spec.get("traderId") or settings.trader or ws.trader_id
	try:
		quest["traderId"] = resolver.trader(trader) if trader else ""
	except ValueError as e:
		problems.add("trader", str(e))
	if not quest["traderId"]:
		problems.add("trader", "every quest needs a trader")
	quest_fields = {f.key for f in QUEST.fields}
	for key, value in spec.items():
		if key in QUEST_KEYS or key == "traderId" or key == "QuestName":
			continue
		if key not in quest_fields:
			problems.add(key, f"isn't a key of a quest. A quest spec has {', '.join(QUEST_KEYS)} and the quest's own keys ({', '.join(sorted(quest_fields - {'QuestName', 'traderId'}))})")
			continue
		try:
			quest[key] = convert(QUEST.field(key), value, resolver, "quest", "quest")
		except ValueError as e:
			problems.add(key, str(e))
	texts = {}
	lists = expand({name: _list(spec, name, problems) for name in TASK_LISTS}, spec, problems)
	for list_name, list_key in TASK_LISTS.items():
		built = [build_condition(c, "task", resolver, f"{list_name}[{i}]", problems, texts) for i, c in enumerate(lists[list_name])]
		quest["conditions"][list_key] = [b for b in built if b is not None]
	locks = []
	rewards = spec.get("rewards") or {}
	if not isinstance(rewards, dict):
		problems.add("rewards", "must be an object: {\"success\": [...], \"started\": [...], \"fail\": [...]}")
		rewards = {}
	for key in rewards:
		if key not in REWARD_LISTS:
			problems.add(f"rewards.{key}", f"isn't a reward list (they are {', '.join(REWARD_LISTS)})")
	for list_name, list_key in REWARD_LISTS.items():
		built = [build_reward(r, list_key, resolver, ws, quest_id, f"rewards.{list_name}[{i}]", problems, locks) for i, r in enumerate(_list(rewards, list_name, problems))]
		quest["rewards"][list_key] = [b for b in built if b is not None]
	text = spec.get("text") or {}
	if not isinstance(text, dict):
		problems.add("text", "must be an object of the quest's text: name, description, successMessageText, ...")
		text = {}
	known_text = set(L.QUEST_TEXT_KEYS)
	for key, value in text.items():
		if key not in known_text:
			problems.add(f"text.{key}", f"isn't a text field (they are {', '.join(L.QUEST_TEXT_KEYS)})")
		elif not isinstance(value, str):
			problems.add(f"text.{key}", "must be text")
		else:
			texts[L.quest_key(quest_id, key)] = value
	if isinstance(spec.get("extra"), dict):
		quest.update(copy.deepcopy(spec["extra"]))
	_omit(quest, spec, "quest", problems)
	problems.raise_any()
	return quest, texts, locks


def _list(spec, key, problems):
	value = spec.get(key) or []
	if not isinstance(value, list):
		problems.add(key, "must be a list")
		return []
	return value


def apply_quest(ws, quest, texts, locks, replace=False):
	"""Put a built quest into the workspace's files: the quest, its text (with an entry for each text it still lacks)
	and its quest locks. replace=True replaces a quest with the same id, else that is an error."""
	quests = ws.quests.data
	quest_id = quest["_id"]
	if quest_id in quests and not replace:
		raise SpecError([f"id: a quest with the id {quest_id} is already in the quests file (use quest update to change it)"])
	ws.quests.change("Add quest" if not replace else "Update quest", lambda data: data.__setitem__(quest_id, quest))
	entries = L.quest_entries(quest)
	entries.update({k: v for k, v in ws.locale.data.items() if k in entries and v and k not in texts})
	entries.update(texts)
	name_key = L.quest_key(quest_id, "name")
	if not entries.get(name_key):
		entries[name_key] = quest.get("QuestName", "")  # (the name the player sees: the quest's own name until it is written)
	ws.locale.change("Quest text", lambda data: data.update(entries))
	if locks:
		if ws.questassort is None:
			raise SpecError(["rewards: an unlock needs the project's questassort file, to lock the offer to the quest"])
		def lock(data):
			for section, offer, qid in locks:
				data.setdefault(section, {})[offer] = qid
		ws.questassort.change("Quest locks", lock)


# --- describing quests ------------------------------------------------------------------------------------

def describe_quest(quest, ws, locale=None):
	"""A quest as a spec: what differs from a new quest, the text from the locale ({key: text}; the workspace's locale
	if None), and "names" telling what the ids are. Building it again gives the same quest (with the same ids)."""
	locale = ws.locale.data if locale is None else locale
	quest_id = quest.get("_id", "")
	spec = {"id": quest_id, "name": quest.get("QuestName", ""), "trader": quest.get("traderId", "")}
	for key in QUEST_BASE:
		if key in ("_id", "QuestName", "traderId", "conditions", "rewards") or key in L.QUEST_TEXT_KEYS:
			continue
		if key in quest and quest[key] != QUEST_BASE[key]:
			spec[key] = copy.deepcopy(quest[key])
	text = {k: locale.get(L.quest_key(quest_id, k)) for k in L.QUEST_TEXT_KEYS}
	spec["text"] = {k: v for k, v in text.items() if v}
	for list_name, list_key in TASK_LISTS.items():
		items = (quest.get("conditions") or {}).get(list_key) or []
		if items:
			spec[list_name] = [describe_condition(t, "task", ws, locale) for t in items]
	rewards = {}
	for list_name, list_key in REWARD_LISTS.items():
		items = (quest.get("rewards") or {}).get(list_key) or []
		if items:
			rewards[list_name] = [describe_reward(r, list_key, quest_id, ws) for r in items]
	if rewards:
		spec["rewards"] = rewards
	extra = {k: copy.deepcopy(v) for k, v in quest.items() if k not in QUEST_BASE}
	extra.update({k: quest[k] for k in L.QUEST_TEXT_KEYS if k in quest and quest[k] != L.quest_key(quest_id, k)})
	if extra:
		spec["extra"] = extra
	omit = [k for k in QUEST_BASE if k not in quest]
	if omit:
		spec["omit"] = omit
	spec["names"] = _names(quest, ws)
	return spec


def describe_condition(item, group, ws, locale=None):
	kind = item.get("conditionType")
	s = registry.spec_for(group, kind)
	out = {"kind": kind, "id": item.get("id", "")}
	extra = {}
	for key, value in item.items():
		if key in ("conditionType", "id", "dynamicLocale") or (key == "counter" and kind == "CounterCreator"):
			continue
		if (key in s.base or s.field(key) is not None) and _fits(s.field(key), value):
			if s.base.get(key, object()) != value:
				out[key] = copy.deepcopy(value)
		else:
			extra[key] = copy.deepcopy(value)
	if kind == "CounterCreator":
		counter = item.get("counter") or {}
		out["counterId"] = counter.get("id", "")
		out["conditions"] = [describe_condition(c, "subtask", ws, locale) for c in counter.get("conditions") or []]
	if item.get("dynamicLocale"):
		extra["dynamicLocale"] = item["dynamicLocale"]
	if extra:
		out["extra"] = extra
	omit = [k for k in s.base if k not in item]
	if omit:
		out["omit"] = omit
	text = (ws.locale.data if locale is None else locale).get(item.get("id", "")) if group == "task" else None
	if text:
		out["text"] = text
	return out


def describe_reward(reward, list_key, quest_id, ws):
	kind = reward.get("type")
	s = registry.spec_for("reward", kind)
	out = {"kind": kind, "id": reward.get("id", "")}
	extra = {}
	for key, value in reward.items():
		if key in ("type", "id"):
			continue
		if kind in ("Item", "AssortmentUnlock", "ProductionScheme") and key in ("items", "target", "value"):
			continue
		if (key in s.base or s.field(key) is not None) and _fits(s.field(key), value):
			if s.base.get(key, object()) != value:
				out[key] = copy.deepcopy(value)
		else:
			extra[key] = copy.deepcopy(value)
	if kind in ("Item", "AssortmentUnlock", "ProductionScheme"):
		parts = reward.get("items") or []
		simple = _simple_items(parts, reward)
		if simple is not None and kind == "Item":
			out["items"] = simple
		else:
			out["parts"] = copy.deepcopy(parts)
			out["target"] = reward.get("target", "")
		if kind == "AssortmentUnlock" and ws.questassort is not None:
			section = LOCK_OF.get(list_key)
			for offer, qid in (ws.questassort.data.get(section) or {}).items() if section else []:
				if qid == quest_id and ws.assort is not None and A.offer_tpl(ws.assort.data, offer) == (A.reward_root(reward) or {}).get("_tpl"):
					out["offer"] = offer
					break
		if kind == "Item" and "findInRaid" in reward and _only_money(parts):
			# (a new reward of only money isn't found in raid, so that is what goes without saying)
			out.pop("findInRaid", None)
			if reward["findInRaid"] is not False:
				out["findInRaid"] = copy.deepcopy(reward["findInRaid"])
	if extra:
		out["extra"] = extra
	omit = [k for k in s.base if k not in reward]
	if omit:
		out["omit"] = omit
	return out


def _fits(field, value):
	"""False for a value of the wrong type for its field (the base game has a few, like a count written as text):
	describe puts those under "extra", where they are kept as they are."""
	if field is None:
		return True
	if field.kind == INT:
		return isinstance(value, (int, float)) and not isinstance(value, bool) and int(value) == value
	if field.kind == NUMBER:
		return isinstance(value, (int, float)) and not isinstance(value, bool)
	if field.kind == BOOL:
		return isinstance(value, bool)
	if field.kind in (TEXT, MULTILINE):
		return isinstance(value, str)
	return True


def _simple_items(parts, reward):
	"""The parts as {"item", "count", "foundInRaid"} entries when they are plain items whose found in raid flag is what
	building them again would give, else None."""
	fir = reward.get("findInRaid", True)
	simple = []
	for part in parts:
		upd = part.get("upd") or {}
		if part.get("parentId") or set(part) - {"_id", "_tpl", "upd"} or set(upd) - {"StackObjectsCount", "SpawnedInSession"}:
			return None
		default = None if part.get("_tpl") in MONEY else fir
		if upd.get("SpawnedInSession", None) != default and not ("SpawnedInSession" not in upd and default is None):
			return None
		count = upd.get("StackObjectsCount")
		if isinstance(count, bool) or not isinstance(count, int) or count < 1:
			return None
		simple.append({"item": part["_tpl"], "count": upd["StackObjectsCount"], "id": part["_id"]})
	if reward.get("target") != (parts[0]["_id"] if parts else ""):
		return None
	return simple


def _names(quest, ws):
	"""{id: name} of the items, traders, quests and maps the quest points at."""
	names = Names(ws.gamedata, {qid: q.get("QuestName", "") for qid, q in ws.quests.data.items() if isinstance(q, dict)})
	found = {}

	def visit(node):
		if isinstance(node, dict):
			for key, value in node.items():
				if isinstance(value, str) and is_id(value) and key not in ("id", "_id", "parentId"):
					name = _name_of(value, names, ws)
					if name:
						found[value] = name
				else:
					visit(value)
		elif isinstance(node, list):
			for value in node:
				if isinstance(value, str) and is_id(value):
					name = _name_of(value, names, ws)
					if name:
						found[value] = name
				else:
					visit(value)

	visit({k: v for k, v in quest.items() if k != "_id"})
	return found


def _name_of(value, names, ws):
	g = ws.gamedata
	return g.item_name(value) or g.trader_name(value) or names.quest_names.get(value) or g.quest_name(value) or g.locations.get(value) or ""


def copy_with_new_ids(spec):
	"""A described quest spec with every id removed, so building it makes a new quest."""
	clean = copy.deepcopy(spec)
	clean.pop("id", None)
	clean.pop("names", None)

	def strip(node):
		if isinstance(node, dict):
			for key in ("id", "counterId"):
				node.pop(key, None)
			for value in node.values():
				strip(value)
		elif isinstance(node, list):
			for value in node:
				strip(value)

	for key in TASK_LISTS:
		strip(clean.get(key))
	if "rewards" in clean:
		for rewards in clean["rewards"].values():
			for reward in rewards:
				reward.pop("id", None)
				if "parts" in reward:
					id_map = {}
					reward["parts"] = with_new_ids(reward["parts"], new_id, id_map)
					reward["target"] = id_map.get(reward.get("target"), reward.get("target"))
	return clean
