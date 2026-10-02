# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'gui_about.ui'
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

class Ui_AboutMenu(object):
    def setupUi(self, AboutMenu):
        if not AboutMenu.objectName():
            AboutMenu.setObjectName(u"AboutMenu")
        AboutMenu.resize(400, 135)
        AboutMenu.setMinimumSize(QSize(0, 0))
        AboutMenu.setMaximumSize(QSize(400, 135))
        icon = QIcon()
        icon.addFile(u"data/icon.ico", QSize(), QIcon.Normal, QIcon.Off)
        AboutMenu.setWindowIcon(icon)
        self.label = QLabel(AboutMenu)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(10, 10, 381, 131))
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setMinimumSize(QSize(0, 1))
        self.label.setScaledContents(False)
        self.label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.label.setWordWrap(True)
        self.label.setOpenExternalLinks(True)

        self.retranslateUi(AboutMenu)

        QMetaObject.connectSlotsByName(AboutMenu)
    # setupUi

    def retranslateUi(self, AboutMenu):
        AboutMenu.setWindowTitle(QCoreApplication.translate("AboutMenu", u"About", None))
        self.label.setText(QCoreApplication.translate("AboutMenu", u"<html><head/><body><p>Made with \u2665 by the SPT Trader Builder Team</p><p>V_CUR</p><p><a href=\"SRC_URL\"><span style=\" text-decoration: underline; color:#0000ff;\">SRC_URL</span></a></p></body></html>", None))
    # retranslateUi

