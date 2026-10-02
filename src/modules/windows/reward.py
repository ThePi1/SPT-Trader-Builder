import copy
import logging

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMainWindow

from modules.builders import rewards
from modules.gui.compiled.gui_rewards import Ui_rewardBuilder
from modules.state import TableFields
from modules.table_fields import add_table_field, remove_selected_table_item
from modules.utils import is_true, new_id
from modules.windows.common import select_id, select_or_add

log = logging.getLogger(__name__)

# The kinds of reward the dialog can make, and so can edit: the tab of each one, and the button that finishes it
REWARD_TABS = {
	"Experience": 0,
	"Item": 1,
	"AssortmentUnlock": 2,
	"TraderStanding": 3,
	"Skill": 4,
	"StashRows": 5,
	"Achievement": 6,
	"TraderUnlock": 7,
}
FINISH_BUTTONS = {
	"Experience": "pb_finalize_exp",
	"Item": "pb_finalize_item",
	"AssortmentUnlock": "pb_finalize_asu",
	"TraderStanding": "pb_finalize_ts",
	"Skill": "pb_finalize_sk",
	"StashRows": "pb_finalize_sr",
	"Achievement": "pb_finalize_ach",
	"TraderUnlock": "pb_finalize_tul",
}


def can_edit(reward):
	"""Whether the Reward Builder can open this reward (it can't, for kinds it can't make)."""
	return reward.get("type") in REWARD_TABS


def item_row(item):
	"""The columns of an item's row in the Item / Assort Unlock tables."""
	upd = item.get("upd", {})
	return {
		0: item["_id"],
		1: item["_tpl"],
		2: upd.get("StackObjectsCount", "n/a"),
		3: item.get("parentId", "n/a"),
		4: item.get("slotId", "n/a"),
		5: bool(upd.get("SpawnedInSession", False)),
	}


def whole_number(value):
	"""A reward's number as a whole number for a spin box (a number written as text works too)."""
	try:
		return int(float(value))
	except (TypeError, ValueError):
		return 0


