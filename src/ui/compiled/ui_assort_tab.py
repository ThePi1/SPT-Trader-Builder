# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'assort_tab.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
    QSplitter, QToolButton, QVBoxLayout, QWidget)

class Ui_AssortForm(object):
    def setupUi(self, AssortForm):
        if not AssortForm.objectName():
            AssortForm.setObjectName(u"AssortForm")
        self.outerLayout = QVBoxLayout(AssortForm)
        self.outerLayout.setObjectName(u"outerLayout")
        self.outerLayout.setContentsMargins(0, 0, 0, 0)
        self.topRow = QHBoxLayout()
        self.topRow.setObjectName(u"topRow")
        self.traderLabel = QLabel(AssortForm)
        self.traderLabel.setObjectName(u"traderLabel")

        self.topRow.addWidget(self.traderLabel)

        self.trader = QComboBox(AssortForm)
        self.trader.setObjectName(u"trader")
        self.trader.setMinimumSize(QSize(240, 0))
        self.trader.setEditable(True)
        self.trader.setInsertPolicy(QComboBox.NoInsert)

        self.topRow.addWidget(self.trader)

        self.topSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.topRow.addItem(self.topSpacer)


        self.outerLayout.addLayout(self.topRow)

        self.splitter = QSplitter(AssortForm)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.leftPane = QWidget(self.splitter)
        self.leftPane.setObjectName(u"leftPane")
        self.leftLayout = QVBoxLayout(self.leftPane)
        self.leftLayout.setObjectName(u"leftLayout")
        self.leftLayout.setContentsMargins(0, 0, 0, 0)
        self.searchRow = QHBoxLayout()
        self.searchRow.setObjectName(u"searchRow")
        self.search = QLineEdit(self.leftPane)
        self.search.setObjectName(u"search")

        self.searchRow.addWidget(self.search)

        self.levelFilter = QComboBox(self.leftPane)
        self.levelFilter.setObjectName(u"levelFilter")

        self.searchRow.addWidget(self.levelFilter)

        self.searchRow.setStretch(0, 1)

        self.leftLayout.addLayout(self.searchRow)

        self.list = QListWidget(self.leftPane)
        self.list.setObjectName(u"list")

        self.leftLayout.addWidget(self.list)

        self.note = QLabel(self.leftPane)
        self.note.setObjectName(u"note")
        self.note.setStyleSheet(u"color: #808080;")

        self.leftLayout.addWidget(self.note)

        self.problemsToggle = QToolButton(self.leftPane)
        self.problemsToggle.setObjectName(u"problemsToggle")
        self.problemsToggle.setVisible(False)
        self.problemsToggle.setStyleSheet(u"QToolButton { color: #b9770e; text-align: left; border: none; }")
        self.problemsToggle.setCheckable(True)
        self.problemsToggle.setToolButtonStyle(Qt.ToolButtonTextOnly)

        self.leftLayout.addWidget(self.problemsToggle)

        self.problemsList = QListWidget(self.leftPane)
        self.problemsList.setObjectName(u"problemsList")
        self.problemsList.setVisible(False)
        self.problemsList.setMaximumHeight(110)
        self.problemsList.setWordWrap(True)

        self.leftLayout.addWidget(self.problemsList)

        self.buttonRow = QHBoxLayout()
        self.buttonRow.setObjectName(u"buttonRow")
        self.addButton = QPushButton(self.leftPane)
        self.addButton.setObjectName(u"addButton")

        self.buttonRow.addWidget(self.addButton)

        self.copyButton = QPushButton(self.leftPane)
        self.copyButton.setObjectName(u"copyButton")

        self.buttonRow.addWidget(self.copyButton)

        self.deleteButton = QPushButton(self.leftPane)
        self.deleteButton.setObjectName(u"deleteButton")

        self.buttonRow.addWidget(self.deleteButton)


        self.leftLayout.addLayout(self.buttonRow)

        self.leftLayout.setStretch(1, 1)
        self.splitter.addWidget(self.leftPane)
        self.rightScroll = QScrollArea(self.splitter)
        self.rightScroll.setObjectName(u"rightScroll")
        self.rightScroll.setFrameShape(QFrame.NoFrame)
        self.rightScroll.setWidgetResizable(True)
        self.right = QWidget()
        self.right.setObjectName(u"right")
        self.right_layout = QVBoxLayout(self.right)
        self.right_layout.setObjectName(u"right_layout")
        self.right_layout.setContentsMargins(9, 9, 9, 9)
        self.rightScroll.setWidget(self.right)
        self.splitter.addWidget(self.rightScroll)

        self.outerLayout.addWidget(self.splitter)

        self.outerLayout.setStretch(1, 1)
        QWidget.setTabOrder(self.search, self.levelFilter)
        QWidget.setTabOrder(self.levelFilter, self.list)
        QWidget.setTabOrder(self.list, self.addButton)
        QWidget.setTabOrder(self.addButton, self.copyButton)
        QWidget.setTabOrder(self.copyButton, self.deleteButton)
        QWidget.setTabOrder(self.deleteButton, self.trader)

        self.retranslateUi(AssortForm)

        QMetaObject.connectSlotsByName(AssortForm)
    # setupUi

    def retranslateUi(self, AssortForm):
        self.traderLabel.setText(QCoreApplication.translate("AssortForm", u"Trader", None))
#if QT_CONFIG(tooltip)
        self.trader.setToolTip(QCoreApplication.translate("AssortForm", u"The trader this assort is for. Needed to add quest unlocks. You can paste a trader id.", None))
#endif // QT_CONFIG(tooltip)
        self.search.setPlaceholderText(QCoreApplication.translate("AssortForm", u"Search the offers", None))
#if QT_CONFIG(tooltip)
        self.levelFilter.setToolTip(QCoreApplication.translate("AssortForm", u"Show only the offers that unlock at this trader level.", None))
#endif // QT_CONFIG(tooltip)
        self.note.setText("")
#if QT_CONFIG(tooltip)
        self.problemsToggle.setToolTip(QCoreApplication.translate("AssortForm", u"Where the quest locks and the quests' unlock rewards don't agree. Click to see each one.", None))
#endif // QT_CONFIG(tooltip)
        self.problemsToggle.setText(QCoreApplication.translate("AssortForm", u"\u25b6", None))
        self.addButton.setText(QCoreApplication.translate("AssortForm", u"Add offer...", None))
        self.copyButton.setText(QCoreApplication.translate("AssortForm", u"Copy", None))
        self.deleteButton.setText(QCoreApplication.translate("AssortForm", u"Delete", None))
        pass
    # retranslateUi

