"""Editing an existing quest in the Quest Builder."""

import copy

import pytest

from modules.builders import conditions, locale as locale_builders, quests, rewards
from modules.builders.quests import LOCALE_FIELDS
from modules.windows.quest import TASK_TEXT_COLUMN, Gui_QuestDlg


def open_editor(main_window, quest, locale=None):
	"""An edit dialog for quest, and the list the quest_saved signals it sends are collected in."""
	dlg = Gui_QuestDlg(main_window.state, parent=main_window, quest=quest, locale=locale)
	saved = []
	dlg.quest_saved.connect(lambda *args: saved.append(args))
	main_window.windows.append(dlg)
	return dlg, saved


def make_vanilla_like_quest():
	"""A quest like the ones SPT ships: values the Quest Builder can't make, and keys it never writes."""
	counter = conditions.counter_creator(
		"cc00000000000000000000aa",
		counter_id="cc00000000000000000000ab",
		sub_conditions=[conditions.visit_place("cc00000000000000000000ac", "zone_one")],
		parent_id="",
		quest_type="Exploration",
		value=2,
		visibility_conditions=[conditions.visibility_condition("cc00000000000000000000ad", "lv00000000000000000000aa")],
	)
	counter["oneSessionOnly"] = True
	counter["index"] = 3
	level = conditions.level("lv00000000000000000000aa", compare_method=">=", value=15)
	level["index"] = 1
	exp = rewards.experience("ex00000000000000000000aa", unknown=False, value="5000")  # (a string, as in vanilla)
	exp["index"] = 2
	item = rewards.item(
		"it00000000000000000000aa",
		find_in_raid=True,
		items=[
			{
				"_id": "it00000000000000000000ab",
				"_tpl": "5449016a4bdc2d6f028b456f",
				"upd": {"StackObjectsCount": 1, "Repairable": {"Durability": 100, "MaxDurability": 100}},
			}
		],
		target="it00000000000000000000ab",
		unknown=False,
		value=1,
	)
	quest = quests.quest(
		"60000000000000000000aaaa",
		name="Vanilla Style",
		can_show_notifications=True,
		finish_conditions=[counter],
		start_conditions=[level],
		fail_conditions=[],
		image="/files/quest/icon/596b465486f77457ca186188.jpg",
		instant_complete=False,
		location="marathon",  # not one of the locations the Builder offers
		restartable=False,
		rewards={"Fail": [], "Started": [], "Success": [exp, item]},
		secret_quest=False,
		side="Pmc",  # (the Builder offers "pmc")
		trader_id="ffffffffffffffffffffffff",  # not one of the traders the Builder knows
		quest_type="Elimination",
	)
	quest["status"] = 0
	quest["gameModes"] = []
	quest["isKey"] = False
	return quest


def save_unchanged(main_window, quest, locale=None):
	dlg, saved = open_editor(main_window, quest, locale)
	dlg.finalize()
	(quest_id, name, new_quest, new_locale), = saved
	return quest_id, name, new_quest, new_locale


# --- nothing is lost on the way through -----------------------------------------------------


def test_saving_an_untouched_quest_gives_back_exactly_the_same_quest(main_window):
	quest = make_vanilla_like_quest()
	quest_id, name, saved_quest, _ = save_unchanged(main_window, quest)
	assert quest_id == quest["_id"] and name == "Vanilla Style"
	assert saved_quest == quest


def test_values_the_builder_does_not_offer_are_kept(main_window):
	quest = make_vanilla_like_quest()
	dlg, saved = open_editor(main_window, quest)
	assert dlg.ui.box_avail_faction.currentText() == "Pmc"
	assert dlg.ui.box_location.currentText() == "marathon"
	assert dlg.ui.box_trader.currentText() == "ffffffffffffffffffffffff"
	dlg.ui.fld_quest_name.setText("Renamed")
	dlg.finalize()
	(_, _, edited, _), = saved
	assert (edited["side"], edited["location"], edited["traderId"]) == ("Pmc", "marathon", "ffffffffffffffffffffffff")


def test_a_known_trader_and_location_are_shown_by_name(main_window):
	state = main_window.state
	quest = make_vanilla_like_quest()
	quest["traderId"] = state.traders["Prapor"]
	quest["location"] = state.locations["Woods"]
	dlg, _ = open_editor(main_window, quest)
	assert dlg.ui.box_trader.currentText() == "Prapor"
	assert dlg.ui.box_location.currentText() == "Woods"
	assert dlg.ui.box_location.count() == len(main_window.state.config.qb_box_location)  # nothing was added


