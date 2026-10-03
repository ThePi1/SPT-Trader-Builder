"""Read the SPT server's C# data models and write the parts the validator needs to
schema/server_models.json.

The server (sp-tarkov/server-csharp) turns every quest, reward, item and assort file into
these C# records when it loads them. A key the record marks ``required`` that is missing, or
a value of the wrong type, stops the file from loading; a key the record doesn't have is
ignored. So the records are the exact rules for "the server can load this".

Usage (from src_new):
    python tools/extract_server_models.py <path to a server-csharp checkout>

The checkout used for SPT 4.0.13 is commit 2891fd41fd07b6150a2192ac0d24adb93eb72862.
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT_FILE = HERE.parent / "schema" / "server_models.json"

MODELS_DIR = "Libraries/SPTarkov.Server.Core/Models"

# The records the app's files are read into; everything they refer to is included too.
ROOTS = ("Quest", "Reward", "Item", "TraderAssort", "QuestAssortFile")

# Where to look first when two files declare a record of the same name
PREFERRED_DIRS = ("Eft/Common/Tables", "Enums", "Eft/Common", "Common")

# questassort.json is a plain dictionary in the server (Trader.QuestAssort); give it a name
EXTRA_RECORDS = {
	"QuestAssortFile": {
		"file": "(Trader.QuestAssort)",
		"kind": "dictionary",
		"type": "Dictionary<string, Dictionary<MongoId, MongoId>>",
	}
}

_DECL_RE = re.compile(r"^\s*public\s+(?:sealed\s+|partial\s+|abstract\s+)*(record|class|enum)\s+(\w+)")
_ATTR_NAME_RE = re.compile(r'\[JsonPropertyName\("([^"]+)"\)\]')
_ATTR_CONVERTER_RE = re.compile(r"\[JsonConverter\(typeof\((\w+)")
_ATTR_IGNORE_RE = re.compile(r"\[JsonIgnore")
_ATTR_EXTENSION_RE = re.compile(r"\[JsonExtensionData")
_PROP_RE = re.compile(
	r"^\s*public\s+(?P<modifiers>(?:(?:required|virtual|override|new)\s+)*)(?P<type>[\w<>?,\[\]\s.]+?)\s+(?P<name>\w+)\s*(?:\{|$)"
)
_ENUM_MEMBER_RE = re.compile(r"^\s*(\w+)\s*(?:=\s*(-?\d+))?\s*,?\s*(?://.*)?$")


def strip_comments(text):
	text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
	return "\n".join(line.split("//", 1)[0] if "//" in line and "http" not in line else line for line in text.splitlines())


def parse_file(path):
	"""{name: declaration} for every record, class and enum in a .cs file."""
	found = {}
	lines = strip_comments(path.read_text(encoding="utf-8-sig")).splitlines()
	i = 0
	while i < len(lines):
		m = _DECL_RE.match(lines[i])
		if not m:
			i += 1
			continue
		kind, name = m.groups()
		# the body: from the first "{" to its matching "}"
		depth, body, started = 0, [], False
		while i < len(lines):
			line = lines[i]
			if started:
				body.append(line)
			depth += line.count("{") - line.count("}")
			if "{" in line and not started:
				started = True
				after = line.split("{", 1)[1]
				body.append(after)
			i += 1
			if started and depth <= 0:
				break
		decl = parse_enum(body) if kind == "enum" else parse_record(body)
		decl["kind"] = kind
		found[name] = decl
	return found


def parse_enum(body):
	members = {}
	value = 0
	for line in " ".join(body).replace("}", "").split(","):
		line = line.strip()
		if not line:
			continue
		m = re.match(r"^(\w+)\s*(?:=\s*(-?\d+))?$", line)
		if not m:
			continue
		if m.group(2) is not None:
			value = int(m.group(2))
		members[m.group(1)] = value
		value += 1
	return {"members": members}


def parse_record(body):
	"""The JSON properties of a record: {json name: {type, required, converter}}."""
	props = {}
	pending = {}
	depth = 0
	for line in body:
		if depth == 0:
			if _ATTR_NAME_RE.search(line):
				pending["name"] = _ATTR_NAME_RE.search(line).group(1)
			if _ATTR_CONVERTER_RE.search(line):
				pending["converter"] = _ATTR_CONVERTER_RE.search(line).group(1)
			if _ATTR_IGNORE_RE.search(line):
				pending["ignore"] = True
			if _ATTR_EXTENSION_RE.search(line):
				pending["extension"] = True
			m = _PROP_RE.match(line)
			if m and "(" not in line.split("{")[0] and "=>" not in line.split("{")[0]:
				name = pending.get("name", m.group("name"))
				if not pending.get("ignore") and not pending.get("extension"):
					prop = {"type": " ".join(m.group("type").split()), "required": "required" in m.group("modifiers").split()}
					if pending.get("converter"):
						prop["converter"] = pending["converter"]
					props[name] = prop
				pending = {}
			elif m is None and line.strip().startswith("public"):
				pending = {}  # (a method or constant: forget the attributes)
		depth += line.count("{") - line.count("}")
	return {"properties": props}


_TYPE_NAME_RE = re.compile(r"[A-Za-z_]\w*")
_BUILTIN = {
	"string", "bool", "int", "long", "short", "byte", "double", "float", "decimal", "object",
	"MongoId", "List", "HashSet", "IEnumerable", "Dictionary", "ListOrT", "IList", "ISet",
	"IReadOnlyList", "IReadOnlyDictionary", "IDictionary", "ICollection", "Nullable",
}


def referenced(decl):
	names = set()
	for prop in decl.get("properties", {}).values():
		names |= set(_TYPE_NAME_RE.findall(prop["type"]))
	if "type" in decl:
		names |= set(_TYPE_NAME_RE.findall(decl["type"]))
	return {n for n in names if n not in _BUILTIN}


def main(server_dir):
	models_dir = Path(server_dir) / MODELS_DIR
	if not models_dir.is_dir():
		sys.exit(f"Not a server-csharp checkout (no {MODELS_DIR}): {server_dir}")
	candidates = {}
	for path in sorted(models_dir.rglob("*.cs")):
		rel = path.relative_to(models_dir).as_posix()
		for name, decl in parse_file(path).items():
			decl["file"] = rel
			candidates.setdefault(name, []).append(decl)

	def pick(name):
		options = candidates.get(name)
		if not options:
			return None
		for preferred in PREFERRED_DIRS:
			for decl in options:
				if decl["file"].startswith(preferred):
					return decl
		return options[0]

	out = {}
	todo = list(ROOTS)
	while todo:
		name = todo.pop()
		if name in out:
			continue
		decl = EXTRA_RECORDS.get(name) or pick(name)
		if decl is None:
			print(f"note: no declaration found for {name}")
			continue
		out[name] = decl
		todo += sorted(referenced(decl) - set(out))
	OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
	result = {
		"source": "sp-tarkov/server-csharp",
		"records": {k: out[k] for k in sorted(out) if out[k]["kind"] != "enum"},
		"enums": {k: out[k]["members"] for k in sorted(out) if out[k]["kind"] == "enum"},
	}
	with open(OUT_FILE, "w", encoding="utf-8", newline="\n") as f:
		f.write(compact_json(result))
	print(f"Wrote {len(result['records'])} records and {len(result['enums'])} enums to {OUT_FILE}")


def compact_json(data):
	"""JSON with one line per record property / enum, so diffs stay readable."""
	lines = ["{", f'  "source": {json.dumps(data["source"])},', '  "records": {']
	records = list(data["records"].items())
	for i, (name, decl) in enumerate(records):
		head = {k: v for k, v in decl.items() if k != "properties"}
		lines.append(f"    {json.dumps(name)}: {{")
		for k, v in head.items():
			lines.append(f"      {json.dumps(k)}: {json.dumps(v)},")
		props = list(decl.get("properties", {}).items())
		lines.append('      "properties": {')
		for j, (pname, prop) in enumerate(props):
			lines.append(f"        {json.dumps(pname)}: {json.dumps(prop)}{',' if j < len(props) - 1 else ''}")
		lines.append("      }")
		lines.append("    }" + ("," if i < len(records) - 1 else ""))
	lines.append("  },")
	lines.append('  "enums": {')
	enums = list(data["enums"].items())
	for i, (name, members) in enumerate(enums):
		lines.append(f"    {json.dumps(name)}: {json.dumps(members)}{',' if i < len(enums) - 1 else ''}")
	lines.append("  }")
	lines.append("}")
	return "\n".join(lines) + "\n"


if __name__ == "__main__":
	if len(sys.argv) != 2:
		sys.exit(__doc__)
	main(sys.argv[1])
