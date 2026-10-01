"""AppState's game data, the per-dialog TableFields store, and the Qt helpers that keep a table in step with it."""

import pytest
from PySide6.QtWidgets import QTableWidget

from config import load_config
from state import AppState, TableFields
from table_fields import add_table_field, remove_selected_table_item


@pytest.fixture(scope="module")
def state():
	return AppState.load(load_config())


@pytest.fixture
def fields():
	return TableFields()


@pytest.fixture
def table(qapp):
	table = QTableWidget(0, 2)
	return table


def test_game_data_is_loaded(state):
	assert state.traders and state.items and state.locations and state.weapons


def test_app_state_no_longer_holds_table_rows(state):
	# rows belong to the dialog that collects them, not to the app
	assert not hasattr(state, "table_fields")


def test_field_lists(fields):
	fields.data["Things"] = {"a": {"x": 1}, "b": {"x": 2}}
	assert fields.get_singlecolumn_field_list("Things") == ["a", "b"]
	assert fields.get_multicolumn_values_list("Things") == [{"x": 1}, {"x": 2}]
	assert fields.get_singlecolumn_field_list("Missing") == []
	assert fields.get_multicolumn_values_list("Missing") == []


def test_each_store_is_independent():
	one, two = TableFields(), TableFields()
	one.data["Things"] = {"a": 1}
	assert two.get_singlecolumn_field_list("Things") == []


def test_add_table_field_adds_a_row_and_stores_the_data(fields, table):
	add_table_field(fields, "Things", table, "id1", {0: "id1", 1: "second"}, {"d": 1})
	assert table.rowCount() == 1
	assert table.item(0, 0).text() == "id1" and table.item(0, 1).text() == "second"
	assert fields.data == {"Things": {"id1": {"d": 1}}}


def test_adding_the_same_id_again_replaces_the_row_only_if_selected(fields, table):
	add_table_field(fields, "Things", table, "id1", {0: "id1"}, "old")
	table.selectRow(0)
	add_table_field(fields, "Things", table, "id1", {0: "id1"}, "new")
	assert table.rowCount() == 1
	assert fields.data["Things"] == {"id1": "new"}


def test_remove_selected_table_item(fields, table):
	add_table_field(fields, "Things", table, "a", {0: "a"}, 1)
	add_table_field(fields, "Things", table, "b", {0: "b"}, 2)
	table.selectRow(0)
	remove_selected_table_item(fields, "Things", table)
	assert table.rowCount() == 1 and table.item(0, 0).text() == "b"
	assert fields.data["Things"] == {"b": 2}


def test_remove_with_nothing_selected_does_nothing(fields, table):
	add_table_field(fields, "Things", table, "a", {0: "a"}, 1)
	table.clearSelection()
	remove_selected_table_item(fields, "Things", table)
	assert table.rowCount() == 1 and fields.data["Things"] == {"a": 1}


def test_reward_any_removes_from_whichever_timing_holds_it(fields, table):
	add_table_field(fields, "RewardStarted", table, "r1", {0: "r1"}, {"id": "r1"})
	table.selectRow(0)
	remove_selected_table_item(fields, "RewardAny", table)
	assert table.rowCount() == 0
	assert fields.data["RewardStarted"] == {}
