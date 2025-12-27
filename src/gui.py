import sys
import re
import json
from pymongo import MongoClient
from bson.objectid import ObjectId

from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import Qt, QRunnable
from PyQt6.QtWidgets import QApplication, QDialog, QFileDialog, QMainWindow, QPushButton, QListView, QListWidget, QListWidgetItem

from gui_about import Ui_AboutMenu
from gui_main import Ui_MainGUI
from gui_updates import Ui_UpdateMenu
from gui_quests import Ui_QuestWindow
from gui_tasks import Ui_TaskWindow
from gui_assort import Ui_AssortBuilder
from gui_rewards import Ui_rewardBuilder

class Gui_MainWindow(QMainWindow):
  def __init__(self, parent=None):
    super().__init__(parent)
    self.ui = Ui_MainGUI()
    self.ui.setupUi(self)
    self.controller = None
    self.parent = parent
    self.ui.actionExit.triggered.connect(self.onExit)
    self.ui.actionExport_Queued_Quests.triggered.connect(self.onExportQuests)
    self.ui.actionEdit_Selected_Quest.triggered.connect(self.editSelectedQuest)
    self.ui.actionImport_Quests.triggered.connect(self.importQuests)
    self.traders = self.importJson("data\\traders.json")
    # used for going back from ID to trader name for loading quest to edit
    self.traders_invert = {v:k for k,v in self.traders.items()}
    self.weapons = self.importJson("data\weapons.json")
    self.quests = {}

  def importJson(self, path):
    with open(path, "r") as f:
      out = json.load(f)
      return out
  
  def importQuests(self):
    filename, ok = QFileDialog.getOpenFileName(self, "Import Quest JSON")
    print(filename)
    with open(filename, "r") as f:
      try:
        quests_import = json.load(f)
      except Exception as e:
        print(f"Error loading quest file: {e}")
      for quest_id in quests_import.keys():
        print(f"Found quest {quests_import[quest_id]['QuestName']} ({quest_id})")
        self.quests[quest_id] = quests_import[quest_id]
        self.ui.questList.addItem(f"{quests_import[quest_id]['QuestName']}, {quest_id}")

  def editSelectedQuest(self):
    qlist = self.ui.questList
    select = qlist.selectedItems()
    # if no quest selected, just skip
    if len(select) <= 0:
      return
    quest_text = select[0].text()

    # hacky but easier than setting up a bunch of tables in qt6
    quest_id = quest_text.split(" ")[-1]
    # remove the quest-to-be-edited from the lists; we will regenerate it later
    quest = self.quests[quest_id]
    # create questbuilder window and load fields
    dlg = Gui_QuestDlg(parent=self)
    dlg.load_settings_from_dict(quest)

  def onAbout(self, ver_current, url_text):
    dlg = Gui_AboutDlg(self)
    dlg.updateAbout(ver_current, url_text)
    dlg.exec()

  def popup(self, message):
    dlg = Gui_AboutDlg(self)
    text = dlg.ui.label.text()
    text = message
    dlg.ui.label.setText(QtCore.QCoreApplication.translate("AboutMenu", text))
    dlg.exec()

  def onExportQuests(self):
    self.exportAll(self.quests)

  def onExit(self):
    sys.exit(0)

  def onUpdateWindow(self, ver_current, ver_latest, url_text, update_text):
    dlg = Gui_UpdatesDlg()
    dlg.updateVersion(ver_current, ver_latest, url_text, update_text)
    dlg.exec()

  def onQuestWindow(self):
     dlg = Gui_QuestDlg(parent=self)
  
  def onAssortWindow(self):
     dlg = Gui_AssortDlg(parent=self)

  def exportAll(self, quest):
    filename, ok = QFileDialog.getSaveFileName(self, "Export Quest JSON")
    with open(filename, 'w') as f:
      try:
        out = json.dumps(quest, indent=4).strip('[]\n')
        f.write(out)
        f.close()
        self.popup(message=f"The export has completed successfully and can be found at {filename}.")
      except Exception as e:
        print(f"Error: {e}")
        self.popup(message=f"An error has occurred while exporting the final JSON file.")
      finally:
        f.close()
