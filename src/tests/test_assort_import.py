"""Importing an assort file, removing items from it, and what the table shows."""

import json

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog, QMessageBox

from modules.builders import assort as assort_builders

ROUBLES, USD, EUROS = assort_builders.ROUBLES_TPL, assort_builders.USD_TPL, assort_builders.EUROS_TPL
USER_ROLE = Qt.ItemDataRole.UserRole


def part(item_id, parent, slot):
	return {"_id": item_id, "_tpl": f"tpl_{item_id}", "parentId": parent, "slotId": slot}


def root(item_id, qty):
	return {
		"_id": item_id,
		"_tpl": f"tpl_{item_id}",
		"parentId": "hideout",
		"slotId": "hideout",
		"upd": {"StackObjectsCount": qty, "UnlimitedCount": False},
	}


def price(tpl, count):
	return [[{"count": count, "_tpl": tpl}]]


# two weapons for sale; the first has a mod, which has a mod of its own
ASSORT = {
	"items": [
		root("gun1", 1),
		part("stock1", "gun1", "mod_stock"),
		part("scope1", "stock1", "mod_scope"),
		root("gun2", 2),
		part("grip2", "gun2", "mod_pistol_grip"),
	],
	"barter_scheme": {"gun1": price(ROUBLES, 1000), "gun2": price(USD, 20)},
	"loyal_level_items": {"gun1": 1, "gun2": 3},
}


@pytest.fixture
def dialogs(monkeypatch):
	"""Record message boxes; the file dialog and the 'replace?' question are set per test."""
	state = {"errors": [], "questions": [], "answer": QMessageBox.StandardButton.Yes, "file": None}
	monkeypatch.setattr(
		QMessageBox, "critical", staticmethod(lambda parent, title, text: state["errors"].append(text))
	)

	def question(parent, title, text):
		state["questions"].append(text)
		return state["answer"]

	monkeypatch.setattr(QMessageBox, "question", staticmethod(question))
	monkeypatch.setattr(
		QFileDialog, "getOpenFileName", staticmethod(lambda *a, **k: (str(state["file"]) if state["file"] else "", ""))
	)
	return state


@pytest.fixture
def window(main_window):
	return main_window.spawnWindow("AssortBuilder")


def import_file(window, dialogs, tmp_path, data, name="in.json"):
	f = tmp_path / name
	f.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")
	dialogs["file"] = f
	window.onImportAssort()


def rows(window):
	"""(own id, parent id, quantity, cost, loyalty, currency) for every row."""
	table = window.ui.ab_table
	return [
		(
			table.item(r, 1).data(USER_ROLE),
			table.item(r, 0).data(USER_ROLE),
			table.item(r, 1).text(),
			table.item(r, 2).text(),
			table.item(r, 3).text(),
			table.item(r, 5).text(),
		)
		for r in range(table.rowCount())
	]


def ids(window):
	return sorted(row[0] for row in rows(window))


def select(window, item_id):
	table = window.ui.ab_table
	for r in range(table.rowCount()):
		if table.item(r, 1).data(USER_ROLE) == item_id:
			table.setCurrentCell(r, 0)
			table.selectRow(r)
			return
	raise AssertionError(f"{item_id} is not in the table")


# --- what an import shows -------------------------------------------------------------------


def test_every_item_becomes_a_row_with_its_own_id_and_its_parents(window, dialogs, tmp_path):
	import_file(window, dialogs, tmp_path, ASSORT)
	by_id = {r[0]: r for r in rows(window)}
	assert set(by_id) == {"gun1", "stock1", "scope1", "gun2", "grip2"}
	assert by_id["gun1"][1] is None and by_id["gun2"][1] is None  # root items have no parent
	assert by_id["stock1"][1] == "gun1" and by_id["scope1"][1] == "stock1"


def test_prices_and_loyalty_are_shown_for_items_for_sale(window, dialogs, tmp_path):
	import_file(window, dialogs, tmp_path, ASSORT)
	by_id = {r[0]: r for r in rows(window)}
	assert by_id["gun1"][2:] == ("1", "1000", "1", "Roubles")
	assert by_id["gun2"][2:] == ("2", "20", "3", "USD")
	assert by_id["stock1"][3:] == ("", "", "")  # (a mod has no price)


