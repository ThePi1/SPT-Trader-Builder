import sys
import re
import json
import copy
from pymongo import MongoClient
from bson.objectid import ObjectId

from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import Qt, QRunnable
from PyQt6.QtWidgets import QApplication, QDialog, QHeaderView, QAbstractScrollArea, QFileDialog, QMainWindow, QPushButton, QListView, QListWidget, QListWidgetItem, QTableWidgetItem

from gui_about import Ui_AboutMenu
from gui_main import Ui_MainGUI
from gui_updates import Ui_UpdateMenu
from gui_quests import Ui_QuestWindow
from gui_tasks import Ui_TaskWindow
from gui_assort import Ui_AssortBuilder
from gui_rewards import Ui_rewardBuilder

# oops copy paste sue me, should replace boxes w/ checkbox
def is_true(val):
  val = val.lower()
  if val in ('y', 'yes', 't', 'true', 'on', '1'):
    return True
  elif val in ('n', 'no', 'f', 'false', 'off', '0'):
    return False
  else:
    raise ValueError("invalid truth value %r" % (val,))
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
    self.ui.actionRemove_Selected_Quest.triggered.connect(self.remove_selected_quest)
    self.traders = self.importJson("data\\traders.json")
    # used for going back from ID to trader name for loading quest to edit
    self.traders_invert = {v:k for k,v in self.traders.items()}
    self.weapons = self.importJson("data\weapons.json")
    self.locations = self.importJson("data\locations.json")
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
    quest = self.quests[quest_id]
    # create questbuilder window and load fields
    dlg = Gui_QuestDlg(parent=self)
    dlg.load_settings_from_dict(quest)

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
    if quest_id in self.quests:
      old_quest = self.quests.pop(quest_id)
    for i in range(self.ui.questList.count()):
      if str(quest_id) in self.ui.questList.item(i).text():
        self.ui.questList.takeItem(i)
        break

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
    self.id = str(ObjectId())
    self.items_item = []
    self.items_asu = []
  
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
          "_id": self.ui.fld_uid_item.displayText(),
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
        self.items_item.append(item)
        self.ui.list_items_item.addItem(f"_id: {item['_id']}, _tpl: {item['_tpl']}, SOC: {item['upd']['StackObjectsCount'] if has_soc else 'n/a'}, parentId: {item['parentId'] if has_pid else 'n/a'}, slotId: {item['slotId'] if has_sid else 'n/a'}, fir: {self.ui.chk_fir_item.isChecked()}")

      case "AssortmentUnlock":
        item = {
          "_id": self.ui.fld_uid_asu.displayText(),
          "_tpl": self.ui.fld_utpl_asu.displayText(),
        }
        if self.ui.chk_soc_asu.isChecked() or self.ui.chk_fir_asu.isChecked():
          item["upd"] = {}
        if self.ui.chk_soc_asu.isChecked():
          item["upd"]["StackObjectsCount"] = int(self.ui.box_soc_asu.cleanText())
          has_soc = True
        if self.ui.chk_fir_asu.isChecked():
          item["upd"]["SpawnedInSession"] = self.ui.chk_fir_asu.isChecked()
        if self.ui.chk_parentid_asu.isChecked():
          item["parentId"] = self.ui.box_parentid_asu.displayText()
          has_pid = True
        if self.ui.chk_slotid_asu.isChecked():
          item["slotId"] = self.ui.box_slotid_asu.displayText()
          has_sid = True

        self.items_asu.append(item)
        self.ui.list_items_asu.addItem(f"_id: {item['_id']}, _tpl: {item['_tpl']}, SOC: {item['upd']['StackObjectsCount'] if has_soc else 'n/a'}, fir: {self.ui.chk_fir_asu.isChecked()}")


  def remove_selected_item(self, tab):
    match tab:
      case "AssortmentUnlock":
        gui_items = self.ui.list_items_asu
        internal_items = self.items_asu
      case "Item":
        gui_items = self.ui.list_items_item
        internal_items = self.items_item

    select = gui_items.selectedItems()
    # if no reward selected, just skip
    if len(select) <= 0:
      return
    item_text = select[0].text()

    # really hacky but easier than setting up a bunch of tables in qt6
    item_id = item_text.split(',')[0].strip('_id: ')
    for item in internal_items:
      if item['_id'] == item_id:
        internal_items.remove(item)
        break
    
    for i in range(gui_items.count()):
      if str(item_id) in gui_items.item(i).text():
        gui_items.takeItem(i)
        break

  def load_selected_item_to_fields(self, tab):
    # TODO: implement
    print("Skipping, not yet implemented")
    match tab:
      case "AssortmentUnlock":
        pass
      case "Item":
        pass

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
          "unknown": is_true(self.ui.bx_unknown_ach.currentText())
        }
      case "AssortmentUnlock":
        reward_timing = self.ui.box_rewardtiming_asu.currentText()
        reward = {
          "availableInGameEditions": [],
          "id": self.id,
          "index": 0,
          "items": self.items_asu,
          "loyaltyLevel": int(self.ui.box_loyalty_asu.cleanText()),
          "target": self.ui.fld_tid_asu.displayText(),
          "traderId": self.parent.parent.traders[self.ui.box_trader_asu.currentText()],
          "type": "AssortmentUnlock",
          "unknown": is_true(self.ui.box_unknown_asu.currentText())
        }
      case "Experience":
        reward_timing = self.ui.box_rewardtiming_exp.currentText()
        reward = {
          "availableInGameEditions": [],
          "id": self.id,
          "index": 0,
          "type": "Experience",
          "unknown": is_true(self.ui.box_unknown_exp.currentText()),
          "value": int(self.ui.box_amount_exp.displayText())
        }
      case "Item":
        reward_timing = self.ui.box_rewardtiming_item.currentText()
        reward = {
          "availableInGameEditions": [],
          "findInRaid": is_true(self.ui.box_fir_item.currentText()),
          "id": self.id,
          "index": 0,
          "items": self.items_item,
          "target": self.ui.fld_tid_item.displayText(),
          "type": "Item",
          "unknown": is_true(self.ui.box_unknown_item.currentText()),
          "value": int(self.ui.box_value_item.cleanText())
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
          "value": int(self.ui.box_points_sk.cleanText())
        }
      case "StashRows":
        reward_timing = self.ui.box_rewardtiming_sr.currentText()
        reward = {
          "availableInGameEditions": [],
          "id": self.id,
          "index": 0,
          "type": "StashRows",
          "unknown": is_true(self.ui.box_unknown_sr.currentText()),
          "value": int(self.ui.box_rows_sr.cleanText())
        }
      case "TraderStanding":
        reward_timing = self.ui.box_rewardtiming_ts.currentText()
        reward = {
          "availableInGameEditions": [],
          "id": self.id,
          "index": 0,
          "target": self.parent.parent.traders[self.ui.box_trader_ts.currentText()],
          "type": "TraderStanding",
          "unknown": is_true(self.ui.box_unknown_ts.currentText()),
          "value": float(self.ui.box_loyalty_ts.cleanText())
        }
      
      case "TraderUnlock":
        reward_timing = self.ui.box_rewardtiming_tul.currentText()
        reward = {
          "availableInGameEditions": [],
          "id": self.id,
          "index": 0,
          "target": self.parent.parent.traders[self.ui.box_trader_tul.currentText()],
          "type": "TraderUnlock",
          "unknown": is_true(self.ui.box_unknown_tul.currentText()),
        }

    rewards = self.parent.rewards
    rlist = self.parent.ui.list_rewards
    # remove rewards with the same id, if they already exist in either the reward lists or the qt list
    for type in ["Fail", "Started", "Success"]:
      for reward_idx in range(len(rewards[type])):
        if rewards[type][reward_idx]["id"] == self.id:
          rewards[type].pop(reward_idx)
          break

    for i in range(rlist.count()):
      if str(self.id) in rlist.item(i).text():
        rlist.takeItem(i)
        break

    rewards[reward_timing].append(reward)
    rlist.addItem(f"{reward_type}, {self.id}")
    self.close()

  def load_settings_from_dict(self, settings, reward_timing):
      pass
      print(f"Loading reward from dict: {settings}")
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
          trader = self.parent.parent.traders_invert[settings["traderId"]]
          self.ui.fld_tid_asu.setText(settings["target"])
          self.ui.box_trader_asu.setCurrentText(trader)
          self.ui.box_loyalty_asu.setValue(int(settings["loyaltyLevel"]))
          self.ui.box_unknown_asu.setCurrentText(unknown_or)
          self.ui.box_rewardtiming_asu.setCurrentText(reward_timing)
          self.ui.tabWidget.setCurrentIndex(2)
          self.items_asu = copy.deepcopy(settings["items"])
          for item in self.items_asu:
            has_soc = 'upd' in item and 'StackObjectsCount' in item['upd']
            has_pid = 'parentId' in item
            has_sid = 'slotId' in item
            self.ui.list_items_asu.addItem(f"_id: {item['_id']}, _tpl: {item['_tpl']}, SOC: {item['upd']['StackObjectsCount'] if has_soc else 'n/a'}, parentId: {item['parentId'] if has_pid else 'n/a'}, slotId: {item['slotId'] if has_sid else 'n/a'}, fir: {1}")

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
            has_soc = 'upd' in item and 'StackObjectsCount' in item['upd']
            has_pid = 'parentId' in item
            has_sid = 'slotId' in item
            self.ui.list_items_item.addItem(f"_id: {item['_id']}, _tpl: {item['_tpl']}, SOC: {item['upd']['StackObjectsCount'] if has_soc else 'n/a'}, parentId: {item['parentId'] if has_pid else 'n/a'}, slotId: {item['slotId'] if has_sid else 'n/a'}, fir: {1}")


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
          trader = self.parent.parent.traders_invert[settings["target"]]
          self.ui.tabWidget.setCurrentIndex(3)
          self.ui.box_rewardtiming_ts.setCurrentText(reward_timing)
          self.ui.box_loyalty_ts.setValue(float(settings["value"]))
          self.ui.box_trader_ts.setCurrentText(trader)
          self.ui.box_unknown_ts.setCurrentText(unknown_or)

        case "TraderUnlock":
          trader = self.parent.parent.traders_invert[settings["target"]]
          self.ui.tabWidget.setCurrentIndex(7)
          self.ui.box_rewardtiming_tul.setCurrentText(reward_timing)
          self.ui.box_unknown_tul.setCurrentText(unknown_or)
          self.ui.box_trader_tul.setCurrentText(trader)

  def setup_buttons(self):
    self.ui.pb_finalize_ach.released.connect(lambda: self.finalize("Achievement"))
    self.ui.pb_finalize_asu.released.connect(lambda: self.finalize("AssortmentUnlock"))
    self.ui.pb_finalize_exp.released.connect(lambda: self.finalize("Experience"))
    self.ui.pb_finalize_item.released.connect(lambda: self.finalize("Item"))
    self.ui.pb_finalize_sk.released.connect(lambda: self.finalize("Skill"))
    self.ui.pb_finalize_sr.released.connect(lambda: self.finalize("StashRows"))
    self.ui.pb_finalize_ts.released.connect(lambda: self.finalize("TraderStanding"))
    self.ui.pb_finalize_tul.released.connect(lambda: self.finalize("TraderUnlock"))
    self.ui.pb_additem_asu.released.connect(lambda: self.add_item("AssortmentUnlock"))
    self.ui.pb_remitem_asu.released.connect(lambda: self.remove_selected_item("AssortmentUnlock"))
    self.ui.pb_additem_item.released.connect(lambda: self.add_item("Item"))
    self.ui.pb_remitem_item.released.connect(lambda: self.remove_selected_item("Item"))
    self.ui.pb_load_fields_item.released.connect(lambda: self.load_selected_item_to_fields("Item"))
    self.ui.pb_load_fields_asu.released.connect(lambda: self.load_selected_item_to_fields("AssortmentUnlock"))


  def setup_box_selections(self):
    self.ui.box_trader_asu.addItems(self.parent.parent.traders.keys())
    self.ui.box_trader_ts.addItems(self.parent.parent.traders.keys())
    self.ui.box_trader_tul.addItems(self.parent.parent.traders.keys())
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
    self.ui.box_rewardtiming_tul.addItems(self.parent.parent.controller.reward_timing)
    self.ui.box_unknown_tul.addItems(self.parent.parent.controller.default_tf)

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
    self.ui.pb_edit_reward.released.connect(self.edit_selected_reward)
    self.ui.pb_remove_reward.released.connect(self.remove_selected_reward)
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

  def edit_selected_reward(self):
    rlist = self.ui.list_rewards
    select = rlist.selectedItems()
    # if no reward selected, just skip
    if len(select) <= 0:
      return
    reward_text = select[0].text()

    # hacky but easier than setting up a bunch of tables in qt6
    reward_id = reward_text.split(" ")[-1]
    for type in ["Fail", "Started", "Success"]:
      for reward in self.rewards[type]:
        if reward["id"] == reward_id:
          found_reward = reward
          break
    # create questbuilder window and load fields
    dlg = Gui_RewardDlg(parent=self)
    dlg.load_settings_from_dict(found_reward, type)

  def remove_selected_reward(self):
    rlist = self.ui.list_rewards
    select = rlist.selectedItems()
    # if no reward selected, just skip
    if len(select) <= 0:
      return
    reward_text = select[0].text()

    # hacky but easier than setting up a bunch of tables in qt6
    reward_id = reward_text.split(" ")[-1]

    # remove the quest-to-be-edited from the lists
    for type in ["Fail", "Started", "Success"]:
      for reward in self.rewards[type]:
        if reward["id"] == reward_id:
          self.rewards[type].remove(reward)
          break
    
    for i in range(rlist.count()):
      if str(reward_id) in rlist.item(i).text():
        rlist.takeItem(i)
        break

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
      # rewards WIP
      "rewards": (None, "rewards"),
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
          case "rewards":
            print("Setting rewards")
            self.rewards = copy.deepcopy(v) # copy it b/c pass by reference screws thing up here
            for type in ["Fail", "Started", "Success"]:
              for reward in self.rewards[type]:
                self.ui.list_rewards.addItem(f"{reward['type']}, {reward['id']}")
      else:
        print(f"Skipping {k}")

  def finalize(self):
    quest_id = self.quest_id
    quest = {
      quest_id: {
      "QuestName": self.ui.fld_quest_name.displayText(),
      "_id": quest_id,
      "acceptPlayerMessage": quest_id + " acceptPlayerMessage",
      "acceptanceAndFinishingSource": "eft",
      "arenaLocations": [],
      "canShowNotificationsInGame": is_true(self.ui.box_can_show_notif.currentText()),
      "changeQuestMessageText": quest_id + " changeQuestMessageText",
      "completePlayerMessage": quest_id + " completePlayerMessage",
      "conditions": {
        "AvailableForFinish": [],#add task lists
        "AvailableForStart": [],
        "Fail": []
      },
      "declinePlayerMessage": quest_id + " declinePlayerMessage",
      "description": quest_id + " description",
      "failMessageText": quest_id + " failMessageText",
      "image": self.ui.fld_image_name.displayText(),
      "instantComplete": is_true(self.ui.box_insta_complete.currentText()),
      "isKey": False,
      "location": self.parent.locations[self.ui.box_location.currentText()],
      "name": quest_id + " name",
      "note": quest_id + " note",
      "progressSource": "eft",
      "rankingModes": [],
      "restartable": is_true(self.ui.box_restartable.currentText()),
      "rewards": self.rewards,
      "secretQuest": is_true(self.ui.box_secret_quest.currentText()),
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
    self.ui.ab_add_item.released.connect(self.add_item)
    self.on_launch() #custom Code
    self.show()

    

    # if self.ui.ab_unlimitedcount.isChecked() : 
    #   self.ui.ab_quantity.clear()
    #   self.ui.ab_quantity.setEnabled(False)

    self.itemlist = []
    self.barterlist = []
    self.loyaltylist = []


  def on_launch(self):
     self.setup_box_selections()

  def setup_box_selections(self):
    self.ui.ab_loyalty_combo.addItems(self.parent.controller.ab_box_loyalty_level)
    self.ui.ab_rouble_radiobutton.setChecked(True)
    self.ui.ab_quest_check.setChecked(False)

  def add_item(self):
    table = self.ui.ab_table
    header = self.ui.ab_table.horizontalHeader()

    table.setColumnCount(6)
    table.setHorizontalHeaderLabels(["Name","Quantity","Cost","Loyalty Level","Quest Locked?","Currency"])
    table.setAlternatingRowColors(True)
    table.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
    table.resizeRowsToContents
    table.adjustSize
    header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    mongosaved = ObjectId
    name = self.ui.ab_itemname.text()
    unlimited = "true" if self.ui.ab_unlimitedcount.isChecked() else "false"
    quantity = "Unlimited" if self.ui.ab_unlimitedcount.isChecked() else int(self.ui.ab_quantity.text() or 0)
    loyatlylevel = self.ui.ab_loyalty_combo.currentText()
    itemID = self.ui.ab_Item_Id
    cost = self.ui.ab_cost_edit.text() or 0
    questlocked = "Yes" if self.ui.ab_quest_check.isChecked() else "No"
    questID = self.ui.ab_quest_id

    #insert questCondition

    cashtype = "Undefined" #set cashtype then check type and apply
    if self.ui.ab_rouble_radiobutton.isChecked() :
      cashtype = "Roubles"
    elif self.ui.ab_usd_button.isChecked():
      cashtype = "USD"
    else :
      cashtype = "Euros"

    if self.ui.ab_unlimitedcount.isChecked():
      item = {
        "_id": mongosaved,
            "_tpl": itemID,
            "parentId": "hideout",
            "slotId": "hideout",
            "upd": {
                "UnlimitedCount": unlimited,
                "StackObjectsCount": 1
            },
            "unlockedOn": "",
            "questID": ""
      }
    else:
      item = {
        "_id": mongosaved,
            "_tpl": itemID,
            "parentId": "hideout",
            "slotId": "hideout",
            "upd": {
                "UnlimitedCount": unlimited,
                "StackObjectsCount": self.ui.ab_quantity
            },
            "unlockedOn": "",
            "questID": ""
      }

    if self.ui.ab_quest_check.isChecked():
      item = {
        "_id": mongosaved,
            "_tpl": itemID,
            "parentId": "hideout",
            "slotId": "hideout",
            "upd": {
                "UnlimitedCount": unlimited,
                "StackObjectsCount": self.ui.ab_quantity
            },
            "unlockedOn": "success",
            "questID": questID
      }
    else:
      item.pop("unlockedOn", None)
      item.pop("questID", None)

    match cashtype:
      case "Roubles":
        barter = {
          mongosaved: [
            [
              {
                  "_tpl": "5449016a4bdc2d6f028b456f",
                  "count": cost
              }
            ]
          ]
        }
      case "USD":
        barter = {
          mongosaved: [
            [
              {
                  "_tpl": "5696686a4bdc2da3298b456a",
                  "count": cost
              }
            ]
          ]
        }
      case "Euros":
        barter = {
          mongosaved: [
            [   
              {
                  "_tpl": "569668774bdc2da2298b4568",
                  "count": cost
              }
            ]
          ]
        }

    loyalty = {
          mongosaved:loyatlylevel,
    }



    row = table.rowCount()
    table.insertRow(row)
    
    table.setItem(row,0,QTableWidgetItem(name))
    table.setItem(row,1,QTableWidgetItem(str(quantity)))
    table.setItem(row,2,QTableWidgetItem(str(cost)))
    table.setItem(row,3,QTableWidgetItem(loyatlylevel))
    table.setItem(row,4,QTableWidgetItem(questlocked))
    table.setItem(row,5,QTableWidgetItem(cashtype))



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