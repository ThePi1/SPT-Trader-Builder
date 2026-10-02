import sys
import traceback
import logging

from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtWidgets import (
	QApplication,
	QAbstractItemView,
	QFileDialog,
	QMainWindow,
	QListWidgetItem,
	QMessageBox,
	QTableWidgetItem,
)

from modules.builders import assort as assort_builders
from modules.builders import locale as locale_builders
from modules.builders.lookup import filter_rows, lookup_rows
from modules.config import UPDATE_SETTING_NAMES
from modules.state import load_items_file
from modules.gui.compiled.gui_main import Ui_MainGUI
from modules.updates import OUTDATED, UNKNOWN, UpdateCheckWorker, pending_status
from modules.utils import LOG_FILE, new_id, read_json, set_debug_logging, write_json
from modules.windows.about import Gui_AboutDlg
from modules.windows.assort import Gui_AssortDlg
from modules.windows.children_dialog import Gui_ChildrenDlg
from modules.windows.common import safe_file_dialog
from modules.windows.data_editor import Gui_DataEditor
from modules.windows.quest import Gui_QuestDlg
from modules.windows.settings import Gui_SettingsDlg
from modules.windows.update_dialog import Gui_UpdatesDlg

log = logging.getLogger(__name__)

# What createLocaleFromJSON and export_locale report
LOCALE_UPDATED = "updated"
LOCALE_CANCELLED = "cancelled"  # a file wasn't chosen
LOCALE_FAILED = "failed"  # an error was shown


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
		self.refresh_items_status()
		if state.items_error:  # (the file chosen in Settings couldn't be used at startup)
			self.statusBar().showMessage(f"Could not load items.json: {state.items_error}", 20000)

	def setup_vars(self):
		self.weaponlist = []
		self.windows = []
		self.quest_editors = {}  # quest id -> the dialog editing that quest
		self.weapon_preset_filename = None

	def connect_actions(self):
		self.ui.actionExit.triggered.connect(self.onExit)
		self.ui.actionSettingsMenu.triggered.connect(self.onSettings)
		self.ui.actionExport_Queued_Quests.triggered.connect(self.onExportQuests)
		self.ui.actionGet_all_children_of_parent_ID.triggered.connect(
			self.getAllChildrenCalc
		)
		self.ui.actionCreate_locale_from_Quest_JSON.triggered.connect(
			self.onCreateLocale
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
		self.ui.actionEdit_Selected_Quest.triggered.connect(self.edit_selected_quest)
		self.ui.questList.itemDoubleClicked.connect(
			lambda item: self.edit_quest(item.data(Qt.ItemDataRole.UserRole))
		)
		self.ui.fld_idlookup.textChanged.connect(self.update_idlookup)
		# self.ui.wb_treeview.itemSelectionChanged.connect(self.onWeaponSelected)

	def update_idlookup(self):
		"""Fill the ID Lookup table with every row where the search text matches any column."""
		rows = lookup_rows(
			self.state.id_search,
			self.state.quests,
			self.state.items,
			self.state.locations,
			self.state.traders,
		)
		matches = filter_rows(rows, self.ui.fld_idlookup.text())
		table = self.ui.id_table
		table.setUpdatesEnabled(False)  # (thousands of rows: repaint once at the end)
		try:
			table.setRowCount(len(matches))
			for row, (item_id, data, kind) in enumerate(matches):
				table.setItem(row, 0, Gui_MainWindow.table_widget(item_id))
				table.setItem(row, 1, Gui_MainWindow.table_widget(data, hover=True))
				table.setItem(row, 2, Gui_MainWindow.table_widget(kind))
		finally:
			table.setUpdatesEnabled(True)

	def refresh_items_status(self):
		"""The line on the ID Lookup tab saying whether an items.json is loaded."""
		state = self.state
		label = self.ui.lbl_items_status
		if state.loaded_items is None:
			label.setText("No items.json loaded - import items in Settings.")
			label.setToolTip(state.items_error or "")
		elif state.items_error:
			label.setText(
				f"items.json loaded ({len(state.items)} items): the one chosen in Settings "
				"could not be used, so the included file is in use."
			)
			label.setToolTip(state.items_error)
		else:
			label.setText(f"items.json loaded ({len(state.items)} items).")
			label.setToolTip(str(state.items_path))

	def apply_items(self, items, path=None, error=None):
		"""Use this items.json as the item database from now on (None for none), and update
		everything that shows it."""
		if items is None:
			self.state.set_items({}, None, error)
		else:
			self.state.set_items(items, path, error)
		self.refresh_items_status()
		if self.ui.fld_idlookup.text() or self.ui.id_table.rowCount():
			self.update_idlookup()  # (the rows come from the items)

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
				dlg = Gui_SettingsDlg(
					self.state.config,
					parent=self,
					state=self.state,
					apply_items=self.apply_items,
				)

		self.windows.append(dlg)
		return dlg

	def on_quest_saved(self, quest_id, quest_name, quest, locale):
		"""A quest was made (or an existing one edited): store it, and show it in the quest list."""
		self.state.quests[quest_id] = quest
		self.state.quest_locales[quest_id] = locale
		text = f"{quest_name}, {quest_id}"
		item = self.quest_list_item(quest_id)
		if item is not None:
			item.setText(text)  # (an edited quest keeps its place in the list)
		else:
			item = QListWidgetItem(text)
			item.setData(Qt.ItemDataRole.UserRole, quest_id)
			self.ui.questList.addItem(item)
		if self.ui.fld_idlookup.text() or self.ui.id_table.rowCount():
			self.update_idlookup()  # (it lists the quests' names)

	def quest_list_item(self, quest_id):
		"""The quest list's entry for a quest, or None."""
		for i in range(self.ui.questList.count()):
			item = self.ui.questList.item(i)
			if item.data(Qt.ItemDataRole.UserRole) == quest_id:
				return item
		return None

	def edit_selected_quest(self):
		"""The Edit > Edit Selected Quest menu item."""
		select = self.ui.questList.selectedItems()
		if select:
			self.edit_quest(select[0].data(Qt.ItemDataRole.UserRole))

	def edit_quest(self, quest_id):
		"""Open a quest in the Quest Builder to edit it (or bring its window forward if it is already open).

		Returns the dialog, or None if there is no such quest.
		"""
		quest = self.state.quests.get(quest_id)
		if quest is None:
			return None
		open_dlg = self.quest_editors.get(quest_id)
		if open_dlg is not None and open_dlg.isVisible():
			open_dlg.raise_()
			open_dlg.activateWindow()
			return open_dlg
		dlg = Gui_QuestDlg(
			self.state, parent=self, quest=quest, locale=self.state.quest_locales.get(quest_id)
		)
		dlg.quest_saved.connect(self.on_quest_saved)
		self.quest_editors[quest_id] = dlg
		self.windows.append(dlg)
		return dlg

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
		try:
			write_json(self.weapon_preset_filename, weaponlist, indent=2)
		except OSError as e:
			log.error(f"Could not save the weapon preset to {self.weapon_preset_filename}: {e}")
			self.show_error(
				"Export Weapon Preset",
				f"The weapon preset could not be saved to {self.weapon_preset_filename}.\n\n{e}",
			)
			self.weapon_preset_filename = None  # ask again next time

	def copy_clicked_cell(self, item):
		# if self.ui.ab_weappart_check.isChecked():
		# return
		text = item.data(Qt.ItemDataRole.UserRole)
		QApplication.clipboard().setText(text)

	def show_error(self, title, message):
		QMessageBox.critical(self, title, message)

	def load_quests_file(self, filename):
		"""Read a quest JSON file. If it can't be used, shows why and returns None."""
		try:
			quests = read_json(filename)
		except (OSError, ValueError) as e:  # (a bad JSON file is a ValueError)
			log.error(f"Could not read {filename}: {e}")
			self.show_error("Quest file", f"Could not read {filename}.\n\n{e}")
			return None
		looks_right = isinstance(quests, dict) and all(
			isinstance(quest, dict) and "QuestName" in quest for quest in quests.values()
		)
		if not looks_right:
			log.error(f"{filename} is not a quest file")
			self.show_error(
				"Quest file",
				f"{filename} doesn't look like a quest file.\n\n"
				"Expected quests keyed by their id, each with a QuestName.",
			)
			return None
		return quests

	def load_locale_file(self, filename):
		"""Read a locale JSON file ({key: text}). If it can't be used, shows why and returns None."""
		try:
			locale = read_json(filename)
		except (OSError, ValueError) as e:  # (a bad JSON file is a ValueError)
			log.error(f"Could not read {filename}: {e}")
			self.show_error("Locale file", f"Could not read {filename}.\n\n{e}")
			return None
		if not isinstance(locale, dict):
			log.error(f"{filename} is not a locale file")
			self.show_error(
				"Locale file",
				f"{filename} doesn't look like a locale file.\n\nExpected a dictionary of text entries.",
			)
			return None
		return locale

	def analyze_cc(self):
		log.info(f"Analyzing CC subtypes, opening dialogue...")

		filename, ok = safe_file_dialog(
			QFileDialog.getOpenFileName, "Import Quest JSON"
		)
		if not ok or filename is None:
			log.info("No file selected, aborting CC analysis.")
			return

		log.info(filename)
		quests_import = self.load_quests_file(filename)
		if quests_import is None:
			return
		cc_keeptrack = {}
		non_cc_keeptrack = {}
		for quest_id in quests_import.keys():
			# print(f"Found quest {quests_import[quest_id]['QuestName']} ({quest_id})")
			log.info(f"{quests_import[quest_id]['QuestName']}")
			if (
				"conditions" in quests_import[quest_id]
				and "AvailableForFinish" in quests_import[quest_id]["conditions"]
				and len(quests_import[quest_id]["conditions"]["AvailableForFinish"]) > 0
			):
				for avf_c in quests_import[quest_id]["conditions"]["AvailableForFinish"]:
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
		quests_import = self.load_quests_file(filename)
		if quests_import is None:
			return
		for quest_id, quest_data in quests_import.items():
			log.info(f"{quest_data['QuestName']}")
			if quest_id in self.state.quests:
				self.remove_quest_list_item(quest_id)  # (importing it again replaces it)
			self.state.quests[quest_id] = quest_data
			quest = QListWidgetItem(f"{quest_data['QuestName']}, {quest_id}")
			quest.setData(Qt.ItemDataRole.UserRole, quest_id)
			self.ui.questList.addItem(quest)

	def remove_quest_list_item(self, quest_id):
		"""Take a quest's entry out of the quest list (not out of state.quests)."""
		for i in range(self.ui.questList.count()):
			if self.ui.questList.item(i).data(Qt.ItemDataRole.UserRole) == quest_id:
				self.ui.questList.takeItem(i)
				return

	def loadItemsJSON(self):
		"""Ask for an items.json, load it, and remember it as the one to load at startup.

		Returns True if one was loaded.
		"""
		filename, ok = safe_file_dialog(
			QFileDialog.getOpenFileName, "Import items.json"
		)
		if not ok or filename is None:
			log.info("No file selected, aborting items import.")
			return False
		try:
			items = load_items_file(filename)
		except (OSError, ValueError) as e:  # (a bad JSON file is a ValueError)
			log.error(f"Could not read {filename}: {e}")
			self.show_error("items.json", f"Could not read {filename}.\n\n{e}")
			return False
		if self.state.loaded_items is not None:
			log.info("Items.json detected, replacing it.")
		self.apply_items(items, filename)  # (only replaced once the new file has loaded)
		log.info(f"Loaded {len(items)} items from {filename}")
		self.remember_items_file(filename)
		return True

	def remember_items_file(self, path):
		"""Save path as the items.json to load at startup."""
		config = self.state.config
		try:
			config.update_settings({**config.settings(), "items_file": path})
		except (OSError, ValueError) as e:
			log.warning(f"Could not save the items.json setting: {e}")
			QMessageBox.warning(
				self,
				"items.json",
				f"The items.json was loaded, but it could not be remembered for next time.\n\n{e}",
			)

	def getAllChildrenCalc(self):
		"""Open the child-item finder (it can load an items.json itself if none is loaded yet)."""
		dlg = Gui_ChildrenDlg(lambda: self.state.loaded_items, self.loadItemsJSON, parent=self)
		self.windows.append(dlg)
		dlg.show()
		return dlg

	def createLocaleFromJSON(self, q_file=None, l_file=None):
		"""Add blank locale entries for a quest file's text to a locale file.

		Asks for whichever files aren't given. Returns "updated", "cancelled" (a file
		wasn't chosen) or "failed" (an error was shown).
		"""
		if q_file:
			qfilename = q_file
		else:
			qfilename, ok = safe_file_dialog(QFileDialog.getOpenFileName, "Open Quest JSON")
			if not ok or qfilename is None:
				log.info("No file selected for quest JSON, aborting locale generation.")
				return LOCALE_CANCELLED
		log.info(qfilename)

		if l_file:
			lfilename = l_file
		else:
			lfilename, ok = safe_file_dialog(QFileDialog.getOpenFileName, "Open Locale JSON")
			if not ok or lfilename is None:
				log.info("No file selected for locale JSON, aborting locale generation.")
				return LOCALE_CANCELLED
		log.info(lfilename)

		quests_import = self.load_quests_file(qfilename)
		if quests_import is None:
			return LOCALE_FAILED
		for quest_id, quest in quests_import.items():
			log.info(f"Found quest: {quest['QuestName']} ({quest_id})")
		base_locale = self.load_locale_file(lfilename)
		if base_locale is None:
			return LOCALE_FAILED
		try:
			locales = locale_builders.locale_keys(quests_import)
			log.debug(locales)
			final_locale = locale_builders.merge_locale(base_locale, locales)
			log.debug(final_locale)
			write_json(lfilename, final_locale, indent=4)
		except (OSError, ValueError, KeyError, TypeError) as e:
			log.error(f"Error generating locale for quest file: {traceback.format_exc()}")
			self.show_error(
				"Locale file", f"The locale file {lfilename} could not be updated.\n\n{type(e).__name__}: {e}"
			)
			return LOCALE_FAILED
		return LOCALE_UPDATED

	def onCreateLocale(self):
		"""The Edit > Create locale from Quest JSON menu item."""
		if self.createLocaleFromJSON() == LOCALE_UPDATED:
			self.popup("Create locale from Quest JSON", "The locale has been successfully updated.")

	def remove_selected_quest(self):
		qlist = self.ui.questList
		select = qlist.selectedItems()
		# if no quest selected, just skip
		if len(select) <= 0:
			return
		quest_text = select[0].text()

		# hacky but easier than setting up a bunch of tables in qt6
		quest_id = quest_text.split(" ")[-1]
		editor = self.quest_editors.pop(quest_id, None)
		if editor is not None:
			editor.close()  # (saving it would bring the removed quest back)
		# remove the quest-to-be-edited from the lists
		if quest_id in self.state.quests:
			old_quest = self.state.quests.pop(quest_id)
		self.state.quest_locales.pop(quest_id, None)
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
		if not dlg.exec():
			return
		self.apply_debug_logging()
		if any(before[name] != getattr(config, name) for name in UPDATE_SETTING_NAMES):
			# the update settings changed, so check again with the new ones
			self.update_status = pending_status(config)
			self.start_update_check()

	def apply_debug_logging(self):
		"""Turn the debug log file on or off to match the setting, and say so if it can't be created."""
		try:
			set_debug_logging(self.state.config.debug_logging)
		except OSError as e:
			log.error(f"Could not create the debug log file {LOG_FILE}: {e}")
			QMessageBox.warning(
				self,
				"Debug log",
				f"Debug logging is turned on, but the log file could not be created at {LOG_FILE}.\n\n{e}",
			)

	def onAbout(self):
		dlg = self.spawnWindow("AboutWindow")
		dlg.updateAbout(self.update_status.local_version, self.update_status.project_url)
		dlg.exec()

	def editDataFiles(self):
		dlg = self.spawnWindow("DataWindow")

	def popup(self, title, message):
		"""Show a message, with an OK button to close it."""
		QMessageBox.information(self, title, message)

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

	def exportAll(self, quests):
		qfilename, ok = safe_file_dialog(
			QFileDialog.getSaveFileName, "Export Quest JSON"
		)
		if not ok or qfilename is None:
			log.info("No file selected for quest export, aborting export.")
			return
		try:
			write_json(qfilename, quests, indent=4)
		except (OSError, ValueError, TypeError) as e:
			log.error(f"Error: {e}")
			self.show_error(
				"Export Quest JSON",
				f"An error has occurred while exporting the final quest JSON file.\n\n{e}",
			)
			return  # (don't go on to save a locale for a quest file that wasn't written)
		self.popup(
			"Export Quest JSON",
			f"The quest export has completed successfully and can be found at {qfilename}.",
		)

		result, lfilename = self.export_locale(quests)
		if result == LOCALE_UPDATED:
			self.popup(
				"Export Locale JSON",
				f"The locale export has completed successfully and can be found at {lfilename}.",
			)
		elif result == LOCALE_CANCELLED:
			self.popup("Export Locale JSON", "The locale was not saved, because no locale file was chosen.")
		# (LOCALE_FAILED: the error has already been shown)

	def export_locale(self, quests):
		"""Save the locale entries of quests that have just been exported.

		Each entry gets the text typed for it in the Quest Builder, or is blank. With "Merge
		locales on export" on, asks for an existing locale file, adds the entries it doesn't have
		yet (the ones it has are kept as they are), and asks where to save the result, starting at
		the file that was opened. With it off, asks where to save a locale file of just these entries.

		Returns (result, the file saved): result is "updated", "cancelled" (a file wasn't chosen)
		or "failed" (an error was shown).
		"""
		try:
			keys = locale_builders.locale_keys(quests)
		except (KeyError, TypeError) as e:  # (e.g. a condition without an id)
			log.error(f"Error working out the locale entries: {traceback.format_exc()}")
			self.show_error(
				"Export Locale JSON",
				f"The locale entries for these quests could not be worked out.\n\n{type(e).__name__}: {e}",
			)
			return LOCALE_FAILED, None
		texts = self.state.locale_texts()
		if self.state.config.merge_locales_on_export:
			base_filename, ok = safe_file_dialog(
				QFileDialog.getOpenFileName, "Open Locale JSON to merge into"
			)
			if not ok or base_filename is None:
				log.info("No locale file selected to merge into, skipping the locale export.")
				return LOCALE_CANCELLED, None
			base_locale = self.load_locale_file(base_filename)
			if base_locale is None:
				return LOCALE_FAILED, None
			locale = locale_builders.merge_locale(base_locale, keys, texts)
			lfilename, ok = safe_file_dialog(
				QFileDialog.getSaveFileName, "Export Locale JSON", dir=base_filename
			)
		else:
			locale = locale_builders.new_locale(keys, texts)
			lfilename, ok = safe_file_dialog(QFileDialog.getSaveFileName, "Export Locale JSON")
		if not ok or lfilename is None:
			log.info("No file selected for the locale export, skipping it.")
			return LOCALE_CANCELLED, None
		try:
			write_json(lfilename, locale, indent=4)
		except (OSError, ValueError, TypeError) as e:
			log.error(f"Could not save the locale to {lfilename}: {e}")
			self.show_error("Export Locale JSON", f"The locale could not be saved to {lfilename}.\n\n{e}")
			return LOCALE_FAILED, None
		log.info(f"Saved {len(locale)} locale entries to {lfilename}")
		return LOCALE_UPDATED, lfilename
