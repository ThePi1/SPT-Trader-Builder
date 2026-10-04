# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'explorer_tab.ui'
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
from PySide6.QtWidgets import (QApplication, QSizePolicy, QTabWidget, QWidget)

class Ui_ExplorerForm(object):
    def setupUi(self, ExplorerForm):
        if not ExplorerForm.objectName():
            ExplorerForm.setObjectName(u"ExplorerForm")
        self.page_browse = QWidget()
        self.page_browse.setObjectName(u"page_browse")
        ExplorerForm.addTab(self.page_browse, "")
        self.page_check = QWidget()
        self.page_check.setObjectName(u"page_check")
        ExplorerForm.addTab(self.page_check, "")

        self.retranslateUi(ExplorerForm)

        ExplorerForm.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(ExplorerForm)
    # setupUi

    def retranslateUi(self, ExplorerForm):
        ExplorerForm.setTabText(ExplorerForm.indexOf(self.page_browse), QCoreApplication.translate("ExplorerForm", u"What things are made of", None))
        ExplorerForm.setTabText(ExplorerForm.indexOf(self.page_check), QCoreApplication.translate("ExplorerForm", u"Check a file", None))
        pass
    # retranslateUi

