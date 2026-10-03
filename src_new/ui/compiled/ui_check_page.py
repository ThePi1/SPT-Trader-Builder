# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'check_page.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QHBoxLayout,
    QLabel, QListWidget, QListWidgetItem, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_CheckForm(object):
    def setupUi(self, CheckForm):
        if not CheckForm.objectName():
            CheckForm.setObjectName(u"CheckForm")
        self.verticalLayout = QVBoxLayout(CheckForm)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.topRow = QHBoxLayout()
        self.topRow.setObjectName(u"topRow")
        self.openButton = QPushButton(CheckForm)
        self.openButton.setObjectName(u"openButton")

        self.topRow.addWidget(self.openButton)

        self.kind = QComboBox(CheckForm)
        self.kind.setObjectName(u"kind")

        self.topRow.addWidget(self.kind)

        self.with_open = QCheckBox(CheckForm)
        self.with_open.setObjectName(u"with_open")

        self.topRow.addWidget(self.with_open)

        self.topSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.topRow.addItem(self.topSpacer)


        self.verticalLayout.addLayout(self.topRow)

        self.summary = QLabel(CheckForm)
        self.summary.setObjectName(u"summary")
        self.summary.setWordWrap(True)

        self.verticalLayout.addWidget(self.summary)

        self.list = QListWidget(CheckForm)
        self.list.setObjectName(u"list")

        self.verticalLayout.addWidget(self.list)


        self.retranslateUi(CheckForm)

        QMetaObject.connectSlotsByName(CheckForm)
    # setupUi

    def retranslateUi(self, CheckForm):
        self.openButton.setText(QCoreApplication.translate("CheckForm", u"Open a file to check...", None))
        self.with_open.setText(QCoreApplication.translate("CheckForm", u"Check against the quests and locale that are open", None))
        self.summary.setText(QCoreApplication.translate("CheckForm", u"Open a quest, locale, assort or quest-lock file. Nothing is changed in it.", None))
        pass
    # retranslateUi

