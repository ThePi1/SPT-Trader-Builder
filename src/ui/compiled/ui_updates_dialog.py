# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'updates_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QLabel, QSizePolicy, QVBoxLayout, QWidget)

class Ui_UpdatesForm(object):
    def setupUi(self, UpdatesForm):
        if not UpdatesForm.objectName():
            UpdatesForm.setObjectName(u"UpdatesForm")
        self.verticalLayout = QVBoxLayout(UpdatesForm)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(UpdatesForm)
        self.label.setObjectName(u"label")
        self.label.setOpenExternalLinks(True)

        self.verticalLayout.addWidget(self.label)

        self.buttons = QDialogButtonBox(UpdatesForm)
        self.buttons.setObjectName(u"buttons")
        self.buttons.setStandardButtons(QDialogButtonBox.Close)

        self.verticalLayout.addWidget(self.buttons)


        self.retranslateUi(UpdatesForm)
        self.buttons.rejected.connect(UpdatesForm.reject)

        QMetaObject.connectSlotsByName(UpdatesForm)
    # setupUi

    def retranslateUi(self, UpdatesForm):
        UpdatesForm.setWindowTitle(QCoreApplication.translate("UpdatesForm", u"Check for updates", None))
        self.label.setText(QCoreApplication.translate("UpdatesForm", u"The versions are filled in by the program.", None))
    # retranslateUi

