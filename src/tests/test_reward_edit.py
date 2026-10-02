"""Editing an existing reward in the Reward Builder."""

import copy

import pytest

from modules.builders import rewards
from modules.config import load_config
from modules.state import AppState
from modules.windows.reward import REWARD_TABS, Gui_RewardDlg, can_edit


@pytest.fixture
def state(qapp):
	return AppState.load(load_config())


def open_reward(state, reward, timing="Success"):
	"""An edit dialog for reward, and the list its reward_ready signals are collected in."""
	dlg = Gui_RewardDlg(state, reward=reward, timing=timing)
	received = []
	dlg.reward_ready.connect(lambda *args: received.append(args))
	return dlg, received


def save(dlg, received):
	dlg.finalize(dlg.original["type"])
	(timing, kind, reward_id, reward), = received
	assert kind == dlg.original["type"] and reward_id == dlg.original["id"]
	return timing, reward


def table_ids(table):
	return [table.item(row, 0).text() for row in range(table.rowCount())]


ITEMS = [
	{
		"_id": "a0000000000000000000a001",
		"_tpl": "5449016a4bdc2d6f028b456f",
		"upd": {"StackObjectsCount": 5000, "SpawnedInSession": True},
	},
	{
		"_id": "a0000000000000000000a002",
		"_tpl": "5447a9cd4bdc2dbd208b4567",
		"upd": {"FireMode": {"FireMode": "single"}, "Repairable": {"Durability": 100, "MaxDurability": 100}},
	},
	{
		"_id": "a0000000000000000000a003",
		"_tpl": "5d6e6806a4b936088465b17e",
		"location": 1,
		"parentId": "a0000000000000000000a002",
		"slotId": "cartridges",
		"upd": {"StackObjectsCount": 30, "SpawnedInSession": True},
	},
]


def vanilla_like(kind, state):
	"""A reward like the ones SPT ships, with values the Reward Builder can't make."""
	prapor = state.traders["Prapor"]
	made = {
		"Experience": rewards.experience("r0000000000000000000a001", unknown=False, value=5000),
		"Item": rewards.item("r0000000000000000000a002", find_in_raid=True, items=ITEMS, target=ITEMS[1]["_id"], unknown=False, value=3),
		"AssortmentUnlock": rewards.assortment_unlock(
			"r0000000000000000000a003", items=ITEMS[:2], loyalty_level=3, target=ITEMS[0]["_id"], trader_id=prapor, unknown=True
		),
		"TraderStanding": rewards.trader_standing("r0000000000000000000a004", target=prapor, unknown=False, value=-0.04),
		"Skill": rewards.skill("r0000000000000000000a005", target="Strength", unknown=True, value=200),
		"StashRows": rewards.stash_rows("r0000000000000000000a006", unknown=False, value=2),
		"Achievement": rewards.achievement("r0000000000000000000a007", target="6544d4187c5457729210d5dd", unknown=False),
		"TraderUnlock": rewards.trader_unlock("r0000000000000000000a008", target=prapor, unknown=False),
	}[kind]
	made["index"] = 4
	made["availableInGameEditions"] = ["standard", "edge_of_darkness"]
	made["somethingNew"] = {"a": 1}
	return made


# --- nothing is lost on the way through -----------------------------------------------------


@pytest.mark.parametrize("kind", list(REWARD_TABS))
def test_saving_an_untouched_reward_gives_back_exactly_the_same_reward(state, kind):
	reward = vanilla_like(kind, state)
	dlg, received = open_reward(state, reward, "Started")
	timing, saved = save(dlg, received)
	assert saved == reward
	assert timing == "Started"


def test_numbers_written_as_text_survive(state):
	for kind, value in (("Experience", "5000"), ("TraderStanding", "0.15"), ("Skill", "500"), ("StashRows", "2")):
		reward = vanilla_like(kind, state)
		reward["value"] = value
		dlg, received = open_reward(state, reward)
		assert save(dlg, received)[1] == reward, kind


def test_a_reward_without_the_optional_keys_stays_without_them(state):
	# (some vanilla rewards have no "unknown" or "availableInGameEditions")
	reward = rewards.experience("r0000000000000000000b001", unknown=False, value=700)
	del reward["unknown"], reward["availableInGameEditions"]
	item = rewards.item("r0000000000000000000b002", find_in_raid=False, items=ITEMS[:1], target=ITEMS[0]["_id"], unknown=False, value=1)
	del item["unknown"], item["findInRaid"]
	for original in (reward, item):
		dlg, received = open_reward(state, original)
		assert save(dlg, received)[1] == original


