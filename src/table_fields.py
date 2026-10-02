"""Keeping a Qt table and the dialog's TableFields in step.

Dialogs that collect a list of rows (reward items, kill weapons, ...) add and
remove them through these two functions, so the table the user sees and the data
that ends up in the exported JSON can't drift apart.
"""

import logging

from PySide6.QtWidgets import QTableWidgetItem

log = logging.getLogger(__name__)

# Some "types" are really a group of several; removal checks all of them
_TYPE_GROUPS = {
	"RewardAny": ["RewardFail", "RewardStarted", "RewardSuccess"],
	"ConditionAny": ["ConditionFinish", "ConditionStart", "ConditionFail"],
}


def find_row(table, _id, id_col=0):
	"""The row whose id column shows _id, or None."""
	for row in range(table.rowCount()):
		item = table.item(row, id_col)
		if item is not None and item.text() == str(_id):
			return row
	return None


def add_table_field(fields, type, table, _id, values, dataobj):
	"""Add a row to the table and store its data. Adding an id that is already there updates that row.

	Column 0 of the table is the id. values looks like {0: "id", 1: "col1 field", ...}.
	"""
	log.debug(
		f"adding type: {type}, table: {table}, id: {_id}, values:  {values}, dataobj: {dataobj}"
	)
	fields.data.setdefault(type, {})[_id] = dataobj  # (a repeated id replaces the old data)

	# update the existing row for this id in place, or add a new one
	row = find_row(table, _id)
	if row is None:
		row = table.rowCount()
		table.insertRow(row)
	for col, text in values.items():
		table.setItem(row, col, QTableWidgetItem(str(text)))
	log.debug(f"Table fields:\n{fields.data}")


def remove_selected_table_item(fields, type, table, id_row=0):
	log.debug(
		f"removing selected item, type: {type}, table: {table}. Table fields: {fields.data}"
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
		if type in fields.data and row_id in fields.data[type]:
			fields.data[type].pop(row_id)
	table.removeRow(row)
	log.debug(f"Table fields:\n{fields.data}")
