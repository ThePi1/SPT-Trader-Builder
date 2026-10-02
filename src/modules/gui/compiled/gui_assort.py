# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'gui_assort.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QGridLayout,
    QHeaderView, QLabel, QLineEdit, QMainWindow,
    QMenu, QMenuBar, QPushButton, QRadioButton,
    QSizePolicy, QStatusBar, QTabWidget, QTableWidget,
    QTableWidgetItem, QWidget)

class Ui_AssortBuilder(object):
    def setupUi(self, AssortBuilder):
        if not AssortBuilder.objectName():
            AssortBuilder.setObjectName(u"AssortBuilder")
        AssortBuilder.setEnabled(True)
        AssortBuilder.resize(1246, 588)
        AssortBuilder.setTabShape(QTabWidget.Rounded)
        self.actionHome = QAction(AssortBuilder)
        self.actionHome.setObjectName(u"actionHome")
        self.actionImport_Assort_json = QAction(AssortBuilder)
        self.actionImport_Assort_json.setObjectName(u"actionImport_Assort_json")
        self.actionExport_Assort_json = QAction(AssortBuilder)
        self.actionExport_Assort_json.setObjectName(u"actionExport_Assort_json")
        self.centralwidget = QWidget(AssortBuilder)
        self.centralwidget.setObjectName(u"centralwidget")
        self.ab_table = QTableWidget(self.centralwidget)
        self.ab_table.setObjectName(u"ab_table")
        self.ab_table.setGeometry(QRect(10, 40, 651, 501))
        self.ab_search_label = QLabel(self.centralwidget)
        self.ab_search_label.setObjectName(u"ab_search_label")
        self.ab_search_label.setGeometry(QRect(10, 10, 41, 22))
        self.ab_search = QLineEdit(self.centralwidget)
        self.ab_search.setObjectName(u"ab_search")
        self.ab_search.setGeometry(QRect(50, 10, 241, 22))
        self.ab_tab = QTabWidget(self.centralwidget)
        self.ab_tab.setObjectName(u"ab_tab")
        self.ab_tab.setGeometry(QRect(670, 40, 561, 411))
        self.ab_newitem_tab = QWidget()
        self.ab_newitem_tab.setObjectName(u"ab_newitem_tab")
        self.gridLayoutWidget = QWidget(self.ab_newitem_tab)
        self.gridLayoutWidget.setObjectName(u"gridLayoutWidget")
        self.gridLayoutWidget.setGeometry(QRect(10, 10, 541, 351))
        self.gridLayout = QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.ab_rouble_radiobutton = QRadioButton(self.gridLayoutWidget)
        self.ab_rouble_radiobutton.setObjectName(u"ab_rouble_radiobutton")

        self.gridLayout.addWidget(self.ab_rouble_radiobutton, 4, 1, 1, 1)

        self.ab_cost_edit = QLineEdit(self.gridLayoutWidget)
        self.ab_cost_edit.setObjectName(u"ab_cost_edit")

        self.gridLayout.addWidget(self.ab_cost_edit, 3, 2, 1, 1)

        self.ab_itemid = QLabel(self.gridLayoutWidget)
        self.ab_itemid.setObjectName(u"ab_itemid")

        self.gridLayout.addWidget(self.ab_itemid, 0, 1, 1, 1)

        self.ab_usd_button = QRadioButton(self.gridLayoutWidget)
        self.ab_usd_button.setObjectName(u"ab_usd_button")

        self.gridLayout.addWidget(self.ab_usd_button, 5, 1, 1, 1)

        self.ab_cost = QLabel(self.gridLayoutWidget)
        self.ab_cost.setObjectName(u"ab_cost")

        self.gridLayout.addWidget(self.ab_cost, 3, 1, 1, 1)

        self.ab_buyrestriction = QLabel(self.gridLayoutWidget)
        self.ab_buyrestriction.setObjectName(u"ab_buyrestriction")

        self.gridLayout.addWidget(self.ab_buyrestriction, 1, 4, 1, 1)

        self.ab_euro_button = QRadioButton(self.gridLayoutWidget)
        self.ab_euro_button.setObjectName(u"ab_euro_button")

        self.gridLayout.addWidget(self.ab_euro_button, 6, 1, 1, 1)

        self.ab_quantity = QLineEdit(self.gridLayoutWidget)
        self.ab_quantity.setObjectName(u"ab_quantity")

        self.gridLayout.addWidget(self.ab_quantity, 2, 2, 1, 1)

        self.ab_itembarter_edit = QLineEdit(self.gridLayoutWidget)
        self.ab_itembarter_edit.setObjectName(u"ab_itembarter_edit")

        self.gridLayout.addWidget(self.ab_itembarter_edit, 7, 2, 1, 1)

        self.ab_buyRestriction_edit = QLineEdit(self.gridLayoutWidget)
        self.ab_buyRestriction_edit.setObjectName(u"ab_buyRestriction_edit")

        self.gridLayout.addWidget(self.ab_buyRestriction_edit, 1, 5, 1, 1)

        self.ab_buyrestriction_checkbox = QCheckBox(self.gridLayoutWidget)
        self.ab_buyrestriction_checkbox.setObjectName(u"ab_buyrestriction_checkbox")

        self.gridLayout.addWidget(self.ab_buyrestriction_checkbox, 0, 4, 1, 1)

        self.ab_Item_Id = QLineEdit(self.gridLayoutWidget)
        self.ab_Item_Id.setObjectName(u"ab_Item_Id")

        self.gridLayout.addWidget(self.ab_Item_Id, 0, 2, 1, 1)

        self.ab_itembarter_check = QRadioButton(self.gridLayoutWidget)
        self.ab_itembarter_check.setObjectName(u"ab_itembarter_check")

        self.gridLayout.addWidget(self.ab_itembarter_check, 7, 1, 1, 1)

        self.ab_quantity_2 = QLabel(self.gridLayoutWidget)
        self.ab_quantity_2.setObjectName(u"ab_quantity_2")

        self.gridLayout.addWidget(self.ab_quantity_2, 2, 1, 1, 1)

        self.ab_unlimitedcount = QCheckBox(self.gridLayoutWidget)
        self.ab_unlimitedcount.setObjectName(u"ab_unlimitedcount")

        self.gridLayout.addWidget(self.ab_unlimitedcount, 1, 1, 1, 1)

        self.ab_quest_check = QCheckBox(self.gridLayoutWidget)
        self.ab_quest_check.setObjectName(u"ab_quest_check")

        self.gridLayout.addWidget(self.ab_quest_check, 2, 4, 1, 1)

        self.label = QLabel(self.gridLayoutWidget)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 3, 4, 1, 1)

        self.ab_quest_id = QLineEdit(self.gridLayoutWidget)
        self.ab_quest_id.setObjectName(u"ab_quest_id")

        self.gridLayout.addWidget(self.ab_quest_id, 3, 5, 1, 1)

        self.ab_condition = QLabel(self.gridLayoutWidget)
        self.ab_condition.setObjectName(u"ab_condition")

        self.gridLayout.addWidget(self.ab_condition, 4, 4, 1, 1)

        self.ab_condition_box = QComboBox(self.gridLayoutWidget)
        self.ab_condition_box.setObjectName(u"ab_condition_box")

        self.gridLayout.addWidget(self.ab_condition_box, 4, 5, 1, 1)

        self.ab_loyalty = QLabel(self.gridLayoutWidget)
        self.ab_loyalty.setObjectName(u"ab_loyalty")

        self.gridLayout.addWidget(self.ab_loyalty, 7, 4, 1, 1)

        self.ab_loyalty_combo = QComboBox(self.gridLayoutWidget)
        self.ab_loyalty_combo.setObjectName(u"ab_loyalty_combo")

        self.gridLayout.addWidget(self.ab_loyalty_combo, 7, 5, 1, 1)

        self.ab_tab.addTab(self.ab_newitem_tab, "")
        self.ab_weapon_tab = QWidget()
        self.ab_weapon_tab.setObjectName(u"ab_weapon_tab")
        self.gridLayoutWidget_4 = QWidget(self.ab_weapon_tab)
        self.gridLayoutWidget_4.setObjectName(u"gridLayoutWidget_4")
        self.gridLayoutWidget_4.setGeometry(QRect(20, 20, 301, 331))
        self.gridLayout_4 = QGridLayout(self.gridLayoutWidget_4)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout_4.setContentsMargins(0, 0, 0, 0)
        self.ab_weap_ammo_count = QLineEdit(self.gridLayoutWidget_4)
        self.ab_weap_ammo_count.setObjectName(u"ab_weap_ammo_count")

        self.gridLayout_4.addWidget(self.ab_weap_ammo_count, 3, 1, 1, 1)

        self.ab_modslot_combo = QComboBox(self.gridLayoutWidget_4)
        self.ab_modslot_combo.setObjectName(u"ab_modslot_combo")

        self.gridLayout_4.addWidget(self.ab_modslot_combo, 2, 1, 1, 1)

        self.ab_partid_edit = QLineEdit(self.gridLayoutWidget_4)
        self.ab_partid_edit.setObjectName(u"ab_partid_edit")

        self.gridLayout_4.addWidget(self.ab_partid_edit, 1, 1, 1, 1)

        self.ab_weapid = QLabel(self.gridLayoutWidget_4)
        self.ab_weapid.setObjectName(u"ab_weapid")

        self.gridLayout_4.addWidget(self.ab_weapid, 1, 0, 1, 1)

        self.ab_mongo = QLabel(self.gridLayoutWidget_4)
        self.ab_mongo.setObjectName(u"ab_mongo")

        self.gridLayout_4.addWidget(self.ab_mongo, 0, 0, 1, 1)

        self.ab_weap_ammo_check = QCheckBox(self.gridLayoutWidget_4)
        self.ab_weap_ammo_check.setObjectName(u"ab_weap_ammo_check")

        self.gridLayout_4.addWidget(self.ab_weap_ammo_check, 3, 0, 1, 1)

        self.ab_weapmongo_edit = QLineEdit(self.gridLayoutWidget_4)
        self.ab_weapmongo_edit.setObjectName(u"ab_weapmongo_edit")

        self.gridLayout_4.addWidget(self.ab_weapmongo_edit, 0, 1, 1, 1)

        self.ab_modslot = QLabel(self.gridLayoutWidget_4)
        self.ab_modslot.setObjectName(u"ab_modslot")

        self.gridLayout_4.addWidget(self.ab_modslot, 2, 0, 1, 1)

        self.ab_tab.addTab(self.ab_weapon_tab, "")
        self.gridLayoutWidget_2 = QWidget(self.centralwidget)
        self.gridLayoutWidget_2.setObjectName(u"gridLayoutWidget_2")
        self.gridLayoutWidget_2.setGeometry(QRect(670, 460, 255, 91))
        self.gridLayout_2 = QGridLayout(self.gridLayoutWidget_2)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.ab_add_item = QPushButton(self.gridLayoutWidget_2)
        self.ab_add_item.setObjectName(u"ab_add_item")

        self.gridLayout_2.addWidget(self.ab_add_item, 2, 1, 1, 1)

        self.ab_remove_item = QPushButton(self.gridLayoutWidget_2)
        self.ab_remove_item.setObjectName(u"ab_remove_item")

        self.gridLayout_2.addWidget(self.ab_remove_item, 3, 1, 1, 1)

        AssortBuilder.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(AssortBuilder)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1246, 22))
        self.menuHome = QMenu(self.menubar)
        self.menuHome.setObjectName(u"menuHome")
        AssortBuilder.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(AssortBuilder)
        self.statusbar.setObjectName(u"statusbar")
        AssortBuilder.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuHome.menuAction())
        self.menuHome.addAction(self.actionHome)
        self.menuHome.addAction(self.actionImport_Assort_json)
        self.menuHome.addAction(self.actionExport_Assort_json)

        self.retranslateUi(AssortBuilder)

        self.ab_tab.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(AssortBuilder)
    # setupUi

    def retranslateUi(self, AssortBuilder):
        AssortBuilder.setWindowTitle(QCoreApplication.translate("AssortBuilder", u"Assort Builder", None))
        self.actionHome.setText(QCoreApplication.translate("AssortBuilder", u"Home", None))
        self.actionImport_Assort_json.setText(QCoreApplication.translate("AssortBuilder", u"Import Assort.json", None))
        self.actionExport_Assort_json.setText(QCoreApplication.translate("AssortBuilder", u"Export Assort / Quest Assort", None))
