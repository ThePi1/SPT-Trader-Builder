# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'browse_page.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QHeaderView, QLabel,
    QSizePolicy, QSplitter, QTableWidget, QTableWidgetItem,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

class Ui_BrowseForm(object):
    def setupUi(self, BrowseForm):
        if not BrowseForm.objectName():
            BrowseForm.setObjectName(u"BrowseForm")
        self.outerLayout = QHBoxLayout(BrowseForm)
        self.outerLayout.setObjectName(u"outerLayout")
        self.splitter = QSplitter(BrowseForm)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.tree = QTreeWidget(self.splitter)
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setText(0, u"1");
        self.tree.setHeaderItem(__qtreewidgetitem)
        self.tree.setObjectName(u"tree")
        self.splitter.addWidget(self.tree)
        self.tree.header().setVisible(False)
        self.right = QWidget(self.splitter)
        self.right.setObjectName(u"right")
        self.column = QVBoxLayout(self.right)
        self.column.setObjectName(u"column")
        self.column.setContentsMargins(9, 9, 9, 9)
        self.title = QLabel(self.right)
        self.title.setObjectName(u"title")
        self.title.setStyleSheet(u"font-weight: bold;")

        self.column.addWidget(self.title)

        self.note = QLabel(self.right)
        self.note.setObjectName(u"note")
        self.note.setWordWrap(True)

        self.column.addWidget(self.note)

        self.where = QLabel(self.right)
        self.where.setObjectName(u"where")
        self.where.setStyleSheet(u"color: #808080;")
        self.where.setWordWrap(True)

        self.column.addWidget(self.where)

        self.commonLabel = QLabel(self.right)
        self.commonLabel.setObjectName(u"commonLabel")
        self.commonLabel.setWordWrap(True)

        self.column.addWidget(self.commonLabel)

        self.table = QTableWidget(self.right)
        if (self.table.columnCount() < 5):
            self.table.setColumnCount(5)
        __qtablewidgetitem = QTableWidgetItem()
        self.table.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.table.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.table.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.table.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.table.setHorizontalHeaderItem(4, __qtablewidgetitem4)
        self.table.setObjectName(u"table")
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)

        self.column.addWidget(self.table)

        self.splitter.addWidget(self.right)

        self.outerLayout.addWidget(self.splitter)


        self.retranslateUi(BrowseForm)

        QMetaObject.connectSlotsByName(BrowseForm)
    # setupUi

    def retranslateUi(self, BrowseForm):
        self.title.setText("")
        self.note.setText("")
        self.where.setText("")
        self.commonLabel.setText("")
        ___qtablewidgetitem = self.table.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("BrowseForm", u"Field", None));
        ___qtablewidgetitem1 = self.table.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("BrowseForm", u"Key in the file", None));
        ___qtablewidgetitem2 = self.table.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("BrowseForm", u"Kind", None));
        ___qtablewidgetitem3 = self.table.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("BrowseForm", u"Needed", None));
        ___qtablewidgetitem4 = self.table.horizontalHeaderItem(4)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("BrowseForm", u"Starts as", None));
        pass
    # retranslateUi

