import copy
import logging

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMainWindow

from builders import rewards
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
		ui = self.ui
		match tab:
			case "Item":
				table, table_type, fir_check = ui.tb_item, "RewardItem", ui.chk_fir_item
				item = rewards.reward_item(
					new_id(),
					ui.fld_utpl_item.displayText(),
					stack_count=(
						ui.box_soc_item.cleanText() if ui.chk_soc_item.isChecked() else None
					),
					spawned_in_session=ui.chk_fir_item.isChecked(),
					parent_id=(
						ui.fld_parentid_item.displayText()
						if ui.chk_parentid_item.isChecked()
						else None
					),
					slot_id=(
						ui.fld_slotid_item.displayText()
						if ui.chk_slotid_item.isChecked()
						else None
					),
				)
			case "AssortmentUnlock":
				table, table_type, fir_check = (
					ui.tb_asu_item,
					"RewardAssortmentUnlock",
					ui.chk_fir_asu,
				)
				item = rewards.reward_item(
					new_id(),
					ui.fld_utpl_asu.displayText(),
					stack_count=(
						int(ui.box_soc_asu.cleanText())
						if ui.chk_soc_asu.isChecked()
						else None
					),
					spawned_in_session=ui.chk_fir_asu.isChecked(),
					parent_id=(
						ui.box_parentid_asu.displayText()
						if ui.chk_parentid_asu.isChecked()
						else None
					),
					slot_id=(
						ui.box_slotid_asu.displayText()
						if ui.chk_slotid_asu.isChecked()
						else None
					),
				)
			case _:
				return

		add_table_field(
			self.state,
			table_type,
			table,
			item["_id"],
			{
				0: item["_id"],
				1: item["_tpl"],
				2: item.get("upd", {}).get("StackObjectsCount", "n/a"),
				3: item.get("parentId", "n/a"),
				4: item.get("slotId", "n/a"),
				5: fir_check.isChecked(),
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

	def finalize(self, reward_type):
		ui = self.ui
		state = self.state
		match reward_type:
			case "Achievement":
				reward_timing = ui.box_rewardtiming_ach.currentText()
				reward = rewards.achievement(
					self.id,
					target=ui.fld_ach_id_ach.displayText(),
					unknown=is_true(ui.bx_unknown_ach.currentText()),
				)
			case "AssortmentUnlock":
				reward_timing = ui.box_rewardtiming_asu.currentText()
				local_items = state.get_multicolumn_values_list("RewardAssortmentUnlock")
				reward = rewards.assortment_unlock(
					self.id,
					items=local_items,
					loyalty_level=int(ui.box_loyalty_asu.cleanText()),
					target=(
						ui.fld_man_target_asu.displayText()
						if ui.chk_target_specify_asu.isChecked()
						else rewards.first_item_id(local_items)
					),
					trader_id=state.traders[ui.box_trader_asu.currentText()],
					unknown=is_true(ui.box_unknown_asu.currentText()),
				)
			case "Experience":
				reward_timing = ui.box_rewardtiming_exp.currentText()
				reward = rewards.experience(
					self.id,
					unknown=is_true(ui.box_unknown_exp.currentText()),
					value=int(ui.box_amount_exp.displayText()),
				)
			case "Item":
				reward_timing = ui.box_rewardtiming_item.currentText()
				local_items = state.get_multicolumn_values_list("RewardItem")
				reward = rewards.item(
					self.id,
					find_in_raid=is_true(ui.box_fir_item.currentText()),
					items=local_items,
					target=(
						ui.fld_man_target_it.displayText()
						if ui.chk_target_specify_it.isChecked()
						else rewards.first_item_id(local_items)
					),
					unknown=is_true(ui.box_unknown_item.currentText()),
					value=int(ui.box_value_item.cleanText()),
				)
			case "Skill":
				reward_timing = ui.box_rewardtiming_sk.currentText()
				reward = rewards.skill(
					self.id,
					target=ui.box_skill_sk.currentText(),
					unknown=is_true(ui.box_unknown_sk.currentText()),
					value=int(ui.box_points_sk.cleanText()),
				)
			case "StashRows":
				reward_timing = ui.box_rewardtiming_sr.currentText()
				reward = rewards.stash_rows(
					self.id,
					unknown=is_true(ui.box_unknown_sr.currentText()),
					value=int(ui.box_rows_sr.cleanText()),
				)
			case "TraderStanding":
				reward_timing = ui.box_rewardtiming_ts.currentText()
				reward = rewards.trader_standing(
					self.id,
					target=state.traders[ui.box_trader_ts.currentText()],
					unknown=is_true(ui.box_unknown_ts.currentText()),
					value=float(ui.box_loyalty_ts.cleanText()),
				)
			case "TraderUnlock":
				reward_timing = ui.box_rewardtiming_tul.currentText()
				reward = rewards.trader_unlock(
					self.id,
					target=state.traders[ui.box_trader_tul.currentText()],
					unknown=is_true(ui.box_unknown_tul.currentText()),
				)

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
