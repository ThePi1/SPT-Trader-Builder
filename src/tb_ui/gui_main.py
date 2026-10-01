# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'gui_main.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QAbstractScrollArea, QApplication, QCheckBox,
    QComboBox, QGridLayout, QHeaderView, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
    QMenu, QMenuBar, QPushButton, QSizePolicy,
    QStatusBar, QTabWidget, QTableWidget, QTableWidgetItem,
    QTreeView, QWidget)

class Ui_MainGUI(object):
    def setupUi(self, MainGUI):
        if not MainGUI.objectName():
            MainGUI.setObjectName(u"MainGUI")
        MainGUI.setWindowModality(Qt.NonModal)
        MainGUI.setEnabled(True)
        MainGUI.resize(874, 612)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainGUI.sizePolicy().hasHeightForWidth())
        MainGUI.setSizePolicy(sizePolicy)
        MainGUI.setMinimumSize(QSize(0, 0))
        MainGUI.setMaximumSize(QSize(1080, 720))
        icon = QIcon()
        icon.addFile(u"data/icon.ico", QSize(), QIcon.Normal, QIcon.Off)
        MainGUI.setWindowIcon(icon)
        MainGUI.setTabShape(QTabWidget.Rounded)
        self.actionAbout = QAction(MainGUI)
        self.actionAbout.setObjectName(u"actionAbout")
        self.actionSettingsMenu = QAction(MainGUI)
        self.actionSettingsMenu.setObjectName(u"actionSettingsMenu")
        self.actionSettingsMenu.setEnabled(True)
        self.actionExit = QAction(MainGUI)
        self.actionExit.setObjectName(u"actionExit")
        self.actionUpdateCheck = QAction(MainGUI)
        self.actionUpdateCheck.setObjectName(u"actionUpdateCheck")
        self.actionQuest_Builder = QAction(MainGUI)
        self.actionQuest_Builder.setObjectName(u"actionQuest_Builder")
        self.actionAssort_Builder = QAction(MainGUI)
        self.actionAssort_Builder.setObjectName(u"actionAssort_Builder")
        self.actionLocale_Builder = QAction(MainGUI)
        self.actionLocale_Builder.setObjectName(u"actionLocale_Builder")
        self.actionExport_Queued_Quests = QAction(MainGUI)
        self.actionExport_Queued_Quests.setObjectName(u"actionExport_Queued_Quests")
        self.actionView_Queued_Quests = QAction(MainGUI)
        self.actionView_Queued_Quests.setObjectName(u"actionView_Queued_Quests")
        self.actionAdd_queued_to_open_list = QAction(MainGUI)
        self.actionAdd_queued_to_open_list.setObjectName(u"actionAdd_queued_to_open_list")
        self.actionImport_Quests = QAction(MainGUI)
        self.actionImport_Quests.setObjectName(u"actionImport_Quests")
        self.actionRemove_Selected_Quest = QAction(MainGUI)
        self.actionRemove_Selected_Quest.setObjectName(u"actionRemove_Selected_Quest")
        self.actionAnalyze_CC_subtypes = QAction(MainGUI)
        self.actionAnalyze_CC_subtypes.setObjectName(u"actionAnalyze_CC_subtypes")
        self.actionCreate_locale_from_Quest_JSON = QAction(MainGUI)
        self.actionCreate_locale_from_Quest_JSON.setObjectName(u"actionCreate_locale_from_Quest_JSON")
        self.actionLoad_items_json_for_below = QAction(MainGUI)
        self.actionLoad_items_json_for_below.setObjectName(u"actionLoad_items_json_for_below")
        self.actionGet_all_children_of_parent_ID = QAction(MainGUI)
        self.actionGet_all_children_of_parent_ID.setObjectName(u"actionGet_all_children_of_parent_ID")
        self.actionEdit_Tracked_Data_Files_locale_quest = QAction(MainGUI)
        self.actionEdit_Tracked_Data_Files_locale_quest.setObjectName(u"actionEdit_Tracked_Data_Files_locale_quest")
        self.centralwidget = QWidget(MainGUI)
        self.centralwidget.setObjectName(u"centralwidget")
        sizePolicy1 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy1)
        self.main_tab = QTabWidget(self.centralwidget)
        self.main_tab.setObjectName(u"main_tab")
        self.main_tab.setGeometry(QRect(0, 0, 861, 561))
        font = QFont()
        font.setFamilies([u"Segoe UI"])
        self.main_tab.setFont(font)
        self.quest_tab = QWidget()
        self.quest_tab.setObjectName(u"quest_tab")
        self.questList = QListWidget(self.quest_tab)
        self.questList.setObjectName(u"questList")
        self.questList.setGeometry(QRect(10, 50, 831, 471))
        self.questList.setFont(font)
        self.questList.setFocusPolicy(Qt.NoFocus)
        self.questList.setWordWrap(False)
        self.gridLayoutWidget = QWidget(self.quest_tab)
        self.gridLayoutWidget.setObjectName(u"gridLayoutWidget")
        self.gridLayoutWidget.setGeometry(QRect(10, 10, 831, 31))
        self.gridLayout = QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setHorizontalSpacing(27)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.label_4 = QLabel(self.gridLayoutWidget)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout.addWidget(self.label_4, 0, 1, 1, 1)

        self.label = QLabel(self.gridLayoutWidget)
        self.label.setObjectName(u"label")
        sizePolicy2 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy2)
        self.label.setMinimumSize(QSize(200, 0))
        font1 = QFont()
        font1.setFamilies([u"Segoe UI"])
        font1.setPointSize(9)
        self.label.setFont(font1)

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.label_5 = QLabel(self.gridLayoutWidget)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout.addWidget(self.label_5, 0, 3, 1, 1)

        self.questsearch = QLineEdit(self.gridLayoutWidget)
        self.questsearch.setObjectName(u"questsearch")

        self.gridLayout.addWidget(self.questsearch, 0, 2, 1, 1)

        self.main_tab.addTab(self.quest_tab, "")
        self.wb_tab = QWidget()
        self.wb_tab.setObjectName(u"wb_tab")
        self.wb_treeview = QTreeView(self.wb_tab)
        self.wb_treeview.setObjectName(u"wb_treeview")
        self.wb_treeview.setGeometry(QRect(10, 30, 491, 501))
        self.gridLayoutWidget_5 = QWidget(self.wb_tab)
        self.gridLayoutWidget_5.setObjectName(u"gridLayoutWidget_5")
        self.gridLayoutWidget_5.setGeometry(QRect(510, 0, 341, 521))
        self.gridLayout_5 = QGridLayout(self.gridLayoutWidget_5)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.gridLayout_5.setContentsMargins(0, 0, 0, 0)
        self.wb_removepart_button = QPushButton(self.gridLayoutWidget_5)
        self.wb_removepart_button.setObjectName(u"wb_removepart_button")

        self.gridLayout_5.addWidget(self.wb_removepart_button, 6, 0, 1, 1)

        self.wb_itemid_edit = QLineEdit(self.gridLayoutWidget_5)
        self.wb_itemid_edit.setObjectName(u"wb_itemid_edit")

        self.gridLayout_5.addWidget(self.wb_itemid_edit, 2, 1, 1, 1)

        self.label_2 = QLabel(self.gridLayoutWidget_5)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout_5.addWidget(self.label_2, 2, 0, 1, 1)

        self.wb_modslot = QLabel(self.gridLayoutWidget_5)
        self.wb_modslot.setObjectName(u"wb_modslot")

        self.gridLayout_5.addWidget(self.wb_modslot, 4, 0, 1, 1)

        self.wb_parentId_edit = QLineEdit(self.gridLayoutWidget_5)
        self.wb_parentId_edit.setObjectName(u"wb_parentId_edit")

        self.gridLayout_5.addWidget(self.wb_parentId_edit, 3, 1, 1, 1)

        self.wb_addpart_button = QPushButton(self.gridLayoutWidget_5)
        self.wb_addpart_button.setObjectName(u"wb_addpart_button")

        self.gridLayout_5.addWidget(self.wb_addpart_button, 5, 0, 1, 1)

        self.wb_modslot_combo = QComboBox(self.gridLayoutWidget_5)
        self.wb_modslot_combo.setObjectName(u"wb_modslot_combo")

        self.gridLayout_5.addWidget(self.wb_modslot_combo, 4, 1, 1, 1)

        self.wb_base_check = QCheckBox(self.gridLayoutWidget_5)
        self.wb_base_check.setObjectName(u"wb_base_check")

        self.gridLayout_5.addWidget(self.wb_base_check, 0, 0, 1, 1)

        self.wb_parentid = QLabel(self.gridLayoutWidget_5)
        self.wb_parentid.setObjectName(u"wb_parentid")

        self.gridLayout_5.addWidget(self.wb_parentid, 3, 0, 1, 1)

        self.wb_weaponname = QLabel(self.gridLayoutWidget_5)
        self.wb_weaponname.setObjectName(u"wb_weaponname")

        self.gridLayout_5.addWidget(self.wb_weaponname, 1, 0, 1, 1)

        self.wb_weaponname_edit = QLineEdit(self.gridLayoutWidget_5)
        self.wb_weaponname_edit.setObjectName(u"wb_weaponname_edit")

        self.gridLayout_5.addWidget(self.wb_weaponname_edit, 1, 1, 1, 1)

        self.label_3 = QLabel(self.wb_tab)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(10, 10, 111, 16))
        self.label_3.setFont(font1)
        self.main_tab.addTab(self.wb_tab, "")
        self.locale_tab = QWidget()
        self.locale_tab.setObjectName(u"locale_tab")
        self.main_tab.addTab(self.locale_tab, "")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.gridLayoutWidget_2 = QWidget(self.tab)
        self.gridLayoutWidget_2.setObjectName(u"gridLayoutWidget_2")
        self.gridLayoutWidget_2.setGeometry(QRect(10, 10, 831, 31))
        self.gridLayout_2 = QGridLayout(self.gridLayoutWidget_2)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setHorizontalSpacing(27)
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.fld_idlookup = QLineEdit(self.gridLayoutWidget_2)
        self.fld_idlookup.setObjectName(u"fld_idlookup")

        self.gridLayout_2.addWidget(self.fld_idlookup, 0, 1, 1, 1)

        self.label_6 = QLabel(self.gridLayoutWidget_2)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout_2.addWidget(self.label_6, 0, 0, 1, 1)

        self.id_table = QTableWidget(self.tab)
        if (self.id_table.columnCount() < 3):
            self.id_table.setColumnCount(3)
        __qtablewidgetitem = QTableWidgetItem()
        self.id_table.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.id_table.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.id_table.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        self.id_table.setObjectName(u"id_table")
        self.id_table.setGeometry(QRect(10, 60, 831, 451))
        self.id_table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.id_table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.id_table.setTextElideMode(Qt.ElideRight)
        self.id_table.horizontalHeader().setVisible(True)
        self.id_table.horizontalHeader().setDefaultSectionSize(250)
        self.main_tab.addTab(self.tab, "")
        MainGUI.setCentralWidget(self.centralwidget)
        self.statusBar = QStatusBar(MainGUI)
        self.statusBar.setObjectName(u"statusBar")
        self.statusBar.setSizeGripEnabled(True)
        MainGUI.setStatusBar(self.statusBar)
        self.menubar = QMenuBar(MainGUI)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 874, 22))
        self.menubar.setDefaultUp(False)
        self.menubar.setNativeMenuBar(True)
        self.menuSettings = QMenu(self.menubar)
        self.menuSettings.setObjectName(u"menuSettings")
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName(u"menuHelp")
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuEdit = QMenu(self.menubar)
        self.menuEdit.setObjectName(u"menuEdit")
        self.menuDebug = QMenu(self.menubar)
        self.menuDebug.setObjectName(u"menuDebug")
        MainGUI.setMenuBar(self.menubar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuSettings.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menubar.addAction(self.menuDebug.menuAction())
        self.menuSettings.addAction(self.actionSettingsMenu)
        self.menuHelp.addAction(self.actionAbout)
        self.menuHelp.addAction(self.actionUpdateCheck)
        self.menuFile.addAction(self.actionQuest_Builder)
        self.menuFile.addAction(self.actionAssort_Builder)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionImport_Quests)
        self.menuFile.addAction(self.actionExport_Queued_Quests)
        self.menuFile.addSeparator()
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menuEdit.addAction(self.actionEdit_Tracked_Data_Files_locale_quest)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionRemove_Selected_Quest)
        self.menuEdit.addAction(self.actionCreate_locale_from_Quest_JSON)
        self.menuDebug.addAction(self.actionAdd_queued_to_open_list)
        self.menuDebug.addAction(self.actionAnalyze_CC_subtypes)
        self.menuDebug.addSeparator()
        self.menuDebug.addAction(self.actionLoad_items_json_for_below)
        self.menuDebug.addAction(self.actionGet_all_children_of_parent_ID)

        self.retranslateUi(MainGUI)

        self.main_tab.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainGUI)
    # setupUi

    def retranslateUi(self, MainGUI):
        MainGUI.setWindowTitle(QCoreApplication.translate("MainGUI", u"SPT Trader Builder", None))
        self.actionAbout.setText(QCoreApplication.translate("MainGUI", u"About", None))
        self.actionSettingsMenu.setText(QCoreApplication.translate("MainGUI", u"See settings.ini for more details.", None))
        self.actionExit.setText(QCoreApplication.translate("MainGUI", u"Exit", None))
        self.actionUpdateCheck.setText(QCoreApplication.translate("MainGUI", u"Check for Updates", None))
        self.actionQuest_Builder.setText(QCoreApplication.translate("MainGUI", u"Quest Builder", None))
        self.actionAssort_Builder.setText(QCoreApplication.translate("MainGUI", u"Assort Builder", None))
        self.actionLocale_Builder.setText(QCoreApplication.translate("MainGUI", u"Locale Builder", None))
        self.actionExport_Queued_Quests.setText(QCoreApplication.translate("MainGUI", u"Export Quests", None))
        self.actionView_Queued_Quests.setText(QCoreApplication.translate("MainGUI", u"View Queued Quests", None))
        self.actionAdd_queued_to_open_list.setText(QCoreApplication.translate("MainGUI", u"Add queued to open list", None))
        self.actionImport_Quests.setText(QCoreApplication.translate("MainGUI", u"Import Quests", None))
        self.actionRemove_Selected_Quest.setText(QCoreApplication.translate("MainGUI", u"Remove Selected Quest", None))
        self.actionAnalyze_CC_subtypes.setText(QCoreApplication.translate("MainGUI", u"Analyze CC subtypes", None))
        self.actionCreate_locale_from_Quest_JSON.setText(QCoreApplication.translate("MainGUI", u"Create locale from Quest JSON", None))
        self.actionLoad_items_json_for_below.setText(QCoreApplication.translate("MainGUI", u"Load items.json for below", None))
        self.actionGet_all_children_of_parent_ID.setText(QCoreApplication.translate("MainGUI", u"Get all children of parent ID", None))
        self.actionEdit_Tracked_Data_Files_locale_quest.setText(QCoreApplication.translate("MainGUI", u"Edit Tracked Data Files (locale/quest)", None))
        self.label_4.setText(QCoreApplication.translate("MainGUI", u"Search:", None))
        self.label.setText(QCoreApplication.translate("MainGUI", u"Open Quests:", None))
        self.label_5.setText(QCoreApplication.translate("MainGUI", u"(Click quest to copy MongoID)", None))
        self.main_tab.setTabText(self.main_tab.indexOf(self.quest_tab), QCoreApplication.translate("MainGUI", u"Quests", None))
        self.wb_removepart_button.setText(QCoreApplication.translate("MainGUI", u"Remove Part", None))