class Gui_RewardDlg(QMainWindow):
	# (reward_timing, reward_type, reward_id, reward) - sent when the user finalizes a reward
	reward_ready = Signal(str, str, str, object)

	def __init__(self, state, parent=None, reward=None, timing=None):
		"""A new reward, or (if reward is given) an existing one to edit.

		reward is the reward dict and timing the list it is in (Success, Started or Fail). The dialog
		works on a copy: nothing changes until the reward is saved. ValueError if the reward is of a
		kind the dialog can't make.
		"""
		super().__init__(parent)
		if reward is not None and not can_edit(reward):
			raise ValueError(f"The Reward Builder can't edit rewards of type {reward.get('type')!r}")
		self.ui = Ui_rewardBuilder()
		self.ui.setupUi(self)
		self.state = state
		self.fields = TableFields()  # this dialog's own table rows
		self.original = copy.deepcopy(reward) if reward is not None else None  # None for a new reward
		self.trader_ids = dict(state.traders)  # name shown in the boxes -> id
		self.id = self.original["id"] if self.original is not None else new_id()
		self.on_launch()  # Custom code in this one
		if self.original is not None:
			self.load_reward(self.original, timing)
		self.show()
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
						ui.box_soc_item.value() if ui.chk_soc_item.isChecked() else None
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
						ui.box_soc_asu.value() if ui.chk_soc_asu.isChecked() else None
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
			self.fields,
			table_type,
			table,
			item["_id"],
			item_row(item),
			item,
		)

	def remove_selected_item(self, tab):
		match tab:
			case "AssortmentUnlock":
				remove_selected_table_item(
					self.fields,
					type="RewardAssortmentUnlock", table=self.ui.tb_asu_item, id_row=0
				)
			case "Item":
				remove_selected_table_item(
					self.fields,
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
				local_items = self.fields.get_multicolumn_values_list("RewardAssortmentUnlock")
				reward = rewards.assortment_unlock(
					self.id,
					items=local_items,
					loyalty_level=int(ui.box_loyalty_asu.cleanText()),
					target=(
						ui.fld_man_target_asu.displayText()
						if ui.chk_target_specify_asu.isChecked()
						else rewards.first_item_id(local_items)
					),
					trader_id=self.trader_ids[ui.box_trader_asu.currentText()],
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
				local_items = self.fields.get_multicolumn_values_list("RewardItem")
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
					target=self.trader_ids[ui.box_trader_ts.currentText()],
					unknown=is_true(ui.box_unknown_ts.currentText()),
					value=float(ui.box_loyalty_ts.cleanText()),
				)
			case "TraderUnlock":
				reward_timing = ui.box_rewardtiming_tul.currentText()
				reward = rewards.trader_unlock(
					self.id,
					target=self.trader_ids[ui.box_trader_tul.currentText()],
					unknown=is_true(ui.box_unknown_tul.currentText()),
				)

		if self.editing:
			reward = rewards.edited_reward(self.original, reward)
		self.reward_ready.emit(reward_timing, reward_type, self.id, reward)
		self.close()

	# --- editing an existing reward ---------------------------------------------------------

	@property
	def editing(self):
		"""Whether this dialog edits an existing reward (rather than making a new one)."""
		return self.original is not None

	def load_reward(self, reward, timing):
		"""Fill the form of the reward's kind from the reward, and leave only that kind's tab usable."""
		ui = self.ui
		kind = reward["type"]
		self.setWindowTitle("Edit Reward")
		for other, index in REWARD_TABS.items():
			ui.tabWidget.setTabEnabled(index, other == kind)
		ui.tabWidget.setCurrentIndex(REWARD_TABS[kind])
		getattr(ui, FINISH_BUTTONS[kind]).setText("Save Changes")
		getattr(self, f"load_{kind}")(reward, timing)

	def set_flag(self, box, value):
		select_or_add(box, str(bool(value)).lower())

	def load_target(self, reward, specify_check, specify_field):
		"""The reward's target is the first item's id unless one was typed in."""
		if reward.get("target", "") != rewards.first_item_id(reward.get("items")):
			specify_check.setChecked(True)
			specify_field.setText(str(reward.get("target", "")))

	def load_items(self, reward, table_type, table):
		for item in copy.deepcopy(reward.get("items", [])):
			add_table_field(self.fields, table_type, table, item["_id"], item_row(item), item)

	def load_Experience(self, reward, timing):
		ui = self.ui
		ui.box_amount_exp.setText(str(reward.get("value", 0)))
		self.set_flag(ui.box_unknown_exp, reward.get("unknown", False))
		select_or_add(ui.box_rewardtiming_exp, timing or "Success")

	def load_Item(self, reward, timing):
		ui = self.ui
		self.set_flag(ui.box_fir_item, reward.get("findInRaid", False))
		self.set_flag(ui.box_unknown_item, reward.get("unknown", False))
		ui.box_value_item.setValue(whole_number(reward.get("value", 0)))
		select_or_add(ui.box_rewardtiming_item, timing or "Success")
		self.load_items(reward, "RewardItem", ui.tb_item)
		self.load_target(reward, ui.chk_target_specify_it, ui.fld_man_target_it)

	def load_AssortmentUnlock(self, reward, timing):
		ui = self.ui
		ui.box_loyalty_asu.setValue(whole_number(reward.get("loyaltyLevel", 1)))
		select_id(ui.box_trader_asu, self.trader_ids, reward.get("traderId", ""))
		self.set_flag(ui.box_unknown_asu, reward.get("unknown", False))
		select_or_add(ui.box_rewardtiming_asu, timing or "Success")
		self.load_items(reward, "RewardAssortmentUnlock", ui.tb_asu_item)
		self.load_target(reward, ui.chk_target_specify_asu, ui.fld_man_target_asu)

	def load_TraderStanding(self, reward, timing):
		ui = self.ui
		select_id(ui.box_trader_ts, self.trader_ids, reward.get("target", ""))
		try:
			ui.box_loyalty_ts.setValue(float(reward.get("value", 0)))
		except (TypeError, ValueError):
			ui.box_loyalty_ts.setValue(0)
		self.set_flag(ui.box_unknown_ts, reward.get("unknown", False))
		select_or_add(ui.box_rewardtiming_ts, timing or "Success")

	def load_Skill(self, reward, timing):
		ui = self.ui
		select_or_add(ui.box_skill_sk, str(reward.get("target", "")))
		ui.box_points_sk.setValue(whole_number(reward.get("value", 0)))
		self.set_flag(ui.box_unknown_sk, reward.get("unknown", False))
		select_or_add(ui.box_rewardtiming_sk, timing or "Success")

	def load_StashRows(self, reward, timing):
		ui = self.ui
		ui.box_rows_sr.setValue(whole_number(reward.get("value", 0)))
		self.set_flag(ui.box_unknown_sr, reward.get("unknown", False))
		select_or_add(ui.box_rewardtiming_sr, timing or "Success")

	def load_Achievement(self, reward, timing):
		ui = self.ui
		ui.fld_ach_id_ach.setText(str(reward.get("target", "")))
		self.set_flag(ui.bx_unknown_ach, reward.get("unknown", False))
		select_or_add(ui.box_rewardtiming_ach, timing or "Success")

	def load_TraderUnlock(self, reward, timing):
		ui = self.ui
		select_id(ui.box_trader_tul, self.trader_ids, reward.get("target", ""))
		self.set_flag(ui.box_unknown_tul, reward.get("unknown", False))
		select_or_add(ui.box_rewardtiming_tul, timing or "Success")

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
