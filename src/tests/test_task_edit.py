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


# --- a Counter's sub-conditions --------------------------------------------------------------------


def make_subs(state):
	"""One sub-condition of every kind, like the ones SPT ships: with values the Task Builder can't make."""
	weapon_name, weapon_id = next(iter(state.weapons.items()))
	kills = conditions.kills(
		"k0000000000000000000a001",
		weapon_ids=[weapon_id, "ffffffffffffffffffffff01"],  # (the second isn't one the Builder knows)
		target="Savage",
		target_roles=["bossBully", "infectedAssault"],
		body_parts=["Head", "Chest"],
		mods_inclusive=["m1", "m2"],
		mods_exclusive=["m3"],
		distance=40,
		distance_compare="<=",
		time_from=22,
		time_to=10,
		reset_on_session_end=True,
	)
	kills.update(
		value=0,
		weaponCaliber=["5.56x45"],
		weaponModsInclusive=[["m1", "m2"]],
		enemyEquipmentInclusive=[["e1"]],
		enemyHealthEffects=[{"bodyParts": ["Head"], "effects": ["Pain"]}],
	)
	shots = conditions.shots(
		"sh000000000000000000a001",
		weapon_ids=["w1", "w2"],
		body_parts=["Head"],
		target_roles=["bossBoar"],
		mods_inclusive=["m1"],
		mods_exclusive=[],
		distance=25,
		distance_compare=">=",
		time_from=1,
		time_to=2,
		value=3,
		target="Savage",
		reset_on_session_end=True,
	)
	equipment = conditions.equipment(
		"eq000000000000000000a001",
		inclusive=[{"id": "i1", "org": "1"}, {"id": "i2", "org": "1"}, {"id": "i3", "org": "2"}],
		exclusive=[{"id": "x1", "org": "1"}],
		include_not_equipped=True,
	)
	health = conditions.health_effect(
		"he000000000000000000a001",
		body_parts=["Head", "Chest"],
		effects=["Pain", "Tremor"],
		energy=10,
		energy_compare="<=",
		hydration=20,
		hydration_compare=">=",
		time=300,
		time_compare=">=",
	)
	return {
		"VisitPlace": conditions.visit_place("vp000000000000000000a001", "zone_one"),
		"Kills": kills,
		"ExitStatus": conditions.exit_status("es000000000000000000a001", ["Survived", "Runner"]),
		"ExitName": conditions.exit_name("en000000000000000000a001", "E7_car"),
		"Location": conditions.location("lo000000000000000000a001", ["Woods", "Shoreline"]),
		"Equipment": equipment,
		"Shots": shots,
		"HealthEffect": health,
		"HealthBuff": conditions.health_buff("hb000000000000000000a001", ["Buffs_Frostbite", "Buffs_Obdolbos"]),
		"LaunchFlare": conditions.launch_flare("lf000000000000000000a001", "flare_zone"),
		"InZone": conditions.in_zone("iz000000000000000000a001", ["huntsman_013", "huntsman_020"]),
	}


SUB_KINDS = [
	"VisitPlace", "Kills", "ExitStatus", "ExitName", "Location", "Equipment", "Shots", "HealthEffect", "HealthBuff", "LaunchFlare", "InZone",
]


def counter_of(state, *kinds):
	subs = make_subs(state)
	cond = vanilla_like("CounterCreator", state)
	cond["counter"]["conditions"] = [copy.deepcopy(subs[kind]) for kind in kinds]
	return cond


def sub_row(dlg, sub_id):
	for row in range(dlg.ui.tb_cc.rowCount()):
		if dlg.ui.tb_cc.item(row, 0).text() == sub_id:
			return row


@pytest.mark.parametrize("kind", SUB_KINDS)
def test_a_sub_condition_opened_and_saved_untouched_is_unchanged(state, kind):
	cond = counter_of(state, kind)
	original = cond["counter"]["conditions"][0]
	dlg, received = open_task(state, cond)
	assert dlg.edit_subtask(0)
	dlg.cc_add(kind)
	assert dlg.fields.get_multicolumn_values_list("CounterCreator") == [original]
	assert save(dlg, received)[1] == cond
	assert dlg.sub_edit is None