class Gui_AboutDlg(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_AboutMenu()
        self.ui.setupUi(self)
        self.parent = parent

    def updateAbout(self, ver_current, url_text):
      text =  self.ui.label.text()
      text = re.sub('V_CUR', ver_current, text)
      text = re.sub('SRC_URL', url_text ,text)
      self.ui.label.setText(QtCore.QCoreApplication.translate("AboutMenu", text))

class Gui_UpdatesDlg(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_UpdateMenu()
        self.ui.setupUi(self)
        self.parent = parent

    def updateVersion(self, ver_current, ver_latest, url_text, update_text):
      text =  self.ui.label.text()
      text = re.sub('V_CUR', ver_current, text)
      text = re.sub('V_LAT', ver_latest, text)
      text = re.sub('UPDATE_TEXT', update_text ,text)
      text = re.sub('SRC_URL', url_text, text)
      self.ui.label.setText(QtCore.QCoreApplication.translate("UpdateMenu", text))

class Gui_RewardDlg(QMainWindow):
  def __init__(self, parent=None, _controller=None):
    super().__init__(parent)
    self.ui = Ui_rewardBuilder()
    self.ui.setupUi(self)
    self.parent = parent
    self.on_launch() # Custom code in this one
    self.show()
  
  def on_launch(self):
    self.setup_box_selections()
    self.setup_buttons()

  def finalize(self, reward_type):
    reward_id = str(ObjectId())
    match reward_type:
      case "achievement":
        reward_timing = self.ui.box_rewardtiming_ach.currentText()
        reward = {
          "availableInGameEditions": [],
          "id": reward_id,
          "index": 0,
          "target": self.ui.fld_ach_id_ach.displayText(),
          "type": "Achievement",
          "unknown": self.ui.bx_unknown_ach.currentText()
        }
      case "assortunlock":
        reward_timing = self.ui.box_rewardtiming_asu.currentText()
        reward = {
          "availableInGameEditions": [],
          "id": reward_id,
          "index": 0,
          "items": [],# todo: add item list logic
          "loyaltyLevel": self.ui.box_loyalty_asu.currentText(),
          "target": self.ui.fld_tid_asu.displayText(),
          "traderId": self.ui.fld_traderid_asu.displayText(),
          "type": "AssortmentUnlock",
          "unknown": self.ui.box_unknown_asu.currentText()
        }
      case "experience":
        reward_timing = self.ui.box_rewardtiming_exp.currentText()
      case "item":
        reward_timing = self.ui.box_rewardtiming_item.currentText()
      case "skills":
        reward_timing = self.ui.box_rewardtiming_sk.currentText()
      case "stashrows":
        reward_timing = self.ui.box_rewardtiming_sr.currentText()
      case "traderstanding":
        reward_timing = self.ui.box_rewardtiming_ts.currentText()

  def setup_buttons(self):
    self.ui.pb_finalize_ach.released.connect(lambda: self.finalize("achievement"))
    self.ui.pb_finalize_asu.released.connect(lambda: self.finalize("assortunlock"))
    self.ui.pb_finalize_exp.released.connect(lambda: self.finalize("experience"))
    self.ui.pb_finalize_item.released.connect(lambda: self.finalize("item"))
    self.ui.pb_finalize_sk.released.connect(lambda: self.finalize("skills"))
    self.ui.pb_finalize_sr.released.connect(lambda: self.finalize("stashrows"))
    self.ui.pb_finalize_ts.released.connect(lambda: self.finalize("traderstanding"))
    pass

  def setup_box_selections(self):
    self.ui.box_unknown_exp.addItems(self.parent.parent.controller.default_tf)
    self.ui.box_rewardtiming_exp.addItems(self.parent.parent.controller.reward_timing)
    self.ui.box_fir_item.addItems(self.parent.parent.controller.default_tf)
    self.ui.box_unknown_item.addItems(self.parent.parent.controller.default_tf)
    self.ui.box_rewardtiming_item.addItems(self.parent.parent.controller.reward_timing)
    self.ui.box_unknown_asu.addItems(self.parent.parent.controller.default_tf)
    self.ui.box_rewardtiming_asu.addItems(self.parent.parent.controller.reward_timing)
    self.ui.box_unknown_ts.addItems(self.parent.parent.controller.default_tf)
    self.ui.box_rewardtiming_ts.addItems(self.parent.parent.controller.reward_timing)
    self.ui.box_skill_sk.addItems(self.parent.parent.controller.default_skills)
    self.ui.box_unknown_sk.addItems(self.parent.parent.controller.default_tf)
    self.ui.box_rewardtiming_sk.addItems(self.parent.parent.controller.reward_timing)
    self.ui.box_rewardtiming_sr.addItems(self.parent.parent.controller.reward_timing)
    self.ui.box_unknown_sr.addItems(self.parent.parent.controller.default_tf)
    self.ui.bx_unknown_ach.addItems(self.parent.parent.controller.default_tf)
    self.ui.box_rewardtiming_ach.addItems(self.parent.parent.controller.reward_timing)

class Gui_QuestDlg(QMainWindow):
  def __init__(self, parent=None, _controller=None):
    super().__init__(parent)
    self.ui = Ui_QuestWindow()
    self.ui.setupUi(self)
    self.parent = parent
    self.rewards = {
      "Fail": [],
      "Started": [],
      "Success": []
    }
    self.on_launch() # Custom code in this one
    self.show()
  
  def on_launch(self):
    self.ui.pb_add_task.released.connect(lambda: Gui_TaskDlg(parent=self))
    self.ui.pb_finalize_quest.released.connect(self.finalize)
    self.ui.pb_add_reward.released.connect(lambda: Gui_RewardDlg(parent=self))
    self.setup_box_selections()
    self.setup_text_edit()
    # can be edited later if needed
    self.quest_id = str(ObjectId())

  def setup_box_selections(self):
    self.ui.box_avail_faction.addItems(self.parent.controller.qb_box_avail_faction)
    self.ui.box_quest_type_label.addItems(self.parent.controller.qb_box_quest_type_label)
    self.ui.box_trader.addItems(self.parent.traders.keys())
    self.ui.box_location.addItems(self.parent.controller.qb_box_location)
    self.ui.box_can_show_notif.addItems(self.parent.controller.default_tf)
    self.ui.box_insta_complete.addItems(self.parent.controller.default_ft)
    self.ui.box_restartable.addItems(self.parent.controller.default_ft)
    self.ui.box_secret_quest.addItems(self.parent.controller.default_ft)
  
  def setup_text_edit(self):
    self.ui.qb_locale_box.setPlainText(self.parent.controller.default_locale)

  def load_settings_from_dict(self, settings):
    print(f"Loading settings from dict: {settings}")
    quest_id = settings["_id"]
    self.quest_id = quest_id
    # first field is the JSON key
    # tuple is (item reference to set, type of item reference (determines func to set))
    field_map = {
      "QuestName": (self.ui.fld_quest_name, "fld"),
      "_id": (None, "skip"),
      "canShowNotificationsInGame": (self.ui.box_can_show_notif, "box"),
      # do conditions later
      "conditions":(None, "skip"),
      "image": (self.ui.fld_image_name, "fld"),
      "instantComplete": (self.ui.box_insta_complete, "box"),
      "location": (self.ui.box_location, "box"),
      "restartable": (self.ui.box_restartable, "box"),
      # do rewards later
      "rewards": (None, "skip"),
      "secretQuest": (self.ui.box_secret_quest, "box"),
      "side": (self.ui.box_avail_faction, "box"),
      "traderId": (self.ui.box_trader, "traderid"),
      "type": (self.ui.box_quest_type_label, "box")
    }
    for k,v in settings.items():
      if k in field_map:
        set_obj = field_map[k][0]
        set_type = field_map[k][1]
        match set_type:
          case "skip":
            #print(f"Setting {k} to {v}, type skip")
            pass
          case "fld":
            #print(f"Setting {k} to {v}, type field")
            set_obj.setText(str(v))
          case "box":
            #print(f"Setting {k} to {v}, type box")
            set_obj.setCurrentText(str(v))
          case "traderid":
            #print(f"Setting {k} to {v}, type traderid")
            set_obj.setCurrentText(self.parent.traders_invert[str(v)])
      else:
        print(f"Skipping {k}")

  def finalize(self):
    quest_id = self.quest_id
    quest = {
      quest_id: {
      "QuestName": self.ui.fld_quest_name.displayText(),
      "_id": quest_id,
      "acceptPlayerMessage": quest_id + " acceptPlayerMessage",
      "canShowNotificationsInGame": self.ui.box_can_show_notif.currentText(),
      "changeQuestMessageText": quest_id + " changeQuestMessageText",
      "completePlayerMessage": quest_id + " completePlayerMessage",
      "conditions":{
        "AvailableForFinish":[],#add task lists
        "AvailableForStart":[],
        "Fail":[]
      },
      "declinePlayerMessage": quest_id + " declinePlayerMessage",
      "description": quest_id + " description",
      "failMessageText": quest_id + " failMessageText",
      "image": self.ui.fld_image_name.displayText(),
      "instantComplete": self.ui.box_insta_complete.currentText(),
      "isKey": "false",
      "location": self.ui.box_location.currentText(),
      "name": quest_id + " name",
      "note": quest_id + " note",
      "restartable": self.ui.box_restartable.currentText(),
      "rewards": {
        "Fail": [],#add reward lists
        "Started": [],
        "Success": [],
      },
      "secretQuest": self.ui.box_secret_quest.currentText(),
      "side": self.ui.box_avail_faction.currentText(),
      "startedMessageText": quest_id + " startedMessageText",
      "successMessageText": quest_id + " successMessageText",
      "traderId": self.parent.traders[self.ui.box_trader.currentText()],
      "type": self.ui.box_quest_type_label.currentText()
      }
    }
    print(f"Added quest: {quest}")
    # may or may not be already in (if it was edited, it is)
    if quest_id in self.parent.quests:
      old_quest = self.parent.quests.pop(quest_id)
    for i in range(self.parent.ui.questList.count()):
      if str(quest_id) in self.parent.ui.questList.item(i).text():
        self.parent.ui.questList.takeItem(i)
        break

    self.parent.quests[quest_id] = quest[quest_id]
    self.parent.ui.questList.addItem(f"{self.ui.fld_quest_name.displayText()}, {quest_id}")
    self.close()

class Gui_AssortDlg(QMainWindow):
  def __init__(self, parent=None,):
    super().__init__(parent)
    self.ui = Ui_AssortBuilder()
    self.ui.setupUi(self)
    self.parent = parent
    self.on_launch() #custom Code
    self.show()

  def on_launch(self):
     self.setup_box_selections()

  def setup_box_selections(self):
    self.ui.ab_loyalty_combo.addItems(self.parent.controller.ab_box_loyalty_level)

class Gui_TaskDlg(QMainWindow):
  def __init__(self, parent=None):
    super().__init__(parent)
    self.ui = Ui_TaskWindow()
    self.ui.setupUi(self)
    self.parent = parent
    self.on_launch() # Custom code in this one
    self.show()
  
  def on_launch(self):
     self.setup_box_selections()
     self.setup_text_edit()

  def setup_box_selections(self):
    self.ui.box_target.addItems(self.parent.parent.controller.tb_elim_box_target)
    self.ui.box_targetrole.addItems(self.parent.parent.controller.tb_elim_box_targetrole)
    self.ui.box_bodypart.addItems(self.parent.parent.controller.tb_elim_box_bodypart)
    self.ui.box_dist_compare.addItems(self.parent.parent.controller.tb_elim_box_dist_compare)
    self.ui.box_weapons.addItems(self.parent.parent.weapons.keys())
    self.ui.box_cond_type.addItems(self.parent.parent.controller.tb_handover_box_cond_type)
    self.ui.box_only_fir.addItems(self.parent.parent.controller.default_tf)
    self.ui.box_one_session.addItems(self.parent.parent.controller.default_tf)
    self.ui.box_fir.addItems(self.parent.parent.controller.default_tf)
    self.ui.traderloyalty_compare_box.addItems(self.parent.parent.controller.tb_traderloyalty_compare_box)
    self.ui.traderloyalt_target_box.addItems(self.parent.parent.controller.tb_traderloyalt_target_box)
    self.ui.traderloyalty_level.addItems(self.parent.parent.controller.tb_traderloyalty_level)
    self.ui.skillreq_compare_box.addItems(self.parent.parent.controller.tb_skillreq_compare_box)
    self.ui.skillreq_target_box.addItems(self.parent.parent.controller.default_skills)
    self.ui.exitstatus_status_box.addItems(self.parent.parent.controller.tb_exitstatus_status_box)
    self.ui.exitstatus_name_box.addItems(self.parent.parent.controller.tb_exitstatus_name_box)

  def setup_text_edit(self):
    self.ui.elim_locale_box.setPlainText(self.parent.parent.controller.default_locale)
    self.ui.handover_locale_box.setPlainText(self.parent.parent.controller.default_locale)
    self.ui.visitzone_locale_box.setPlainText(self.parent.parent.controller.default_locale)
    self.ui.leaveitem_locale_box.setPlainText(self.parent.parent.controller.default_locale)
    self.ui.leaveitem_locale_box.setPlainText(self.parent.parent.controller.default_locale)
    self.ui.traderloyalty_locale_box.setPlainText(self.parent.parent.controller.default_locale)
    self.ui.skillreq_locale_box.setPlainText(self.parent.parent.controller.default_locale)
    self.ui.exitstatus_locale_box.setPlainText(self.parent.parent.controller.default_locale)