import logging

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMainWindow

from tb_ui.gui_quests import Ui_QuestWindow
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
		self.windows = []
		self.on_launch()  # Custom code in this one
		self.show()

	def on_launch(self):
		self.ui.pb_add_task.released.connect(self.open_task_window)
		self.ui.pb_rem_task.released.connect(
			lambda: remove_selected_table_item(
				self.state,
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
		self.state.safe_clear_table_fields()
		add_table_field(
			self.state,
			f"Condition{timing}",
			self.ui.tb_cond,
			cond_id,
			{0: cond_id, 1: timing, 2: cond_type},
			cond,
		)

	def add_reward(self, reward_timing, reward_type, reward_id, reward):
		self.state.safe_clear_table_fields()
		add_table_field(
			self.state,
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

	# def edit_selected_reward(self):
	#   tb_reward = self.ui.tb_rewards
	#   select = tb_reward.selectedItems()
	#   # if no reward selected, just skip
	#   if len(select) <= 0:
	#     return
	#   row = select[0].row()
	#   reward_id = tb_reward.item(row, 0).text()

	#   for type in ["Fail", "Started", "Success"]:
	#     if f"Reward{type}" in self.state.table_fields:
	#       for id in self.state.table_fields[f"Reward{type}"]:
	#         print(id)
	#         reward = self.state.table_fields[f"Reward{type}"][id]
	#         if id == reward_id:
	#           found_reward = reward
	#           break
	#   # create questbuilder window and load fields
	#   # dlg = Gui_RewardDlg(parent=self)
	#   dlg = self.state.spawnWindow("RewardBuilder", _parent=self)
	#   dlg.load_settings_from_dict(found_reward, type)

	def remove_selected_reward(self):
		remove_selected_table_item(
			self.state,
			type="RewardAny", table=self.ui.tb_rewards
		)
		log.debug(self.state.table_fields)

	# def load_settings_from_dict(self, settings):
	#   print(f"Loading settings from dict: {settings}")
	#   quest_id = settings["_id"]
	#   self.quest_id = quest_id
	#   # first field is the JSON key
	#   # tuple is (item reference to set, type of item reference (determines func to set))
	#   field_map = {
	#     "QuestName": (self.ui.fld_quest_name, "fld"),
	#     "_id": (None, "skip"),
	#     "canShowNotificationsInGame": (self.ui.box_can_show_notif, "box"),
	#     "conditions":(None, "conditions"),
	#     "image": (self.ui.fld_image_name, "fld"),
	#     "instantComplete": (self.ui.box_insta_complete, "box"),
	#     "location": (self.ui.box_location, "box"),
	#     "restartable": (self.ui.box_restartable, "box"),
	#     "rewards": (None, "rewards"),
	#     "secretQuest": (self.ui.box_secret_quest, "box"),
	#     "side": (self.ui.box_avail_faction, "box"),
	#     "traderId": (self.ui.box_trader, "traderid"),
	#     "type": (self.ui.box_quest_type_label, "box")
	#   }
	#   for k,v in settings.items():
	#     if k in field_map:
	#       set_obj = field_map[k][0]
	#       set_type = field_map[k][1]
	#       match set_type:
	#         case "skip":
	#           #print(f"Setting {k} to {v}, type skip")
	#           pass
	#         case "fld":
	#           #print(f"Setting {k} to {v}, type field")
	#           set_obj.setText(str(v))
	#         case "box":
	#           #print(f"Setting {k} to {v}, type box")
	#           set_obj.setCurrentText(str(v))
	#         case "traderid":
	#           #print(f"Setting {k} to {v}, type traderid")
	#           set_obj.setCurrentText(self.state.traders_invert[str(v)])
	#         case "rewards":
	#           print("Loading rewards...")
	#           local_rewards = copy.deepcopy(v) # copy it b/c pass by reference screws thing up here
	#           for type in ["Fail", "Started", "Success"]:
	#             for reward in local_rewards[type]:
	#               if f"Reward{type}" not in self.state.table_fields:
	#                 self.state.table_fields[f"Reward{type}"] = {}
	#               self.state.add_table_field(f"Reward{type}", self.ui.tb_rewards, reward['id'], {0: reward['id'], 1:type, 2:reward['type']}, reward)
	#           print("Done loading rewards!")
	#         case "conditions":
	#           print("Loading conditions...")
	#           local_conditions = copy.deepcopy(v)
	#           for type in ["Finish", "Start", "Fail"]:
	#             m = {"Finish":"AvailableForFinish", "Start":"AvailableForStart", "Fail":"Fail"}
	#             for cond in local_conditions[m[type]]:
	#               if f"Condition{type}" not in self.state.table_fields:
	#                 self.state.table_fields[f"Condition{type}"] = {}
	#               self.state.add_table_field(f"Condition{type}", self.ui.tb_cond, cond['id'], {0: cond['id'], 1:type, 2:cond['conditionType']}, cond)
	#           print("Done loading conditions!")
	#           pass
	#     else:
	#       print(f"Skipping {k}")

	# def edit_selected_task(self):
	#     breaknext = False
	#     tb_cond = self.ui.tb_cond
	#     select = tb_cond.selectedItems()
	#     # if no cond selected, just skip
	#     if len(select) <= 0:
	#       return
	#     row = select[0].row()
	#     cond_id = tb_cond.item(row, 0).text()

	#     for type in ["Finish", "Start", "Fail"]:
	#       if breaknext: break
	#       if f"Condition{type}" in self.state.table_fields:
	#         for id in self.state.table_fields[f"Condition{type}"]:
	#           if breaknext: break
	#           print(id)
	#           cond = self.state.table_fields[f"Condition{type}"][id]
	#           if id == cond_id:
	#             print(f"Editing task: found id {id} under type {type}.")
	#             found_reward = cond
	#             breaknext = True

	#     # create questbuilder window and load fields
	#     dlg = self.state.spawnWindow("TaskBuilder", _parent=self)
	#     dlg.load_settings_from_dict(found_reward, type)

	def finalize(self):
		quest_id = self.quest_id
		rewards_calc = {"Fail": [], "Started": [], "Success": []}
		for k, v in rewards_calc.items():
			if f"Reward{k}" in self.state.table_fields:
				for _id, reward in self.state.table_fields[f"Reward{k}"].items():
					rewards_calc[k].append(reward)
					# print(_id, reward)
		location_calc = (
			"any"
			if self.ui.box_location.currentText() == "any"
			else self.state.locations[self.ui.box_location.currentText()]
		)
		quest = {
			quest_id: {
				"QuestName": self.ui.fld_quest_name.displayText(),
				"_id": quest_id,
				"acceptPlayerMessage": quest_id + " acceptPlayerMessage",
				"acceptanceAndFinishingSource": "eft",
				"arenaLocations": [],
				"canShowNotificationsInGame": is_true(
					self.ui.box_can_show_notif.currentText()
				),
				"changeQuestMessageText": quest_id + " changeQuestMessageText",
				"completePlayerMessage": quest_id + " completePlayerMessage",
				"conditions": {
					"AvailableForFinish": self.state.get_multicolumn_values_list(
						"ConditionFinish"
					),  # ConditionFinish
					"AvailableForStart": self.state.get_multicolumn_values_list(
						"ConditionStart"
					),  # ConditionStart
					"Fail": self.state.get_multicolumn_values_list(
						"ConditionFail"
					),  # ConditionFail
				},
				"declinePlayerMessage": quest_id + " declinePlayerMessage",
				"description": quest_id + " description",
				"failMessageText": quest_id + " failMessageText",
				"image": self.ui.fld_image_name.displayText(),
				"instantComplete": is_true(self.ui.box_insta_complete.currentText()),
				"isKey": False,
				"location": location_calc,
				"name": quest_id + " name",
				"note": quest_id + " note",
				"progressSource": "eft",
				"rankingModes": [],
				"restartable": is_true(self.ui.box_restartable.currentText()),
				"rewards": rewards_calc,
				"secretQuest": is_true(self.ui.box_secret_quest.currentText()),
				"side": self.ui.box_avail_faction.currentText(),
				"startedMessageText": quest_id + " startedMessageText",
				"successMessageText": quest_id + " successMessageText",
				"traderId": self.state.traders[self.ui.box_trader.currentText()],
				"type": self.ui.box_quest_type_label.currentText(),
			}
		}
		log.info(f"Added quest: {self.ui.fld_quest_name.displayText()}, id: {quest_id}")
		# may or may not be already in (if it was edited, it is)
		# if quest_id in self.state.quests:
		#   old_quest = self.state.quests.pop(quest_id)
		# for i in range(self.state.ui.questList.count()):
		#   if str(quest_id) in self.state.ui.questList.item(i).text():
		#     self.state.ui.questList.takeItem(i)
		#     break

		self.quest_saved.emit(
			quest_id, self.ui.fld_quest_name.displayText(), quest[quest_id]
		)
		self.close()
