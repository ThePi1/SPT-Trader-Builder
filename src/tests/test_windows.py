"""The windows get what they need from AppState and signals, not from their parent."""

import json

from modules.config import load_config
from modules.state import AppState
from modules.windows import data_editor
from modules.windows.assort import Gui_AssortDlg
from modules.windows.reward import Gui_RewardDlg
from modules.windows.task import Gui_TaskDlg


def _state():
	return AppState.load(load_config())


def test_task_dialog_works_without_a_parent(qapp, fixed_ids):
	dlg = Gui_TaskDlg(_state())
	received = []
	dlg.condition_ready.connect(lambda *args: received.append(args))
	dlg.ui.fld_value_lv.setText("20")
	dlg.finalize("Level")
	(timing, cond_type, cond_id, cond), = received
	assert (timing, cond_type) == ("Start", "Level")
	assert cond["value"] == 20 and cond["id"] == cond_id


def test_reward_dialog_works_without_a_parent(qapp, fixed_ids):
	dlg = Gui_RewardDlg(_state())
	received = []
	dlg.reward_ready.connect(lambda *args: received.append(args))
	dlg.ui.box_amount_exp.setText("100")
	dlg.finalize("Experience")
	(timing, reward_type, reward_id, reward), = received
	assert reward_type == "Experience" and reward["value"] == 100


def test_assort_dialog_works_without_a_parent(qapp):
	assert Gui_AssortDlg(_state()).ui.ab_loyalty_combo.count() > 0


def test_child_dialogs_are_owned_by_their_opener(main_window):
	quest = main_window.spawnWindow("QuestBuilder")
	task = quest.open_task_window()
	reward = quest.open_reward_window()
	assert quest.parent() is main_window
	assert task.parent() is quest
	assert reward.parent() is quest


def test_saving_a_quest_updates_the_main_window(main_window):
	quest = main_window.spawnWindow("QuestBuilder")
	quest.ui.fld_quest_name.setText("My Quest")
	quest.finalize()
	assert len(main_window.state.quests) == 1
	assert main_window.ui.questList.count() == 1
	assert main_window.ui.questList.item(0).text().startswith("My Quest, ")
	assert quest.fields.data == {}  # nothing was added to this quest's tables


def test_wtt_import_saves_datafiles_in_the_data_dir(main_window, tmp_path, monkeypatch):
	wtt = tmp_path / "wtt"
	(wtt / "CustomItems").mkdir(parents=True)
	(wtt / "CustomItems" / "items.json").write_text(
		json.dumps(
			{"abc": {"locales": {"en": {"name": "N", "shortName": "S", "description": "D"}}}}
		)
	)
	data_dir = tmp_path / "somewhere_else"
	data_dir.mkdir()
	monkeypatch.setattr(data_editor, "DATA_DIR", data_dir)
	monkeypatch.setattr(data_editor, "safe_file_dialog", lambda method, title: (str(wtt), True))

	editor = main_window.spawnWindow("DataWindow")
	editor.import_wtt()

	saved = json.loads((data_dir / "datafiles.json").read_text())
	assert list(saved) == ["CustomItems"]
	assert main_window.state.id_search["N"] == "abc"


def test_trader_standing_task_can_be_finalized(qapp, fixed_ids):
	# Used to crash with an undefined variable (the value was read into the wrong name).
	dlg = Gui_TaskDlg(_state())
	received = []
	dlg.condition_ready.connect(lambda *args: received.append(args))
	dlg.ui.fld_value_ts.setText("3")
	dlg.finalize("TraderStanding")
	(timing, cond_type, _, cond), = received
	assert (timing, cond_type) == ("Start", "TraderStanding")
	assert cond["value"] == 3


def test_visibility_conditions_are_written_as_objects_like_vanilla_quests(qapp, fixed_ids):
	dlg = Gui_TaskDlg(_state())
	received = []
	dlg.condition_ready.connect(lambda *args: received.append(args))
	dlg.ui.fld_visibility_targetid.setText("63ac22351b5c95746621ddc4")
	dlg.ui.pb_addvis.click()
	dlg.ui.fld_visibility_targetid.setText("63ac2151972364554162a27c")
	dlg.ui.pb_addvis.click()
	dlg.ui.fld_itemid_it.setText("5449016a4bdc2d6f028b456f")
	dlg.ui.pb_additem_it.click()
	dlg.finalize("Item")
	(_, _, _, cond), = received
	visibility = cond["visibilityConditions"]
	assert [v["target"] for v in visibility] == ["63ac22351b5c95746621ddc4", "63ac2151972364554162a27c"]
	assert all(v["conditionType"] == "CompleteCondition" for v in visibility)
	assert all(set(v) == {"conditionType", "id", "target"} for v in visibility)
	assert len({v["id"] for v in visibility}) == 2  # each has its own id
