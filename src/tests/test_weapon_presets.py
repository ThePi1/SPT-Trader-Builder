"""The weapon builder tab records each mod's chosen slot."""

import json

import pytest


@pytest.fixture
def win(main_window, tmp_path):
	main_window.weapon_preset_filename = str(tmp_path / "preset.json")
	return main_window


def _add_base(win, name="AK", tpl="base_tpl"):
	win.ui.wb_base_check.setChecked(True)
	win.ui.wb_weaponname_edit.setText(name)
	win.ui.wb_itemid_edit.setText(tpl)
	win.addpart()


def _select_row(win, row=0):
	win.ui.wb_treeview.setCurrentIndex(win.model.index(row, 0))


def _add_mod(win, tpl, slot):
	win.ui.wb_base_check.setChecked(False)
	win.ui.wb_itemid_edit.setText(tpl)
	win.ui.wb_modslot_combo.setCurrentText(slot)
	win.addpart()


def _items(win):
	return [next(iter(entry.values())) for entry in win.weaponlist]


def test_the_base_weapon_sits_in_the_hideout(win):
	_add_base(win)
	(base,) = _items(win)
	assert base["_tpl"] == "base_tpl"
	assert base["parentId"] == "hideout" and base["slotId"] == "hideout"


def test_a_mod_records_the_slot_chosen_in_the_dropdown(win):
	_add_base(win)
	_select_row(win)
	_add_mod(win, "stock_tpl", "mod_stock")
	base, mod = _items(win)
	assert mod["_tpl"] == "stock_tpl"
	assert mod["slotId"] == "mod_stock"
	assert mod["parentId"] == base["_id"]


def test_each_mod_keeps_its_own_slot(win):
	_add_base(win)
	_select_row(win)
	_add_mod(win, "stock_tpl", "mod_stock")
	_select_row(win)
	_add_mod(win, "grip_tpl", "mod_pistol_grip")
	slots = {item["_tpl"]: item["slotId"] for item in _items(win)[1:]}
	assert slots == {"stock_tpl": "mod_stock", "grip_tpl": "mod_pistol_grip"}


def test_a_mod_on_a_mod_hangs_off_that_mod(win):
	_add_base(win)
	_select_row(win)
	_add_mod(win, "handguard_tpl", "mod_handguard")
	handguard_index = win.model.item(0, 0).child(0, 0).index()
	win.ui.wb_treeview.setCurrentIndex(handguard_index)
	_add_mod(win, "scope_tpl", "mod_scope")
	_, handguard, scope = _items(win)
	assert scope["parentId"] == handguard["_id"] and scope["slotId"] == "mod_scope"


def test_the_saved_preset_file_has_the_slots(win, tmp_path):
	_add_base(win)
	_select_row(win)
	_add_mod(win, "stock_tpl", "mod_stock")
	saved = json.loads((tmp_path / "preset.json").read_text())
	assert [next(iter(e.values()))["slotId"] for e in saved] == ["hideout", "mod_stock"]