def test_the_whole_form_is_filled_from_the_quest(main_window):
	state = main_window.state
	quest = make_vanilla_like_quest()
	quest.update(
		traderId=state.traders["Skier"],
		location="any",
		side="bear",
		canShowNotificationsInGame=False,
		instantComplete=True,
		restartable=True,
		secretQuest=True,
		image="/files/quest/icon/x.jpg",
	)
	dlg, _ = open_editor(main_window, quest)
	ui = dlg.ui
	assert ui.fld_quest_name.text() == "Vanilla Style"
	assert (ui.box_trader.currentText(), ui.box_location.currentText()) == ("Skier", "any")
	assert (ui.box_avail_faction.currentText(), ui.box_quest_type_label.currentText()) == ("bear", "Elimination")
	assert [
		box.currentText()
		for box in (ui.box_can_show_notif, ui.box_insta_complete, ui.box_restartable, ui.box_secret_quest)
	] == ["false", "true", "true", "true"]
	assert ui.fld_image_name.text() == "/files/quest/icon/x.jpg"
	assert dlg.windowTitle() == "Edit Quest - Vanilla Style"
	assert ui.pb_finalize_quest.text() == "Save Changes"
	assert dlg.quest_id == quest["_id"]


def test_the_tasks_and_rewards_tables_show_the_quests_tasks_and_rewards(main_window):
	dlg, _ = open_editor(main_window, make_vanilla_like_quest())
	tasks = dlg.ui.tb_cond
	assert [(tasks.item(r, 0).text(), tasks.item(r, 1).text(), tasks.item(r, 2).text()) for r in range(tasks.rowCount())] == [
		("lv00000000000000000000aa", "Start", "Level"),
		("cc00000000000000000000aa", "Finish", "CounterCreator"),
	]
	table = dlg.ui.tb_rewards
	assert [(table.item(r, 1).text(), table.item(r, 2).text()) for r in range(table.rowCount())] == [
		("Success", "Experience"),
		("Success", "Item"),
	]


# --- changes -----------------------------------------------------------------------------------


def test_changed_fields_are_saved_and_the_rest_is_kept(main_window):
	quest = make_vanilla_like_quest()
	dlg, saved = open_editor(main_window, quest)
	dlg.ui.fld_quest_name.setText("Renamed")
	dlg.ui.box_avail_faction.setCurrentText("usec")
	dlg.ui.box_restartable.setCurrentText("true")
	dlg.finalize()
	(_, name, edited, _), = saved
	assert name == "Renamed"
	assert (edited["QuestName"], edited["side"], edited["restartable"]) == ("Renamed", "usec", True)
	expected = copy.deepcopy(quest)
	expected.update(QuestName="Renamed", side="usec", restartable=True)
	assert edited == expected  # (including status, gameModes and everything in the conditions and rewards)


def test_a_task_can_be_removed_and_a_new_one_added(main_window):
	quest = make_vanilla_like_quest()
	dlg, saved = open_editor(main_window, quest)
	dlg.ui.tb_cond.selectRow(0)  # the Level task
	dlg.remove_selected_task()
	task = dlg.open_task_window()
	task.ui.fld_level_sk.setText("5")
	task.finalize("Skill")
	dlg.finalize()
	(_, _, edited, _), = saved
	assert edited["conditions"]["AvailableForStart"] == []
	finish = edited["conditions"]["AvailableForFinish"]
	assert [c["conditionType"] for c in finish] == ["CounterCreator", "Skill"]
	assert finish[0] == quest["conditions"]["AvailableForFinish"][0]  # the untouched one is exactly as it was


def test_a_reward_can_be_removed_and_a_new_one_added(main_window):
	quest = make_vanilla_like_quest()
	dlg, saved = open_editor(main_window, quest)
	dlg.ui.tb_rewards.selectRow(0)  # the Experience reward
	dlg.remove_selected_reward()
	reward = dlg.open_reward_window()
	reward.ui.box_amount_exp.setText("900")
	reward.ui.box_rewardtiming_exp.setCurrentText("Started")
	reward.finalize("Experience")
	dlg.finalize()
	(_, _, edited, _), = saved
	assert [r["type"] for r in edited["rewards"]["Success"]] == ["Item"]
	assert edited["rewards"]["Success"][0] == quest["rewards"]["Success"][1]
	assert [r["value"] for r in edited["rewards"]["Started"]] == [900]


