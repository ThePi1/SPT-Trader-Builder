"""Every window can be constructed without errors."""

def test_main_window_loads_data(main_window):
	assert main_window.state.traders
	assert main_window.state.items
	assert main_window.state.locations


def test_all_windows_open(main_window):
	quest = main_window.spawnWindow("QuestBuilder")
	main_window.spawnWindow("AssortBuilder")
	main_window.spawnWindow("DataWindow")
	quest.open_task_window()
	quest.open_reward_window()
	main_window.spawnWindow("AboutWindow")
	main_window.spawnWindow("UpdateWindow")
	# quest/assort/data/about/update are tracked by the main window; task/reward by the quest dialog
	assert len(main_window.windows) == 5
	assert len(quest.windows) == 2


def test_the_old_edit_selected_quest_is_gone_and_the_new_one_is_in_its_place(main_window):
	# the old feature (editSelectedQuest, built on load_settings_from_dict) was removed...
	assert not hasattr(main_window, "editSelectedQuest")
	# ...and Edit Selected Quest was added back, reopening a quest in the Quest Builder
	assert main_window.ui.actionEdit_Selected_Quest.text() == "Edit Selected Quest"
	assert main_window.ui.actionEdit_Selected_Quest in main_window.ui.menuEdit.actions()
