"""How the base game fills in a kind of condition, counter step, reward or quest (`python -m cli usage`): the values
each field takes and how often, with quests that use each, so a new quest can copy the game's patterns. No Qt."""

import json
from collections import Counter

from schema import assort as A

MONEY = set(A.MONEY.values())
MISSING = object()


def _steps(item):
	return sorted(s.get("conditionType", "") for s in (item.get("counter") or {}).get("conditions") or [] if isinstance(s, dict))


def _money(item):
	roots = [p for p in item.get("items") or [] if isinstance(p, dict) and not p.get("parentId")]
	return bool(roots) and all(p.get("_tpl") in MONEY for p in roots)


# Fields worked out from an item rather than stored in it: (group, kind, name) -> (function, what it is)
PSEUDO = {
	("task", "CounterCreator", "steps"): (_steps, "the kinds of its counter's steps, sorted"),
	("reward", "Item", "money"): (_money, "true when every item given is money"),
}


def items_of(quests, group, kind):
	"""[(quest name, item)] for every condition (group task), counter step (subtask), reward (reward) or quest (quest)
	of a kind in quests {id: quest}."""
	found = []
	for quest in quests.values():
		if not isinstance(quest, dict):
			continue
		name = quest.get("QuestName", "")
		if group == "quest":
			found.append((name, quest))
		elif group in ("task", "subtask"):
			for tasks in (quest.get("conditions") or {}).values():
				for task in tasks if isinstance(tasks, list) else []:
					if not isinstance(task, dict):
						continue
					if group == "task" and task.get("conditionType") == kind:
						found.append((name, task))
					if group == "subtask":
						for sub in (task.get("counter") or {}).get("conditions") or []:
							if isinstance(sub, dict) and sub.get("conditionType") == kind:
								found.append((name, sub))
		elif group == "reward":
			for rewards in (quest.get("rewards") or {}).values():
				for reward in rewards if isinstance(rewards, list) else []:
					if isinstance(reward, dict) and reward.get("type") == kind:
						found.append((name, reward))
	return found


def value_at(item, path, group="", kind=""):
	"""The value at a dotted path (counter.conditions.0.conditionType), a worked-out field (PSEUDO), or MISSING."""
	pseudo = PSEUDO.get((group, kind, path))
	if pseudo:
		return pseudo[0](item)
	node = item
	for part in path.split("."):
		if isinstance(node, dict) and part in node:
			node = node[part]
		elif isinstance(node, list) and part.isdigit() and int(part) < len(node):
			node = node[int(part)]
		else:
			return MISSING
	return node


def parse_where(text):
	"""(path, value) from "path=value" (the value read as JSON when it can be: 5, true, ["a"]), or (path, MISSING)
	from "path" alone, which keeps the items that have the path."""
	if "=" not in text:
		return text, MISSING
	path, raw = text.split("=", 1)
	try:
		return path.strip(), json.loads(raw)
	except ValueError:
		return path.strip(), raw


def keep(pairs, wheres, group, kind):
	kept = []
	for name, item in pairs:
		ok = True
		for path, wanted in wheres:
			value = value_at(item, path, group, kind)
			if value is MISSING or (wanted is not MISSING and value != wanted):
				ok = False
				break
		if ok:
			kept.append((name, item))
	return kept


def _key(value):
	return json.dumps(value, sort_keys=True, ensure_ascii=False)


def histogram(pairs, path, group, kind, limit=15, examples=2):
	"""(rows [{value, count, examples}], how many items lack the path, how many different values) for one field."""
	counts, names, values, missing = Counter(), {}, {}, 0
	for name, item in pairs:
		value = value_at(item, path, group, kind)
		if value is MISSING:
			missing += 1
			continue
		key = _key(value)
		counts[key] += 1
		values[key] = value
		shown = names.setdefault(key, [])
		if len(shown) < examples and name not in shown:
			shown.append(name)
	rows = [{"value": values[k], "count": n, "examples": names[k]} for k, n in counts.most_common(limit)]
	return rows, missing, len(counts)


def fields(pairs, group, kind, top=3):
	"""{field: {present, values, top: [{value, count}]}} for every key the items have, and the worked-out fields."""
	keys = list(dict.fromkeys(k for _n, item in pairs for k in item))
	keys += [name for (g, k, name) in PSEUDO if (g, k) == (group, kind)]
	summary = {}
	for key in keys:
		rows, missing, distinct = histogram(pairs, key, group, kind, limit=top, examples=0)
		summary[key] = {"present": len(pairs) - missing, "values": distinct, "top": [{"value": _short(r["value"]), "count": r["count"]} for r in rows]}
	return summary


def _short(value):
	text = _key(value)
	return value if len(text) <= 120 else text[:117] + "..."