# --- the original is never touched ---------------------------------------------------------


def test_nothing_changes_until_the_quest_is_saved(main_window):
	quest = make_vanilla_like_quest()
	snapshot = copy.deepcopy(quest)
	dlg, saved = open_editor(main_window, quest)
	dlg.ui.fld_quest_name.setText("Renamed")
	dlg.ui.tb_cond.selectRow(0)
	dlg.remove_selected_task()
	dlg.close()  # (closing without saving)
	assert saved == [] and quest == snapshot


def test_the_saved_quest_does_not_share_data_with_the_one_that_was_opened(main_window):
	quest = make_vanilla_like_quest()
	snapshot = copy.deepcopy(quest)
	_, _, saved_quest, _ = save_unchanged(main_window, quest)
	saved_quest["conditions"]["AvailableForFinish"][0]["value"] = 99
	saved_quest["rewards"]["Success"][1]["items"][0]["upd"]["StackObjectsCount"] = 99
	assert quest == snapshot


# --- the Locale tab ------------------------------------------------------------------------


def make_locale(quest):
	texts = {field: f"text for {field}" for field in LOCALE_FIELDS}
	task_texts = {c["id"]: f"task {c['id'][:2]}" for c in quest["conditions"]["AvailableForFinish"] + quest["conditions"]["AvailableForStart"]}
	return locale_builders.quest_locale(quest["_id"], texts, task_texts)


def test_the_locale_text_is_loaded_and_saved_back(main_window):
	quest = make_vanilla_like_quest()
	locale = make_locale(quest)
	dlg, saved = open_editor(main_window, quest, locale)
	assert dlg.locale_text("description") == "text for description"
	assert dlg.task_texts() == {"lv00000000000000000000aa": "task lv", "cc00000000000000000000aa": "task cc"}
	dlg.finalize()
	(_, _, _, new_locale), = saved
	assert new_locale == locale


def test_changed_locale_text_is_saved(main_window):
	quest = make_vanilla_like_quest()
	dlg, saved = open_editor(main_window, quest, make_locale(quest))
	dlg.set_locale_text("name", "A new name")
	dlg.ui.tb_cond_locale.item(0, TASK_TEXT_COLUMN).setText("A new task text")
	dlg.finalize()
	(_, _, _, new_locale), = saved
	assert new_locale[f"{quest['_id']} name"] == "A new name"
	assert new_locale["lv00000000000000000000aa"] == "A new task text"


def test_a_quest_with_no_locale_gets_blank_entries(main_window):
	# (imported quests have no locale text)
	quest = make_vanilla_like_quest()
	_, _, _, new_locale = save_unchanged(main_window, quest)
	assert new_locale == locale_builders.quest_locale(quest["_id"], {}, {"lv00000000000000000000aa": "", "cc00000000000000000000aa": ""})


# --- quests with less in them than the Builder makes ---------------------------------------


@pytest.mark.parametrize("missing", ["side", "type", "traderId", "location", "restartable", "image", "rewards", "conditions"])
def test_a_quest_missing_a_key_can_still_be_opened(main_window, missing):
	quest = make_vanilla_like_quest()
	del quest[missing]
	dlg, _ = open_editor(main_window, quest)
	assert dlg.ui.fld_quest_name.text() == "Vanilla Style"


def test_a_new_quest_is_unaffected(main_window):
	dlg = Gui_QuestDlg(main_window.state, parent=main_window)
	assert not dlg.editing
	assert dlg.windowTitle() == "Quest Builder" and dlg.ui.pb_finalize_quest.text() == "Finalize Quest"
	assert dlg.ui.tb_cond.rowCount() == 0


# --- from the main window ----------------------------------------------------------------


def add_to_main_window(main_window, quest, locale=None):
	main_window.on_quest_saved(quest["_id"], quest["QuestName"], quest, locale or {})


def select(main_window, quest_id):
	lst = main_window.ui.questList
	item = main_window.quest_list_item(quest_id)
	lst.setCurrentItem(item)
	return item


