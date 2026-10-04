# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'locale_tab.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QSpacerItem, QTableView, QVBoxLayout, QWidget)

class Ui_LocaleForm(object):
    def setupUi(self, LocaleForm):
        if not LocaleForm.objectName():
            LocaleForm.setObjectName(u"LocaleForm")
        self.verticalLayout = QVBoxLayout(LocaleForm)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.topRow = QHBoxLayout()
        self.topRow.setObjectName(u"topRow")
        self.search = QLineEdit(LocaleForm)
        self.search.setObjectName(u"search")
        self.search.setClearButtonEnabled(True)

        self.topRow.addWidget(self.search)

        self.mode = QComboBox(LocaleForm)
        self.mode.setObjectName(u"mode")

        self.topRow.addWidget(self.mode)

        self.topRow.setStretch(0, 1)

        self.verticalLayout.addLayout(self.topRow)

        self.table = QTableView(LocaleForm)
        self.table.setObjectName(u"table")
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)

        self.verticalLayout.addWidget(self.table)

        self.note = QLabel(LocaleForm)
        self.note.setObjectName(u"note")
        self.note.setStyleSheet(u"color: #808080;")

        self.verticalLayout.addWidget(self.note)

        self.buttonRow = QHBoxLayout()
        self.buttonRow.setObjectName(u"buttonRow")
        self.addMissingButton = QPushButton(LocaleForm)
        self.addMissingButton.setObjectName(u"addMissingButton")

        self.buttonRow.addWidget(self.addMissingButton)

        self.addEntryButton = QPushButton(LocaleForm)
        self.addEntryButton.setObjectName(u"addEntryButton")

        self.buttonRow.addWidget(self.addEntryButton)

        self.deleteButton = QPushButton(LocaleForm)
        self.deleteButton.setObjectName(u"deleteButton")

        self.buttonRow.addWidget(self.deleteButton)

        self.fixSpellingButton = QPushButton(LocaleForm)
        self.fixSpellingButton.setObjectName(u"fixSpellingButton")

        self.buttonRow.addWidget(self.fixSpellingButton)

        self.buttonSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.buttonRow.addItem(self.buttonSpacer)


        self.verticalLayout.addLayout(self.buttonRow)


        self.retranslateUi(LocaleForm)

        QMetaObject.connectSlotsByName(LocaleForm)
    # setupUi

    def retranslateUi(self, LocaleForm):
        self.search.setPlaceholderText(QCoreApplication.translate("LocaleForm", u"Search the text, keys or quest names", None))
        self.note.setText("")
        self.addMissingButton.setText(QCoreApplication.translate("LocaleForm", u"Add missing text", None))
        self.addEntryButton.setText(QCoreApplication.translate("LocaleForm", u"Add an entry...", None))
        self.deleteButton.setText(QCoreApplication.translate("LocaleForm", u"Delete", None))
        self.fixSpellingButton.setText(QCoreApplication.translate("LocaleForm", u"Fix old spellings", None))
        pass
    # retranslateUi

