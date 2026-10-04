# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'composite_tab.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QSizePolicy, QSplitter,
    QVBoxLayout, QWidget)

class Ui_CompositeForm(object):
    def setupUi(self, CompositeForm):
        if not CompositeForm.objectName():
            CompositeForm.setObjectName(u"CompositeForm")
        self.outerLayout = QHBoxLayout(CompositeForm)
        self.outerLayout.setObjectName(u"outerLayout")
        self.outerLayout.setContentsMargins(0, 0, 0, 0)
        self.splitter = QSplitter(CompositeForm)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.leftPane = QWidget(self.splitter)
        self.leftPane.setObjectName(u"leftPane")
        self.leftLayout = QVBoxLayout(self.leftPane)
        self.leftLayout.setObjectName(u"leftLayout")
        self.leftLayout.setContentsMargins(0, 0, 0, 0)
        self.mineLabel = QLabel(self.leftPane)
        self.mineLabel.setObjectName(u"mineLabel")

        self.leftLayout.addWidget(self.mineLabel)

        self.mine = QListWidget(self.leftPane)
        self.mine.setObjectName(u"mine")

        self.leftLayout.addWidget(self.mine)

        self.buttonRow = QHBoxLayout()
        self.buttonRow.setObjectName(u"buttonRow")
        self.newButton = QPushButton(self.leftPane)
        self.newButton.setObjectName(u"newButton")

        self.buttonRow.addWidget(self.newButton)

        self.renameButton = QPushButton(self.leftPane)
        self.renameButton.setObjectName(u"renameButton")

        self.buttonRow.addWidget(self.renameButton)

        self.deleteButton = QPushButton(self.leftPane)
        self.deleteButton.setObjectName(u"deleteButton")

        self.buttonRow.addWidget(self.deleteButton)


        self.leftLayout.addLayout(self.buttonRow)

        self.vanillaLabel = QLabel(self.leftPane)
        self.vanillaLabel.setObjectName(u"vanillaLabel")

        self.leftLayout.addWidget(self.vanillaLabel)

        self.vanilla = QListWidget(self.leftPane)
        self.vanilla.setObjectName(u"vanilla")

        self.leftLayout.addWidget(self.vanilla)

        self.copyButton = QPushButton(self.leftPane)
        self.copyButton.setObjectName(u"copyButton")

        self.leftLayout.addWidget(self.copyButton)

        self.leftLayout.setStretch(1, 2)
        self.leftLayout.setStretch(4, 2)
        self.splitter.addWidget(self.leftPane)
        self.right = QWidget(self.splitter)
        self.right.setObjectName(u"right")
        self.right_layout = QVBoxLayout(self.right)
        self.right_layout.setObjectName(u"right_layout")
        self.right_layout.setContentsMargins(9, 9, 9, 9)
        self.splitter.addWidget(self.right)

        self.outerLayout.addWidget(self.splitter)


        self.retranslateUi(CompositeForm)

        QMetaObject.connectSlotsByName(CompositeForm)
    # setupUi

    def retranslateUi(self, CompositeForm):
        self.mineLabel.setText(QCoreApplication.translate("CompositeForm", u"<b>My items</b>", None))
        self.newButton.setText(QCoreApplication.translate("CompositeForm", u"New", None))
        self.renameButton.setText(QCoreApplication.translate("CompositeForm", u"Rename", None))
        self.deleteButton.setText(QCoreApplication.translate("CompositeForm", u"Delete", None))
        self.vanillaLabel.setText(QCoreApplication.translate("CompositeForm", u"<b>Base game items</b> (read only)", None))
        self.copyButton.setText(QCoreApplication.translate("CompositeForm", u"Make my own copy", None))
        pass
    # retranslateUi

