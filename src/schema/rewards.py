"""Rewards: what the player gets, in a quest's ``rewards`` lists.

A reward sits in one of three lists: Success (on completing the quest), Started (when it is
accepted) or Fail (when it fails). Item rewards carry a list of items; an item with parts
(a weapon with mods) is several entries linked by ``parentId`` / ``slotId``.
"""

from schema import choices
from schema.common import short
from schema.fields import (
	ACHIEVEMENT, BOOL, CHOICE, CUSTOMIZATION, INT, JSON, LIST, NUMBER, REF, REWARD_ITEMS, SKILL, TEXT, TRADER, Field, Spec,
)

SUCCESS, STARTED, FAIL = "Success", "Started", "Fail"

UNLOCK_ITEM_HELP = (
	"The item in the assort unlock reward (in the quest JSON) only controls the preview for the item. "
	"The actual assort is stored in the trader assort file, and linked to the quest through the quest assort file."
)

MANAGED = ("type", "id")


def item_count(parts):
	"""How many items an Item reward gives: the stack sizes of its top-level parts added up (a part with no stack counts as 1). The base game
	keeps the reward's "value" equal to this in every one of its item rewards. 0 when there are no parts."""
	known = {p.get("_id") for p in parts if isinstance(p, dict)}
	total = 0
	for part in parts:
		if not isinstance(part, dict) or (part.get("parentId") not in (None, "", "hideout") and part.get("parentId") in known):
			continue
		stack = (part.get("upd") or {}).get("StackObjectsCount", 1) if isinstance(part.get("upd") or {}, dict) else 1
		total += stack if isinstance(stack, (int, float)) and not isinstance(stack, bool) else 1
	return int(total) if total == int(total) else total


def _base(reward_type, **keys):
	item = {
		"availableInGameEditions": [],
		"gameMode": list(choices.DEFAULT_REWARD_GAME_MODES),
		"id": "",
		"isHidden": False,
		"type": reward_type,
		"unknown": False,
	}
	item.update(keys)
	return dict(sorted(item.items(), key=lambda kv: kv[0]))


_COMMON = (
	Field("unknown", "Hidden until earned", BOOL, False, advanced=True),
	Field("isHidden", "Hide in list", BOOL, False, advanced=True),
	Field("gameMode", "Game modes", LIST, ["regular", "pve"], choices="game_modes", open=True, advanced=True),
	Field("availableInGameEditions", "Only for editions", LIST, [], advanced=True),
	Field("index", "Order", INT, 0, advanced=True, minimum=0),
	Field("illustrationConfig", "Picture", JSON, advanced=True),
)

REWARDS = {}


def _add(spec):
	REWARDS[spec.kind] = spec


_add(Spec(
	"reward", "Experience", "Experience", (Field("value", "Experience", INT, 1000, minimum=0),) + _COMMON,
	_base("Experience", value=1000),
	vanilla_timing_use=(SUCCESS,), managed=MANAGED, summary=lambda item, names: f"Experience {item.get('value')}",
	note="Experience points.",
))

_add(Spec(
	"reward", "TraderStanding", "Trader standing", (
		Field("target", "Trader", REF, ref=TRADER, required=True),
		Field("value", "Standing", NUMBER, 0.02),
	) + _COMMON,
	_base("TraderStanding", target="", value=0.02),
	vanilla_timing_use=(SUCCESS, FAIL), managed=MANAGED,
	summary=lambda item, names: f"{names.trader(item.get('target', ''))} standing {item.get('value')}",
	note="Standing with a trader. Can be negative.",
))

_add(Spec(
	"reward", "Skill", "Skill points", (
		Field("target", "Skill", CHOICE, "Sniper", choices="skills", open=True, required=True),
		Field("value", "Points", INT, 100, minimum=0),
	) + _COMMON,
	_base("Skill", target="Sniper", value=100),
	vanilla_timing_use=(SUCCESS,), managed=MANAGED,
	summary=lambda item, names: f"{item.get('target')} +{item.get('value')}",
	note="Skill points (100 is one level).",
))

_add(Spec(
	"reward", "Item", "Items", (
		Field("items", "Items", REWARD_ITEMS, required=True),
		Field("findInRaid", "Found in raid", BOOL, True),
		Field("target", "Main item id", REF, advanced=True),
		Field("isEncoded", "Encoded", BOOL, False, advanced=True),
	) + _COMMON,
	_base("Item", findInRaid=True, isEncoded=False, items=[], target="", value=1),
	vanilla_timing_use=(SUCCESS, STARTED), managed=MANAGED + ("value",),  # (value follows the stack sizes: see item_count)
	summary=lambda item, names: f"{item.get('value', 1)}x {_main_item_name(item, names)}",
	note="Items given to the player. A weapon with mods is one item made of several parts.",
))

_add(Spec(
	"reward", "AssortmentUnlock", "Assort unlock", (
		Field("traderId", "Trader", REF, ref=TRADER, required=True),
		Field("loyaltyLevel", "Trader level", INT, 1, minimum=1, maximum=4),
		Field("items", "Item", REWARD_ITEMS, required=True, help=UNLOCK_ITEM_HELP),
		Field("target", "Main item id", REF, advanced=True),
	) + _COMMON,
	_base("AssortmentUnlock", items=[], loyaltyLevel=1, target="", traderId=""),
	vanilla_timing_use=(SUCCESS, STARTED), managed=MANAGED,
	summary=lambda item, names: f"Unlock {_main_item_name(item, names)} at {names.trader(item.get('traderId', ''))}",
	note="Lets the player buy an item from a trader. The trader's assort must have the item.",
))

