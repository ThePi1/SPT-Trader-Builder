"""Subtasks: the steps of a Counter ("In-raid objective") task, in its ``counter.conditions`` list."""

from schema.common import compare_object, compare_text, count, flag, short
from schema.fields import (
	BOOL, CHOICE, GROUPS, IDLIST, INT, ITEM, JSON, LIST, OBJECT, TEXT, Field, Spec,
)

MANAGED = ("conditionType", "id", "dynamicLocale")


def _base(condition_type, **keys):
	item = {"conditionType": condition_type, "dynamicLocale": False, "id": ""}
	item.update(keys)
	return dict(sorted(item.items(), key=lambda kv: kv[0]))


SUBTASKS = {}


def _add(spec):
	SUBTASKS[spec.kind] = spec


_DAYTIME = Field(
	"daytime", "Time of day", OBJECT, advanced=True,
	fields=(Field("from", "From hour", INT, 0, minimum=0, maximum=24), Field("to", "To hour", INT, 0, minimum=0, maximum=24)),
)
_HEALTH_EFFECTS = Field("enemyHealthEffects", "Enemy has effects", JSON, advanced=True)


def _weapon_filters(shots):
	"""The fields Kills and Shots share: what with, on whom, where, how far."""
	return (
		Field("target", "Target", CHOICE, "Savage", choices="kill_targets", open=True),
		Field("savageRole", "Only these enemies", LIST, [], choices="target_roles", open=True),
		Field("weapon", "With weapons", IDLIST, [], ref=ITEM),
		Field("weaponModsInclusive", "Weapon has mods", GROUPS, [], ref=ITEM),
		Field("weaponModsExclusive", "Weapon lacks mods", GROUPS, [], ref=ITEM, advanced=True),
		Field("weaponCaliber", "Caliber", LIST, [], advanced=True),
		Field("bodyPart", "Hit in", LIST, [], choices="body_parts"),
		compare_object("distance", "Distance (m)"),
		_DAYTIME,
		Field("enemyEquipmentInclusive", "Enemy wears", GROUPS, [], ref=ITEM, advanced=True),
		Field("enemyEquipmentExclusive", "Enemy doesn't wear", GROUPS, [], ref=ITEM, advanced=True),
		_HEALTH_EFFECTS,
		Field("resetOnSessionEnd", "Reset at end of raid", BOOL, False, advanced=True),
		Field("compareMethod", "Count is", CHOICE, ">=", choices="compare", advanced=True),
		Field("value", "Count", INT, 0 if not shots else 1, advanced=True, minimum=0),
	)


def _weapon_base(condition_type, value):
	return _base(
		condition_type, bodyPart=[], compareMethod=">=", daytime={"from": 0, "to": 0},
		distance={"compareMethod": ">=", "value": 0}, enemyEquipmentExclusive=[], enemyEquipmentInclusive=[],
		enemyHealthEffects=[], resetOnSessionEnd=False, savageRole=[], target="Savage", value=value, weapon=[],
		weaponCaliber=[], weaponModsExclusive=[], weaponModsInclusive=[],
	)


def _kills_text(item, names):
	target = {"Savage": "Scavs", "AnyPmc": "PMCs", "Any": "anyone", "Usec": "USEC", "Bear": "BEAR"}.get(item.get("target"), item.get("target", ""))
	text = f"Kill {target}"
	roles = item.get("savageRole") or []
	if roles:
		text += f" ({', '.join(roles[:2])}{'...' if len(roles) > 2 else ''})"
	if item.get("weapon"):
		text += f" with {names.items(item['weapon'], 1)}"
	return text


_add(Spec(
	"subtask", "Kills", "Kill enemies", _weapon_filters(False), _weapon_base("Kills", 0),
	timings=("Finish", "Fail"), managed=MANAGED, summary=_kills_text,
	note="Kill a kind of enemy, optionally with a weapon, from a distance, or in a body part.",
))

_add(Spec(
	"subtask", "Shots", "Hit enemies", _weapon_filters(True), _weapon_base("Shots", 1),
	timings=("Finish", "Fail"), managed=MANAGED, summary=lambda item, names: "Hit " + _kills_text(item, names)[5:],
	note="Land shots on a kind of enemy (not necessarily killing them).",
))

_add(Spec(
	"subtask", "VisitPlace", "Visit a place", (Field("target", "Place", TEXT, ""),),
	_base("VisitPlace", target="", value=1),
	timings=("Finish",), managed=MANAGED, summary=lambda item, names: f"Visit {item.get('target', '')}",
	note="Reach a trigger zone on the map.",
))

_add(Spec(
	"subtask", "InZone", "Be in a place", (Field("zoneIds", "Places", LIST, []),),
	_base("InZone", zoneIds=[]),
	timings=("Finish",), managed=MANAGED, summary=lambda item, names: f"In {short(', '.join(item.get('zoneIds', [])), 30)}",
	note="Be inside one of the trigger zones.",
))

_add(Spec(
	"subtask", "Location", "On a map", (Field("target", "Maps", LIST, [], choices="locations", open=True),),
	_base("Location", target=[]),
	timings=("Finish", "Fail"), managed=MANAGED, summary=lambda item, names: f"On {', '.join(item.get('target', []))}",
	note="The raid must be on one of these maps.",
))

