# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'lookup_tab.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_LookupTabForm(object):
    def setupUi(self, LookupTabForm):
        if not LookupTabForm.objectName():
            LookupTabForm.setObjectName(u"LookupTabForm")
        self.verticalLayout = QVBoxLayout(LookupTabForm)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.buttonRow = QHBoxLayout()
        self.buttonRow.setObjectName(u"buttonRow")
        self.copy_id_button = QPushButton(LookupTabForm)
        self.copy_id_button.setObjectName(u"copy_id_button")

        self.buttonRow.addWidget(self.copy_id_button)

        self.copy_name_button = QPushButton(LookupTabForm)
        self.copy_name_button.setObjectName(u"copy_name_button")

        self.buttonRow.addWidget(self.copy_name_button)

        self.buttonSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.buttonRow.addItem(self.buttonSpacer)


        self.verticalLayout.addLayout(self.buttonRow)


        self.retranslateUi(LookupTabForm)

        QMetaObject.connectSlotsByName(LookupTabForm)
    # setupUi

    def retranslateUi(self, LookupTabForm):
        self.copy_id_button.setText(QCoreApplication.translate("LookupTabForm", u"Copy id", None))
        self.copy_name_button.setText(QCoreApplication.translate("LookupTabForm", u"Copy name", None))
        pass
    # retranslateUi