def make_second_quest():
	quest = make_vanilla_like_quest()
	quest.update(_id="60000000000000000000bbbb", QuestName="Second Quest")
	return quest


def test_the_edit_menu_item_opens_the_selected_quest(main_window):
	quest = make_vanilla_like_quest()
	add_to_main_window(main_window, quest)
	select(main_window, quest["_id"])
	main_window.ui.actionEdit_Selected_Quest.trigger()
	(dlg,) = [w for w in main_window.windows if isinstance(w, Gui_QuestDlg)]
	assert dlg.editing and dlg.quest_id == quest["_id"]
	assert dlg.ui.fld_quest_name.text() == "Vanilla Style"
	assert dlg.parent() is main_window


def test_double_clicking_a_quest_opens_it(main_window):
	quest = make_vanilla_like_quest()
	add_to_main_window(main_window, quest)
	item = select(main_window, quest["_id"])
	main_window.ui.questList.itemDoubleClicked.emit(item)
	assert main_window.quest_editors[quest["_id"]].isVisible()


def test_the_edit_menu_item_does_nothing_without_a_selection(main_window):
	add_to_main_window(main_window, make_vanilla_like_quest())
	main_window.ui.questList.clearSelection()
	main_window.ui.questList.setCurrentItem(None)
	main_window.ui.actionEdit_Selected_Quest.trigger()
	assert main_window.quest_editors == {}


def test_editing_a_quest_that_is_not_there_does_nothing(main_window):
	assert main_window.edit_quest("nope") is None
	assert main_window.edit_quest(None) is None


def test_saving_an_edit_replaces_the_quest_instead_of_adding_another(main_window):
	first, second = make_vanilla_like_quest(), make_second_quest()
	add_to_main_window(main_window, first, make_locale(first))
	add_to_main_window(main_window, second)
	dlg = main_window.edit_quest(first["_id"])
	dlg.ui.fld_quest_name.setText("Renamed")
	dlg.set_locale_text("name", "A new name")
	dlg.finalize()

	lst = main_window.ui.questList
	assert [lst.item(i).text() for i in range(lst.count())] == [
		f"Renamed, {first['_id']}",
		f"Second Quest, {second['_id']}",
	]  # (same place in the list)
	state = main_window.state
	assert list(state.quests) == [first["_id"], second["_id"]]
	assert state.quests[first["_id"]]["QuestName"] == "Renamed"
	assert state.quests[second["_id"]] == second  # the other quest is untouched
	assert state.quest_locales[first["_id"]][f"{first['_id']} name"] == "A new name"
	assert not dlg.isVisible()  # (saving closes the dialog, as for a new quest)


def test_cancelling_an_edit_changes_nothing(main_window):
	quest = make_vanilla_like_quest()
	snapshot = copy.deepcopy(quest)
	add_to_main_window(main_window, quest)
	dlg = main_window.edit_quest(quest["_id"])
	dlg.ui.fld_quest_name.setText("Renamed")
	dlg.close()
	assert main_window.state.quests[quest["_id"]] == snapshot
	assert main_window.quest_list_item(quest["_id"]).text().startswith("Vanilla Style")


def test_a_quest_already_being_edited_is_not_opened_twice(main_window):
	quest = make_vanilla_like_quest()
	add_to_main_window(main_window, quest)
	first = main_window.edit_quest(quest["_id"])
	assert main_window.edit_quest(quest["_id"]) is first
	first.close()
	assert main_window.edit_quest(quest["_id"]) is not first  # (once closed, a new one opens)


def test_two_different_quests_can_be_edited_at_once(main_window):
	first, second = make_vanilla_like_quest(), make_second_quest()
	add_to_main_window(main_window, first)
	add_to_main_window(main_window, second)
	a, b = main_window.edit_quest(first["_id"]), main_window.edit_quest(second["_id"])
	assert a is not b and a.isVisible() and b.isVisible()
	a.finalize()
	b.ui.fld_quest_name.setText("Second, renamed")
	b.finalize()
	assert main_window.state.quests[second["_id"]]["QuestName"] == "Second, renamed"
	assert main_window.state.quests[first["_id"]] == first


