import sys
import re
import random
import csv
import os
import glob
from datetime import datetime

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

  def onAbout(self, ver_current, url_text):
    dlg = Gui_AboutDlg(self)
    dlg.updateAbout(ver_current, url_text)
    dlg.exec()

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
    self.setup_box_selections()

  def setup_box_selections(self):
    self.ui.box_avail_faction.addItems(self.parent.controller.qb_box_avail_faction)
    self.ui.box_quest_type_label.addItems(self.parent.controller.qb_box_quest_type_label)
    self.ui.box_trader.addItems(self.parent.controller.qb_box_trader)
    self.ui.box_location.addItems(self.parent.controller.qb_box_location)
    self.ui.box_can_show_notif.addItems(self.parent.controller.qb_box_can_show_notif)
    self.ui.box_insta_complete.addItems(self.parent.controller.qb_box_insta_complete)
    self.ui.box_restartable.addItems(self.parent.controller.qb_box_restartable)
    self.ui.box_secret_quest.addItems(self.parent.controller.qb_box_secret_quest)
    self.ui.box_reward.addItems(self.parent.controller.qb_box_reward)
    self.ui.box_status.addItems(self.parent.controller.qb_box_status)
    self.ui.box_traderid.addItems(self.parent.controller.qb_box_traderid)
    self.ui.box_fir.addItems(self.parent.controller.qb_box_fir)

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

  def setup_box_selections(self):
    self.ui.box_target.addItems(self.parent.parent.controller.tb_elim_box_target)
    self.ui.box_targetrole.addItems(self.parent.parent.controller.tb_elim_box_targetrole)
    self.ui.box_bodypart.addItems(self.parent.parent.controller.tb_elim_box_bodypart)
    self.ui.box_dist_compare.addItems(self.parent.parent.controller.tb_elim_box_dist_compare)
    self.ui.box_weapons.addItems(self.parent.parent.controller.tb_elim_box_weapons)
    self.ui.box_cond_type.addItems(self.parent.parent.controller.tb_handover_box_cond_type)
    self.ui.box_only_fir.addItems(self.parent.parent.controller.tb_handover_box_only_fir)
    self.ui.box_one_session.addItems(self.parent.parent.controller.tb_visitzone_box_one_session)
    self.ui.box_fir.addItems(self.parent.parent.controller.tb_leaveitem_box_fir)
