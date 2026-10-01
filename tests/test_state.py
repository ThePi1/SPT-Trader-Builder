"""AppState's table-field store, and the Qt helpers that keep a table in step with it."""

import pytest
from PySide6.QtWidgets import QTableWidget

from config import load_config
from state import AppState
from table_fields import add_table_field, remove_selected_table_item


@pytest.fixture(scope="module")
def state():
	return AppState.load(load_config())


@pytest.fixture
def fresh(state):
	state.clear_table_fields()
	yield state
	state.clear_table_fields()


@pytest.fixture
def table(qapp):
	table = QTableWidget(0, 2)
	return table


def test_game_data_is_loaded(state):
	assert state.traders and state.items and state.locations and state.weapons


def test_field_lists(fresh):
	fresh.table_fields["Things"] = {"a": {"x": 1}, "b": {"x": 2}}
	assert fresh.get_singlecolumn_field_list("Things") == ["a", "b"]
	assert fresh.get_multicolumn_values_list("Things") == [{"x": 1}, {"x": 2}]
	assert fresh.get_singlecolumn_field_list("Missing") == []
	assert fresh.get_multicolumn_values_list("Missing") == []


def test_safe_clear_keeps_rewards_and_conditions_only(fresh):
	fresh.table_fields.update(
		{"RewardSuccess": {"r": 1}, "ConditionFinish": {"c": 1}, "KillsWep": {"w": 1}}
	)
	fresh.safe_clear_table_fields()
	assert set(fresh.table_fields) == {"RewardSuccess", "ConditionFinish"}
	fresh.clear_table_fields()
	assert fresh.table_fields == {}


def test_reset_by_key_and_id(fresh):
	fresh.table_fields.update({"A": {"1": "x", "2": "y"}, "B": {"1": "z"}})
	fresh.reset_by_id("1")
	assert fresh.table_fields == {"A": {"2": "y"}, "B": {}}
	fresh.reset_by_key("A")
	assert "A" not in fresh.table_fields


def test_add_table_field_adds_a_row_and_stores_the_data(fresh, table):
	add_table_field(fresh, "Things", table, "id1", {0: "id1", 1: "second"}, {"d": 1})
	assert table.rowCount() == 1
	assert table.item(0, 0).text() == "id1" and table.item(0, 1).text() == "second"
	assert fresh.table_fields == {"Things": {"id1": {"d": 1}}}


def test_adding_the_same_id_again_replaces_the_row_only_if_selected(fresh, table):
	add_table_field(fresh, "Things", table, "id1", {0: "id1"}, "old")
	table.selectRow(0)
	add_table_field(fresh, "Things", table, "id1", {0: "id1"}, "new")
	assert table.rowCount() == 1
	assert fresh.table_fields["Things"] == {"id1": "new"}


def test_remove_selected_table_item(fresh, table):
	add_table_field(fresh, "Things", table, "a", {0: "a"}, 1)
	add_table_field(fresh, "Things", table, "b", {0: "b"}, 2)
	table.selectRow(0)
	remove_selected_table_item(fresh, "Things", table)
	assert table.rowCount() == 1 and table.item(0, 0).text() == "b"
	assert fresh.table_fields["Things"] == {"b": 2}


def test_remove_with_nothing_selected_does_nothing(fresh, table):
	add_table_field(fresh, "Things", table, "a", {0: "a"}, 1)
	table.clearSelection()
	remove_selected_table_item(fresh, "Things", table)
	assert table.rowCount() == 1 and fresh.table_fields["Things"] == {"a": 1}


def test_reward_any_removes_from_whichever_timing_holds_it(fresh, table):
	add_table_field(fresh, "RewardStarted", table, "r1", {0: "r1"}, {"id": "r1"})
	table.selectRow(0)
	remove_selected_table_item(fresh, "RewardAny", table)
	assert table.rowCount() == 0
	assert fresh.table_fields["RewardStarted"] == {}
