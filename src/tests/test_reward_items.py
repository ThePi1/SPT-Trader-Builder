"""Stack counts in reward items are numbers (SPT reads them as numbers), for both reward kinds."""

import pytest


@pytest.fixture
def reward(main_window):
	return main_window.spawnWindow("QuestBuilder").open_reward_window()


def _only_item(reward, key):
	(item,) = reward.fields.get_multicolumn_values_list(key)
	return item


def test_item_reward_stack_count_is_a_number(reward):
	reward.ui.fld_utpl_item.setText("tpl")
	reward.ui.chk_soc_item.setChecked(True)
	reward.ui.box_soc_item.setValue(50000)
	reward.add_item("Item")
	count = _only_item(reward, "RewardItem")["upd"]["StackObjectsCount"]
	assert count == 50000 and isinstance(count, int)


def test_assortment_unlock_stack_count_is_a_number(reward):
	reward.ui.fld_utpl_asu.setText("tpl")
	reward.ui.chk_soc_asu.setChecked(True)
	reward.ui.box_soc_asu.setValue(7)
	reward.add_item("AssortmentUnlock")
	count = _only_item(reward, "RewardAssortmentUnlock")["upd"]["StackObjectsCount"]
	assert count == 7 and isinstance(count, int)


def test_the_number_survives_into_the_finished_reward(reward):
	got = []
	reward.reward_ready.connect(lambda *args: got.append(args))
	reward.ui.fld_utpl_item.setText("tpl")
	reward.ui.chk_soc_item.setChecked(True)
	reward.ui.box_soc_item.setValue(12)
	reward.add_item("Item")
	reward.ui.box_value_item.setValue(1)
	reward.finalize("Item")
	(count,) = [i["upd"]["StackObjectsCount"] for i in got[0][3]["items"]]
	assert count == 12 and isinstance(count, int)


def test_no_stack_count_when_the_box_is_unticked(reward):
	reward.ui.fld_utpl_item.setText("tpl")
	reward.ui.chk_soc_item.setChecked(False)  # (both of these start ticked)
	reward.ui.chk_fir_item.setChecked(False)
	reward.add_item("Item")
	assert "upd" not in _only_item(reward, "RewardItem")
