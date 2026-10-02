"""Editing an existing task (a quest condition) in the Task Builder."""

import copy

import pytest

from modules.builders import conditions
from modules.config import load_config
from modules.state import AppState
from modules.table_fields import remove_selected_table_item
from modules.windows.task import FINISH_BUTTONS, TASK_TABS, Gui_TaskDlg, can_edit, dialog_type


@pytest.fixture
def state(qapp):
	return AppState.load(load_config())


def open_task(state, condition, timing="Finish"):
	"""An edit dialog for condition, and the list its condition_ready signals are collected in."""
	dlg = Gui_TaskDlg(state, condition=condition, timing=timing)
	received = []
	dlg.condition_ready.connect(lambda *args: received.append(args))
	return dlg, received


def save(dlg, received):
	dlg.finalize(dialog_type(dlg.original))
	(timing, kind, cond_id, cond), = received
	assert kind == dialog_type(dlg.original) and cond_id == dlg.original["id"]
	return timing, cond


def table_ids(table):
	return [table.item(row, 0).text() for row in range(table.rowCount())]


VIS = [{"conditionType": "CompleteCondition", "id": "bb0000000000000000000001", "target": "tt0000000000000000000001"}]


def vanilla_like(kind, state):
	"""A condition like the ones SPT ships: values the Task Builder can't make, and keys it never writes."""
	prapor = state.traders["Prapor"]
	item_args = dict(
		parent_id="",
		targets=["5449016a4bdc2d6f028b456f", "5448e8d04bdc2ddf718b4569"],
		value=3,
		min_durability=0,
		max_durability=100,
		only_found_in_raid=True,
		visibility_conditions=copy.deepcopy(VIS),
	)
	made = {
		"Level": conditions.level("c0000000000000000000a001", compare_method=">=", value=15),
		"Quest": conditions.quest_status("c0000000000000000000a002", available_after=36000, status_ids=[4, 2], target="5936d90786f7742b1420ba5b"),
		"TraderStanding": conditions.trader_standing("c0000000000000000000a003", compare_method="<=", trader_id=prapor, value=-1),
		"TraderLoyalty": conditions.trader_loyalty("c0000000000000000000a004", compare_method=">=", parent_id="", trader_id=prapor, value=3, visibility_conditions=copy.deepcopy(VIS)),
		"Skill": conditions.skill("c0000000000000000000a005", compare_method=">=", parent_id="", target="Strength", value=5, visibility_conditions=copy.deepcopy(VIS)),
		"FindItem": conditions.find_item("c0000000000000000000a006", **item_args),
		"HandoverItem": conditions.handover_item("c0000000000000000000a007", **item_args),
		"LeaveItemAtLocation": conditions.leave_item_at_location("c0000000000000000000a008", plant_time=30, zone_id="zone_a", **item_args),
		"PlaceBeacon": conditions.place_beacon("c0000000000000000000a009", parent_id="", plant_time=15, value=1, zone_id="zone_b", visibility_conditions=copy.deepcopy(VIS)),
		"CounterCreator": conditions.counter_creator(
			"c0000000000000000000a00a",
			counter_id="cn0000000000000000000a00",
			sub_conditions=[
				conditions.visit_place("s00000000000000000000a01", "zone_one"),
				conditions.exit_status("s00000000000000000000a02", ["Survived", "Runner"]),
			],
			parent_id="",
			quest_type="Exploration",
			value=2,
			visibility_conditions=copy.deepcopy(VIS),
		),
	}[kind]
	made["index"] = 3
	made["somethingNew"] = {"a": 1}
	return made


KINDS = ["Level", "Quest", "TraderStanding", "TraderLoyalty", "Skill", "FindItem", "HandoverItem", "LeaveItemAtLocation", "PlaceBeacon", "CounterCreator"]


# --- nothing is lost on the way through -----------------------------------------------------


@pytest.mark.parametrize("kind", KINDS)
def test_saving_an_untouched_task_gives_back_exactly_the_same_task(state, kind):
	cond = vanilla_like(kind, state)
	timing = "Start" if kind in ("Level", "TraderStanding") else "Finish"
	dlg, received = open_task(state, cond, timing)
	saved_timing, saved = save(dlg, received)
	assert saved == cond
	assert saved_timing == timing


