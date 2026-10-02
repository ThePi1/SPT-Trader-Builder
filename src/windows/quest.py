import logging

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMainWindow

from builders import quests
from tb_ui.gui_quests import Ui_QuestWindow
from state import TableFields
from table_fields import add_table_field, remove_selected_table_item
from utils import is_true, new_id
from windows.reward import Gui_RewardDlg
from windows.task import Gui_TaskDlg

log = logging.getLogger(__name__)


class Gui_QuestDlg(QMainWindow):
	# (quest_id, quest_name, quest) - sent when the user finalizes the quest
	quest_saved = Signal(str, str, object)

	def __init__(self, state, parent=None):
		super().__init__(parent)
		self.ui = Ui_QuestWindow()
		self.ui.setupUi(self)
		self.state = state
		self.fields = TableFields()  # this quest's conditions and rewards
		self.windows = []
		self.on_launch()  # Custom code in this one
		self.show()

	def on_launch(self):
		self.ui.pb_add_task.released.connect(self.open_task_window)
		self.ui.pb_rem_task.released.connect(
			lambda: remove_selected_table_item(
				self.fields,
				type="ConditionAny", table=self.ui.tb_cond
			)
		)
		self.ui.pb_finalize_quest.released.connect(self.finalize)
		self.ui.pb_add_reward.released.connect(self.open_reward_window)
		self.ui.pb_remove_reward.released.connect(self.remove_selected_reward)
		self.setup_box_selections()
		self.setup_text_edit()
		# can be edited later if needed
		self.quest_id = new_id()

	def open_task_window(self):
		dlg = Gui_TaskDlg(self.state, parent=self)
		dlg.condition_ready.connect(self.add_condition)
		self.windows.append(dlg)
		return dlg

	def open_reward_window(self):
		dlg = Gui_RewardDlg(self.state, parent=self)
		dlg.reward_ready.connect(self.add_reward)
		self.windows.append(dlg)
		return dlg

	def add_condition(self, timing, cond_type, cond_id, cond):
		add_table_field(
			self.fields,
			f"Condition{timing}",
			self.ui.tb_cond,
			cond_id,
			{0: cond_id, 1: timing, 2: cond_type},
			cond,
		)

	def add_reward(self, reward_timing, reward_type, reward_id, reward):
		add_table_field(
			self.fields,
			f"Reward{reward_timing}",
			self.ui.tb_rewards,
			reward_id,
			{0: reward_id, 1: reward_timing, 2: reward_type},
			reward,
		)

	def setup_box_selections(self):
		self.ui.box_avail_faction.addItems(self.state.config.qb_box_avail_faction)
		self.ui.box_quest_type_label.addItems(
			self.state.config.qb_box_quest_type_label
		)
		self.ui.box_trader.addItems(self.state.traders.keys())
		self.ui.box_location.addItems(self.state.config.qb_box_location)
		self.ui.fld_image_name.setText(self.state.config.default_questicon)
		self.ui.box_can_show_notif.addItems(self.state.config.default_tf)
		self.ui.box_insta_complete.addItems(self.state.config.default_ft)
		self.ui.box_restartable.addItems(self.state.config.default_ft)
		self.ui.box_secret_quest.addItems(self.state.config.default_ft)

	def setup_text_edit(self):
		pass

	def remove_selected_reward(self):
		remove_selected_table_item(
			self.fields,
			type="RewardAny", table=self.ui.tb_rewards
		)
		log.debug(self.fields.data)

	def finalize(self):
		ui = self.ui
		state = self.state
		quest_id = self.quest_id
		quest_name = ui.fld_quest_name.displayText()
		location = (
			"any"
			if ui.box_location.currentText() == "any"
			else state.locations[ui.box_location.currentText()]
		)
		quest = quests.quest(
			quest_id,
			name=quest_name,
			can_show_notifications=is_true(ui.box_can_show_notif.currentText()),
			finish_conditions=self.fields.get_multicolumn_values_list("ConditionFinish"),
			start_conditions=self.fields.get_multicolumn_values_list("ConditionStart"),
			fail_conditions=self.fields.get_multicolumn_values_list("ConditionFail"),
			image=ui.fld_image_name.displayText(),
			instant_complete=is_true(ui.box_insta_complete.currentText()),
			location=location,
			restartable=is_true(ui.box_restartable.currentText()),
			rewards={
				timing: self.fields.get_multicolumn_values_list(f"Reward{timing}")
				for timing in ("Fail", "Started", "Success")
			},
			secret_quest=is_true(ui.box_secret_quest.currentText()),
			side=ui.box_avail_faction.currentText(),
			trader_id=state.traders[ui.box_trader.currentText()],
			quest_type=ui.box_quest_type_label.currentText(),
		)
		log.info(f"Added quest: {quest_name}, id: {quest_id}")
		self.quest_saved.emit(quest_id, quest_name, quest)
		self.close()
