# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'gui_quests.ui'
##
## Created by: Qt User Interface Compiler version 6.6.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QFormLayout,
    QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMainWindow, QMenu,
    QMenuBar, QPlainTextEdit, QPushButton, QSizePolicy,
    QSpacerItem, QStatusBar, QTabWidget, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_QuestWindow(object):
    def setupUi(self, QuestWindow):
        if not QuestWindow.objectName():
            QuestWindow.setObjectName(u"QuestWindow")
        QuestWindow.resize(775, 760)
        self.actionHome = QAction(QuestWindow)
        self.actionHome.setObjectName(u"actionHome")
        self.centralwidget = QWidget(QuestWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralwidget.setEnabled(True)
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.tabs_quest = QTabWidget(self.centralwidget)
        self.tabs_quest.setObjectName(u"tabs_quest")
        self.tab_quest = QWidget()
        self.tab_quest.setObjectName(u"tab_quest")
        self.tab_quest.setMinimumSize(QSize(720, 630))
        self.gridLayoutWidget = QWidget(self.tab_quest)
        self.gridLayoutWidget.setObjectName(u"gridLayoutWidget")
        self.gridLayoutWidget.setGeometry(QRect(9, 9, 331, 351))
        self.grd_fields_1 = QGridLayout(self.gridLayoutWidget)
        self.grd_fields_1.setObjectName(u"grd_fields_1")
        self.grd_fields_1.setContentsMargins(0, 0, 0, 0)
        self.lb_secret_quest = QLabel(self.gridLayoutWidget)
        self.lb_secret_quest.setObjectName(u"lb_secret_quest")

        self.grd_fields_1.addWidget(self.lb_secret_quest, 10, 0, 1, 1)

        self.box_secret_quest = QComboBox(self.gridLayoutWidget)
        self.box_secret_quest.setObjectName(u"box_secret_quest")

        self.grd_fields_1.addWidget(self.box_secret_quest, 10, 1, 1, 1)

        self.lb_questname = QLabel(self.gridLayoutWidget)
        self.lb_questname.setObjectName(u"lb_questname")

        self.grd_fields_1.addWidget(self.lb_questname, 0, 0, 1, 1)

        self.fld_quest_name = QLineEdit(self.gridLayoutWidget)
        self.fld_quest_name.setObjectName(u"fld_quest_name")

        self.grd_fields_1.addWidget(self.fld_quest_name, 0, 1, 1, 1)

        self.box_insta_complete = QComboBox(self.gridLayoutWidget)
        self.box_insta_complete.setObjectName(u"box_insta_complete")

        self.grd_fields_1.addWidget(self.box_insta_complete, 8, 1, 1, 1)

        self.lb_insta_complete = QLabel(self.gridLayoutWidget)
        self.lb_insta_complete.setObjectName(u"lb_insta_complete")

        self.grd_fields_1.addWidget(self.lb_insta_complete, 8, 0, 1, 1)

        self.lb_defaultvalues = QLabel(self.gridLayoutWidget)
        self.lb_defaultvalues.setObjectName(u"lb_defaultvalues")

        self.grd_fields_1.addWidget(self.lb_defaultvalues, 6, 0, 1, 1)

        self.fld_image_name = QLineEdit(self.gridLayoutWidget)
        self.fld_image_name.setObjectName(u"fld_image_name")

        self.grd_fields_1.addWidget(self.fld_image_name, 5, 1, 1, 1)

        self.lb_location = QLabel(self.gridLayoutWidget)
        self.lb_location.setObjectName(u"lb_location")

        self.grd_fields_1.addWidget(self.lb_location, 4, 0, 1, 1)

        self.box_avail_faction = QComboBox(self.gridLayoutWidget)
        self.box_avail_faction.setObjectName(u"box_avail_faction")

        self.grd_fields_1.addWidget(self.box_avail_faction, 1, 1, 1, 1)

        self.lb_trader = QLabel(self.gridLayoutWidget)
        self.lb_trader.setObjectName(u"lb_trader")

        self.grd_fields_1.addWidget(self.lb_trader, 3, 0, 1, 1)

        self.lb_quest_type_label = QLabel(self.gridLayoutWidget)
        self.lb_quest_type_label.setObjectName(u"lb_quest_type_label")

        self.grd_fields_1.addWidget(self.lb_quest_type_label, 2, 0, 1, 1)

        self.box_quest_type_label = QComboBox(self.gridLayoutWidget)
        self.box_quest_type_label.setObjectName(u"box_quest_type_label")

        self.grd_fields_1.addWidget(self.box_quest_type_label, 2, 1, 1, 1)

        self.lb_imagename = QLabel(self.gridLayoutWidget)
        self.lb_imagename.setObjectName(u"lb_imagename")

        self.grd_fields_1.addWidget(self.lb_imagename, 5, 0, 1, 1)

        self.box_location = QComboBox(self.gridLayoutWidget)
        self.box_location.setObjectName(u"box_location")

        self.grd_fields_1.addWidget(self.box_location, 4, 1, 1, 1)

        self.lb_can_show_notif = QLabel(self.gridLayoutWidget)
        self.lb_can_show_notif.setObjectName(u"lb_can_show_notif")

        self.grd_fields_1.addWidget(self.lb_can_show_notif, 7, 0, 1, 1)

        self.lb_avail_faction = QLabel(self.gridLayoutWidget)
        self.lb_avail_faction.setObjectName(u"lb_avail_faction")

        self.grd_fields_1.addWidget(self.lb_avail_faction, 1, 0, 1, 1)

        self.box_trader = QComboBox(self.gridLayoutWidget)
        self.box_trader.setObjectName(u"box_trader")

        self.grd_fields_1.addWidget(self.box_trader, 3, 1, 1, 1)

        self.box_can_show_notif = QComboBox(self.gridLayoutWidget)
        self.box_can_show_notif.setObjectName(u"box_can_show_notif")

        self.grd_fields_1.addWidget(self.box_can_show_notif, 7, 1, 1, 1)

        self.lb_restartable = QLabel(self.gridLayoutWidget)
        self.lb_restartable.setObjectName(u"lb_restartable")

        self.grd_fields_1.addWidget(self.lb_restartable, 9, 0, 1, 1)

        self.box_restartable = QComboBox(self.gridLayoutWidget)
        self.box_restartable.setObjectName(u"box_restartable")

        self.grd_fields_1.addWidget(self.box_restartable, 9, 1, 1, 1)

        self.gridLayoutWidget_3 = QWidget(self.tab_quest)
        self.gridLayoutWidget_3.setObjectName(u"gridLayoutWidget_3")
        self.gridLayoutWidget_3.setGeometry(QRect(10, 570, 348, 51))
        self.grd_fields_3 = QGridLayout(self.gridLayoutWidget_3)
        self.grd_fields_3.setObjectName(u"grd_fields_3")
        self.grd_fields_3.setContentsMargins(0, 0, 0, 0)
        self.pb_rem_task = QPushButton(self.gridLayoutWidget_3)
        self.pb_rem_task.setObjectName(u"pb_rem_task")

        self.grd_fields_3.addWidget(self.pb_rem_task, 0, 1, 1, 1)

        self.pb_add_task = QPushButton(self.gridLayoutWidget_3)
        self.pb_add_task.setObjectName(u"pb_add_task")

        self.grd_fields_3.addWidget(self.pb_add_task, 0, 0, 1, 1)

        self.gridLayoutWidget_4 = QWidget(self.tab_quest)
        self.gridLayoutWidget_4.setObjectName(u"gridLayoutWidget_4")
        self.gridLayoutWidget_4.setGeometry(QRect(370, 190, 341, 51))
        self.grd_fields_4 = QGridLayout(self.gridLayoutWidget_4)
        self.grd_fields_4.setObjectName(u"grd_fields_4")
        self.grd_fields_4.setContentsMargins(0, 0, 0, 0)
        self.pb_add_reward = QPushButton(self.gridLayoutWidget_4)
        self.pb_add_reward.setObjectName(u"pb_add_reward")

        self.grd_fields_4.addWidget(self.pb_add_reward, 0, 0, 1, 1)

        self.pb_remove_reward = QPushButton(self.gridLayoutWidget_4)
        self.pb_remove_reward.setObjectName(u"pb_remove_reward")

        self.grd_fields_4.addWidget(self.pb_remove_reward, 0, 1, 1, 1)

        self.label_2 = QLabel(self.tab_quest)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(370, 10, 61, 16))
        self.label_3 = QLabel(self.tab_quest)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(10, 390, 49, 16))
        self.tb_rewards = QTableWidget(self.tab_quest)
        if (self.tb_rewards.columnCount() < 3):
            self.tb_rewards.setColumnCount(3)
        __qtablewidgetitem = QTableWidgetItem()
        self.tb_rewards.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tb_rewards.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.tb_rewards.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        self.tb_rewards.setObjectName(u"tb_rewards")
        self.tb_rewards.setGeometry(QRect(370, 40, 341, 141))
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tb_rewards.sizePolicy().hasHeightForWidth())
        self.tb_rewards.setSizePolicy(sizePolicy)
        self.tb_rewards.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tb_cond = QTableWidget(self.tab_quest)
        if (self.tb_cond.columnCount() < 3):
            self.tb_cond.setColumnCount(3)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.tb_cond.setHorizontalHeaderItem(0, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.tb_cond.setHorizontalHeaderItem(1, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.tb_cond.setHorizontalHeaderItem(2, __qtablewidgetitem5)
        self.tb_cond.setObjectName(u"tb_cond")
        self.tb_cond.setGeometry(QRect(10, 410, 341, 151))
        self.tb_cond.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabs_quest.addTab(self.tab_quest, "")
        self.tab_locale = QWidget()
        self.tab_locale.setObjectName(u"tab_locale")
        self.verticalLayout_locale = QVBoxLayout(self.tab_locale)
        self.verticalLayout_locale.setObjectName(u"verticalLayout_locale")
        self.grp_quest_text = QGroupBox(self.tab_locale)
        self.grp_quest_text.setObjectName(u"grp_quest_text")
        self.form_quest_text = QFormLayout(self.grp_quest_text)
        self.form_quest_text.setObjectName(u"form_quest_text")
        self.lb_loc_name = QLabel(self.grp_quest_text)
        self.lb_loc_name.setObjectName(u"lb_loc_name")

        self.form_quest_text.setWidget(0, QFormLayout.LabelRole, self.lb_loc_name)

        self.fld_loc_name = QLineEdit(self.grp_quest_text)
        self.fld_loc_name.setObjectName(u"fld_loc_name")

        self.form_quest_text.setWidget(0, QFormLayout.FieldRole, self.fld_loc_name)

        self.lb_loc_note = QLabel(self.grp_quest_text)
        self.lb_loc_note.setObjectName(u"lb_loc_note")

        self.form_quest_text.setWidget(1, QFormLayout.LabelRole, self.lb_loc_note)

        self.fld_loc_note = QLineEdit(self.grp_quest_text)
        self.fld_loc_note.setObjectName(u"fld_loc_note")

        self.form_quest_text.setWidget(1, QFormLayout.FieldRole, self.fld_loc_note)

        self.lb_loc_acceptPlayerMessage = QLabel(self.grp_quest_text)
        self.lb_loc_acceptPlayerMessage.setObjectName(u"lb_loc_acceptPlayerMessage")

        self.form_quest_text.setWidget(2, QFormLayout.LabelRole, self.lb_loc_acceptPlayerMessage)

        self.fld_loc_acceptPlayerMessage = QLineEdit(self.grp_quest_text)
        self.fld_loc_acceptPlayerMessage.setObjectName(u"fld_loc_acceptPlayerMessage")

        self.form_quest_text.setWidget(2, QFormLayout.FieldRole, self.fld_loc_acceptPlayerMessage)

        self.lb_loc_changeQuestMessageText = QLabel(self.grp_quest_text)
        self.lb_loc_changeQuestMessageText.setObjectName(u"lb_loc_changeQuestMessageText")

        self.form_quest_text.setWidget(3, QFormLayout.LabelRole, self.lb_loc_changeQuestMessageText)

        self.fld_loc_changeQuestMessageText = QLineEdit(self.grp_quest_text)
        self.fld_loc_changeQuestMessageText.setObjectName(u"fld_loc_changeQuestMessageText")

        self.form_quest_text.setWidget(3, QFormLayout.FieldRole, self.fld_loc_changeQuestMessageText)

        self.lb_loc_completePlayerMessage = QLabel(self.grp_quest_text)
        self.lb_loc_completePlayerMessage.setObjectName(u"lb_loc_completePlayerMessage")

        self.form_quest_text.setWidget(4, QFormLayout.LabelRole, self.lb_loc_completePlayerMessage)

        self.fld_loc_completePlayerMessage = QLineEdit(self.grp_quest_text)
        self.fld_loc_completePlayerMessage.setObjectName(u"fld_loc_completePlayerMessage")

        self.form_quest_text.setWidget(4, QFormLayout.FieldRole, self.fld_loc_completePlayerMessage)

        self.lb_loc_declinePlayerMessage = QLabel(self.grp_quest_text)
        self.lb_loc_declinePlayerMessage.setObjectName(u"lb_loc_declinePlayerMessage")

        self.form_quest_text.setWidget(5, QFormLayout.LabelRole, self.lb_loc_declinePlayerMessage)

        self.fld_loc_declinePlayerMessage = QLineEdit(self.grp_quest_text)
        self.fld_loc_declinePlayerMessage.setObjectName(u"fld_loc_declinePlayerMessage")

        self.form_quest_text.setWidget(5, QFormLayout.FieldRole, self.fld_loc_declinePlayerMessage)

        self.lb_loc_description = QLabel(self.grp_quest_text)
        self.lb_loc_description.setObjectName(u"lb_loc_description")

        self.form_quest_text.setWidget(6, QFormLayout.LabelRole, self.lb_loc_description)

        self.fld_loc_description = QPlainTextEdit(self.grp_quest_text)
        self.fld_loc_description.setObjectName(u"fld_loc_description")
        self.fld_loc_description.setMinimumSize(QSize(0, 80))
        self.fld_loc_description.setMaximumSize(QSize(16777215, 80))
        self.fld_loc_description.setTabChangesFocus(True)

        self.form_quest_text.setWidget(6, QFormLayout.FieldRole, self.fld_loc_description)

        self.lb_loc_failMessageText = QLabel(self.grp_quest_text)
        self.lb_loc_failMessageText.setObjectName(u"lb_loc_failMessageText")

        self.form_quest_text.setWidget(7, QFormLayout.LabelRole, self.lb_loc_failMessageText)

        self.fld_loc_failMessageText = QLineEdit(self.grp_quest_text)
        self.fld_loc_failMessageText.setObjectName(u"fld_loc_failMessageText")

        self.form_quest_text.setWidget(7, QFormLayout.FieldRole, self.fld_loc_failMessageText)

        self.lb_loc_startedMessageText = QLabel(self.grp_quest_text)
        self.lb_loc_startedMessageText.setObjectName(u"lb_loc_startedMessageText")

        self.form_quest_text.setWidget(8, QFormLayout.LabelRole, self.lb_loc_startedMessageText)

        self.fld_loc_startedMessageText = QLineEdit(self.grp_quest_text)
        self.fld_loc_startedMessageText.setObjectName(u"fld_loc_startedMessageText")

        self.form_quest_text.setWidget(8, QFormLayout.FieldRole, self.fld_loc_startedMessageText)

        self.lb_loc_successMessageText = QLabel(self.grp_quest_text)
        self.lb_loc_successMessageText.setObjectName(u"lb_loc_successMessageText")

        self.form_quest_text.setWidget(9, QFormLayout.LabelRole, self.lb_loc_successMessageText)

        self.fld_loc_successMessageText = QLineEdit(self.grp_quest_text)
        self.fld_loc_successMessageText.setObjectName(u"fld_loc_successMessageText")

        self.form_quest_text.setWidget(9, QFormLayout.FieldRole, self.fld_loc_successMessageText)


        self.verticalLayout_locale.addWidget(self.grp_quest_text)

        self.grp_task_text = QGroupBox(self.tab_locale)
        self.grp_task_text.setObjectName(u"grp_task_text")
        self.verticalLayout_task_text = QVBoxLayout(self.grp_task_text)
        self.verticalLayout_task_text.setObjectName(u"verticalLayout_task_text")
        self.lb_task_text_help = QLabel(self.grp_task_text)
        self.lb_task_text_help.setObjectName(u"lb_task_text_help")
        self.lb_task_text_help.setWordWrap(True)

        self.verticalLayout_task_text.addWidget(self.lb_task_text_help)

        self.tb_cond_locale = QTableWidget(self.grp_task_text)
        if (self.tb_cond_locale.columnCount() < 4):
            self.tb_cond_locale.setColumnCount(4)
        __qtablewidgetitem6 = QTableWidgetItem()
        self.tb_cond_locale.setHorizontalHeaderItem(0, __qtablewidgetitem6)
        __qtablewidgetitem7 = QTableWidgetItem()
        self.tb_cond_locale.setHorizontalHeaderItem(1, __qtablewidgetitem7)
        __qtablewidgetitem8 = QTableWidgetItem()
        self.tb_cond_locale.setHorizontalHeaderItem(2, __qtablewidgetitem8)
        __qtablewidgetitem9 = QTableWidgetItem()
        self.tb_cond_locale.setHorizontalHeaderItem(3, __qtablewidgetitem9)
        self.tb_cond_locale.setObjectName(u"tb_cond_locale")
        self.tb_cond_locale.horizontalHeader().setStretchLastSection(True)
        self.tb_cond_locale.verticalHeader().setVisible(False)

        self.verticalLayout_task_text.addWidget(self.tb_cond_locale)


        self.verticalLayout_locale.addWidget(self.grp_task_text)

        self.tabs_quest.addTab(self.tab_locale, "")

        self.verticalLayout.addWidget(self.tabs_quest)

        self.horizontalLayout_finalize = QHBoxLayout()
        self.horizontalLayout_finalize.setObjectName(u"horizontalLayout_finalize")
        self.pb_finalize_quest = QPushButton(self.centralwidget)
        self.pb_finalize_quest.setObjectName(u"pb_finalize_quest")

        self.horizontalLayout_finalize.addWidget(self.pb_finalize_quest)

        self.horizontalSpacer_finalize = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_finalize.addItem(self.horizontalSpacer_finalize)


        self.verticalLayout.addLayout(self.horizontalLayout_finalize)

        QuestWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(QuestWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 775, 22))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        QuestWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(QuestWindow)
        self.statusbar.setObjectName(u"statusbar")
        QuestWindow.setStatusBar(self.statusbar)
#if QT_CONFIG(shortcut)
        self.lb_loc_name.setBuddy(self.fld_loc_name)
        self.lb_loc_note.setBuddy(self.fld_loc_note)
        self.lb_loc_acceptPlayerMessage.setBuddy(self.fld_loc_acceptPlayerMessage)
        self.lb_loc_changeQuestMessageText.setBuddy(self.fld_loc_changeQuestMessageText)
        self.lb_loc_completePlayerMessage.setBuddy(self.fld_loc_completePlayerMessage)
        self.lb_loc_declinePlayerMessage.setBuddy(self.fld_loc_declinePlayerMessage)
        self.lb_loc_description.setBuddy(self.fld_loc_description)
        self.lb_loc_failMessageText.setBuddy(self.fld_loc_failMessageText)
        self.lb_loc_startedMessageText.setBuddy(self.fld_loc_startedMessageText)
        self.lb_loc_successMessageText.setBuddy(self.fld_loc_successMessageText)
#endif // QT_CONFIG(shortcut)

        self.menubar.addAction(self.menuFile.menuAction())

        self.retranslateUi(QuestWindow)

        self.tabs_quest.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(QuestWindow)
    # setupUi

    def retranslateUi(self, QuestWindow):
        QuestWindow.setWindowTitle(QCoreApplication.translate("QuestWindow", u"Quest Builder", None))
        self.actionHome.setText(QCoreApplication.translate("QuestWindow", u"Home", None))
        self.lb_secret_quest.setText(QCoreApplication.translate("QuestWindow", u"Secret Quest", None))
        self.lb_questname.setText(QCoreApplication.translate("QuestWindow", u"Quest Name", None))
        self.lb_insta_complete.setText(QCoreApplication.translate("QuestWindow", u"Insta-complete", None))
        self.lb_defaultvalues.setText(QCoreApplication.translate("QuestWindow", u"<html><head/><body><p><span style=\" text-decoration: underline;\">Default Values</span></p></body></html>", None))
        self.fld_image_name.setText("")
        self.lb_location.setText(QCoreApplication.translate("QuestWindow", u"Location", None))
        self.lb_trader.setText(QCoreApplication.translate("QuestWindow", u"Trader", None))
        self.lb_quest_type_label.setText(QCoreApplication.translate("QuestWindow", u"Quest Type Label", None))
        self.lb_imagename.setText(QCoreApplication.translate("QuestWindow", u"Image Name", None))
        self.lb_can_show_notif.setText(QCoreApplication.translate("QuestWindow", u"canShowNotificationsInGame", None))
        self.lb_avail_faction.setText(QCoreApplication.translate("QuestWindow", u"Available for Factions", None))
        self.lb_restartable.setText(QCoreApplication.translate("QuestWindow", u"Restartable", None))
        self.pb_rem_task.setText(QCoreApplication.translate("QuestWindow", u"Remove Task", None))
        self.pb_add_task.setText(QCoreApplication.translate("QuestWindow", u"Add Task (launch menu)", None))
        self.pb_add_reward.setText(QCoreApplication.translate("QuestWindow", u" Add Reward (launch menu)", None))
        self.pb_remove_reward.setText(QCoreApplication.translate("QuestWindow", u"Remove Reward", None))
        self.label_2.setText(QCoreApplication.translate("QuestWindow", u"Rewards:", None))
        self.label_3.setText(QCoreApplication.translate("QuestWindow", u"Tasks:", None))
        ___qtablewidgetitem = self.tb_rewards.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("QuestWindow", u"id", None));
        ___qtablewidgetitem1 = self.tb_rewards.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("QuestWindow", u"timing", None));
        ___qtablewidgetitem2 = self.tb_rewards.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("QuestWindow", u"type", None));
        ___qtablewidgetitem3 = self.tb_cond.horizontalHeaderItem(0)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("QuestWindow", u"id", None));
        ___qtablewidgetitem4 = self.tb_cond.horizontalHeaderItem(1)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("QuestWindow", u"timing", None));
        ___qtablewidgetitem5 = self.tb_cond.horizontalHeaderItem(2)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("QuestWindow", u"type", None));
        self.tabs_quest.setTabText(self.tabs_quest.indexOf(self.tab_quest), QCoreApplication.translate("QuestWindow", u"Quest", None))
        self.grp_quest_text.setTitle(QCoreApplication.translate("QuestWindow", u"Quest text", None))
        self.lb_loc_name.setText(QCoreApplication.translate("QuestWindow", u"Name", None))
        self.lb_loc_note.setText(QCoreApplication.translate("QuestWindow", u"Note", None))
        self.lb_loc_acceptPlayerMessage.setText(QCoreApplication.translate("QuestWindow", u"Accept Player Message", None))
        self.lb_loc_changeQuestMessageText.setText(QCoreApplication.translate("QuestWindow", u"Change Quest Message Text", None))
        self.lb_loc_completePlayerMessage.setText(QCoreApplication.translate("QuestWindow", u"Complete Player Message", None))
        self.lb_loc_declinePlayerMessage.setText(QCoreApplication.translate("QuestWindow", u"Decline Player Message", None))
        self.lb_loc_description.setText(QCoreApplication.translate("QuestWindow", u"Description", None))
        self.lb_loc_failMessageText.setText(QCoreApplication.translate("QuestWindow", u"Fail Message Text", None))
        self.lb_loc_startedMessageText.setText(QCoreApplication.translate("QuestWindow", u"Started Message Text", None))
        self.lb_loc_successMessageText.setText(QCoreApplication.translate("QuestWindow", u"Success Message Text", None))
        self.grp_task_text.setTitle(QCoreApplication.translate("QuestWindow", u"Task text", None))
        self.lb_task_text_help.setText(QCoreApplication.translate("QuestWindow", u"The text shown in game for each task. Double-click a task's text to edit it.", None))
        ___qtablewidgetitem6 = self.tb_cond_locale.horizontalHeaderItem(0)
        ___qtablewidgetitem6.setText(QCoreApplication.translate("QuestWindow", u"id", None));
        ___qtablewidgetitem7 = self.tb_cond_locale.horizontalHeaderItem(1)
        ___qtablewidgetitem7.setText(QCoreApplication.translate("QuestWindow", u"timing", None));
        ___qtablewidgetitem8 = self.tb_cond_locale.horizontalHeaderItem(2)
        ___qtablewidgetitem8.setText(QCoreApplication.translate("QuestWindow", u"type", None));
        ___qtablewidgetitem9 = self.tb_cond_locale.horizontalHeaderItem(3)
        ___qtablewidgetitem9.setText(QCoreApplication.translate("QuestWindow", u"text", None));
        self.tabs_quest.setTabText(self.tabs_quest.indexOf(self.tab_locale), QCoreApplication.translate("QuestWindow", u"Locale", None))
        self.pb_finalize_quest.setText(QCoreApplication.translate("QuestWindow", u"Finalize Quest", None))
        self.menuFile.setTitle(QCoreApplication.translate("QuestWindow", u"File", None))
    # retranslateUi