def test_the_kills_form_is_filled_from_the_sub_condition(state):
	cond = counter_of(state, "Kills")
	dlg, _ = open_task(state, cond)
	dlg.edit_subtask(0)
	ui = dlg.ui
	weapon_name = next(iter(state.weapons))
	assert table_ids(ui.tb_wep) == [weapon_name, "ffffffffffffffffffffff01"]
	assert table_ids(ui.tb_targetrole) == ["bossBully", "infectedAssault"]
	assert table_ids(ui.tb_bodypart) == ["Head", "Chest"]
	assert table_ids(ui.tb_incmods) == ["m1", "m2"] and table_ids(ui.tb_excmods) == ["m3"]
	assert ui.chk_cck_usetarget.isChecked() and ui.box_targets_cck.currentText() == "Savage"
	assert (ui.fld_dist_cck.text(), ui.box_dist_compare_cck.currentText()) == ("40", "<=")
	assert (ui.fld_time_from_cck.text(), ui.fld_time_to_cck.text()) == ("22", "10")
	assert ui.chk_cck_reset_sessionend.isChecked()
	assert ui.tabWidget_4.currentWidget() is ui.tab_12
	assert ui.pb_finalize_cck.text() == "Save Subtask"


def test_the_other_sub_condition_forms(state):
	subs = make_subs(state)
	dlg, _ = open_task(state, counter_of(state, *SUB_KINDS))
	for kind in SUB_KINDS:
		assert dlg.edit_subtask(sub_row(dlg, subs[kind]["id"]))
	ui = dlg.ui
	assert ui.fld_zoneid_ccvp.text() == "zone_one" and ui.fld_exitname_ccen.text() == "E7_car" and ui.fld_fl_zone.text() == "flare_zone"
	assert table_ids(ui.tb_cces) == ["Survived", "Runner"] and table_ids(ui.tb_ccl) == ["Woods", "Shoreline"]
	assert table_ids(ui.tb_iz) == ["huntsman_013", "huntsman_020"]
	assert table_ids(ui.tb_hb) == ["Buffs_Frostbite", "Buffs_Obdolbos"]
	assert table_ids(ui.tb_eq_inc) == ["i1", "i2", "i3"] and table_ids(ui.tb_eq_exc) == ["x1"] and ui.cb_eq_uneq.isChecked()
	assert [ui.tb_eq_inc.item(r, 1).text() for r in range(3)] == ["1", "1", "2"]
	assert table_ids(ui.tb_sh_wep) == ["w1", "w2"] and table_ids(ui.tb_sh_bp) == ["Head"] and table_ids(ui.tb_incmod_sh) == ["m1"]
	assert (ui.fld_dist_sh.text(), ui.fld_value_sh.text(), ui.box_target_sh.currentText()) == ("25", "3", "Savage")
	assert table_ids(ui.tb_hebp) == ["Head", "Chest"] and table_ids(ui.tb_heef) == ["Pain", "Tremor"]
	assert (ui.fld_enval_he.text(), ui.box_encomp_he.currentText(), ui.fld_timeval_he.text()) == ("10", "<=", "300")


def test_a_changed_field_is_replaced_and_the_rest_is_kept(state):
	cond = counter_of(state, "Kills")
	original = cond["counter"]["conditions"][0]
	dlg, received = open_task(state, cond)
	dlg.edit_subtask(0)
	dlg.ui.fld_dist_cck.setText("100")
	dlg.cc_add("Kills")
	_, saved = save(dlg, received)
	edited = saved["counter"]["conditions"][0]
	expected = copy.deepcopy(original)
	expected["distance"] = {"compareMethod": "<=", "value": 100}
	assert edited == expected  # (value 0, the OR-group of mods, the caliber, ... are all as they were)


def test_changing_the_mods_replaces_the_groups(state):
	cond = counter_of(state, "Kills")
	dlg, received = open_task(state, cond)
	dlg.edit_subtask(0)
	dlg.ui.fld_incmod_cck.setText("m9")
	dlg.ui.pb_add_imod.click()
	dlg.cc_add("Kills")
	edited = save(dlg, received)[1]["counter"]["conditions"][0]
	assert edited["weaponModsInclusive"] == [["m1"], ["m2"], ["m9"]]
	assert edited["weaponModsExclusive"] == [["m3"]] and edited["weaponCaliber"] == ["5.56x45"]


def test_a_weapon_the_builder_does_not_know_is_kept(state):
	cond = counter_of(state, "Kills")
	dlg, received = open_task(state, cond)
	dlg.edit_subtask(0)
	dlg.ui.tb_wep.selectRow(0)
	remove_selected_table_item(dlg.fields, type="KillsWep", table=dlg.ui.tb_wep)
	dlg.cc_add("Kills")
	assert save(dlg, received)[1]["counter"]["conditions"][0]["weapon"] == ["ffffffffffffffffffffff01"]


