"""Every window can be constructed without errors."""

import gui


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