@pytest.mark.parametrize(
	"tpl, label",
	[(ROUBLES, "Roubles"), (USD, "USD"), (EUROS, "Euros"), ("some_barter_item_tpl", "Item"), ("cash", "Undefined")],
)
def test_the_currency_label_matches_what_the_form_uses(window, dialogs, tmp_path, tpl, label):
	data = {"items": [root("x", 1)], "barter_scheme": {"x": price(tpl, 5)}, "loyal_level_items": {"x": 1}}
	import_file(window, dialogs, tmp_path, data)
	assert rows(window)[0][5] == label


def test_an_imported_item_barter_looks_the_same_as_one_added_by_hand(window, dialogs, tmp_path):
	# (the form lists a payment by item as "Item" and a euro price as "Euros")
	window.ui.ab_Item_Id.setText("5449016a4bdc2d6f028b456f")
	window.ui.ab_quantity.setText("1")
	window.ui.ab_cost_edit.setText("5")
	window.ui.ab_euro_button.setChecked(True)
	window.add_item()
	window.ui.ab_Item_Id.setText("590c661e86f7741e566b646a")
	window.ui.ab_quantity.setText("1")
	window.ui.ab_cost_edit.setText("5")
	window.ui.ab_itembarter_check.setChecked(True)
	window.ui.ab_itembarter_edit.setText("barter_tpl")
	window.add_item()
	form_labels = sorted(r[5] for r in rows(window))
	assert form_labels == ["Euros", "Item"]

	data = {
		"items": [root("e", 1), root("b", 1)],
		"barter_scheme": {"e": price(EUROS, 5), "b": price("barter_tpl", 5)},
		"loyal_level_items": {"e": 1, "b": 1},
	}
	import_file(window, dialogs, tmp_path, data)
	assert sorted(r[5] for r in rows(window)) == form_labels


def test_each_row_matches_its_item_whatever_order_the_names_sort_in(window, dialogs, tmp_path):
	# names sort differently from the file order; every row must still hold its own item's data
	items = [root(f"item{n:02d}", n) for n in (7, 3, 9, 1, 5, 8, 2, 6, 4, 0)]
	barter = {i["_id"]: price(ROUBLES, i["upd"]["StackObjectsCount"] * 100) for i in items}
	import_file(window, dialogs, tmp_path, {"items": items, "barter_scheme": barter, "loyal_level_items": {}})
	assert len(rows(window)) == 10
	for item_id, _, qty, cost, *_ in rows(window):
		n = int(item_id[4:])
		assert (qty, cost) == (str(n), str(n * 100)), item_id


# --- removing items ---------------------------------------------------------------------------------


def test_removing_an_imported_item_works_and_takes_its_mods_with_it(window, dialogs, tmp_path):
	import_file(window, dialogs, tmp_path, ASSORT)
	select(window, "gun1")
	window.remove_Item()  # used to raise RecursionError
	assert ids(window) == ["gun2", "grip2"] or ids(window) == sorted(["gun2", "grip2"])
	assert [i["_id"] for i in window.itemlist] == ["gun2", "grip2"]
	assert set(window.barterlist) == {"gun2"} and set(window.loyaltylist) == {"gun2"}


def test_removing_a_mod_takes_the_mods_on_it_but_leaves_the_weapon(window, dialogs, tmp_path):
	import_file(window, dialogs, tmp_path, ASSORT)
	select(window, "stock1")
	window.remove_Item()
	assert ids(window) == sorted(["gun1", "gun2", "grip2"])
	assert sorted(i["_id"] for i in window.itemlist) == sorted(["gun1", "gun2", "grip2"])
	assert "gun1" in window.barterlist  # (the weapon keeps its price)


def test_removing_the_last_mod_on_the_chain(window, dialogs, tmp_path):
	import_file(window, dialogs, tmp_path, ASSORT)
	select(window, "scope1")
	window.remove_Item()
	assert ids(window) == sorted(["gun1", "stock1", "gun2", "grip2"])