def test_the_hard_coded_values_of_vanilla_tasks_survive(state):
	cond = vanilla_like("CounterCreator", state)
	cond.update(oneSessionOnly=True, doNotResetIfCounterCompleted=True, globalQuestCounterId="gq", value="2")
	cond["counter"]["id"] = "original-counter-id"
	dlg, received = open_task(state, cond)
	assert save(dlg, received)[1] == cond
	item = vanilla_like("HandoverItem", state)
	item.update(dogtagLevel=50, isEncoded=True, value="3")
	dlg, received = open_task(state, item)
	assert save(dlg, received)[1] == item
	quest = vanilla_like("Quest", state)
	quest.update(dispersion=3600, status=["4", "2"], visibilityConditions=copy.deepcopy(VIS))
	dlg, received = open_task(state, quest, "Start")
	assert save(dlg, received)[1] == quest
	beacon = vanilla_like("PlaceBeacon", state)
	beacon["target"] = ["63a0b2eabea67a6d93009e52"]  # (the Radio Repeater)
	dlg, received = open_task(state, beacon)
	assert save(dlg, received)[1] == beacon


def test_values_the_builder_does_not_offer_are_kept(state):
	standing = vanilla_like("TraderStanding", state)
	standing["compareMethod"] = "<"
	standing["target"] = "ffffffffffffffffffffffff"
	dlg, received = open_task(state, standing, "Fail")
	assert (dlg.ui.box_comparemethod_ts.currentText(), dlg.ui.box_trader_ts.currentText()) == ("<", "ffffffffffffffffffffffff")
	timing, saved = save(dlg, received)
	assert saved == standing and timing == "Fail"  # (a start-only kind keeps the list it was in)
	skill = vanilla_like("Skill", state)
	skill["target"] = "Search"
	dlg, received = open_task(state, skill)
	assert save(dlg, received)[1] == skill
	quest = vanilla_like("Quest", state)
	quest["status"] = [4, 42]
	dlg, received = open_task(state, quest, "Start")
	assert save(dlg, received)[1] == quest


@pytest.mark.parametrize(
	"kind", ["Skill", "FindItem", "HandoverItem", "LeaveItemAtLocation", "PlaceBeacon", "TraderLoyalty", "CounterCreator", "Quest"]
)
@pytest.mark.parametrize("timing", ["Start", "Finish", "Fail"])
def test_a_task_saved_untouched_stays_in_the_list_it_was_in(state, kind, timing):
	dlg, received = open_task(state, vanilla_like(kind, state), timing)
	assert save(dlg, received)[0] == timing


def test_a_trader_loyalty_start_condition_keeps_its_timing(state):
	dlg, received = open_task(state, vanilla_like("TraderLoyalty", state), "Start")
	assert dlg.ui.box_ff_tl.currentText() == "Start"
	assert save(dlg, received)[0] == "Start"


# --- the form is filled from the task ----------------------------------------------------------


def test_the_simple_forms(state):
	ui = open_task(state, vanilla_like("Level", state), "Start")[0].ui
	assert (ui.box_compare_lv.currentText(), ui.fld_value_lv.text()) == (">=", "15")
	dlg = open_task(state, vanilla_like("Quest", state), "Start")[0]
	ui = dlg.ui
	assert (ui.fld_tid_qs.text(), ui.fld_avail_qs.text(), ui.box_timing_qs.currentText()) == ("5936d90786f7742b1420ba5b", "36000", "Start")
	assert table_ids(ui.tb_status_qs) == ["Success", "Started"]
	ui = open_task(state, vanilla_like("TraderStanding", state), "Start")[0].ui
	assert (ui.box_trader_ts.currentText(), ui.box_comparemethod_ts.currentText(), ui.fld_value_ts.text()) == ("Prapor", "<=", "-1")
	ui = open_task(state, vanilla_like("TraderLoyalty", state))[0].ui
	assert (ui.box_target_tl.currentText(), ui.box_compare_tl.currentText(), ui.fld_level_tl.text()) == ("Prapor", ">=", "3")
	ui = open_task(state, vanilla_like("Skill", state))[0].ui
	assert (ui.box_target_sk.currentText(), ui.fld_level_sk.text(), ui.box_ff_sk.currentText()) == ("Strength", "5", "Finish")


