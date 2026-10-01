import copy
import logging

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMainWindow

from tb_ui.gui_rewards import Ui_rewardBuilder
from table_fields import add_table_field, remove_selected_table_item
from utils import is_true, new_id

log = logging.getLogger(__name__)


class Gui_RewardDlg(QMainWindow):
	# (reward_timing, reward_type, reward_id, reward) - sent when the user finalizes a reward
	reward_ready = Signal(str, str, str, object)

	def __init__(self, state, parent=None):
		super().__init__(parent)
		self.ui = Ui_rewardBuilder()
		self.ui.setupUi(self)
		self.state = state
		self.on_launch()  # Custom code in this one
		self.show()
		self.id = new_id()
		# self.items_item = []
		# self.items_asu = []

	def on_launch(self):
		self.setup_box_selections()
		self.setup_buttons()

	def add_item(self, tab):
		has_soc = False
		has_pid = False
		has_sid = False
		match tab:
			case "Item":
				item = {
					"_id": new_id(),
					"_tpl": self.ui.fld_utpl_item.displayText(),
				}
				if self.ui.chk_soc_item.isChecked() or self.ui.chk_fir_item.isChecked():
					item["upd"] = {}
				if self.ui.chk_soc_item.isChecked():
					item["upd"]["StackObjectsCount"] = self.ui.box_soc_item.cleanText()
					has_soc = True
				if self.ui.chk_fir_item.isChecked():
					item["upd"]["SpawnedInSession"] = self.ui.chk_fir_item.isChecked()
				if self.ui.chk_parentid_item.isChecked():
					item["parentId"] = self.ui.fld_parentid_item.displayText()
					has_pid = True
				if self.ui.chk_slotid_item.isChecked():
					item["slotId"] = self.ui.fld_slotid_item.displayText()
					has_sid = True
				# self.items_item.append(item)
				# self.ui.list_items_item.addItem(f"_id: {item['_id']}, _tpl: {item['_tpl']}, SOC: {item['upd']['StackObjectsCount'] if has_soc else 'n/a'}, parentId: {item['parentId'] if has_pid else 'n/a'}, slotId: {item['slotId'] if has_sid else 'n/a'}, fir: {self.ui.chk_fir_item.isChecked()}")
				add_table_field(
					self.state,
					f"RewardItem",
					self.ui.tb_item,
					item["_id"],
					{
						0: item["_id"],
						1: item["_tpl"],
						2: item["upd"]["StackObjectsCount"] if has_soc else "n/a",
						3: item["parentId"] if has_pid else "n/a",
						4: item["slotId"] if has_sid else "n/a",
						5: self.ui.chk_fir_item.isChecked(),
					},
					item,
				)

			case "AssortmentUnlock":
				item = {
					"_id": new_id(),
					"_tpl": self.ui.fld_utpl_asu.displayText(),
				}
				if self.ui.chk_soc_asu.isChecked() or self.ui.chk_fir_asu.isChecked():
					item["upd"] = {}
				if self.ui.chk_soc_asu.isChecked():
					item["upd"]["StackObjectsCount"] = int(
						self.ui.box_soc_asu.cleanText()
					)
					has_soc = True
				if self.ui.chk_fir_asu.isChecked():
					item["upd"]["SpawnedInSession"] = self.ui.chk_fir_asu.isChecked()
				if self.ui.chk_parentid_asu.isChecked():
					item["parentId"] = self.ui.box_parentid_asu.displayText()
					has_pid = True
				if self.ui.chk_slotid_asu.isChecked():
					item["slotId"] = self.ui.box_slotid_asu.displayText()
					has_sid = True

				# self.items_asu.append(item)
				# self.ui.list_items_asu.addItem(f"_id: {item['_id']}, _tpl: {item['_tpl']}, SOC: {item['upd']['StackObjectsCount'] if has_soc else 'n/a'}, fir: {self.ui.chk_fir_asu.isChecked()}")

				add_table_field(
					self.state,
					f"RewardAssortmentUnlock",
					self.ui.tb_asu_item,
					item["_id"],
					{
						0: item["_id"],
						1: item["_tpl"],
						2: item["upd"]["StackObjectsCount"] if has_soc else "n/a",
						3: item["parentId"] if has_pid else "n/a",
						4: item["slotId"] if has_sid else "n/a",
						5: self.ui.chk_fir_asu.isChecked(),
					},
					item,
				)

	def remove_selected_item(self, tab):
		match tab:
			case "AssortmentUnlock":
				remove_selected_table_item(
					self.state,
					type="RewardAssortmentUnlock", table=self.ui.tb_asu_item, id_row=0
				)
			case "Item":
				remove_selected_table_item(
					self.state,
					type="RewardItem", table=self.ui.tb_item, id_row=0
				)

	def select_target_id(self, item_obj, manual=False, manual_id=None):
		if manual:
			return manual_id
		if item_obj is None or len(item_obj) <= 0:
			return ""
		else:
			if len(item_obj[0]) >= 1:
				try:
					return item_obj[0]["_id"]
				except Exception as e:
					return ""
			else:  # Should never happen, but if there is no ID (empty item list might happen)
				return ""

	def finalize(self, reward_type):
		match reward_type:
			case "Achievement":
				reward_timing = self.ui.box_rewardtiming_ach.currentText()
				reward = {
					"availableInGameEditions": [],
					"id": self.id,
					"index": 0,
					"target": self.ui.fld_ach_id_ach.displayText(),
					"type": "Achievement",
					"unknown": is_true(self.ui.bx_unknown_ach.currentText()),
				}
			case "AssortmentUnlock":
				reward_timing = self.ui.box_rewardtiming_asu.currentText()
				local_items = self.state.get_multicolumn_values_list(
					"RewardAssortmentUnlock"
				)
				reward = {
					"availableInGameEditions": [],
					"id": self.id,
					"index": 0,
					"items": local_items,
					"loyaltyLevel": int(self.ui.box_loyalty_asu.cleanText()),
					"target": self.select_target_id(
						item_obj=local_items,
						manual=self.ui.chk_target_specify_asu.isChecked(),
						manual_id=self.ui.fld_man_target_asu.displayText(),
					),
					"traderId": self.state.traders[
						self.ui.box_trader_asu.currentText()
					],
					"type": "AssortmentUnlock",
					"unknown": is_true(self.ui.box_unknown_asu.currentText()),
				}
			case "Experience":
				reward_timing = self.ui.box_rewardtiming_exp.currentText()
				reward = {
					"availableInGameEditions": [],
					"id": self.id,
					"index": 0,
					"type": "Experience",
					"unknown": is_true(self.ui.box_unknown_exp.currentText()),
					"value": int(self.ui.box_amount_exp.displayText()),
				}
			case "Item":
				reward_timing = self.ui.box_rewardtiming_item.currentText()
				local_items = self.state.get_multicolumn_values_list(
					"RewardItem"
				)
				reward = {
					"availableInGameEditions": [],
					"findInRaid": is_true(self.ui.box_fir_item.currentText()),
					"id": self.id,
					"index": 0,
					"items": local_items,
					"target": self.select_target_id(
						item_obj=local_items,
						manual=self.ui.chk_target_specify_it.isChecked(),
						manual_id=self.ui.fld_man_target_it.displayText(),
					),
					"type": "Item",
					"unknown": is_true(self.ui.box_unknown_item.currentText()),
					"value": int(self.ui.box_value_item.cleanText()),
				}
			case "Skill":
				reward_timing = self.ui.box_rewardtiming_sk.currentText()
				reward = {
					"availableInGameEditions": [],
					"id": self.id,
					"index": 0,
					"target": self.ui.box_skill_sk.currentText(),
					"type": "Skill",
					"unknown": is_true(self.ui.box_unknown_sk.currentText()),
					"value": int(self.ui.box_points_sk.cleanText()),
				}
			case "StashRows":
				reward_timing = self.ui.box_rewardtiming_sr.currentText()
				reward = {
					"availableInGameEditions": [],
					"id": self.id,
					"index": 0,
					"type": "StashRows",
					"unknown": is_true(self.ui.box_unknown_sr.currentText()),
					"value": int(self.ui.box_rows_sr.cleanText()),
				}
			case "TraderStanding":
				reward_timing = self.ui.box_rewardtiming_ts.currentText()
				reward = {
					"availableInGameEditions": [],
					"id": self.id,
					"index": 0,
					"target": self.state.traders[
						self.ui.box_trader_ts.currentText()
					],
					"type": "TraderStanding",
					"unknown": is_true(self.ui.box_unknown_ts.currentText()),
					"value": float(self.ui.box_loyalty_ts.cleanText()),
				}

			case "TraderUnlock":
				reward_timing = self.ui.box_rewardtiming_tul.currentText()
				reward = {
					"availableInGameEditions": [],
					"id": self.id,
					"index": 0,
					"target": self.state.traders[
						self.ui.box_trader_tul.currentText()
					],
					"type": "TraderUnlock",
					"unknown": is_true(self.ui.box_unknown_tul.currentText()),
				}

		self.reward_ready.emit(reward_timing, reward_type, self.id, reward)
		self.close()

	def load_settings_from_dict(self, settings, reward_timing):
		pass
		log.info(f"Loading reward from dict: {settings}")
		self.id = settings["id"]
		# first field is the JSON key
		# tuple is (item reference to set, type of item reference (determines func to set))
		reward_type = settings["type"]
		# todo - more robust for rewards missing fields; need to build a better validator
		# doing just the unknown for now since it is missing in Legs' test json
		unknown_or = "true"
		if "unknown" in settings:
			unknown_or = str(settings["unknown"])

		match reward_type:
			case "Achievement":
				self.ui.fld_ach_id_ach.setText(settings["target"])
				self.ui.bx_unknown_ach.setCurrentText(unknown_or)
				self.ui.box_rewardtiming_ach.setCurrentText(reward_timing)
				# set the current selected tab accordingly
				self.ui.tabWidget.setCurrentIndex(6)

			case "AssortmentUnlock":
				trader = self.state.traders_invert[settings["traderId"]]
				self.ui.fld_tid_asu.setText(settings["target"])
				self.ui.box_trader_asu.setCurrentText(trader)
				self.ui.box_loyalty_asu.setValue(int(settings["loyaltyLevel"]))
				self.ui.box_unknown_asu.setCurrentText(unknown_or)
				self.ui.box_rewardtiming_asu.setCurrentText(reward_timing)
				self.ui.tabWidget.setCurrentIndex(2)
				self.items_asu = copy.deepcopy(settings["items"])
				for item in self.items_asu:
					has_soc = "upd" in item and "StackObjectsCount" in item["upd"]
					has_pid = "parentId" in item
					has_sid = "slotId" in item
					add_table_field(
						self.state,
						f"RewardAssortmentUnlock",
						self.ui.tb_asu_item,
						item["_id"],
						{
							0: item["_id"],
							1: item["_tpl"],
							2: item["upd"]["StackObjectsCount"] if has_soc else "n/a",
							3: item["parentId"] if has_pid else "n/a",
							4: item["slotId"] if has_sid else "n/a",
							5: self.ui.chk_fir_asu.isChecked(),
						},
						item,
					)
					# self.ui.list_items_asu.addItem(f"_id: {item['_id']}, _tpl: {item['_tpl']}, SOC: {item['upd']['StackObjectsCount'] if has_soc else 'n/a'}, parentId: {item['parentId'] if has_pid else 'n/a'}, slotId: {item['slotId'] if has_sid else 'n/a'}, fir: {1}")

			case "Experience":
				self.ui.tabWidget.setCurrentIndex(0)
				self.ui.box_rewardtiming_exp.setCurrentText(reward_timing)
				self.ui.box_amount_exp.setText(str(settings["value"]))
				self.ui.box_unknown_exp.setCurrentText(unknown_or)

			case "Item":
				self.ui.tabWidget.setCurrentIndex(1)
				self.ui.box_rewardtiming_item.setCurrentText(reward_timing)
				self.ui.fld_tid_item.setText(settings["target"])
				self.ui.box_value_item.setValue(int(settings["value"]))
				self.ui.box_fir_item.setCurrentText(str(settings["findInRaid"]))
				self.ui.box_unknown_item.setCurrentText(unknown_or)
				self.items_item = copy.deepcopy(settings["items"])
				for item in self.items_item:
					has_soc = "upd" in item and "StackObjectsCount" in item["upd"]
					has_pid = "parentId" in item
					has_sid = "slotId" in item
					add_table_field(
						self.state,
						f"RewardItem",
						self.ui.tb_item,
						item["_id"],
						{
							0: item["_id"],
							1: item["_tpl"],
							2: item["upd"]["StackObjectsCount"] if has_soc else "n/a",
							3: item["parentId"] if has_pid else "n/a",
							4: item["slotId"] if has_sid else "n/a",
							5: self.ui.chk_fir_item.isChecked(),
						},
						item,
					)
					# self.ui.list_items_item.addItem(f"_id: {item['_id']}, _tpl: {item['_tpl']}, SOC: {item['upd']['StackObjectsCount'] if has_soc else 'n/a'}, parentId: {item['parentId'] if has_pid else 'n/a'}, slotId: {item['slotId'] if has_sid else 'n/a'}, fir: {1}")

			case "Skill":
				self.ui.tabWidget.setCurrentIndex(4)
				self.ui.box_rewardtiming_sk.setCurrentText(reward_timing)
				self.ui.box_skill_sk.setCurrentText(settings["target"])
				self.ui.box_points_sk.setValue(int(settings["value"]))
				self.ui.box_unknown_sk.setCurrentText(unknown_or)

			case "StashRows":
				self.ui.tabWidget.setCurrentIndex(5)
				self.ui.box_rewardtiming_sr.setCurrentText(reward_timing)
				self.ui.box_rows_sr.setValue(int(settings["value"]))
				self.ui.box_unknown_sr.setCurrentText(unknown_or)

			case "TraderStanding":
				trader = self.state.traders_invert[settings["target"]]
				self.ui.tabWidget.setCurrentIndex(3)
				self.ui.box_rewardtiming_ts.setCurrentText(reward_timing)
				self.ui.box_loyalty_ts.setValue(float(settings["value"]))
				self.ui.box_trader_ts.setCurrentText(trader)
				self.ui.box_unknown_ts.setCurrentText(unknown_or)

			case "TraderUnlock":
				trader = self.state.traders_invert[settings["target"]]
				self.ui.tabWidget.setCurrentIndex(7)
				self.ui.box_rewardtiming_tul.setCurrentText(reward_timing)
				self.ui.box_unknown_tul.setCurrentText(unknown_or)
				self.ui.box_trader_tul.setCurrentText(trader)

	def setup_buttons(self):
		self.ui.pb_finalize_ach.released.connect(lambda: self.finalize("Achievement"))
		self.ui.pb_finalize_asu.released.connect(
			lambda: self.finalize("AssortmentUnlock")
		)
		self.ui.pb_finalize_exp.released.connect(lambda: self.finalize("Experience"))
		self.ui.pb_finalize_item.released.connect(lambda: self.finalize("Item"))
		self.ui.pb_finalize_sk.released.connect(lambda: self.finalize("Skill"))
		self.ui.pb_finalize_sr.released.connect(lambda: self.finalize("StashRows"))
		self.ui.pb_finalize_ts.released.connect(lambda: self.finalize("TraderStanding"))
		self.ui.pb_finalize_tul.released.connect(lambda: self.finalize("TraderUnlock"))

		self.ui.pb_additem_asu.released.connect(
			lambda: self.add_item("AssortmentUnlock")
		)
		self.ui.pb_remitem_asu.released.connect(
			lambda: self.remove_selected_item("AssortmentUnlock")
		)

		self.ui.pb_additem_item.released.connect(lambda: self.add_item("Item"))
		self.ui.pb_remitem_item.released.connect(
			lambda: self.remove_selected_item("Item")
		)

	def setup_box_selections(self):
		self.ui.box_trader_asu.addItems(self.state.traders.keys())
		self.ui.box_trader_ts.addItems(self.state.traders.keys())
		self.ui.box_trader_tul.addItems(self.state.traders.keys())
		self.ui.box_unknown_exp.addItems(self.state.config.default_ft)
		self.ui.box_rewardtiming_exp.addItems(
			self.state.config.reward_timing
		)
		self.ui.box_fir_item.addItems(self.state.config.default_tf)
		self.ui.box_unknown_item.addItems(self.state.config.default_ft)
		self.ui.box_rewardtiming_item.addItems(
			self.state.config.reward_timing
		)
		self.ui.box_unknown_asu.addItems(self.state.config.default_ft)
		self.ui.box_rewardtiming_asu.addItems(
			self.state.config.reward_timing
		)
		self.ui.box_unknown_ts.addItems(self.state.config.default_ft)
		self.ui.box_rewardtiming_ts.addItems(
			self.state.config.reward_timing
		)
		self.ui.box_skill_sk.addItems(self.state.config.default_skills)
		self.ui.box_unknown_sk.addItems(self.state.config.default_ft)
		self.ui.box_rewardtiming_sk.addItems(
			self.state.config.reward_timing
		)
		self.ui.box_rewardtiming_sr.addItems(
			self.state.config.reward_timing
		)
		self.ui.box_unknown_sr.addItems(self.state.config.default_ft)
		self.ui.bx_unknown_ach.addItems(self.state.config.default_ft)
		self.ui.box_rewardtiming_ach.addItems(
			self.state.config.reward_timing
		)
		self.ui.box_rewardtiming_tul.addItems(
			self.state.config.reward_timing
		)
		self.ui.box_unknown_tul.addItems(self.state.config.default_ft)