def test_removal_still_hits_the_right_rows_after_the_table_is_sorted(window, dialogs, tmp_path):
	import_file(window, dialogs, tmp_path, ASSORT)
	window.ui.ab_table.sortItems(0, Qt.SortOrder.DescendingOrder)
	select(window, "gun2")
	window.remove_Item()
	assert ids(window) == sorted(["gun1", "stock1", "scope1"])


def test_removing_with_nothing_selected_does_nothing(window, dialogs, tmp_path):
	import_file(window, dialogs, tmp_path, ASSORT)
	window.ui.ab_table.setCurrentCell(-1, -1)
	window.remove_Item()
	assert len(rows(window)) == 5 and len(window.itemlist) == 5


def test_an_item_without_a_loyalty_entry_can_still_be_removed(window, dialogs, tmp_path):
	data = {"items": [root("a", 1)], "barter_scheme": {"a": price(ROUBLES, 1)}, "loyal_level_items": {}}
	import_file(window, dialogs, tmp_path, data)
	select(window, "a")
	window.remove_Item()  # used to raise KeyError
	assert rows(window) == [] and window.itemlist == [] and window.barterlist == {}


def test_a_parent_loop_in_the_file_cannot_hang_a_removal(window, dialogs, tmp_path):
	data = {"items": [part("a", "b", "mod_x"), part("b", "a", "mod_x")], "barter_scheme": {}, "loyal_level_items": {}}
	import_file(window, dialogs, tmp_path, data)
	select(window, "a")
	window.remove_Item()
	assert rows(window) == []


def test_removing_an_item_added_by_hand_and_its_part(window):
	window.ui.ab_Item_Id.setText("5449016a4bdc2d6f028b456f")
	window.ui.ab_quantity.setText("1")
	window.ui.ab_cost_edit.setText("5")
	window.add_item()
	weapon_id = window.itemlist[0]["_id"]

	window.ui.ab_tab.setCurrentIndex(1)
	window.ui.ab_weapmongo_edit.setText(weapon_id)
	window.ui.ab_partid_edit.setText("part_tpl")
	window.add_item()
	assert len(window.itemlist) == 2 and len(rows(window)) == 2

	select(window, weapon_id)
	window.remove_Item()
	assert window.itemlist == [] and rows(window) == []
	assert window.barterlist == {} and window.loyaltylist == {}


def test_searching_finds_rows_by_their_own_id(window, dialogs, tmp_path):
	import_file(window, dialogs, tmp_path, ASSORT)
	window.filterTable("grip2")
	table = window.ui.ab_table
	visible = [table.item(r, 1).data(USER_ROLE) for r in range(table.rowCount()) if not table.isRowHidden(r)]
	assert visible == ["grip2"]


def test_searching_finds_items_added_by_hand_by_id_too(window):
	window.ui.ab_Item_Id.setText("5449016a4bdc2d6f028b456f")
	window.ui.ab_quantity.setText("1")
	window.ui.ab_cost_edit.setText("5")
	window.add_item()
	window.ui.ab_Item_Id.setText("590c661e86f7741e566b646a")
	window.ui.ab_quantity.setText("1")
	window.ui.ab_cost_edit.setText("5")
	window.add_item()
	wanted = window.itemlist[1]["_id"]
	window.filterTable(wanted)
	table = window.ui.ab_table
	assert [table.item(r, 1).data(USER_ROLE) for r in range(2) if not table.isRowHidden(r)] == [wanted]


# --- importing again ------------------------------------------------------------------------------------


def test_the_first_import_asks_nothing(window, dialogs, tmp_path):
	import_file(window, dialogs, tmp_path, ASSORT)
	assert dialogs["questions"] == []


def test_importing_again_replaces_the_assort_instead_of_doubling_it(window, dialogs, tmp_path):
	import_file(window, dialogs, tmp_path, ASSORT)
	import_file(window, dialogs, tmp_path, ASSORT)
	assert sorted(i["_id"] for i in window.itemlist) == sorted(i["_id"] for i in ASSORT["items"])
	assert len(rows(window)) == 5
	assert window.barterlist == ASSORT["barter_scheme"] and window.loyaltylist == ASSORT["loyal_level_items"]