def test_the_item_forms(state):
	for kind in ("FindItem", "HandoverItem"):
		dlg, _ = open_task(state, vanilla_like(kind, state), "Fail")
		ui = dlg.ui
		assert ui.box_hofind_it.currentText() == kind and not ui.box_hofind_it.isEnabled()
		assert table_ids(ui.tb_items) == ["5449016a4bdc2d6f028b456f", "5448e8d04bdc2ddf718b4569"]
		assert (ui.fld_quantity_it.text(), ui.fld_mindur_it.text(), ui.fld_maxdur_it.text()) == ("3", "0", "100")
		assert (ui.box_only_fir_it.currentText(), ui.box_ff_it.currentText()) == ("true", "Fail")
		assert table_ids(ui.tb_vis) == ["tt0000000000000000000001"]


def test_the_leave_item_and_beacon_forms(state):
	ui = open_task(state, vanilla_like("LeaveItemAtLocation", state))[0].ui
	assert (ui.fld_zoneid_li.text(), ui.fld_plant_time_li.text(), ui.fld_quantity_li.text()) == ("zone_a", "30", "3")
	assert table_ids(ui.tb_li_target) == ["5449016a4bdc2d6f028b456f", "5448e8d04bdc2ddf718b4569"]
	ui = open_task(state, vanilla_like("PlaceBeacon", state))[0].ui
	assert (ui.fld_zoneid_pb.text(), ui.sb_time_pb.value(), ui.sb_value_pb.value()) == ("zone_b", 15, 1)


def test_the_counter_form_and_its_sub_conditions(state):
	dlg, _ = open_task(state, vanilla_like("CounterCreator", state))
	ui = dlg.ui
	assert (ui.box_cc_qtlab.currentText(), ui.fld_quantity_cc.text(), ui.box_ff.currentText()) == ("Exploration", "2", "Finish")
	assert table_ids(ui.tb_cc) == ["s00000000000000000000a01", "s00000000000000000000a02"]
	assert [ui.tb_cc.item(r, 1).text() for r in range(2)] == ["VisitPlace", "ExitStatus"]


@pytest.mark.parametrize("kind", KINDS)
def test_only_the_tasks_own_tab_can_be_used(state, kind):
	cond = vanilla_like(kind, state)
	dlg, _ = open_task(state, cond)
	for tabs_name, page_name in TASK_TABS[dialog_type(cond)]:
		tabs = getattr(dlg.ui, tabs_name)
		page = getattr(dlg.ui, page_name)
		assert tabs.currentWidget() is page
		assert [tabs.isTabEnabled(i) for i in range(tabs.count())] == [tabs.widget(i) is page for i in range(tabs.count())]
	assert getattr(dlg.ui, FINISH_BUTTONS[dialog_type(cond)]).text() == "Save Changes"
	assert dlg.windowTitle() == "Edit Task" and dlg.id == cond["id"]


# --- changes -----------------------------------------------------------------------------------


def test_only_the_changed_fields_are_replaced(state):
	cond = vanilla_like("Skill", state)
	cond["value"] = "5"  # (a number written as text)
	dlg, received = open_task(state, cond)
	dlg.ui.box_compare_sk.setCurrentText("<=")
	timing, saved = save(dlg, received)
	expected = copy.deepcopy(cond)
	expected["compareMethod"] = "<="
	assert saved == expected


def test_a_changed_number_replaces_the_text_one(state):
	cond = vanilla_like("Skill", state)
	cond["value"] = "5"
	dlg, received = open_task(state, cond)
	dlg.ui.fld_level_sk.setText("7")
	assert save(dlg, received)[1]["value"] == 7


def test_the_timing_can_be_changed(state):
	dlg, received = open_task(state, vanilla_like("Skill", state), "Finish")
	dlg.ui.box_ff_sk.setCurrentText("Fail")
	assert save(dlg, received)[0] == "Fail"


def test_items_can_be_removed_and_added(state):
	cond = vanilla_like("HandoverItem", state)
	dlg, received = open_task(state, cond)
	dlg.ui.tb_items.selectRow(0)
	remove_selected_table_item(dlg.fields, type="HFItems", table=dlg.ui.tb_items)
	dlg.ui.fld_itemid_it.setText("590c661e86f7741e566b646a")
	dlg.ui.pb_additem_it.click()
	_, saved = save(dlg, received)
	assert saved["target"] == ["5448e8d04bdc2ddf718b4569", "590c661e86f7741e566b646a"]
	assert saved["index"] == 3 and saved["somethingNew"] == {"a": 1}


