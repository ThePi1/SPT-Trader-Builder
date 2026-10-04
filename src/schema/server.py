"""Can the SPT server load this? Checks a value against the server's own C# models.

The models are read from server_models.json (made by tools/extract_server_models.py from the
server's source). The rules follow how the server reads JSON (System.Text.Json plus SPT's
converters):

- a ``required`` key that is missing, or a value of the wrong type, stops the file loading (error);
- a key the model doesn't have is dropped without a word (warning: it does nothing);
- a number may be written as text only where the model allows it (``StringToNumberFactoryConverter``);
- an enum value may be its name (any case) or its number;
- an id (``MongoId``) must be 24 hex characters.
"""

import json
from functools import lru_cache
from pathlib import Path

from schema.issues import ERROR, WARNING, Issue

MODELS_FILE = Path(__file__).resolve().parent / "server_models.json"

# Types the server reads without a null check on our side mattering (reference types)
_REFERENCE_TYPES = {"string", "object", "List", "HashSet", "IEnumerable", "ListOrT", "Dictionary", "IList", "ISet", "ICollection"}
_INTEGER_TYPES = {"int", "long", "short", "byte"}
_FLOAT_TYPES = {"double", "float", "decimal"}
_LIST_TYPES = {"List", "HashSet", "IEnumerable", "IList", "ISet", "ICollection", "IReadOnlyList"}
_NUMBER_AS_TEXT = "StringToNumberFactoryConverter"


@lru_cache(maxsize=1)
def models():
	with open(MODELS_FILE, encoding="utf-8") as f:
		return json.load(f)


def record(name):
	return models()["records"][name]


def enum(name):
	return models()["enums"].get(name)


# --- type expressions ("Dictionary<string, List<Reward>>?") --------------------------------


@lru_cache(maxsize=None)
def parse_type(text):
	"""(name, [argument types], nullable). "List<int?>?" -> ("List", [("int", [], True)], True)."""
	text = text.strip()
	nullable = text.endswith("?")
	if nullable:
		text = text[:-1].strip()
	if text.endswith("[]"):
		return ("List", [parse_type(text[:-2])], nullable)
	if "<" not in text:
		return (text, [], nullable)
	name, rest = text.split("<", 1)
	inner = rest[: rest.rindex(">")]
	args, depth, current = [], 0, ""
	for ch in inner:
		if ch == "," and depth == 0:
			args.append(current)
			current = ""
			continue
		depth += ch == "<"
		depth -= ch == ">"
		current += ch
	args.append(current)
	return (name.strip(), [parse_type(a) for a in args], nullable)


# --- checking --------------------------------------------------------------------------


def check(value, type_text, path=(), converter=None):
	"""Every problem the server would have reading value as type_text, as a list of Issues."""
	issues = []
	_check(value, parse_type(type_text), tuple(path), converter, issues)
	return issues


def check_record(value, name, path=()):
	issues = []
	_check_record(value, name, tuple(path), issues)
	return issues


def describe(json_value):
	if json_value is None:
		return "empty (null)"
	if isinstance(json_value, bool):
		return "true/false"
	if isinstance(json_value, (int, float)):
		return "a number"
	if isinstance(json_value, str):
		return "text"
	if isinstance(json_value, list):
		return "a list"
	return "an object"


def _id_message(value):
	if value == "":
		return "This is empty. It needs an id (24 characters: 0-9 and a-f)."
	return f"'{value}' isn't a valid id. It should be 24 characters, using 0-9 and a-f."


def _bad(issues, path, expected, value):
	issues.append(Issue(ERROR, path, f"Must be {expected}, not {describe(value)}."))


