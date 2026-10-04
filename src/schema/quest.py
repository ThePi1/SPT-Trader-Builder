"""A quest: its own keys. Tasks, rewards and text are described in tasks.py, rewards.py and locale.py."""

from core.ids import new_id
from schema.fields import BOOL, CHOICE, INT, JSON, LIST, REF, TEXT, TRADER, Field, Spec
from schema.locale import QUEST_TEXT_KEYS, quest_key

DEFAULT_ICON = "/files/quest/icon/6137505384aedf00fa17b651.jpg"

# Keys that point at the quest's locale text: always "<quest id> <key>"
TEXT_POINTER_KEYS = QUEST_TEXT_KEYS

QUEST_FIELDS = (
	Field("QuestName", "Name (for you)", TEXT, "New quest", required=True),
	Field("traderId", "Trader", REF, ref=TRADER, required=True),
	Field("location", "Map", CHOICE, "any", choices="locations", open=True, required=True),
	Field("type", "Kind", CHOICE, "Completion", choices="quest_types", open=True, required=True),
	Field("side", "Available to", CHOICE, "Pmc", choices="sides", open=True, required=True),
	Field("image", "Icon", TEXT, DEFAULT_ICON, required=True),
	Field("restartable", "Can be redone", BOOL, False),
	Field("secretQuest", "Secret", BOOL, False),
	Field("instantComplete", "Completes at once", BOOL, False, advanced=True),
	Field("canShowNotificationsInGame", "Show notifications", BOOL, True, advanced=True),
	Field("isKey", "Key quest", BOOL, False, advanced=True),
	Field("status", "Starting state", INT, 0, advanced=True, minimum=0),
	Field("gameModes", "Arena game modes", LIST, [], advanced=True),
	Field("progressSource", "Progress source", CHOICE, "eft", choices=("eft", "arena"), open=True, advanced=True),
	Field("acceptanceAndFinishingSource", "Accepted and finished in", CHOICE, "eft", choices=("eft", "arena"), open=True, advanced=True),
	Field("arenaLocations", "Arena maps", LIST, [], advanced=True),
	Field("rankingModes", "Arena ranking modes", LIST, [], advanced=True),
	Field("dialogueId", "Dialogue id", TEXT, "", advanced=True),
)

# A new quest: the keys most of the base game's quests have, in their order (alphabetical)
BASE = {
	"QuestName": "New quest",
	"_id": "",
	"acceptPlayerMessage": "",
	"acceptanceAndFinishingSource": "eft",
	"arenaLocations": [],
	"canShowNotificationsInGame": True,
	"changeQuestMessageText": "",
	"completePlayerMessage": "",
	"conditions": {"AvailableForFinish": [], "AvailableForStart": [], "Fail": []},
	"declinePlayerMessage": "",
	"description": "",
	"failMessageText": "",
	"gameModes": [],
	"image": DEFAULT_ICON,
	"instantComplete": False,
	"isKey": False,
	"location": "any",
	"name": "",
	"note": "",
	"progressSource": "eft",
	"rankingModes": [],
	"restartable": False,
	"rewards": {"Fail": [], "Started": [], "Success": []},
	"secretQuest": False,
	"side": "Pmc",
	"startedMessageText": "",
	"status": 0,
	"successMessageText": "",
	"traderId": "",
	"type": "Completion",
}

QUEST = Spec(
	"quest", "quest", "Quest", QUEST_FIELDS, BASE,
	managed=("_id", "conditions", "rewards") + TEXT_POINTER_KEYS,
	summary=lambda item, names: item.get("QuestName") or "(unnamed quest)",
	note="One quest: who gives it, where, its tasks and its rewards.",
)


def make_quest(quest_id=None, name="New quest", trader_id="", defaults=None):
	"""A new quest with its text keys filled in. defaults ({key: value}) overrides the base
	(for example the icon and side chosen in Settings)."""
	quest = {key: (list(v) if isinstance(v, list) else dict(v) if isinstance(v, dict) else v) for key, v in BASE.items()}
	quest["conditions"] = {"AvailableForFinish": [], "AvailableForStart": [], "Fail": []}
	quest["rewards"] = {"Fail": [], "Started": [], "Success": []}
	quest.update(defaults or {})
	quest_id = quest_id or new_id()
	quest["_id"] = quest_id
	quest["QuestName"] = name
	quest["traderId"] = trader_id
	for key in TEXT_POINTER_KEYS:
		quest[key] = quest_key(quest_id, key)
	return quest


def text_pointers_ok(quest):
	"""[(key, value)] of text pointer keys that are not '<quest id> <key>' (the game then shows the wrong text)."""
	quest_id = quest.get("_id", "")
	return [(k, quest.get(k)) for k in TEXT_POINTER_KEYS if k in quest and quest[k] != quest_key(quest_id, k)]
