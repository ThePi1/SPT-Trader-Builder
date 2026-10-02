# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'gui_updates.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QLabel, QSizePolicy,
    QWidget)

class Ui_UpdateMenu(object):
    def setupUi(self, UpdateMenu):
        if not UpdateMenu.objectName():
            UpdateMenu.setObjectName(u"UpdateMenu")
        UpdateMenu.resize(300, 140)
        UpdateMenu.setMinimumSize(QSize(300, 140))
        UpdateMenu.setMaximumSize(QSize(300, 140))
        icon = QIcon()
        icon.addFile(u"data/icon.ico", QSize(), QIcon.Normal, QIcon.Off)
        UpdateMenu.setWindowIcon(icon)
        self.label = QLabel(UpdateMenu)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(10, 10, 280, 120))
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setScaledContents(False)
        self.label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.label.setWordWrap(True)
        self.label.setOpenExternalLinks(True)

        self.retranslateUi(UpdateMenu)

        QMetaObject.connectSlotsByName(UpdateMenu)
    # setupUi

    def retranslateUi(self, UpdateMenu):
        UpdateMenu.setWindowTitle(QCoreApplication.translate("UpdateMenu", u"About", None))
        self.label.setText(QCoreApplication.translate("UpdateMenu", u"<html><head/><body><p>Current version: V_CUR</p><p>Latest version: V_LAT</p><p>UPDATE_TEXT</p><a href=\"SRC_URL\"><span style=\" text-decoration: underline; color:#0000ff;\">SRC_URL</span></a></body></html>", None))
    # retranslateUi

