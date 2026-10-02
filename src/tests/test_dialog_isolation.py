"""What one dialog collects must never leak into another dialog or another quest."""


def _finalize_reward_item(reward_dlg, tpl=None):
	"""Finalize an Item reward, returning the emitted reward."""
	got = []
	reward_dlg.reward_ready.connect(lambda *args: got.append(args))
	if tpl:
		reward_dlg.ui.fld_utpl_item.setText(tpl)
		reward_dlg.add_item("Item")
	reward_dlg.ui.box_value_item.setValue(1)  # a spinbox on a never-shown tab reads as blank until set
	reward_dlg.finalize("Item")
	return got[0][3]


def _quest_by_name(main_window, name):
	return next(q for q in main_window.state.quests.values() if q["QuestName"] == name)


def test_a_new_reward_dialog_does_not_inherit_the_previous_rewards_items(main_window):
	quest = main_window.spawnWindow("QuestBuilder")
	first = _finalize_reward_item(quest.open_reward_window(), tpl="itemA")
	second = _finalize_reward_item(quest.open_reward_window())
	assert [i["_tpl"] for i in first["items"]] == ["itemA"]
	assert second["items"] == []
	assert second["target"] == ""


def test_two_open_reward_dialogs_keep_their_items_separate(main_window):
	quest = main_window.spawnWindow("QuestBuilder")
	one, two = quest.open_reward_window(), quest.open_reward_window()
	one.ui.fld_utpl_item.setText("itemA")
	one.add_item("Item")
	two.ui.fld_utpl_item.setText("itemB")
	two.add_item("Item")
	assert [i["_tpl"] for i in _finalize_reward_item(one)["items"]] == ["itemA"]
	assert [i["_tpl"] for i in _finalize_reward_item(two)["items"]] == ["itemB"]


def test_abandoned_quest_does_not_leak_into_the_next_quest(main_window):
	abandoned = main_window.spawnWindow("QuestBuilder")
	task = abandoned.open_task_window()
	task.ui.fld_value_lv.setText("7")
	task.finalize("Level")
	reward = abandoned.open_reward_window()
	reward.ui.box_amount_exp.setText("100")
	reward.finalize("Experience")
	abandoned.close()  # never saved

	fresh = main_window.spawnWindow("QuestBuilder")
	fresh.ui.fld_quest_name.setText("fresh")
	fresh.finalize()

	quest = _quest_by_name(main_window, "fresh")
	assert quest["conditions"] == {"AvailableForFinish": [], "AvailableForStart": [], "Fail": []}
	assert quest["rewards"] == {"Fail": [], "Started": [], "Success": []}


def test_two_open_quest_dialogs_keep_their_conditions_separate(main_window):
	one = main_window.spawnWindow("QuestBuilder")
	two = main_window.spawnWindow("QuestBuilder")
	task = one.open_task_window()
	task.ui.fld_value_lv.setText("7")
	task.finalize("Level")
	one.ui.fld_quest_name.setText("one")
	two.ui.fld_quest_name.setText("two")
	one.finalize()
	two.finalize()
	assert len(_quest_by_name(main_window, "one")["conditions"]["AvailableForStart"]) == 1
	assert _quest_by_name(main_window, "two")["conditions"]["AvailableForStart"] == []


def test_an_abandoned_task_dialog_does_not_leak_rows_into_the_next_one(main_window):
	quest = main_window.spawnWindow("QuestBuilder")
	abandoned = quest.open_task_window()
	abandoned.ui.box_weapons_cck.setCurrentIndex(1)
	abandoned.ui.pb_addwep_cck.released.emit()
	assert abandoned.ui.tb_wep.rowCount() == 1
	abandoned.close()  # never finalized

	fresh = quest.open_task_window()
	fresh.cc_add("Kills")
	(kills,) = fresh.fields.get_multicolumn_values_list("CounterCreator")
	assert fresh.ui.tb_wep.rowCount() == 0
	assert kills["weapon"] == []


def test_two_open_task_dialogs_keep_their_rows_separate(main_window):
	quest = main_window.spawnWindow("QuestBuilder")
	one, two = quest.open_task_window(), quest.open_task_window()
	one.ui.box_weapons_cck.setCurrentIndex(1)
	one.ui.pb_addwep_cck.released.emit()
	two.cc_add("Kills")
	(kills,) = two.fields.get_multicolumn_values_list("CounterCreator")
	assert kills["weapon"] == []


def test_a_saved_quest_keeps_its_own_rows_when_the_next_quest_is_started(main_window):
	first = main_window.spawnWindow("QuestBuilder")
	task = first.open_task_window()
	task.ui.fld_value_lv.setText("7")
	task.finalize("Level")
	first.ui.fld_quest_name.setText("first")
	first.finalize()

	second = main_window.spawnWindow("QuestBuilder")
	second.ui.fld_quest_name.setText("second")
	second.finalize()

	assert len(_quest_by_name(main_window, "first")["conditions"]["AvailableForStart"]) == 1
	assert _quest_by_name(main_window, "second")["conditions"]["AvailableForStart"] == []
