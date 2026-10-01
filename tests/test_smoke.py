"""Every window can be constructed without errors."""

import gui


def test_main_window_loads_data(main_window):
	assert main_window.traders
	assert main_window.items
	assert main_window.locations


def test_all_windows_open(main_window):
	quest = main_window.spawnWindow("QuestBuilder")
	main_window.spawnWindow("AssortBuilder")
	main_window.spawnWindow("DataWindow")
	main_window.spawnWindow("TaskBuilder", _parent=quest)
	main_window.spawnWindow("RewardBuilder", _parent=quest)
	main_window.spawnWindow("AboutWindow")
	main_window.spawnWindow("UpdateWindow")
	assert len(main_window.windows) == 7