def test_it_asks_before_replacing_what_is_there(window, dialogs, tmp_path):
	import_file(window, dialogs, tmp_path, ASSORT)
	import_file(window, dialogs, tmp_path, ASSORT)
	assert len(dialogs["questions"]) == 1 and "5 item" in dialogs["questions"][0]


def test_saying_no_keeps_what_was_there(window, dialogs, tmp_path):
	import_file(window, dialogs, tmp_path, ASSORT)
	dialogs["answer"] = QMessageBox.StandardButton.No
	other = {"items": [root("other", 1)], "barter_scheme": {"other": price(ROUBLES, 1)}, "loyal_level_items": {"other": 1}}
	import_file(window, dialogs, tmp_path, other, name="other.json")
	assert sorted(i["_id"] for i in window.itemlist) == sorted(i["_id"] for i in ASSORT["items"])
	assert "other" not in ids(window) and len(rows(window)) == 5


def test_replacing_drops_the_old_prices_and_loyalty_levels(window, dialogs, tmp_path):
	import_file(window, dialogs, tmp_path, ASSORT)
	other = {"items": [root("other", 1)], "barter_scheme": {"other": price(EUROS, 7)}, "loyal_level_items": {"other": 2}}
	import_file(window, dialogs, tmp_path, other, name="other.json")
	assert ids(window) == ["other"]
	assert window.barterlist == other["barter_scheme"] and window.loyaltylist == other["loyal_level_items"]


def test_items_added_by_hand_are_replaced_too_and_the_table_agrees_with_the_lists(window, dialogs, tmp_path):
	window.ui.ab_Item_Id.setText("5449016a4bdc2d6f028b456f")
	window.ui.ab_quantity.setText("1")
	window.ui.ab_cost_edit.setText("5")
	window.add_item()
	import_file(window, dialogs, tmp_path, ASSORT)
	assert len(dialogs["questions"]) == 1
	assert sorted(r[0] for r in rows(window)) == sorted(i["_id"] for i in window.itemlist)


def test_importing_into_an_empty_assort_does_not_ask(window, dialogs, tmp_path):
	import_file(window, dialogs, tmp_path, {"items": [], "barter_scheme": {}, "loyal_level_items": {}})
	assert dialogs["questions"] == [] and rows(window) == []


# --- bad files ----------------------------------------------------------------------------------------------


def test_a_file_that_is_not_json_shows_an_error_and_changes_nothing(window, dialogs, tmp_path):
	import_file(window, dialogs, tmp_path, ASSORT)
	import_file(window, dialogs, tmp_path, "{ not json", name="bad.json")
	assert len(dialogs["errors"]) == 1 and "bad.json" in dialogs["errors"][0]
	assert len(window.itemlist) == 5 and len(rows(window)) == 5
	assert len(dialogs["questions"]) == 0  # (it didn't ask to replace something it then refused to load)


@pytest.mark.parametrize(
	"content",
	[[1, 2], '"just text"', {"items": "not a list"}, {"items": [], "barter_scheme": []}, {"items": [], "loyal_level_items": 5}],
	ids=["list", "string", "items-not-list", "barter-not-dict", "loyalty-not-dict"],
)
def test_a_file_that_is_not_an_assort_shows_an_error(window, dialogs, tmp_path, content):
	import_file(window, dialogs, tmp_path, content)
	assert len(dialogs["errors"]) == 1 and "assort" in dialogs["errors"][0]
	assert window.itemlist == [] and rows(window) == []


def test_a_missing_file_shows_an_error(window, dialogs, tmp_path):
	dialogs["file"] = tmp_path / "gone.json"
	window.onImportAssort()
	assert len(dialogs["errors"]) == 1


def test_cancelling_the_file_dialog_does_nothing(window, dialogs):
	dialogs["file"] = None
	window.onImportAssort()
	assert dialogs["errors"] == [] and window.itemlist == []


def test_an_empty_assort_file_with_only_items_still_imports(window, dialogs, tmp_path):
	import_file(window, dialogs, tmp_path, {"items": [root("a", 1)]})
	assert ids(window) == ["a"]
