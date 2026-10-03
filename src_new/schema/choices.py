"""The lists behind dropdowns. A list is a tuple of (value, label) pairs.

Lists the game defines (quest types, ...) come from the server's models; lists the old app
kept come from data/choices.json; names (traders, locations) come from the game data when
it is given. Every list is "open" in the forms where vanilla uses values the list lacks.
"""

import json
from functools import lru_cache

from core.paths import DATA_DIR
from schema import server

COMPARE = (
	(">=", "at least"),
	("<=", "at most"),
	(">", "more than"),
	("<", "less than"),
	("==", "exactly"),
)

TASK_TIMINGS = (
	("Start", "AvailableForStart"),
	("Finish", "AvailableForFinish"),
	("Fail", "Fail"),
)
REWARD_TIMINGS = (
	("Success", "Success"),
	("Started", "Started"),
	("Fail", "Fail"),
)
TASK_LIST_KEY = dict(TASK_TIMINGS)  # "Finish" -> "AvailableForFinish"
TASK_TIMING_OF = {v: k for k, v in TASK_TIMINGS}

SIDES = (("Pmc", "Any"), ("Bear", "BEAR"), ("Usec", "USEC"))

QUEST_STATUS = (
	(0, "Locked"),
	(1, "Available to start"),
	(2, "Started"),
	(3, "Ready to hand in"),
	(4, "Completed"),
	(5, "Failed"),
	(6, "Failed, can restart"),
	(7, "Marked as failed"),
	(8, "Expired"),
	(9, "Available after a delay"),
)

KILL_TARGETS = (
	("Savage", "Scavs"),
	("AnyPmc", "Any PMC"),
	("Usec", "USEC"),
	("Bear", "BEAR"),
	("Any", "Anyone"),
)

EXIT_STATUS = (
	("Survived", "Survived"),
	("Killed", "Killed"),
	("Left", "Left"),
	("Runner", "Runner"),
	("MissingInAction", "Missing in action"),
	("Transit", "Transit"),
)

BODY_PARTS = tuple((v, v) for v in ("Head", "Chest", "Stomach", "LeftArm", "RightArm", "LeftLeg", "RightLeg"))

LOYALTY_LEVELS = tuple((n, str(n)) for n in (1, 2, 3, 4))

ARENA_GAME_MODES = tuple((v, v) for v in ("CheckPoint", "BlastGang", "TeamFight", "LastHero"))

# What a quest's kind of objective is called in the game (QuestTypeEnum)
QUEST_TYPES = tuple((v, v) for v in server.enum("QuestTypeEnum"))

AVAILABLE_GAME_MODES = tuple((v, v) for v in ("regular", "pve"))

# Vanilla's own "gameMode" for a reward
DEFAULT_REWARD_GAME_MODES = ["regular", "pve"]


@lru_cache(maxsize=1)
def _choices_json():
	with open(DATA_DIR / "choices.json", encoding="utf-8") as f:
		return json.load(f)


def _pairs(values):
	return tuple((v, v) for v in values)


def skills():
	return _pairs(_choices_json()["default_skills"] + ["Search"])


def target_roles():
	return _pairs(sorted(set(_choices_json()["tb_elim_box_targetrole"]) | _VANILLA_ROLES))


def effects():
	return _pairs(_choices_json()["tb_effect"])


def buffs():
	return _pairs(_choices_json()["tb_buff"])


def mod_slots():
	return _pairs(_choices_json()["ab_box_modslot"])


# savageRole values vanilla uses that the old app's list lacks (found by comparing with the quests)
_VANILLA_ROLES = {
	"assault", "marksman", "savage", "infectedAssault", "infectedCivil", "infectedLaborant", "infectedPmc",
	"infectedTagilla", "sectantOni", "sectantPrizrak", "sectantPredvestnik", "followerTagilla",
	"followerStormtrooper", "followerGluharSnipe", "cursedAssault", "arenaFighterEvent",
}

_STATIC = {
	"compare": COMPARE,
	"sides": SIDES,
	"quest_status": QUEST_STATUS,
	"kill_targets": KILL_TARGETS,
	"exit_status": EXIT_STATUS,
	"body_parts": BODY_PARTS,
	"loyalty_levels": LOYALTY_LEVELS,
	"arena_game_modes": ARENA_GAME_MODES,
	"quest_types": QUEST_TYPES,
	"game_modes": AVAILABLE_GAME_MODES,
}
_DYNAMIC = {
	"skills": skills,
	"target_roles": target_roles,
	"effects": effects,
	"buffs": buffs,
	"mod_slots": mod_slots,
}


def get(name, gamedata=None):
	"""The (value, label) pairs of a named list. traders and locations need gamedata."""
	if name in _STATIC:
		return _STATIC[name]
	if name in _DYNAMIC:
		return _DYNAMIC[name]()
	if name == "traders":
		names = gamedata.traders if gamedata is not None else {}
		return tuple((trader_id, name) for trader_id, name in names.items())
	if name == "locations":
		names = gamedata.locations if gamedata is not None else {"any": "Any"}
		return tuple(names.items())
	raise KeyError(f"No choice list named {name!r}")


def resolve(choices, gamedata=None):
	"""A Field.choices (a list name, or pairs / plain values) as (value, label) pairs."""
	if isinstance(choices, str):
		return get(choices, gamedata)
	return tuple(c if isinstance(c, tuple) else (c, str(c)) for c in choices)


def label_of(choices, value, gamedata=None):
	for v, label in resolve(choices, gamedata):
		if v == value:
			return label
	return str(value)
