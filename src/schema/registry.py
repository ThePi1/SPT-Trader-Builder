"""Finding the spec for any item, and making new ones."""

from core.ids import new_id
from schema import rewards, subtasks, tasks
from schema.fields import Spec, make
from schema.quest import QUEST

GROUPS = {
	"task": tasks.TASKS,
	"subtask": subtasks.SUBTASKS,
	"reward": rewards.REWARDS,
}

# The key that says which kind an item is
KIND_KEY = {"task": "conditionType", "subtask": "conditionType", "reward": "type"}

# A generic spec for a kind the app has no spec for: everything is kept, nothing has a form.
def unknown_spec(group, kind):
	return Spec(group, kind, kind or "Unknown", (), {}, common=False, summary=lambda item, names: kind or "Unknown",
		note="A kind this app doesn't know. It is kept exactly as it is.")


def kind_of(item, group):
	return item.get(KIND_KEY[group]) if isinstance(item, dict) else None


def spec_for(group, kind):
	"""The spec of a kind, or a generic one if the app doesn't know the kind."""
	if group == "quest":
		return QUEST
	return GROUPS[group].get(kind) or unknown_spec(group, kind)


def spec_of(item, group):
	return spec_for(group, kind_of(item, group))


def is_known(item, group):
	return group == "quest" or kind_of(item, group) in GROUPS[group]


def new_item(group, kind):
	"""A new task / subtask / reward of this kind, with a new id."""
	item = make(spec_for(group, kind), new_id)
	return item


def kinds(group, common_only=False):
	"""The specs of a group in the order the Add menu lists them: the common kinds first."""
	specs = list(GROUPS[group].values())
	if common_only:
		specs = [s for s in specs if s.common]
	return sorted(specs, key=lambda s: not s.common)
