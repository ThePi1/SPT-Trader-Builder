"""The assort form rejects numbers it can't use, and a failed add never leaves a half-added item."""

import pytest

from windows import assort
from windows.assort import ERROR_STYLE


@pytest.fixture
def form(main_window):
	dlg = main_window.spawnWindow("AssortBuilder")
	dlg.ui.ab_Item_Id.setText("5449016a4bdc2d6f028b456f")
	dlg.ui.ab_quantity.setText("5")
	dlg.ui.ab_cost_edit.setText("500")
	return dlg


def _nothing_added(dlg):
	return dlg.itemlist == [] and dlg.barterlist == {} and dlg.loyaltylist == {} and dlg.ui.ab_table.rowCount() == 0


def test_a_valid_item_is_added(form):
	form.add_item()
	assert len(form.itemlist) == 1 and len(form.barterlist) == 1 and len(form.loyaltylist) == 1
	assert form.ui.ab_table.rowCount() == 1


@pytest.mark.parametrize("bad", ["abc", "1.5", "-3", "", " ", "1 000", "²"])
def test_a_bad_cost_is_rejected_cleanly(form, bad):
	form.ui.ab_cost_edit.setText(bad)
	form.add_item()  # must not raise
	assert _nothing_added(form)
	assert form.ui.ab_cost_edit.styleSheet() == ERROR_STYLE


@pytest.mark.parametrize("bad", ["abc", "2.5", "", "-1"])
def test_a_bad_quantity_is_rejected_cleanly(form, bad):
	form.ui.ab_quantity.setText(bad)
	form.add_item()
	assert _nothing_added(form)
	assert form.ui.ab_quantity.styleSheet() == ERROR_STYLE


def test_quantity_is_not_needed_when_unlimited(form):
	form.ui.ab_unlimitedcount.setChecked(True)
	form.add_item()
	assert len(form.itemlist) == 1


def test_a_bad_buy_restriction_is_rejected_only_when_the_box_is_ticked(form):
	form.ui.ab_buyrestriction_checkbox.setChecked(True)
	form.ui.ab_buyRestriction_edit.setText("many")
	form.add_item()
	assert _nothing_added(form)
	assert form.ui.ab_buyRestriction_edit.styleSheet() == ERROR_STYLE

	form.ui.ab_buyRestriction_edit.setText("3")
	form.add_item()
	assert form.itemlist[0]["upd"]["BuyRestrictionMax"] == 3


def test_every_bad_field_is_marked_at_once(form):
	form.ui.ab_quantity.setText("x")
	form.ui.ab_cost_edit.setText("y")
	form.add_item()
	assert form.ui.ab_quantity.styleSheet() == ERROR_STYLE
	assert form.ui.ab_cost_edit.styleSheet() == ERROR_STYLE
	assert form.ui.ab_Item_Id.styleSheet() == ""


def test_marks_clear_once_the_form_is_fixed(form):
	form.ui.ab_cost_edit.setText("bad")
	form.add_item()
	form.ui.ab_cost_edit.setText("10")
	form.add_item()
	assert form.ui.ab_cost_edit.styleSheet() == ""
	assert len(form.itemlist) == 1


def test_a_failure_while_building_adds_nothing(form, monkeypatch):
	def boom(*args, **kwargs):
		raise ValueError("cannot build")

	monkeypatch.setattr(assort.assort_builders, "barter_scheme", boom)
	with pytest.raises(ValueError):
		form.add_item()
	assert form.itemlist == [] and form.barterlist == {} and form.loyaltylist == {}


# --- weapon parts and their ammo count ----------------------------------------------


@pytest.fixture
def part_form(form):
	form.ui.ab_tab.setCurrentIndex(1)
	form.ui.ab_weapmongo_edit.setEnabled(True)
	form.ui.ab_weapmongo_edit.setText("weapon_id")
	form.ui.ab_partid_edit.setText("part_tpl")
	return form


def test_a_weapon_part_is_added(part_form):
	part_form.add_item()
	assert [i["_tpl"] for i in part_form.itemlist] == ["part_tpl"]
	assert part_form.barterlist == {} and part_form.loyaltylist == {}


def test_ammo_count_is_stored_as_a_number(part_form):
	part_form.ui.ab_weap_ammo_check.setChecked(True)
	part_form.ui.ab_weap_ammo_count.setText("30")
	part_form.add_item()
	count = part_form.itemlist[0]["upd"]["StackObjectsCount"]
	assert count == 30 and isinstance(count, int)


@pytest.mark.parametrize("bad", ["", "lots", "1.5"])
def test_a_bad_ammo_count_is_rejected(part_form, bad):
	part_form.ui.ab_weap_ammo_check.setChecked(True)
	part_form.ui.ab_weap_ammo_count.setText(bad)
	part_form.add_item()
	assert part_form.itemlist == []
	assert part_form.ui.ab_weap_ammo_count.styleSheet() == ERROR_STYLE


def test_the_ammo_count_is_ignored_when_the_box_is_unticked(part_form):
	part_form.ui.ab_weap_ammo_count.setText("junk")
	part_form.add_item()
	assert len(part_form.itemlist) == 1 and "upd" not in part_form.itemlist[0]
