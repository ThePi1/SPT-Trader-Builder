# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'quest_outline.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QHBoxLayout, QHeaderView,
    QLineEdit, QPlainTextEdit, QPushButton, QScrollArea,
    QSizePolicy, QSplitter, QToolButton, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget)

class Ui_OutlineForm(object):
    def setupUi(self, OutlineForm):
        if not OutlineForm.objectName():
            OutlineForm.setObjectName(u"OutlineForm")
        OutlineForm.resize(728, 226)
        self.outerLayout = QHBoxLayout(OutlineForm)
        self.outerLayout.setObjectName(u"outerLayout")
        self.outerLayout.setContentsMargins(0, 0, 0, 0)
        self.splitter = QSplitter(OutlineForm)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.leftPane = QWidget(self.splitter)
        self.leftPane.setObjectName(u"leftPane")
        self.leftLayout = QVBoxLayout(self.leftPane)
        self.leftLayout.setObjectName(u"leftLayout")
        self.leftLayout.setContentsMargins(0, 6, 0, 0)
        self.tools = QHBoxLayout()
        self.tools.setSpacing(3)
        self.tools.setObjectName(u"tools")
        self.tools.setContentsMargins(-1, 0, -1, -1)
        self.new_quest_button = QPushButton(self.leftPane)
        self.new_quest_button.setObjectName(u"new_quest_button")

        self.tools.addWidget(self.new_quest_button)

        self.add_button = QToolButton(self.leftPane)
        self.add_button.setObjectName(u"add_button")
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.add_button.sizePolicy().hasHeightForWidth())
        self.add_button.setSizePolicy(sizePolicy)
        self.add_button.setPopupMode(QToolButton.InstantPopup)

        self.tools.addWidget(self.add_button)

        self.copy_button = QPushButton(self.leftPane)
        self.copy_button.setObjectName(u"copy_button")

        self.tools.addWidget(self.copy_button)

        self.delete_button = QPushButton(self.leftPane)
        self.delete_button.setObjectName(u"delete_button")

        self.tools.addWidget(self.delete_button)

        self.up_button = QPushButton(self.leftPane)
        self.up_button.setObjectName(u"up_button")

        self.tools.addWidget(self.up_button)

        self.down_button = QPushButton(self.leftPane)
        self.down_button.setObjectName(u"down_button")

        self.tools.addWidget(self.down_button)

        self.tools.setStretch(0, 1)
        self.tools.setStretch(1, 1)
        self.tools.setStretch(2, 1)
        self.tools.setStretch(3, 1)
        self.tools.setStretch(4, 1)
        self.tools.setStretch(5, 1)

        self.leftLayout.addLayout(self.tools)

        self.search = QLineEdit(self.leftPane)
        self.search.setObjectName(u"search")
        self.search.setClearButtonEnabled(True)

        self.leftLayout.addWidget(self.search)

        self.tree = QTreeWidget(self.leftPane)
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setText(0, u"1");
        self.tree.setHeaderItem(__qtreewidgetitem)
        self.tree.setObjectName(u"tree")
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree.setIndentation(16)
        self.tree.header().setVisible(False)

        self.leftLayout.addWidget(self.tree)

        self.leftLayout.setStretch(2, 1)
        self.splitter.addWidget(self.leftPane)
        self.rightSplitter = QSplitter(self.splitter)
        self.rightSplitter.setObjectName(u"rightSplitter")
        self.rightSplitter.setOrientation(Qt.Vertical)
        self.scroll = QScrollArea(self.rightSplitter)
        self.scroll.setObjectName(u"scroll")
        self.scroll.setWidgetResizable(True)
        self.pane = QWidget()
        self.pane.setObjectName(u"pane")
        self.pane.setGeometry(QRect(0, 0, 252, 69))
        self.pane_layout = QVBoxLayout(self.pane)
        self.pane_layout.setObjectName(u"pane_layout")
        self.scroll.setWidget(self.pane)
        self.rightSplitter.addWidget(self.scroll)
        self.json_view = QPlainTextEdit(self.rightSplitter)
        self.json_view.setObjectName(u"json_view")
        self.json_view.setStyleSheet(u"font-family: Consolas, monospace; font-size: 11px;")
        self.json_view.setReadOnly(True)
        self.rightSplitter.addWidget(self.json_view)
        self.splitter.addWidget(self.rightSplitter)

        self.outerLayout.addWidget(self.splitter)


        self.retranslateUi(OutlineForm)

        QMetaObject.connectSlotsByName(OutlineForm)
    # setupUi

    def retranslateUi(self, OutlineForm):
        self.new_quest_button.setText(QCoreApplication.translate("OutlineForm", u"New quest", None))
        self.add_button.setText(QCoreApplication.translate("OutlineForm", u"Add ", None))
        self.copy_button.setText(QCoreApplication.translate("OutlineForm", u"Copy", None))
        self.delete_button.setText(QCoreApplication.translate("OutlineForm", u"Delete", None))
        self.up_button.setText(QCoreApplication.translate("OutlineForm", u"Up", None))
        self.down_button.setText(QCoreApplication.translate("OutlineForm", u"Down", None))
        self.search.setPlaceholderText(QCoreApplication.translate("OutlineForm", u"Search quests by name", None))
        pass
    # retranslateUi

