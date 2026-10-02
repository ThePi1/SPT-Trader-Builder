import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHeaderView, QMainWindow, QPlainTextEdit, QTableWidgetItem

from modules.builders import locale as locale_builders
from modules.builders import quests
from modules.builders.quests import LOCALE_FIELDS
from modules.gui.compiled.gui_quests import Ui_QuestWindow
from modules.state import TableFields
from modules.table_fields import add_table_field, find_row, remove_selected_table_item
from modules.utils import is_true, new_id
from modules.windows.reward import Gui_RewardDlg
from modules.windows.task import Gui_TaskDlg

log = logging.getLogger(__name__)

# The Locale tab's task table: id, timing, type, and the task's text (the only column that can be edited)
TASK_TEXT_COLUMN = 3


class Gui_QuestDlg(QMainWindow):
	# (quest_id, quest_name, quest, locale) - sent when the user finalizes the quest.
	# locale is the quest's locale entries from the Locale tab, {key: text} (blank if left empty).
	quest_saved = Signal(str, str, object, object)

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
		self.ui.pb_rem_task.released.connect(self.remove_selected_task)
		self.ui.pb_finalize_quest.released.connect(self.finalize)
		self.ui.pb_add_reward.released.connect(self.open_reward_window)
		self.ui.pb_remove_reward.released.connect(self.remove_selected_reward)
		self.setup_box_selections()
		self.setup_text_edit()
		# can be edited later if needed
		self.quest_id = new_id()
		self.setup_locale_tab()

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
		self.add_task_text_row(cond_id, timing, cond_type)

	def remove_selected_task(self):
		"""Remove the task selected in the Tasks table, and its row on the Locale tab."""
		selected = self.ui.tb_cond.selectedItems()
		if not selected:
			return
		cond_id = self.ui.tb_cond.item(selected[0].row(), 0).text()
		remove_selected_table_item(self.fields, type="ConditionAny", table=self.ui.tb_cond)
		row = find_row(self.ui.tb_cond_locale, cond_id)
		if row is not None:
			self.ui.tb_cond_locale.removeRow(row)

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

	# --- the Locale tab ----------------------------------------------------------------

	def setup_locale_tab(self):
		for field in LOCALE_FIELDS:
			self.locale_field(field).setToolTip(f'Saved in the locale as "{self.quest_id} {field}"')
		header = self.ui.tb_cond_locale.horizontalHeader()
		for col in range(TASK_TEXT_COLUMN):
			header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

	def locale_field(self, field):
		"""The Locale tab's box for one of LOCALE_FIELDS."""
		return getattr(self.ui, f"fld_loc_{field}")

	def locale_text(self, field):
		box = self.locale_field(field)
		return box.toPlainText() if isinstance(box, QPlainTextEdit) else box.text()

	def add_task_text_row(self, cond_id, timing, cond_type):
		"""Give a task a row on the Locale tab, or update its row (keeping its text)."""
		table = self.ui.tb_cond_locale
		row = find_row(table, cond_id)
		if row is None:
			row = table.rowCount()
			table.insertRow(row)
			table.setItem(row, TASK_TEXT_COLUMN, QTableWidgetItem(""))
		for col, value in enumerate((cond_id, timing, cond_type)):
			item = QTableWidgetItem(value)
			item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
			table.setItem(row, col, item)

	def task_texts(self):
		"""Each task's text from the Locale tab, by condition id."""
		table = self.ui.tb_cond_locale
		return {
			table.item(row, 0).text(): table.item(row, TASK_TEXT_COLUMN).text()
			for row in range(table.rowCount())
		}

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
		locale = locale_builders.quest_locale(
			quest_id,
			{field: self.locale_text(field) for field in LOCALE_FIELDS},
			self.task_texts(),
		)
		log.info(f"Added quest: {quest_name}, id: {quest_id}")
		self.quest_saved.emit(quest_id, quest_name, quest, locale)
		self.close()
