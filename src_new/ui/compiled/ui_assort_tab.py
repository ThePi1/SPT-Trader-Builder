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
from PySide6.QtWidgets import (QApplication, QComboBox, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QPushButton,
    QSizePolicy, QSpacerItem, QSplitter, QVBoxLayout,
    QWidget)

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
        self.search = QLineEdit(self.leftPane)
        self.search.setObjectName(u"search")

        self.leftLayout.addWidget(self.search)

        self.list = QListWidget(self.leftPane)
        self.list.setObjectName(u"list")

        self.leftLayout.addWidget(self.list)

        self.note = QLabel(self.leftPane)
        self.note.setObjectName(u"note")
        self.note.setStyleSheet(u"color: #808080;")

        self.leftLayout.addWidget(self.note)

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
        self.right = QWidget(self.splitter)
        self.right.setObjectName(u"right")
        self.right_layout = QVBoxLayout(self.right)
        self.right_layout.setObjectName(u"right_layout")
        self.right_layout.setContentsMargins(9, 9, 9, 9)
        self.splitter.addWidget(self.right)

        self.outerLayout.addWidget(self.splitter)

        self.outerLayout.setStretch(1, 1)
        QWidget.setTabOrder(self.search, self.list)
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
        self.note.setText("")
        self.addButton.setText(QCoreApplication.translate("AssortForm", u"Add offer...", None))
        self.copyButton.setText(QCoreApplication.translate("AssortForm", u"Copy", None))
        self.deleteButton.setText(QCoreApplication.translate("AssortForm", u"Delete", None))
        pass
    # retranslateUi

