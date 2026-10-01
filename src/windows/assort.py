import functools
import json
import logging
import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
	QApplication,
	QAbstractItemView,
	QHeaderView,
	QAbstractScrollArea,
	QFileDialog,
	QMainWindow,
	QTableWidgetItem,
)

from builders import assort as assort_builders
from tb_ui.gui_assort import Ui_AssortBuilder
from paths import DATA_DIR, EXPORT_DIR
from utils import new_id

log = logging.getLogger(__name__)

# How a field that needs fixing is marked
ERROR_STYLE = "border: 2px solid red; background-color: #ffe6e6;"


def _is_whole_number(text):
	return re.fullmatch(r"[0-9]+", text.strip()) is not None


@functools.lru_cache(maxsize=None)
def _load_item_names(path):
	"""{item id: display name} from the reference file. Read once per run (keyed by path)."""
	with open(path, "r", encoding="utf-8") as file:
		reference = json.load(file)
	names = {}
	for item in reference.get("items", []):
		# if an id is listed twice, the first entry wins
		names.setdefault(item.get("id", ""), item.get("name", ""))
	return names


class Gui_AssortDlg(QMainWindow):
	def __init__(self, state, parent=None):
		super().__init__(parent)
		self.ui = Ui_AssortBuilder()
		self.ui.setupUi(self)
		self.state = state
		self.on_launch()  # custom Code
		self.show()
		self.ui.ab_add_item.released.connect(self.add_item)
		self.ui.ab_remove_item.released.connect(self.remove_Item)
		self.ui.actionImport_Assort_json.triggered.connect(self.onImportAssort)
		self.ui.actionExport_Assort_json.triggered.connect(self.onExportAssort)
		self.ui.ab_unlimitedcount.toggled.connect(self.unlimitedIsChecked)
		self.ui.ab_buyrestriction_checkbox.toggled.connect(self.brestrictionChecked)
		self.ui.ab_quest_check.toggled.connect(self.questLockedChecked)
		self.ui.ab_weap_ammo_check.toggled.connect(self.ammoCheckIsChecked)
		self.ui.ab_tab.currentChanged.connect(self.tabChange)
		self.ui.ab_table.itemSelectionChanged.connect(self.onWeaponSelected)
		self.ui.ab_table.itemClicked.connect(self.copy_clicked_cell)
		self.ui.ab_search.textChanged.connect(self.filterTable)
		self.ui.ab_itembarter_check.toggled.connect(self.itemBarterChecked)
		self.tabChange(self.ui.ab_tab.currentIndex())
		self.itemlist = []
		self.barterlist = {}
		self.loyaltylist = {}

	def on_launch(self):
		self.setup_box_selections()
		self.ui.ab_rouble_radiobutton.setChecked(True)
		self.ui.ab_quest_check.setChecked(False)
		self.ui.ab_weap_ammo_count.setEnabled(False)
		self.ui.ab_buyRestriction_edit.setEnabled(False)
		self.ui.ab_quest_id.setEnabled(False)
		self.ui.ab_itembarter_edit.setEnabled(False)
		self.ui.ab_tab.setCurrentIndex(0)
		self.questLockedChecked(self.ui.ab_quest_check.isChecked())
		self.brestrictionChecked(self.ui.ab_buyrestriction_checkbox.isChecked())
		table = self.ui.ab_table
		table.setColumnCount(6)
		table.setHorizontalHeaderLabels(
			[
				"ItemTPL",
				"Quantity",
				"Cost",
				"Loyalty Level",
				"Quest Locked?",
				"Currency",
			]
		)
		table.setAlternatingRowColors(True)
		table.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
		header = self.ui.ab_table.horizontalHeader()
		header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
		for col in range(1, 6):
			header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
		self.ui.ab_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

	@staticmethod
	def itemDatabase(tpl):
		names = _load_item_names(DATA_DIR / "ab_itemName_reference.json")
		return names.get(tpl, tpl)

	def verifyComplete(self):
		"""Check the form before adding. Marks every bad field in red; returns True if all are fine."""
		ui = self.ui
		fields = [
			ui.ab_weapmongo_edit,
			ui.ab_quantity,
			ui.ab_cost_edit,
			ui.ab_Item_Id,
			ui.ab_partid_edit,
			ui.ab_buyRestriction_edit,
			ui.ab_weap_ammo_count,
		]
		for field in fields:
			field.setStyleSheet("")

		bad = []
		if ui.ab_tab.currentIndex() == 1:  # weapon part
			if ui.ab_weapmongo_edit.text().strip() == "":
				bad.append(ui.ab_weapmongo_edit)
			if ui.ab_partid_edit.text().strip() == "" and not ui.ab_unlimitedcount.isChecked():
				bad.append(ui.ab_partid_edit)
			if ui.ab_weap_ammo_check.isChecked() and not _is_whole_number(
				ui.ab_weap_ammo_count.text()
			):
				bad.append(ui.ab_weap_ammo_count)
		else:  # a normal item for sale
			# (these are all turned into numbers when the item is added, so they must be whole numbers)
			if not ui.ab_unlimitedcount.isChecked() and not _is_whole_number(ui.ab_quantity.text()):
				bad.append(ui.ab_quantity)
			if not _is_whole_number(ui.ab_cost_edit.text()):
				bad.append(ui.ab_cost_edit)
			if ui.ab_Item_Id.text().strip() == "":
				bad.append(ui.ab_Item_Id)
			if ui.ab_buyrestriction_checkbox.isChecked() and not _is_whole_number(
				ui.ab_buyRestriction_edit.text()
			):
				bad.append(ui.ab_buyRestriction_edit)

		for field in bad:
			field.setStyleSheet(ERROR_STYLE)
		return not bad

	def copy_clicked_cell(self, item):

		# if self.ui.ab_weappart_check.isChecked():
		# return
		text = item.text()
		QApplication.clipboard().setText(text)

	def setup_box_selections(self):
		self.ui.ab_loyalty_combo.addItems(self.state.config.ab_box_loyalty_level)
		self.ui.ab_condition_box.addItems(self.state.config.ab_box_condition_req)
		self.ui.ab_modslot_combo.addItems(self.state.config.ab_box_modslot)

	def onImportAssort(
		self,
	):  # AI WRITTEN function purely for ease. I will be coming back to this.
		table = self.ui.ab_table
		filename, _ = QFileDialog.getOpenFileName(
			self, "Import Assort JSON", "", "JSON Files (*.json);;All Files (*)"
		)
		if not filename:
			return

		with open(filename, "r", encoding="utf-8") as f:
			assort = json.load(f)

		items = assort.get("items", [])
		for item in assort.get("items", []):
			self.itemlist.append(item)

		barter_scheme = assort.get("barter_scheme", {})
		self.barterlist.update(assort.get("barter_scheme", {}))

		loyal_levels = assort.get("loyal_level_items", {})
		self.loyaltylist.update(assort.get("loyal_level_items", {}))

		table = self.ui.ab_table
		table.clear()
		table.setColumnCount(6)
		table.setHorizontalHeaderLabels(
			["Name", "Quantity", "Cost", "Loyalty Level", "Quest Locked?", "Currency"]
		)
		table.setRowCount(0)
		table.setAlternatingRowColors(True)
		table.setSortingEnabled(True)
		table.horizontalHeader().setSortIndicatorShown(True)

		for item in items:
			item_id = item.get("_id", "")
			tpl = item.get("_tpl", "")

			upd = item.get("upd", {}) or {}
			unlimited = bool(upd.get("UnlimitedCount", False))
			stack = upd.get("StackObjectsCount", 1)

			# Quantity
			qty_display = "∞" if unlimited else str(stack)

			# Loyalty level
			loyalty = loyal_levels.get(item_id, "")
			loyalty_display = "" if loyalty == "" else str(loyalty)

			# Quest locked?
			quest_id = item.get("questID", "")
			unlocked_on = item.get("unlockedOn", "")
			# show questID if present, otherwise blank
			quest_display = quest_id if quest_id else ""

			# Cost + currency (your file uses barter_scheme[item_id] -> [[{_tpl, count}, ...]])
			cost_display = ""
			currency_display = ""
			scheme = barter_scheme.get(item_id)

			if scheme and isinstance(scheme, list) and len(scheme) > 0:
				# first "OR" group
				group0 = scheme[0]
				if isinstance(group0, list) and len(group0) > 0:
					payment0 = group0[0]
					if isinstance(payment0, dict):
						cost_display = str(payment0.get("count", ""))
						currency_display = str(payment0.get("_tpl", ""))

						currency_display = assort_builders.currency_name(currency_display)

			# Insert row
			row = table.rowCount()
			table.insertRow(row)

			tpl = item.get("_tpl", "")
			slot = item.get("slotId", "")
			parent = item.get("parentId", "")

			display_name = self.itemDatabase(tpl)
			if (
				isinstance(slot, str)
				and slot.startswith("mod_")
				and parent != "hideout"
			):
				display_name = f"{parent}+{slot}"

			name_item = QTableWidgetItem(display_name)
			name_item.setData(Qt.ItemDataRole.UserRole, item.get("_id", ""))

			table.setItem(row, 0, name_item)
			table.setItem(row, 1, QTableWidgetItem(qty_display))
			table.item(row, 1).setData(Qt.ItemDataRole.UserRole, item.get("_id", ""))
			table.setItem(row, 2, QTableWidgetItem(cost_display))
			table.setItem(row, 3, QTableWidgetItem(loyalty_display))
			table.setItem(row, 4, QTableWidgetItem(quest_display))
			table.setItem(row, 5, QTableWidgetItem(currency_display))

	def onWeaponSelected(
		self,
	):  # gets the user role from the table and fills the assortID line edit.
		row = self.ui.ab_table.currentRow()

		if row < 0:
			return

		self.itemClicked = self.ui.ab_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
		self.parentid = self.ui.ab_table.item(row, 1).data(Qt.ItemDataRole.UserRole)
		log.info("* " + str(self.ui.ab_table.item(row, 0).data(Qt.ItemDataRole.UserRole)))
		self.ui.ab_weapmongo_edit.setText(self.parentid)

	def filterTable(self, query: str):
		table = self.ui.ab_table
		q = query.strip().lower()
		for row in range(table.rowCount()):
			item = table.item(row, 0)  # display name col
			text = item.text().lower() if item else ""
			mongo = item.data(Qt.ItemDataRole.UserRole)
			mongo = str(mongo).lower() if mongo else ""
			match = (q in text) or (
				q in mongo
			)  # contains search; use == for exact match
			table.setRowHidden(row, not match)

	def unlimitedIsChecked(self, checked):  # UI behavior
		if checked:
			self.ui.ab_quantity.clear()
			self.ui.ab_quantity.setEnabled(False)
			self.ui.ab_quantity.setStyleSheet("")
		else:
			self.ui.ab_quantity.setEnabled(True)

	def ammoCheckIsChecked(self, checked):
		if checked:
			self.ui.ab_weap_ammo_count.setEnabled(True)
		else:
			self.ui.ab_weap_ammo_count.setEnabled(False)
			self.ui.ab_weap_ammo_count.clear()

	def brestrictionChecked(self, checked):  # UI behavior
		if checked:
			self.ui.ab_buyRestriction_edit.setEnabled(True)
		else:
			self.ui.ab_buyRestriction_edit.setEnabled(False)
			self.ui.ab_buyRestriction_edit.clear()

	def itemBarterChecked(self, checked):
		if checked:
			self.ui.ab_itembarter_edit.setEnabled(True)
		else:
			self.ui.ab_itembarter_edit.setEnabled(False)
			self.ui.ab_itembarter_edit.clear()

	def questLockedChecked(self, checked):  # UI behavior
		if (
			not self.ui.ab_tab.currentIndex() == 1
		):  # Checks to see if weaponpart is not checked and skips ui behavior if it is
			if checked:
				self.ui.ab_quest_id.setEnabled(True)
				self.ui.ab_condition_box.setEnabled(True)
			else:
				self.ui.ab_quest_id.setEnabled(False)
				self.ui.ab_condition_box.setEnabled(False)
				self.ui.ab_quest_id.clear()

	def clearUI(self):
		self.ui.ab_Item_Id.clear()
		self.ui.ab_cost_edit.clear()
		self.ui.ab_quest_id.clear()
		self.ui.ab_weapmongo_edit.clear()
		self.ui.ab_partid_edit.clear()
		self.ui.ab_quantity.clear()
		self.ui.ab_Item_Id.clear()
		self.ui.ab_cost_edit.clear()
		self.ui.ab_quest_id.clear()
		self.ui.ab_buyRestriction_edit.clear()
		self.ui.ab_itembarter_edit.clear()
		self.ui.ab_weap_ammo_count.clear()

	def tabChange(self, index):  # UI behavior
		if index == 1:
			self.clearUI()
			self.ui.ab_quest_check.setChecked(False)
			self.ui.ab_weapmongo_edit.setEnabled(False)

		else:
			self.clearUI()
			self.ui.ab_weap_ammo_check.setChecked(False)
			self.questLockedChecked(self.ui.ab_quest_check.isChecked())
			self.itemBarterChecked(self.ui.ab_itembarter_check.isChecked())

	def remove_children(self, mongosaved):
		children = [
			item for item in self.itemlist if item.get("parentId") == mongosaved
		]
		self.itemlist = [
			item for item in self.itemlist if item.get("_id") != mongosaved
		]
		for child in children:
			self.remove_children(child.get("_id"))

	def removeTableChildren(self, parent_id):
		rows_to_remove = []
		for row in range(self.ui.ab_table.rowCount()):
			item = self.ui.ab_table.item(row, 0)
			if item and item.data(Qt.ItemDataRole.UserRole) == parent_id:
				rows_to_remove.append(row)

		for row in reversed(rows_to_remove):
			child_id = self.ui.ab_table.item(row, 1).data(Qt.ItemDataRole.UserRole)
			self.removeTableChildren(child_id)  # recurse before removing
			self.ui.ab_table.removeRow(row)

	def remove_Item(
		self,
	):  # remove selected item from lists/dicts and remove from table.
		row = self.ui.ab_table.currentRow()
		if row < 0:
			return

		mongosaved = self.ui.ab_table.item(row, 1).data(Qt.ItemDataRole.UserRole)
		self.remove_children(mongosaved)
		if (
			mongosaved in self.barterlist
		):  # checks if weapon part and skips barterlist and loyaltylist
			self.barterlist.pop(mongosaved)
			self.loyaltylist.pop(mongosaved)

		self.removeTableChildren(mongosaved)
		self.ui.ab_table.removeRow(row)

	def add_item(self):  # The basic assort add function

		table = self.ui.ab_table
		table.setSortingEnabled(False)

		if not self.verifyComplete():
			return

		# Item variables
		mongosaved = new_id()
		itemID = self.ui.ab_Item_Id.text().strip()
		unlimited = True if self.ui.ab_unlimitedcount.isChecked() else False
		quantity = str(self.ui.ab_quantity.text())
		if self.ui.ab_tab.currentIndex() == 1:
			quantity = "N/A"
		barteritem = str(self.ui.ab_itembarter_edit.text())

		loyaltylevel = str(self.ui.ab_loyalty_combo.currentText())
		if self.ui.ab_tab.currentIndex() == 1:
			loyaltylevel = "N/A"

		cost = self.ui.ab_cost_edit.text().strip()
		if self.ui.ab_tab.currentIndex() == 1:
			cost = "N/A"

		if self.ui.ab_quest_check.isChecked():
			questLockedChecked = "Yes"
		elif self.ui.ab_tab.currentIndex() == 1:
			questLockedChecked = "N/A"
		else:
			questLockedChecked = "No"

		questID = self.ui.ab_quest_id.text().strip()
		buyrestriction = self.ui.ab_buyRestriction_edit.text()
		ammoCount = str(self.ui.ab_weap_ammo_count.text())

		item_Id = QTableWidgetItem()

		# Weapon Part Variables
		slotID = str(self.ui.ab_modslot_combo.currentText())
		parentID = self.ui.ab_weapmongo_edit.text().strip()
		partID = self.ui.ab_partid_edit.text().strip()

		# checks whether its a weapon part. if it is creates a name for table that mixes the original weapon its built off of and the slot name
		# if self.ui.ab_weappart_check.isChecked() and self.ui.ab_table.item(self.ui.ab_table.currentRow(),0).data(Qt.ItemDataRole.UserRole) == self.ui.ab_weapmongo_edit.text():
		# itemID = self.ui.ab_table.item(self.ui.ab_table.currentRow(),0).text() + " + " + self.ui.ab_modslot_combo.currentText()

		cashtype = "Undefined"  # set cashtype then check type and apply
		if self.ui.ab_tab.currentIndex() == 1:
			cashtype = "N/A"
		elif self.ui.ab_rouble_radiobutton.isChecked():
			cashtype = "Roubles"
		elif self.ui.ab_usd_button.isChecked():
			cashtype = "USD"
		elif self.ui.ab_itembarter_check.isChecked():
			cashtype = "Item"
		else:
			cashtype = "Euros"

		# selects item key structure depending on item or weapon part.
		# Everything is built first and only then added to the lists, so an error while
		# building can't leave a half-added item behind.
		if self.ui.ab_tab.currentIndex() == 1:
			item = assort_builders.weapon_part_item(
				mongosaved,
				partID,
				parentID,
				slotID,
				ammo_count=int(ammoCount) if self.ui.ab_weap_ammo_check.isChecked() else None,
			)
			barter = {}
			loyalty = {}
		else:
			item = assort_builders.assort_item(
				mongosaved,
				itemID,
				unlimited=unlimited,
				quantity=quantity,
				buy_restriction=(
					buyrestriction if self.ui.ab_buyrestriction_checkbox.isChecked() else None
				),
				quest_id=questID if self.ui.ab_quest_check.isChecked() else None,
			)
			barter = assort_builders.barter_scheme(
				mongosaved,
				cost,
				currency=cashtype,
				barter_item_tpl=str(barteritem) if cashtype == "Item" else None,
			)
			loyalty = {mongosaved: int(loyaltylevel)}

		self.itemlist.append(item)
		self.barterlist.update(barter)
		self.loyaltylist.update(loyalty)

		row = table.rowCount()
		table.insertRow(row)

		if not self.ui.ab_tab.currentIndex() == 1:  # if root item give it no Parent
			item_Id.setData(Qt.ItemDataRole.UserRole, None)
			display_name = self.itemDatabase(itemID)
		else:
			item_Id.setData(
				Qt.ItemDataRole.UserRole, parentID
			)  # if its not give it clicked user role
			display_name = self.itemDatabase(partID)

		# print(f"After setText: {item_Id.text()}\n")
		item_Id.setData(Qt.ItemDataRole.EditRole, mongosaved)
		item_Id.setText(display_name)
		# print(f"itemID: {itemID}, partID: {partID}, display_name: {display_name}")

		tablequantity = "∞" if self.ui.ab_unlimitedcount.isChecked() else quantity

		table.setItem(row, 0, item_Id)
		table.setItem(row, 1, QTableWidgetItem(str(tablequantity)))
		table.item(row, 1).setData(Qt.ItemDataRole.UserRole, mongosaved)
		table.setItem(row, 2, QTableWidgetItem(str(cost)))
		table.setItem(row, 3, QTableWidgetItem(loyaltylevel))
		table.setItem(row, 4, QTableWidgetItem(questLockedChecked))
		table.setItem(row, 5, QTableWidgetItem(cashtype))

		self.ui.ab_weapmongo_edit.setStyleSheet("")

		self.clearUI()

	def onExportAssort(self):  # export the finalized assort
		assort = {
			"items": self.itemlist,
			"barter_scheme": self.barterlist,
			"loyal_level_items": self.loyaltylist,
		}

		EXPORT_DIR.mkdir(exist_ok=True)
		with open(EXPORT_DIR / "assort.json", "w") as f:
			json.dump(assort, f, indent=2)
