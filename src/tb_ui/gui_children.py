# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'gui_children.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel,
    QLineEdit, QPlainTextEdit, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_ChildrenMenu(object):
    def setupUi(self, ChildrenMenu):
        if not ChildrenMenu.objectName():
            ChildrenMenu.setObjectName(u"ChildrenMenu")
        ChildrenMenu.resize(520, 460)
        ChildrenMenu.setMinimumSize(QSize(420, 360))
        icon = QIcon()
        icon.addFile(u"data/icon.ico", QSize(), QIcon.Normal, QIcon.Off)
        ChildrenMenu.setWindowIcon(icon)
        self.verticalLayout = QVBoxLayout(ChildrenMenu)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.lbl_intro = QLabel(ChildrenMenu)
        self.lbl_intro.setObjectName(u"lbl_intro")
        self.lbl_intro.setWordWrap(True)

        self.verticalLayout.addWidget(self.lbl_intro)

        self.horizontalLayout_items = QHBoxLayout()
        self.horizontalLayout_items.setObjectName(u"horizontalLayout_items")
        self.lbl_items_status = QLabel(ChildrenMenu)
        self.lbl_items_status.setObjectName(u"lbl_items_status")
        self.lbl_items_status.setWordWrap(True)

        self.horizontalLayout_items.addWidget(self.lbl_items_status)

        self.pb_load = QPushButton(ChildrenMenu)
        self.pb_load.setObjectName(u"pb_load")

        self.horizontalLayout_items.addWidget(self.pb_load)


        self.verticalLayout.addLayout(self.horizontalLayout_items)

        self.horizontalLayout_find = QHBoxLayout()
        self.horizontalLayout_find.setObjectName(u"horizontalLayout_find")
        self.lbl_parent_id = QLabel(ChildrenMenu)
        self.lbl_parent_id.setObjectName(u"lbl_parent_id")

        self.horizontalLayout_find.addWidget(self.lbl_parent_id)

        self.fld_parent_id = QLineEdit(ChildrenMenu)
        self.fld_parent_id.setObjectName(u"fld_parent_id")

        self.horizontalLayout_find.addWidget(self.fld_parent_id)

        self.pb_find = QPushButton(ChildrenMenu)
        self.pb_find.setObjectName(u"pb_find")

        self.horizontalLayout_find.addWidget(self.pb_find)


        self.verticalLayout.addLayout(self.horizontalLayout_find)

        self.lbl_result = QLabel(ChildrenMenu)
        self.lbl_result.setObjectName(u"lbl_result")
        self.lbl_result.setWordWrap(True)

        self.verticalLayout.addWidget(self.lbl_result)

        self.txt_results = QPlainTextEdit(ChildrenMenu)
        self.txt_results.setObjectName(u"txt_results")
        self.txt_results.setReadOnly(True)
        self.txt_results.setLineWrapMode(QPlainTextEdit.NoWrap)

        self.verticalLayout.addWidget(self.txt_results)

        self.horizontalLayout_buttons = QHBoxLayout()
        self.horizontalLayout_buttons.setObjectName(u"horizontalLayout_buttons")
        self.pb_copy = QPushButton(ChildrenMenu)
        self.pb_copy.setObjectName(u"pb_copy")

        self.horizontalLayout_buttons.addWidget(self.pb_copy)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_buttons.addItem(self.horizontalSpacer)

        self.pb_close = QPushButton(ChildrenMenu)
        self.pb_close.setObjectName(u"pb_close")

        self.horizontalLayout_buttons.addWidget(self.pb_close)


        self.verticalLayout.addLayout(self.horizontalLayout_buttons)


        self.retranslateUi(ChildrenMenu)

        QMetaObject.connectSlotsByName(ChildrenMenu)
    # setupUi

    def retranslateUi(self, ChildrenMenu):
        ChildrenMenu.setWindowTitle(QCoreApplication.translate("ChildrenMenu", u"Find child items", None))
        self.lbl_intro.setText(QCoreApplication.translate("ChildrenMenu", u"Lists every item in items.json that sits under a parent item, however many levels down (for example every weapon, or every magazine).", None))
        self.lbl_items_status.setText(QCoreApplication.translate("ChildrenMenu", u"No items.json loaded.", None))
        self.pb_load.setText(QCoreApplication.translate("ChildrenMenu", u"Load items.json...", None))
        self.lbl_parent_id.setText(QCoreApplication.translate("ChildrenMenu", u"Parent item ID:", None))
        self.fld_parent_id.setPlaceholderText(QCoreApplication.translate("ChildrenMenu", u"e.g. 5422acb9af1c889c16000029", None))
        self.pb_find.setText(QCoreApplication.translate("ChildrenMenu", u"Find children", None))
        self.lbl_result.setText("")
        self.pb_copy.setText(QCoreApplication.translate("ChildrenMenu", u"Copy to clipboard", None))
        self.pb_close.setText(QCoreApplication.translate("ChildrenMenu", u"Close", None))
    # retranslateUi

