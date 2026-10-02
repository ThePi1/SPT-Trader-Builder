# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'gui_tasks.ui'
##
## Created by: Qt User Interface Compiler version 6.6.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox,
    QGridLayout, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QMainWindow, QMenuBar, QPushButton,
    QSizePolicy, QSpinBox, QStatusBar, QTabWidget,
    QTableWidget, QTableWidgetItem, QTextBrowser, QWidget)

class Ui_TaskWindow(object):
    def setupUi(self, TaskWindow):
        if not TaskWindow.objectName():
            TaskWindow.setObjectName(u"TaskWindow")
        TaskWindow.resize(1469, 730)
        self.centralwidget = QWidget(TaskWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.tabWidget_2 = QTabWidget(self.centralwidget)
        self.tabWidget_2.setObjectName(u"tabWidget_2")
        self.tabWidget_2.setGeometry(QRect(0, 0, 1251, 381))
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.tabWidget = QTabWidget(self.tab)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setGeometry(QRect(0, 0, 1241, 351))
        self.tab_6 = QWidget()
        self.tab_6.setObjectName(u"tab_6")
        self.lb_cond = QLabel(self.tab_6)
        self.lb_cond.setObjectName(u"lb_cond")
        self.lb_cond.setGeometry(QRect(10, 10, 71, 21))
        self.tabWidget_4 = QTabWidget(self.tab_6)
        self.tabWidget_4.setObjectName(u"tabWidget_4")
        self.tabWidget_4.setGeometry(QRect(320, 10, 911, 321))
        self.tab_11 = QWidget()
        self.tab_11.setObjectName(u"tab_11")
        self.gridLayoutWidget_19 = QWidget(self.tab_11)
        self.gridLayoutWidget_19.setObjectName(u"gridLayoutWidget_19")
        self.gridLayoutWidget_19.setGeometry(QRect(10, 10, 331, 61))
        self.grid_fields_10 = QGridLayout(self.gridLayoutWidget_19)
        self.grid_fields_10.setObjectName(u"grid_fields_10")
        self.grid_fields_10.setContentsMargins(0, 0, 0, 0)
        self.lb_zoneid_7 = QLabel(self.gridLayoutWidget_19)
        self.lb_zoneid_7.setObjectName(u"lb_zoneid_7")

        self.grid_fields_10.addWidget(self.lb_zoneid_7, 0, 0, 1, 1)

        self.fld_zoneid_ccvp = QLineEdit(self.gridLayoutWidget_19)
        self.fld_zoneid_ccvp.setObjectName(u"fld_zoneid_ccvp")

        self.grid_fields_10.addWidget(self.fld_zoneid_ccvp, 0, 1, 1, 1)

        self.pb_finalize_ccvp = QPushButton(self.tab_11)
        self.pb_finalize_ccvp.setObjectName(u"pb_finalize_ccvp")
        self.pb_finalize_ccvp.setGeometry(QRect(10, 80, 121, 24))
        self.tabWidget_4.addTab(self.tab_11, "")
        self.tab_12 = QWidget()
        self.tab_12.setObjectName(u"tab_12")
        self.gridLayoutWidget_5 = QWidget(self.tab_12)
        self.gridLayoutWidget_5.setObjectName(u"gridLayoutWidget_5")
        self.gridLayoutWidget_5.setGeometry(QRect(10, 10, 371, 136))
        self.grid_fields1_3 = QGridLayout(self.gridLayoutWidget_5)
        self.grid_fields1_3.setObjectName(u"grid_fields1_3")
        self.grid_fields1_3.setContentsMargins(0, 0, 0, 0)
        self.lb_time_to_cck = QLabel(self.gridLayoutWidget_5)
        self.lb_time_to_cck.setObjectName(u"lb_time_to_cck")

        self.grid_fields1_3.addWidget(self.lb_time_to_cck, 1, 0, 1, 1)

        self.fld_time_from_cck = QLineEdit(self.gridLayoutWidget_5)
        self.fld_time_from_cck.setObjectName(u"fld_time_from_cck")

        self.grid_fields1_3.addWidget(self.fld_time_from_cck, 0, 1, 1, 1)

        self.lb_time_from_cck = QLabel(self.gridLayoutWidget_5)
        self.lb_time_from_cck.setObjectName(u"lb_time_from_cck")

        self.grid_fields1_3.addWidget(self.lb_time_from_cck, 0, 0, 1, 1)

        self.box_dist_compare_cck = QComboBox(self.gridLayoutWidget_5)
        self.box_dist_compare_cck.setObjectName(u"box_dist_compare_cck")

        self.grid_fields1_3.addWidget(self.box_dist_compare_cck, 3, 1, 1, 1)

        self.lb_dist_cck = QLabel(self.gridLayoutWidget_5)
        self.lb_dist_cck.setObjectName(u"lb_dist_cck")

        self.grid_fields1_3.addWidget(self.lb_dist_cck, 2, 0, 1, 1)

        self.fld_time_to_cck = QLineEdit(self.gridLayoutWidget_5)
        self.fld_time_to_cck.setObjectName(u"fld_time_to_cck")

        self.grid_fields1_3.addWidget(self.fld_time_to_cck, 1, 1, 1, 1)

        self.lb_dist_compare_cck = QLabel(self.gridLayoutWidget_5)
        self.lb_dist_compare_cck.setObjectName(u"lb_dist_compare_cck")

        self.grid_fields1_3.addWidget(self.lb_dist_compare_cck, 3, 0, 1, 1)

        self.fld_dist_cck = QLineEdit(self.gridLayoutWidget_5)
        self.fld_dist_cck.setObjectName(u"fld_dist_cck")

        self.grid_fields1_3.addWidget(self.fld_dist_cck, 2, 1, 1, 1)

        self.chk_cck_usetarget = QCheckBox(self.gridLayoutWidget_5)
        self.chk_cck_usetarget.setObjectName(u"chk_cck_usetarget")

        self.grid_fields1_3.addWidget(self.chk_cck_usetarget, 4, 0, 1, 1)

        self.box_targets_cck = QComboBox(self.gridLayoutWidget_5)
        self.box_targets_cck.setObjectName(u"box_targets_cck")

        self.grid_fields1_3.addWidget(self.box_targets_cck, 4, 1, 1, 1)

        self.pb_finalize_cck = QPushButton(self.tab_12)
        self.pb_finalize_cck.setObjectName(u"pb_finalize_cck")
        self.pb_finalize_cck.setGeometry(QRect(10, 190, 121, 24))
        self.chk_cck_reset_sessionend = QCheckBox(self.tab_12)
        self.chk_cck_reset_sessionend.setObjectName(u"chk_cck_reset_sessionend")
        self.chk_cck_reset_sessionend.setGeometry(QRect(10, 160, 151, 16))
        self.tabWidget_5 = QTabWidget(self.tab_12)
        self.tabWidget_5.setObjectName(u"tabWidget_5")
        self.tabWidget_5.setGeometry(QRect(390, 10, 511, 281))
        sizePolicy = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabWidget_5.sizePolicy().hasHeightForWidth())
        self.tabWidget_5.setSizePolicy(sizePolicy)
        self.tab_15 = QWidget()
        self.tab_15.setObjectName(u"tab_15")
        self.horizontalLayoutWidget_5 = QWidget(self.tab_15)
        self.horizontalLayoutWidget_5.setObjectName(u"horizontalLayoutWidget_5")
        self.horizontalLayoutWidget_5.setGeometry(QRect(0, 200, 301, 31))
        self.grid_addremove_3 = QHBoxLayout(self.horizontalLayoutWidget_5)
        self.grid_addremove_3.setObjectName(u"grid_addremove_3")
        self.grid_addremove_3.setContentsMargins(0, 0, 0, 0)
        self.pb_removewep_cck = QPushButton(self.horizontalLayoutWidget_5)
        self.pb_removewep_cck.setObjectName(u"pb_removewep_cck")

        self.grid_addremove_3.addWidget(self.pb_removewep_cck)

        self.pb_addwep_cck = QPushButton(self.horizontalLayoutWidget_5)
        self.pb_addwep_cck.setObjectName(u"pb_addwep_cck")

        self.grid_addremove_3.addWidget(self.pb_addwep_cck)

        self.gridLayoutWidget_26 = QWidget(self.tab_15)
        self.gridLayoutWidget_26.setObjectName(u"gridLayoutWidget_26")
        self.gridLayoutWidget_26.setGeometry(QRect(10, 160, 271, 31))
        self.gridLayout_14 = QGridLayout(self.gridLayoutWidget_26)
        self.gridLayout_14.setObjectName(u"gridLayout_14")
        self.gridLayout_14.setContentsMargins(0, 0, 0, 0)
        self.box_weapons_cck = QComboBox(self.gridLayoutWidget_26)
        self.box_weapons_cck.setObjectName(u"box_weapons_cck")

        self.gridLayout_14.addWidget(self.box_weapons_cck, 0, 0, 1, 1)

        self.tb_wep = QTableWidget(self.tab_15)
        if (self.tb_wep.columnCount() < 1):
            self.tb_wep.setColumnCount(1)
        __qtablewidgetitem = QTableWidgetItem()
        self.tb_wep.setHorizontalHeaderItem(0, __qtablewidgetitem)
        self.tb_wep.setObjectName(u"tb_wep")
        self.tb_wep.setGeometry(QRect(10, 40, 271, 101))
        self.tb_wep.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.lb_addedweps_3 = QLabel(self.tab_15)
        self.lb_addedweps_3.setObjectName(u"lb_addedweps_3")
        self.lb_addedweps_3.setGeometry(QRect(10, 10, 161, 16))
        self.tabWidget_5.addTab(self.tab_15, "")
        self.tab_18 = QWidget()
        self.tab_18.setObjectName(u"tab_18")
        self.gridLayoutWidget_35 = QWidget(self.tab_18)
        self.gridLayoutWidget_35.setObjectName(u"gridLayoutWidget_35")
        self.gridLayoutWidget_35.setGeometry(QRect(10, 160, 271, 31))
        self.gridLayout_25 = QGridLayout(self.gridLayoutWidget_35)
        self.gridLayout_25.setObjectName(u"gridLayout_25")
        self.gridLayout_25.setContentsMargins(0, 0, 0, 0)
        self.box_targetrole_cck = QComboBox(self.gridLayoutWidget_35)
        self.box_targetrole_cck.setObjectName(u"box_targetrole_cck")

        self.gridLayout_25.addWidget(self.box_targetrole_cck, 0, 0, 1, 1)

        self.tb_targetrole = QTableWidget(self.tab_18)
        if (self.tb_targetrole.columnCount() < 1):
            self.tb_targetrole.setColumnCount(1)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tb_targetrole.setHorizontalHeaderItem(0, __qtablewidgetitem1)
        self.tb_targetrole.setObjectName(u"tb_targetrole")
        self.tb_targetrole.setGeometry(QRect(10, 40, 271, 101))
        self.tb_targetrole.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.horizontalLayoutWidget_8 = QWidget(self.tab_18)
        self.horizontalLayoutWidget_8.setObjectName(u"horizontalLayoutWidget_8")
        self.horizontalLayoutWidget_8.setGeometry(QRect(0, 200, 301, 31))
        self.grid_addremove_8 = QHBoxLayout(self.horizontalLayoutWidget_8)
        self.grid_addremove_8.setObjectName(u"grid_addremove_8")
        self.grid_addremove_8.setContentsMargins(0, 0, 0, 0)
        self.pb_removetr_cck = QPushButton(self.horizontalLayoutWidget_8)
        self.pb_removetr_cck.setObjectName(u"pb_removetr_cck")

        self.grid_addremove_8.addWidget(self.pb_removetr_cck)

        self.pb_addtr_cck = QPushButton(self.horizontalLayoutWidget_8)
        self.pb_addtr_cck.setObjectName(u"pb_addtr_cck")

        self.grid_addremove_8.addWidget(self.pb_addtr_cck)

        self.lb_addedweps_6 = QLabel(self.tab_18)
        self.lb_addedweps_6.setObjectName(u"lb_addedweps_6")
        self.lb_addedweps_6.setGeometry(QRect(10, 10, 161, 16))
        self.tabWidget_5.addTab(self.tab_18, "")
        self.tab_16 = QWidget()
        self.tab_16.setObjectName(u"tab_16")
        self.gridLayoutWidget_36 = QWidget(self.tab_16)
        self.gridLayoutWidget_36.setObjectName(u"gridLayoutWidget_36")
        self.gridLayoutWidget_36.setGeometry(QRect(10, 160, 271, 31))
        self.gridLayout_26 = QGridLayout(self.gridLayoutWidget_36)
        self.gridLayout_26.setObjectName(u"gridLayout_26")
        self.gridLayout_26.setContentsMargins(0, 0, 0, 0)
        self.box_bodypart_cck = QComboBox(self.gridLayoutWidget_36)
        self.box_bodypart_cck.setObjectName(u"box_bodypart_cck")

        self.gridLayout_26.addWidget(self.box_bodypart_cck, 0, 0, 1, 1)

        self.tb_bodypart = QTableWidget(self.tab_16)
        if (self.tb_bodypart.columnCount() < 1):
            self.tb_bodypart.setColumnCount(1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.tb_bodypart.setHorizontalHeaderItem(0, __qtablewidgetitem2)
        self.tb_bodypart.setObjectName(u"tb_bodypart")
        self.tb_bodypart.setGeometry(QRect(10, 40, 271, 101))
        self.tb_bodypart.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.horizontalLayoutWidget_9 = QWidget(self.tab_16)
        self.horizontalLayoutWidget_9.setObjectName(u"horizontalLayoutWidget_9")
        self.horizontalLayoutWidget_9.setGeometry(QRect(0, 200, 301, 31))
        self.grid_addremove_9 = QHBoxLayout(self.horizontalLayoutWidget_9)
        self.grid_addremove_9.setObjectName(u"grid_addremove_9")
        self.grid_addremove_9.setContentsMargins(0, 0, 0, 0)
        self.pb_rembp_cck = QPushButton(self.horizontalLayoutWidget_9)
        self.pb_rembp_cck.setObjectName(u"pb_rembp_cck")

        self.grid_addremove_9.addWidget(self.pb_rembp_cck)

        self.pb_addbp_cck = QPushButton(self.horizontalLayoutWidget_9)
        self.pb_addbp_cck.setObjectName(u"pb_addbp_cck")

        self.grid_addremove_9.addWidget(self.pb_addbp_cck)

        self.lb_addedweps_7 = QLabel(self.tab_16)
        self.lb_addedweps_7.setObjectName(u"lb_addedweps_7")
        self.lb_addedweps_7.setGeometry(QRect(10, 10, 161, 16))
        self.tabWidget_5.addTab(self.tab_16, "")
        self.tab_19 = QWidget()
        self.tab_19.setObjectName(u"tab_19")
        self.gridLayoutWidget_37 = QWidget(self.tab_19)
        self.gridLayoutWidget_37.setObjectName(u"gridLayoutWidget_37")
        self.gridLayoutWidget_37.setGeometry(QRect(10, 160, 271, 31))
        self.gridLayout_27 = QGridLayout(self.gridLayoutWidget_37)
        self.gridLayout_27.setObjectName(u"gridLayout_27")
        self.gridLayout_27.setContentsMargins(0, 0, 0, 0)
        self.fld_incmod_cck = QLineEdit(self.gridLayoutWidget_37)
        self.fld_incmod_cck.setObjectName(u"fld_incmod_cck")

        self.gridLayout_27.addWidget(self.fld_incmod_cck, 0, 0, 1, 1)

        self.tb_incmods = QTableWidget(self.tab_19)
        if (self.tb_incmods.columnCount() < 1):
            self.tb_incmods.setColumnCount(1)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.tb_incmods.setHorizontalHeaderItem(0, __qtablewidgetitem3)
        self.tb_incmods.setObjectName(u"tb_incmods")
        self.tb_incmods.setGeometry(QRect(10, 40, 271, 101))
        self.tb_incmods.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.horizontalLayoutWidget_10 = QWidget(self.tab_19)
        self.horizontalLayoutWidget_10.setObjectName(u"horizontalLayoutWidget_10")
        self.horizontalLayoutWidget_10.setGeometry(QRect(0, 200, 301, 31))
        self.grid_addremove_10 = QHBoxLayout(self.horizontalLayoutWidget_10)
        self.grid_addremove_10.setObjectName(u"grid_addremove_10")
        self.grid_addremove_10.setContentsMargins(0, 0, 0, 0)
        self.pb_rem_imod = QPushButton(self.horizontalLayoutWidget_10)
        self.pb_rem_imod.setObjectName(u"pb_rem_imod")

        self.grid_addremove_10.addWidget(self.pb_rem_imod)

        self.pb_add_imod = QPushButton(self.horizontalLayoutWidget_10)
        self.pb_add_imod.setObjectName(u"pb_add_imod")

        self.grid_addremove_10.addWidget(self.pb_add_imod)

        self.lb_addedweps_8 = QLabel(self.tab_19)
        self.lb_addedweps_8.setObjectName(u"lb_addedweps_8")
        self.lb_addedweps_8.setGeometry(QRect(10, 10, 161, 16))
        self.textBrowser_3 = QTextBrowser(self.tab_19)
        self.textBrowser_3.setObjectName(u"textBrowser_3")
        self.textBrowser_3.setGeometry(QRect(300, 40, 181, 61))
        self.tabWidget_5.addTab(self.tab_19, "")
        self.tab_26 = QWidget()
        self.tab_26.setObjectName(u"tab_26")
        self.gridLayoutWidget_38 = QWidget(self.tab_26)
        self.gridLayoutWidget_38.setObjectName(u"gridLayoutWidget_38")
        self.gridLayoutWidget_38.setGeometry(QRect(10, 160, 271, 31))
        self.gridLayout_28 = QGridLayout(self.gridLayoutWidget_38)
        self.gridLayout_28.setObjectName(u"gridLayout_28")
        self.gridLayout_28.setContentsMargins(0, 0, 0, 0)
        self.fld_excmod_cck = QLineEdit(self.gridLayoutWidget_38)
        self.fld_excmod_cck.setObjectName(u"fld_excmod_cck")

        self.gridLayout_28.addWidget(self.fld_excmod_cck, 0, 0, 1, 1)

        self.tb_excmods = QTableWidget(self.tab_26)
        if (self.tb_excmods.columnCount() < 1):
            self.tb_excmods.setColumnCount(1)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.tb_excmods.setHorizontalHeaderItem(0, __qtablewidgetitem4)
        self.tb_excmods.setObjectName(u"tb_excmods")
        self.tb_excmods.setGeometry(QRect(10, 40, 271, 101))
        self.tb_excmods.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.horizontalLayoutWidget_11 = QWidget(self.tab_26)
        self.horizontalLayoutWidget_11.setObjectName(u"horizontalLayoutWidget_11")
        self.horizontalLayoutWidget_11.setGeometry(QRect(0, 200, 301, 31))
        self.grid_addremove_11 = QHBoxLayout(self.horizontalLayoutWidget_11)
        self.grid_addremove_11.setObjectName(u"grid_addremove_11")
        self.grid_addremove_11.setContentsMargins(0, 0, 0, 0)
        self.pb_rem_emod = QPushButton(self.horizontalLayoutWidget_11)
        self.pb_rem_emod.setObjectName(u"pb_rem_emod")

        self.grid_addremove_11.addWidget(self.pb_rem_emod)

        self.pb_add_emod = QPushButton(self.horizontalLayoutWidget_11)
        self.pb_add_emod.setObjectName(u"pb_add_emod")

        self.grid_addremove_11.addWidget(self.pb_add_emod)

        self.lb_addedweps_9 = QLabel(self.tab_26)
        self.lb_addedweps_9.setObjectName(u"lb_addedweps_9")
        self.lb_addedweps_9.setGeometry(QRect(10, 10, 161, 16))
        self.textBrowser_2 = QTextBrowser(self.tab_26)
        self.textBrowser_2.setObjectName(u"textBrowser_2")
        self.textBrowser_2.setGeometry(QRect(300, 40, 181, 61))
        self.tabWidget_5.addTab(self.tab_26, "")
        self.tabWidget_4.addTab(self.tab_12, "")
        self.tab_20 = QWidget()
        self.tab_20.setObjectName(u"tab_20")
        self.gridLayoutWidget_21 = QWidget(self.tab_20)
        self.gridLayoutWidget_21.setObjectName(u"gridLayoutWidget_21")
        self.gridLayoutWidget_21.setGeometry(QRect(10, 10, 321, 31))
        self.gridLayout_7 = QGridLayout(self.gridLayoutWidget_21)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.gridLayout_7.setContentsMargins(0, 0, 0, 0)
        self.label_39 = QLabel(self.gridLayoutWidget_21)
        self.label_39.setObjectName(u"label_39")

        self.gridLayout_7.addWidget(self.label_39, 0, 0, 1, 1)

        self.box_status_cces = QComboBox(self.gridLayoutWidget_21)
        self.box_status_cces.setObjectName(u"box_status_cces")

        self.gridLayout_7.addWidget(self.box_status_cces, 0, 1, 1, 1)

        self.pb_cces_add = QPushButton(self.tab_20)
        self.pb_cces_add.setObjectName(u"pb_cces_add")
        self.pb_cces_add.setGeometry(QRect(340, 10, 75, 24))
        self.label_8 = QLabel(self.tab_20)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setGeometry(QRect(10, 50, 49, 16))
        self.pb_finalize_cces = QPushButton(self.tab_20)
        self.pb_finalize_cces.setObjectName(u"pb_finalize_cces")
        self.pb_finalize_cces.setGeometry(QRect(10, 190, 111, 24))
        self.pb_status_rem_cces = QPushButton(self.tab_20)
        self.pb_status_rem_cces.setObjectName(u"pb_status_rem_cces")
        self.pb_status_rem_cces.setGeometry(QRect(130, 190, 151, 24))
        self.tb_cces = QTableWidget(self.tab_20)
        if (self.tb_cces.columnCount() < 1):
            self.tb_cces.setColumnCount(1)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.tb_cces.setHorizontalHeaderItem(0, __qtablewidgetitem5)
        self.tb_cces.setObjectName(u"tb_cces")
        self.tb_cces.setGeometry(QRect(10, 80, 281, 91))
        self.tb_cces.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabWidget_4.addTab(self.tab_20, "")
        self.tab_21 = QWidget()
        self.tab_21.setObjectName(u"tab_21")
        self.gridLayoutWidget_2 = QWidget(self.tab_21)
        self.gridLayoutWidget_2.setObjectName(u"gridLayoutWidget_2")
        self.gridLayoutWidget_2.setGeometry(QRect(10, 10, 241, 41))
        self.gridLayout_8 = QGridLayout(self.gridLayoutWidget_2)
        self.gridLayout_8.setObjectName(u"gridLayout_8")
        self.gridLayout_8.setContentsMargins(0, 0, 0, 0)
        self.label_3 = QLabel(self.gridLayoutWidget_2)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout_8.addWidget(self.label_3, 0, 0, 1, 1)

        self.fld_exitname_ccen = QLineEdit(self.gridLayoutWidget_2)
        self.fld_exitname_ccen.setObjectName(u"fld_exitname_ccen")

        self.gridLayout_8.addWidget(self.fld_exitname_ccen, 0, 1, 1, 1)

        self.pb_finalize_ccen = QPushButton(self.tab_21)
        self.pb_finalize_ccen.setObjectName(u"pb_finalize_ccen")
        self.pb_finalize_ccen.setGeometry(QRect(10, 60, 111, 24))
        self.tabWidget_4.addTab(self.tab_21, "")
        self.tab_22 = QWidget()
        self.tab_22.setObjectName(u"tab_22")
        self.label_4 = QLabel(self.tab_22)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setGeometry(QRect(10, 10, 71, 16))
        self.horizontalLayoutWidget = QWidget(self.tab_22)
        self.horizontalLayoutWidget.setObjectName(u"horizontalLayoutWidget")
        self.horizontalLayoutWidget.setGeometry(QRect(10, 40, 231, 31))
        self.horizontalLayout = QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.label_7 = QLabel(self.horizontalLayoutWidget)
        self.label_7.setObjectName(u"label_7")

        self.horizontalLayout.addWidget(self.label_7)

        self.box_location_ccl = QComboBox(self.horizontalLayoutWidget)
        self.box_location_ccl.setObjectName(u"box_location_ccl")

        self.horizontalLayout.addWidget(self.box_location_ccl)

        self.pb_add_ccl = QPushButton(self.tab_22)
        self.pb_add_ccl.setObjectName(u"pb_add_ccl")
        self.pb_add_ccl.setGeometry(QRect(250, 40, 75, 24))
        self.gridLayoutWidget_27 = QWidget(self.tab_22)
        self.gridLayoutWidget_27.setObjectName(u"gridLayoutWidget_27")
        self.gridLayoutWidget_27.setGeometry(QRect(10, 170, 311, 41))
        self.gridLayout_15 = QGridLayout(self.gridLayoutWidget_27)
        self.gridLayout_15.setObjectName(u"gridLayout_15")
        self.gridLayout_15.setContentsMargins(0, 0, 0, 0)
        self.pb_finalize_ccl = QPushButton(self.gridLayoutWidget_27)
        self.pb_finalize_ccl.setObjectName(u"pb_finalize_ccl")

        self.gridLayout_15.addWidget(self.pb_finalize_ccl, 0, 0, 1, 1)

        self.pb_rem_ccl = QPushButton(self.gridLayoutWidget_27)
        self.pb_rem_ccl.setObjectName(u"pb_rem_ccl")

        self.gridLayout_15.addWidget(self.pb_rem_ccl, 0, 1, 1, 1)

        self.tb_ccl = QTableWidget(self.tab_22)
        if (self.tb_ccl.columnCount() < 1):
            self.tb_ccl.setColumnCount(1)
        __qtablewidgetitem6 = QTableWidgetItem()
        self.tb_ccl.setHorizontalHeaderItem(0, __qtablewidgetitem6)
        self.tb_ccl.setObjectName(u"tb_ccl")
        self.tb_ccl.setGeometry(QRect(10, 80, 311, 71))
        self.tb_ccl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabWidget_4.addTab(self.tab_22, "")
        self.tab_9 = QWidget()
        self.tab_9.setObjectName(u"tab_9")
        self.tb_eq_inc = QTableWidget(self.tab_9)
        if (self.tb_eq_inc.columnCount() < 2):
            self.tb_eq_inc.setColumnCount(2)
        __qtablewidgetitem7 = QTableWidgetItem()
        self.tb_eq_inc.setHorizontalHeaderItem(0, __qtablewidgetitem7)
        __qtablewidgetitem8 = QTableWidgetItem()
        self.tb_eq_inc.setHorizontalHeaderItem(1, __qtablewidgetitem8)
        self.tb_eq_inc.setObjectName(u"tb_eq_inc")
        self.tb_eq_inc.setGeometry(QRect(10, 50, 311, 111))
        self.tb_eq_inc.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tb_eq_exc = QTableWidget(self.tab_9)
        if (self.tb_eq_exc.columnCount() < 2):
            self.tb_eq_exc.setColumnCount(2)
        __qtablewidgetitem9 = QTableWidgetItem()
        self.tb_eq_exc.setHorizontalHeaderItem(0, __qtablewidgetitem9)
        __qtablewidgetitem10 = QTableWidgetItem()
        self.tb_eq_exc.setHorizontalHeaderItem(1, __qtablewidgetitem10)
        self.tb_eq_exc.setObjectName(u"tb_eq_exc")
        self.tb_eq_exc.setGeometry(QRect(350, 50, 311, 111))
        self.tb_eq_exc.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.label_9 = QLabel(self.tab_9)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setGeometry(QRect(10, 10, 111, 16))
        self.label_17 = QLabel(self.tab_9)
        self.label_17.setObjectName(u"label_17")
        self.label_17.setGeometry(QRect(350, 10, 131, 16))
        self.label_20 = QLabel(self.tab_9)
        self.label_20.setObjectName(u"label_20")
        self.label_20.setGeometry(QRect(10, 30, 111, 16))
        self.label_21 = QLabel(self.tab_9)
        self.label_21.setObjectName(u"label_21")
        self.label_21.setGeometry(QRect(350, 30, 101, 16))
        self.gridLayoutWidget_7 = QWidget(self.tab_9)
        self.gridLayoutWidget_7.setObjectName(u"gridLayoutWidget_7")
        self.gridLayoutWidget_7.setGeometry(QRect(10, 260, 421, 31))
        self.gridLayout_4 = QGridLayout(self.gridLayoutWidget_7)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout_4.setContentsMargins(0, 0, 0, 0)
        self.cb_eq_uneq = QCheckBox(self.gridLayoutWidget_7)
        self.cb_eq_uneq.setObjectName(u"cb_eq_uneq")

        self.gridLayout_4.addWidget(self.cb_eq_uneq, 0, 2, 1, 1)

        self.pb_finalize_cc_eq = QPushButton(self.gridLayoutWidget_7)
        self.pb_finalize_cc_eq.setObjectName(u"pb_finalize_cc_eq")

        self.gridLayout_4.addWidget(self.pb_finalize_cc_eq, 0, 1, 1, 1)

        self.horizontalLayoutWidget_23 = QWidget(self.tab_9)
        self.horizontalLayoutWidget_23.setObjectName(u"horizontalLayoutWidget_23")
        self.horizontalLayoutWidget_23.setGeometry(QRect(10, 230, 301, 31))
        self.grid_addremove_25 = QHBoxLayout(self.horizontalLayoutWidget_23)
        self.grid_addremove_25.setObjectName(u"grid_addremove_25")
        self.grid_addremove_25.setContentsMargins(0, 0, 0, 0)
        self.pb_rem_eqi = QPushButton(self.horizontalLayoutWidget_23)
        self.pb_rem_eqi.setObjectName(u"pb_rem_eqi")

        self.grid_addremove_25.addWidget(self.pb_rem_eqi)

        self.pb_add_eqi = QPushButton(self.horizontalLayoutWidget_23)
        self.pb_add_eqi.setObjectName(u"pb_add_eqi")

        self.grid_addremove_25.addWidget(self.pb_add_eqi)

        self.horizontalLayoutWidget_24 = QWidget(self.tab_9)
        self.horizontalLayoutWidget_24.setObjectName(u"horizontalLayoutWidget_24")
        self.horizontalLayoutWidget_24.setGeometry(QRect(350, 230, 301, 31))
        self.grid_addremove_26 = QHBoxLayout(self.horizontalLayoutWidget_24)
        self.grid_addremove_26.setObjectName(u"grid_addremove_26")
        self.grid_addremove_26.setContentsMargins(0, 0, 0, 0)
        self.pb_rem_eqe = QPushButton(self.horizontalLayoutWidget_24)
        self.pb_rem_eqe.setObjectName(u"pb_rem_eqe")

        self.grid_addremove_26.addWidget(self.pb_rem_eqe)

        self.pb_add_eqe = QPushButton(self.horizontalLayoutWidget_24)
        self.pb_add_eqe.setObjectName(u"pb_add_eqe")

        self.grid_addremove_26.addWidget(self.pb_add_eqe)

        self.gridLayoutWidget_11 = QWidget(self.tab_9)
        self.gridLayoutWidget_11.setObjectName(u"gridLayoutWidget_11")
        self.gridLayoutWidget_11.setGeometry(QRect(10, 170, 261, 52))
        self.gridLayout_19 = QGridLayout(self.gridLayoutWidget_11)
        self.gridLayout_19.setObjectName(u"gridLayout_19")
        self.gridLayout_19.setContentsMargins(0, 0, 0, 0)
        self.fld_eqi = QLineEdit(self.gridLayoutWidget_11)
        self.fld_eqi.setObjectName(u"fld_eqi")

        self.gridLayout_19.addWidget(self.fld_eqi, 0, 1, 1, 1)

        self.fld_equi_org = QLineEdit(self.gridLayoutWidget_11)
        self.fld_equi_org.setObjectName(u"fld_equi_org")

        self.gridLayout_19.addWidget(self.fld_equi_org, 1, 1, 1, 1)

        self.label_22 = QLabel(self.gridLayoutWidget_11)
        self.label_22.setObjectName(u"label_22")

        self.gridLayout_19.addWidget(self.label_22, 0, 0, 1, 1)

        self.label_23 = QLabel(self.gridLayoutWidget_11)
        self.label_23.setObjectName(u"label_23")

        self.gridLayout_19.addWidget(self.label_23, 1, 0, 1, 1)

        self.gridLayoutWidget_12 = QWidget(self.tab_9)
        self.gridLayoutWidget_12.setObjectName(u"gridLayoutWidget_12")
        self.gridLayoutWidget_12.setGeometry(QRect(350, 170, 261, 52))
        self.gridLayout_20 = QGridLayout(self.gridLayoutWidget_12)
        self.gridLayout_20.setObjectName(u"gridLayout_20")
        self.gridLayout_20.setContentsMargins(0, 0, 0, 0)
        self.fld_eqi_2 = QLineEdit(self.gridLayoutWidget_12)
        self.fld_eqi_2.setObjectName(u"fld_eqi_2")

        self.gridLayout_20.addWidget(self.fld_eqi_2, 0, 1, 1, 1)

        self.fld_eqe_org = QLineEdit(self.gridLayoutWidget_12)
        self.fld_eqe_org.setObjectName(u"fld_eqe_org")

        self.gridLayout_20.addWidget(self.fld_eqe_org, 1, 1, 1, 1)

        self.label_73 = QLabel(self.gridLayoutWidget_12)
        self.label_73.setObjectName(u"label_73")

        self.gridLayout_20.addWidget(self.label_73, 0, 0, 1, 1)

        self.label_74 = QLabel(self.gridLayoutWidget_12)
        self.label_74.setObjectName(u"label_74")

        self.gridLayout_20.addWidget(self.label_74, 1, 0, 1, 1)

        self.tabWidget_4.addTab(self.tab_9, "")
        self.tab_10 = QWidget()
        self.tab_10.setObjectName(u"tab_10")
        self.tabWidget_6 = QTabWidget(self.tab_10)
        self.tabWidget_6.setObjectName(u"tabWidget_6")
        self.tabWidget_6.setGeometry(QRect(410, 0, 491, 281))
        self.tab_25 = QWidget()
        self.tab_25.setObjectName(u"tab_25")
        self.tb_sh_bp = QTableWidget(self.tab_25)
        if (self.tb_sh_bp.columnCount() < 1):
            self.tb_sh_bp.setColumnCount(1)
        __qtablewidgetitem11 = QTableWidgetItem()
        self.tb_sh_bp.setHorizontalHeaderItem(0, __qtablewidgetitem11)
        self.tb_sh_bp.setObjectName(u"tb_sh_bp")
        self.tb_sh_bp.setGeometry(QRect(20, 40, 311, 91))
        self.tb_sh_bp.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.label_24 = QLabel(self.tab_25)
        self.label_24.setObjectName(u"label_24")
        self.label_24.setGeometry(QRect(20, 10, 81, 16))
        self.horizontalLayoutWidget_14 = QWidget(self.tab_25)
        self.horizontalLayoutWidget_14.setObjectName(u"horizontalLayoutWidget_14")
        self.horizontalLayoutWidget_14.setGeometry(QRect(19, 176, 301, 31))
        self.grid_addremove_15 = QHBoxLayout(self.horizontalLayoutWidget_14)
        self.grid_addremove_15.setObjectName(u"grid_addremove_15")
        self.grid_addremove_15.setContentsMargins(0, 0, 0, 0)
        self.pb_rem_shbp = QPushButton(self.horizontalLayoutWidget_14)
        self.pb_rem_shbp.setObjectName(u"pb_rem_shbp")

        self.grid_addremove_15.addWidget(self.pb_rem_shbp)

        self.pb_add_shbp = QPushButton(self.horizontalLayoutWidget_14)
        self.pb_add_shbp.setObjectName(u"pb_add_shbp")

        self.grid_addremove_15.addWidget(self.pb_add_shbp)

        self.box_shbp = QComboBox(self.tab_25)
        self.box_shbp.setObjectName(u"box_shbp")
        self.box_shbp.setGeometry(QRect(20, 150, 269, 22))
        self.tabWidget_6.addTab(self.tab_25, "")
        self.tab_30 = QWidget()
        self.tab_30.setObjectName(u"tab_30")
        self.horizontalLayoutWidget_18 = QWidget(self.tab_30)
        self.horizontalLayoutWidget_18.setObjectName(u"horizontalLayoutWidget_18")
        self.horizontalLayoutWidget_18.setGeometry(QRect(9, 176, 301, 31))
        self.grid_addremove_19 = QHBoxLayout(self.horizontalLayoutWidget_18)
        self.grid_addremove_19.setObjectName(u"grid_addremove_19")
        self.grid_addremove_19.setContentsMargins(0, 0, 0, 0)
        self.pb_rem_shtr = QPushButton(self.horizontalLayoutWidget_18)
        self.pb_rem_shtr.setObjectName(u"pb_rem_shtr")

        self.grid_addremove_19.addWidget(self.pb_rem_shtr)

        self.pb_add_shtr = QPushButton(self.horizontalLayoutWidget_18)
        self.pb_add_shtr.setObjectName(u"pb_add_shtr")

        self.grid_addremove_19.addWidget(self.pb_add_shtr)

        self.box_shtr = QComboBox(self.tab_30)
        self.box_shtr.setObjectName(u"box_shtr")
        self.box_shtr.setGeometry(QRect(10, 150, 269, 22))
        self.tb_sh_tr = QTableWidget(self.tab_30)
        if (self.tb_sh_tr.columnCount() < 1):
            self.tb_sh_tr.setColumnCount(1)
        __qtablewidgetitem12 = QTableWidgetItem()
        self.tb_sh_tr.setHorizontalHeaderItem(0, __qtablewidgetitem12)
        self.tb_sh_tr.setObjectName(u"tb_sh_tr")
        self.tb_sh_tr.setGeometry(QRect(10, 40, 311, 91))
        self.tb_sh_tr.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.label_28 = QLabel(self.tab_30)
        self.label_28.setObjectName(u"label_28")
        self.label_28.setGeometry(QRect(10, 20, 151, 16))
        self.tabWidget_6.addTab(self.tab_30, "")
        self.tab_27 = QWidget()
        self.tab_27.setObjectName(u"tab_27")
        self.tb_sh_wep = QTableWidget(self.tab_27)
        if (self.tb_sh_wep.columnCount() < 1):
            self.tb_sh_wep.setColumnCount(1)
        __qtablewidgetitem13 = QTableWidgetItem()
        self.tb_sh_wep.setHorizontalHeaderItem(0, __qtablewidgetitem13)
        self.tb_sh_wep.setObjectName(u"tb_sh_wep")
        self.tb_sh_wep.setGeometry(QRect(10, 30, 311, 91))
        self.tb_sh_wep.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.label_25 = QLabel(self.tab_27)
        self.label_25.setObjectName(u"label_25")
        self.label_25.setGeometry(QRect(10, 10, 51, 16))
        self.horizontalLayoutWidget_15 = QWidget(self.tab_27)
        self.horizontalLayoutWidget_15.setObjectName(u"horizontalLayoutWidget_15")
        self.horizontalLayoutWidget_15.setGeometry(QRect(9, 166, 301, 31))
        self.grid_addremove_16 = QHBoxLayout(self.horizontalLayoutWidget_15)
        self.grid_addremove_16.setObjectName(u"grid_addremove_16")
        self.grid_addremove_16.setContentsMargins(0, 0, 0, 0)
        self.pb_rem_shw = QPushButton(self.horizontalLayoutWidget_15)
        self.pb_rem_shw.setObjectName(u"pb_rem_shw")

        self.grid_addremove_16.addWidget(self.pb_rem_shw)

        self.pb_add_shw = QPushButton(self.horizontalLayoutWidget_15)
        self.pb_add_shw.setObjectName(u"pb_add_shw")

        self.grid_addremove_16.addWidget(self.pb_add_shw)

        self.fld_shw = QLineEdit(self.tab_27)
        self.fld_shw.setObjectName(u"fld_shw")
        self.fld_shw.setGeometry(QRect(10, 130, 221, 22))
        self.tabWidget_6.addTab(self.tab_27, "")
        self.tab_28 = QWidget()
        self.tab_28.setObjectName(u"tab_28")
        self.tb_incmod_sh = QTableWidget(self.tab_28)
        if (self.tb_incmod_sh.columnCount() < 1):
            self.tb_incmod_sh.setColumnCount(1)
        __qtablewidgetitem14 = QTableWidgetItem()
        self.tb_incmod_sh.setHorizontalHeaderItem(0, __qtablewidgetitem14)
        self.tb_incmod_sh.setObjectName(u"tb_incmod_sh")
        self.tb_incmod_sh.setGeometry(QRect(10, 40, 311, 91))
        self.tb_incmod_sh.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.label_26 = QLabel(self.tab_28)
        self.label_26.setObjectName(u"label_26")
        self.label_26.setGeometry(QRect(10, 10, 151, 16))
        self.horizontalLayoutWidget_16 = QWidget(self.tab_28)
        self.horizontalLayoutWidget_16.setObjectName(u"horizontalLayoutWidget_16")
        self.horizontalLayoutWidget_16.setGeometry(QRect(9, 176, 301, 31))
        self.grid_addremove_17 = QHBoxLayout(self.horizontalLayoutWidget_16)
        self.grid_addremove_17.setObjectName(u"grid_addremove_17")
        self.grid_addremove_17.setContentsMargins(0, 0, 0, 0)
        self.pb_rem_shmi = QPushButton(self.horizontalLayoutWidget_16)
        self.pb_rem_shmi.setObjectName(u"pb_rem_shmi")

        self.grid_addremove_17.addWidget(self.pb_rem_shmi)

        self.pb_add_shmi = QPushButton(self.horizontalLayoutWidget_16)
        self.pb_add_shmi.setObjectName(u"pb_add_shmi")

        self.grid_addremove_17.addWidget(self.pb_add_shmi)

        self.fld_shmi = QLineEdit(self.tab_28)
        self.fld_shmi.setObjectName(u"fld_shmi")
        self.fld_shmi.setGeometry(QRect(10, 140, 251, 22))
        self.tabWidget_6.addTab(self.tab_28, "")
        self.tab_29 = QWidget()
        self.tab_29.setObjectName(u"tab_29")
        self.tb_excmod_sh = QTableWidget(self.tab_29)
        if (self.tb_excmod_sh.columnCount() < 1):
            self.tb_excmod_sh.setColumnCount(1)
        __qtablewidgetitem15 = QTableWidgetItem()
        self.tb_excmod_sh.setHorizontalHeaderItem(0, __qtablewidgetitem15)
        self.tb_excmod_sh.setObjectName(u"tb_excmod_sh")
        self.tb_excmod_sh.setGeometry(QRect(10, 30, 311, 91))
        self.tb_excmod_sh.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.label_27 = QLabel(self.tab_29)
        self.label_27.setObjectName(u"label_27")
        self.label_27.setGeometry(QRect(10, 10, 151, 16))
        self.horizontalLayoutWidget_17 = QWidget(self.tab_29)
        self.horizontalLayoutWidget_17.setObjectName(u"horizontalLayoutWidget_17")
        self.horizontalLayoutWidget_17.setGeometry(QRect(9, 166, 301, 31))
        self.grid_addremove_18 = QHBoxLayout(self.horizontalLayoutWidget_17)
        self.grid_addremove_18.setObjectName(u"grid_addremove_18")
        self.grid_addremove_18.setContentsMargins(0, 0, 0, 0)
        self.pb_rem_shme = QPushButton(self.horizontalLayoutWidget_17)
        self.pb_rem_shme.setObjectName(u"pb_rem_shme")

        self.grid_addremove_18.addWidget(self.pb_rem_shme)

        self.pb_add_shme = QPushButton(self.horizontalLayoutWidget_17)
        self.pb_add_shme.setObjectName(u"pb_add_shme")

        self.grid_addremove_18.addWidget(self.pb_add_shme)

        self.fld_shme = QLineEdit(self.tab_29)
        self.fld_shme.setObjectName(u"fld_shme")
        self.fld_shme.setGeometry(QRect(10, 130, 261, 22))
        self.tabWidget_6.addTab(self.tab_29, "")
        self.gridLayoutWidget_8 = QWidget(self.tab_10)
        self.gridLayoutWidget_8.setObjectName(u"gridLayoutWidget_8")
        self.gridLayoutWidget_8.setGeometry(QRect(20, 20, 371, 190))
        self.gridLayout_5 = QGridLayout(self.gridLayoutWidget_8)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.gridLayout_5.setContentsMargins(0, 0, 0, 0)
        self.label_31 = QLabel(self.gridLayoutWidget_8)
        self.label_31.setObjectName(u"label_31")

        self.gridLayout_5.addWidget(self.label_31, 2, 0, 1, 1)

        self.label_30 = QLabel(self.gridLayoutWidget_8)
        self.label_30.setObjectName(u"label_30")

        self.gridLayout_5.addWidget(self.label_30, 1, 0, 1, 1)

        self.label_29 = QLabel(self.gridLayoutWidget_8)
        self.label_29.setObjectName(u"label_29")

        self.gridLayout_5.addWidget(self.label_29, 0, 0, 1, 1)

        self.fld_timeto_sh = QLineEdit(self.gridLayoutWidget_8)
        self.fld_timeto_sh.setObjectName(u"fld_timeto_sh")

        self.gridLayout_5.addWidget(self.fld_timeto_sh, 1, 1, 1, 1)

        self.box_distcomp_sh = QComboBox(self.gridLayoutWidget_8)
        self.box_distcomp_sh.setObjectName(u"box_distcomp_sh")

        self.gridLayout_5.addWidget(self.box_distcomp_sh, 2, 1, 1, 1)

        self.fld_timefrom_sh = QLineEdit(self.gridLayoutWidget_8)
        self.fld_timefrom_sh.setObjectName(u"fld_timefrom_sh")

        self.gridLayout_5.addWidget(self.fld_timefrom_sh, 0, 1, 1, 1)

        self.label_32 = QLabel(self.gridLayoutWidget_8)
        self.label_32.setObjectName(u"label_32")

        self.gridLayout_5.addWidget(self.label_32, 3, 0, 1, 1)

        self.fld_value_sh = QLineEdit(self.gridLayoutWidget_8)
        self.fld_value_sh.setObjectName(u"fld_value_sh")

        self.gridLayout_5.addWidget(self.fld_value_sh, 5, 1, 1, 1)

        self.fld_dist_sh = QLineEdit(self.gridLayoutWidget_8)
        self.fld_dist_sh.setObjectName(u"fld_dist_sh")

        self.gridLayout_5.addWidget(self.fld_dist_sh, 3, 1, 1, 1)

        self.box_target_sh = QComboBox(self.gridLayoutWidget_8)
        self.box_target_sh.setObjectName(u"box_target_sh")

        self.gridLayout_5.addWidget(self.box_target_sh, 6, 1, 1, 1)

        self.label_33 = QLabel(self.gridLayoutWidget_8)
        self.label_33.setObjectName(u"label_33")

        self.gridLayout_5.addWidget(self.label_33, 5, 0, 1, 1)

        self.chk_cck_reset_sessionend_2 = QCheckBox(self.gridLayoutWidget_8)
        self.chk_cck_reset_sessionend_2.setObjectName(u"chk_cck_reset_sessionend_2")

        self.gridLayout_5.addWidget(self.chk_cck_reset_sessionend_2, 7, 0, 1, 1)

        self.label_34 = QLabel(self.gridLayoutWidget_8)
        self.label_34.setObjectName(u"label_34")

        self.gridLayout_5.addWidget(self.label_34, 6, 0, 1, 1)

        self.pb_finalize_shtr = QPushButton(self.tab_10)
        self.pb_finalize_shtr.setObjectName(u"pb_finalize_shtr")
        self.pb_finalize_shtr.setGeometry(QRect(20, 220, 75, 24))
        self.tabWidget_4.addTab(self.tab_10, "")
        self.tab_13 = QWidget()
        self.tab_13.setObjectName(u"tab_13")
        self.tb_hebp = QTableWidget(self.tab_13)
        if (self.tb_hebp.columnCount() < 1):
            self.tb_hebp.setColumnCount(1)
        __qtablewidgetitem16 = QTableWidgetItem()
        self.tb_hebp.setHorizontalHeaderItem(0, __qtablewidgetitem16)
        self.tb_hebp.setObjectName(u"tb_hebp")
        self.tb_hebp.setGeometry(QRect(370, 30, 261, 91))
        self.tb_hebp.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.label_35 = QLabel(self.tab_13)
        self.label_35.setObjectName(u"label_35")
        self.label_35.setGeometry(QRect(370, 10, 101, 20))
        self.tb_heef = QTableWidget(self.tab_13)
        if (self.tb_heef.columnCount() < 1):
            self.tb_heef.setColumnCount(1)
        __qtablewidgetitem17 = QTableWidgetItem()
        self.tb_heef.setHorizontalHeaderItem(0, __qtablewidgetitem17)
        self.tb_heef.setObjectName(u"tb_heef")
        self.tb_heef.setGeometry(QRect(370, 160, 261, 91))
        self.tb_heef.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.label_36 = QLabel(self.tab_13)
        self.label_36.setObjectName(u"label_36")
        self.label_36.setGeometry(QRect(370, 140, 101, 20))
        self.horizontalLayoutWidget_19 = QWidget(self.tab_13)
        self.horizontalLayoutWidget_19.setObjectName(u"horizontalLayoutWidget_19")
        self.horizontalLayoutWidget_19.setGeometry(QRect(639, 56, 201, 31))
        self.grid_addremove_20 = QHBoxLayout(self.horizontalLayoutWidget_19)
        self.grid_addremove_20.setObjectName(u"grid_addremove_20")
        self.grid_addremove_20.setContentsMargins(0, 0, 0, 0)
        self.pb_rem_hebp = QPushButton(self.horizontalLayoutWidget_19)
        self.pb_rem_hebp.setObjectName(u"pb_rem_hebp")

        self.grid_addremove_20.addWidget(self.pb_rem_hebp)

        self.pb_add_hebp = QPushButton(self.horizontalLayoutWidget_19)
        self.pb_add_hebp.setObjectName(u"pb_add_hebp")

        self.grid_addremove_20.addWidget(self.pb_add_hebp)

        self.box_hebp = QComboBox(self.tab_13)
        self.box_hebp.setObjectName(u"box_hebp")
        self.box_hebp.setGeometry(QRect(640, 30, 201, 22))
        self.box_heef = QComboBox(self.tab_13)
        self.box_heef.setObjectName(u"box_heef")
        self.box_heef.setGeometry(QRect(641, 164, 201, 22))
        self.horizontalLayoutWidget_20 = QWidget(self.tab_13)
        self.horizontalLayoutWidget_20.setObjectName(u"horizontalLayoutWidget_20")
        self.horizontalLayoutWidget_20.setGeometry(QRect(640, 190, 201, 31))
        self.grid_addremove_22 = QHBoxLayout(self.horizontalLayoutWidget_20)
        self.grid_addremove_22.setObjectName(u"grid_addremove_22")
        self.grid_addremove_22.setContentsMargins(0, 0, 0, 0)
        self.pb_rem_heef = QPushButton(self.horizontalLayoutWidget_20)
        self.pb_rem_heef.setObjectName(u"pb_rem_heef")

        self.grid_addremove_22.addWidget(self.pb_rem_heef)

        self.pb_add_heef = QPushButton(self.horizontalLayoutWidget_20)
        self.pb_add_heef.setObjectName(u"pb_add_heef")

        self.grid_addremove_22.addWidget(self.pb_add_heef)

        self.gridLayoutWidget_9 = QWidget(self.tab_13)
        self.gridLayoutWidget_9.setObjectName(u"gridLayoutWidget_9")
        self.gridLayoutWidget_9.setGeometry(QRect(10, 10, 351, 181))
        self.gridLayout_6 = QGridLayout(self.gridLayoutWidget_9)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.gridLayout_6.setContentsMargins(0, 0, 0, 0)
        self.box_encomp_he = QComboBox(self.gridLayoutWidget_9)
        self.box_encomp_he.setObjectName(u"box_encomp_he")

        self.gridLayout_6.addWidget(self.box_encomp_he, 0, 1, 1, 1)

        self.fld_timeval_he = QLineEdit(self.gridLayoutWidget_9)
        self.fld_timeval_he.setObjectName(u"fld_timeval_he")

        self.gridLayout_6.addWidget(self.fld_timeval_he, 7, 1, 1, 1)

        self.fld_hydval_he = QLineEdit(self.gridLayoutWidget_9)
        self.fld_hydval_he.setObjectName(u"fld_hydval_he")

        self.gridLayout_6.addWidget(self.fld_hydval_he, 3, 1, 1, 1)

        self.fld_enval_he = QLineEdit(self.gridLayoutWidget_9)
        self.fld_enval_he.setObjectName(u"fld_enval_he")

        self.gridLayout_6.addWidget(self.fld_enval_he, 1, 1, 1, 1)

        self.box_hydcomp_he = QComboBox(self.gridLayoutWidget_9)
        self.box_hydcomp_he.setObjectName(u"box_hydcomp_he")

        self.gridLayout_6.addWidget(self.box_hydcomp_he, 2, 1, 1, 1)

        self.box_timecomp_he = QComboBox(self.gridLayoutWidget_9)
        self.box_timecomp_he.setObjectName(u"box_timecomp_he")

        self.gridLayout_6.addWidget(self.box_timecomp_he, 4, 1, 1, 1)

        self.label_64 = QLabel(self.gridLayoutWidget_9)
        self.label_64.setObjectName(u"label_64")

        self.gridLayout_6.addWidget(self.label_64, 0, 0, 1, 1)

        self.label_65 = QLabel(self.gridLayoutWidget_9)
        self.label_65.setObjectName(u"label_65")

        self.gridLayout_6.addWidget(self.label_65, 1, 0, 1, 1)

        self.label_66 = QLabel(self.gridLayoutWidget_9)
        self.label_66.setObjectName(u"label_66")

        self.gridLayout_6.addWidget(self.label_66, 2, 0, 1, 1)

        self.label_67 = QLabel(self.gridLayoutWidget_9)
        self.label_67.setObjectName(u"label_67")

        self.gridLayout_6.addWidget(self.label_67, 3, 0, 1, 1)

        self.label_68 = QLabel(self.gridLayoutWidget_9)
        self.label_68.setObjectName(u"label_68")

        self.gridLayout_6.addWidget(self.label_68, 4, 0, 1, 1)

        self.label_69 = QLabel(self.gridLayoutWidget_9)
        self.label_69.setObjectName(u"label_69")

        self.gridLayout_6.addWidget(self.label_69, 7, 0, 1, 1)

        self.pb_finalize_he = QPushButton(self.tab_13)
        self.pb_finalize_he.setObjectName(u"pb_finalize_he")
        self.pb_finalize_he.setGeometry(QRect(10, 200, 75, 24))
        self.tabWidget_4.addTab(self.tab_13, "")
        self.tab_14 = QWidget()
        self.tab_14.setObjectName(u"tab_14")
        self.box_hb = QComboBox(self.tab_14)
        self.box_hb.setObjectName(u"box_hb")
        self.box_hb.setGeometry(QRect(281, 24, 201, 22))
        self.tb_hb = QTableWidget(self.tab_14)
        if (self.tb_hb.columnCount() < 1):
            self.tb_hb.setColumnCount(1)
        __qtablewidgetitem18 = QTableWidgetItem()
        self.tb_hb.setHorizontalHeaderItem(0, __qtablewidgetitem18)
        self.tb_hb.setObjectName(u"tb_hb")
        self.tb_hb.setGeometry(QRect(11, 24, 261, 91))
        self.tb_hb.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.label_70 = QLabel(self.tab_14)
        self.label_70.setObjectName(u"label_70")
        self.label_70.setGeometry(QRect(11, 4, 101, 20))
        self.horizontalLayoutWidget_21 = QWidget(self.tab_14)
        self.horizontalLayoutWidget_21.setObjectName(u"horizontalLayoutWidget_21")
        self.horizontalLayoutWidget_21.setGeometry(QRect(280, 50, 201, 31))
        self.grid_addremove_23 = QHBoxLayout(self.horizontalLayoutWidget_21)
        self.grid_addremove_23.setObjectName(u"grid_addremove_23")
        self.grid_addremove_23.setContentsMargins(0, 0, 0, 0)
        self.pb_rem_hb = QPushButton(self.horizontalLayoutWidget_21)
        self.pb_rem_hb.setObjectName(u"pb_rem_hb")

        self.grid_addremove_23.addWidget(self.pb_rem_hb)

        self.pb_add_hb = QPushButton(self.horizontalLayoutWidget_21)
        self.pb_add_hb.setObjectName(u"pb_add_hb")

        self.grid_addremove_23.addWidget(self.pb_add_hb)

        self.pb_finalize_hb = QPushButton(self.tab_14)
        self.pb_finalize_hb.setObjectName(u"pb_finalize_hb")
        self.pb_finalize_hb.setGeometry(QRect(10, 130, 75, 24))
        self.tabWidget_4.addTab(self.tab_14, "")
        self.tab_23 = QWidget()
        self.tab_23.setObjectName(u"tab_23")
        self.gridLayoutWidget_10 = QWidget(self.tab_23)
        self.gridLayoutWidget_10.setObjectName(u"gridLayoutWidget_10")
        self.gridLayoutWidget_10.setGeometry(QRect(10, 20, 301, 54))
        self.gridLayout_18 = QGridLayout(self.gridLayoutWidget_10)
        self.gridLayout_18.setObjectName(u"gridLayout_18")
        self.gridLayout_18.setContentsMargins(0, 0, 0, 0)
        self.fld_fl_zone = QLineEdit(self.gridLayoutWidget_10)
        self.fld_fl_zone.setObjectName(u"fld_fl_zone")

        self.gridLayout_18.addWidget(self.fld_fl_zone, 0, 1, 1, 1)

        self.label_71 = QLabel(self.gridLayoutWidget_10)
        self.label_71.setObjectName(u"label_71")

        self.gridLayout_18.addWidget(self.label_71, 0, 0, 1, 1)

        self.pb_finalize_fl = QPushButton(self.tab_23)
        self.pb_finalize_fl.setObjectName(u"pb_finalize_fl")
        self.pb_finalize_fl.setGeometry(QRect(10, 80, 102, 24))
        self.tabWidget_4.addTab(self.tab_23, "")
        self.tab_24 = QWidget()
        self.tab_24.setObjectName(u"tab_24")
        self.tb_iz = QTableWidget(self.tab_24)
        if (self.tb_iz.columnCount() < 1):
            self.tb_iz.setColumnCount(1)
        __qtablewidgetitem19 = QTableWidgetItem()
        self.tb_iz.setHorizontalHeaderItem(0, __qtablewidgetitem19)
        self.tb_iz.setObjectName(u"tb_iz")
        self.tb_iz.setGeometry(QRect(11, 34, 261, 91))
        self.tb_iz.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.label_72 = QLabel(self.tab_24)
        self.label_72.setObjectName(u"label_72")
        self.label_72.setGeometry(QRect(11, 14, 101, 20))
        self.horizontalLayoutWidget_22 = QWidget(self.tab_24)
        self.horizontalLayoutWidget_22.setObjectName(u"horizontalLayoutWidget_22")
        self.horizontalLayoutWidget_22.setGeometry(QRect(280, 60, 201, 31))
        self.grid_addremove_24 = QHBoxLayout(self.horizontalLayoutWidget_22)
        self.grid_addremove_24.setObjectName(u"grid_addremove_24")
        self.grid_addremove_24.setContentsMargins(0, 0, 0, 0)
        self.pb_rem_iz = QPushButton(self.horizontalLayoutWidget_22)
        self.pb_rem_iz.setObjectName(u"pb_rem_iz")

        self.grid_addremove_24.addWidget(self.pb_rem_iz)

        self.pb_add_iz = QPushButton(self.horizontalLayoutWidget_22)
        self.pb_add_iz.setObjectName(u"pb_add_iz")

        self.grid_addremove_24.addWidget(self.pb_add_iz)

        self.pb_finalize_iz = QPushButton(self.tab_24)
        self.pb_finalize_iz.setObjectName(u"pb_finalize_iz")
        self.pb_finalize_iz.setGeometry(QRect(10, 140, 102, 24))
        self.fld_iz = QLineEdit(self.tab_24)
        self.fld_iz.setObjectName(u"fld_iz")
        self.fld_iz.setGeometry(QRect(280, 30, 201, 22))
        self.tabWidget_4.addTab(self.tab_24, "")
        self.gridLayoutWidget_20 = QWidget(self.tab_6)
        self.gridLayoutWidget_20.setObjectName(u"gridLayoutWidget_20")
        self.gridLayoutWidget_20.setGeometry(QRect(10, 180, 251, 138))
        self.grid_quantity_3 = QGridLayout(self.gridLayoutWidget_20)
        self.grid_quantity_3.setObjectName(u"grid_quantity_3")
        self.grid_quantity_3.setContentsMargins(0, 0, 0, 0)
        self.box_ff = QComboBox(self.gridLayoutWidget_20)
        self.box_ff.setObjectName(u"box_ff")

        self.grid_quantity_3.addWidget(self.box_ff, 2, 1, 1, 1)

        self.label_59 = QLabel(self.gridLayoutWidget_20)
        self.label_59.setObjectName(u"label_59")

        self.grid_quantity_3.addWidget(self.label_59, 1, 0, 1, 1)

        self.fld_quantity_cc = QLineEdit(self.gridLayoutWidget_20)
        self.fld_quantity_cc.setObjectName(u"fld_quantity_cc")

        self.grid_quantity_3.addWidget(self.fld_quantity_cc, 0, 1, 1, 1)

        self.pb_remove_cc = QPushButton(self.gridLayoutWidget_20)
        self.pb_remove_cc.setObjectName(u"pb_remove_cc")

        self.grid_quantity_3.addWidget(self.pb_remove_cc, 4, 1, 1, 1)

        self.lb_quantity_cck = QLabel(self.gridLayoutWidget_20)
        self.lb_quantity_cck.setObjectName(u"lb_quantity_cck")

        self.grid_quantity_3.addWidget(self.lb_quantity_cck, 0, 0, 1, 1)

        self.pb_finalize_cc = QPushButton(self.gridLayoutWidget_20)
        self.pb_finalize_cc.setObjectName(u"pb_finalize_cc")

        self.grid_quantity_3.addWidget(self.pb_finalize_cc, 4, 0, 1, 1)

        self.box_cc_qtlab = QComboBox(self.gridLayoutWidget_20)
        self.box_cc_qtlab.setObjectName(u"box_cc_qtlab")

        self.grid_quantity_3.addWidget(self.box_cc_qtlab, 1, 1, 1, 1)

        self.label_53 = QLabel(self.gridLayoutWidget_20)
        self.label_53.setObjectName(u"label_53")

        self.grid_quantity_3.addWidget(self.label_53, 2, 0, 1, 1)

        self.fld_parentid_cc = QLineEdit(self.gridLayoutWidget_20)
        self.fld_parentid_cc.setObjectName(u"fld_parentid_cc")

        self.grid_quantity_3.addWidget(self.fld_parentid_cc, 3, 1, 1, 1)

        self.label_60 = QLabel(self.gridLayoutWidget_20)
        self.label_60.setObjectName(u"label_60")

        self.grid_quantity_3.addWidget(self.label_60, 3, 0, 1, 1)

        self.tb_cc = QTableWidget(self.tab_6)
        if (self.tb_cc.columnCount() < 2):
            self.tb_cc.setColumnCount(2)
        __qtablewidgetitem20 = QTableWidgetItem()
        self.tb_cc.setHorizontalHeaderItem(0, __qtablewidgetitem20)
        __qtablewidgetitem21 = QTableWidgetItem()
        self.tb_cc.setHorizontalHeaderItem(1, __qtablewidgetitem21)
        self.tb_cc.setObjectName(u"tb_cc")
        self.tb_cc.setGeometry(QRect(10, 40, 301, 101))
        self.tb_cc.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tb_cc.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.pb_edit_cc = QPushButton(self.tab_6)
        self.pb_edit_cc.setObjectName(u"pb_edit_cc")
        self.pb_edit_cc.setGeometry(QRect(10, 146, 301, 26))
        self.tabWidget.addTab(self.tab_6, "")
        self.tab_handover_item = QWidget()
        self.tab_handover_item.setObjectName(u"tab_handover_item")
        self.gridLayoutWidget_3 = QWidget(self.tab_handover_item)
        self.gridLayoutWidget_3.setObjectName(u"gridLayoutWidget_3")
        self.gridLayoutWidget_3.setGeometry(QRect(10, 10, 331, 270))
        self.grid_fields2 = QGridLayout(self.gridLayoutWidget_3)
        self.grid_fields2.setObjectName(u"grid_fields2")
        self.grid_fields2.setContentsMargins(0, 0, 0, 0)
        self.lb_quantity_2 = QLabel(self.gridLayoutWidget_3)
        self.lb_quantity_2.setObjectName(u"lb_quantity_2")

        self.grid_fields2.addWidget(self.lb_quantity_2, 5, 0, 1, 1)

        self.fld_mindur_it = QLineEdit(self.gridLayoutWidget_3)
        self.fld_mindur_it.setObjectName(u"fld_mindur_it")

        self.grid_fields2.addWidget(self.fld_mindur_it, 3, 1, 1, 1)

        self.box_hofind_it = QComboBox(self.gridLayoutWidget_3)
        self.box_hofind_it.setObjectName(u"box_hofind_it")

        self.grid_fields2.addWidget(self.box_hofind_it, 0, 1, 1, 1)

        self.label_6 = QLabel(self.gridLayoutWidget_3)
        self.label_6.setObjectName(u"label_6")

        self.grid_fields2.addWidget(self.label_6, 0, 0, 1, 1)

        self.lb_maxdur = QLabel(self.gridLayoutWidget_3)
        self.lb_maxdur.setObjectName(u"lb_maxdur")

        self.grid_fields2.addWidget(self.lb_maxdur, 2, 0, 1, 1)

        self.fld_maxdur_it = QLineEdit(self.gridLayoutWidget_3)
        self.fld_maxdur_it.setObjectName(u"fld_maxdur_it")

        self.grid_fields2.addWidget(self.fld_maxdur_it, 2, 1, 1, 1)

        self.label_54 = QLabel(self.gridLayoutWidget_3)
        self.label_54.setObjectName(u"label_54")

        self.grid_fields2.addWidget(self.label_54, 7, 0, 1, 1)

        self.fld_dogtaglev_it = QLineEdit(self.gridLayoutWidget_3)
        self.fld_dogtaglev_it.setObjectName(u"fld_dogtaglev_it")

        self.grid_fields2.addWidget(self.fld_dogtaglev_it, 1, 1, 1, 1)

        self.box_only_fir_2 = QLabel(self.gridLayoutWidget_3)
        self.box_only_fir_2.setObjectName(u"box_only_fir_2")

        self.grid_fields2.addWidget(self.box_only_fir_2, 4, 0, 1, 1)

        self.fld_parentid_it = QLineEdit(self.gridLayoutWidget_3)
        self.fld_parentid_it.setObjectName(u"fld_parentid_it")

        self.grid_fields2.addWidget(self.fld_parentid_it, 9, 1, 1, 1)

        self.box_ff_it = QComboBox(self.gridLayoutWidget_3)
        self.box_ff_it.setObjectName(u"box_ff_it")

        self.grid_fields2.addWidget(self.box_ff_it, 7, 1, 1, 1)

        self.box_only_fir_it = QComboBox(self.gridLayoutWidget_3)
        self.box_only_fir_it.setObjectName(u"box_only_fir_it")

        self.grid_fields2.addWidget(self.box_only_fir_it, 4, 1, 1, 1)

        self.fld_quantity_it = QLineEdit(self.gridLayoutWidget_3)
        self.fld_quantity_it.setObjectName(u"fld_quantity_it")

        self.grid_fields2.addWidget(self.fld_quantity_it, 5, 1, 1, 1)

        self.label = QLabel(self.gridLayoutWidget_3)
        self.label.setObjectName(u"label")

        self.grid_fields2.addWidget(self.label, 1, 0, 1, 1)

        self.lb_mindur = QLabel(self.gridLayoutWidget_3)
        self.lb_mindur.setObjectName(u"lb_mindur")

        self.grid_fields2.addWidget(self.lb_mindur, 3, 0, 1, 1)

        self.label_61 = QLabel(self.gridLayoutWidget_3)
        self.label_61.setObjectName(u"label_61")

        self.grid_fields2.addWidget(self.label_61, 9, 0, 1, 1)

        self.lb_itemid_list = QLabel(self.tab_handover_item)
        self.lb_itemid_list.setObjectName(u"lb_itemid_list")
        self.lb_itemid_list.setGeometry(QRect(370, 10, 231, 16))
        self.gridLayoutWidget_4 = QWidget(self.tab_handover_item)
        self.gridLayoutWidget_4.setObjectName(u"gridLayoutWidget_4")
        self.gridLayoutWidget_4.setGeometry(QRect(370, 150, 311, 31))
        self.grid_itemid = QGridLayout(self.gridLayoutWidget_4)
        self.grid_itemid.setObjectName(u"grid_itemid")
        self.grid_itemid.setContentsMargins(0, 0, 0, 0)
        self.lb_itemid = QLabel(self.gridLayoutWidget_4)
        self.lb_itemid.setObjectName(u"lb_itemid")

        self.grid_itemid.addWidget(self.lb_itemid, 0, 0, 1, 1)

        self.fld_itemid_it = QLineEdit(self.gridLayoutWidget_4)
        self.fld_itemid_it.setObjectName(u"fld_itemid_it")

        self.grid_itemid.addWidget(self.fld_itemid_it, 0, 1, 1, 1)

        self.horizontalLayoutWidget_2 = QWidget(self.tab_handover_item)
        self.horizontalLayoutWidget_2.setObjectName(u"horizontalLayoutWidget_2")
        self.horizontalLayoutWidget_2.setGeometry(QRect(370, 180, 311, 51))
        self.grid_add_remitem = QHBoxLayout(self.horizontalLayoutWidget_2)
        self.grid_add_remitem.setObjectName(u"grid_add_remitem")
        self.grid_add_remitem.setContentsMargins(0, 0, 0, 0)
        self.pb_additem_it = QPushButton(self.horizontalLayoutWidget_2)
        self.pb_additem_it.setObjectName(u"pb_additem_it")

        self.grid_add_remitem.addWidget(self.pb_additem_it)

        self.pb_remitem_it = QPushButton(self.horizontalLayoutWidget_2)
        self.pb_remitem_it.setObjectName(u"pb_remitem_it")

        self.grid_add_remitem.addWidget(self.pb_remitem_it)

        self.pb_finalize_it = QPushButton(self.tab_handover_item)
        self.pb_finalize_it.setObjectName(u"pb_finalize_it")
        self.pb_finalize_it.setGeometry(QRect(10, 290, 101, 24))
        self.tb_items = QTableWidget(self.tab_handover_item)
        if (self.tb_items.columnCount() < 1):
            self.tb_items.setColumnCount(1)
        __qtablewidgetitem22 = QTableWidgetItem()
        self.tb_items.setHorizontalHeaderItem(0, __qtablewidgetitem22)
        self.tb_items.setObjectName(u"tb_items")
        self.tb_items.setGeometry(QRect(370, 40, 311, 91))
        self.tabWidget.addTab(self.tab_handover_item, "")
        self.tb_Skill = QWidget()
        self.tb_Skill.setObjectName(u"tb_Skill")
        self.gridLayoutWidget_13 = QWidget(self.tb_Skill)
        self.gridLayoutWidget_13.setObjectName(u"gridLayoutWidget_13")
        self.gridLayoutWidget_13.setGeometry(QRect(10, 10, 261, 141))
        self.gridLayout = QGridLayout(self.gridLayoutWidget_13)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.box_ff_sk = QComboBox(self.gridLayoutWidget_13)
        self.box_ff_sk.setObjectName(u"box_ff_sk")

        self.gridLayout.addWidget(self.box_ff_sk, 3, 1, 1, 1)

        self.label_12 = QLabel(self.gridLayoutWidget_13)
        self.label_12.setObjectName(u"label_12")

        self.gridLayout.addWidget(self.label_12, 1, 0, 1, 1)

        self.label_55 = QLabel(self.gridLayoutWidget_13)
        self.label_55.setObjectName(u"label_55")

        self.gridLayout.addWidget(self.label_55, 3, 0, 1, 1)

        self.label_13 = QLabel(self.gridLayoutWidget_13)
        self.label_13.setObjectName(u"label_13")

        self.gridLayout.addWidget(self.label_13, 2, 0, 1, 1)

        self.label_11 = QLabel(self.gridLayoutWidget_13)
        self.label_11.setObjectName(u"label_11")

        self.gridLayout.addWidget(self.label_11, 0, 0, 1, 1)

        self.label_62 = QLabel(self.gridLayoutWidget_13)
        self.label_62.setObjectName(u"label_62")

        self.gridLayout.addWidget(self.label_62, 4, 0, 1, 1)

        self.fld_level_sk = QLineEdit(self.gridLayoutWidget_13)
        self.fld_level_sk.setObjectName(u"fld_level_sk")

        self.gridLayout.addWidget(self.fld_level_sk, 2, 1, 1, 1)

        self.box_compare_sk = QComboBox(self.gridLayoutWidget_13)
        self.box_compare_sk.setObjectName(u"box_compare_sk")

        self.gridLayout.addWidget(self.box_compare_sk, 0, 1, 1, 1)

        self.box_target_sk = QComboBox(self.gridLayoutWidget_13)
        self.box_target_sk.setObjectName(u"box_target_sk")

        self.gridLayout.addWidget(self.box_target_sk, 1, 1, 1, 1)

        self.fld_parentid_sk_2 = QLineEdit(self.gridLayoutWidget_13)
        self.fld_parentid_sk_2.setObjectName(u"fld_parentid_sk_2")

        self.gridLayout.addWidget(self.fld_parentid_sk_2, 4, 1, 1, 1)

        self.pb_finalize_sk = QPushButton(self.tb_Skill)
        self.pb_finalize_sk.setObjectName(u"pb_finalize_sk")
        self.pb_finalize_sk.setGeometry(QRect(10, 160, 75, 24))
        self.tabWidget.addTab(self.tb_Skill, "")
        self.tab_leave_item = QWidget()
        self.tab_leave_item.setObjectName(u"tab_leave_item")
        self.gridLayoutWidget_6 = QWidget(self.tab_leave_item)
        self.gridLayoutWidget_6.setObjectName(u"gridLayoutWidget_6")
        self.gridLayoutWidget_6.setGeometry(QRect(10, 10, 411, 298))
        self.grid_fields_4 = QGridLayout(self.gridLayoutWidget_6)
        self.grid_fields_4.setObjectName(u"grid_fields_4")
        self.grid_fields_4.setContentsMargins(0, 0, 0, 0)
        self.fld_mindur_li = QLineEdit(self.gridLayoutWidget_6)
        self.fld_mindur_li.setObjectName(u"fld_mindur_li")

        self.grid_fields_4.addWidget(self.fld_mindur_li, 3, 1, 1, 1)

        self.lb_quantity_3 = QLabel(self.gridLayoutWidget_6)
        self.lb_quantity_3.setObjectName(u"lb_quantity_3")

        self.grid_fields_4.addWidget(self.lb_quantity_3, 7, 0, 1, 1)

        self.fld_plant_time_li = QLineEdit(self.gridLayoutWidget_6)
        self.fld_plant_time_li.setObjectName(u"fld_plant_time_li")

        self.grid_fields_4.addWidget(self.fld_plant_time_li, 6, 1, 1, 1)

        self.lb_plant_time = QLabel(self.gridLayoutWidget_6)
        self.lb_plant_time.setObjectName(u"lb_plant_time")

        self.grid_fields_4.addWidget(self.lb_plant_time, 6, 0, 1, 1)

        self.lb_maxdur_2 = QLabel(self.gridLayoutWidget_6)
        self.lb_maxdur_2.setObjectName(u"lb_maxdur_2")

        self.grid_fields_4.addWidget(self.lb_maxdur_2, 4, 0, 1, 1)

        self.lb_mindur_2 = QLabel(self.gridLayoutWidget_6)
        self.lb_mindur_2.setObjectName(u"lb_mindur_2")

        self.grid_fields_4.addWidget(self.lb_mindur_2, 3, 0, 1, 1)

        self.box_ff_li = QComboBox(self.gridLayoutWidget_6)
        self.box_ff_li.setObjectName(u"box_ff_li")

        self.grid_fields_4.addWidget(self.box_ff_li, 8, 1, 1, 1)

        self.fld_dogtaglevel_li = QLineEdit(self.gridLayoutWidget_6)
        self.fld_dogtaglevel_li.setObjectName(u"fld_dogtaglevel_li")

        self.grid_fields_4.addWidget(self.fld_dogtaglevel_li, 1, 1, 1, 1)

        self.label_41 = QLabel(self.gridLayoutWidget_6)
        self.label_41.setObjectName(u"label_41")

        self.grid_fields_4.addWidget(self.label_41, 9, 0, 1, 1)

        self.label_18 = QLabel(self.gridLayoutWidget_6)
        self.label_18.setObjectName(u"label_18")

        self.grid_fields_4.addWidget(self.label_18, 1, 0, 1, 1)

        self.lb_zoneid = QLabel(self.gridLayoutWidget_6)
        self.lb_zoneid.setObjectName(u"lb_zoneid")

        self.grid_fields_4.addWidget(self.lb_zoneid, 0, 0, 1, 1)

        self.box_fir_li = QComboBox(self.gridLayoutWidget_6)
        self.box_fir_li.setObjectName(u"box_fir_li")

        self.grid_fields_4.addWidget(self.box_fir_li, 5, 1, 1, 1)

        self.fld_quantity_li = QLineEdit(self.gridLayoutWidget_6)
        self.fld_quantity_li.setObjectName(u"fld_quantity_li")

        self.grid_fields_4.addWidget(self.fld_quantity_li, 7, 1, 1, 1)

        self.fld_maxdur_li = QLineEdit(self.gridLayoutWidget_6)
        self.fld_maxdur_li.setObjectName(u"fld_maxdur_li")

        self.grid_fields_4.addWidget(self.fld_maxdur_li, 4, 1, 1, 1)

        self.lb_fir = QLabel(self.gridLayoutWidget_6)
        self.lb_fir.setObjectName(u"lb_fir")

        self.grid_fields_4.addWidget(self.lb_fir, 5, 0, 1, 1)

        self.fld_zoneid_li = QLineEdit(self.gridLayoutWidget_6)
        self.fld_zoneid_li.setObjectName(u"fld_zoneid_li")

        self.grid_fields_4.addWidget(self.fld_zoneid_li, 0, 1, 1, 1)

        self.label_56 = QLabel(self.gridLayoutWidget_6)
        self.label_56.setObjectName(u"label_56")

        self.grid_fields_4.addWidget(self.label_56, 8, 0, 1, 1)

        self.fld_parentid_li = QLineEdit(self.gridLayoutWidget_6)
        self.fld_parentid_li.setObjectName(u"fld_parentid_li")

        self.grid_fields_4.addWidget(self.fld_parentid_li, 9, 1, 1, 1)

        self.pb_finalize_li = QPushButton(self.tab_leave_item)
        self.pb_finalize_li.setObjectName(u"pb_finalize_li")
        self.pb_finalize_li.setGeometry(QRect(440, 240, 91, 24))
        self.horizontalLayoutWidget_12 = QWidget(self.tab_leave_item)
        self.horizontalLayoutWidget_12.setObjectName(u"horizontalLayoutWidget_12")
        self.horizontalLayoutWidget_12.setGeometry(QRect(440, 200, 301, 31))
        self.grid_addremove_12 = QHBoxLayout(self.horizontalLayoutWidget_12)
        self.grid_addremove_12.setObjectName(u"grid_addremove_12")
        self.grid_addremove_12.setContentsMargins(0, 0, 0, 0)
        self.pb_rem_li_target = QPushButton(self.horizontalLayoutWidget_12)
        self.pb_rem_li_target.setObjectName(u"pb_rem_li_target")

        self.grid_addremove_12.addWidget(self.pb_rem_li_target)

        self.pb_add_li_target = QPushButton(self.horizontalLayoutWidget_12)
        self.pb_add_li_target.setObjectName(u"pb_add_li_target")

        self.grid_addremove_12.addWidget(self.pb_add_li_target)

        self.lb_addedweps_10 = QLabel(self.tab_leave_item)
        self.lb_addedweps_10.setObjectName(u"lb_addedweps_10")
        self.lb_addedweps_10.setGeometry(QRect(450, 10, 161, 16))
        self.tb_li_target = QTableWidget(self.tab_leave_item)
        if (self.tb_li_target.columnCount() < 1):
            self.tb_li_target.setColumnCount(1)
        __qtablewidgetitem23 = QTableWidgetItem()
        self.tb_li_target.setHorizontalHeaderItem(0, __qtablewidgetitem23)
        self.tb_li_target.setObjectName(u"tb_li_target")
        self.tb_li_target.setGeometry(QRect(450, 40, 271, 101))
        self.tb_li_target.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.fld_li_target = QLineEdit(self.tab_leave_item)
        self.fld_li_target.setObjectName(u"fld_li_target")
        self.fld_li_target.setGeometry(QRect(450, 160, 269, 22))
        self.tabWidget.addTab(self.tab_leave_item, "")
        self.tab_7 = QWidget()
        self.tab_7.setObjectName(u"tab_7")
        self.gridLayoutWidget = QWidget(self.tab_7)
        self.gridLayoutWidget.setObjectName(u"gridLayoutWidget")
        self.gridLayoutWidget.setGeometry(QRect(10, 10, 341, 136))
        self.gridLayout_3 = QGridLayout(self.gridLayoutWidget)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setContentsMargins(0, 0, 0, 0)
        self.label_44 = QLabel(self.gridLayoutWidget)
        self.label_44.setObjectName(u"label_44")

        self.gridLayout_3.addWidget(self.label_44, 2, 0, 1, 1)

        self.label_43 = QLabel(self.gridLayoutWidget)
        self.label_43.setObjectName(u"label_43")

        self.gridLayout_3.addWidget(self.label_43, 1, 0, 1, 1)

        self.label_45 = QLabel(self.gridLayoutWidget)
        self.label_45.setObjectName(u"label_45")

        self.gridLayout_3.addWidget(self.label_45, 3, 0, 1, 1)

        self.box_ff_pb = QComboBox(self.gridLayoutWidget)
        self.box_ff_pb.setObjectName(u"box_ff_pb")

        self.gridLayout_3.addWidget(self.box_ff_pb, 4, 3, 1, 1)

        self.label_57 = QLabel(self.gridLayoutWidget)
        self.label_57.setObjectName(u"label_57")

        self.gridLayout_3.addWidget(self.label_57, 4, 0, 1, 1)

        self.sb_value_pb = QSpinBox(self.gridLayoutWidget)
        self.sb_value_pb.setObjectName(u"sb_value_pb")
        self.sb_value_pb.setMaximum(999999)

        self.gridLayout_3.addWidget(self.sb_value_pb, 2, 3, 1, 1)

        self.fld_zoneid_pb = QLineEdit(self.gridLayoutWidget)
        self.fld_zoneid_pb.setObjectName(u"fld_zoneid_pb")

        self.gridLayout_3.addWidget(self.fld_zoneid_pb, 3, 3, 1, 1)

        self.sb_time_pb = QSpinBox(self.gridLayoutWidget)
        self.sb_time_pb.setObjectName(u"sb_time_pb")
        self.sb_time_pb.setMaximum(9999999)

        self.gridLayout_3.addWidget(self.sb_time_pb, 1, 3, 1, 1)

        self.label_42 = QLabel(self.gridLayoutWidget)
        self.label_42.setObjectName(u"label_42")

        self.gridLayout_3.addWidget(self.label_42, 5, 0, 1, 1)

        self.fld_parentid_pb = QLineEdit(self.gridLayoutWidget)
        self.fld_parentid_pb.setObjectName(u"fld_parentid_pb")

        self.gridLayout_3.addWidget(self.fld_parentid_pb, 5, 3, 1, 1)

        self.pb_finalize_pb = QPushButton(self.tab_7)
        self.pb_finalize_pb.setObjectName(u"pb_finalize_pb")
        self.pb_finalize_pb.setGeometry(QRect(10, 160, 75, 24))
        self.tabWidget.addTab(self.tab_7, "")
        self.tab_8 = QWidget()
        self.tab_8.setObjectName(u"tab_8")
        self.label_2 = QLabel(self.tab_8)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(10, 10, 201, 16))
        self.pb_finalize_wa = QPushButton(self.tab_8)
        self.pb_finalize_wa.setObjectName(u"pb_finalize_wa")
        self.pb_finalize_wa.setGeometry(QRect(10, 40, 191, 24))
        self.tabWidget.addTab(self.tab_8, "")
        self.tab_trader_loyalty = QWidget()
        self.tab_trader_loyalty.setObjectName(u"tab_trader_loyalty")
        self.gridLayoutWidget_14 = QWidget(self.tab_trader_loyalty)
        self.gridLayoutWidget_14.setObjectName(u"gridLayoutWidget_14")
        self.gridLayoutWidget_14.setGeometry(QRect(10, 10, 311, 136))
        self.gridLayout_2 = QGridLayout(self.gridLayoutWidget_14)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.label_14 = QLabel(self.gridLayoutWidget_14)
        self.label_14.setObjectName(u"label_14")

        self.gridLayout_2.addWidget(self.label_14, 1, 0, 1, 1)

        self.box_target_tl = QComboBox(self.gridLayoutWidget_14)
        self.box_target_tl.setObjectName(u"box_target_tl")

        self.gridLayout_2.addWidget(self.box_target_tl, 1, 1, 1, 1)

        self.box_compare_tl = QComboBox(self.gridLayoutWidget_14)
        self.box_compare_tl.setObjectName(u"box_compare_tl")

        self.gridLayout_2.addWidget(self.box_compare_tl, 0, 1, 1, 1)

        self.label_16 = QLabel(self.gridLayoutWidget_14)
        self.label_16.setObjectName(u"label_16")

        self.gridLayout_2.addWidget(self.label_16, 2, 0, 1, 1)

        self.label_15 = QLabel(self.gridLayoutWidget_14)
        self.label_15.setObjectName(u"label_15")

        self.gridLayout_2.addWidget(self.label_15, 0, 0, 1, 1)

        self.fld_level_tl = QLineEdit(self.gridLayoutWidget_14)
        self.fld_level_tl.setObjectName(u"fld_level_tl")

        self.gridLayout_2.addWidget(self.fld_level_tl, 2, 1, 1, 1)

        self.label_58 = QLabel(self.gridLayoutWidget_14)
        self.label_58.setObjectName(u"label_58")

        self.gridLayout_2.addWidget(self.label_58, 3, 0, 1, 1)

        self.box_ff_tl = QComboBox(self.gridLayoutWidget_14)
        self.box_ff_tl.setObjectName(u"box_ff_tl")

        self.gridLayout_2.addWidget(self.box_ff_tl, 3, 1, 1, 1)

        self.label_63 = QLabel(self.gridLayoutWidget_14)
        self.label_63.setObjectName(u"label_63")

        self.gridLayout_2.addWidget(self.label_63, 4, 0, 1, 1)

        self.fld_parentid_tl = QLineEdit(self.gridLayoutWidget_14)
        self.fld_parentid_tl.setObjectName(u"fld_parentid_tl")

        self.gridLayout_2.addWidget(self.fld_parentid_tl, 4, 1, 1, 1)

        self.pb_finalize_tl = QPushButton(self.tab_trader_loyalty)
        self.pb_finalize_tl.setObjectName(u"pb_finalize_tl")
        self.pb_finalize_tl.setGeometry(QRect(10, 150, 75, 24))
        self.tabWidget.addTab(self.tab_trader_loyalty, "")
        self.tabWidget_2.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.tabWidget_3 = QTabWidget(self.tab_2)
        self.tabWidget_3.setObjectName(u"tabWidget_3")
        self.tabWidget_3.setGeometry(QRect(0, 0, 991, 371))
        self.tab_3 = QWidget()
        self.tab_3.setObjectName(u"tab_3")
        self.label_5 = QLabel(self.tab_3)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setGeometry(QRect(10, 530, 221, 16))
        self.gridLayoutWidget_22 = QWidget(self.tab_3)
        self.gridLayoutWidget_22.setObjectName(u"gridLayoutWidget_22")
        self.gridLayoutWidget_22.setGeometry(QRect(10, 10, 231, 71))
        self.gridLayout_10 = QGridLayout(self.gridLayoutWidget_22)
        self.gridLayout_10.setObjectName(u"gridLayout_10")
        self.gridLayout_10.setContentsMargins(0, 0, 0, 0)
        self.label_40 = QLabel(self.gridLayoutWidget_22)
        self.label_40.setObjectName(u"label_40")

        self.gridLayout_10.addWidget(self.label_40, 0, 0, 1, 1)

        self.label_46 = QLabel(self.gridLayoutWidget_22)
        self.label_46.setObjectName(u"label_46")

        self.gridLayout_10.addWidget(self.label_46, 1, 0, 1, 1)

        self.box_compare_lv = QComboBox(self.gridLayoutWidget_22)
        self.box_compare_lv.setObjectName(u"box_compare_lv")

        self.gridLayout_10.addWidget(self.box_compare_lv, 0, 1, 1, 1)

        self.fld_value_lv = QLineEdit(self.gridLayoutWidget_22)
        self.fld_value_lv.setObjectName(u"fld_value_lv")

        self.gridLayout_10.addWidget(self.fld_value_lv, 1, 1, 1, 1)

        self.pb_finalize_lv = QPushButton(self.tab_3)
        self.pb_finalize_lv.setObjectName(u"pb_finalize_lv")
        self.pb_finalize_lv.setGeometry(QRect(10, 90, 75, 24))
        self.tabWidget_3.addTab(self.tab_3, "")
        self.tab_5 = QWidget()
        self.tab_5.setObjectName(u"tab_5")
        self.gridLayoutWidget_25 = QWidget(self.tab_5)
        self.gridLayoutWidget_25.setObjectName(u"gridLayoutWidget_25")
        self.gridLayoutWidget_25.setGeometry(QRect(10, 10, 301, 91))
        self.gridLayout_13 = QGridLayout(self.gridLayoutWidget_25)
        self.gridLayout_13.setObjectName(u"gridLayout_13")
        self.gridLayout_13.setContentsMargins(0, 0, 0, 0)
        self.box_comparemethod_ts = QComboBox(self.gridLayoutWidget_25)
        self.box_comparemethod_ts.setObjectName(u"box_comparemethod_ts")

        self.gridLayout_13.addWidget(self.box_comparemethod_ts, 0, 1, 1, 1)

        self.fld_value_ts = QLineEdit(self.gridLayoutWidget_25)
        self.fld_value_ts.setObjectName(u"fld_value_ts")

        self.gridLayout_13.addWidget(self.fld_value_ts, 2, 1, 1, 1)

        self.label_19 = QLabel(self.gridLayoutWidget_25)
        self.label_19.setObjectName(u"label_19")

        self.gridLayout_13.addWidget(self.label_19, 0, 0, 1, 1)

        self.label_51 = QLabel(self.gridLayoutWidget_25)
        self.label_51.setObjectName(u"label_51")

        self.gridLayout_13.addWidget(self.label_51, 1, 0, 1, 1)

        self.label_52 = QLabel(self.gridLayoutWidget_25)
        self.label_52.setObjectName(u"label_52")

        self.gridLayout_13.addWidget(self.label_52, 2, 0, 1, 1)

        self.box_trader_ts = QComboBox(self.gridLayoutWidget_25)
        self.box_trader_ts.setObjectName(u"box_trader_ts")

        self.gridLayout_13.addWidget(self.box_trader_ts, 1, 1, 1, 1)

        self.pb_finalize_ts = QPushButton(self.tab_5)
        self.pb_finalize_ts.setObjectName(u"pb_finalize_ts")
        self.pb_finalize_ts.setGeometry(QRect(10, 110, 75, 24))
        self.tabWidget_3.addTab(self.tab_5, "")
        self.tabWidget_2.addTab(self.tab_2, "")
        self.tab_17 = QWidget()
        self.tab_17.setObjectName(u"tab_17")
        self.tabWidget_8 = QTabWidget(self.tab_17)
        self.tabWidget_8.setObjectName(u"tabWidget_8")
        self.tabWidget_8.setGeometry(QRect(0, 0, 1241, 351))
        self.tab_33 = QWidget()
        self.tab_33.setObjectName(u"tab_33")
        self.gridLayoutWidget_30 = QWidget(self.tab_33)
        self.gridLayoutWidget_30.setObjectName(u"gridLayoutWidget_30")
        self.gridLayoutWidget_30.setGeometry(QRect(10, 10, 301, 80))
        self.gridLayout_21 = QGridLayout(self.gridLayoutWidget_30)
        self.gridLayout_21.setObjectName(u"gridLayout_21")
        self.gridLayout_21.setContentsMargins(0, 0, 0, 0)
        self.label_76 = QLabel(self.gridLayoutWidget_30)
        self.label_76.setObjectName(u"label_76")

        self.gridLayout_21.addWidget(self.label_76, 1, 0, 1, 1)

        self.fld_avail_qs = QLineEdit(self.gridLayoutWidget_30)
        self.fld_avail_qs.setObjectName(u"fld_avail_qs")

        self.gridLayout_21.addWidget(self.fld_avail_qs, 0, 1, 1, 1)

        self.fld_tid_qs = QLineEdit(self.gridLayoutWidget_30)
        self.fld_tid_qs.setObjectName(u"fld_tid_qs")

        self.gridLayout_21.addWidget(self.fld_tid_qs, 1, 1, 1, 1)

        self.label_75 = QLabel(self.gridLayoutWidget_30)
        self.label_75.setObjectName(u"label_75")

        self.gridLayout_21.addWidget(self.label_75, 0, 0, 1, 1)

        self.label_47 = QLabel(self.gridLayoutWidget_30)
        self.label_47.setObjectName(u"label_47")

        self.gridLayout_21.addWidget(self.label_47, 2, 0, 1, 1)

        self.box_timing_qs = QComboBox(self.gridLayoutWidget_30)
        self.box_timing_qs.setObjectName(u"box_timing_qs")

        self.gridLayout_21.addWidget(self.box_timing_qs, 2, 1, 1, 1)

        self.pb_finalize_qs = QPushButton(self.tab_33)
        self.pb_finalize_qs.setObjectName(u"pb_finalize_qs")
        self.pb_finalize_qs.setGeometry(QRect(10, 110, 75, 24))
        self.label_77 = QLabel(self.tab_33)
        self.label_77.setObjectName(u"label_77")
        self.label_77.setGeometry(QRect(330, 50, 49, 16))
        self.gridLayoutWidget_31 = QWidget(self.tab_33)
        self.gridLayoutWidget_31.setObjectName(u"gridLayoutWidget_31")
        self.gridLayoutWidget_31.setGeometry(QRect(330, 10, 281, 31))
        self.gridLayout_22 = QGridLayout(self.gridLayoutWidget_31)
        self.gridLayout_22.setObjectName(u"gridLayout_22")
        self.gridLayout_22.setContentsMargins(0, 0, 0, 0)
        self.box_status_qs = QComboBox(self.gridLayoutWidget_31)
        self.box_status_qs.setObjectName(u"box_status_qs")

        self.gridLayout_22.addWidget(self.box_status_qs, 0, 1, 1, 1)

        self.label_78 = QLabel(self.gridLayoutWidget_31)
        self.label_78.setObjectName(u"label_78")

        self.gridLayout_22.addWidget(self.label_78, 0, 0, 1, 1)

        self.tb_status_qs = QTableWidget(self.tab_33)
        if (self.tb_status_qs.columnCount() < 1):
            self.tb_status_qs.setColumnCount(1)
        __qtablewidgetitem24 = QTableWidgetItem()
        self.tb_status_qs.setHorizontalHeaderItem(0, __qtablewidgetitem24)
        self.tb_status_qs.setObjectName(u"tb_status_qs")
        self.tb_status_qs.setGeometry(QRect(330, 80, 331, 81))
        self.tb_status_qs.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.gridLayoutWidget_32 = QWidget(self.tab_33)
        self.gridLayoutWidget_32.setObjectName(u"gridLayoutWidget_32")
        self.gridLayoutWidget_32.setGeometry(QRect(620, 10, 181, 31))
        self.gridLayout_23 = QGridLayout(self.gridLayoutWidget_32)
        self.gridLayout_23.setObjectName(u"gridLayout_23")
        self.gridLayout_23.setContentsMargins(0, 0, 0, 0)
        self.pb_addstatus_qs = QPushButton(self.gridLayoutWidget_32)
        self.pb_addstatus_qs.setObjectName(u"pb_addstatus_qs")

        self.gridLayout_23.addWidget(self.pb_addstatus_qs, 0, 0, 1, 1)

        self.pb_remstatus_qs = QPushButton(self.gridLayoutWidget_32)
        self.pb_remstatus_qs.setObjectName(u"pb_remstatus_qs")

        self.gridLayout_23.addWidget(self.pb_remstatus_qs, 0, 1, 1, 1)

        self.tabWidget_8.addTab(self.tab_33, "")
        self.tabWidget_2.addTab(self.tab_17, "")
        self.textBrowser = QTextBrowser(self.centralwidget)
        self.textBrowser.setObjectName(u"textBrowser")
        self.textBrowser.setGeometry(QRect(340, 490, 371, 111))
        self.fld_taskid_gen = QLineEdit(self.centralwidget)
        self.fld_taskid_gen.setObjectName(u"fld_taskid_gen")
        self.fld_taskid_gen.setGeometry(QRect(10, 590, 321, 22))
        self.label_37 = QLabel(self.centralwidget)
        self.label_37.setObjectName(u"label_37")
        self.label_37.setGeometry(QRect(10, 570, 141, 16))
        self.gridLayoutWidget_15 = QWidget(self.centralwidget)
        self.gridLayoutWidget_15.setObjectName(u"gridLayoutWidget_15")
        self.gridLayoutWidget_15.setGeometry(QRect(10, 410, 241, 31))
        self.gridLayout_9 = QGridLayout(self.gridLayoutWidget_15)
        self.gridLayout_9.setObjectName(u"gridLayout_9")
        self.gridLayout_9.setContentsMargins(0, 0, 0, 0)
        self.label_38 = QLabel(self.gridLayoutWidget_15)
        self.label_38.setObjectName(u"label_38")

        self.gridLayout_9.addWidget(self.label_38, 0, 0, 1, 1)

        self.fld_visibility_targetid = QLineEdit(self.gridLayoutWidget_15)
        self.fld_visibility_targetid.setObjectName(u"fld_visibility_targetid")

        self.gridLayout_9.addWidget(self.fld_visibility_targetid, 0, 1, 1, 1)

        self.tb_vis = QTableWidget(self.centralwidget)
        if (self.tb_vis.columnCount() < 1):
            self.tb_vis.setColumnCount(1)
        __qtablewidgetitem25 = QTableWidgetItem()
        self.tb_vis.setHorizontalHeaderItem(0, __qtablewidgetitem25)
        self.tb_vis.setObjectName(u"tb_vis")
        self.tb_vis.setGeometry(QRect(10, 490, 321, 71))
        self.gridLayoutWidget_28 = QWidget(self.centralwidget)
        self.gridLayoutWidget_28.setObjectName(u"gridLayoutWidget_28")
        self.gridLayoutWidget_28.setGeometry(QRect(10, 450, 241, 31))
        self.gridLayout_16 = QGridLayout(self.gridLayoutWidget_28)
        self.gridLayout_16.setObjectName(u"gridLayout_16")
        self.gridLayout_16.setContentsMargins(0, 0, 0, 0)
        self.pb_addvis = QPushButton(self.gridLayoutWidget_28)
        self.pb_addvis.setObjectName(u"pb_addvis")

        self.gridLayout_16.addWidget(self.pb_addvis, 0, 0, 1, 1)

        self.pb_remvis = QPushButton(self.gridLayoutWidget_28)
        self.pb_remvis.setObjectName(u"pb_remvis")

        self.gridLayout_16.addWidget(self.pb_remvis, 0, 1, 1, 1)

        self.label_10 = QLabel(self.centralwidget)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setGeometry(QRect(10, 380, 111, 16))
        TaskWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(TaskWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1469, 22))
        TaskWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(TaskWindow)
        self.statusbar.setObjectName(u"statusbar")
        TaskWindow.setStatusBar(self.statusbar)

        self.retranslateUi(TaskWindow)

        self.tabWidget_2.setCurrentIndex(0)
        self.tabWidget.setCurrentIndex(0)
        self.tabWidget_4.setCurrentIndex(0)
        self.tabWidget_5.setCurrentIndex(0)
        self.tabWidget_6.setCurrentIndex(4)
        self.tabWidget_3.setCurrentIndex(0)
        self.tabWidget_8.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(TaskWindow)
    # setupUi

    def retranslateUi(self, TaskWindow):
        TaskWindow.setWindowTitle(QCoreApplication.translate("TaskWindow", u"Task Builder", None))
        self.lb_cond.setText(QCoreApplication.translate("TaskWindow", u"Conditions:", None))
        self.lb_zoneid_7.setText(QCoreApplication.translate("TaskWindow", u"Zone ID:", None))
        self.pb_finalize_ccvp.setText(QCoreApplication.translate("TaskWindow", u"Finalize Condition", None))
        self.tabWidget_4.setTabText(self.tabWidget_4.indexOf(self.tab_11), QCoreApplication.translate("TaskWindow", u"VisitPlace", None))
        self.lb_time_to_cck.setText(QCoreApplication.translate("TaskWindow", u"Time To:", None))
        self.lb_time_from_cck.setText(QCoreApplication.translate("TaskWindow", u"Time From:", None))
        self.lb_dist_cck.setText(QCoreApplication.translate("TaskWindow", u"Distance:", None))
        self.lb_dist_compare_cck.setText(QCoreApplication.translate("TaskWindow", u"Distance Compare:", None))
        self.chk_cck_usetarget.setText(QCoreApplication.translate("TaskWindow", u"Use Target", None))
        self.pb_finalize_cck.setText(QCoreApplication.translate("TaskWindow", u"Finalize Condition", None))
        self.chk_cck_reset_sessionend.setText(QCoreApplication.translate("TaskWindow", u"Reset on Session End", None))
        self.pb_removewep_cck.setText(QCoreApplication.translate("TaskWindow", u"Remove Selected", None))
        self.pb_addwep_cck.setText(QCoreApplication.translate("TaskWindow", u"Add", None))
        ___qtablewidgetitem = self.tb_wep.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("TaskWindow", u"name", None));
        self.lb_addedweps_3.setText(QCoreApplication.translate("TaskWindow", u"Added Weapons:", None))
        self.tabWidget_5.setTabText(self.tabWidget_5.indexOf(self.tab_15), QCoreApplication.translate("TaskWindow", u"Weapons", None))
        ___qtablewidgetitem1 = self.tb_targetrole.horizontalHeaderItem(0)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("TaskWindow", u"name", None));
        self.pb_removetr_cck.setText(QCoreApplication.translate("TaskWindow", u"Remove Selected", None))
        self.pb_addtr_cck.setText(QCoreApplication.translate("TaskWindow", u"Add", None))
        self.lb_addedweps_6.setText(QCoreApplication.translate("TaskWindow", u"Added Target Roles:", None))
        self.tabWidget_5.setTabText(self.tabWidget_5.indexOf(self.tab_18), QCoreApplication.translate("TaskWindow", u"Target Roles", None))
        ___qtablewidgetitem2 = self.tb_bodypart.horizontalHeaderItem(0)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("TaskWindow", u"name", None));
        self.pb_rembp_cck.setText(QCoreApplication.translate("TaskWindow", u"Remove Selected", None))
        self.pb_addbp_cck.setText(QCoreApplication.translate("TaskWindow", u"Add", None))
        self.lb_addedweps_7.setText(QCoreApplication.translate("TaskWindow", u"Added Body Parts:", None))
        self.tabWidget_5.setTabText(self.tabWidget_5.indexOf(self.tab_16), QCoreApplication.translate("TaskWindow", u"Body Parts", None))
        ___qtablewidgetitem3 = self.tb_incmods.horizontalHeaderItem(0)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("TaskWindow", u"name", None));
        self.pb_rem_imod.setText(QCoreApplication.translate("TaskWindow", u"Remove Selected", None))
        self.pb_add_imod.setText(QCoreApplication.translate("TaskWindow", u"Add", None))
        self.lb_addedweps_8.setText(QCoreApplication.translate("TaskWindow", u"Added Inclusive Mods:", None))
        self.textBrowser_3.setHtml(QCoreApplication.translate("TaskWindow", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Segoe UI'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">The killing weapon must have all attachments to count.</p></body></html>", None))
        self.tabWidget_5.setTabText(self.tabWidget_5.indexOf(self.tab_19), QCoreApplication.translate("TaskWindow", u"Mods (Include)", None))
        ___qtablewidgetitem4 = self.tb_excmods.horizontalHeaderItem(0)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("TaskWindow", u"name", None));
        self.pb_rem_emod.setText(QCoreApplication.translate("TaskWindow", u"Remove Selected", None))
        self.pb_add_emod.setText(QCoreApplication.translate("TaskWindow", u"Add", None))
        self.lb_addedweps_9.setText(QCoreApplication.translate("TaskWindow", u"Added Exclusive Mods:", None))
        self.textBrowser_2.setHtml(QCoreApplication.translate("TaskWindow", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Segoe UI'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">If the killing weapon has any of these attachments, the kill will not count.</p></body></html>", None))
        self.tabWidget_5.setTabText(self.tabWidget_5.indexOf(self.tab_26), QCoreApplication.translate("TaskWindow", u"Mods (Exclude)", None))
        self.tabWidget_4.setTabText(self.tabWidget_4.indexOf(self.tab_12), QCoreApplication.translate("TaskWindow", u"Kills", None))
        self.label_39.setText(QCoreApplication.translate("TaskWindow", u"Status", None))
        self.pb_cces_add.setText(QCoreApplication.translate("TaskWindow", u"Add", None))
        self.label_8.setText(QCoreApplication.translate("TaskWindow", u"Statuses:", None))
        self.pb_finalize_cces.setText(QCoreApplication.translate("TaskWindow", u"Finalize Condition", None))
        self.pb_status_rem_cces.setText(QCoreApplication.translate("TaskWindow", u"Remove Selected Status", None))
        ___qtablewidgetitem5 = self.tb_cces.horizontalHeaderItem(0)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("TaskWindow", u"status", None));
        self.tabWidget_4.setTabText(self.tabWidget_4.indexOf(self.tab_20), QCoreApplication.translate("TaskWindow", u"ExitStatus", None))
        self.label_3.setText(QCoreApplication.translate("TaskWindow", u"Exit Name", None))
        self.pb_finalize_ccen.setText(QCoreApplication.translate("TaskWindow", u"Finalize Condition", None))
        self.tabWidget_4.setTabText(self.tabWidget_4.indexOf(self.tab_21), QCoreApplication.translate("TaskWindow", u"ExitName", None))
        self.label_4.setText(QCoreApplication.translate("TaskWindow", u"Locations:", None))
        self.label_7.setText(QCoreApplication.translate("TaskWindow", u"Location", None))
        self.pb_add_ccl.setText(QCoreApplication.translate("TaskWindow", u"Add", None))
        self.pb_finalize_ccl.setText(QCoreApplication.translate("TaskWindow", u"Finalize Condition", None))
        self.pb_rem_ccl.setText(QCoreApplication.translate("TaskWindow", u"Remove Selected Location", None))
        ___qtablewidgetitem6 = self.tb_ccl.horizontalHeaderItem(0)
        ___qtablewidgetitem6.setText(QCoreApplication.translate("TaskWindow", u"location", None));
        self.tabWidget_4.setTabText(self.tabWidget_4.indexOf(self.tab_22), QCoreApplication.translate("TaskWindow", u"Location", None))
        ___qtablewidgetitem7 = self.tb_eq_inc.horizontalHeaderItem(0)
        ___qtablewidgetitem7.setText(QCoreApplication.translate("TaskWindow", u"id", None));
        ___qtablewidgetitem8 = self.tb_eq_inc.horizontalHeaderItem(1)
        ___qtablewidgetitem8.setText(QCoreApplication.translate("TaskWindow", u"orGroup", None));
        ___qtablewidgetitem9 = self.tb_eq_exc.horizontalHeaderItem(0)
        ___qtablewidgetitem9.setText(QCoreApplication.translate("TaskWindow", u"id", None));
        ___qtablewidgetitem10 = self.tb_eq_exc.horizontalHeaderItem(1)
        ___qtablewidgetitem10.setText(QCoreApplication.translate("TaskWindow", u"orGroup", None));
        self.label_9.setText(QCoreApplication.translate("TaskWindow", u"Equipment Inclusive:", None))
        self.label_17.setText(QCoreApplication.translate("TaskWindow", u"Equipment Exclusive:", None))
        self.label_20.setText(QCoreApplication.translate("TaskWindow", u"(Must have all)", None))
        self.label_21.setText(QCoreApplication.translate("TaskWindow", u"(Can't have any)", None))
        self.cb_eq_uneq.setText(QCoreApplication.translate("TaskWindow", u"Include Unequipped Items?", None))
        self.pb_finalize_cc_eq.setText(QCoreApplication.translate("TaskWindow", u"Finalize Condition", None))
        self.pb_rem_eqi.setText(QCoreApplication.translate("TaskWindow", u"Remove Selected", None))
        self.pb_add_eqi.setText(QCoreApplication.translate("TaskWindow", u"Add", None))
        self.pb_rem_eqe.setText(QCoreApplication.translate("TaskWindow", u"Remove Selected", None))
        self.pb_add_eqe.setText(QCoreApplication.translate("TaskWindow", u"Add", None))
        self.label_22.setText(QCoreApplication.translate("TaskWindow", u"id", None))
        self.label_23.setText(QCoreApplication.translate("TaskWindow", u"orGroup id (int)", None))
        self.label_73.setText(QCoreApplication.translate("TaskWindow", u"id", None))
        self.label_74.setText(QCoreApplication.translate("TaskWindow", u"orGroup id (int)", None))
        self.tabWidget_4.setTabText(self.tabWidget_4.indexOf(self.tab_9), QCoreApplication.translate("TaskWindow", u"Equipment", None))
        ___qtablewidgetitem11 = self.tb_sh_bp.horizontalHeaderItem(0)
        ___qtablewidgetitem11.setText(QCoreApplication.translate("TaskWindow", u"BodyPart", None));
        self.label_24.setText(QCoreApplication.translate("TaskWindow", u"Body Parts:", None))
        self.pb_rem_shbp.setText(QCoreApplication.translate("TaskWindow", u"Remove Selected", None))
        self.pb_add_shbp.setText(QCoreApplication.translate("TaskWindow", u"Add", None))
        self.tabWidget_6.setTabText(self.tabWidget_6.indexOf(self.tab_25), QCoreApplication.translate("TaskWindow", u"Body Parts", None))
        self.pb_rem_shtr.setText(QCoreApplication.translate("TaskWindow", u"Remove Selected", None))
        self.pb_add_shtr.setText(QCoreApplication.translate("TaskWindow", u"Add", None))
        ___qtablewidgetitem12 = self.tb_sh_tr.horizontalHeaderItem(0)
        ___qtablewidgetitem12.setText(QCoreApplication.translate("TaskWindow", u"role", None));
        self.label_28.setText(QCoreApplication.translate("TaskWindow", u"Target Roles:", None))
        self.tabWidget_6.setTabText(self.tabWidget_6.indexOf(self.tab_30), QCoreApplication.translate("TaskWindow", u"Target Roles", None))
        ___qtablewidgetitem13 = self.tb_sh_wep.horizontalHeaderItem(0)
        ___qtablewidgetitem13.setText(QCoreApplication.translate("TaskWindow", u"id", None));
        self.label_25.setText(QCoreApplication.translate("TaskWindow", u"Weapons:", None))
        self.pb_rem_shw.setText(QCoreApplication.translate("TaskWindow", u"Remove Selected", None))
        self.pb_add_shw.setText(QCoreApplication.translate("TaskWindow", u"Add", None))
        self.tabWidget_6.setTabText(self.tabWidget_6.indexOf(self.tab_27), QCoreApplication.translate("TaskWindow", u"Weapons", None))
        ___qtablewidgetitem14 = self.tb_incmod_sh.horizontalHeaderItem(0)
        ___qtablewidgetitem14.setText(QCoreApplication.translate("TaskWindow", u"id", None));
        self.label_26.setText(QCoreApplication.translate("TaskWindow", u"Inclusive Weapon Mods:", None))
        self.pb_rem_shmi.setText(QCoreApplication.translate("TaskWindow", u"Remove Selected", None))
        self.pb_add_shmi.setText(QCoreApplication.translate("TaskWindow", u"Add", None))
        self.tabWidget_6.setTabText(self.tabWidget_6.indexOf(self.tab_28), QCoreApplication.translate("TaskWindow", u"Mods (include)", None))
        ___qtablewidgetitem15 = self.tb_excmod_sh.horizontalHeaderItem(0)
        ___qtablewidgetitem15.setText(QCoreApplication.translate("TaskWindow", u"id", None));
        self.label_27.setText(QCoreApplication.translate("TaskWindow", u"Exclusive Weapon Mods:", None))
        self.pb_rem_shme.setText(QCoreApplication.translate("TaskWindow", u"Remove Selected", None))
        self.pb_add_shme.setText(QCoreApplication.translate("TaskWindow", u"Add", None))
        self.tabWidget_6.setTabText(self.tabWidget_6.indexOf(self.tab_29), QCoreApplication.translate("TaskWindow", u"Mods (exclude)", None))
        self.label_31.setText(QCoreApplication.translate("TaskWindow", u"Distance Compare:", None))
        self.label_30.setText(QCoreApplication.translate("TaskWindow", u"Time To:", None))
        self.label_29.setText(QCoreApplication.translate("TaskWindow", u"Time From:", None))
        self.label_32.setText(QCoreApplication.translate("TaskWindow", u"Distance:", None))
        self.label_33.setText(QCoreApplication.translate("TaskWindow", u"Value:", None))
        self.chk_cck_reset_sessionend_2.setText(QCoreApplication.translate("TaskWindow", u"Reset on Session End", None))
        self.label_34.setText(QCoreApplication.translate("TaskWindow", u"Target:", None))
        self.pb_finalize_shtr.setText(QCoreApplication.translate("TaskWindow", u"Finalize", None))
        self.tabWidget_4.setTabText(self.tabWidget_4.indexOf(self.tab_10), QCoreApplication.translate("TaskWindow", u"Shots", None))
        ___qtablewidgetitem16 = self.tb_hebp.horizontalHeaderItem(0)
        ___qtablewidgetitem16.setText(QCoreApplication.translate("TaskWindow", u"name", None));
        self.label_35.setText(QCoreApplication.translate("TaskWindow", u"Body Parts:", None))
        ___qtablewidgetitem17 = self.tb_heef.horizontalHeaderItem(0)
        ___qtablewidgetitem17.setText(QCoreApplication.translate("TaskWindow", u"name", None));
        self.label_36.setText(QCoreApplication.translate("TaskWindow", u"Effects:", None))
        self.pb_rem_hebp.setText(QCoreApplication.translate("TaskWindow", u"Remove Selected", None))
        self.pb_add_hebp.setText(QCoreApplication.translate("TaskWindow", u"Add", None))
        self.pb_rem_heef.setText(QCoreApplication.translate("TaskWindow", u"Remove Selected", None))
        self.pb_add_heef.setText(QCoreApplication.translate("TaskWindow", u"Add", None))
        self.label_64.setText(QCoreApplication.translate("TaskWindow", u"Energy Compare:", None))
        self.label_65.setText(QCoreApplication.translate("TaskWindow", u"Energy Value:", None))
        self.label_66.setText(QCoreApplication.translate("TaskWindow", u"Hydration Compare:", None))
        self.label_67.setText(QCoreApplication.translate("TaskWindow", u"Hydration Value:", None))
        self.label_68.setText(QCoreApplication.translate("TaskWindow", u"Time Compare:", None))
        self.label_69.setText(QCoreApplication.translate("TaskWindow", u"Time Value:", None))
        self.pb_finalize_he.setText(QCoreApplication.translate("TaskWindow", u"Finalize", None))
        self.tabWidget_4.setTabText(self.tabWidget_4.indexOf(self.tab_13), QCoreApplication.translate("TaskWindow", u"HealthEffect", None))
        ___qtablewidgetitem18 = self.tb_hb.horizontalHeaderItem(0)
        ___qtablewidgetitem18.setText(QCoreApplication.translate("TaskWindow", u"name", None));
        self.label_70.setText(QCoreApplication.translate("TaskWindow", u"Health Buffs:", None))
        self.pb_rem_hb.setText(QCoreApplication.translate("TaskWindow", u"Remove Selected", None))
        self.pb_add_hb.setText(QCoreApplication.translate("TaskWindow", u"Add", None))
        self.pb_finalize_hb.setText(QCoreApplication.translate("TaskWindow", u"Finalize", None))
        self.tabWidget_4.setTabText(self.tabWidget_4.indexOf(self.tab_14), QCoreApplication.translate("TaskWindow", u"HealthBuff", None))
        self.label_71.setText(QCoreApplication.translate("TaskWindow", u"Zone/Target Name:", None))
        self.pb_finalize_fl.setText(QCoreApplication.translate("TaskWindow", u"Finalize", None))
        self.tabWidget_4.setTabText(self.tabWidget_4.indexOf(self.tab_23), QCoreApplication.translate("TaskWindow", u"LaunchFlare", None))
        ___qtablewidgetitem19 = self.tb_iz.horizontalHeaderItem(0)
        ___qtablewidgetitem19.setText(QCoreApplication.translate("TaskWindow", u"name", None));
        self.label_72.setText(QCoreApplication.translate("TaskWindow", u"Zones:", None))
        self.pb_rem_iz.setText(QCoreApplication.translate("TaskWindow", u"Remove Selected", None))
        self.pb_add_iz.setText(QCoreApplication.translate("TaskWindow", u"Add", None))
        self.pb_finalize_iz.setText(QCoreApplication.translate("TaskWindow", u"Finalize", None))
        self.tabWidget_4.setTabText(self.tabWidget_4.indexOf(self.tab_24), QCoreApplication.translate("TaskWindow", u"InZone", None))
        self.label_59.setText(QCoreApplication.translate("TaskWindow", u"CC QuestType Label", None))
        self.pb_remove_cc.setText(QCoreApplication.translate("TaskWindow", u"Remove Selected", None))
        self.lb_quantity_cck.setText(QCoreApplication.translate("TaskWindow", u"Quantity:  ", None))
        self.pb_finalize_cc.setText(QCoreApplication.translate("TaskWindow", u"Finalize", None))
        self.label_53.setText(QCoreApplication.translate("TaskWindow", u"Finish/Fail:", None))
        self.label_60.setText(QCoreApplication.translate("TaskWindow", u"Parent ID", None))
        ___qtablewidgetitem20 = self.tb_cc.horizontalHeaderItem(0)
        ___qtablewidgetitem20.setText(QCoreApplication.translate("TaskWindow", u"id", None));
        ___qtablewidgetitem21 = self.tb_cc.horizontalHeaderItem(1)
        ___qtablewidgetitem21.setText(QCoreApplication.translate("TaskWindow", u"type", None));
        self.pb_edit_cc.setText(QCoreApplication.translate("TaskWindow", u"Edit Selected Subtask", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_6), QCoreApplication.translate("TaskWindow", u"CounterCreator", None))
        self.lb_quantity_2.setText(QCoreApplication.translate("TaskWindow", u"Quantity:", None))
        self.label_6.setText(QCoreApplication.translate("TaskWindow", u"HandOver or Find:", None))
        self.lb_maxdur.setText(QCoreApplication.translate("TaskWindow", u"Max Durability:", None))
        self.label_54.setText(QCoreApplication.translate("TaskWindow", u"Finish/Fail:", None))
        self.box_only_fir_2.setText(QCoreApplication.translate("TaskWindow", u"Only Found In Raid:", None))
#if QT_CONFIG(tooltip)
        self.label.setToolTip(QCoreApplication.translate("TaskWindow", u"<html><head/><body><p>Required if handing over DogTag</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.label.setText(QCoreApplication.translate("TaskWindow", u"Dogtag Level:", None))
        self.lb_mindur.setText(QCoreApplication.translate("TaskWindow", u"Min Durability:", None))
        self.label_61.setText(QCoreApplication.translate("TaskWindow", u"Parent ID", None))
        self.lb_itemid_list.setText(QCoreApplication.translate("TaskWindow", u"Items (by MongoID):", None))
        self.lb_itemid.setText(QCoreApplication.translate("TaskWindow", u"Item: (MongoID):          ", None))
        self.pb_additem_it.setText(QCoreApplication.translate("TaskWindow", u"Add Item", None))
        self.pb_remitem_it.setText(QCoreApplication.translate("TaskWindow", u"Remove Item", None))
        self.pb_finalize_it.setText(QCoreApplication.translate("TaskWindow", u"Finalize Task", None))
        ___qtablewidgetitem22 = self.tb_items.horizontalHeaderItem(0)
        ___qtablewidgetitem22.setText(QCoreApplication.translate("TaskWindow", u"id", None));
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_handover_item), QCoreApplication.translate("TaskWindow", u"HandoverItem / FindItem", None))
        self.label_12.setText(QCoreApplication.translate("TaskWindow", u"Target:", None))
        self.label_55.setText(QCoreApplication.translate("TaskWindow", u"Finish/Fail:", None))
        self.label_13.setText(QCoreApplication.translate("TaskWindow", u"Level:", None))
        self.label_11.setText(QCoreApplication.translate("TaskWindow", u"Compare Method:", None))
        self.label_62.setText(QCoreApplication.translate("TaskWindow", u"Parent ID", None))
        self.pb_finalize_sk.setText(QCoreApplication.translate("TaskWindow", u"Finalize Task", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tb_Skill), QCoreApplication.translate("TaskWindow", u"Skill", None))
        self.lb_quantity_3.setText(QCoreApplication.translate("TaskWindow", u"Quantity:", None))
        self.lb_plant_time.setText(QCoreApplication.translate("TaskWindow", u"Plant Time:", None))
        self.lb_maxdur_2.setText(QCoreApplication.translate("TaskWindow", u"Max Durability:", None))
        self.lb_mindur_2.setText(QCoreApplication.translate("TaskWindow", u"Min Durability:", None))
        self.label_41.setText(QCoreApplication.translate("TaskWindow", u"Parent ID:", None))
        self.label_18.setText(QCoreApplication.translate("TaskWindow", u"Dogtag Level:", None))
        self.lb_zoneid.setText(QCoreApplication.translate("TaskWindow", u"Zone ID:", None))
        self.lb_fir.setText(QCoreApplication.translate("TaskWindow", u"Found In Raid:", None))
        self.label_56.setText(QCoreApplication.translate("TaskWindow", u"Finish/Fail:", None))
        self.pb_finalize_li.setText(QCoreApplication.translate("TaskWindow", u"Finalize Task", None))
        self.pb_rem_li_target.setText(QCoreApplication.translate("TaskWindow", u"Remove Selected", None))
        self.pb_add_li_target.setText(QCoreApplication.translate("TaskWindow", u"Add", None))
        self.lb_addedweps_10.setText(QCoreApplication.translate("TaskWindow", u"Target IDs:", None))
        ___qtablewidgetitem23 = self.tb_li_target.horizontalHeaderItem(0)
        ___qtablewidgetitem23.setText(QCoreApplication.translate("TaskWindow", u"name", None));
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_leave_item), QCoreApplication.translate("TaskWindow", u"LeaveItemAtLocation", None))
        self.label_44.setText(QCoreApplication.translate("TaskWindow", u"Value:", None))
        self.label_43.setText(QCoreApplication.translate("TaskWindow", u"Plant Time:", None))
        self.label_45.setText(QCoreApplication.translate("TaskWindow", u"Zone ID:", None))
        self.label_57.setText(QCoreApplication.translate("TaskWindow", u"Finish/Fail:", None))
        self.label_42.setText(QCoreApplication.translate("TaskWindow", u"Parent ID:", None))
        self.pb_finalize_pb.setText(QCoreApplication.translate("TaskWindow", u"Finalize", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_7), QCoreApplication.translate("TaskWindow", u"PlaceBeacon", None))
        self.label_2.setText(QCoreApplication.translate("TaskWindow", u"To be implemented at a later date :)", None))
        self.pb_finalize_wa.setText(QCoreApplication.translate("TaskWindow", u"Finalize (generate placeholder)", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_8), QCoreApplication.translate("TaskWindow", u"WeaponAssembly", None))
        self.label_14.setText(QCoreApplication.translate("TaskWindow", u"Target:", None))
        self.label_16.setText(QCoreApplication.translate("TaskWindow", u"Level:", None))
        self.label_15.setText(QCoreApplication.translate("TaskWindow", u"Compare Method:", None))
        self.label_58.setText(QCoreApplication.translate("TaskWindow", u"Finish/Fail:", None))
        self.label_63.setText(QCoreApplication.translate("TaskWindow", u"Parent ID", None))
        self.pb_finalize_tl.setText(QCoreApplication.translate("TaskWindow", u"Finalize Task", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_trader_loyalty), QCoreApplication.translate("TaskWindow", u"TraderLoyalty", None))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab), QCoreApplication.translate("TaskWindow", u"Finish/Fail Only", None))
        self.label_5.setText(QCoreApplication.translate("TaskWindow", u"Fail: ANY condition causes quest to fail\n"
"", None))
        self.label_40.setText(QCoreApplication.translate("TaskWindow", u"Compare Method:", None))
        self.label_46.setText(QCoreApplication.translate("TaskWindow", u"Value:", None))
        self.pb_finalize_lv.setText(QCoreApplication.translate("TaskWindow", u"Finalize", None))
        self.tabWidget_3.setTabText(self.tabWidget_3.indexOf(self.tab_3), QCoreApplication.translate("TaskWindow", u"Level", None))
        self.label_19.setText(QCoreApplication.translate("TaskWindow", u"Compare Method", None))
        self.label_51.setText(QCoreApplication.translate("TaskWindow", u"Trader", None))
        self.label_52.setText(QCoreApplication.translate("TaskWindow", u"Value", None))
        self.pb_finalize_ts.setText(QCoreApplication.translate("TaskWindow", u"Finalize", None))
        self.tabWidget_3.setTabText(self.tabWidget_3.indexOf(self.tab_5), QCoreApplication.translate("TaskWindow", u"TraderStanding", None))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab_2), QCoreApplication.translate("TaskWindow", u"Start Only", None))
        self.label_76.setText(QCoreApplication.translate("TaskWindow", u"Target ID:", None))