def test_removing_a_quest_closes_its_editor_so_it_cannot_come_back(main_window):
	quest = make_vanilla_like_quest()
	add_to_main_window(main_window, quest)
	dlg = main_window.edit_quest(quest["_id"])
	select(main_window, quest["_id"])
	main_window.remove_selected_quest()
	assert not dlg.isVisible()
	assert quest["_id"] not in main_window.state.quests
	assert main_window.ui.questList.count() == 0


def test_the_id_lookup_shows_the_new_name_after_an_edit(main_window):
	quest = make_vanilla_like_quest()
	add_to_main_window(main_window, quest)
	main_window.ui.fld_idlookup.setText(quest["_id"])
	table = main_window.ui.id_table
	assert any("Vanilla Style" in (table.item(r, 1).text() or "") for r in range(table.rowCount()))
	dlg = main_window.edit_quest(quest["_id"])
	dlg.ui.fld_quest_name.setText("Renamed Quest")
	dlg.finalize()
	assert any("Renamed Quest" in (table.item(r, 1).text() or "") for r in range(table.rowCount()))
	assert not any("Vanilla Style" in (table.item(r, 1).text() or "") for r in range(table.rowCount()))


def test_a_new_quest_still_adds_one_entry_each_time(main_window):
	for name in ("One", "Two"):
		dlg = main_window.spawnWindow("QuestBuilder")
		dlg.ui.fld_quest_name.setText(name)
		dlg.finalize()
	assert main_window.ui.questList.count() == 2
	assert len(main_window.state.quests) == 2


def test_a_quest_made_in_the_builder_can_be_edited_and_saved_unchanged(main_window):
	dlg = main_window.spawnWindow("QuestBuilder")
	dlg.ui.fld_quest_name.setText("Made here")
	task = dlg.open_task_window()
	task.ui.fld_value_lv.setText("15")
	task.finalize("Level")
	reward = dlg.open_reward_window()
	reward.ui.box_amount_exp.setText("1500")
	reward.finalize("Experience")
	dlg.set_locale_text("description", "About this quest")
	dlg.finalize()
	(quest_id, quest), = main_window.state.quests.items()
	before = copy.deepcopy(quest)
	locale_before = copy.deepcopy(main_window.state.quest_locales[quest_id])
	editor = main_window.edit_quest(quest_id)
	editor.finalize()
	assert main_window.state.quests[quest_id] == before
	assert main_window.state.quest_locales[quest_id] == locale_before
	assert main_window.ui.questList.count() == 1


# --- editing a reward from the Quest Builder ----------------------------------------------------

EXP_ID = "ex00000000000000000000aa"
ITEM_ID = "it00000000000000000000aa"


def reward_table(dlg):
	table = dlg.ui.tb_rewards
	return [(table.item(r, 0).text(), table.item(r, 1).text(), table.item(r, 2).text()) for r in range(table.rowCount())]


def row_of(dlg, reward_id):
	for row in range(dlg.ui.tb_rewards.rowCount()):
		if dlg.ui.tb_rewards.item(row, 0).text() == reward_id:
			return row


def test_the_edit_button_opens_the_selected_reward(main_window):
	dlg, _ = open_editor(main_window, make_vanilla_like_quest())
	dlg.ui.tb_rewards.selectRow(row_of(dlg, EXP_ID))
	dlg.ui.pb_edit_reward.click()
	editor = dlg.reward_editors[EXP_ID]
	assert editor.editing and editor.id == EXP_ID and editor.parent() is dlg
	assert editor.ui.box_amount_exp.text() == "5000"
	assert editor in dlg.windows


def test_double_clicking_a_reward_opens_it_without_editing_the_cell(main_window):
	dlg, _ = open_editor(main_window, make_vanilla_like_quest())
	row = row_of(dlg, ITEM_ID)
	dlg.ui.tb_rewards.cellDoubleClicked.emit(row, 0)
	assert dlg.reward_editors[ITEM_ID].isVisible()
	assert not dlg.ui.tb_rewards.editTriggers() & dlg.ui.tb_rewards.EditTrigger.DoubleClicked  # (no typing over the id)


def test_the_edit_button_does_nothing_without_a_selection(main_window):
	dlg, _ = open_editor(main_window, make_vanilla_like_quest())
	dlg.ui.tb_rewards.clearSelection()
	dlg.ui.pb_edit_reward.click()
	assert dlg.reward_editors == {}


