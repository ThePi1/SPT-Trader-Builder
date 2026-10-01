"""Characterization tests: drive the real windows and compare the JSON they
build against golden files, so refactors can't silently change the output.
"""

import json

from table_fields import add_table_field


def _build_quest(main_window):
	quest_dlg = main_window.spawnWindow("QuestBuilder")
	quest_dlg.ui.fld_quest_name.setText("Golden Quest")

	# Start condition: Level
	task = quest_dlg.open_task_window()
	task.ui.fld_value_lv.setText("15")
	task.finalize("Level")

	# Finish condition: Skill
	task = quest_dlg.open_task_window()
	task.ui.fld_level_sk.setText("5")
	task.finalize("Skill")

	# Finish condition: CounterCreator with a VisitPlace sub-condition
	task = quest_dlg.open_task_window()
	task.ui.fld_zoneid_ccvp.setText("zone_one")
	task.cc_add("VisitPlace")
	task.ui.fld_quantity_cc.setText("2")
	task.finalize("CounterCreator")

	# Finish condition: HandoverItem with one item
	task = quest_dlg.open_task_window()
	add_table_field(
		main_window.state, "HFItems", task.ui.tb_items, "5449016a4bdc2d6f028b456f", {0: "x"}, "5449016a4bdc2d6f028b456f"
	)
	task.ui.box_hofind_it.setCurrentText("HandoverItem")
	task.ui.fld_quantity_it.setText("3")
	task.finalize("Item")

	# Rewards: Experience + Item
	reward = quest_dlg.open_reward_window()
	reward.ui.box_amount_exp.setText("1500")
	reward.finalize("Experience")

	reward = quest_dlg.open_reward_window()
	reward.ui.fld_utpl_item.setText("5449016a4bdc2d6f028b456f")
	reward.ui.chk_soc_item.setChecked(True)
	reward.ui.box_soc_item.setValue(50000)
	reward.add_item("Item")
	reward.ui.box_value_item.setValue(50000)
	reward.finalize("Item")

	quest_dlg.finalize()
	return main_window.state.quests


def test_quest_export_matches_golden(main_window, check_golden):
	quests = _build_quest(main_window)
	assert len(quests) == 1
	check_golden("quest_export", quests)
	# the main window's quest list was updated too
	assert main_window.ui.questList.count() == 1


def test_assort_export_matches_golden(main_window, check_golden):
	dlg = main_window.spawnWindow("AssortBuilder")
	dlg.ui.ab_Item_Id.setText("5449016a4bdc2d6f028b456f")
	dlg.ui.ab_quantity.setText("10")
	dlg.ui.ab_cost_edit.setText("500")
	dlg.add_item()

	dlg.ui.ab_Item_Id.setText("590c661e86f7741e566b646a")
	dlg.ui.ab_unlimitedcount.setChecked(True)
	dlg.ui.ab_cost_edit.setText("12")
	dlg.ui.ab_usd_button.setChecked(True)
	dlg.add_item()

	check_golden(
		"assort_export",
		{
			"items": dlg.itemlist,
			"barter_scheme": dlg.barterlist,
			"loyal_level_items": dlg.loyaltylist,
		},
	)
	assert dlg.ui.ab_table.rowCount() == 2


def test_locale_generation_matches_golden(main_window, check_golden, tmp_path):
	quest_file = tmp_path / "quests.json"
	locale_file = tmp_path / "en.json"
	quests = _build_quest(main_window)
	quest_file.write_text(json.dumps(quests), encoding="utf-8")
	locale_file.write_text(json.dumps({"existing key": "existing value"}), encoding="utf-8")

	main_window.createLocaleFromJSON(q_file=str(quest_file), l_file=str(locale_file))

	check_golden("locale_export", json.loads(locale_file.read_text(encoding="utf-8")))
