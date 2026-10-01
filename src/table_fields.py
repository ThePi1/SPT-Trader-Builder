"""Keeping a Qt table and AppState.table_fields in step.

Dialogs that collect a list of rows (reward items, kill weapons, ...) add and
remove them through these two functions, so the table the user sees and the data
that ends up in the exported JSON can't drift apart.
"""

import logging

from PySide6.QtWidgets import QTableWidgetItem

log = logging.getLogger(__name__)

# Some "types" are really a group of several; removal checks all of them
_TYPE_GROUPS = {
	"RewardAny": [
		"RewardFail",
		"RewardStarted",
		"RewardSuccess",
		"RewardAssortmentUnlock",
		"RewardSuccess",
	],
	"ConditionAny": ["ConditionFinish", "ConditionStart", "ConditionFail"],
}


def add_table_field(state, type, table, _id, values, dataobj):
	log.debug(
		f"adding type: {type}, table: {table}, id: {_id}, values:  {values}, dataobj: {dataobj}"
	)
	# for single column tables, the only column is the "id"
	# values looks like this: {1: "col1 field", 2: "col2 field", ...}
	if type not in state.table_fields:
		state.table_fields[type] = {}

	# we already have an entry for this, let's remove it first
	if _id in state.table_fields[type]:
		remove_selected_table_item(state, type=type, table=table)

	# add it into the list if it doesn't already exist
	if not _id in state.table_fields[type]:
		# set data
		state.table_fields[type][_id] = dataobj
		# add it into the table
		row = table.rowCount()
		table.insertRow(row)
		log.debug(values)
		for col, text in values.items():
			table.setItem(row, col, QTableWidgetItem(str(text)))
	log.debug(f"Table fields:\n{state.table_fields}")


def remove_selected_table_item(state, type, table, id_row=0):
	log.debug(
		f"removing selected item, type: {type}, table: {table}. Table_fields: {state.table_fields}"
	)
	# if we need to check multiple types (like for rewards), do so
	alltypes = _TYPE_GROUPS.get(type, [type])

	select = table.selectedItems()
	# if no reward selected, just skip
	if len(select) <= 0:
		return
	row = select[0].row()
	row_id = table.item(row, id_row).text()
	for type in alltypes:
		log.debug(
			f"type found?{type in state.table_fields}, row_id in typedict?{type in row_id in state.table_fields and row_id in state.table_fields[type]}"
		)
		if type in state.table_fields and row_id in state.table_fields[type]:
			state.table_fields[type].pop(row_id)
	table.removeRow(row)
	log.debug(f"Table fields:\n{state.table_fields}")