def test_a_quest_task_status_can_be_changed(state):
	cond = vanilla_like("Quest", state)
	cond["status"] = ["4", "2"]
	dlg, received = open_task(state, cond, "Start")
	dlg.ui.box_status_qs.setCurrentText("Fail")
	dlg.ui.pb_addstatus_qs.click()
	_, saved = save(dlg, received)
	assert saved["status"] == [4, 2, 5]


# --- visibility conditions -----------------------------------------------------------------------


def test_visibility_conditions_that_were_there_keep_their_ids(state):
	dlg, received = open_task(state, vanilla_like("Skill", state))
	dlg.ui.fld_visibility_targetid.setText("tt0000000000000000000002")
	dlg.ui.pb_addvis.click()
	_, saved = save(dlg, received)
	visibility = saved["visibilityConditions"]
	assert visibility[0] == VIS[0]  # (same id as before)
	assert visibility[1]["target"] == "tt0000000000000000000002" and visibility[1]["id"] != VIS[0]["id"]
	assert visibility[1]["conditionType"] == "CompleteCondition"


def test_a_visibility_condition_can_be_removed(state):
	dlg, received = open_task(state, vanilla_like("Skill", state))
	dlg.ui.tb_vis.selectRow(0)
	remove_selected_table_item(dlg.fields, type="VisibilityCond", table=dlg.ui.tb_vis)
	assert save(dlg, received)[1]["visibilityConditions"] == []


def test_visibility_conditions_written_as_plain_ids_by_an_older_version_are_kept(state):
	cond = vanilla_like("Skill", state)
	cond["visibilityConditions"] = ["tt0000000000000000000001"]
	dlg, received = open_task(state, cond)
	assert table_ids(dlg.ui.tb_vis) == ["tt0000000000000000000001"]
	assert save(dlg, received)[1] == cond


# --- counters ------------------------------------------------------------------------------------


def test_a_sub_condition_can_be_removed_and_one_added_to_a_counter(state):
	cond = vanilla_like("CounterCreator", state)
	cond["counter"]["id"] = "original-counter-id"
	dlg, received = open_task(state, cond)
	dlg.ui.tb_cc.selectRow(0)
	remove_selected_table_item(dlg.fields, type="CounterCreator", table=dlg.ui.tb_cc)
	dlg.ui.fld_exitname_ccen.setText("E7_car")
	dlg.cc_add("ExitName")
	_, saved = save(dlg, received)
	subs = saved["counter"]["conditions"]
	assert [s["conditionType"] for s in subs] == ["ExitStatus", "ExitName"]
	assert subs[0] == cond["counter"]["conditions"][1]  # (the untouched one is exactly as it was)
	assert saved["counter"]["id"] == "original-counter-id"


# --- the original is never touched -------------------------------------------------------------


def test_nothing_changes_until_the_task_is_saved(state):
	cond = vanilla_like("CounterCreator", state)
	snapshot = copy.deepcopy(cond)
	dlg, received = open_task(state, cond)
	dlg.ui.fld_quantity_cc.setText("99")
	dlg.close()
	assert received == [] and cond == snapshot


def test_the_saved_task_does_not_share_data_with_the_one_that_was_opened(state):
	cond = vanilla_like("CounterCreator", state)
	snapshot = copy.deepcopy(cond)
	dlg, received = open_task(state, cond)
	_, saved = save(dlg, received)
	saved["counter"]["conditions"][0]["target"] = "changed"
	assert cond == snapshot


# --- other kinds, and new tasks -------------------------------------------------------------------


@pytest.mark.parametrize("kind", ["WeaponAssembly", "SellItemToTrader", "HideoutArea", "Nonsense"])
def test_tasks_the_builder_cannot_make_cannot_be_opened(state, kind):
	cond = {"id": "x", "conditionType": kind, "index": 0}
	assert not can_edit(cond)
	with pytest.raises(ValueError):
		Gui_TaskDlg(state, condition=cond, timing="Finish")


def test_a_new_task_is_unaffected(state, fixed_ids):
	dlg = Gui_TaskDlg(state)
	assert not dlg.editing
	assert dlg.ui.tabWidget_2.isTabEnabled(0) and dlg.ui.tabWidget_2.isTabEnabled(1) and dlg.ui.tabWidget_2.isTabEnabled(2)
	assert dlg.ui.box_hofind_it.isEnabled() and dlg.windowTitle() != "Edit Task"
	assert dlg.ui.pb_finalize_lv.text() != "Save Changes"
