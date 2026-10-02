# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'gui_rewards.ui'
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
    QDoubleSpinBox, QGridLayout, QHeaderView, QLabel,
    QLineEdit, QMainWindow, QMenuBar, QPushButton,
    QSizePolicy, QSpinBox, QStatusBar, QTabWidget,
    QTableWidget, QTableWidgetItem, QWidget)

class Ui_rewardBuilder(object):
    def setupUi(self, rewardBuilder):
        if not rewardBuilder.objectName():
            rewardBuilder.setObjectName(u"rewardBuilder")
        rewardBuilder.resize(1156, 424)
        self.centralwidget = QWidget(rewardBuilder)
        self.centralwidget.setObjectName(u"centralwidget")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setGeometry(QRect(0, 0, 1121, 381))
        self.tabWidget.setStyleSheet(u"")
        self.tab_9 = QWidget()
        self.tab_9.setObjectName(u"tab_9")
        self.gridLayoutWidget_2 = QWidget(self.tab_9)
        self.gridLayoutWidget_2.setObjectName(u"gridLayoutWidget_2")
        self.gridLayoutWidget_2.setGeometry(QRect(10, 10, 321, 111))
        self.gridLayout_2 = QGridLayout(self.gridLayoutWidget_2)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.label_7 = QLabel(self.gridLayoutWidget_2)
        self.label_7.setObjectName(u"label_7")

        self.gridLayout_2.addWidget(self.label_7, 3, 0, 1, 1)

        self.box_amount_exp = QLineEdit(self.gridLayoutWidget_2)
        self.box_amount_exp.setObjectName(u"box_amount_exp")

        self.gridLayout_2.addWidget(self.box_amount_exp, 1, 1, 1, 1)

        self.box_unknown_exp = QComboBox(self.gridLayoutWidget_2)
        self.box_unknown_exp.setObjectName(u"box_unknown_exp")

        self.gridLayout_2.addWidget(self.box_unknown_exp, 3, 1, 1, 1)

        self.label_8 = QLabel(self.gridLayoutWidget_2)
        self.label_8.setObjectName(u"label_8")

        self.gridLayout_2.addWidget(self.label_8, 1, 0, 1, 1)

        self.label_2 = QLabel(self.gridLayoutWidget_2)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout_2.addWidget(self.label_2, 4, 0, 1, 1)

        self.box_rewardtiming_exp = QComboBox(self.gridLayoutWidget_2)
        self.box_rewardtiming_exp.setObjectName(u"box_rewardtiming_exp")

        self.gridLayout_2.addWidget(self.box_rewardtiming_exp, 4, 1, 1, 1)

        self.pb_finalize_exp = QPushButton(self.tab_9)
        self.pb_finalize_exp.setObjectName(u"pb_finalize_exp")
        self.pb_finalize_exp.setGeometry(QRect(10, 130, 75, 24))
        self.tabWidget.addTab(self.tab_9, "")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.gridLayoutWidget_3 = QWidget(self.tab)
        self.gridLayoutWidget_3.setObjectName(u"gridLayoutWidget_3")
        self.gridLayoutWidget_3.setGeometry(QRect(10, 10, 301, 161))
        self.gridLayout_3 = QGridLayout(self.gridLayoutWidget_3)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setContentsMargins(0, 0, 0, 0)
        self.box_fir_item = QComboBox(self.gridLayoutWidget_3)
        self.box_fir_item.setObjectName(u"box_fir_item")

        self.gridLayout_3.addWidget(self.box_fir_item, 3, 1, 1, 1)

        self.chk_target_specify_it = QCheckBox(self.gridLayoutWidget_3)
        self.chk_target_specify_it.setObjectName(u"chk_target_specify_it")

        self.gridLayout_3.addWidget(self.chk_target_specify_it, 6, 0, 1, 1)

        self.label_3 = QLabel(self.gridLayoutWidget_3)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout_3.addWidget(self.label_3, 3, 0, 1, 1)

        self.label_4 = QLabel(self.gridLayoutWidget_3)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout_3.addWidget(self.label_4, 5, 0, 1, 1)

        self.box_rewardtiming_item = QComboBox(self.gridLayoutWidget_3)
        self.box_rewardtiming_item.setObjectName(u"box_rewardtiming_item")

        self.gridLayout_3.addWidget(self.box_rewardtiming_item, 5, 1, 1, 1)

        self.label_11 = QLabel(self.gridLayoutWidget_3)
        self.label_11.setObjectName(u"label_11")

        self.gridLayout_3.addWidget(self.label_11, 2, 0, 1, 1)

        self.fld_man_target_it = QLineEdit(self.gridLayoutWidget_3)
        self.fld_man_target_it.setObjectName(u"fld_man_target_it")

        self.gridLayout_3.addWidget(self.fld_man_target_it, 6, 1, 1, 1)

        self.box_value_item = QSpinBox(self.gridLayoutWidget_3)
        self.box_value_item.setObjectName(u"box_value_item")
        self.box_value_item.setMaximum(999999999)

        self.gridLayout_3.addWidget(self.box_value_item, 2, 1, 1, 1)

        self.label_10 = QLabel(self.gridLayoutWidget_3)
        self.label_10.setObjectName(u"label_10")

        self.gridLayout_3.addWidget(self.label_10, 4, 0, 1, 1)

        self.box_unknown_item = QComboBox(self.gridLayoutWidget_3)
        self.box_unknown_item.setObjectName(u"box_unknown_item")

        self.gridLayout_3.addWidget(self.box_unknown_item, 4, 1, 1, 1)

        self.pb_finalize_item = QPushButton(self.tab)
        self.pb_finalize_item.setObjectName(u"pb_finalize_item")
        self.pb_finalize_item.setGeometry(QRect(10, 240, 75, 24))
        self.label_12 = QLabel(self.tab)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setGeometry(QRect(330, 10, 49, 16))
        self.gridLayoutWidget_8 = QWidget(self.tab)
        self.gridLayoutWidget_8.setObjectName(u"gridLayoutWidget_8")
        self.gridLayoutWidget_8.setGeometry(QRect(380, 190, 591, 151))
        self.gridLayout_8 = QGridLayout(self.gridLayoutWidget_8)
        self.gridLayout_8.setObjectName(u"gridLayout_8")
        self.gridLayout_8.setContentsMargins(0, 0, 0, 0)
        self.chk_slotid_item = QCheckBox(self.gridLayoutWidget_8)
        self.chk_slotid_item.setObjectName(u"chk_slotid_item")

        self.gridLayout_8.addWidget(self.chk_slotid_item, 1, 0, 1, 1)

        self.label_30 = QLabel(self.gridLayoutWidget_8)
        self.label_30.setObjectName(u"label_30")

        self.gridLayout_8.addWidget(self.label_30, 0, 0, 1, 1)

        self.chk_fir_item = QCheckBox(self.gridLayoutWidget_8)
        self.chk_fir_item.setObjectName(u"chk_fir_item")
        self.chk_fir_item.setChecked(True)

        self.gridLayout_8.addWidget(self.chk_fir_item, 5, 0, 1, 1)

        self.chk_parentid_item = QCheckBox(self.gridLayoutWidget_8)
        self.chk_parentid_item.setObjectName(u"chk_parentid_item")

        self.gridLayout_8.addWidget(self.chk_parentid_item, 2, 0, 1, 1)

        self.fld_parentid_item = QLineEdit(self.gridLayoutWidget_8)
        self.fld_parentid_item.setObjectName(u"fld_parentid_item")

        self.gridLayout_8.addWidget(self.fld_parentid_item, 2, 2, 1, 1)

        self.box_soc_item = QSpinBox(self.gridLayoutWidget_8)
        self.box_soc_item.setObjectName(u"box_soc_item")
        self.box_soc_item.setMaximum(999999999)

        self.gridLayout_8.addWidget(self.box_soc_item, 4, 2, 1, 1)

        self.chk_soc_item = QCheckBox(self.gridLayoutWidget_8)
        self.chk_soc_item.setObjectName(u"chk_soc_item")
        self.chk_soc_item.setChecked(True)

        self.gridLayout_8.addWidget(self.chk_soc_item, 4, 0, 1, 1)

        self.fld_slotid_item = QLineEdit(self.gridLayoutWidget_8)
        self.fld_slotid_item.setObjectName(u"fld_slotid_item")

        self.gridLayout_8.addWidget(self.fld_slotid_item, 1, 2, 1, 1)

        self.fld_utpl_item = QLineEdit(self.gridLayoutWidget_8)
        self.fld_utpl_item.setObjectName(u"fld_utpl_item")

        self.gridLayout_8.addWidget(self.fld_utpl_item, 0, 2, 1, 1)

        self.gridLayoutWidget_13 = QWidget(self.tab)
        self.gridLayoutWidget_13.setObjectName(u"gridLayoutWidget_13")
        self.gridLayoutWidget_13.setGeometry(QRect(334, 140, 711, 41))
        self.gridLayout_13 = QGridLayout(self.gridLayoutWidget_13)
        self.gridLayout_13.setObjectName(u"gridLayout_13")
        self.gridLayout_13.setContentsMargins(0, 0, 0, 0)
        self.pb_remitem_item = QPushButton(self.gridLayoutWidget_13)
        self.pb_remitem_item.setObjectName(u"pb_remitem_item")

        self.gridLayout_13.addWidget(self.pb_remitem_item, 0, 0, 1, 1)

        self.pb_additem_item = QPushButton(self.gridLayoutWidget_13)
        self.pb_additem_item.setObjectName(u"pb_additem_item")

        self.gridLayout_13.addWidget(self.pb_additem_item, 0, 1, 1, 1)

        self.tb_item = QTableWidget(self.tab)
        if (self.tb_item.columnCount() < 6):
            self.tb_item.setColumnCount(6)
        __qtablewidgetitem = QTableWidgetItem()
        self.tb_item.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tb_item.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.tb_item.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.tb_item.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.tb_item.setHorizontalHeaderItem(4, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.tb_item.setHorizontalHeaderItem(5, __qtablewidgetitem5)
        self.tb_item.setObjectName(u"tb_item")
        self.tb_item.setGeometry(QRect(330, 30, 741, 91))
        self.tb_item.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.label_31 = QLabel(self.tab)
        self.label_31.setObjectName(u"label_31")
        self.label_31.setGeometry(QRect(10, 190, 241, 41))
        self.label_31.setWordWrap(True)
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.gridLayoutWidget_4 = QWidget(self.tab_2)
        self.gridLayoutWidget_4.setObjectName(u"gridLayoutWidget_4")
        self.gridLayoutWidget_4.setGeometry(QRect(10, 10, 311, 151))
        self.gridLayout_4 = QGridLayout(self.gridLayoutWidget_4)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout_4.setContentsMargins(0, 0, 0, 0)
        self.label_18 = QLabel(self.gridLayoutWidget_4)
        self.label_18.setObjectName(u"label_18")

        self.gridLayout_4.addWidget(self.label_18, 0, 0, 1, 1)

        self.box_rewardtiming_asu = QComboBox(self.gridLayoutWidget_4)
        self.box_rewardtiming_asu.setObjectName(u"box_rewardtiming_asu")

        self.gridLayout_4.addWidget(self.box_rewardtiming_asu, 4, 1, 1, 1)

        self.label_25 = QLabel(self.gridLayoutWidget_4)
        self.label_25.setObjectName(u"label_25")

        self.gridLayout_4.addWidget(self.label_25, 4, 0, 1, 1)

        self.box_loyalty_asu = QSpinBox(self.gridLayoutWidget_4)
        self.box_loyalty_asu.setObjectName(u"box_loyalty_asu")
        self.box_loyalty_asu.setMaximum(999999999)

        self.gridLayout_4.addWidget(self.box_loyalty_asu, 1, 1, 1, 1)

        self.label_33 = QLabel(self.gridLayoutWidget_4)
        self.label_33.setObjectName(u"label_33")

        self.gridLayout_4.addWidget(self.label_33, 1, 0, 1, 1)

        self.box_trader_asu = QComboBox(self.gridLayoutWidget_4)
        self.box_trader_asu.setObjectName(u"box_trader_asu")

        self.gridLayout_4.addWidget(self.box_trader_asu, 0, 1, 1, 1)

        self.label_13 = QLabel(self.gridLayoutWidget_4)
        self.label_13.setObjectName(u"label_13")

        self.gridLayout_4.addWidget(self.label_13, 2, 0, 1, 1)

        self.box_unknown_asu = QComboBox(self.gridLayoutWidget_4)
        self.box_unknown_asu.setObjectName(u"box_unknown_asu")

        self.gridLayout_4.addWidget(self.box_unknown_asu, 2, 1, 1, 1)

        self.chk_target_specify_asu = QCheckBox(self.gridLayoutWidget_4)
        self.chk_target_specify_asu.setObjectName(u"chk_target_specify_asu")

        self.gridLayout_4.addWidget(self.chk_target_specify_asu, 5, 0, 1, 1)

        self.fld_man_target_asu = QLineEdit(self.gridLayoutWidget_4)
        self.fld_man_target_asu.setObjectName(u"fld_man_target_asu")

        self.gridLayout_4.addWidget(self.fld_man_target_asu, 5, 1, 1, 1)

        self.label_17 = QLabel(self.tab_2)
        self.label_17.setObjectName(u"label_17")
        self.label_17.setGeometry(QRect(330, 10, 49, 16))
        self.pb_finalize_asu = QPushButton(self.tab_2)
        self.pb_finalize_asu.setObjectName(u"pb_finalize_asu")
        self.pb_finalize_asu.setGeometry(QRect(10, 220, 75, 24))
        self.gridLayoutWidget_11 = QWidget(self.tab_2)
        self.gridLayoutWidget_11.setObjectName(u"gridLayoutWidget_11")
        self.gridLayoutWidget_11.setGeometry(QRect(390, 190, 591, 141))
        self.gridLayout_11 = QGridLayout(self.gridLayoutWidget_11)
        self.gridLayout_11.setObjectName(u"gridLayout_11")
        self.gridLayout_11.setContentsMargins(0, 0, 0, 0)
        self.label_32 = QLabel(self.gridLayoutWidget_11)
        self.label_32.setObjectName(u"label_32")

        self.gridLayout_11.addWidget(self.label_32, 0, 0, 1, 1)

        self.chk_parentid_asu = QCheckBox(self.gridLayoutWidget_11)
        self.chk_parentid_asu.setObjectName(u"chk_parentid_asu")

        self.gridLayout_11.addWidget(self.chk_parentid_asu, 2, 0, 1, 1)

        self.chk_fir_asu = QCheckBox(self.gridLayoutWidget_11)
        self.chk_fir_asu.setObjectName(u"chk_fir_asu")
        self.chk_fir_asu.setChecked(True)

        self.gridLayout_11.addWidget(self.chk_fir_asu, 4, 0, 1, 1)

        self.box_parentid_asu = QLineEdit(self.gridLayoutWidget_11)
        self.box_parentid_asu.setObjectName(u"box_parentid_asu")

        self.gridLayout_11.addWidget(self.box_parentid_asu, 2, 1, 1, 1)

        self.fld_utpl_asu = QLineEdit(self.gridLayoutWidget_11)
        self.fld_utpl_asu.setObjectName(u"fld_utpl_asu")

        self.gridLayout_11.addWidget(self.fld_utpl_asu, 0, 1, 1, 1)

        self.box_soc_asu = QSpinBox(self.gridLayoutWidget_11)
        self.box_soc_asu.setObjectName(u"box_soc_asu")
        self.box_soc_asu.setMaximum(999999999)

        self.gridLayout_11.addWidget(self.box_soc_asu, 3, 1, 1, 1)

        self.chk_soc_asu = QCheckBox(self.gridLayoutWidget_11)
        self.chk_soc_asu.setObjectName(u"chk_soc_asu")
        self.chk_soc_asu.setChecked(True)

        self.gridLayout_11.addWidget(self.chk_soc_asu, 3, 0, 1, 1)

        self.box_slotid_asu = QLineEdit(self.gridLayoutWidget_11)
        self.box_slotid_asu.setObjectName(u"box_slotid_asu")

        self.gridLayout_11.addWidget(self.box_slotid_asu, 1, 1, 1, 1)

        self.chk_slotid_asu = QCheckBox(self.gridLayoutWidget_11)
        self.chk_slotid_asu.setObjectName(u"chk_slotid_asu")

        self.gridLayout_11.addWidget(self.chk_slotid_asu, 1, 0, 1, 1)

        self.gridLayoutWidget_14 = QWidget(self.tab_2)
        self.gridLayoutWidget_14.setObjectName(u"gridLayoutWidget_14")
        self.gridLayoutWidget_14.setGeometry(QRect(330, 140, 721, 51))
        self.gridLayout_14 = QGridLayout(self.gridLayoutWidget_14)
        self.gridLayout_14.setObjectName(u"gridLayout_14")
        self.gridLayout_14.setContentsMargins(0, 0, 0, 0)
        self.pb_additem_asu = QPushButton(self.gridLayoutWidget_14)
        self.pb_additem_asu.setObjectName(u"pb_additem_asu")

        self.gridLayout_14.addWidget(self.pb_additem_asu, 0, 2, 1, 1)

        self.pb_remitem_asu = QPushButton(self.gridLayoutWidget_14)
        self.pb_remitem_asu.setObjectName(u"pb_remitem_asu")

        self.gridLayout_14.addWidget(self.pb_remitem_asu, 0, 0, 1, 1)

        self.pb_load_fields_asu = QPushButton(self.gridLayoutWidget_14)
        self.pb_load_fields_asu.setObjectName(u"pb_load_fields_asu")

        self.gridLayout_14.addWidget(self.pb_load_fields_asu, 0, 1, 1, 1)

        self.tb_asu_item = QTableWidget(self.tab_2)
        if (self.tb_asu_item.columnCount() < 6):
            self.tb_asu_item.setColumnCount(6)
        __qtablewidgetitem6 = QTableWidgetItem()
        self.tb_asu_item.setHorizontalHeaderItem(0, __qtablewidgetitem6)
        __qtablewidgetitem7 = QTableWidgetItem()
        self.tb_asu_item.setHorizontalHeaderItem(1, __qtablewidgetitem7)
        __qtablewidgetitem8 = QTableWidgetItem()
        self.tb_asu_item.setHorizontalHeaderItem(2, __qtablewidgetitem8)
        __qtablewidgetitem9 = QTableWidgetItem()
        self.tb_asu_item.setHorizontalHeaderItem(3, __qtablewidgetitem9)
        __qtablewidgetitem10 = QTableWidgetItem()
        self.tb_asu_item.setHorizontalHeaderItem(4, __qtablewidgetitem10)
        __qtablewidgetitem11 = QTableWidgetItem()
        self.tb_asu_item.setHorizontalHeaderItem(5, __qtablewidgetitem11)
        self.tb_asu_item.setObjectName(u"tb_asu_item")
        self.tb_asu_item.setGeometry(QRect(330, 30, 741, 91))
        self.tb_asu_item.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.label = QLabel(self.tab_2)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(10, 170, 241, 41))
        self.label.setWordWrap(True)
        self.tabWidget.addTab(self.tab_2, "")
        self.tab_5 = QWidget()
        self.tab_5.setObjectName(u"tab_5")
        self.gridLayoutWidget_5 = QWidget(self.tab_5)
        self.gridLayoutWidget_5.setObjectName(u"gridLayoutWidget_5")
        self.gridLayoutWidget_5.setGeometry(QRect(10, 10, 261, 130))
        self.gridLayout_5 = QGridLayout(self.gridLayoutWidget_5)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.gridLayout_5.setContentsMargins(0, 0, 0, 0)
        self.label_14 = QLabel(self.gridLayoutWidget_5)
        self.label_14.setObjectName(u"label_14")

        self.gridLayout_5.addWidget(self.label_14, 0, 0, 1, 1)

        self.label_19 = QLabel(self.gridLayoutWidget_5)
        self.label_19.setObjectName(u"label_19")

        self.gridLayout_5.addWidget(self.label_19, 2, 0, 1, 1)

        self.label_15 = QLabel(self.gridLayoutWidget_5)
        self.label_15.setObjectName(u"label_15")

        self.gridLayout_5.addWidget(self.label_15, 3, 0, 1, 1)

        self.box_unknown_ts = QComboBox(self.gridLayoutWidget_5)
        self.box_unknown_ts.setObjectName(u"box_unknown_ts")

        self.gridLayout_5.addWidget(self.box_unknown_ts, 3, 2, 1, 1)

        self.box_loyalty_ts = QDoubleSpinBox(self.gridLayoutWidget_5)
        self.box_loyalty_ts.setObjectName(u"box_loyalty_ts")
        self.box_loyalty_ts.setMaximum(9999999999.989999771118164)

        self.gridLayout_5.addWidget(self.box_loyalty_ts, 2, 2, 1, 1)

        self.box_rewardtiming_ts = QComboBox(self.gridLayoutWidget_5)
        self.box_rewardtiming_ts.setObjectName(u"box_rewardtiming_ts")

        self.gridLayout_5.addWidget(self.box_rewardtiming_ts, 5, 2, 1, 1)

        self.label_26 = QLabel(self.gridLayoutWidget_5)
        self.label_26.setObjectName(u"label_26")

        self.gridLayout_5.addWidget(self.label_26, 5, 0, 1, 1)

        self.box_trader_ts = QComboBox(self.gridLayoutWidget_5)
        self.box_trader_ts.setObjectName(u"box_trader_ts")

        self.gridLayout_5.addWidget(self.box_trader_ts, 0, 2, 1, 1)

        self.pb_finalize_ts = QPushButton(self.tab_5)
        self.pb_finalize_ts.setObjectName(u"pb_finalize_ts")
        self.pb_finalize_ts.setGeometry(QRect(10, 150, 75, 24))
        self.tabWidget.addTab(self.tab_5, "")
        self.tab_6 = QWidget()
        self.tab_6.setObjectName(u"tab_6")
        self.gridLayoutWidget_6 = QWidget(self.tab_6)
        self.gridLayoutWidget_6.setObjectName(u"gridLayoutWidget_6")
        self.gridLayoutWidget_6.setGeometry(QRect(10, 10, 351, 130))
        self.gridLayout_6 = QGridLayout(self.gridLayoutWidget_6)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.gridLayout_6.setContentsMargins(0, 0, 0, 0)
        self.label_20 = QLabel(self.gridLayoutWidget_6)
        self.label_20.setObjectName(u"label_20")

        self.gridLayout_6.addWidget(self.label_20, 0, 0, 1, 1)

        self.label_22 = QLabel(self.gridLayoutWidget_6)
        self.label_22.setObjectName(u"label_22")

        self.gridLayout_6.addWidget(self.label_22, 2, 0, 1, 1)

        self.box_skill_sk = QComboBox(self.gridLayoutWidget_6)
        self.box_skill_sk.setObjectName(u"box_skill_sk")

        self.gridLayout_6.addWidget(self.box_skill_sk, 0, 1, 1, 1)

        self.box_unknown_sk = QComboBox(self.gridLayoutWidget_6)
        self.box_unknown_sk.setObjectName(u"box_unknown_sk")

        self.gridLayout_6.addWidget(self.box_unknown_sk, 3, 1, 1, 1)

        self.box_points_sk = QSpinBox(self.gridLayoutWidget_6)
        self.box_points_sk.setObjectName(u"box_points_sk")
        self.box_points_sk.setMaximum(999999999)

        self.gridLayout_6.addWidget(self.box_points_sk, 2, 1, 1, 1)

        self.label_21 = QLabel(self.gridLayoutWidget_6)
        self.label_21.setObjectName(u"label_21")

        self.gridLayout_6.addWidget(self.label_21, 3, 0, 1, 1)

        self.label_27 = QLabel(self.gridLayoutWidget_6)
        self.label_27.setObjectName(u"label_27")

        self.gridLayout_6.addWidget(self.label_27, 4, 0, 1, 1)

        self.box_rewardtiming_sk = QComboBox(self.gridLayoutWidget_6)
        self.box_rewardtiming_sk.setObjectName(u"box_rewardtiming_sk")

        self.gridLayout_6.addWidget(self.box_rewardtiming_sk, 4, 1, 1, 1)

        self.pb_finalize_sk = QPushButton(self.tab_6)
        self.pb_finalize_sk.setObjectName(u"pb_finalize_sk")
        self.pb_finalize_sk.setGeometry(QRect(10, 150, 75, 24))
        self.tabWidget.addTab(self.tab_6, "")
        self.tab_7 = QWidget()
        self.tab_7.setObjectName(u"tab_7")
        self.gridLayoutWidget_7 = QWidget(self.tab_7)
        self.gridLayoutWidget_7.setObjectName(u"gridLayoutWidget_7")
        self.gridLayoutWidget_7.setGeometry(QRect(10, 10, 271, 102))
        self.gridLayout_7 = QGridLayout(self.gridLayoutWidget_7)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.gridLayout_7.setContentsMargins(0, 0, 0, 0)
        self.label_24 = QLabel(self.gridLayoutWidget_7)
        self.label_24.setObjectName(u"label_24")

        self.gridLayout_7.addWidget(self.label_24, 1, 0, 1, 1)

        self.box_unknown_sr = QComboBox(self.gridLayoutWidget_7)
        self.box_unknown_sr.setObjectName(u"box_unknown_sr")

        self.gridLayout_7.addWidget(self.box_unknown_sr, 2, 1, 1, 1)

        self.label_23 = QLabel(self.gridLayoutWidget_7)
        self.label_23.setObjectName(u"label_23")

        self.gridLayout_7.addWidget(self.label_23, 2, 0, 1, 1)

        self.label_28 = QLabel(self.gridLayoutWidget_7)
        self.label_28.setObjectName(u"label_28")

        self.gridLayout_7.addWidget(self.label_28, 3, 0, 1, 1)

        self.box_rewardtiming_sr = QComboBox(self.gridLayoutWidget_7)
        self.box_rewardtiming_sr.setObjectName(u"box_rewardtiming_sr")

        self.gridLayout_7.addWidget(self.box_rewardtiming_sr, 3, 1, 1, 1)

        self.box_rows_sr = QSpinBox(self.gridLayoutWidget_7)
        self.box_rows_sr.setObjectName(u"box_rows_sr")
        self.box_rows_sr.setMaximum(999999999)

        self.gridLayout_7.addWidget(self.box_rows_sr, 1, 1, 1, 1)

        self.pb_finalize_sr = QPushButton(self.tab_7)
        self.pb_finalize_sr.setObjectName(u"pb_finalize_sr")
        self.pb_finalize_sr.setGeometry(QRect(10, 120, 75, 24))
        self.tabWidget.addTab(self.tab_7, "")
        self.tab_8 = QWidget()
        self.tab_8.setObjectName(u"tab_8")
        self.gridLayoutWidget = QWidget(self.tab_8)
        self.gridLayoutWidget.setObjectName(u"gridLayoutWidget")
        self.gridLayoutWidget.setGeometry(QRect(10, 10, 321, 102))
        self.gridLayout = QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.bx_unknown_ach = QComboBox(self.gridLayoutWidget)
        self.bx_unknown_ach.setObjectName(u"bx_unknown_ach")

        self.gridLayout.addWidget(self.bx_unknown_ach, 2, 1, 1, 1)

        self.label_5 = QLabel(self.gridLayoutWidget)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout.addWidget(self.label_5, 1, 0, 1, 1)

        self.fld_ach_id_ach = QLineEdit(self.gridLayoutWidget)
        self.fld_ach_id_ach.setObjectName(u"fld_ach_id_ach")

        self.gridLayout.addWidget(self.fld_ach_id_ach, 1, 1, 1, 1)

        self.label_6 = QLabel(self.gridLayoutWidget)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout.addWidget(self.label_6, 2, 0, 1, 1)

        self.box_rewardtiming_ach = QComboBox(self.gridLayoutWidget)
        self.box_rewardtiming_ach.setObjectName(u"box_rewardtiming_ach")

        self.gridLayout.addWidget(self.box_rewardtiming_ach, 4, 1, 1, 1)

        self.label_29 = QLabel(self.gridLayoutWidget)
        self.label_29.setObjectName(u"label_29")

        self.gridLayout.addWidget(self.label_29, 4, 0, 1, 1)

        self.pb_finalize_ach = QPushButton(self.tab_8)
        self.pb_finalize_ach.setObjectName(u"pb_finalize_ach")
        self.pb_finalize_ach.setGeometry(QRect(10, 120, 75, 24))
        self.tabWidget.addTab(self.tab_8, "")
        self.tab_10 = QWidget()
        self.tab_10.setObjectName(u"tab_10")
        self.gridLayoutWidget_12 = QWidget(self.tab_10)
        self.gridLayoutWidget_12.setObjectName(u"gridLayoutWidget_12")
        self.gridLayoutWidget_12.setGeometry(QRect(10, 10, 321, 111))
        self.gridLayout_12 = QGridLayout(self.gridLayoutWidget_12)
        self.gridLayout_12.setObjectName(u"gridLayout_12")
        self.gridLayout_12.setContentsMargins(0, 0, 0, 0)
        self.label_34 = QLabel(self.gridLayoutWidget_12)
        self.label_34.setObjectName(u"label_34")

        self.gridLayout_12.addWidget(self.label_34, 3, 0, 1, 1)

        self.box_unknown_tul = QComboBox(self.gridLayoutWidget_12)
        self.box_unknown_tul.setObjectName(u"box_unknown_tul")

        self.gridLayout_12.addWidget(self.box_unknown_tul, 3, 1, 1, 1)

        self.label_35 = QLabel(self.gridLayoutWidget_12)
        self.label_35.setObjectName(u"label_35")

        self.gridLayout_12.addWidget(self.label_35, 1, 0, 1, 1)

        self.label_36 = QLabel(self.gridLayoutWidget_12)
        self.label_36.setObjectName(u"label_36")

        self.gridLayout_12.addWidget(self.label_36, 4, 0, 1, 1)

        self.box_rewardtiming_tul = QComboBox(self.gridLayoutWidget_12)
        self.box_rewardtiming_tul.setObjectName(u"box_rewardtiming_tul")

        self.gridLayout_12.addWidget(self.box_rewardtiming_tul, 4, 1, 1, 1)

        self.box_trader_tul = QComboBox(self.gridLayoutWidget_12)
        self.box_trader_tul.setObjectName(u"box_trader_tul")

        self.gridLayout_12.addWidget(self.box_trader_tul, 1, 1, 1, 1)

        self.pb_finalize_tul = QPushButton(self.tab_10)
        self.pb_finalize_tul.setObjectName(u"pb_finalize_tul")
        self.pb_finalize_tul.setGeometry(QRect(10, 130, 75, 24))
        self.tabWidget.addTab(self.tab_10, "")
        rewardBuilder.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(rewardBuilder)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1156, 22))
        rewardBuilder.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(rewardBuilder)
        self.statusbar.setObjectName(u"statusbar")
        rewardBuilder.setStatusBar(self.statusbar)

        self.retranslateUi(rewardBuilder)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(rewardBuilder)
    # setupUi

    def retranslateUi(self, rewardBuilder):
        rewardBuilder.setWindowTitle(QCoreApplication.translate("rewardBuilder", u"Reward Builder", None))
        self.label_7.setText(QCoreApplication.translate("rewardBuilder", u"Hide reward?", None))
        self.label_8.setText(QCoreApplication.translate("rewardBuilder", u"Amount", None))
        self.label_2.setText(QCoreApplication.translate("rewardBuilder", u"Reward Timing", None))
        self.pb_finalize_exp.setText(QCoreApplication.translate("rewardBuilder", u"Finalize", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_9), QCoreApplication.translate("rewardBuilder", u"Experience", None))
        self.chk_target_specify_it.setText(QCoreApplication.translate("rewardBuilder", u"Manually specify target:", None))
        self.label_3.setText(QCoreApplication.translate("rewardBuilder", u"Found In Raid?", None))
        self.label_4.setText(QCoreApplication.translate("rewardBuilder", u"Reward Timing", None))
        self.label_11.setText(QCoreApplication.translate("rewardBuilder", u"Value", None))
        self.label_10.setText(QCoreApplication.translate("rewardBuilder", u"Hide reward?", None))
        self.pb_finalize_item.setText(QCoreApplication.translate("rewardBuilder", u"Finalize", None))
        self.label_12.setText(QCoreApplication.translate("rewardBuilder", u"Items:", None))
        self.chk_slotid_item.setText(QCoreApplication.translate("rewardBuilder", u"Use slotID:", None))
        self.label_30.setText(QCoreApplication.translate("rewardBuilder", u"Item ID (_tpl):", None))
        self.chk_fir_item.setText(QCoreApplication.translate("rewardBuilder", u"Found In Raid", None))
        self.chk_parentid_item.setText(QCoreApplication.translate("rewardBuilder", u"Use parentID:", None))
