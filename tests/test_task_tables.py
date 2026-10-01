"""LeaveItemAtLocation reads its min and max durability from their own fields."""

import pytest


@pytest.fixture
def task(main_window):
	return main_window.spawnWindow("QuestBuilder").open_task_window()


# --- LeaveItemAtLocation durability -----------------------------------------------------


def _leave_item(task, **fields):
	got = []
	task.condition_ready.connect(lambda *args: got.append(args))
	for name, text in fields.items():
		getattr(task.ui, name).setText(text)
	task.finalize("LeaveItemAtLocation")
	return got[0][3]


def test_leave_item_min_and_max_durability_are_read_from_their_own_fields(task):
	cond = _leave_item(task, fld_mindur_li="30", fld_maxdur_li="80")
	assert (cond["minDurability"], cond["maxDurability"]) == (30, 80)


def test_leave_item_blank_durabilities_default_to_0_and_100(task):
	cond = _leave_item(task)
	assert (cond["minDurability"], cond["maxDurability"]) == (0, 100)


def test_leave_item_min_alone_does_not_change_max(task):
	cond = _leave_item(task, fld_mindur_li="30")
	assert (cond["minDurability"], cond["maxDurability"]) == (30, 100)


def test_leave_item_max_alone_does_not_change_min(task):
	cond = _leave_item(task, fld_maxdur_li="60")
	assert (cond["minDurability"], cond["maxDurability"]) == (0, 60)
