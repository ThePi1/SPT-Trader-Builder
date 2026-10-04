"""The schema against the base game's own files: nothing the game ships may be an error."""

from schema import server, validate
from schema.issues import ERROR, errors


def test_vanilla_quests_have_no_errors(vanilla_quests, vanilla_locale):
	issues = validate.validate_quests(vanilla_quests, vanilla_locale)
	assert not errors(issues), "\n".join(str(i) for i in errors(issues)[:10])


def test_vanilla_quests_only_have_the_known_oddities(vanilla_quests, vanilla_locale):
	# the base game reuses a few ids inside one quest; nothing else should be reported
	issues = validate.validate_quests(vanilla_quests, vanilla_locale)
	assert all("used twice" in i.message for i in issues), "\n".join(str(i) for i in issues[:10])


def test_vanilla_assort_loads(vanilla_assort):
	assert not server.check_record(vanilla_assort, "TraderAssort")


def test_every_vanilla_task_is_a_known_kind(vanilla_quests):
	from schema import registry

	unknown = set()
	for quest in vanilla_quests.values():
		for tasks in quest["conditions"].values():
			for task in tasks:
				if not registry.is_known(task, "task"):
					unknown.add(task["conditionType"])
				for sub in (task.get("counter") or {}).get("conditions", []):
					if not registry.is_known(sub, "subtask"):
						unknown.add("subtask " + sub["conditionType"])
		for rewards in quest["rewards"].values():
			for reward in rewards:
				if not registry.is_known(reward, "reward"):
					unknown.add("reward " + reward["type"])
	assert not unknown, unknown
