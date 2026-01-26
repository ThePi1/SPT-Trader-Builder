import sys
import re
import json
import copy
from pymongo import MongoClient
from bson.objectid import ObjectId

from PyQt6 import QtCore, QtGui
from PyQt6.QtGui import  QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt, QRunnable
from PyQt6.QtWidgets import QApplication, QAbstractItemView, QDialog, QHeaderView, QAbstractScrollArea, QFileDialog, QMainWindow, QPushButton, QListView, QListWidget, QListWidgetItem, QTableWidgetItem

from gui_about import Ui_AboutMenu
from gui_main import Ui_MainGUI
from gui_updates import Ui_UpdateMenu
from gui_quests import Ui_QuestWindow
from gui_tasks import Ui_TaskWindow
from gui_assort import Ui_AssortBuilder
from gui_rewards import Ui_rewardBuilder

def val_field(value, emptyval, defaultval, expectclass):
  if value == emptyval:
    return defaultval
  else:
    try:
      convert_val = expectclass(value)
      return value
    except Exception as e:
      if expectclass == int:
        return 0
      if expectclass == float:
        return 0.0
      if expectclass == list:
        return []
      if expectclass == dict:
        return {}
      return ""

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
  def __init__(self, controller, parent=None):
    super().__init__(parent)
    self.ui = Ui_MainGUI()
    self.ui.setupUi(self)
    self.on_launch()
    self.setupTreeView()
    self.controller = controller
    self.parent = parent
    self.setup_box_selections()
    self.ui.actionExit.triggered.connect(self.onExit)
    self.ui.actionExport_Queued_Quests.triggered.connect(self.onExportQuests)
    self.ui.actionEdit_Selected_Quest.triggered.connect(self.editSelectedQuest)
    self.ui.actionImport_Quests.triggered.connect(self.importQuests)
    self.ui.wb_addpart_button.released.connect(self.addpart)
    self.ui.wb_base_check.toggled.connect(self.baseWeaponChecked)
    self.ui.actionAnalyze_CC_subtypes.triggered.connect(self.analyze_cc)
    self.ui.actionRemove_Selected_Quest.triggered.connect(self.remove_selected_quest)
    #self.ui.wb_treeview.itemSelectionChanged.connect(self.onWeaponSelected)
    self.traders = self.importJson("data\\traders.json")
    # used for going back from ID to trader name for loading quest to edit
    self.traders_invert = {v:k for k,v in self.traders.items()}
    self.weapons = self.importJson("data\weapons.json")
    self.locations = self.importJson("data\locations.json")
    self.status = self.importJson("data\status.json")
    self.status_invert = {v:k for k,v in self.status.items()}
    self.quests = {}
    #RewardFail RewardStarted RewardSuccess
    self.table_fields = {}
    self.weaponlist = []

  def on_launch(self):
    self.ui.main_tab.setCurrentIndex(0)
    self.ui.wb_base_check.setChecked(True)
    self.baseWeaponChecked(self.ui.wb_base_check.isChecked())
  
  def setup_box_selections(self):
    self.ui.wb_modslot_combo.addItems(self.controller.ab_box_modslot)


  def baseWeaponChecked(self,checked): #UI Behavior
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
    self.model.setHorizontalHeaderLabels(["Name","ItemID","DatabaseID","ParentID"])
    self.ui.wb_treeview.setModel(self.model)
    self.ui.wb_treeview.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
  
  def addpart(self): #add part to treeview and weaponlist
    savedmongo = str(ObjectId())
    item_name = QStandardItem(self.ui.wb_weaponname_edit.text())
    parent_ID = QStandardItem(self.ui.wb_itemid_edit.text())

    child_name = QStandardItem(str(self.ui.wb_modslot_combo.currentText()))
    child_ID = QStandardItem(self.ui.wb_itemid_edit.text())
    print("Button Started")
    
    slotID = self.ui.wb_modslot_combo.currentText() if not self.ui.wb_base_check else ""

    if self.ui.wb_base_check.isChecked(): # check if the base weapon box is checked.
      database_ID = QStandardItem(savedmongo)
      item_name.setData(savedmongo,Qt.ItemDataRole.UserRole)
      self.model.appendRow([item_name,parent_ID,database_ID, QStandardItem("")])
      self.addPartToLists(parent_ID.text(),database_ID.text(), "",slotID)
      print("checkbox is checked")
      return
    
    tree_index = self.ui.wb_treeview.currentIndex()
    if not tree_index.isValid(): # checks if new index is valid
      print("Tree index is not valid")
      return
    
    clicked_item = self.model.itemFromIndex(tree_index) # gets data from tree_index

    
    parent_item = clicked_item.parent() # checks what is the parent and returns none if has no parent
    if parent_item is None: # if item has no parent then set the parent back to index 0 basically catches if the user selected the value collumn and the key then sets it to the key collumn
      clicked_item = self.model.item(clicked_item.row(),0)
    else:#same as above but if user clicks the childs value not the key
      clicked_item = parent_item.child(clicked_item.row(),0)

    parent_data = clicked_item.data(Qt.ItemDataRole.UserRole)



    if parent_data is None:
      print("No Parent Data")

    child_savedmongo = str(ObjectId())
    child_name.setData(child_savedmongo,Qt.ItemDataRole.UserRole)

    print("Append Child")
    #add item to treeview
    clicked_item.appendRow([child_name,child_ID,QStandardItem(child_savedmongo),QStandardItem(str(parent_data))])
    self.addPartToLists(child_ID.text(),child_savedmongo, parent_data,slotID)
    #expands tree of newly added items parent
    self.ui.wb_treeview.expand(tree_index)
    print("Button Completed")

  def addPartToLists(self,ItemID,databaseID, parentID,slotID):
    print("Item ID: " + ItemID)
    print("Database ID: " + databaseID)
    print("Parent ID: " + parentID)
    
    if not self.ui.wb_base_check.isChecked():
      item = {
        "_id": databaseID,
        "_tpl": ItemID,
        "parentId": parentID,
        "slotId": slotID
      }

    else:
      item = { #sets initial item key structure for editing in logic.
        "_id": databaseID,
        "_tpl": ItemID,
        "parentId": "hideout",
        "slotId": "hideout",
        "upd": {

          }
      }
    finalized_item = {
      databaseID: item
    }

    self.weaponlist.append(finalized_item)

    self.exportWeaponPresets(self.weaponlist)

  def exportWeaponPresets(self,weaponlist):

    with open("Exported Files/weaponpresets.json", "w") as f:
      json.dump(weaponlist, f, indent=2)

  def importJson(self, path):
    with open(path, "r") as f:
      out = json.load(f)
      return out
  
  def analyze_cc(self):
    print(f"Analyzing CC subtypes, opening dialogue...")
    filename, ok = QFileDialog.getOpenFileName(self, "Import Quest JSON")
    print(filename)
    cc_keeptrack = {}
    with open(filename, "r") as f:
      try:
        quests_import = json.load(f)
      except Exception as e:
        print(f"Error loading quest file: {e}")
      for quest_id in quests_import.keys():
        #print(f"Found quest {quests_import[quest_id]['QuestName']} ({quest_id})")
        print(f"{quests_import[quest_id]['QuestName']}")
        if "conditions" in quests_import[quest_id] and "AvailableForFinish" in quests_import[quest_id]['conditions'] and len(quests_import[quest_id]['conditions']['AvailableForFinish']) > 0:
          for avf_c in quests_import[quest_id]['conditions']['AvailableForFinish']:
            if avf_c['conditionType'] == "CounterCreator":
              for cond in avf_c['counter']['conditions']:
                print(f"Inner conditionType: {cond['conditionType']}")
                if cond['conditionType'] not in cc_keeptrack:
                  cc_keeptrack[cond['conditionType']] = 1
                else:
                  cc_keeptrack[cond['conditionType']] += 1
    
    print(cc_keeptrack)

  def importQuests(self):
    filename, ok = QFileDialog.getOpenFileName(self, "Import Quest JSON")
    print(filename)
    with open(filename, "r") as f:
      try:
        quests_import = json.load(f)
      except Exception as e:
        print(f"Error loading quest file: {e}")
      for quest_id in quests_import.keys():
        #print(f"Found quest {quests_import[quest_id]['QuestName']} ({quest_id})")
        print(f"{quests_import[quest_id]['QuestName']}")
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
    elif type == "ConditionAny":
      alltypes = ["ConditionFinish", "ConditionStart", "ConditionFail"]
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

  def reset_by_id(self, id):
    for category,cat_dict in self.table_fields.items():
      if id in cat_dict:
        del cat_dict[id]
      # if id is found, remove it similar to reset by key above

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
    self.ui.pb_rem_task.released.connect(lambda: self.parent.remove_selected_table_item(type="ConditionAny", table=self.ui.tb_cond))
    self.ui.pb_finalize_quest.released.connect(self.finalize)
    self.ui.pb_add_reward.released.connect(lambda: Gui_RewardDlg(parent=self))
    self.ui.pb_edit_reward.released.connect(self.edit_selected_reward)
    self.ui.pb_edit_task.released.connect(self.edit_selected_task)
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
      "conditions":(None, "conditions"),
      "image": (self.ui.fld_image_name, "fld"),
      "instantComplete": (self.ui.box_insta_complete, "box"),
      "location": (self.ui.box_location, "box"),
      "restartable": (self.ui.box_restartable, "box"),
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
            print("Loading rewards...")
            local_rewards = copy.deepcopy(v) # copy it b/c pass by reference screws thing up here
            for type in ["Fail", "Started", "Success"]:
              for reward in local_rewards[type]:
                if f"Reward{type}" not in self.parent.table_fields:
                  self.parent.table_fields[f"Reward{type}"] = {}
                self.parent.add_table_field(f"Reward{type}", self.ui.tb_rewards, reward['id'], {0: reward['id'], 1:type, 2:reward['type']}, reward)
            print("Done loading rewards!")
          case "conditions":
            print("Loading conditions...")
            local_conditions = copy.deepcopy(v)
            for type in ["Finish", "Start", "Fail"]:
              m = {"Finish":"AvailableForFinish", "Start":"AvailableForStart", "Fail":"Fail"}
              for cond in local_conditions[m[type]]:
                if f"Condition{type}" not in self.parent.table_fields:
                  self.parent.table_fields[f"Condition{type}"] = {}
                self.parent.add_table_field(f"Condition{type}", self.ui.tb_cond, cond['id'], {0: cond['id'], 1:type, 2:cond['conditionType']}, cond)
            print("Done loading conditions!")
            pass
      else:
        print(f"Skipping {k}")

  def edit_selected_task(self):
      breaknext = False
      tb_cond = self.ui.tb_cond
      select = tb_cond.selectedItems()
      # if no cond selected, just skip
      if len(select) <= 0:
        return
      row = select[0].row()
      cond_id = tb_cond.item(row, 0).text()

      for type in ["Finish", "Start", "Fail"]:
        if breaknext: break
        if f"Condition{type}" in self.parent.table_fields:
          for id in self.parent.table_fields[f"Condition{type}"]:
            if breaknext: break
            print(id)
            cond = self.parent.table_fields[f"Condition{type}"][id]
            if id == cond_id:
              print(f"Editing task: found id {id} under type {type}.")
              found_reward = cond
              breaknext = True
            
      # create questbuilder window and load fields
      dlg = Gui_TaskDlg(parent=self)
      dlg.load_settings_from_dict(found_reward, type)

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
    self.on_launch() #custom Code
    self.show()
    self.ui.ab_add_item.released.connect(self.add_item)
    self.ui.ab_remove_item.released.connect(self.remove_Item)
    self.ui.actionImport_Assort_json.triggered.connect(self.onImportAssort)
    self.ui.actionExport_Assort_json.triggered.connect(self.onExportAssort)
    self.ui.ab_unlimitedcount.toggled.connect(self.unlimitedIsChecked)
    self.ui.ab_buyrestriction_checkbox.toggled.connect(self.brestrictionChecked)
    self.ui.ab_quest_check.toggled.connect(self.questLockedChecked)
    self.ui.ab_weappart_check.toggled.connect(self.weaponPartChecked)
    self.ui.ab_table.itemSelectionChanged.connect(self.onWeaponSelected)
    self.ui.ab_table.itemClicked.connect(self.copy_clicked_cell)
    self.ui.ab_search.textChanged.connect(self.filterTable)
    self.ui.ab_itembarter_check.toggled.connect(self.itemBarterChecked)
    self.itemlist = []
    self.barterlist = {}
    self.loyaltylist = {}

  def on_launch(self):
    self.setup_box_selections()
    self.ui.ab_rouble_radiobutton.setChecked(True)
    self.ui.ab_quest_check.setChecked(False)
    self.ui.ab_buyRestriction_edit.setEnabled(False)
    self.ui.ab_quest_id.setEnabled(False)
    self.ui.ab_itembarter_edit.setEnabled(False)
    self.weaponPartChecked(self.ui.ab_weappart_check.isChecked())
    self.questLockedChecked(self.ui.ab_quest_check.isChecked())
    self.brestrictionChecked(self.ui.ab_buyrestriction_checkbox.isChecked())
    table = self.ui.ab_table
    table.setColumnCount(6)
    table.setHorizontalHeaderLabels(["ItemTPL","Quantity","Cost","Loyalty Level","Quest Locked?","Currency"])
    table.setAlternatingRowColors(True)
    table.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
    header = self.ui.ab_table.horizontalHeader()
    header.setSectionResizeMode(0,QHeaderView.ResizeMode.ResizeToContents)
    for col in range (1,6):
      header.setSectionResizeMode(col,QHeaderView.ResizeMode.Stretch)
    self.ui.ab_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

  def copy_clicked_cell(self, item):
      
      #if self.ui.ab_weappart_check.isChecked():
        #return
      text = item.text()
      QApplication.clipboard().setText(text)

  def setup_box_selections(self):
    self.ui.ab_loyalty_combo.addItems(self.parent.controller.ab_box_loyalty_level)
    self.ui.ab_condition_box.addItems(self.parent.controller.ab_box_condition_req)
    self.ui.ab_modslot_combo.addItems(self.parent.controller.ab_box_modslot)

  def onImportAssort(self): #AI WRITTEN function purely for fun lol.
      table = self.ui.ab_table
      filename, _ = QFileDialog.getOpenFileName(
          self,
          "Import Assort JSON",
          "",
          "JSON Files (*.json);;All Files (*)"
      )
      if not filename:
          return

      with open(filename, "r", encoding="utf-8") as f:
          assort = json.load(f)

      items = assort.get("items", [])
      for item in assort.get("items",[]):
        self.itemlist.append(item)

      barter_scheme = assort.get("barter_scheme", {})
      self.barterlist.update(assort.get("barter_scheme", {}))

      loyal_levels = assort.get("loyal_level_items", {})
      self.loyaltylist.update(assort.get("loyal_level_items", {}))


      table = self.ui.ab_table
      table.clear()
      table.setColumnCount(6)
      table.setHorizontalHeaderLabels(["Name","Quantity","Cost","Loyalty Level","Quest Locked?","Currency"])
      table.setRowCount(0)
      table.setAlternatingRowColors(True)
      table.setSortingEnabled(True)
      table.horizontalHeader().setSortIndicatorShown(True)

      for it in items:
          item_id = it.get("_id", "")
          tpl = it.get("_tpl", "")
          

          upd = it.get("upd", {}) or {}
          unlimited = bool(upd.get("UnlimitedCount", False))
          stack = upd.get("StackObjectsCount", 1)

          # Quantity
          qty_display = "∞" if unlimited else str(stack)

          # Loyalty level
          loyalty = loyal_levels.get(item_id, "")
          loyalty_display = "" if loyalty == "" else str(loyalty)

          # Quest locked?
          quest_id = it.get("questID", "")
          unlocked_on = it.get("unlockedOn", "")
          # show questID if present, otherwise blank
          quest_display = quest_id if quest_id else ""

          # Cost + currency (your file uses barter_scheme[item_id] -> [[{_tpl, count}, ...]])
          cost_display = ""
          currency_display = ""
          scheme = barter_scheme.get(item_id)

          if scheme and isinstance(scheme, list) and len(scheme) > 0:
              # first "OR" group
              group0 = scheme[0]
              if isinstance(group0, list) and len(group0) > 0:
                  payment0 = group0[0]
                  if isinstance(payment0, dict):
                      cost_display = str(payment0.get("count", ""))
                      currency_display = str(payment0.get("_tpl", ""))

                      if currency_display == "5449016a4bdc2d6f028b456f":
                        currency_display = "Roubles"
                      elif currency_display == "5696686a4bdc2da3298b456a":
                        currency_display = "USD"
                      else:
                        currency_display = "Euro"

          # Insert row
          row = table.rowCount()
          table.insertRow(row)

          tpl = it.get("_tpl", "")
          slot = it.get("slotId", "")
          parent = it.get("parentId", "")

          display_name = tpl
          if isinstance(slot, str) and slot.startswith("mod_") and parent != "hideout":
              display_name = f"{parent}+{slot}"   # <-- what you asked for

          name_item = QTableWidgetItem(display_name)
          name_item.setData(Qt.ItemDataRole.UserRole, it.get("_id", ""))  # keep your hidden id


          table.setItem(row, 0, name_item)
          table.setItem(row, 1, QTableWidgetItem(qty_display))
          table.setItem(row, 2, QTableWidgetItem(cost_display))
          table.setItem(row, 3, QTableWidgetItem(loyalty_display))
          table.setItem(row, 4, QTableWidgetItem(quest_display))
          table.setItem(row, 5, QTableWidgetItem(currency_display))

  def onWeaponSelected(self): #gets the user role from the table and fills the assortID line edit.
    row = self.ui.ab_table.currentRow()
    
    if row < 0 : 
      return
    
    mongosaved = self.ui.ab_table.item(row,0).data(Qt.ItemDataRole.UserRole)
    print("* " + str(self.ui.ab_table.item(row,0).data(Qt.ItemDataRole.UserRole)))
    self.ui.ab_weapmongo_edit.setText(mongosaved)

  def filterTable(self,query:str):
    table = self.ui.ab_table
    q = query.strip().lower()
    for row in range(table.rowCount()):
      item = table.item(row, 0)  # display name col
      text = item.text().lower() if item else ""
      mongo = item.data(Qt.ItemDataRole.UserRole)
      mongo = str(mongo).lower() if mongo else ""
      match = (q in text) or (q in mongo)  # contains search; use == for exact match
      table.setRowHidden(row, not match)

  def unlimitedIsChecked(self, checked): #UI behavior
    if checked : 
      self.ui.ab_quantity.clear()
      self.ui.ab_quantity.setEnabled(False)
    else:
      self.ui.ab_quantity.setEnabled(True)

  def brestrictionChecked(self, checked): #UI behavior
      if checked : 
        self.ui.ab_buyRestriction_edit.setEnabled(True)
      else:
        self.ui.ab_buyRestriction_edit.setEnabled(False)
        self.ui.ab_buyRestriction_edit.clear()

  def itemBarterChecked(self,checked):
      if checked : 
        self.ui.ab_itembarter_edit.setEnabled(True)
      else:
        self.ui.ab_itembarter_edit.setEnabled(False)
        self.ui.ab_itembarter_edit.clear()

  def questLockedChecked(self, checked): #UI behavior
      
      if not self.ui.ab_weappart_check.isChecked(): #Checks to see if weaponpart is not checked and skips ui behavior if it is
        if checked : 
          self.ui.ab_quest_id.setEnabled(True)
          self.ui.ab_condition_box.setEnabled(True)
        else:
          self.ui.ab_quest_id.setEnabled(False)
          self.ui.ab_condition_box.setEnabled(False)
          self.ui.ab_quest_id.clear()

  def weaponPartChecked(self, checked): #UI behavior
    if checked : 
      self.ui.ab_quantity.clear()
      self.ui.ab_quantity.setEnabled(False)
      self.ui.ab_Item_Id.clear()
      self.ui.ab_Item_Id.setEnabled(False)
      self.ui.ab_unlimitedcount.setEnabled(False)
      self.ui.ab_cost_edit.clear()
      self.ui.ab_cost_edit.setEnabled(False)
      self.ui.ab_rouble_radiobutton.setEnabled(False)
      self.ui.ab_usd_button.setEnabled(False)
      self.ui.ab_euro_button.setEnabled(False)
      self.ui.ab_loyalty_combo.setEnabled(False)
      self.ui.ab_quest_check.setEnabled(False)
      self.ui.ab_quest_id.setEnabled(False)
      self.ui.ab_quest_id.clear()
      self.ui.ab_condition_box.setEnabled(False)
      self.ui.ab_buyrestriction_checkbox.setEnabled(False)
      self.ui.ab_buyRestriction_edit.setEnabled(False)
      self.ui.ab_buyRestriction_edit.clear()
      self.ui.ab_itembarter_check.setEnabled(False)
      self.ui.ab_itembarter_edit.setEnabled(False)
      self.ui.ab_itembarter_edit.clear()
      self.ui.ab_buyrestriction.setStyleSheet("color: gray;")
      self.ui.ab_itemid.setStyleSheet("color: gray;")
      self.ui.ab_quantity_2.setStyleSheet("color: gray;")
      self.ui.ab_loyalty.setStyleSheet("color: gray;")
      self.ui.ab_condition.setStyleSheet("color: gray;")
      self.ui.ab_cost.setStyleSheet("color: gray;")

      self.ui.ab_partid_edit.setEnabled(True)
      self.ui.ab_weapmongo_edit.setEnabled(False)
      self.ui.ab_modslot_combo.setEnabled(True)
      self.ui.ab_mongo.setStyleSheet("")
      self.ui.ab_weapid.setStyleSheet("")
      self.ui.ab_modslot.setStyleSheet("")
      self.questLockedChecked(self.ui.ab_quest_check.isChecked())
      
    else:
      self.ui.ab_quantity.clear()
      self.ui.ab_quantity.setEnabled(True)
      self.ui.ab_Item_Id.clear()
      self.ui.ab_Item_Id.setEnabled(True)
      self.ui.ab_unlimitedcount.setEnabled(True)
      self.ui.ab_cost_edit.clear()
      self.ui.ab_cost_edit.setEnabled(True)
      self.ui.ab_rouble_radiobutton.setEnabled(True)
      self.ui.ab_usd_button.setEnabled(True)
      self.ui.ab_euro_button.setEnabled(True)
      self.ui.ab_loyalty_combo.setEnabled(True)
      self.ui.ab_quest_check.setEnabled(True)
      self.ui.ab_quest_id.setEnabled(True)
      self.ui.ab_quest_id.clear()
      self.ui.ab_condition_box.setEnabled(True)
      self.ui.ab_buyrestriction_checkbox.setEnabled(True)
      self.ui.ab_buyRestriction_edit.setEnabled(True)
      self.ui.ab_itembarter_check.setEnabled(True)
      self.ui.ab_buyrestriction.setStyleSheet("")
      self.ui.ab_itemid.setStyleSheet("")
      self.ui.ab_quantity_2.setStyleSheet("")
      self.ui.ab_loyalty.setStyleSheet("")
      self.ui.ab_condition.setStyleSheet("")
      self.ui.ab_cost.setStyleSheet("")

      self.ui.ab_weapmongo_edit.setEnabled(False)
      self.ui.ab_modslot_combo.setEnabled(False)
      self.ui.ab_partid_edit.setEnabled(False)
      self.ui.ab_weapmongo_edit.clear()
      self.ui.ab_partid_edit.clear()
      self.ui.ab_mongo.setStyleSheet("color: gray;")
      self.ui.ab_weapid.setStyleSheet("color: gray;")
      self.ui.ab_modslot.setStyleSheet("color: gray;")

      self.questLockedChecked(self.ui.ab_quest_check.isChecked())
      self.itemBarterChecked(self.ui.ab_itembarter_check.isChecked())

  def remove_Item(self): # remove selected item from lists/dicts and remove from table.
    row = self.ui.ab_table.currentRow()
    if row < 0 : 
      return
    
    mongosaved = self.ui.ab_table.item(row,0).data(Qt.ItemDataRole.UserRole)
    self.itemlist = [ #goes through list and keeps all items that do not have specific mongoID
      item for item in self.itemlist
      if item.get("_id") != mongosaved
    ]
    if mongosaved not in self.barterlist: #checks if weapon part and skips barterlist and loyaltylist
      self.ui.ab_table.removeRow(row)
    else: #If not part removes from remaining Dicts and table.
      self.barterlist.pop(mongosaved)
      self.loyaltylist.pop(mongosaved)
      self.ui.ab_table.removeRow(row)

  def add_item(self): #The basic assort add function

    table = self.ui.ab_table

    if self.ui.ab_weappart_check.isChecked() and self.ui.ab_weapmongo_edit.text().strip() == "":
      self.ui.ab_weapmongo_edit.setStyleSheet("border: 2px solid red; background-color: #ffe6e6;")
      return

    #Item variables
    mongosaved = str(ObjectId())
    itemID = self.ui.ab_Item_Id.text().strip()
    unlimited = True if self.ui.ab_unlimitedcount.isChecked() else False
    quantity = str(self.ui.ab_quantity.text() or 0)
    barteritem = str(self.ui.ab_itembarter_edit.text() or 0)
    loyaltylevel = str(self.ui.ab_loyalty_combo.currentText())
    cost = self.ui.ab_cost_edit.text().strip() or 0
    questLockedChecked = "Yes" if self.ui.ab_quest_check.isChecked() else "No"
    questID = self.ui.ab_quest_id.text().strip()
    buyrestriction = self.ui.ab_buyRestriction_edit.text() or 0

    #Weapon Part Variables
    slotID = str(self.ui.ab_modslot_combo.currentText())
    parentID = self.ui.ab_weapmongo_edit.text().strip()
    partID = self.ui.ab_partid_edit.text().strip()

    #checks whether its a weapon part. if it is creates a name for table that mixes the original weapon its built off of and the slot name
    if self.ui.ab_weappart_check.isChecked() and self.ui.ab_table.item(self.ui.ab_table.currentRow(),0).data(Qt.ItemDataRole.UserRole) == self.ui.ab_weapmongo_edit.text():
      itemID = self.ui.ab_table.item(self.ui.ab_table.currentRow(),0).text() + " + " + self.ui.ab_modslot_combo.currentText()

    cashtype = "Undefined" #set cashtype then check type and apply
    if self.ui.ab_rouble_radiobutton.isChecked() :
      cashtype = "Roubles"
    elif self.ui.ab_usd_button.isChecked():
      cashtype = "USD"
    elif self.ui.ab_itembarter_check.isChecked():
      cashtype = "Item" 
    else :
      cashtype = "Euros"

    #selects item key structure depending on item or weapon part.
    if self.ui.ab_weappart_check.isChecked():
      item = {
        "_id": mongosaved,
        "_tpl": partID,
        "parentId": parentID,
        "slotId": slotID
      }
      self.itemlist.append(item)

    else:
      item = { #sets initial item key structure for editing in logic.
        "_id": mongosaved,
        "_tpl": itemID,
        "parentId": "hideout",
        "slotId": "hideout",
        "upd": {

          }
      }

      if self.ui.ab_unlimitedcount.isChecked():
        item["upd"].update({
          "UnlimitedCount": unlimited,
          "StackObjectsCount": 9999
        })

      else:
        item["upd"].update({
          "UnlimitedCount": unlimited,
          "StackObjectsCount": int(quantity)
        })

      if self.ui.ab_buyrestriction_checkbox.isChecked():
        item["upd"].update({
          "BuyRestrictionMax": int(buyrestriction),
          "BuyRestrictionCurrent": 0
        })

      if self.ui.ab_quest_check.isChecked():
        item.update({       
              "unlockedOn": "success",
              "questID": questID
        })
      self.itemlist.append(item)

      barter = { #sets initial barter_scheme key structure for editing in logic.
        mongosaved: [
              [
                {
                  "count": int(cost),
                  "_tpl": "cash"
                }
              ]
            ]
      }
      barterupdate = barter[mongosaved][0][0] #sets path for updating cashtypes cleans up logic readability

      match cashtype:
        case "Roubles":
          barterupdate.update({
            "_tpl": "5449016a4bdc2d6f028b456f"
          })
        case "USD":
          barterupdate.update({
            "_tpl": "5696686a4bdc2da3298b456a"
          })
        case "Euros":
          barterupdate.update({
            "_tpl": "569668774bdc2da2298b4568"
          })
        case "Item":
          barterupdate.update({
            "_tpl": str(barteritem)
          })
      
      
      loyalty = {mongosaved: int(loyaltylevel)} 


      self.barterlist.update(barter)
      self.loyaltylist.update(loyalty)

    row = table.rowCount()
    table.insertRow(row)
    item_Id = QTableWidgetItem(str(itemID))
    item_Id.setData(Qt.ItemDataRole.UserRole, mongosaved)
    tablequantity = "∞" if self.ui.ab_unlimitedcount.isChecked() else quantity
    
    table.setItem(row,0,item_Id)
    table.setItem(row,1,QTableWidgetItem(str(tablequantity)))
    table.setItem(row,2,QTableWidgetItem(str(cost)))
    table.setItem(row,3,QTableWidgetItem(loyaltylevel))
    table.setItem(row,4,QTableWidgetItem(questLockedChecked))
    table.setItem(row,5,QTableWidgetItem(cashtype))

    self.ui.ab_weapmongo_edit.setStyleSheet("")

  def onExportAssort(self):  #export the finalized assort
    assort = {
      "items": self.itemlist,
      "barter_scheme": self.barterlist,
      "loyal_level_items": self.loyaltylist
    }
    
    with open("Exported Files/assort.json", "w") as f:
      json.dump(assort, f, indent=2)



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
    self.ui.box_targets_cck.addItems(ctr.tb_elim_box_target)
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
    self.ui.box_distcomp_sh.addItems(ctr.default_compare)
    self.ui.box_target_sh.addItems(ctr.tb_elim_box_target)
    self.ui.box_shbp.addItems(ctr.tb_elim_box_bodypart)
    self.ui.box_shtr.addItems(ctr.tb_elim_box_targetrole)
    self.ui.box_encomp_he.addItems(ctr.default_compare)
    self.ui.box_hydcomp_he.addItems(ctr.default_compare)
    self.ui.box_timecomp_he.addItems(ctr.default_compare)
    self.ui.box_hebp.addItems(ctr.tb_elim_box_bodypart)
    self.ui.box_heef.addItems(ctr.tb_effect)
    self.ui.box_hb.addItems(ctr.tb_buff)


  def setup_buttons(self):
    # CounterCreator types first:
    self.ui.pb_finalize_ccvp.released.connect(lambda: self.cc_add("VisitPlace"))
    self.ui.pb_finalize_cck.released.connect(lambda: self.cc_add("Kills"))
    self.ui.pb_finalize_cces.released.connect(lambda: self.cc_add("ExitStatus"))
    self.ui.pb_finalize_ccen.released.connect(lambda: self.cc_add("ExitName"))
    self.ui.pb_finalize_ccl.released.connect(lambda: self.cc_add("Location"))
    self.ui.pb_finalize_cc_eq.released.connect(lambda: self.cc_add("Equipment"))
    self.ui.pb_finalize_shtr.released.connect(lambda: self.cc_add("Shots"))
    self.ui.pb_finalize_he.released.connect(lambda: self.cc_add("HealthEffect"))
    self.ui.pb_finalize_hb.released.connect(lambda: self.cc_add("HealthBuff"))
    self.ui.pb_finalize_fl.released.connect(lambda: self.cc_add("LaunchFlare"))
    self.ui.pb_finalize_iz.released.connect(lambda: self.cc_add("InZone"))

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
    self.ui.pb_finalize_wa.released.connect(lambda: self.finalize("WeaponAssembly"))

    # Kills table add/remove buttons
    self.ui.pb_addwep_cck.released.connect(lambda: self.parent.parent.add_table_field(f"KillsWep", self.ui.tb_wep, self.ui.box_weapons_cck.currentText(), {0: self.ui.box_weapons_cck.currentText()}, self.ui.box_weapons_cck.currentText()))
    self.ui.pb_removewep_cck.released.connect(lambda: self.parent.parent.remove_selected_table_item(type="KillsWep", table=self.ui.tb_wep))
    self.ui.pb_addtar_cck.released.connect(lambda: self.parent.parent.add_table_field(f"KillsTarget", self.ui.tb_targets, self.ui.box_targets_cck.currentText(), {0: self.ui.box_targets_cck.currentText()}, self.ui.box_targets_cck.currentText()))
    self.ui.pb_removetar_cck.released.connect(lambda: self.parent.parent.remove_selected_table_item(type="KillsTarget", table=self.ui.tb_targets))
    self.ui.pb_addtr_cck.released.connect(lambda: self.parent.parent.add_table_field(f"KillsTargetRole", self.ui.tb_targetrole, self.ui.box_targetrole_cck.currentText(), {0: self.ui.box_targetrole_cck.currentText()}, self.ui.box_targetrole_cck.currentText()))
    self.ui.pb_removetr_cck.released.connect(lambda: self.parent.parent.remove_selected_table_item(type="KillsTargetRole", table=self.ui.tb_targetrole))
    self.ui.pb_addbp_cck.released.connect(lambda: self.parent.parent.add_table_field(f"KillsBodyPart", self.ui.tb_bodypart, self.ui.box_bodypart_cck.currentText(), {0: self.ui.box_bodypart_cck.currentText()}, self.ui.box_bodypart_cck.currentText()))
    self.ui.pb_rembp_cck.released.connect(lambda: self.parent.parent.remove_selected_table_item(type="KillsBodyPart", table=self.ui.tb_bodypart))
    self.ui.pb_add_imod.released.connect(lambda: self.parent.parent.add_table_field(f"KillsModInc", self.ui.tb_incmods, self.ui.fld_incmod_cck.displayText(), {0: self.ui.fld_incmod_cck.displayText()}, self.ui.fld_incmod_cck.displayText()))
    self.ui.pb_rem_imod.released.connect(lambda: self.parent.parent.remove_selected_table_item(type="KillsModInc", table=self.ui.tb_incmods))
    self.ui.pb_add_emod.released.connect(lambda: self.parent.parent.add_table_field(f"KillsModExc", self.ui.tb_excmods, self.ui.fld_excmod_cck.displayText(), {0: self.ui.fld_excmod_cck.displayText()}, self.ui.fld_excmod_cck.displayText()))
    self.ui.pb_rem_emod.released.connect(lambda: self.parent.parent.remove_selected_table_item(type="KillsExc", table=self.ui.tb_excmods))

    # Other table buttons
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
    
    self.ui.pb_add_li_target.released.connect(lambda: self.parent.parent.add_table_field(f"LeaveItemTarget", self.ui.tb_li_target, self.ui.fld_li_target.displayText(), {0: self.ui.fld_li_target.displayText()}, self.ui.fld_li_target.displayText()))
    self.ui.pb_rem_li_target.released.connect(lambda: self.parent.parent.remove_selected_table_item(type="LeaveItemTarget", table=self.ui.tb_li_target))
    
    self.ui.pb_add_eqi.released.connect(lambda: self.parent.parent.add_table_field(f"EquipmentInclusive", self.ui.tb_eq_inc, self.ui.fld_eqi.displayText(), {0: self.ui.fld_eqi.displayText(), 1:self.ui.fld_equi_org.displayText()}, {'id': self.ui.fld_eqi.displayText(), 'org':self.ui.fld_equi_org.displayText()}))
    self.ui.pb_rem_eqi.released.connect(lambda: self.parent.parent.remove_selected_table_item(type="EquipmentInclusive", table=self.ui.tb_eq_inc))
    
    self.ui.pb_add_eqe.released.connect(lambda: self.parent.parent.add_table_field(f"EquipmentExclusive", self.ui.tb_eq_exc, self.ui.fld_eqi_2.displayText(), {0: self.ui.fld_eqi_2.displayText(), 1:self.ui.fld_eqe_org.displayText()}, {'id': self.ui.fld_eqi_2.displayText(), 'org':self.ui.fld_eqe_org.displayText()}))
    self.ui.pb_rem_eqe.released.connect(lambda: self.parent.parent.remove_selected_table_item(type="EquipmentExclusive", table=self.ui.tb_eq_exc))
    
    self.ui.pb_add_shbp.released.connect(lambda: self.parent.parent.add_table_field(f"ShotsBodyPart", self.ui.tb_sh_bp, self.ui.box_shbp.currentText(), {0: self.ui.box_shbp.currentText()}, self.ui.box_shbp.currentText()))
    self.ui.pb_rem_shbp.released.connect(lambda: self.parent.parent.remove_selected_table_item(type="ShotsBodyPart", table=self.ui.tb_sh_bp))
    
    self.ui.pb_add_shtr.released.connect(lambda: self.parent.parent.add_table_field(f"ShotsTargetRole", self.ui.tb_sh_tr, self.ui.box_shtr.currentText(), {0: self.ui.box_shtr.currentText()}, self.ui.box_shtr.currentText()))
    self.ui.pb_rem_shtr.released.connect(lambda: self.parent.parent.remove_selected_table_item(type="ShotsTargetRole", table=self.ui.tb_sh_tr))
    
    self.ui.pb_add_shw.released.connect(lambda: self.parent.parent.add_table_field(f"ShotsWeapon", self.ui.tb_sh_wep, self.ui.fld_shw.displayText(), {0: self.ui.fld_shw.displayText()}, self.ui.fld_shw.displayText()))
    self.ui.pb_rem_shw.released.connect(lambda: self.parent.parent.remove_selected_table_item(type="ShotsWeapon", table=self.ui.tb_sh_wep))
    
    self.ui.pb_add_shmi.released.connect(lambda: self.parent.parent.add_table_field(f"ShotsModsInclusive", self.ui.tb_incmod_sh, self.ui.fld_shmi.displayText(), {0: self.ui.fld_shmi.displayText()}, self.ui.fld_shmi.displayText()))
    self.ui.pb_rem_shmi.released.connect(lambda: self.parent.parent.remove_selected_table_item(type="ShotsModsInclusive", table=self.ui.tb_incmod_sh))
    
    self.ui.pb_add_shme.released.connect(lambda: self.parent.parent.add_table_field(f"ShotsModsExclusive", self.ui.tb_excmod_sh, self.ui.fld_shme.displayText(), {0: self.ui.fld_shme.displayText()}, self.ui.fld_shme.displayText()))
    self.ui.pb_rem_shme.released.connect(lambda: self.parent.parent.remove_selected_table_item(type="ShotsModsExclusive", table=self.ui.tb_excmod_sh))
    
    self.ui.pb_add_hebp.released.connect(lambda: self.parent.parent.add_table_field(f"HealthEffectBodyPart", self.ui.tb_hebp, self.ui.box_hebp.currentText(), {0: self.ui.box_hebp.currentText()}, self.ui.box_hebp.currentText()))
    self.ui.pb_rem_hebp.released.connect(lambda: self.parent.parent.remove_selected_table_item(type="HealthEffectBodyPart", table=self.ui.tb_hebp))
    
    self.ui.pb_add_heef.released.connect(lambda: self.parent.parent.add_table_field(f"HealthEffectEffects", self.ui.tb_heef, self.ui.box_heef.currentText(), {0: self.ui.box_heef.currentText()}, self.ui.box_heef.currentText()))
    self.ui.pb_rem_heef.released.connect(lambda: self.parent.parent.remove_selected_table_item(type="HealthEffectEffects", table=self.ui.tb_heef))
    
    self.ui.pb_add_hb.released.connect(lambda: self.parent.parent.add_table_field(f"HealthBuff", self.ui.tb_hb, self.ui.box_hb.currentText(), {0: self.ui.box_hb.currentText()}, self.ui.box_hb.currentText()))
    self.ui.pb_rem_hb.released.connect(lambda: self.parent.parent.remove_selected_table_item(type="HealthBuff", table=self.ui.tb_hb))

    self.ui.pb_add_iz.released.connect(lambda: self.parent.parent.add_table_field(f"InZone", self.ui.tb_iz, self.ui.fld_iz.displayText(), {0: self.ui.fld_iz.displayText()}, self.ui.fld_iz.displayText()))
    self.ui.pb_rem_iz.released.connect(lambda: self.parent.parent.remove_selected_table_item(type="InZone", table=self.ui.tb_iz))
    


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
        local_weapons = self.parent.parent.get_singlecolumn_field_list("KillsWep")
        local_weapons_id = []
        for wep in local_weapons:
          local_weapons_id.append(self.parent.parent.weapons[wep])
        local_targets = self.parent.parent.get_singlecolumn_field_list("KillsTarget")
        local_targetrole = self.parent.parent.get_singlecolumn_field_list("KillsTargetRole")
        local_bodypart = self.parent.parent.get_singlecolumn_field_list("KillsBodyPart")
        local_incmod = self.parent.parent.get_singlecolumn_field_list("KillsModInc")
        local_excmod = self.parent.parent.get_singlecolumn_field_list("KillsModExc")
        local_dist = val_field(self.ui.fld_dist_cck.displayText(), "", 0, int)
        local_timefrom = val_field(self.ui.fld_time_from_cck.displayText(), "", 0, int)
        local_timeto = val_field(self.ui.fld_time_to_cck.displayText(), "", 0, int)

        cond = {
          "bodyPart": local_bodypart,
          "compareMethod": ">=", # hard code for kill quest
          "conditionType": "Kills",
          "daytime": {
            "from": local_timefrom,
            "to": local_timeto
          },
          "distance": {
            "compareMethod": self.ui.box_dist_compare_cck.currentText(), 
            "distance": local_dist
          },
          "dynamicLocale": False,
          "enemyEquipmentExclusive": [],
          "enemyEquipmentInclusive": [],
          "enemyHealthEffects": [],
          "id": subtask_id,
          "resetOnSessionEnd": self.ui.chk_cck_reset_sessionend.isChecked(),
          "savageRole": local_targetrole,
          "target": local_targets,
          "value": 1,
          "weapon": local_weapons_id,
          "weaponCaliber": [],
          "weaponModsExclusive": local_excmod,
          "weaponModsInclusive": local_incmod
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
      case "Equipment":
        # This is all kind of a lot of work, but basically it's grouping the lists by org(or_group) for a list of multiple lists.
        # So, you can have (this set of 3 equip items) OR  (this other set of 2), etc.
        local_eqi = self.parent.parent.get_multicolumn_values_list("EquipmentInclusive")
        local_eqe = self.parent.parent.get_multicolumn_values_list("EquipmentExclusive")
        local_eqi_dict = {}
        local_eqe_dict = {}
        for e in local_eqi:
          if e['org'] not in local_eqi_dict:
            local_eqi_dict[e['org']] = [e['id']]
          else:
            local_eqi_dict[e['org']].append(e['id'])

        for e in local_eqe:
          if e['org'] not in local_eqe_dict:
            local_eqe_dict[e['org']] = [e['id']]
          else:
            local_eqe_dict[e['org']].append(e['id'])

        cond = {
          "IncludeNotEquippedItems": self.ui.cb_eq_uneq.isChecked(),
          "conditionType": "Equipment",
          "dynamicLocale": False,
          "equipmentExclusive": list(local_eqe_dict.values()),
          "equipmentInclusive": list(local_eqi_dict.values()),
          "id": subtask_id
        }
      case "Shots":
        local_bodypart = self.parent.parent.get_singlecolumn_field_list("ShotsBodyPart")
        local_targetrole  = self.parent.parent.get_singlecolumn_field_list("ShotsTargetRole")
        local_weapons  = self.parent.parent.get_singlecolumn_field_list("ShotsWeapon")
        local_modinc  = self.parent.parent.get_singlecolumn_field_list("ShotsModsInclusive")
        local_modexc  = self.parent.parent.get_singlecolumn_field_list("ShotsModsExclusive")
        local_dist = val_field(self.ui.fld_dist_sh.displayText(), "", 0, int)
        local_timefrom = val_field(self.ui.fld_timefrom_sh.displayText(), "", 0, int)
        local_timeto = val_field(self.ui.fld_timeto_sh.displayText(), "", 0, int)
        local_value = val_field(self.ui.fld_value_sh.displayText(), "", 0, int)
        cond = {
          "bodyPart": local_bodypart,
          "compareMethod": ">=",
          "conditionType": "Shots",
          "daytime": {
            "from": local_timefrom,
            "to": local_timeto
          },
          "distance": {
            "compareMethod": self.ui.box_distcomp_sh.currentText(),
            "value": local_dist
          },
          "dynamicLocale": False,
          "enemyEquipmentExclusive": [],
          "enemyEquipmentInclusive": [],
          "enemyHealthEffects": [],
          "id": subtask_id,
          "resetOnSessionEnd": self.ui.chk_cck_reset_sessionend_2.isChecked(),
          "savageRole": local_targetrole,
          "target": self.ui.box_target_sh.currentText(),
          "value": local_value,
          "weapon": [],
          "weaponCaliber": [],
          "weaponModsExclusive": local_modexc,
          "weaponModsInclusive": local_modinc
        }
      case "HealthEffect":
        local_enval = val_field(self.ui.fld_enval_he.displayText(), "", 0, int)
        local_timeval = val_field(self.ui.fld_timeval_he.displayText(), "", 0, int)
        local_hydval = val_field(self.ui.fld_hydval_he.displayText(), "", 0, int)
        local_bodypart = self.parent.parent.get_singlecolumn_field_list("HealthEffectBodyPart")
        local_effect = self.parent.parent.get_singlecolumn_field_list("HealthEffectEffects")
        cond = {
          "bodyPartsWithEffects": [
            {
              "bodyParts": local_bodypart,
              "effects": local_effect
            }
          ],
          "conditionType": "HealthEffect",
          "dynamicLocale": False,
          "energy": {
            "compareMethod": self.ui.box_encomp_he.currentText(),
            "value": local_enval
          },
          "hydration": {
            "compareMethod": self.ui.box_hydcomp_he.currentText(),
            "value": local_hydval
          },
          "id": subtask_id,
          "time": {
            "compareMethod": self.ui.box_timecomp_he.currentText(),
            "value": local_timeval
          }
        }
      case "HealthBuff":
        local_buff = self.parent.parent.get_singlecolumn_field_list("HealthBuff")
        cond = {
          "conditionType": "HealthBuff",
          "dynamicLocale": False,
          "id": subtask_id,
          "target": local_buff
        }
      case "LaunchFlare":
        cond = {
          "conditionType": "LaunchFlare",
          "dynamicLocale": False,
          "id": subtask_id,
          "target": self.ui.fld_fl_zone.displayText()
        }
      case "InZone":
        local_zone = self.parent.parent.get_singlecolumn_field_list("InZone")
        cond = {
          "conditionType": "InZone",
          "dynamicLocale": False,
          "id": subtask_id,
          "zoneIds": local_zone
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
        local_value = val_field(self.ui.fld_quantity_cc.displayText(), "", 0, int)
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
          "value": local_value,
          "visibilityConditions": local_vis_cond
        }
      case "Item":
        sub_cond_type = self.ui.box_hofind_it.currentText()
        if sub_cond_type == "FindItem":
          local_vis_cond = self.parent.parent.get_singlecolumn_field_list("VisibilityCond")
          timing = self.ui.box_ff_it.currentText()
          local_target = self.parent.parent.get_singlecolumn_field_list("HFItems")
          local_value = val_field(self.ui.fld_quantity_it.displayText(), "", 0, int)

          cond = {
            "conditionType": "FindItem",
            "countInRaid": False,
            "dogtagLevel": 0,
            "dynamicLocale": False,
            "globalQuestCounterId": "",
            "id": self.id,
            "index": 0,
            "inEncoded": False,
            "onlyFoundInRaid": is_true(self.ui.box_only_fir_it.currentText()),
            "parentId": self.ui.fld_parentid_it.displayText(),
            "target": local_target,
            "value": local_value,
            "visibilityConditions": local_vis_cond
          }
          if self.ui.fld_maxdur_it.displayText() != "":
            cond["maxDurability"] = val_field(self.ui.fld_maxdur_it.displayText(), "", 0, int)

          if self.ui.fld_maxdur_it.displayText() != "":
            cond["minDurability"] = val_field(self.ui.fld_mindur_it.displayText(), "", 0, int)


        if sub_cond_type == "HandoverItem":
          local_vis_cond = self.parent.parent.get_singlecolumn_field_list("VisibilityCond")
          timing = self.ui.box_ff_it.currentText()
          local_target = self.parent.parent.get_singlecolumn_field_list("HFItems")
          local_value = val_field(self.ui.fld_quantity_it.displayText(), "", 0, int)
          cond = {
            "conditionType": "HandoverItem",
            "dogtagLevel": 0,
            "dynamicLocale": False,
            "globalQuestCounterId": "",
            "id": self.id,
            "index": 0,
            "inEncoded": False,
            "onlyFoundInRaid": is_true(self.ui.box_only_fir_it.currentText()),
            "parentId": self.ui.fld_parentid.displayText(),
            "target": local_target,
            "value": local_value,
            "visibilityConditions": local_vis_cond
          }
          if self.ui.fld_maxdur_it.displayText() != "":
            cond["maxDurability"] = val_field(self.ui.fld_maxdur_it.displayText(), "", 0, int)

          if self.ui.fld_maxdur_it.displayText() != "":
            cond["minDurability"] = val_field(self.ui.fld_mindur_it.displayText(), "", 0, int)

      case "Skill":
        local_vis_cond = self.parent.parent.get_singlecolumn_field_list("VisibilityCond")
        timing = self.ui.box_ff_sk.currentText()
        local_value = val_field(self.ui.fld_level_sk.displayText(), "", 0, int)
        cond = {
          "compareMethod": self.ui.box_compare_sk.currentText(),
          "conditionType": "Skill",
          "dynamicLocale": False,
          "globalQuestCounterId": "",
          "id": self.id,
          "index": 0,
          "parentId": self.ui.fld_parentid_sk_2.displayText(),
          "target": self.ui.box_target_sk.currentText(),
          "value": local_value,
          "visibilityConditions": local_vis_cond
        }
      case "LeaveItemAtLocation":
        local_vis_cond = self.parent.parent.get_singlecolumn_field_list("VisibilityCond")
        local_target_ids = self.parent.parent.get_singlecolumn_field_list("LeaveItemTarget")
        timing = self.ui.box_ff_li.currentText()
        local_ptime = val_field(self.ui.fld_plant_time_li.displayText(), "", 0, int)
        local_value = val_field(self.ui.fld_quantity_li.displayText(), "", 0, int)
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
          "plantTime": local_ptime,
          "target": local_target_ids,
          "value": local_value,
          "visibilityConditions": local_vis_cond,
          "zoneId": self.ui.fld_zoneid_li.displayText()
        }
      case "PlaceBeacon":
        local_vis_cond = self.parent.parent.get_singlecolumn_field_list("VisibilityCond")
        timing = self.ui.box_ff_pb.currentText()
        local_ptime = val_field(self.ui.sb_time_pb.cleanText(), "", 10, int)
        local_value = val_field(self.ui.sb_value_pb.cleanText(), "", 1, int)
        cond = {
          "conditionType": "PlaceBeacon",
          "dynamicLocale": False,
          "globalQuestCounterId": "",
          "id": self.id,
          "index": 0,
          "parentId": self.ui.fld_parentid_pb.displayText(),
          "plantTime": local_ptime,
          "target": ["5991b51486f77447b112d44f"],  # ItemID for the MS2000 marker, can also use Radio Repeater (63a0b2eabea67a6d93009e52) according to docs
          "value": local_value,
          "visibilityConditions": local_vis_cond,
          "zoneId": self.ui.fld_zoneid_pb.displayText()
        }
      case "WeaponAssembly":
        # TODO: implement
        local_vis_cond = self.parent.parent.get_singlecolumn_field_list("VisibilityCond")
        timing = "Finish"
        cond = {
          "weapon_assembly_placeholder": "add_weapon_assembly_object_here"
        }
        pass
      case "TraderLoyalty":
        local_vis_cond = self.parent.parent.get_singlecolumn_field_list("VisibilityCond")
        timing = self.ui.box_ff_tl.currentText()
        local_value = val_field(self.ui.fld_level_tl.displayText(), "", 0, int)
        cond = {
          "compareMethod": self.ui.box_compare_tl.currentText(),
          "conditionType": "TraderLoyalty",
          "dynamicLocale": False,
          "globalQuestCounterId": "",
          "id": self.id,
          "index": 0,
          "parentId": self.ui.fld_parentid_tl.displayText(), # TODO: this isn't actually in the docs, does it work?? remove if not
          "target": self.parent.parent.traders[self.ui.box_target_tl.currentText()],
          "value": local_value,
          "visibilityConditions": local_vis_cond,
        }

      # These 3 next are start-only
      case "Level":
        timing = "Start"
        local_value = val_field(self.ui.fld_value_lv.displayText(), "", 0, int)
        cond = {
          "compareMethod": self.ui.box_compare_lv.currentText(),
          "conditionType": "Level",
          "dynamicLocale": False,
          "globalQuestCounterId": "",
          "id": self.id,
          "index": 0,
          "parentId": "",
          "value": local_value,
          "visibilityConditions": []
        }
      case "Quest":
        timing = "Start"
        local_status = self.parent.parent.get_singlecolumn_field_list("QStatus")
        local_status_int = [self.parent.parent.status[s] for s in local_status]
        local_availafter = val_field(self.ui.fld_avail_qs.displayText(), "", 0, int)
        cond = {
          "availableAfter": local_availafter,
          "conditionType": "Quest",
          "dispersion": 0,
          "dynamicLocale": False,
          "globalQuestCounterId": "",
          "id": self.id,
          "index": 0,
          "parentId": "",
          "status": local_status_int,
          "target": self.ui.fld_tid_qs.displayText(),
          "visibilityConditions": []
        }
      case "TraderStanding":
        timing = "Start"
        local_availafter = val_field(self.ui.fld_value_ts.displayText(), "", 0, int)
        cond = {
          "compareMethod": self.ui.box_comparemethod_ts.currentText(),
          "conditionType": "TraderStanding",
          "dynamicLocale": False,
          "globalQuestCounterId": "",
          "id": self.id,
          "index": 0,
          "parentId": "",
          "target": self.parent.parent.traders[self.ui.box_trader_ts.currentText()],
          "value": local_value,
          "visibilityConditions": []
        }
    
    # Add to task list and close self out
    # remove conditions with the same id, if they already exist in GUI or internal datastructs

    self.parent.parent.reset_by_id(self.id)
    table = self.parent.ui.tb_cond
    for i in range(table.rowCount()):
      if str(self.id) in table.item(i, 0).text():#row,column
        table.removeRow(i)
        break
    # ConditionFinish, ConditionStart, ConditionFail
    self.parent.parent.add_table_field(f"Condition{timing}", self.parent.ui.tb_cond, self.id, {0: self.id, 1: timing, 2: cond_type}, cond)
    # clear the list, since we're exported and done with it, if we need to load, we will do it from the JSON object itself
    self.parent.parent.reset_by_key(cond_type)
    if cond_type == "CounterCreator": # we also need to clear all the subfields, if they were used, if it's cc
      for c in ["VisitPlace", "Kills", "ExitStatus", "ExitName", "Location"]:
        self.parent.parent.reset_by_key(c)
    self.close()

  def load_settings_from_dict(self, settings, condition_timing):
        print(f"Loading condition from dict: {settings}")
        self.id = settings["id"]
        self.ui.fld_taskid_gen.setText(settings["id"]) # update the Cond ID field to match the import
        # first field is the JSON key
        # tuple is (item reference to set, type of item reference (determines func to set))
        condition_type = settings["conditionType"]
        # todo - more robust for rewards missing fields; need to build a better validator
        # doing just the unknown for now since it is missing in Legs' test json
        print(f"Cond type: {condition_type}, timing: {condition_timing}")

        for viscon in settings["visibilityConditions"]:
          self.parent.parent.add_table_field(f"VisibilityCond", self.ui.tb_vis, viscon, {0: viscon}, viscon)

        match condition_type:
          case "CounterCreator":
            # Editing a CC condition doesn't really do much as implemented because there is no edit CC subtask yet
            # TODO: Add edit subtask for CC
            self.ui.tabWidget.setCurrentIndex(0)
            for cc_item in settings["counter"]["conditions"]:
              self.parent.parent.add_table_field(f"CounterCreator", self.ui.tb_cc, cc_item["id"], {0: cc_item["id"], 1: cc_item["conditionType"]}, cc_item)
          case "FindItem" | "HandoverItem":
            self.ui.tabWidget.setCurrentIndex(1)
            self.ui.box_hofind_it.setCurrentText(condition_type)
            self.ui.box_only_fir_it.setCurrentText(str(settings["onlyFoundInRaid"]).lower())
            self.ui.box_ff_it.setCurrentText(condition_timing)
            self.ui.fld_dogtaglev_it.setText(str(settings["dogtagLevel"]))
            self.ui.fld_parentid_it.setText(settings["parentId"])
            self.ui.fld_maxdur_it.setText(str(settings["maxDurability"]))
            self.ui.fld_mindur_it.setText(str(settings["minDurability"]))
            self.ui.fld_quantity_it.setText(str(settings["value"]))
            for itemid in settings["target"]:
              self.parent.parent.add_table_field(f"HFItems", self.ui.tb_items, itemid, {0: itemid}, itemid)
          case "Skill":
            self.ui.tabWidget.setCurrentIndex(2)
            self.ui.box_compare_sk.setCurrentText(settings["compareMethod"])
            self.ui.box_target_sk.setCurrentText(settings["target"])
            self.ui.box_ff_sk.setCurrentText(condition_timing)
            self.ui.fld_level_sk.setText(str(settings["value"]))
            self.ui.fld_parentid_sk_2.setText(settings["parentId"])
          case "LeaveItemAtLocation":
            self.ui.tabWidget.setCurrentIndex(3)
            self.ui.box_fir_li.setCurrentText(str(settings["onlyFoundInRaid"]).lower())
            self.ui.box_ff_li.setCurrentText(condition_timing)
            self.ui.fld_zoneid_li.setText(settings["zoneId"])
            self.ui.fld_dogtaglevel_li.setText(str(settings["dogtagLevel"]))
            self.ui.fld_mindur_li.setText(str(settings["minDurability"]))
            self.ui.fld_maxdur_li.setText(str(settings["maxDurability"]))
            self.ui.fld_plant_time_li.setText(str(settings["plantTime"]))
            self.ui.fld_quantity_li.setText(str(settings["value"]))
            self.ui.fld_parentid_li.setText(settings["parentId"])
            for tid in settings["target"]:
              self.parent.parent.add_table_field(f"LeaveItemTarget", self.ui.tb_li_target, tid, {0: tid}, tid)
          case "WeaponAssembly":
            self.ui.tabWidget.setCurrentIndex(5)
            # TODO: Implement WeaponAssembly
          case "PlaceBeacon":
            self.ui.tabWidget.setCurrentIndex(4)
            self.ui.sb_time_pb.setValue(int(settings["plantTime"]))
            self.ui.sb_value_pb.setValue(int(settings["value"]))
            self.ui.fld_zoneid_pb.setText(settings["zoneId"])
            self.ui.fld_parentid_pb.setText(settings["parentId"])
            self.ui.box_ff_pb.setCurrentText(settings[condition_timing])
          case "TraderLoyalty":
            target_str = self.parent.parent.traders_invert[settings["target"]]
            self.ui.tabWidget.setCurrentIndex(6)
            self.ui.box_compare_tl.setCurrentText(settings["compareMethod"])
            self.ui.box_target_tl.setCurrentText(target_str)
            self.ui.box_ff_tl.setCurrentText(condition_timing)
            self.ui.fld_level_tl.setText(str(settings["value"]))
            self.ui.fld_parentid_tl.setText(settings["parentId"])
          case "Level":
            self.ui.tabWidget_2.setCurrentIndex(1)
            self.ui.tabWidget_3.setCurrentIndex(0)
            self.ui.box_compare_lv.setCurrentText(settings["compareMethod"])
            self.ui.fld_value_lv.setText(str(settings["value"]))
          case "Quest":
            self.ui.tabWidget_2.setCurrentIndex(1)
            self.ui.tabWidget_3.setCurrentIndex(1)
            self.ui.fld_avail_qs.setText(str(settings["availableAfter"]))
            self.ui.fld_tid_qs.setText(str(settings["target"]))
            for status in settings["status"]:
              str_status = self.parent.parent.status_invert[status]
              self.parent.parent.add_table_field(f"QStatus", self.ui.tb_status_qs, str_status, {0: str_status}, str_status)
          case "TraderStanding":
            trader = self.parent.parent.traders_invert[settings["target"]]
            self.ui.tabWidget_2.setCurrentIndex(1)
            self.ui.tabWidget_3.setCurrentIndex(2)
            self.ui.box_comparemethod_ts.setCurrentText(settings["compareMethod"])
            self.ui.box_trader_ts.setCurrentText(trader)
            self.ui.fld_value_ts.setText(settings["value"])