def test_the_save_button_goes_back_and_the_edit_ends_when_saved(state):
	dlg, _ = open_task(state, counter_of(state, "ExitName", "VisitPlace"))
	original_text = dlg.ui.pb_finalize_ccen.text()
	dlg.edit_subtask(0)
	assert dlg.ui.pb_finalize_ccen.text() == "Save Subtask" and dlg.sub_edit is not None
	dlg.cc_add("ExitName")
	assert dlg.ui.pb_finalize_ccen.text() == original_text and dlg.sub_edit is None
	dlg.cc_add("ExitName")  # (pressing it again makes a new subtask, it doesn't edit the old one again)
	assert dlg.ui.tb_cc.rowCount() == 3


def test_a_sub_condition_of_another_kind_can_be_added_while_one_is_being_edited(state):
	dlg, _ = open_task(state, counter_of(state, "ExitName"))
	dlg.edit_subtask(0)
	dlg.ui.fld_zoneid_ccvp.setText("a new zone")
	dlg.cc_add("VisitPlace")  # (a different kind: this adds a new subtask, and the edit stays open)
	assert dlg.ui.tb_cc.rowCount() == 2 and dlg.sub_edit is not None


def test_opening_another_sub_condition_drops_the_first_edit(state):
	dlg, received = open_task(state, counter_of(state, "ExitName", "VisitPlace"))
	dlg.edit_subtask(0)
	dlg.ui.fld_exitname_ccen.setText("changed but never saved")
	dlg.edit_subtask(1)
	assert dlg.sub_edit["type"] == "VisitPlace" and dlg.ui.pb_finalize_ccen.text() != "Save Subtask"
	assert save(dlg, received)[1]["counter"]["conditions"][0]["exitName"] == "E7_car"


def test_the_forms_tables_are_replaced_not_added_to(state):
	cond = counter_of(state, "Location")
	cond["counter"]["conditions"].append(conditions.location("lo000000000000000000a002", ["Interchange"]))
	dlg, _ = open_task(state, cond)
	dlg.edit_subtask(0)
	assert table_ids(dlg.ui.tb_ccl) == ["Woods", "Shoreline"]
	dlg.edit_subtask(1)
	assert table_ids(dlg.ui.tb_ccl) == ["Interchange"]


def test_removing_the_sub_condition_being_edited_ends_the_edit(state):
	dlg, _ = open_task(state, counter_of(state, "ExitName", "VisitPlace"))
	dlg.edit_subtask(0)
	dlg.ui.tb_cc.selectRow(0)
	dlg.remove_selected_subtask()
	assert dlg.sub_edit is None and dlg.ui.pb_finalize_ccen.text() != "Save Subtask"
	dlg.cc_add("ExitName")  # (a new one, not the removed one back)
	assert [s["conditionType"] for s in dlg.fields.get_multicolumn_values_list("CounterCreator")] == ["VisitPlace", "ExitName"]


def test_the_edit_button_and_double_click_open_a_sub_condition(state):
	dlg, _ = open_task(state, counter_of(state, "ExitName", "VisitPlace"))
	dlg.ui.tb_cc.selectRow(1)
	dlg.ui.pb_edit_cc.click()
	assert dlg.sub_edit["type"] == "VisitPlace"
	dlg.ui.tb_cc.cellDoubleClicked.emit(0, 0)
	assert dlg.sub_edit["type"] == "ExitName"
	assert not dlg.ui.tb_cc.editTriggers() & dlg.ui.tb_cc.EditTrigger.DoubleClicked
	dlg.finish_sub_edit()
	dlg.ui.tb_cc.clearSelection()
	dlg.ui.pb_edit_cc.click()
	assert dlg.sub_edit is None


def test_a_sub_condition_of_a_kind_the_builder_cannot_make_says_so(state, monkeypatch):
	cond = counter_of(state, "VisitPlace")
	arena = {"id": "ar000000000000000000a001", "conditionType": "ArenaMatchPlace", "compareMethod": "==", "value": 1, "dynamicLocale": False}
	cond["counter"]["conditions"].append(arena)
	dlg, received = open_task(state, cond)
	messages = []
	monkeypatch.setattr("modules.windows.task.QMessageBox.information", lambda *args: messages.append(args[2]))
	assert not dlg.edit_subtask(1)
	assert "ArenaMatchPlace" in messages[0] and dlg.sub_edit is None
	assert save(dlg, received)[1] == cond  # (and it is kept)


def test_a_sub_condition_just_added_can_be_edited(state):
	dlg = Gui_TaskDlg(state)
	dlg.ui.fld_exitname_ccen.setText("first")
	dlg.cc_add("ExitName")
	dlg.edit_subtask(0)
	dlg.ui.fld_exitname_ccen.setText("second")
	dlg.cc_add("ExitName")
	subs = dlg.fields.get_multicolumn_values_list("CounterCreator")
	assert len(subs) == 1 and subs[0]["exitName"] == "second"
