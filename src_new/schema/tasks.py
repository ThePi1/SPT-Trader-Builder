"""Tasks: the things a quest asks for (conditions in the quest JSON).

A task sits in one of three lists of the quest: Start (needed before the quest can start),
Finish (needed to complete it) or Fail (makes the quest fail). A Counter task holds its own
list of subtasks (see subtasks.py).
"""

from schema import choices
from schema.common import PLAIN, compare_text, count, flag, short
from schema.fields import (
	BOOL, CHOICE, IDLIST, INT, ITEM, LIST, NUMBER, QUEST, REF, SKILL, TASK, TEXT, TRADER, VISIBILITY,
	Field, Spec,
)

START, FINISH, FAIL = "Start", "Finish", "Fail"
ANY_TIMING = (FINISH, START, FAIL)

# Keys every task has; the app fills them in
MANAGED = ("conditionType", "id", "dynamicLocale", "globalQuestCounterId")


def _base(condition_type, **keys):
	"""A new task with the keys vanilla writes, in vanilla's order (alphabetical)."""
	item = {
		"conditionType": condition_type,
		"dynamicLocale": False,
		"globalQuestCounterId": "",
		"id": "",
		"index": 0,
		"parentId": "",
		"visibilityConditions": [],
	}
	item.update(keys)
	return dict(sorted(item.items(), key=lambda kv: kv[0]))


_VISIBLE = Field("visibilityConditions", "Only show after", VISIBILITY)
_LINKED = Field("parentId", "Linked task", REF, ref=TASK, advanced=True)
_ORDER = Field("index", "Order", INT, 0, advanced=True, minimum=0)


def _item_fields(extra=()):
	return (
		Field("target", "Items", IDLIST, ref=ITEM, required=True),
		Field("value", "How many", INT, 1, minimum=1),
		Field("onlyFoundInRaid", "Found in raid only", BOOL, False),
		Field("minDurability", "Lowest condition", INT, 0, advanced=True, minimum=0, maximum=100),
		Field("maxDurability", "Highest condition", INT, 100, advanced=True, minimum=0, maximum=100),
		Field("dogtagLevel", "Dog tag level", INT, 0, advanced=True, minimum=0),
		Field("isEncoded", "Encoded", BOOL, False, advanced=True),
	) + tuple(extra) + (_VISIBLE, _LINKED, _ORDER)


def _find(item, names):
	return f"Find {item.get('value', 1)}x {names.items(item.get('target', []))}"


def _hand_over(item, names):
	return f"Hand over {item.get('value', 1)}x {names.items(item.get('target', []))}"


def _counter(item, names):
	kind = item.get("type", "")
	return f"Counter: {kind} x{item.get('value', 1)}" if kind else f"Counter x{item.get('value', 1)}"


TASKS = {}


def _add(spec):
	TASKS[spec.kind] = spec


_add(Spec(
	"task", "CounterCreator", "In-raid objective", (
		Field("type", "Kind", CHOICE, "Elimination", choices="quest_types", open=True),
		Field("value", "How many", INT, 1, minimum=0),
		Field("oneSessionOnly", "In one raid", BOOL, False),
		Field("isResetOnConditionFailed", "Reset if failed", BOOL, False, advanced=True),
		Field("isNecessary", "Required", BOOL, False, advanced=True),
		Field("doNotResetIfCounterCompleted", "Keep when done", BOOL, False, advanced=True),
		Field("completeInSeconds", "Time limit (seconds)", INT, 0, advanced=True, minimum=0),
		Field("globalQuestCounterId", "Shared counter", TEXT, "", advanced=True),
		_VISIBLE, _LINKED, _ORDER,
	),
	_base(
		"CounterCreator", completeInSeconds=0, counter={"conditions": [], "id": ""}, doNotResetIfCounterCompleted=False,
		isNecessary=False, isResetOnConditionFailed=False, oneSessionOnly=False, type="Elimination", value=1,
	),
	timings=(FINISH, FAIL), managed=("conditionType", "id", "dynamicLocale", "counter"), summary=_counter,
	fresh_ids=("counter.id",),
	note="Something to do during a raid: kill, visit a place, survive. The steps are its subtasks.",
))

_add(Spec(
	"task", "HandoverItem", "Hand over items", _item_fields(),
	_base(
		"HandoverItem", dogtagLevel=0, isEncoded=False, maxDurability=100, minDurability=0, onlyFoundInRaid=False,
		target=[], value=1,
	),
	timings=(FINISH,), managed=MANAGED, summary=_hand_over,
	note="Give items to the trader.",
))

