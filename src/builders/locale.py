"""Working out which locale entries a set of quests needs."""

from builders.quests import LOCALE_FIELDS

CONDITION_LISTS = ("AvailableForFinish", "AvailableForStart", "Fail")

# Quests we never want locale entries for
SKIPPED_QUEST_NAMES = ("Collector",)


def locale_keys(quests):
	"""Every locale key the quests need: their text fields, and each condition id."""
	keys = []
	for quest_id, quest in quests.items():
		if quest["QuestName"] in SKIPPED_QUEST_NAMES:
			continue  # we want to manually skip these
		# do top-level quest fields
		for field in LOCALE_FIELDS:
			if field in quest:
				keys.append(f"{quest_id} {field}")
		# do condition ids
		for list_name in CONDITION_LISTS:
			for condition in quest["conditions"][list_name]:
				keys.append(condition["id"])
	return keys


def merge_locale(base_locale, keys):
	"""The existing locale plus an empty entry for every key it does not have yet."""
	merged = dict(base_locale)
	for key in keys:
		if key not in merged:
			merged[key] = ""
	return merged