#if QT_CONFIG(tooltip)
        self.label_75.setToolTip(QCoreApplication.translate("TaskWindow", u"<html><head/><body><p>Minutes that must have passed since completing the quest target for this quest to become available</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.label_75.setText(QCoreApplication.translate("TaskWindow", u"Available after:", None))
        self.label_47.setText(QCoreApplication.translate("TaskWindow", u"Timing", None))
        self.pb_finalize_qs.setText(QCoreApplication.translate("TaskWindow", u"Finalize", None))
        self.label_77.setText(QCoreApplication.translate("TaskWindow", u"Statuses:", None))
        self.label_78.setText(QCoreApplication.translate("TaskWindow", u"Status", None))
        ___qtablewidgetitem24 = self.tb_status_qs.horizontalHeaderItem(0)
        ___qtablewidgetitem24.setText(QCoreApplication.translate("TaskWindow", u"status", None));
        self.pb_addstatus_qs.setText(QCoreApplication.translate("TaskWindow", u"Add", None))
        self.pb_remstatus_qs.setText(QCoreApplication.translate("TaskWindow", u"Remove Selected", None))
        self.tabWidget_8.setTabText(self.tabWidget_8.indexOf(self.tab_33), QCoreApplication.translate("TaskWindow", u"Quest", None))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab_17), QCoreApplication.translate("TaskWindow", u"Any", None))
        self.textBrowser.setHtml(QCoreApplication.translate("TaskWindow", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Segoe UI'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Note:</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">AvailableForStart: ALL conditions satisfied, causes quest to become available</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">AvailableForFinish: ALL conditions satisfied, causes quest to "
                        "be complete (be able to turn in)</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Visibility Conditions are only valid for Finish/Fail conditions.</p></body></html>", None))
        self.fld_taskid_gen.setText("")
        self.label_37.setText(QCoreApplication.translate("TaskWindow", u"Condition ID:", None))
        self.label_38.setText(QCoreApplication.translate("TaskWindow", u"Target", None))
        ___qtablewidgetitem25 = self.tb_vis.horizontalHeaderItem(0)
        ___qtablewidgetitem25.setText(QCoreApplication.translate("TaskWindow", u"target", None));
        self.pb_addvis.setText(QCoreApplication.translate("TaskWindow", u"Add", None))
        self.pb_remvis.setText(QCoreApplication.translate("TaskWindow", u"Remove Selected", None))
        self.label_10.setText(QCoreApplication.translate("TaskWindow", u"Visibility Conditions:", None))
    # retranslateUi

