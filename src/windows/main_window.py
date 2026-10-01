import sys
import re
import json
import traceback
import logging

from PySide6 import QtCore
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtWidgets import (
	QApplication,
	QAbstractItemView,
	QFileDialog,
	QMainWindow,
	QListWidgetItem,
	QTableWidgetItem,
)

from builders import assort as assort_builders
from builders import locale as locale_builders
from config import UPDATE_SETTING_NAMES
from tb_ui.gui_main import Ui_MainGUI
from updates import OUTDATED, UNKNOWN, UpdateCheckWorker, pending_status
from utils import new_id
from windows.about import Gui_AboutDlg
from windows.assort import Gui_AssortDlg
from windows.common import safe_file_dialog
from windows.data_editor import Gui_DataEditor
from windows.quest import Gui_QuestDlg
from windows.settings import Gui_SettingsDlg
from windows.update_dialog import Gui_UpdatesDlg

log = logging.getLogger(__name__)


class Gui_MainWindow(QMainWindow):
	def __init__(self, state, parent=None):
		super().__init__(parent)
		self.ui = Ui_MainGUI()
		self.ui.setupUi(self)
		self.on_launch()
		self.setupTreeView()
		self.state = state
		self.update_status = pending_status(state.config)
		self._update_workers = []
		self.setup_box_selections()
		self.connect_actions()
		self.setup_vars()

	def setup_vars(self):
		self.weaponlist = []
		self.windows = []
		self.itemsJSON = None
		self.weapon_preset_filename = None

	def connect_actions(self):
		self.ui.actionExit.triggered.connect(self.onExit)
		self.ui.actionSettingsMenu.triggered.connect(self.onSettings)
		self.ui.actionExport_Queued_Quests.triggered.connect(self.onExportQuests)
		self.ui.actionLoad_items_json_for_below.triggered.connect(self.loadItemsJSON)
		self.ui.actionGet_all_children_of_parent_ID.triggered.connect(
			self.getAllChildrenCalc
		)
		self.ui.actionCreate_locale_from_Quest_JSON.triggered.connect(
			self.createLocaleFromJSON
		)
		self.ui.actionImport_Quests.triggered.connect(self.importQuests)
		self.ui.wb_addpart_button.released.connect(self.addpart)
		self.ui.questList.itemClicked.connect(self.copy_clicked_cell)
		self.ui.questsearch.textChanged.connect(self.filterList)
		self.ui.wb_base_check.toggled.connect(self.baseWeaponChecked)
		self.ui.actionAnalyze_CC_subtypes.triggered.connect(self.analyze_cc)
		self.ui.actionRemove_Selected_Quest.triggered.connect(
			self.remove_selected_quest
		)
		self.ui.fld_idlookup.textChanged.connect(self.update_idlookup)
		# self.ui.wb_treeview.itemSelectionChanged.connect(self.onWeaponSelected)

	def update_idlookup(self):
		self.ui.id_table.setRowCount(0)
		search_str = self.ui.fld_idlookup.displayText()
		try:
			search_re = re.compile(search_str, re.IGNORECASE)
		except Exception as e:
			search_re = re.compile("")
		keys_to_search = list(self.state.id_search.keys())
		local_quest_ids = {}

		# add newly created quests
		for _id, _data in self.state.quests.items():
			keys_to_search.append(_data["QuestName"])
			local_quest_ids[_data["QuestName"]] = _id

		# add item keys
		for _id, _data in self.state.items.items():
			keys_to_search.append(_data["_name"])

		# add locations
		for _location, _id in self.state.locations.items():
			keys_to_search.append(_location)

		# add traders
		for _trader, _id in self.state.traders.items():
			keys_to_search.append(_trader)

		# do the filtered search and inserts
		filtered_keys = [item for item in keys_to_search if re.search(search_re, item)]
		for key in filtered_keys:
			row_position = self.ui.id_table.rowCount()
			self.ui.id_table.insertRow(row_position)
			if key in self.state.id_search:
				self.ui.id_table.setItem(
					row_position, 0, Gui_MainWindow.table_widget(self.state.id_search[key])
				)
				self.ui.id_table.setItem(
					row_position, 2, Gui_MainWindow.table_widget("wtt_custom")
				)
			elif key in local_quest_ids:
				self.ui.id_table.setItem(
					row_position, 0, Gui_MainWindow.table_widget(local_quest_ids[key])
				)
				self.ui.id_table.setItem(
					row_position, 2, Gui_MainWindow.table_widget("new_quest")
				)
			elif key in self.state.item_id_name:
				self.ui.id_table.setItem(
					row_position, 0, Gui_MainWindow.table_widget(self.state.item_id_name[key])
				)
				self.ui.id_table.setItem(
					row_position, 2, Gui_MainWindow.table_widget("eft_item")
				)
			elif key in self.state.locations.keys():
				self.ui.id_table.setItem(
					row_position, 0, Gui_MainWindow.table_widget(self.state.locations[key])
				)
				self.ui.id_table.setItem(
					row_position, 2, Gui_MainWindow.table_widget("location")
				)
			elif key in self.state.traders.keys():
				self.ui.id_table.setItem(
					row_position, 0, Gui_MainWindow.table_widget(self.state.traders[key])
				)
				self.ui.id_table.setItem(
					row_position, 2, Gui_MainWindow.table_widget("trader")
				)

			self.ui.id_table.setItem(
				row_position, 1, Gui_MainWindow.table_widget(key, hover=True)
			)

	@staticmethod
	def table_widget(text, hover=False):
		item = QTableWidgetItem(text)
		if hover:
			item.setToolTip(text)
		return item

	def spawnWindow(self, window_type):
		match window_type:
			case "QuestBuilder":
				dlg = Gui_QuestDlg(self.state, parent=self)
				dlg.quest_saved.connect(self.on_quest_saved)
			case "DataWindow":
				dlg = Gui_DataEditor(self.state, parent=self)
			case "AboutWindow":
				dlg = Gui_AboutDlg(parent=self)
			case "UpdateWindow":
				dlg = Gui_UpdatesDlg(parent=self)
			case "AssortBuilder":
				dlg = Gui_AssortDlg(self.state, parent=self)
			case "SettingsWindow":
				dlg = Gui_SettingsDlg(self.state.config, parent=self)

		self.windows.append(dlg)
		return dlg

	def on_quest_saved(self, quest_id, quest_name, quest):
		self.state.quests[quest_id] = quest
		item = QListWidgetItem(f"{quest_name}, {quest_id}")
		item.setData(Qt.ItemDataRole.UserRole, quest_id)
		self.ui.questList.addItem(item)

	def on_launch(self):
		self.ui.main_tab.setCurrentIndex(0)
		self.ui.wb_base_check.setChecked(True)
		self.baseWeaponChecked(self.ui.wb_base_check.isChecked())

	def setup_box_selections(self):
		self.ui.wb_modslot_combo.addItems(self.state.config.ab_box_modslot)

	def filterList(self, query: str):
		lst = self.ui.questList
		q = query.strip().lower()
		for row in range(lst.count()):
			item = lst.item(row)  # display name col
			text = item.text().lower() if item else ""
			quest_id = item.data(Qt.ItemDataRole.UserRole)
			quest_id = str(quest_id).lower() if quest_id else ""
			match = (q in text) or (
				q in quest_id
			)  # contains search; use == for exact match
			item.setHidden(not match)

	def baseWeaponChecked(self, checked):  # UI Behavior
		if checked:
			self.ui.wb_parentId_edit.setEnabled(False)
			self.ui.wb_parentid.setStyleSheet("color: gray;")
			self.ui.wb_modslot_combo.setEnabled(False)
			self.ui.wb_modslot.setStyleSheet("color: gray;")
			self.ui.wb_weaponname_edit.setEnabled(True)
			self.ui.wb_weaponname.setStyleSheet("")
		else:
			self.ui.wb_parentId_edit.setEnabled(True)
			self.ui.wb_parentid.setStyleSheet("")
			self.ui.wb_modslot_combo.setEnabled(True)
			self.ui.wb_modslot.setStyleSheet("")
			self.ui.wb_weaponname_edit.setEnabled(False)
			self.ui.wb_weaponname.setStyleSheet("color: gray;")

	def setupTreeView(self):
		self.model = QStandardItemModel()
		self.model.setHorizontalHeaderLabels(
			["Name", "ItemID", "DatabaseID", "ParentID"]
		)
		self.ui.wb_treeview.setModel(self.model)
		self.ui.wb_treeview.setEditTriggers(
			QAbstractItemView.EditTrigger.NoEditTriggers
		)

	def addpart(self):  # add part to treeview and weaponlist
		savedmongo = new_id()
		item_name = QStandardItem(self.ui.wb_weaponname_edit.text())
		parent_ID = QStandardItem(self.ui.wb_itemid_edit.text())

		child_name = QStandardItem(str(self.ui.wb_modslot_combo.currentText()))
		child_ID = QStandardItem(self.ui.wb_itemid_edit.text())
		# print("Button Started")

		slotID = (
			self.ui.wb_modslot_combo.currentText()
			if not self.ui.wb_base_check.isChecked()
			else ""
		)
		if (
			self.ui.wb_base_check.isChecked()
		):  # check if the base weapon box is checked.
			database_ID = QStandardItem(savedmongo)
			item_name.setData(savedmongo, Qt.ItemDataRole.UserRole)
			self.model.appendRow([item_name, parent_ID, database_ID, QStandardItem("")])
			self.addPartToLists(parent_ID.text(), database_ID.text(), "", slotID)
			# print("checkbox is checked")
			return

		tree_index = self.ui.wb_treeview.currentIndex()
		if not tree_index.isValid():  # checks if new index is valid
			log.info("Tree index is not valid")
			return

		clicked_item = self.model.itemFromIndex(tree_index)  # gets data from tree_index
		parent_item = (
			clicked_item.parent()
		)  # checks what is the parent and returns none if has no parent
		if (
			parent_item is None
		):  # if item has no parent then set the parent back to index 0 basically catches if the user selected the value collumn and the key then sets it to the key collumn
			clicked_item = self.model.item(clicked_item.row(), 0)
		else:  # same as above but if user clicks the childs value not the key
			clicked_item = parent_item.child(clicked_item.row(), 0)
		parent_data = clicked_item.data(Qt.ItemDataRole.UserRole)

		if parent_data is None:
			log.info("No Parent Data")

		child_savedmongo = new_id()
		child_name.setData(child_savedmongo, Qt.ItemDataRole.UserRole)
		# print("Append Child")
		# add item to treeview
		clicked_item.appendRow(
			[
				child_name,
				child_ID,
				QStandardItem(child_savedmongo),
				QStandardItem(str(parent_data)),
			]
		)
		self.addPartToLists(child_ID.text(), child_savedmongo, parent_data, slotID)
		# expands tree of newly added items parent
		self.ui.wb_treeview.expand(tree_index)
		# print("Button Completed")

	def addPartToLists(self, ItemID, databaseID, parentID, slotID):
		# print("Item ID: " + ItemID)
		# print("Database ID: " + databaseID)
		# print("Parent ID: " + parentID)

		item = assort_builders.weapon_preset_part(
			databaseID,
			ItemID,
			parentID,
			slotID,
			is_base=self.ui.wb_base_check.isChecked(),
		)
		finalized_item = {databaseID: item}
		self.weaponlist.append(finalized_item)
		self.exportWeaponPresets(self.weaponlist)

	def exportWeaponPresets(self, weaponlist):
		if self.weapon_preset_filename is None:
			self.weapon_preset_filename, ok = safe_file_dialog(
				QFileDialog.getSaveFileName, "Export Weapon Preset"
			)
			if self.weapon_preset_filename is None or not ok:
				log.info("No file selected for weapon presets, skipping export.")
				return
		with open(self.weapon_preset_filename, "w") as f:
			json.dump(weaponlist, f, indent=2)

	def copy_clicked_cell(self, item):
		# if self.ui.ab_weappart_check.isChecked():
		# return
		text = item.data(Qt.ItemDataRole.UserRole)
		QApplication.clipboard().setText(text)

	def analyze_cc(self):
		log.info(f"Analyzing CC subtypes, opening dialogue...")

		filename, ok = safe_file_dialog(
			QFileDialog.getOpenFileName, "Import Quest JSON"
		)
		if not ok or filename is None:
			log.info("No file selected, aborting CC analysis.")
			return

		log.info(filename)
		cc_keeptrack = {}
		non_cc_keeptrack = {}
		with open(filename, "r", encoding="utf-8") as f:
			try:
				quests_import = json.load(f)
			except Exception as e:
				log.error(f"Error loading quest file: {e}")
			for quest_id in quests_import.keys():
				# print(f"Found quest {quests_import[quest_id]['QuestName']} ({quest_id})")
				log.info(f"{quests_import[quest_id]['QuestName']}")
				if (
					"conditions" in quests_import[quest_id]
					and "AvailableForFinish" in quests_import[quest_id]["conditions"]
					and len(quests_import[quest_id]["conditions"]["AvailableForFinish"])
					> 0
				):
					for avf_c in quests_import[quest_id]["conditions"][
						"AvailableForFinish"
					]:
						if avf_c["conditionType"] not in non_cc_keeptrack:
							non_cc_keeptrack[avf_c["conditionType"]] = 1
						else:
							non_cc_keeptrack[avf_c["conditionType"]] += 1
						if avf_c["conditionType"] == "CounterCreator":
							for cond in avf_c["counter"]["conditions"]:
								log.info(f"Inner conditionType: {cond['conditionType']}")
								if cond["conditionType"] not in cc_keeptrack:
									cc_keeptrack[cond["conditionType"]] = 1
								else:
									cc_keeptrack[cond["conditionType"]] += 1

		log.info(cc_keeptrack)
		log.info(non_cc_keeptrack)

	def importQuests(self):
		filename, ok = safe_file_dialog(
			QFileDialog.getOpenFileName, "Import Quest JSON"
		)
		if not ok or filename is None:
			log.info("No file selected, aborting quest import.")
			return
		log.info(filename)
		with open(filename, "r") as f:
			try:
				quests_import = json.load(f)
			except Exception as e:
				log.error(f"Error loading quest file: {e}")
			for quest_id in quests_import.keys():
				# print(f"Found quest {quests_import[quest_id]['QuestName']} ({quest_id})")
				log.info(f"{quests_import[quest_id]['QuestName']}")
				self.state.quests[quest_id] = quests_import[quest_id]
				quest = QListWidgetItem(
					f"{quests_import[quest_id]['QuestName']}, {quest_id}"
				)
				quest.setData(Qt.ItemDataRole.UserRole, quest_id)
				self.ui.questList.addItem(quest)
				log.info(quest.data(Qt.ItemDataRole.UserRole))

	def loadItemsJSON(self):
		if self.itemsJSON is not None:
			self.itemsJSON = None
			log.info(f"Items.json detected, wiping and re-importing.")
		filename, ok = safe_file_dialog(
			QFileDialog.getOpenFileName, "Import items.json"
		)
		if not ok or filename is None:
			log.info("No file selected, aborting items import.")
			return
		with open(filename, "r", encoding="cp866") as f:
			self.itemsJSON = json.load(f)

	def getAllChildrenCalc(self):
		if self.itemsJSON is None:
			print(f"No items.json loaded, cannot calculate children.")
			return
		print(f"Enter via console the parent ID that you wish to use:")
		parent_id = input()
		found_ids = []
		for item_id in self.itemsJSON.keys():
			chain_top = False
			current_id = item_id
			while not chain_top:
				current_parent = self.itemsJSON[current_id]["_parent"]
				if current_parent == parent_id:
					chain_top = True
					found_ids.append(item_id)
				if current_id == "54009119af1c881c07000029":
					chain_top = True
				current_id = current_parent
		print(f"[")
		for _id in found_ids:
			print(f'"{_id}",')
		print(f"]")

	def createLocaleFromJSON(self, q_file=None, l_file=None):

		if q_file:
			qfilename = q_file
		else:
			try:
				qfilename, ok = safe_file_dialog(
					QFileDialog.getOpenFileName, "Open Quest JSON"
				)
				if not ok or qfilename is None:
					log.info(
						"No file selected for quest JSON, aborting locale generation."
					)
					return
			except:
				return
		log.info(qfilename)

		if l_file:
			lfilename = l_file
		else:
			try:
				lfilename, ok = safe_file_dialog(
					QFileDialog.getOpenFileName, "Open Locale JSON"
				)
				if not ok or lfilename is None:
					log.info(
						"No file selected for locale JSON, aborting locale generation."
					)
					return
			except:
				return
		log.info(lfilename)

		with open(qfilename, "r", encoding="utf-8") as f:
			try:
				quests_import = json.load(f)
				for quest_id, quest in quests_import.items():
					log.info(f"Found quest: {quest['QuestName']} ({quest_id})")
				locales = locale_builders.locale_keys(quests_import)
				log.debug(locales)

				with open(lfilename, "r") as baselocale_f:
					base_locale = json.load(baselocale_f)
				final_locale = locale_builders.merge_locale(base_locale, locales)
				log.debug(final_locale)
				with open(lfilename, "w") as savelocale_f:
					json.dump(final_locale, savelocale_f, indent=4)

			except Exception as e:
				log.error(
					f"Error generating locale for quest file: {traceback.format_exc()}"
				)

	def remove_selected_quest(self):
		qlist = self.ui.questList
		select = qlist.selectedItems()
		# if no quest selected, just skip
		if len(select) <= 0:
			return
		quest_text = select[0].text()

		# hacky but easier than setting up a bunch of tables in qt6
		quest_id = quest_text.split(" ")[-1]
		# remove the quest-to-be-edited from the lists
		if quest_id in self.state.quests:
			old_quest = self.state.quests.pop(quest_id)
		for i in range(self.ui.questList.count()):
			if str(quest_id) in self.ui.questList.item(i).text():
				self.ui.questList.takeItem(i)
				break

	def start_update_check(self):
		"""Check for a newer release in the background; the result lands in set_update_status."""
		for old_worker in self._update_workers:
			old_worker.stale = True  # an older check's result must not overwrite this one's
		worker = UpdateCheckWorker(self.state.config)
		worker.signals.finished.connect(self.set_update_status)
		self._update_workers.append(worker)  # keep it (and its signals) alive while it runs
		QThreadPool.globalInstance().start(worker)

	def set_update_status(self, status):
		self.update_status = status
		if status.state == OUTDATED:
			self.statusBar().showMessage(
				f"{status.text} Latest version: {status.latest_version}", 15000
			)
		elif status.state == UNKNOWN:
			self.statusBar().showMessage(status.text, 8000)

	def onSettings(self):
		config = self.state.config
		before = config.settings()
		dlg = self.spawnWindow("SettingsWindow")
		if dlg.exec() and any(before[name] != getattr(config, name) for name in UPDATE_SETTING_NAMES):
			# the update settings changed, so check again with the new ones
			self.update_status = pending_status(config)
			self.start_update_check()

	def onAbout(self):
		dlg = self.spawnWindow("AboutWindow")
		dlg.updateAbout(self.update_status.local_version, self.update_status.project_url)
		dlg.exec()

	def editDataFiles(self):
		dlg = self.spawnWindow("DataWindow")

	def popup(self, message):
		dlg = self.spawnWindow("AboutWindow")
		text = dlg.ui.label.text()
		text = message
		dlg.ui.label.setText(QtCore.QCoreApplication.translate("AboutMenu", text))
		dlg.exec()

	def onExportQuests(self):
		self.exportAll(self.state.quests)

	def onExit(self):
		sys.exit(0)

	def onUpdateWindow(self):
		status = self.update_status
		dlg = self.spawnWindow("UpdateWindow")
		dlg.updateVersion(
			status.local_version, status.latest_display, status.project_url, status.text
		)
		dlg.exec()

	def onQuestWindow(self):
		for window in self.windows:  # Checks if QUESTDLG Open if so make active window.
			if isinstance(window, Gui_QuestDlg) and window.isVisible():
				window.activateWindow()
				return
		dlg = self.spawnWindow("QuestBuilder")

	def onAssortWindow(self):
		dlg = self.spawnWindow("AssortBuilder")

	def exportAll(self, quest):
		qfilename, ok = safe_file_dialog(
			QFileDialog.getSaveFileName, "Export Quest JSON"
		)
		if not ok or qfilename is None:
			log.info("No file selected for quest export, aborting export.")
			return
		with open(qfilename, "w") as f:
			try:
				out = json.dumps(quest, indent=4).strip("[]\n")
				f.write(out)
				f.close()
				self.popup(
					message=f"The quest export has completed successfully and can be found at {qfilename}."
				)
			except Exception as e:
				log.error(f"Error: {e}")
				self.popup(
					message=f"An error has occurred while exporting the final quest JSON file."
				)
			finally:
				f.close()

		try:
			self.createLocaleFromJSON(q_file=qfilename)
			self.popup(message=f"The locale has been successfully updated.")
		except Exception as e:
			log.error(f"Error: {e}")
			self.popup(
				message=f"An error has occurred while updating the locale JSON file."
			)
		finally:
			f.close()