def test_a_saved_reward_edit_replaces_the_reward_in_place(main_window):
	quest = make_vanilla_like_quest()
	dlg, saved = open_editor(main_window, quest)
	before = reward_table(dlg)
	editor = dlg.edit_reward(row_of(dlg, EXP_ID))
	editor.ui.box_amount_exp.setText("9000")
	editor.finalize("Experience")
	assert reward_table(dlg) == before  # (same rows, same order)
	dlg.finalize()
	(_, _, edited, _), = saved
	exp, item = edited["rewards"]["Success"]
	assert exp["id"] == EXP_ID and exp["value"] == 9000 and exp["index"] == 2  # (index kept)
	assert item == quest["rewards"]["Success"][1]  # (the other reward is untouched)
	assert edited["rewards"]["Started"] == [] and edited["rewards"]["Fail"] == []


def test_changing_a_rewards_timing_moves_it_to_that_list(main_window):
	quest = make_vanilla_like_quest()
	dlg, saved = open_editor(main_window, quest)
	editor = dlg.edit_reward(row_of(dlg, ITEM_ID))
	editor.ui.box_rewardtiming_item.setCurrentText("Started")
	editor.finalize("Item")
	assert (ITEM_ID, "Started", "Item") in reward_table(dlg)
	assert len(reward_table(dlg)) == 2
	dlg.finalize()
	(_, _, edited, _), = saved
	assert [r["id"] for r in edited["rewards"]["Success"]] == [EXP_ID]
	assert [r["id"] for r in edited["rewards"]["Started"]] == [ITEM_ID]
	assert edited["rewards"]["Started"][0]["items"] == quest["rewards"]["Success"][1]["items"]


def test_a_reward_of_a_kind_the_builder_cannot_make_says_so(main_window, monkeypatch):
	quest = make_vanilla_like_quest()
	quest["rewards"]["Success"].append({"id": "pk0000000000000000000000", "type": "Pockets", "index": 0, "target": "x"})
	dlg, saved = open_editor(main_window, quest)
	messages = []
	monkeypatch.setattr(
		"modules.windows.quest.QMessageBox.information", lambda *args: messages.append(args[2])
	)
	assert dlg.edit_reward(row_of(dlg, "pk0000000000000000000000")) is None
	assert dlg.reward_editors == {}
	assert "Pockets" in messages[0]
	dlg.finalize()  # (and it is kept when the quest is saved)
	assert saved[0][2] == quest


def test_a_reward_already_being_edited_is_not_opened_twice(main_window):
	dlg, _ = open_editor(main_window, make_vanilla_like_quest())
	row = row_of(dlg, EXP_ID)
	first = dlg.edit_reward(row)
	assert dlg.edit_reward(row) is first
	first.close()
	assert dlg.edit_reward(row) is not first


def test_removing_a_reward_closes_its_editor_so_it_cannot_come_back(main_window):
	quest = make_vanilla_like_quest()
	dlg, saved = open_editor(main_window, quest)
	editor = dlg.edit_reward(row_of(dlg, EXP_ID))
	dlg.ui.tb_rewards.selectRow(row_of(dlg, EXP_ID))
	dlg.remove_selected_reward()
	assert not editor.isVisible()
	assert [r[0] for r in reward_table(dlg)] == [ITEM_ID]
	dlg.finalize()
	assert [r["id"] for r in saved[0][2]["rewards"]["Success"]] == [ITEM_ID]


def test_cancelling_a_reward_edit_changes_nothing(main_window):
	quest = make_vanilla_like_quest()
	dlg, saved = open_editor(main_window, quest)
	editor = dlg.edit_reward(row_of(dlg, EXP_ID))
	editor.ui.box_amount_exp.setText("1")
	editor.close()
	dlg.finalize()
	assert saved[0][2] == quest


def test_a_reward_just_added_to_a_new_quest_can_be_edited(main_window):
	dlg = main_window.spawnWindow("QuestBuilder")
	reward = dlg.open_reward_window()
	reward.ui.box_amount_exp.setText("100")
	reward.finalize("Experience")
	editor = dlg.edit_reward(0)
	assert editor.ui.box_amount_exp.text() == "100"
	editor.ui.box_amount_exp.setText("250")
	editor.finalize("Experience")
	assert dlg.ui.tb_rewards.rowCount() == 1
	assert dlg.fields.get_multicolumn_values_list("RewardSuccess")[0]["value"] == 250