def test_an_unknown_trader_and_skill_are_kept(state):
	reward = vanilla_like("TraderStanding", state)
	reward["target"] = "ffffffffffffffffffffffff"
	dlg, received = open_reward(state, reward)
	assert dlg.ui.box_trader_ts.currentText() == "ffffffffffffffffffffffff"
	assert save(dlg, received)[1] == reward
	skill = vanilla_like("Skill", state)
	skill["target"] = "SomeNewSkill"
	dlg, received = open_reward(state, skill)
	assert save(dlg, received)[1] == skill


# --- the form is filled from the reward -------------------------------------------------------


def test_the_experience_form(state):
	dlg, _ = open_reward(state, vanilla_like("Experience", state), "Fail")
	ui = dlg.ui
	assert (ui.box_amount_exp.text(), ui.box_unknown_exp.currentText(), ui.box_rewardtiming_exp.currentText()) == ("5000", "false", "Fail")


def test_the_item_form_and_its_items_table(state):
	dlg, _ = open_reward(state, vanilla_like("Item", state))
	ui = dlg.ui
	assert ui.box_fir_item.currentText() == "true" and ui.box_value_item.value() == 3
	assert table_ids(ui.tb_item) == [item["_id"] for item in ITEMS]
	assert [ui.tb_item.item(0, c).text() for c in range(6)] == [ITEMS[0]["_id"], ITEMS[0]["_tpl"], "5000", "n/a", "n/a", "True"]
	assert [ui.tb_item.item(2, c).text() for c in range(6)][3:5] == [ITEMS[1]["_id"], "cartridges"]
	# the target isn't the first item's id, so it was "specified"
	assert ui.chk_target_specify_it.isChecked() and ui.fld_man_target_it.text() == ITEMS[1]["_id"]


def test_the_target_is_not_marked_as_specified_when_it_is_the_first_item(state):
	reward = vanilla_like("Item", state)
	reward["target"] = ITEMS[0]["_id"]
	dlg, received = open_reward(state, reward)
	assert not dlg.ui.chk_target_specify_it.isChecked()
	assert save(dlg, received)[1]["target"] == ITEMS[0]["_id"]


def test_the_assort_unlock_form(state):
	dlg, _ = open_reward(state, vanilla_like("AssortmentUnlock", state))
	ui = dlg.ui
	assert (ui.box_trader_asu.currentText(), ui.box_loyalty_asu.value(), ui.box_unknown_asu.currentText()) == ("Prapor", 3, "true")
	assert table_ids(ui.tb_asu_item) == [item["_id"] for item in ITEMS[:2]]
	assert not ui.chk_target_specify_asu.isChecked()


def test_the_other_forms(state):
	ui = open_reward(state, vanilla_like("TraderStanding", state))[0].ui
	assert (ui.box_trader_ts.currentText(), ui.box_loyalty_ts.value()) == ("Prapor", -0.04)
	ui = open_reward(state, vanilla_like("Skill", state))[0].ui
	assert (ui.box_skill_sk.currentText(), ui.box_points_sk.value(), ui.box_unknown_sk.currentText()) == ("Strength", 200, "true")
	ui = open_reward(state, vanilla_like("StashRows", state))[0].ui
	assert ui.box_rows_sr.value() == 2
	ui = open_reward(state, vanilla_like("Achievement", state))[0].ui
	assert ui.fld_ach_id_ach.text() == "6544d4187c5457729210d5dd"
	ui = open_reward(state, vanilla_like("TraderUnlock", state))[0].ui
	assert ui.box_trader_tul.currentText() == "Prapor"


@pytest.mark.parametrize("kind", list(REWARD_TABS))
def test_only_the_rewards_own_tab_can_be_used(state, kind):
	dlg, _ = open_reward(state, vanilla_like(kind, state))
	tabs = dlg.ui.tabWidget
	assert tabs.currentIndex() == REWARD_TABS[kind]
	assert [tabs.isTabEnabled(i) for i in range(tabs.count())] == [i == REWARD_TABS[kind] for i in range(tabs.count())]
	assert dlg.windowTitle() == "Edit Reward"