_add(Spec(
	"subtask", "ExitStatus", "How the raid ends", (Field("status", "Result", LIST, [], choices="exit_status"),),
	_base("ExitStatus", status=[]),
	timings=("Finish", "Fail"), managed=MANAGED, summary=lambda item, names: f"Raid ends: {', '.join(item.get('status', []))}",
	note="The raid must end in one of these ways.",
))

_add(Spec(
	"subtask", "ExitName", "Leave by an exit", (Field("exitName", "Exit", TEXT, ""),),
	_base("ExitName", exitName=""),
	timings=("Finish",), managed=MANAGED, summary=lambda item, names: f"Exit {item.get('exitName', '')}",
	note="Leave the map through a named exit.",
))

_add(Spec(
	"subtask", "Equipment", "Wear equipment", (
		Field("equipmentInclusive", "Wearing", GROUPS, [], ref=ITEM),
		Field("equipmentExclusive", "Not wearing", GROUPS, [], ref=ITEM, advanced=True),
		Field("IncludeNotEquippedItems", "Count items not worn", BOOL, False, advanced=True),
	),
	_base("Equipment", IncludeNotEquippedItems=False, equipmentExclusive=[], equipmentInclusive=[]),
	timings=("Finish", "Fail"), managed=MANAGED, summary=lambda item, names: "Wear equipment",
	note="Go in wearing certain items. A group needs all of its items, and any one group is enough.",
))

_add(Spec(
	"subtask", "LaunchFlare", "Launch a flare", (Field("target", "Place", TEXT, ""),),
	_base("LaunchFlare", target=""),
	timings=("Finish",), managed=MANAGED, summary=lambda item, names: f"Flare at {item.get('target', '')}",
	note="Fire a flare in a trigger zone.",
))

_add(Spec(
	"subtask", "HealthEffect", "Have a health effect", (
		Field("bodyPartsWithEffects", "Effects on body parts", JSON),
		compare_object("energy", "Energy"),
		compare_object("hydration", "Hydration"),
		compare_object("time", "For (seconds)", 0),
	),
	_base(
		"HealthEffect", bodyPartsWithEffects=[{"bodyParts": [], "effects": []}], energy={"compareMethod": ">=", "value": 0},
		hydration={"compareMethod": ">=", "value": 0}, time={"compareMethod": ">=", "value": 0},
	),
	timings=("Finish",), managed=MANAGED, summary=lambda item, names: "Have a health effect",
	note="Have effects (like bleeding) on body parts for some time.",
))

_add(Spec(
	"subtask", "HealthBuff", "Have a buff", (Field("target", "Buffs", LIST, [], choices="buffs", open=True),),
	_base("HealthBuff", target=[]),
	timings=("Finish",), managed=MANAGED, summary=lambda item, names: f"Buff {', '.join(item.get('target', []))}",
	note="Have a stimulant or other buff active.",
))

# --- rare kinds ---------------------------------------------------------------------------


def _compare_value(condition_type, label, note, value=1, **extra):
	return Spec(
		"subtask", condition_type, label, (
			Field("compareMethod", "Is", CHOICE, ">=", choices="compare"),
			Field("value", "Value", INT, value, minimum=0),
		) + tuple(extra.get("fields", ())),
		_base(condition_type, compareMethod=">=", value=value, **extra.get("base", {})),
		timings=("Finish", "Fail"), managed=MANAGED, everyday=False,
		summary=lambda item, names, label=label: f"{label} {compare_text(item.get('compareMethod'))} {item.get('value')}",
		note=note,
	)


_add(_compare_value("Time", "Raid time", "How long the raid has lasted."))
_add(_compare_value("ArenaMatchPlace", "Arena place", "Finish an Arena match in a place."))
_add(_compare_value("ArenaPlayerInTeamPlace", "Arena place in team", "Place within the team in Arena."))
_add(_compare_value(
	"UseItem", "Use items", "Use items a number of times.",
	fields=(Field("target", "Items", IDLIST, [], ref=ITEM),), base={"target": []},
))
_add(Spec(
	"subtask", "ArenaGameMode", "Arena game mode", (Field("target", "Modes", LIST, [], choices="arena_game_modes", open=True),),
	_base("ArenaGameMode", target=[]),
	timings=("Finish", "Fail"), managed=MANAGED, everyday=False, summary=lambda item, names: f"Arena {', '.join(item.get('target', []))}",
	note="Play an Arena game mode.",
))
_add(Spec(
	"subtask", "ArenaRankingMode", "Arena ranking mode", (Field("target", "Modes", LIST, []),),
	_base("ArenaRankingMode", target=[]),
	timings=("Finish", "Fail"), managed=MANAGED, everyday=False, summary=lambda item, names: "Arena ranking mode",
	note="Play an Arena ranking mode.",
))
_add(Spec(
	"subtask", "UnderArtilleryFire", "Under artillery fire", (),
	_base("UnderArtilleryFire"),
	timings=("Finish",), managed=MANAGED, everyday=False, summary=lambda item, names: "Survive artillery fire",
	note="Be under artillery fire.",
))
