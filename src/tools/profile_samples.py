"""Profile the base game's quests (and assorts): for every kind of quest, task, subtask,
reward and reward item, how often each key appears, what types its values have, and (for
short lists of values) which values occur.

Writes schema/vanilla_profile.json, which the validator uses to warn about anything unlike
the base game, and the Schema Explorer shows. Run it again when the game data changes.

Usage (from src):
    python tools/profile_samples.py <database folder or a folder holding quests.json> [assort.json ...]
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT_FILE = HERE.parent / "schema" / "vanilla_profile.json"

MAX_VALUES = 40  # a key with more distinct scalar values than this is free-form: no value list
MAX_EXAMPLE_LEN = 80


def type_name(value):
	if value is None:
		return "null"
	if isinstance(value, bool):
		return "bool"
	if isinstance(value, int):
		return "int"
	if isinstance(value, float):
		return "float"
	if isinstance(value, str):
		return "string"
	if isinstance(value, list):
		return "list"
	return "object"


class KindProfile:
	def __init__(self):
		self.count = 0
		self.keys = defaultdict(lambda: {"count": 0, "types": Counter(), "values": Counter(), "example": None})
		self.where = Counter()  # which list / timing the kind sits in

	def add(self, obj, where=None):
		self.count += 1
		if where:
			self.where[where] += 1
		for key, value in obj.items():
			entry = self.keys[key]
			entry["count"] += 1
			entry["types"][type_name(value)] += 1
			for scalar in scalars(value):
				entry["values"][scalar] += 1
			if entry["example"] is None and value not in ("", [], {}, None):
				entry["example"] = value

	def to_json(self):
		keys = {}
		for key, entry in sorted(self.keys.items()):
			item = {"count": entry["count"], "types": dict(entry["types"].most_common())}
			values = entry["values"]
			if 0 < len(values) <= MAX_VALUES:
				item["values"] = {json.dumps(v) if not isinstance(v, str) else v: n for v, n in values.most_common()}
			example = entry["example"]
			if example is not None and len(json.dumps(example)) <= MAX_EXAMPLE_LEN:
				item["example"] = example
			keys[key] = item
		return {"count": self.count, "where": dict(self.where), "keys": keys}


def scalars(value):
	"""The scalar values in value (inside lists too, one level), for the value lists."""
	if isinstance(value, (str, int, float)) or isinstance(value, bool):
		return [value]
	if isinstance(value, list):
		return [v for v in value if isinstance(v, (str, int, float))]
	return []


def profile_quests(quests):
	kinds = defaultdict(KindProfile)
	for quest in quests.values():
		kinds["quest"].add({k: v for k, v in quest.items() if k not in ("conditions", "rewards")})
		for timing, conditions in quest.get("conditions", {}).items():
			for condition in conditions:
				kind = condition.get("conditionType", "?")
				kinds[f"task:{kind}"].add({k: v for k, v in condition.items() if k not in ("counter", "visibilityConditions")}, timing)
				for visibility in condition.get("visibilityConditions", []) or []:
					if isinstance(visibility, dict):
						kinds["visibility"].add(visibility)
				counter = condition.get("counter")
				if isinstance(counter, dict):
					kinds["counter"].add({k: v for k, v in counter.items() if k != "conditions"})
					for sub in counter.get("conditions", []):
						kinds[f"subtask:{sub.get('conditionType', '?')}"].add(sub, timing)
		for timing, rewards in quest.get("rewards", {}).items():
			for reward in rewards:
				kind = reward.get("type", "?")
				kinds[f"reward:{kind}"].add({k: v for k, v in reward.items() if k != "items"}, timing)
				for item in reward.get("items", []) or []:
					kinds["reward_item"].add({k: v for k, v in item.items() if k != "upd"})
					if isinstance(item.get("upd"), dict):
						kinds["reward_item_upd"].add(item["upd"])
	return kinds


def profile_assort(assort, kinds):
	for item in assort.get("items", []):
		root = item.get("parentId") == "hideout"
		kinds["assort_root" if root else "assort_part"].add({k: v for k, v in item.items() if k != "upd"})
		if isinstance(item.get("upd"), dict):
			kinds["assort_root_upd" if root else "assort_part_upd"].add(item["upd"])
	for schemes in assort.get("barter_scheme", {}).values():
		for alternative in schemes:
			for price in alternative:
				kinds["barter_price"].add(price)
	levels = Counter(assort.get("loyal_level_items", {}).values())
	kinds["loyal_level"].count += sum(levels.values())
	for level, n in levels.items():
		kinds["loyal_level"].keys["level"]["count"] += n
		kinds["loyal_level"].keys["level"]["values"][level] += n
		kinds["loyal_level"].keys["level"]["types"]["int"] += n


def find(folder, relative_options):
	for relative in relative_options:
		if (folder / relative).is_file():
			return folder / relative
	return None


def load(path):
	return json.loads(Path(path).read_bytes().decode("utf-8-sig"))


def main(args):
	source = Path(args[0])
	quests_path = source if source.is_file() else find(source, ("templates/quests.json", "quests.json"))
	if quests_path is None:
		sys.exit(f"No quests.json found in {source}")
	kinds = profile_quests(load(quests_path))
	assorts = [Path(a) for a in args[1:]]
	if not assorts and source.is_dir():
		assorts = sorted(source.glob("traders/*/assort.json"))
	for path in assorts:
		profile_assort(load(path), kinds)
	result = {"kinds": {name: kinds[name].to_json() for name in sorted(kinds)}}
	with open(OUT_FILE, "w", encoding="utf-8", newline="\n") as f:
		json.dump(result, f, indent=1, ensure_ascii=False)
		f.write("\n")
	print(f"Wrote {len(kinds)} kinds to {OUT_FILE} ({OUT_FILE.stat().st_size // 1024} KB)")
	for name in sorted(kinds):
		print(f"{kinds[name].count:6}  {name}")


if __name__ == "__main__":
	if len(sys.argv) < 2:
		sys.exit(__doc__)
	main(sys.argv[1:])
