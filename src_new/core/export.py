"""Exporting some of the open quests as files of their own: the quests, their text, and the trader offers
that the quests unlock (with the locks that tie them together). Nothing here changes its inputs."""

import copy
from dataclasses import dataclass, field

from schema import assort as assort_schema
from schema import locale as locale_schema


@dataclass
class Export:
	quests: dict = field(default_factory=dict)
	locale: dict = field(default_factory=dict)  # the text of those quests that is in the open locale
	assort: dict = field(default_factory=dict)  # only the offers locked to those quests (empty: none)
	locks: dict = field(default_factory=dict)  # only the locks that point at those quests (empty: none)

	def offer_count(self):
		return len(assort_schema.offer_ids(self.assort)) if self.assort else 0

	def lock_count(self):
		return sum(len(v) for v in self.locks.values()) if self.locks else 0


def export_selection(quest_ids, quests, locale, assort, locks):
	"""What goes into an export of these quests, taken from the open quests, locale, assort and locks."""
	chosen = {qid: copy.deepcopy(quests[qid]) for qid in quest_ids if isinstance(quests.get(qid), dict)}
	result = Export(quests=chosen)
	owners = locale_schema.key_owners(chosen)
	result.locale = {key: text for key, text in locale.items() if key in owners and text}
	selected_locks = {
		status: {offer: quest for offer, quest in (locks.get(status) or {}).items() if quest in chosen}
		for status in assort_schema.QUEST_LOCKS
	}
	offers = {offer for status in selected_locks.values() for offer in status}
	there = [offer for offer in assort_schema.offer_ids(assort) if offer in offers]
	if there:
		out = assort_schema.empty_assort()
		for offer in there:
			parts = assort_schema.offer_parts(assort, offer)
			out["items"].extend(copy.deepcopy(parts))
			out["barter_scheme"][offer] = copy.deepcopy(assort.get("barter_scheme", {}).get(offer, [[]]))
			out["loyal_level_items"][offer] = assort.get("loyal_level_items", {}).get(offer, 1)
		result.assort = out
		result.locks = {status: {o: q for o, q in found.items() if o in set(there)} for status, found in selected_locks.items()}
		if not any(result.locks.values()):
			result.locks = {}
	return result