# --- changes -----------------------------------------------------------------------------------


def test_changed_values_are_saved_and_the_rest_is_kept(state):
	reward = vanilla_like("Experience", state)
	dlg, received = open_reward(state, reward)
	dlg.ui.box_amount_exp.setText("9000")
	dlg.ui.box_unknown_exp.setCurrentText("true")
	timing, saved = save(dlg, received)
	expected = copy.deepcopy(reward)
	expected.update(value=9000, unknown=True)
	assert saved == expected


def test_the_timing_can_be_changed(state):
	dlg, received = open_reward(state, vanilla_like("Skill", state), "Success")
	dlg.ui.box_rewardtiming_sk.setCurrentText("Fail")
	timing, saved = save(dlg, received)
	assert timing == "Fail"


def test_an_item_can_be_removed_and_one_added(state):
	reward = vanilla_like("Item", state)
	dlg, received = open_reward(state, reward)
	dlg.ui.tb_item.selectRow(0)
	dlg.remove_selected_item("Item")
	dlg.ui.fld_utpl_item.setText("590c661e86f7741e566b646a")
	dlg.add_item("Item")
	timing, saved = save(dlg, received)
	assert [item["_id"] for item in saved["items"][:2]] == [ITEMS[1]["_id"], ITEMS[2]["_id"]]
	assert saved["items"][0] == ITEMS[1] and saved["items"][1] == ITEMS[2]  # (untouched items are exactly as they were)
	assert saved["items"][2]["_tpl"] == "590c661e86f7741e566b646a"
	assert saved["target"] == ITEMS[1]["_id"]  # (the target typed in stays)


def test_the_automatic_target_follows_the_first_item(state):
	reward = vanilla_like("AssortmentUnlock", state)
	dlg, received = open_reward(state, reward)
	dlg.ui.tb_asu_item.selectRow(0)
	dlg.remove_selected_item("AssortmentUnlock")
	_, saved = save(dlg, received)
	assert saved["target"] == ITEMS[1]["_id"]


def test_a_trader_standing_can_be_changed_to_a_negative_value(state):
	reward = vanilla_like("TraderStanding", state)
	reward["value"] = 0.1
	dlg, received = open_reward(state, reward)
	dlg.ui.box_loyalty_ts.setValue(-0.25)
	dlg.ui.box_trader_ts.setCurrentText("Skier")
	_, saved = save(dlg, received)
	assert saved["value"] == -0.25 and saved["target"] == state.traders["Skier"]


# --- the original is never touched -------------------------------------------------------------


def test_nothing_changes_until_the_reward_is_saved(state):
	reward = vanilla_like("Item", state)
	snapshot = copy.deepcopy(reward)
	dlg, received = open_reward(state, reward)
	dlg.ui.tb_item.selectRow(0)
	dlg.remove_selected_item("Item")
	dlg.ui.box_value_item.setValue(99)
	dlg.close()
	assert received == [] and reward == snapshot


def test_the_saved_reward_does_not_share_data_with_the_one_that_was_opened(state):
	reward = vanilla_like("Item", state)
	snapshot = copy.deepcopy(reward)
	dlg, received = open_reward(state, reward)
	_, saved = save(dlg, received)
	saved["items"][0]["upd"]["StackObjectsCount"] = 1
	assert reward == snapshot


# --- other kinds, and new rewards ---------------------------------------------------------------


@pytest.mark.parametrize("kind", ["ProductionScheme", "CustomizationDirect", "TraderStandingRestore", "Pockets", "Nonsense"])
def test_rewards_the_builder_cannot_make_cannot_be_opened(state, kind):
	reward = {"id": "x", "type": kind, "index": 0}
	assert not can_edit(reward)
	with pytest.raises(ValueError):
		Gui_RewardDlg(state, reward=reward, timing="Success")


def test_a_new_reward_is_unaffected(state, fixed_ids):
	dlg = Gui_RewardDlg(state)
	tabs = dlg.ui.tabWidget
	assert not dlg.editing
	assert all(tabs.isTabEnabled(i) for i in range(tabs.count()))
	assert dlg.ui.pb_finalize_exp.text() != "Save Changes" and dlg.windowTitle() != "Edit Reward"
	assert len(dlg.id) == 24
