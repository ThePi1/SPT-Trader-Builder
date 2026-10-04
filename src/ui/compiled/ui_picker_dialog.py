# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'picker_dialog.ui'
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
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_PickerForm(object):
    def setupUi(self, PickerForm):
        if not PickerForm.objectName():
            PickerForm.setObjectName(u"PickerForm")
        PickerForm.resize(760, 480)
        self.verticalLayout = QVBoxLayout(PickerForm)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.buttons = QDialogButtonBox(PickerForm)
        self.buttons.setObjectName(u"buttons")
        self.buttons.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttons)


        self.retranslateUi(PickerForm)
        self.buttons.accepted.connect(PickerForm.accept)
        self.buttons.rejected.connect(PickerForm.reject)

        QMetaObject.connectSlotsByName(PickerForm)
    # setupUi

    def retranslateUi(self, PickerForm):
        pass
    # retranslateUi

