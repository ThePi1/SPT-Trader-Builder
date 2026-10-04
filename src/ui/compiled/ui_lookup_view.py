# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'lookup_view.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QSizePolicy,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_LookupForm(object):
    def setupUi(self, LookupForm):
        if not LookupForm.objectName():
            LookupForm.setObjectName(u"LookupForm")
        self.verticalLayout = QVBoxLayout(LookupForm)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.topRow = QHBoxLayout()
        self.topRow.setObjectName(u"topRow")
        self.search = QLineEdit(LookupForm)
        self.search.setObjectName(u"search")
        self.search.setClearButtonEnabled(True)

        self.topRow.addWidget(self.search)

        self.filter = QComboBox(LookupForm)
        self.filter.setObjectName(u"filter")

        self.topRow.addWidget(self.filter)

        self.topRow.setStretch(0, 1)

        self.verticalLayout.addLayout(self.topRow)

        self.table = QTableWidget(LookupForm)
        if (self.table.columnCount() < 4):
            self.table.setColumnCount(4)
        __qtablewidgetitem = QTableWidgetItem()
        self.table.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.table.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.table.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.table.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        self.table.setObjectName(u"table")
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)

        self.verticalLayout.addWidget(self.table)

        self.note = QLabel(LookupForm)
        self.note.setObjectName(u"note")
        self.note.setStyleSheet(u"color: #808080;")

        self.verticalLayout.addWidget(self.note)


        self.retranslateUi(LookupForm)

        QMetaObject.connectSlotsByName(LookupForm)
    # setupUi

    def retranslateUi(self, LookupForm):
        self.search.setPlaceholderText(QCoreApplication.translate("LookupForm", u"Type a name or id", None))
        ___qtablewidgetitem = self.table.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("LookupForm", u"Name", None));
        ___qtablewidgetitem1 = self.table.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("LookupForm", u"Details", None));
        ___qtablewidgetitem2 = self.table.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("LookupForm", u"Type", None));
        ___qtablewidgetitem3 = self.table.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("LookupForm", u"Id", None));
        self.note.setText("")
        pass
    # retranslateUi