#if QT_CONFIG(tooltip)
        self.box_soc_item.setToolTip(QCoreApplication.translate("rewardBuilder", u"<html><head/><body><p><br/></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.chk_soc_item.setText(QCoreApplication.translate("rewardBuilder", u"Use StackObjectsCount:", None))
        self.pb_remitem_item.setText(QCoreApplication.translate("rewardBuilder", u"Remove Selected Item", None))
        self.pb_additem_item.setText(QCoreApplication.translate("rewardBuilder", u"Add Item", None))
        ___qtablewidgetitem = self.tb_item.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("rewardBuilder", u"_id", None));
        ___qtablewidgetitem1 = self.tb_item.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("rewardBuilder", u"_tpl", None));
        ___qtablewidgetitem2 = self.tb_item.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("rewardBuilder", u"SOC", None));
        ___qtablewidgetitem3 = self.tb_item.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("rewardBuilder", u"parentId", None));
        ___qtablewidgetitem4 = self.tb_item.horizontalHeaderItem(4)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("rewardBuilder", u"slotId", None));
        ___qtablewidgetitem5 = self.tb_item.horizontalHeaderItem(5)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("rewardBuilder", u"fir", None));
        self.label_31.setText(QCoreApplication.translate("rewardBuilder", u"If not manually specified, the target will be the first ID in the item list.", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("rewardBuilder", u"Item", None))
        self.label_18.setText(QCoreApplication.translate("rewardBuilder", u"Trader", None))
        self.label_25.setText(QCoreApplication.translate("rewardBuilder", u"Reward Timing", None))
        self.label_33.setText(QCoreApplication.translate("rewardBuilder", u"Loyalty Level", None))
        self.label_13.setText(QCoreApplication.translate("rewardBuilder", u"Hide reward?", None))
        self.chk_target_specify_asu.setText(QCoreApplication.translate("rewardBuilder", u"Manually specify target:", None))
        self.label_17.setText(QCoreApplication.translate("rewardBuilder", u"Items:", None))
        self.pb_finalize_asu.setText(QCoreApplication.translate("rewardBuilder", u"Finalize", None))
        self.label_32.setText(QCoreApplication.translate("rewardBuilder", u"Item ID (_tpl):", None))
        self.chk_parentid_asu.setText(QCoreApplication.translate("rewardBuilder", u"Use parentID:", None))
        self.chk_fir_asu.setText(QCoreApplication.translate("rewardBuilder", u"Found In Raid", None))
        self.chk_soc_asu.setText(QCoreApplication.translate("rewardBuilder", u"Use StackObjectsCount:", None))
        self.chk_slotid_asu.setText(QCoreApplication.translate("rewardBuilder", u"Use slotID:", None))
        self.pb_additem_asu.setText(QCoreApplication.translate("rewardBuilder", u"Add Item", None))
        self.pb_remitem_asu.setText(QCoreApplication.translate("rewardBuilder", u"Remove Selected Item", None))
        self.pb_load_fields_asu.setText(QCoreApplication.translate("rewardBuilder", u"Load to Fields", None))
        ___qtablewidgetitem6 = self.tb_asu_item.horizontalHeaderItem(0)
        ___qtablewidgetitem6.setText(QCoreApplication.translate("rewardBuilder", u"_id", None));
        ___qtablewidgetitem7 = self.tb_asu_item.horizontalHeaderItem(1)
        ___qtablewidgetitem7.setText(QCoreApplication.translate("rewardBuilder", u"_tpl", None));
        ___qtablewidgetitem8 = self.tb_asu_item.horizontalHeaderItem(2)
        ___qtablewidgetitem8.setText(QCoreApplication.translate("rewardBuilder", u"SOC", None));
        ___qtablewidgetitem9 = self.tb_asu_item.horizontalHeaderItem(3)
        ___qtablewidgetitem9.setText(QCoreApplication.translate("rewardBuilder", u"parentId", None));
        ___qtablewidgetitem10 = self.tb_asu_item.horizontalHeaderItem(4)
        ___qtablewidgetitem10.setText(QCoreApplication.translate("rewardBuilder", u"slotId", None));
        ___qtablewidgetitem11 = self.tb_asu_item.horizontalHeaderItem(5)
        ___qtablewidgetitem11.setText(QCoreApplication.translate("rewardBuilder", u"fir", None));
        self.label.setText(QCoreApplication.translate("rewardBuilder", u"If not manually specified, the target will be the first ID in the item list.", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("rewardBuilder", u"Assort Unlock", None))
        self.label_14.setText(QCoreApplication.translate("rewardBuilder", u"Trader", None))
        self.label_19.setText(QCoreApplication.translate("rewardBuilder", u"Loyalty", None))
        self.label_15.setText(QCoreApplication.translate("rewardBuilder", u"Hide reward?", None))
        self.label_26.setText(QCoreApplication.translate("rewardBuilder", u"Reward Timing", None))
        self.pb_finalize_ts.setText(QCoreApplication.translate("rewardBuilder", u"Finalize", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_5), QCoreApplication.translate("rewardBuilder", u"Trader Standing", None))
        self.label_20.setText(QCoreApplication.translate("rewardBuilder", u"Skill", None))
        self.label_22.setText(QCoreApplication.translate("rewardBuilder", u"Points", None))
        self.label_21.setText(QCoreApplication.translate("rewardBuilder", u"Hide reward?", None))
        self.label_27.setText(QCoreApplication.translate("rewardBuilder", u"Reward Timing", None))
        self.pb_finalize_sk.setText(QCoreApplication.translate("rewardBuilder", u"Finalize", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_6), QCoreApplication.translate("rewardBuilder", u"Skills", None))
        self.label_24.setText(QCoreApplication.translate("rewardBuilder", u"Number of Rows", None))
        self.label_23.setText(QCoreApplication.translate("rewardBuilder", u"Hide reward?", None))
        self.label_28.setText(QCoreApplication.translate("rewardBuilder", u"Reward Timing", None))
        self.pb_finalize_sr.setText(QCoreApplication.translate("rewardBuilder", u"Finalize", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_7), QCoreApplication.translate("rewardBuilder", u"Stash Rows", None))
        self.label_5.setText(QCoreApplication.translate("rewardBuilder", u"Achievement ID", None))
        self.label_6.setText(QCoreApplication.translate("rewardBuilder", u"Hide reward?", None))
        self.label_29.setText(QCoreApplication.translate("rewardBuilder", u"Reward Timing", None))
        self.pb_finalize_ach.setText(QCoreApplication.translate("rewardBuilder", u"Finalize", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_8), QCoreApplication.translate("rewardBuilder", u"Achievement", None))
        self.label_34.setText(QCoreApplication.translate("rewardBuilder", u"Hide reward?", None))
        self.label_35.setText(QCoreApplication.translate("rewardBuilder", u"Trader", None))
        self.label_36.setText(QCoreApplication.translate("rewardBuilder", u"Reward Timing", None))
        self.pb_finalize_tul.setText(QCoreApplication.translate("rewardBuilder", u"Finalize", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_10), QCoreApplication.translate("rewardBuilder", u"Trader Unlock", None))
    # retranslateUi

