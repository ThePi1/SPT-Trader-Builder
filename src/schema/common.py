"""Pieces the task, subtask and reward specs share."""

from schema import choices
from schema.fields import BOOL, CHOICE, INT, NUMBER, OBJECT, Field


def short(text, width=40):
	text = str(text)
	return text if len(text) <= width else text[: width - 1] + "..."


class Names:
	"""Turns ids into names for the outline. Without game data it just shows the ids."""

	def __init__(self, gamedata=None, quest_names=None):
		self.gamedata = gamedata
		self.quest_names = quest_names or {}  # {quest id: name} of the quests being edited

	def item(self, tpl):
		name = self.gamedata.item_name(tpl) if self.gamedata is not None else ""
		return name or short(tpl, 12)

	def trader(self, trader_id):
		name = self.gamedata.trader_name(trader_id) if self.gamedata is not None else ""
		return name or short(trader_id, 12)

	def quest(self, quest_id):
		name = self.quest_names.get(quest_id) or (self.gamedata.quest_name(quest_id) if self.gamedata is not None else "")
		return name or short(quest_id, 12)

	def skill(self, skill_id):
		"""A skill's name as the game shows it (Sniper is 'Bolt-action Rifles'); the id when the locale doesn't have it."""
		return (self.gamedata.locale.get(skill_id) if self.gamedata is not None else None) or str(skill_id)

	def location(self, location_id):
		"""A map's name (the id when it isn't a known map)."""
		return (self.gamedata.locations.get(location_id) if self.gamedata is not None else None) or str(location_id)

	def items(self, tpls, limit=2):
		names = [self.item(t) for t in tpls[:limit]]
		if len(tpls) > limit:
			names.append(f"+{len(tpls) - limit} more")
		return ", ".join(names)


PLAIN = Names()


def compare_text(method):
	return {">=": ">=", "<=": "<=", ">": ">", "<": "<", "==": "="}.get(method, str(method))


def compare_object(key, label, default_value=0):
	"""A {compareMethod, value} object, as the Kills distance and the health tasks use."""
	return Field(
		key, label, OBJECT,
		fields=(
			Field("compareMethod", "Is", CHOICE, ">=", choices="compare"),
			Field("value", "Value", NUMBER, default_value),
		),
	)


def flag(key, label, default=False, advanced=True):
	return Field(key, label, BOOL, default, advanced=advanced)


def count(key, label, default=1, minimum=0):
	return Field(key, label, INT, default, minimum=minimum)