_add(Spec(
	"reward", "TraderUnlock", "Trader unlock", (Field("target", "Trader", REF, ref=TRADER, required=True),) + _COMMON,
	_base("TraderUnlock", target=""),
	vanilla_timing_use=(SUCCESS,), managed=MANAGED, summary=lambda item, names: f"Unlock {names.trader(item.get('target', ''))}",
	note="Makes a locked trader available.",
))

_add(Spec(
	"reward", "Achievement", "Achievement", (Field("target", "Achievement", REF, ref=ACHIEVEMENT, required=True),) + _COMMON,
	_base("Achievement", target=""),
	vanilla_timing_use=(SUCCESS,), managed=MANAGED, summary=lambda item, names: f"Achievement {short(item.get('target', ''), 12)}",
	note="Gives an achievement.",
))

_add(Spec(
	"reward", "StashRows", "Stash rows", (Field("value", "Rows", INT, 1, minimum=1),) + _COMMON,
	_base("StashRows", value=1),
	vanilla_timing_use=(), managed=MANAGED, common=False, summary=lambda item, names: f"Stash +{item.get('value')} rows",
	note="Makes the stash taller.",
))

# --- less common kinds ---------------------------------------------------------------------------

_add(Spec(
	"reward", "ProductionScheme", "Hideout recipe", (
		Field("target", "Recipe item", REF, required=True),
		Field("loyaltyLevel", "Level", INT, 1, minimum=1),
		Field("traderId", "Workbench", INT, 10),
		Field("items", "Item", REWARD_ITEMS),
	) + _COMMON,
	_base("ProductionScheme", items=[], loyaltyLevel=1, target="", traderId=10),
	vanilla_timing_use=(SUCCESS, STARTED), managed=MANAGED, common=False,
	summary=lambda item, names: f"Hideout recipe {_main_item_name(item, names)}",
	note="Unlocks a hideout crafting recipe. traderId is a hideout area number here, not a trader.",
))

_add(Spec(
	"reward", "CustomizationDirect", "Clothing or customization", (Field("target", "Item", REF, ref=CUSTOMIZATION, required=True),) + _COMMON,
	_base("CustomizationDirect", target=""),
	vanilla_timing_use=(SUCCESS,), managed=MANAGED, common=False, summary=lambda item, names: f"Customization {short(item.get('target', ''), 12)}",
	note="Gives a clothing or customization item.",
))

_add(Spec(
	"reward", "TraderStandingRestore", "Restore trader standing (unused)", (
		Field("target", "Trader", REF, ref=TRADER), Field("value", "Value", NUMBER, 0),
	) + _COMMON,
	_base("TraderStandingRestore", target="", value=0),
	vanilla_timing_use=(SUCCESS,), managed=MANAGED, common=False,
	summary=lambda item, names: f"Restore {names.trader(item.get('target', ''))} standing",
	note="Sets a trader's standing to a specific value. This is only used once in SPT - for Make Amends, a Mechanic / Lightkeeper quest. SPT server code itself says it's not implemented, so I would not suggest using this.",
))

_add(Spec(
	"reward", "Pockets", "Pockets", (Field("target", "Pockets item", REF),) + _COMMON,
	_base("Pockets", target=""),
	vanilla_timing_use=(SUCCESS,), managed=MANAGED, common=False, summary=lambda item, names: "Pockets",
	note="Gives a pockets upgrade.",
))

_add(Spec(
	"reward", "NotificationPopup", "Pop-up message", (Field("message", "Message id", TEXT, ""),) + _COMMON,
	_base("NotificationPopup", message=""),
	vanilla_timing_use=(SUCCESS,), managed=MANAGED, common=False, summary=lambda item, names: "Pop-up message",
	fresh_ids=("message",),
	note="Shows a pop-up message.",
))

_add(Spec(
	"reward", "WebPromoCode", "Promo code", _COMMON, _base("WebPromoCode"),
	vanilla_timing_use=(SUCCESS,), managed=MANAGED, common=False, summary=lambda item, names: "Promo code",
	note="Gives a web promo code.",
))


def _main_item_name(reward, names):
	"""The name of the item a reward gives: its target part, else the first part."""
	items = reward.get("items") or []
	target = reward.get("target")
	for part in items:
		if part.get("_id") == target:
			return names.item(part.get("_tpl", ""))
	return names.item(items[0].get("_tpl", "")) if items else "(nothing)"


# --- the items inside Item / AssortmentUnlock rewards ----------------------------------------

REWARD_ITEM = Spec(
	"reward_item", "reward_item", "Item part", (
		Field("_tpl", "Item", REF, ref="item", required=True),
		Field("upd.StackObjectsCount", "Stack size", INT, 1, minimum=1),
		Field("upd.SpawnedInSession", "Found in raid", BOOL, True),
		Field("location", "Position in container", INT, advanced=True),
	),
	{"_id": "", "_tpl": ""},
	managed=("_id", "parentId", "slotId"), summary=lambda item, names: names.item(item.get("_tpl", "")),
	note="One entry of an item. A part with parentId and slotId hangs off another part.",
)