def _check(value, parsed, path, converter, issues):
	name, args, nullable = parsed
	if value is None:
		if not nullable and name not in _REFERENCE_TYPES and enum(name) is None and name not in models()["records"]:
			issues.append(Issue(ERROR, path, "Can't be empty (null)."))
		return
	if name == "object":
		return
	if name == "string":
		if not isinstance(value, str):
			_bad(issues, path, "text", value)
	elif name == "bool":
		if not isinstance(value, bool):
			_bad(issues, path, "true or false", value)
	elif name in _INTEGER_TYPES or name in _FLOAT_TYPES:
		_check_number(value, name in _INTEGER_TYPES, path, converter, issues)
	elif name == "MongoId":
		if not isinstance(value, str):
			_bad(issues, path, "an id (text)", value)
		elif not _is_id(value):
			issues.append(Issue(ERROR, path, _id_message(value)))
	elif name in _LIST_TYPES:
		if not isinstance(value, list):
			_bad(issues, path, "a list", value)
			return
		for i, item in enumerate(value):
			_check(item, args[0], path + (i,), None, issues)
	elif name == "ListOrT":
		if isinstance(value, list):
			for i, item in enumerate(value):
				_check(item, args[0], path + (i,), None, issues)
		else:
			_check(value, args[0], path, None, issues)
	elif name in ("Dictionary", "IDictionary", "IReadOnlyDictionary"):
		if not isinstance(value, dict):
			_bad(issues, path, "an object", value)
			return
		key_type = args[0]
		for key, item in value.items():
			if key_type[0] == "MongoId" and not _is_id(key):
				issues.append(Issue(ERROR, path + (key,), _id_message(key)))
			elif enum(key_type[0]) is not None and not _enum_ok(key, key_type[0]):
				issues.append(Issue(ERROR, path + (key,), f"'{key}' is not one of: {', '.join(enum(key_type[0]))}."))
			_check(item, args[1], path + (key,), None, issues)
	elif enum(name) is not None:
		if not _enum_ok(value, name):
			issues.append(Issue(ERROR, path, f"'{value}' is not one of: {', '.join(enum(name))}."))
	elif name in models()["records"]:
		_check_record(value, name, path, issues)
	# (an unknown type name: nothing we can check)


def _check_number(value, integer, path, converter, issues):
	if isinstance(value, bool):
		_bad(issues, path, "a number", value)
		return
	if isinstance(value, str):
		if converter != _NUMBER_AS_TEXT:
			_bad(issues, path, "a number", value)
			return
		text = value.strip()
		if not text:
			return  # (read as empty)
		try:
			number = float(text)
		except ValueError:
			issues.append(Issue(WARNING, path, f"'{value}' is not a number; SPT reads it as empty."))
			return
		if integer and not number.is_integer():
			issues.append(Issue(WARNING, path, f"'{value}' is not a whole number; SPT reads it as empty."))
		return
	if not isinstance(value, (int, float)):
		_bad(issues, path, "a number", value)
	elif integer and isinstance(value, float) and not value.is_integer():
		_bad(issues, path, "a whole number", value)
	elif integer and isinstance(value, float):
		_bad(issues, path, "a whole number written without a decimal point", value)


def _check_record(value, name, path, issues):
	decl = record(name)
	if decl.get("kind") == "dictionary":
		_check(value, parse_type(decl["type"]), path, None, issues)
		return
	if not isinstance(value, dict):
		_bad(issues, path, "an object", value)
		return
	props = decl["properties"]
	for key, prop in props.items():
		if prop["required"] and key not in value:
			issues.append(Issue(ERROR, path + (key,), f"Missing '{key}' (SPT needs it)."))
	for key, item in value.items():
		prop = props.get(key)
		if prop is None:
			issues.append(Issue(WARNING, path + (key,), f"SPT doesn't use '{key}'; it is ignored."))
			continue
		_check(item, parse_type(prop["type"]), path + (key,), prop.get("converter"), issues)


def _is_id(text):
	return isinstance(text, str) and len(text) == 24 and all(c in "0123456789abcdefABCDEF" for c in text)


def _enum_ok(value, name):
	members = enum(name)
	if isinstance(value, bool):
		return False
	if isinstance(value, int):
		return True  # (a number is accepted as it is)
	if isinstance(value, str):
		if value.lstrip("-").isdigit():
			return True
		return value.lower() in {m.lower() for m in members}
	return False
