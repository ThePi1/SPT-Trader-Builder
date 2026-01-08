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
    #RewardFail RewardStarted RewardSuccess
    self.table_fields = {}

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

  def add_table_field(self, type, table, _id, values, dataobj):
    print(f"Debug: adding type: {type}, table: {table}, id: {_id}, values:  {values}, dataobj: {dataobj}")
    # for single column tables, the only column is the "id"
    # values looks like this: {1: "col1 field", 2: "col2 field", ...}
    if type not in self.table_fields:
      self.table_fields[type] = {}

    # we already have an entry for this, let's remove it first
    if _id in self.table_fields[type]:
      self.remove_selected_table_item(type=type, table=table)
    
    # add it into the list if it doesn't already exist
    if not _id in self.table_fields[type]:
      # set data
      self.table_fields[type][_id] = dataobj
      # add it into the table
      row = table.rowCount()
      table.insertRow(row)
      print(values)
      for col,text in values.items():
        table.setItem(row,col,QTableWidgetItem(str(text)))
    print(f"Table fields:\n{self.table_fields}")

  def remove_selected_table_item(self, type, table, id_row=0):
    print(f"Debug: removing selected item, type: {type}, table: {table}. Table_fields: {self.table_fields}")
    # if we need to check multiple types (like for rewards), do so
    if type == "RewardAny":
      alltypes = ["RewardFail", "RewardStarted", "RewardSuccess"]
    else:
      alltypes = [type]

    select = table.selectedItems()
    # if no reward selected, just skip
    if len(select) <= 0:
      return
    row = select[0].row()
    row_id = table.item(row, id_row).text()
    for type in alltypes:
      print(f"Debug remove: type found?{type in self.table_fields}, row_id in typedict?{type in row_id in self.table_fields and row_id in self.table_fields[type]}")
      if type in self.table_fields and row_id in self.table_fields[type]:
        self.table_fields[type].pop(row_id)
    table.removeRow(row)
    print(f"Table fields:\n{self.table_fields}")

  def get_singlecolumn_field_list(self, key):
    if key in self.table_fields:
      return list(self.table_fields[key].keys())
    else:
      return []

  def get_multicolumn_values_list(self, key):
    if key in self.table_fields:
      return list(self.table_fields[key].values())
    else:
      return []

  def reset_by_key(self, key):
    if key in self.table_fields:
      del self.table_fields[key]

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
    # self.items_item = []
    # self.items_asu = []
  
  def on_launch(self):
    self.setup_box_selections()
    self.setup_buttons()

  def add_item(self, tab):
    internal_id = str(ObjectId())
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
        # self.items_item.append(item)
        # self.ui.list_items_item.addItem(f"_id: {item['_id']}, _tpl: {item['_tpl']}, SOC: {item['upd']['StackObjectsCount'] if has_soc else 'n/a'}, parentId: {item['parentId'] if has_pid else 'n/a'}, slotId: {item['slotId'] if has_sid else 'n/a'}, fir: {self.ui.chk_fir_item.isChecked()}")
        self.parent.parent.add_table_field(f"RewardItem", self.ui.tb_item, internal_id, {0: item['_id'], 1: item['_tpl'], 2: item['upd']['StackObjectsCount'] if has_soc else 'n/a', 3: item['parentId'] if has_pid else 'n/a', 4: item['slotId'] if has_sid else 'n/a', 5: self.ui.chk_fir_item.isChecked(), 6: internal_id}, item)

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

        # self.items_asu.append(item)
        # self.ui.list_items_asu.addItem(f"_id: {item['_id']}, _tpl: {item['_tpl']}, SOC: {item['upd']['StackObjectsCount'] if has_soc else 'n/a'}, fir: {self.ui.chk_fir_asu.isChecked()}")
        
        self.parent.parent.add_table_field(f"RewardAssortmentUnlock", self.ui.tb_asu_item, internal_id, {0: item['_id'], 1: item['_tpl'], 2: item['upd']['StackObjectsCount'] if has_soc else 'n/a', 3: item['parentId'] if has_pid else 'n/a', 4: item['slotId'] if has_sid else 'n/a', 5: self.ui.chk_fir_asu.isChecked(), 6: internal_id}, item)


  def remove_selected_item(self, tab):
    match tab:
      case "AssortmentUnlock":
        self.parent.parent.remove_selected_table_item(type="RewardAssortmentUnlock", table=self.ui.tb_asu_item, id_row=6)
      case "Item":
        self.parent.parent.remove_selected_table_item(type="RewardItem", table=self.ui.tb_item, id_row=6)

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
        local_items = self.parent.parent.get_multicolumn_values_list("RewardAssortmentUnlock")
        reward = {
          "availableInGameEditions": [],
          "id": self.id,
          "index": 0,
          "items": local_items,
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
        local_items = self.parent.parent.get_multicolumn_values_list("RewardItem")
        reward = {
          "availableInGameEditions": [],
          "findInRaid": is_true(self.ui.box_fir_item.currentText()),
          "id": self.id,
          "index": 0,
          "items": local_items,
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
    table  = self.parent.ui.tb_rewards

    # remove rewards with the same id, if they already exist in either the reward lists or the qt list
    for type in ["Fail", "Started", "Success"]:
      for reward_idx in range(len(rewards[type])):
        if rewards[type][reward_idx]["id"] == self.id:
          rewards[type].pop(reward_idx)
          break

    for i in range(table.rowCount()):
      if str(self.id) in table.item(i, 0).text():#row,column
        table.removeRow(i)
        break
    
    self.parent.parent.add_table_field(f"Reward{reward_timing}", self.parent.ui.tb_rewards, self.id, {0: self.id, 1: reward_timing, 2: reward_type}, reward)
    print(self.parent.parent.table_fields)
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
            internal_id = str(ObjectId()) # this is only used for table purposes, so we don't need to actually match it to anything
            self.parent.parent.add_table_field(f"RewardAssortmentUnlock", self.ui.tb_asu_item, internal_id, {0: item['_id'], 1: item['_tpl'], 2: item['upd']['StackObjectsCount'] if has_soc else 'n/a', 3: item['parentId'] if has_pid else 'n/a', 4: item['slotId'] if has_sid else 'n/a', 5: self.ui.chk_fir_asu.isChecked(), 6: internal_id}, item)
            #self.ui.list_items_asu.addItem(f"_id: {item['_id']}, _tpl: {item['_tpl']}, SOC: {item['upd']['StackObjectsCount'] if has_soc else 'n/a'}, parentId: {item['parentId'] if has_pid else 'n/a'}, slotId: {item['slotId'] if has_sid else 'n/a'}, fir: {1}")

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
            internal_id = str(ObjectId()) # this is only used for table purposes, so we don't need to actually match it to anything
            self.parent.parent.add_table_field(f"RewardItem", self.ui.tb_item, internal_id, {0: item['_id'], 1: item['_tpl'], 2: item['upd']['StackObjectsCount'] if has_soc else 'n/a', 3: item['parentId'] if has_pid else 'n/a', 4: item['slotId'] if has_sid else 'n/a', 5: self.ui.chk_fir_item.isChecked(), 6: internal_id}, item)
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
    self.ui.pb_rem_task.released.connect(lambda: self.parent.remove_selected_table_item(type="Condition", table=self.ui.tb_cond))
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
    pass

  def edit_selected_reward(self):
    tb_reward = self.ui.tb_rewards
    select = tb_reward.selectedItems()
    # if no reward selected, just skip
    if len(select) <= 0:
      return
    row = select[0].row()
    reward_id = tb_reward.item(row, 0).text()

    for type in ["Fail", "Started", "Success"]:
      if f"Reward{type}" in self.parent.table_fields:
        for id in self.parent.table_fields[f"Reward{type}"]:
          print(id)
          reward = self.parent.table_fields[f"Reward{type}"][id]
          if id == reward_id:
            found_reward = reward
            break
    # create questbuilder window and load fields
    dlg = Gui_RewardDlg(parent=self)
    dlg.load_settings_from_dict(found_reward, type)

  def remove_selected_reward(self):
    self.parent.remove_selected_table_item(type="RewardAny", table=self.ui.tb_rewards)
    print(self.parent.table_fields)

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
            local_rewards = copy.deepcopy(v) # copy it b/c pass by reference screws thing up here
            for type in ["Fail", "Started", "Success"]:
              for reward in local_rewards[type]:
                if f"Reward{type}" not in self.parent.table_fields:
                  self.parent.table_fields[f"Reward{type}"] = {}
                self.parent.add_table_field(f"Reward{type}", self.ui.tb_rewards, reward['id'], {0: reward['id'], 1:type, 2:reward['type']}, reward)
      else:
        print(f"Skipping {k}")

  def finalize(self):
    quest_id = self.quest_id
    rewards_calc = {
      "Fail": [],
      "Started": [],
      "Success": []
    }
    for k,v in rewards_calc.items():
      if f"Reward{k}" in self.parent.table_fields:
        for _id,reward in self.parent.table_fields[f"Reward{k}"].items():
          rewards_calc[k].append(reward)
          # print(_id, reward)
    location_calc = [] if self.ui.box_location.currentText() == "any" else self.parent.locations[self.ui.box_location.currentText()]
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
        "AvailableForFinish": self.parent.get_multicolumn_values_list("ConditionFinish"), # ConditionFinish
        "AvailableForStart": self.parent.get_multicolumn_values_list("ConditionStart"), # ConditionStart
        "Fail": self.parent.get_multicolumn_values_list("ConditionFail") # ConditionFail
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
    self.id = str(ObjectId())
    self.cc = []
    # self.weapons = [] # used for CC/Kills, add ids in as needed
    # self.status = [] # used for CC/exitstatus
    # self.location = [] # used for cc/location
    self.on_launch() # Custom code in this one
    self.show()
  
  def on_launch(self):
     self.setup_box_selections()
     self.setup_text_edit()
     self.setup_buttons()

  def setup_box_selections(self):
    ctr = self.parent.parent.controller
    self.ui.box_target_cck.addItems(ctr.tb_elim_box_target)
    self.ui.box_targetrole_cck.addItems(ctr.tb_elim_box_targetrole)
    self.ui.box_bodypart_cck.addItems(ctr.tb_elim_box_bodypart)
    self.ui.box_dist_compare_cck.addItems(ctr.default_compare)
    self.ui.box_weapons_cck.addItems(ctr.tb_elim_box_weapons)
    self.ui.box_status_cces.addItems(ctr.tb_exitstatus)
    self.ui.box_location_ccl.addItems(ctr.qb_box_location)
    self.ui.box_hofind_it.addItems(ctr.tb_handover_box_cond_type)
    self.ui.box_only_fir_it.addItems(ctr.default_ft)
    self.ui.box_compare_sk.addItems(ctr.default_compare)
    self.ui.box_target_sk.addItems(ctr.default_skills)
    self.ui.box_fir_li.addItems(ctr.default_ft)
    self.ui.box_compare_tl.addItems(ctr.default_compare)
    self.ui.box_target_tl.addItems(ctr.tb_traderloyalt_target_box)
    self.ui.box_compare_lv.addItems(ctr.default_compare)
    self.ui.box_status_qs.addItems(ctr.tb_queststatus)
    self.ui.box_comparemethod_ts.addItems(ctr.default_compare)
    self.ui.box_cc_qtlab.addItems(ctr.qb_box_quest_type_label)
    self.ui.box_ff.addItems(ctr.tb_finishfail)
    self.ui.box_ff_it.addItems(ctr.tb_finishfail)
    self.ui.box_ff_sk.addItems(ctr.tb_finishfail)
    self.ui.box_ff_li.addItems(ctr.tb_finishfail)
    self.ui.box_ff_pb.addItems(ctr.tb_finishfail)
    self.ui.box_ff_tl.addItems(ctr.tb_finishfail)
    self.ui.box_trader_ts.addItems(ctr.tb_traderloyalt_target_box)

  def setup_buttons(self):
    # CounterCreator types first:
    self.ui.pb_finalize_ccvp.released.connect(lambda: self.cc_add("VisitPlace"))
    self.ui.pb_finalize_cck.released.connect(lambda: self.cc_add("Kills"))
    self.ui.pb_finalize_cces.released.connect(lambda: self.cc_add("ExitStatus"))
    self.ui.pb_finalize_ccen.released.connect(lambda: self.cc_add("ExitName"))
    self.ui.pb_finalize_ccl.released.connect(lambda: self.cc_add("Location"))
    # Others:
    self.ui.pb_finalize_it.released.connect(lambda: self.finalize("Item")) # will be switched based on subtype later
    self.ui.pb_finalize_sk.released.connect(lambda: self.finalize("Skill"))
    self.ui.pb_finalize_li.released.connect(lambda: self.finalize("LeaveItemAtLocation"))
    self.ui.pb_finalize_pb.released.connect(lambda: self.finalize("PlaceBeacon"))
    self.ui.pb_finalize_cc.released.connect(lambda: self.finalize("CounterCreator"))
    # TODO: Add WeaponAssembly menu and finalize link here
    self.ui.pb_finalize_tl.released.connect(lambda: self.finalize("TraderLoyalty"))
    self.ui.pb_finalize_lv.released.connect(lambda: self.finalize("Level"))
    self.ui.pb_finalize_qs.released.connect(lambda: self.finalize("Quest"))
    self.ui.pb_finalize_ts.released.connect(lambda: self.finalize("TraderStanding"))
    self.ui.pb_addwep_cck.released.connect(lambda: self.parent.parent.add_table_field(f"Kills", self.ui.tb_wep, self.ui.box_weapons_cck.currentText(), {0: self.ui.box_weapons_cck.currentText()}, self.ui.box_weapons_cck.currentText()))
    self.ui.pb_removewep_cck.released.connect(lambda: self.parent.parent.remove_selected_table_item(type="Kills", table=self.ui.tb_wep))
    self.ui.pb_remove_cc.released.connect(lambda: self.parent.parent.remove_selected_table_item(type="CounterCreator", table=self.ui.tb_cc))
    self.ui.pb_status_rem_cces.released.connect(lambda: self.parent.parent.remove_selected_table_item(type="ExitStatus", table=self.ui.tb_cces))
    self.ui.pb_cces_add.released.connect(lambda: self.parent.parent.add_table_field(f"ExitStatus", self.ui.tb_cces, self.ui.box_status_cces.currentText(), {0: self.ui.box_status_cces.currentText()}, self.ui.box_status_cces.currentText()))
    self.ui.pb_add_ccl.released.connect(lambda: self.parent.parent.add_table_field(f"Location", self.ui.tb_ccl, self.ui.box_location_ccl.currentText(), {0: self.ui.box_location_ccl.currentText()}, self.ui.box_location_ccl.currentText()))
    self.ui.pb_rem_ccl.released.connect(lambda: self.parent.parent.remove_selected_table_item(type="Location", table=self.ui.tb_ccl))
    self.ui.pb_addvis.released.connect(lambda: self.parent.parent.add_table_field(f"VisibilityCond", self.ui.tb_vis, self.ui.fld_visibility_targetid.displayText(), {0: self.ui.fld_visibility_targetid.displayText()}, self.ui.fld_visibility_targetid.displayText()))
    self.ui.pb_remvis.released.connect(lambda: self.parent.parent.remove_selected_table_item(type="VisibilityCond", table=self.ui.tb_vis))
    self.ui.pb_additem_it.released.connect(lambda: self.parent.parent.add_table_field(f"HFItems", self.ui.tb_items, self.ui.fld_itemid_it.displayText(), {0: self.ui.fld_itemid_it.displayText()}, self.ui.fld_itemid_it.displayText()))
    self.ui.pb_remitem_it.released.connect(lambda: self.parent.parent.remove_selected_table_item(type="HFItems", table=self.ui.tb_items))
    self.ui.pb_addstatus_qs.released.connect(lambda: self.parent.parent.add_table_field(f"QStatus", self.ui.tb_status_qs, self.ui.box_status_qs.currentText(), {0: self.ui.box_status_qs.currentText()}, self.ui.box_status_qs.currentText()))
    self.ui.pb_remstatus_qs.released.connect(lambda: self.parent.parent.remove_selected_table_item(type="QStatus", table=self.ui.tb_status_qs))

  def setup_text_edit(self):
    self.ui.fld_taskid_gen.setText(self.id)

  def cc_add(self, cond_type):
    subtask_id = str(ObjectId())
    match cond_type:
      case "VisitPlace":
        cond = {
          "conditionType": "VisitPlace",
          "dynamicLocale": False,
          "globalQuestCounterId": "",
          "id": subtask_id,
          "target": self.ui.fld_zoneid_ccvp.displayText(),
          "value": 1
        }
      case "Kills":
        # TODO: add support for arbitrary list of fields, not just one, as is the case with:
        # bodyPart, savageRole, weapon, weaponCaliber, weaponModsExclusive, weaponModsInclusive
        # TODO: add support for weaponModsInclusive and weaponModsExclusive fields
        local_weapons = self.parent.parent.get_singlecolumn_field_list("Kills")
        cond = {
          "bodyPart": [self.ui.box_bodypart_cck.currentText()],
          "compareMethod": ">=", # hard code for kill quest
          "conditionType": "Kills",
          "daytime": {
            "from": int(self.ui.fld_time_from_cck.displayText()), # TODO: add validator for field types instead of blindly erroring out
            "to": int(self.ui.fld_time_to_cck.displayText())
          },
          "distance": {
            "compareMethod": self.ui.box_dist_compare_cck.currentText(), 
            "distance": int(self.ui.fld_dist_cck.displayText())
          },
          "dynamicLocale": False,
          "enemyEquipmentExclusive": [],
          "enemyEquipmentInclusive": [],
          "enemyHealthEffects": [],
          "id": subtask_id,
          "resetOnSessionEnd": self.ui.chk_cck_reset_sessionend.isChecked(),
          "savageRole": self.ui.box_targetrole_cck.currentText(),
          "target": self.ui.box_target_cck.currentText(),
          "value": 1,
          "weapon": local_weapons,
          "weaponCaliber": [],
          "weaponModsExclusive": [],
          "weaponModsInclusive": []
        }
      case "ExitStatus":
        local_status = self.parent.parent.get_singlecolumn_field_list("ExitStatus")
        cond = {
          "conditionType": "ExitStatus",
          "dynamicLocale": False,
          "id": subtask_id,
          "status": local_status,
        }
      case "ExitName":
        cond = {
          "conditionType": "ExitName",
          "dynamicLocale": False,
          "id": subtask_id,
          "exitName": self.ui.fld_exitname_ccen.displayText(),
        }
      case "Location":
        local_locations = self.parent.parent.get_singlecolumn_field_list("Location")
        cond = {
          "conditionType": "Location",
          "dynamicLocale": False,
          "id": subtask_id,
          "target": local_locations,
        }

    self.parent.parent.add_table_field(f"CounterCreator", self.ui.tb_cc, subtask_id, {0: subtask_id, 1: cond_type}, cond)

  def finalize(self, cond_type):
    timing = ""
    match cond_type:
      # 3 different types of ids, all unique:
      # one, each cc list item has its own id
      # two, the whole cc list itself has an id
      # three, the top-level CC task/condition has an id
      # we use number 3 for the id in the internal datastore, and show that id in the task/cond list
      case "CounterCreator":
        local_vis_cond = self.parent.parent.get_singlecolumn_field_list("VisibilityCond")
        local_counter = {
          "conditions": [],
          "id": str(ObjectId())
        }
        local_counter["conditions"] = self.parent.parent.get_multicolumn_values_list("CounterCreator")
        timing = self.ui.box_ff.currentText()
        cond = {
          "completeInSeconds": 0,
          "conditionType": "CounterCreator",
          "counter": local_counter,
          "doNotResetIfCounterCompleted": False, # TODO: implement gui for this
          "dynamicLocale": False,
          "globalQuestCounterId": "",
          "id": self.id,
          "index": 0,
          "isNecessary": False, # TODO: implement gui for this
          "isResetOnConditionFailed": False, # TODO: implement gui for this
          "oneSessionOnly": False,
          "parentId": self.ui.fld_parentid_cc.displayText(),
          "type": self.ui.box_cc_qtlab.currentText(),
          "value": int(self.ui.fld_quantity_cc.displayText()),
          "visibilityConditions": local_vis_cond
        }
      case "Item":
        sub_cond_type = self.ui.box_hofind_it.currentText()
        if sub_cond_type == "FindItem":
          local_vis_cond = self.parent.parent.get_singlecolumn_field_list("VisibilityCond")
          timing = self.ui.box_ff_it.currentText()
          local_target = self.parent.parent.get_singlecolumn_field_list("HFItems")
          cond = {
            "conditionType": "FindItem",
            "countInRaid": False,
            "dogtagLevel": 0,
            "dynamicLocale": False,
            "globalQuestCounterId": "",
            "id": self.id,
            "index": 0,
            "inEncoded": False,
            "maxDurability": int(self.ui.fld_maxdur_it.displayText()),
            "minDurability": int(self.ui.fld_mindur_it.displayText()),
            "onlyFoundInRaid": is_true(self.ui.box_only_fir_it.currentText()),
            "parentId": self.ui.fld_parentid.displayText(),
            "target": local_target,
            "value": int(self.ui.fld_quantity_it.displayText()),
            "visibilityConditions": local_vis_cond
          }
        if sub_cond_type == "HandoverItem":
          local_vis_cond = self.parent.parent.get_singlecolumn_field_list("VisibilityCond")
          timing = self.ui.box_ff_it.currentText()
          local_target = self.parent.parent.get_singlecolumn_field_list("HFItems")
          cond = {
            "conditionType": "HandoverItem",
            "dogtagLevel": 0,
            "dynamicLocale": False,
            "globalQuestCounterId": "",
            "id": self.id,
            "index": 0,
            "inEncoded": False,
            "maxDurability": int(self.ui.fld_maxdur_it.displayText()),
            "minDurability": int(self.ui.fld_mindur_it.displayText()),
            "onlyFoundInRaid": is_true(self.ui.box_only_fir_it.currentText()),
            "parentId": self.ui.fld_parentid.displayText(),
            "target": local_target,
            "value": int(self.ui.fld_quantity_it.displayText()),
            "visibilityConditions": local_vis_cond
          }
      case "Skill":
        local_vis_cond = self.parent.parent.get_singlecolumn_field_list("VisibilityCond")
        timing = self.ui.box_ff_sk.currentText()
        cond = {
          "compareMethod": self.ui.box_compare_sk.currentText(),
          "conditionType": "Skill",
          "dynamicLocale": False,
          "globalQuestCounterId": "",
          "id": self.id,
          "index": 0,
          "parentId": self.ui.fld_parentid_sk_2.displayText(),
          "target": self.ui.box_target_sk.currentText(),
          "value": int(self.ui.fld_level_sk.displayText()),
          "visibilityConditions": local_vis_cond
        }
      case "LeaveItemAtLocation":
        local_vis_cond = self.parent.parent.get_singlecolumn_field_list("VisibilityCond")
        timing = self.ui.box_ff_li.currentText()
        cond = {
          "conditionType": "LeaveItemAtLocation",
          "dogtagLevel": 0,
          "dynamicLocale": False,
          "globalQuestCounterId": "",
          "id": self.id,
          "index": 0,
          "inEncoded": False,
          "maxDurability": self.ui.fld_maxdur_li.displayText(),
          "minDurability": self.ui.fld_mindur_li.displayText(),
          "onlyFoundInRaid": is_true(self.ui.box_fir_li.currentText()),
          "parentId": self.ui.fld_parentid_li.displayText(),
          "plantTime": int(self.ui.fld_plant_time_li.displayText()),
          "target": [self.ui.fld_targeti_li.displayText()], # TODO: add list here, not just single
          "value": int(self.ui.fld_quantity_li.displayText()),
          "visibilityConditions": local_vis_cond,
          "zoneId": self.ui.fld_zoneid_li.displayText()
        }
      case "PlaceBeacon":
        local_vis_cond = self.parent.parent.get_singlecolumn_field_list("VisibilityCond")
        timing = self.ui.box_ff_pb.currentText()
        cond = {
          "conditionType": "PlaceBeacon",
          "dynamicLocale": False,
          "globalQuestCounterId": "",
          "id": self.id,
          "index": 0,
          "parentId": self.ui.fld_parentid_pb.displayText(),
          "plantTime": int(self.ui.sb_time_pb.cleanText()),
          "target": [self.ui.fld_targeti_li.displayText()],
          "value": "5991b51486f77447b112d44f", # ItemID for the MS2000 marker, can also use Radio Repeater (63a0b2eabea67a6d93009e52) according to docs
          "visibilityConditions": local_vis_cond,
          "zoneId": self.ui.fld_zoneid_pb.displayText()
        }
      case "WeaponAssembly":
        # TODO: implement
        pass
      case "TraderLoyalty":
        local_vis_cond = self.parent.parent.get_singlecolumn_field_list("VisibilityCond")
        timing = self.ui.box_ff_tl.currentText()
        cond = {
          "compareMethod": self.ui.box_compare_tl.currentText(),
          "conditionType": "TraderLoyalty",
          "dynamicLocale": False,
          "globalQuestCounterId": "",
          "id": self.id,
          "index": 0,
          "parentId": self.ui.fld_parentid_tl.displayText(), # TODO: this isn't actually in the docs, does it work?? remove if not
          "target": self.parent.parent.traders[self.ui.box_target_tl.currentText()],
          "value": int(self.ui.fld_level_tl.displayText()),
          "visibilityConditions": local_vis_cond,
        }

      # These 3 next are start-only
      case "Level":
        timing = "Start"
        cond = {
          "compareMethod": self.ui.box_compare_lv.currentText(),
          "conditionType": "Level",
          "dynamicLocale": False,
          "globalQuestCounterId": "",
          "id": self.id,
          "index": 0,
          "parentId": "",
          "value": int(self.ui.fld_value_lv.displayText()),
          "visibilityConditions": []
        }
      case "Quest":
        timing = "Start"
        local_status = self.parent.parent.get_singlecolumn_field_list("QStatus")
        cond = {
          "availableAfter": int(self.ui.fld_avail_qs.displayText()),
          "conditionType": "Quest",
          "dispersion": 0,
          "dynamicLocale": False,
          "globalQuestCounterId": "",
          "id": self.id,
          "index": 0,
          "parentId": "",
          "status": local_status,
          "target": self.ui.fld_tid_qs.displayText(),
          "visibilityConditions": []
        }
      case "TraderStanding":
        timing = "Start"
        cond = {
          "compareMethod": self.ui.box_comparemethod_ts.currentText(),
          "conditionType": "TraderStanding",
          "dynamicLocale": False,
          "globalQuestCounterId": "",
          "id": self.id,
          "index": 0,
          "parentId": "",
          "target": self.parent.parent.traders[self.ui.box_trader_ts.currentText()],
          "value": int(self.ui.fld_value_ts.displayText()),
          "visibilityConditions": []
        }
    
    # Add to task list and close self out
    # ConditionFinish, ConditionStart, ConditionFail
    self.parent.parent.add_table_field(f"Condition{timing}", self.parent.ui.tb_cond, self.id, {0: self.id, 1: timing, 2: cond_type}, cond)
    # clear the list, since we're exported and done with it, if we need to load, we will do it from the JSON object itself
    self.parent.parent.reset_by_key(cond_type)
    if cond_type == "CounterCreator": # we also need to clear all the subfields, if they were used, if it's cc
      for c in ["VisitPlace", "Kills", "ExitStatus", "ExitName", "Location"]:
        self.parent.parent.reset_by_key(c)
    self.close()