#if QT_CONFIG(tooltip)
        self.label_2.setToolTip(QCoreApplication.translate("MainGUI", u"<html><head/><body><p>The Mongo ID associated with the weapon part.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.label_2.setText(QCoreApplication.translate("MainGUI", u"Item ID", None))
#if QT_CONFIG(tooltip)
        self.wb_modslot.setToolTip(QCoreApplication.translate("MainGUI", u"<html><head/><body><p>What slot will the part fill.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.wb_modslot.setText(QCoreApplication.translate("MainGUI", u"Mod Slot", None))
        self.wb_addpart_button.setText(QCoreApplication.translate("MainGUI", u"Add Part", None))
#if QT_CONFIG(tooltip)
        self.wb_base_check.setToolTip(QCoreApplication.translate("MainGUI", u"<html><head/><body><p>Is this the first part of an entire weapon? Use the lower reciever to begin.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.wb_base_check.setText(QCoreApplication.translate("MainGUI", u"Base Weapon?", None))
#if QT_CONFIG(tooltip)
        self.wb_parentid.setToolTip(QCoreApplication.translate("MainGUI", u"<html><head/><body><p>The base weapon mongo ID. Click weapon or weapon part. in tree view to fill. eg. the lower reciever for an upper reciever (m4) or the handgaurd for a foregrip/rail.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.wb_parentid.setText(QCoreApplication.translate("MainGUI", u"Parent ID", None))
#if QT_CONFIG(tooltip)
        self.wb_weaponname.setToolTip(QCoreApplication.translate("MainGUI", u"<html><head/><body><p>The name for the weapon as a whole for organization purposes.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.wb_weaponname.setText(QCoreApplication.translate("MainGUI", u"Weapon Name", None))
        self.label_3.setText(QCoreApplication.translate("MainGUI", u"Weapons:", None))
        self.main_tab.setTabText(self.main_tab.indexOf(self.wb_tab), QCoreApplication.translate("MainGUI", u"Weapon Builder", None))
        self.main_tab.setTabText(self.main_tab.indexOf(self.locale_tab), QCoreApplication.translate("MainGUI", u"Locale", None))
        self.label_6.setText(QCoreApplication.translate("MainGUI", u"Search (regex, case insensitive):", None))
        ___qtablewidgetitem = self.id_table.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("MainGUI", u"id", None));
        ___qtablewidgetitem1 = self.id_table.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("MainGUI", u"data", None));
        ___qtablewidgetitem2 = self.id_table.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("MainGUI", u"type", None));
        self.main_tab.setTabText(self.main_tab.indexOf(self.tab), QCoreApplication.translate("MainGUI", u"ID Lookup", None))
        self.menuSettings.setTitle(QCoreApplication.translate("MainGUI", u"Settings", None))
        self.menuHelp.setTitle(QCoreApplication.translate("MainGUI", u"Help", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainGUI", u"File", None))
        self.menuEdit.setTitle(QCoreApplication.translate("MainGUI", u"Edit", None))
        self.menuDebug.setTitle(QCoreApplication.translate("MainGUI", u"Debug", None))
    # retranslateUi

