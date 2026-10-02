"""Every Add/Remove button pair in the Task dialog adds and removes the same data."""

import pytest
from PySide6.QtWidgets import QLineEdit

from modules.windows.task import Gui_TaskDlg

# (add button, remove button, table, input fields to fill in)
PAIRS = [
	("pb_addwep_cck", "pb_removewep_cck", "tb_wep", []),
	("pb_addtr_cck", "pb_removetr_cck", "tb_targetrole", []),
	("pb_addbp_cck", "pb_rembp_cck", "tb_bodypart", []),
	("pb_add_imod", "pb_rem_imod", "tb_incmods", ["fld_incmod_cck"]),
	("pb_add_emod", "pb_rem_emod", "tb_excmods", ["fld_excmod_cck"]),
	("pb_cces_add", "pb_status_rem_cces", "tb_cces", []),
	("pb_add_ccl", "pb_rem_ccl", "tb_ccl", []),
	("pb_addvis", "pb_remvis", "tb_vis", ["fld_visibility_targetid"]),
	("pb_additem_it", "pb_remitem_it", "tb_items", ["fld_itemid_it"]),
	("pb_addstatus_qs", "pb_remstatus_qs", "tb_status_qs", []),
	("pb_add_li_target", "pb_rem_li_target", "tb_li_target", ["fld_li_target"]),
	("pb_add_eqi", "pb_rem_eqi", "tb_eq_inc", ["fld_eqi", "fld_equi_org"]),
	("pb_add_eqe", "pb_rem_eqe", "tb_eq_exc", ["fld_eqi_2", "fld_eqe_org"]),
	("pb_add_shbp", "pb_rem_shbp", "tb_sh_bp", []),
	("pb_add_shtr", "pb_rem_shtr", "tb_sh_tr", []),
	("pb_add_shw", "pb_rem_shw", "tb_sh_wep", ["fld_shw"]),
	("pb_add_shmi", "pb_rem_shmi", "tb_incmod_sh", ["fld_shmi"]),
	("pb_add_shme", "pb_rem_shme", "tb_excmod_sh", ["fld_shme"]),
	("pb_add_hebp", "pb_rem_hebp", "tb_hebp", []),
	("pb_add_heef", "pb_rem_heef", "tb_heef", []),
	("pb_add_hb", "pb_rem_hb", "tb_hb", []),
	("pb_add_iz", "pb_rem_iz", "tb_iz", ["fld_iz"]),
]


@pytest.fixture
def task(main_window):
	return main_window.spawnWindow("QuestBuilder").open_task_window()


@pytest.mark.parametrize("add, remove, table, inputs", PAIRS, ids=[p[2] for p in PAIRS])
def test_add_then_remove_leaves_nothing_behind(task, add, remove, table, inputs):
	for name in inputs:
		field = getattr(task.ui, name)
		assert isinstance(field, QLineEdit)
		field.setText("value_" + name)
	getattr(task.ui, add).released.emit()
	table_widget = getattr(task.ui, table)
	assert table_widget.rowCount() == 1
	assert any(task.fields.data.values()), "the row's data was not stored"

	table_widget.selectRow(0)
	getattr(task.ui, remove).released.emit()

	assert table_widget.rowCount() == 0
	assert not any(task.fields.data.values()), f"removed row is still stored: {task.fields.data}"


def test_a_removed_excluded_mod_is_not_exported(task):
	task.ui.fld_excmod_cck.setText("mod_a")
	task.ui.pb_add_emod.released.emit()
	task.ui.fld_excmod_cck.setText("mod_b")
	task.ui.pb_add_emod.released.emit()
	task.ui.tb_excmods.selectRow(0)  # mod_a
	task.ui.pb_rem_emod.released.emit()

	task.cc_add("Kills")
	(kills,) = task.fields.get_multicolumn_values_list("CounterCreator")
	assert kills["weaponModsExclusive"] == [["mod_b"]]


def test_adding_the_same_mod_twice_is_exported_once(task):
	for _ in range(2):
		task.ui.fld_incmod_cck.setText("mod_a")
		task.ui.pb_add_imod.released.emit()
	assert task.ui.tb_incmods.rowCount() == 1
	task.cc_add("Kills")
	(kills,) = task.fields.get_multicolumn_values_list("CounterCreator")
	assert kills["weaponModsInclusive"] == [["mod_a"]]


def test_re_adding_an_equipment_item_updates_its_group(task):
	task.ui.fld_eqi.setText("item1")
	task.ui.fld_equi_org.setText("group1")
	task.ui.pb_add_eqi.released.emit()
	task.ui.fld_equi_org.setText("group2")
	task.ui.pb_add_eqi.released.emit()  # same item, new group, nothing selected
	assert task.ui.tb_eq_inc.rowCount() == 1
	assert task.ui.tb_eq_inc.item(0, 1).text() == "group2"
	task.cc_add("Equipment")
	(equipment,) = task.fields.get_multicolumn_values_list("CounterCreator")
	assert equipment["equipmentInclusive"] == [["item1"]]


def test_shots_weapons_are_exported(task):
	task.ui.fld_shw.setText("weapon_tpl_1")
	task.ui.pb_add_shw.released.emit()
	task.ui.fld_shw.setText("weapon_tpl_2")
	task.ui.pb_add_shw.released.emit()
	task.cc_add("Shots")
	(shots,) = task.fields.get_multicolumn_values_list("CounterCreator")
	assert shots["weapon"] == ["weapon_tpl_1", "weapon_tpl_2"]


def test_shots_with_no_weapons_exports_an_empty_list(task):
	task.cc_add("Shots")
	(shots,) = task.fields.get_multicolumn_values_list("CounterCreator")
	assert shots["weapon"] == []


# --- LeaveItemAtLocation durability -----------------------------------------------------


def _leave_item(task, **fields):
	got = []
	task.condition_ready.connect(lambda *args: got.append(args))
	for name, text in fields.items():
		getattr(task.ui, name).setText(text)
	task.finalize("LeaveItemAtLocation")
	return got[0][3]


def test_leave_item_min_and_max_durability_are_read_from_their_own_fields(task):
	cond = _leave_item(task, fld_mindur_li="30", fld_maxdur_li="80")
	assert (cond["minDurability"], cond["maxDurability"]) == (30, 80)


def test_leave_item_blank_durabilities_default_to_0_and_100(task):
	cond = _leave_item(task)
	assert (cond["minDurability"], cond["maxDurability"]) == (0, 100)


def test_leave_item_min_alone_does_not_change_max(task):
	cond = _leave_item(task, fld_mindur_li="30")
	assert (cond["minDurability"], cond["maxDurability"]) == (30, 100)


def test_leave_item_max_alone_does_not_change_min(task):
	cond = _leave_item(task, fld_maxdur_li="60")
	assert (cond["minDurability"], cond["maxDurability"]) == (0, 60)