_add(Spec(
	"task", "FindItem", "Find items", _item_fields(),
	_base(
		"FindItem", countInRaid=False, dogtagLevel=0, isEncoded=False, maxDurability=100, minDurability=0,
		onlyFoundInRaid=False, target=[], value=1,
	),
	timings=(FINISH,), managed=MANAGED, summary=_find,
	note="Have items in the stash or found in raid.",
))

_add(Spec(
	"task", "LeaveItemAtLocation", "Place items", _item_fields((
		Field("zoneId", "Place", TEXT, ""),
		Field("plantTime", "Time to place (seconds)", INT, 10, minimum=0),
	)),
	_base(
		"LeaveItemAtLocation", dogtagLevel=0, isEncoded=False, maxDurability=100, minDurability=0, onlyFoundInRaid=False,
		plantTime=10, target=[], value=1, zoneId="",
	),
	timings=(FINISH, FAIL), managed=MANAGED,
	summary=lambda item, names: f"Place {item.get('value', 1)}x {names.items(item.get('target', []))}",
	note="Put items down at a spot on a map.",
))

_add(Spec(
	"task", "PlaceBeacon", "Place a marker", (
		Field("target", "Marker items", IDLIST, ref=ITEM, required=True),
		Field("zoneId", "Place", TEXT, ""),
		Field("plantTime", "Time to place (seconds)", INT, 30, minimum=0),
		Field("value", "How many", INT, 1, minimum=1, advanced=True),
		_VISIBLE, _LINKED, _ORDER,
	),
	_base("PlaceBeacon", plantTime=30, target=["5991b51486f77447b112d44f"], value=1, zoneId=""),
	timings=(FINISH,), managed=MANAGED,
	summary=lambda item, names: f"Place {names.items(item.get('target', []))}",
	note="Plant a marker or radio repeater at a spot on a map.",
))

_add(Spec(
	"task", "Level", "Player level", (
		Field("compareMethod", "Level is", CHOICE, ">=", choices="compare"),
		Field("value", "Level", INT, 1, minimum=1),
		_ORDER,
	),
	_base("Level", compareMethod=">=", value=1),
	timings=(START,), managed=MANAGED,
	summary=lambda item, names: f"Level {compare_text(item.get('compareMethod'))} {item.get('value')}",
	note="The player must be at this level.",
))

_add(Spec(
	"task", "Quest", "Another quest", (
		Field("target", "Quest", REF, ref=QUEST, required=True),
		Field("status", "Must be", LIST, [4], choices="quest_status"),
		Field("availableAfter", "Wait (seconds)", INT, 0, minimum=0),
		Field("dispersion", "Random extra wait (seconds)", INT, 0, advanced=True, minimum=0),
		_LINKED, _ORDER,
	),
	_base("Quest", availableAfter=0, dispersion=0, status=[4], target=""),
	timings=(START, FINISH, FAIL), managed=MANAGED,
	summary=lambda item, names: f"Quest {names.quest(item.get('target', ''))}: {_status_text(item.get('status'))}",
	note="Another quest must be in a given state, such as completed.",
))


def _status_text(status):
	labels = dict(choices.QUEST_STATUS)
	return ", ".join(labels.get(s, str(s)) for s in (status or []))


_add(Spec(
	"task", "TraderLoyalty", "Trader level", (
		Field("target", "Trader", REF, ref=TRADER, required=True),
		Field("compareMethod", "Level is", CHOICE, ">=", choices="compare"),
		Field("value", "Level", INT, 2, minimum=1, maximum=4),
		_VISIBLE, _ORDER,
	),
	_base("TraderLoyalty", compareMethod=">=", target="", value=2),
	timings=(FINISH, START), managed=MANAGED,
	summary=lambda item, names: f"{names.trader(item.get('target', ''))} level {compare_text(item.get('compareMethod'))} {item.get('value')}",
	note="A trader's loyalty level must reach this.",
))

_add(Spec(
	"task", "TraderStanding", "Trader standing", (
		Field("target", "Trader", REF, ref=TRADER, required=True),
		Field("compareMethod", "Standing is", CHOICE, ">=", choices="compare"),
		Field("value", "Standing", NUMBER, 0),
		_ORDER,
	),
	_base("TraderStanding", compareMethod=">=", target="", value=0),
	timings=(START, FINISH, FAIL), managed=MANAGED,
	summary=lambda item, names: f"{names.trader(item.get('target', ''))} standing {compare_text(item.get('compareMethod'))} {item.get('value')}",
	note="A trader's standing must reach this.",
))

