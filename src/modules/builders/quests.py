"""A whole quest definition."""

import copy

# Fields SPT looks up in the locale file, as "<quest id> <field>"
LOCALE_FIELDS = (
	"name",
	"note",
	"acceptPlayerMessage",
	"changeQuestMessageText",
	"completePlayerMessage",
	"declinePlayerMessage",
	"description",
	"failMessageText",
	"startedMessageText",
	"successMessageText",
)


def quest(
	quest_id,
	*,
	name,
	can_show_notifications,
	finish_conditions,
	start_conditions,
	fail_conditions,
	image,
	instant_complete,
	location,
	restartable,
	rewards,
	secret_quest,
	side,
	trader_id,
	quest_type,
):
	"""Returns the quest dict (to be stored under its own id). Text fields are locale keys."""
	return {
		"QuestName": name,
		"_id": quest_id,
		"acceptPlayerMessage": quest_id + " acceptPlayerMessage",
		"acceptanceAndFinishingSource": "eft",
		"arenaLocations": [],
		"canShowNotificationsInGame": can_show_notifications,
		"changeQuestMessageText": quest_id + " changeQuestMessageText",
		"completePlayerMessage": quest_id + " completePlayerMessage",
		"conditions": {
			"AvailableForFinish": finish_conditions,
			"AvailableForStart": start_conditions,
			"Fail": fail_conditions,
		},
		"declinePlayerMessage": quest_id + " declinePlayerMessage",
		"description": quest_id + " description",
		"failMessageText": quest_id + " failMessageText",
		"image": image,
		"instantComplete": instant_complete,
		"isKey": False,
		"location": location,
		"name": quest_id + " name",
		"note": quest_id + " note",
		"progressSource": "eft",
		"rankingModes": [],
		"restartable": restartable,
		"rewards": rewards,
		"secretQuest": secret_quest,
		"side": side,
		"startedMessageText": quest_id + " startedMessageText",
		"successMessageText": quest_id + " successMessageText",
		"traderId": trader_id,
		"type": quest_type,
	}


# The keys of a quest that the Quest Builder has a control for (see windows/quest.py)
EDITABLE_KEYS = (
	"QuestName",
	"canShowNotificationsInGame",
	"conditions",
	"image",
	"instantComplete",
	"location",
	"restartable",
	"rewards",
	"secretQuest",
	"side",
	"traderId",
	"type",
)


def edited_quest(original, built):
	"""A quest that was edited in the Quest Builder: the original, with the edited fields replaced.

	built is what quest() made from the form. Only the keys the form has a control for are taken
	from it; everything else (keys the Builder never writes, such as "status", or ones it always
	writes the same way) stays as the original had it, so editing a quest can't change anything
	the user couldn't see.
	"""
	merged = copy.deepcopy(original)
	for key in EDITABLE_KEYS:
		merged[key] = built[key]
	return merged
