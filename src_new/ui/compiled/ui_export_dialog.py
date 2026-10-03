# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'export_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QDialog,
    QDialogButtonBox, QGridLayout, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_ExportForm(object):
    def setupUi(self, ExportForm):
        if not ExportForm.objectName():
            ExportForm.setObjectName(u"ExportForm")
        ExportForm.resize(680, 300)
        self.verticalLayout = QVBoxLayout(ExportForm)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.summaryLabel = QLabel(ExportForm)
        self.summaryLabel.setObjectName(u"summaryLabel")
        self.summaryLabel.setWordWrap(True)

        self.verticalLayout.addWidget(self.summaryLabel)

        self.grid = QGridLayout()
        self.grid.setObjectName(u"grid")
        self.questsLabel = QLabel(ExportForm)
        self.questsLabel.setObjectName(u"questsLabel")

        self.grid.addWidget(self.questsLabel, 0, 0, 1, 1)

        self.questsEdit = QLineEdit(ExportForm)
        self.questsEdit.setObjectName(u"questsEdit")

        self.grid.addWidget(self.questsEdit, 0, 1, 1, 1)

        self.questsBrowse = QPushButton(ExportForm)
        self.questsBrowse.setObjectName(u"questsBrowse")

        self.grid.addWidget(self.questsBrowse, 0, 2, 1, 1)

        self.localeBox = QCheckBox(ExportForm)
        self.localeBox.setObjectName(u"localeBox")
        self.localeBox.setChecked(True)

        self.grid.addWidget(self.localeBox, 1, 0, 1, 1)

        self.localeEdit = QLineEdit(ExportForm)
        self.localeEdit.setObjectName(u"localeEdit")

        self.grid.addWidget(self.localeEdit, 1, 1, 1, 1)

        self.localeBrowse = QPushButton(ExportForm)
        self.localeBrowse.setObjectName(u"localeBrowse")

        self.grid.addWidget(self.localeBrowse, 1, 2, 1, 1)

        self.assortBox = QCheckBox(ExportForm)
        self.assortBox.setObjectName(u"assortBox")
        self.assortBox.setChecked(True)

        self.grid.addWidget(self.assortBox, 2, 0, 1, 1)

        self.assortEdit = QLineEdit(ExportForm)
        self.assortEdit.setObjectName(u"assortEdit")

        self.grid.addWidget(self.assortEdit, 2, 1, 1, 1)

        self.assortBrowse = QPushButton(ExportForm)
        self.assortBrowse.setObjectName(u"assortBrowse")

        self.grid.addWidget(self.assortBrowse, 2, 2, 1, 1)

        self.locksBox = QCheckBox(ExportForm)
        self.locksBox.setObjectName(u"locksBox")
        self.locksBox.setChecked(True)

        self.grid.addWidget(self.locksBox, 3, 0, 1, 1)

        self.locksEdit = QLineEdit(ExportForm)
        self.locksEdit.setObjectName(u"locksEdit")

        self.grid.addWidget(self.locksEdit, 3, 1, 1, 1)

        self.locksBrowse = QPushButton(ExportForm)
        self.locksBrowse.setObjectName(u"locksBrowse")

        self.grid.addWidget(self.locksBrowse, 3, 2, 1, 1)


        self.verticalLayout.addLayout(self.grid)

        self.noteLabel = QLabel(ExportForm)
        self.noteLabel.setObjectName(u"noteLabel")
        self.noteLabel.setStyleSheet(u"color: #808080;")
        self.noteLabel.setWordWrap(True)

        self.verticalLayout.addWidget(self.noteLabel)

        self.verticalSpacer = QSpacerItem(20, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.buttons = QDialogButtonBox(ExportForm)
        self.buttons.setObjectName(u"buttons")
        self.buttons.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttons)


        self.retranslateUi(ExportForm)
        self.buttons.accepted.connect(ExportForm.accept)
        self.buttons.rejected.connect(ExportForm.reject)

        QMetaObject.connectSlotsByName(ExportForm)
    # setupUi

    def retranslateUi(self, ExportForm):
        ExportForm.setWindowTitle(QCoreApplication.translate("ExportForm", u"Export quests", None))
        self.summaryLabel.setText("")
        self.questsLabel.setText(QCoreApplication.translate("ExportForm", u"Quests", None))
        self.questsBrowse.setText(QCoreApplication.translate("ExportForm", u"Browse...", None))
        self.localeBox.setText(QCoreApplication.translate("ExportForm", u"Their text", None))
        self.localeBrowse.setText(QCoreApplication.translate("ExportForm", u"Browse...", None))
        self.assortBox.setText(QCoreApplication.translate("ExportForm", u"Their trader offers", None))
        self.assortBrowse.setText(QCoreApplication.translate("ExportForm", u"Browse...", None))
        self.locksBox.setText(QCoreApplication.translate("ExportForm", u"Their quest assort", None))
        self.locksBrowse.setText(QCoreApplication.translate("ExportForm", u"Browse...", None))
        self.noteLabel.setText(QCoreApplication.translate("ExportForm", u"Only these files are written. What is open is not changed.", None))
    # retranslateUi