_add(Spec(
	"task", "Skill", "Skill level", (
		Field("target", "Skill", CHOICE, "Sniper", choices="skills", open=True, required=True),
		Field("compareMethod", "Level is", CHOICE, ">=", choices="compare"),
		Field("value", "Level", INT, 1, minimum=1),
		_VISIBLE, _ORDER,
	),
	_base("Skill", compareMethod=">=", target="Sniper", value=1),
	timings=(FINISH,), managed=MANAGED,
	summary=lambda item, names: f"{item.get('target')} {compare_text(item.get('compareMethod'))} {item.get('value')}",
	note="A skill must reach this level.",
))

# --- less common kinds ---------------------------------------------------

_add(Spec(
	"task", "SellItemToTrader", "Sell items to a trader", _item_fields((
		Field("traderId", "Trader", REF, ref=TRADER),
	)),
	_base(
		"SellItemToTrader", dogtagLevel=0, isEncoded=False, maxDurability=100, minDurability=0, onlyFoundInRaid=False,
		target=[], traderId="", value=1,
	),
	timings=(FINISH,), managed=MANAGED, common=False,
	summary=lambda item, names: f"Sell {item.get('value', 1)} roubles' worth to {names.trader(item.get('traderId', ''))}",
	note="Sell items to a trader for a total amount.",
))

_VALUE_OBJECT_KEYS = (
	"baseAccuracy", "durability", "effectiveDistance", "emptyTacticalSlot", "ergonomics", "height",
	"magazineCapacity", "muzzleVelocity", "recoil", "weight", "width",
)


def _weapon_fields():
	from schema.common import compare_object

	labels = {
		"baseAccuracy": "Accuracy", "durability": "Condition", "effectiveDistance": "Effective distance",
		"emptyTacticalSlot": "Empty tactical slots", "ergonomics": "Ergonomics", "height": "Height",
		"magazineCapacity": "Magazine size", "muzzleVelocity": "Muzzle speed", "recoil": "Recoil",
		"weight": "Weight", "width": "Width",
	}
	return (
		Field("target", "Weapons", IDLIST, ref=ITEM),
		Field("containsItems", "Must include", IDLIST, ref=ITEM),
		Field("hasItemFromCategory", "Must include one from", IDLIST, ref=ITEM),
	) + tuple(compare_object(key, labels[key]) for key in _VALUE_OBJECT_KEYS)


def _weapon_assembly_base():
	value = {"compareMethod": ">=", "value": 0}
	keys = {key: dict(value) for key in _VALUE_OBJECT_KEYS}
	return _base("WeaponAssembly", containsItems=[], hasItemFromCategory=[], target=[], value=1, **keys)


_add(Spec(
	"task", "WeaponAssembly", "Build a weapon", _weapon_fields(), _weapon_assembly_base(),
	timings=(FINISH,), managed=MANAGED, common=False,
	summary=lambda item, names: f"Build {names.items(item.get('target', []))}",
	note="Hand in a weapon built to a set of requirements.",
))

_add(Spec(
	"task", "HideoutArea", "Hideout area", (
		Field("areaType", "Area", INT, 0, minimum=0),
		Field("compareMethod", "Level is", CHOICE, ">=", choices="compare"),
		Field("value", "Level", INT, 1, minimum=0),
		_ORDER,
	),
	_base("HideoutArea", areaType=0, compareMethod=">=", value=1),
	timings=(FINISH,), managed=MANAGED, common=False,
	summary=lambda item, names: f"Hideout area {item.get('areaType')} level {compare_text(item.get('compareMethod'))} {item.get('value')}",
	note="A hideout area must reach a level.",
))

_add(Spec(
	"task", "GlobalVariableValue", "Game variable", (
		Field("target", "Variable", TEXT, ""),
		Field("compareMethod", "Is", CHOICE, "==", choices="compare"),
		Field("value", "Value", NUMBER, 1),
		_ORDER,
	),
	_base("GlobalVariableValue", compareMethod="==", target="", value=1),
	timings=(FINISH,), managed=MANAGED, common=False,
	summary=lambda item, names: f"Game variable {short(item.get('target', ''), 12)} {compare_text(item.get('compareMethod'))} {item.get('value')}",
	note="A value the game keeps must match.",
))

_add(Spec(
	"task", "VisitPlace", "Visit a place", (
		Field("target", "Place", TEXT, ""),
		Field("value", "How many", INT, 1, minimum=0),
		_LINKED, _ORDER,
	),
	_base("VisitPlace", target="", value=1),
	timings=(FINISH,), managed=MANAGED, common=False,
	summary=lambda item, names: f"Visit {item.get('target')}",
	note="Visit a place (used outside a raid counter by a few quests).",
))
