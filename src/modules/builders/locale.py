"""Working out which locale entries a set of quests needs."""

from modules.builders.quests import LOCALE_FIELDS

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


def quest_locale(quest_id, field_texts, condition_texts):
	"""One quest's locale entries ({key: text}), from the text typed for its fields
	({field: text}, see LOCALE_FIELDS) and for each of its conditions ({condition id: text}).
	A field with no text is blank."""
	entries = {f"{quest_id} {field}": field_texts.get(field, "") for field in LOCALE_FIELDS}
	entries.update(condition_texts)
	return entries


def merge_locale(base_locale, keys, texts=None):
	"""The existing locale plus an entry for every key it does not have yet.

	A new entry gets its text from texts ({key: text}), or is blank. Entries the locale
	already has are never changed.
	"""
	texts = texts or {}
	merged = dict(base_locale)
	for key in keys:
		if key not in merged:
			merged[key] = texts.get(key, "")
	return merged


def new_locale(keys, texts=None):
	"""A locale of just these keys, with their text from texts ({key: text}), or blank."""
	return merge_locale({}, keys, texts)
