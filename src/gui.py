import sys
import re
import json
from pymongo import MongoClient
from bson.objectid import ObjectId

from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import Qt, QRunnable
from PyQt6.QtWidgets import QApplication, QDialog, QMainWindow, QPushButton, QListView, QListWidget, QListWidgetItem

from gui_about import Ui_AboutMenu
from gui_main import Ui_MainGUI
from gui_updates import Ui_UpdateMenu
from gui_quests import Ui_QuestWindow
from gui_tasks import Ui_TaskWindow
from gui_assort import Ui_AssortBuilder

class Gui_MainWindow(QMainWindow):
  def __init__(self, parent=None):
    super().__init__(parent)
    self.ui = Ui_MainGUI()
    self.ui.setupUi(self)
    self.controller = None
    self.parent = parent
    self.ui.actionExit.triggered.connect(self.onExit)
    self.ui.actionView_Queued_Quests.triggered.connect(self.onViewQuests)
    self.ui.actionExport_Queued_Quests.triggered.connect(self.onExportQuests)
    self.ui.actionAdd_queued_to_open_list.triggered.connect(self.addOpenQuestsToList)
    self.traders = self.importJson("data\\traders.json")
    self.weapons = self.importJson("data\weapons.json")
    self.quests = {}

  def importJson(self, path):
    with open(path, "r") as f:
      out = json.load(f)
      return out
  
  def addOpenQuestsToList(self):
    select = self.ui.questList.selectedItems()
    print(select[0].text())

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

  def onViewQuests(self):
    self.popup(message=f"The following quests are queued for export: {[q['QuestName'] for q in self.quests.values()]}")

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
    exportFile = 'data\quest.json'
    with open(exportFile, 'w') as f:
      try:
        out = json.dumps(quest, indent=4).strip('[]\n')
        f.write(out)
        f.close()
        self.popup(message=f"The export has completed successfully and can be found at {exportFile}.")
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

class Gui_QuestDlg(QMainWindow):
  def __init__(self, parent=None, _controller=None):
    super().__init__(parent)
    self.ui = Ui_QuestWindow()
    self.ui.setupUi(self)
    self.parent = parent
    self.on_launch() # Custom code in this one
    self.show()
  
  def on_launch(self):
    self.ui.pb_add_task.released.connect(lambda: Gui_TaskDlg(parent=self))
    self.ui.pb_finalize_quest.released.connect(self.finalize)
    self.setup_box_selections()
    self.setup_text_edit()

  def setup_box_selections(self):
    self.ui.box_avail_faction.addItems(self.parent.controller.qb_box_avail_faction)
    self.ui.box_quest_type_label.addItems(self.parent.controller.qb_box_quest_type_label)
    self.ui.box_trader.addItems(self.parent.traders.keys())
    self.ui.box_location.addItems(self.parent.controller.qb_box_location)
    self.ui.box_can_show_notif.addItems(self.parent.controller.qb_box_can_show_notif)
    self.ui.box_insta_complete.addItems(self.parent.controller.qb_box_insta_complete)
    self.ui.box_restartable.addItems(self.parent.controller.qb_box_restartable)
    self.ui.box_secret_quest.addItems(self.parent.controller.qb_box_secret_quest)
    self.ui.box_reward.addItems(self.parent.controller.qb_box_reward)
    self.ui.box_status.addItems(self.parent.controller.qb_box_status)
    self.ui.box_traderid.addItems(self.parent.traders.keys())
    self.ui.box_fir.addItems(self.parent.controller.qb_box_fir)
  
  def setup_text_edit(self):
    self.ui.qb_locale_box.setPlainText(self.parent.controller.qb_locale_box)

  def finalize(self):
    quest_id = str(ObjectId())
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
      "image": "/files/quest/icon/" + self.ui.fld_image_name.displayText(),
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
      "traderId": self.parent.traders[self.ui.box_traderid.currentText()],
      "type": self.ui.box_quest_type_label.currentText()
      }
    }
    
    print(f"Added quest: {quest}")
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
    self.ui.box_only_fir.addItems(self.parent.parent.controller.tb_handover_box_only_fir)
    self.ui.box_one_session.addItems(self.parent.parent.controller.tb_visitzone_box_one_session)
    self.ui.box_fir.addItems(self.parent.parent.controller.tb_leaveitem_box_fir)
    self.ui.traderloyalty_compare_box.addItems(self.parent.parent.controller.tb_traderloyalty_compare_box)
    self.ui.traderloyalt_target_box.addItems(self.parent.parent.controller.tb_traderloyalt_target_box)
    self.ui.traderloyalty_level.addItems(self.parent.parent.controller.tb_traderloyalty_level)
    self.ui.skillreq_compare_box.addItems(self.parent.parent.controller.tb_skillreq_compare_box)
    self.ui.skillreq_target_box.addItems(self.parent.parent.controller.tb_skillreq_target_box)
    self.ui.exitstatus_status_box.addItems(self.parent.parent.controller.tb_exitstatus_status_box)
    self.ui.exitstatus_name_box.addItems(self.parent.parent.controller.tb_exitstatus_name_box)

  def setup_text_edit(self):
    self.ui.elim_locale_box.setPlainText(self.parent.parent.controller.tb_elim_locale_box)
    self.ui.handover_locale_box.setPlainText(self.parent.parent.controller.tb_handover_locale_box)
    self.ui.visitzone_locale_box.setPlainText(self.parent.parent.controller.tb_visitzone_locale_box)
    self.ui.leaveitem_locale_box.setPlainText(self.parent.parent.controller.tb_leaveitem_locale_box)
    self.ui.leaveitem_locale_box.setPlainText(self.parent.parent.controller.tb_leaveitem_locale_box)
    self.ui.traderloyalty_locale_box.setPlainText(self.parent.parent.controller.tb_traderloyalty_locale_box)
    self.ui.skillreq_locale_box.setPlainText(self.parent.parent.controller.tb_exitstatus_locale_box)
    self.ui.exitstatus_locale_box.setPlainText(self.parent.parent.controller.tb_skillreq_locale_box)