#if QT_CONFIG(tooltip)
        self.ab_search_label.setToolTip(QCoreApplication.translate("AssortBuilder", u"<html><head/><body><p>Name of the item for your own organizational purposes.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.ab_search_label.setText(QCoreApplication.translate("AssortBuilder", u"Search:", None))
        self.ab_rouble_radiobutton.setText(QCoreApplication.translate("AssortBuilder", u"Rouble", None))
#if QT_CONFIG(tooltip)
        self.ab_itemid.setToolTip(QCoreApplication.translate("AssortBuilder", u"<html><head/><body><p>Mongo ID of the Item to be sold.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.ab_itemid.setText(QCoreApplication.translate("AssortBuilder", u"Item ID:", None))
        self.ab_usd_button.setText(QCoreApplication.translate("AssortBuilder", u"USD", None))
#if QT_CONFIG(tooltip)
        self.ab_cost.setToolTip(QCoreApplication.translate("AssortBuilder", u"<html><head/><body><p>Cost of item.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.ab_cost.setText(QCoreApplication.translate("AssortBuilder", u"Cost:", None))
#if QT_CONFIG(tooltip)
        self.ab_buyrestriction.setToolTip(QCoreApplication.translate("AssortBuilder", u"<html><head/><body><p>How many can be purchased in one restock if quantity is unlimited.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.ab_buyrestriction.setText(QCoreApplication.translate("AssortBuilder", u"Buy Restriction Amount", None))
        self.ab_euro_button.setText(QCoreApplication.translate("AssortBuilder", u"Euro", None))
#if QT_CONFIG(tooltip)
        self.ab_buyrestriction_checkbox.setToolTip(QCoreApplication.translate("AssortBuilder", u"<html><head/><body><p>Is there a restriction to how many can be purchased in a restock period?</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.ab_buyrestriction_checkbox.setText(QCoreApplication.translate("AssortBuilder", u"Buy Restriction?", None))
        self.ab_itembarter_check.setText(QCoreApplication.translate("AssortBuilder", u"Item Barter?", None))
#if QT_CONFIG(tooltip)
        self.ab_quantity_2.setToolTip(QCoreApplication.translate("AssortBuilder", u"<html><head/><body><p>If server wide... how many can be purchased within restock.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.ab_quantity_2.setText(QCoreApplication.translate("AssortBuilder", u"Quantity", None))
#if QT_CONFIG(tooltip)
        self.ab_unlimitedcount.setToolTip(QCoreApplication.translate("AssortBuilder", u"<html><head/><body><p>Typically true unless you want it to run out of stock in fika across server. Use buy restriction to set a limit.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.ab_unlimitedcount.setText(QCoreApplication.translate("AssortBuilder", u"Unlimited Quantity", None))
#if QT_CONFIG(tooltip)
        self.ab_quest_check.setToolTip(QCoreApplication.translate("AssortBuilder", u"<html><head/><body><p>Quest Locked?</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.ab_quest_check.setText(QCoreApplication.translate("AssortBuilder", u"Quest Locked? ID:", None))
        self.label.setText(QCoreApplication.translate("AssortBuilder", u"Quest ID:", None))
#if QT_CONFIG(tooltip)
        self.ab_condition.setToolTip(QCoreApplication.translate("AssortBuilder", u"<html><head/><body><p>What requirement for the above quest to unlock item.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.ab_condition.setText(QCoreApplication.translate("AssortBuilder", u"Condition", None))
#if QT_CONFIG(tooltip)
        self.ab_loyalty.setToolTip(QCoreApplication.translate("AssortBuilder", u"<html><head/><body><p>Which Loyalty Level.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.ab_loyalty.setText(QCoreApplication.translate("AssortBuilder", u"Loyalty Level:", None))
        self.ab_tab.setTabText(self.ab_tab.indexOf(self.ab_newitem_tab), QCoreApplication.translate("AssortBuilder", u"New Item", None))
        self.ab_weapid.setText(QCoreApplication.translate("AssortBuilder", u"Item ID:", None))
        self.ab_mongo.setText(QCoreApplication.translate("AssortBuilder", u"Parent (Click Item)", None))
        self.ab_weap_ammo_check.setText(QCoreApplication.translate("AssortBuilder", u"Box of Ammo", None))
        self.ab_modslot.setText(QCoreApplication.translate("AssortBuilder", u"Mod Slot", None))
        self.ab_tab.setTabText(self.ab_tab.indexOf(self.ab_weapon_tab), QCoreApplication.translate("AssortBuilder", u"New Part for Item", None))
        self.ab_add_item.setText(QCoreApplication.translate("AssortBuilder", u"Add Item", None))
        self.ab_remove_item.setText(QCoreApplication.translate("AssortBuilder", u"Remove Item", None))
        self.menuHome.setTitle(QCoreApplication.translate("AssortBuilder", u"File", None))
    # retranslateUi

