# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'import_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QApplication, QCheckBox,
    QDialog, QDialogButtonBox, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QRadioButton, QSizePolicy,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_ImportForm(object):
    def setupUi(self, ImportForm):
        if not ImportForm.objectName():
            ImportForm.setObjectName(u"ImportForm")
        ImportForm.resize(760, 460)
        self.verticalLayout = QVBoxLayout(ImportForm)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.introLabel = QLabel(ImportForm)
        self.introLabel.setObjectName(u"introLabel")
        self.introLabel.setWordWrap(True)

        self.verticalLayout.addWidget(self.introLabel)

        self.table = QTableWidget(ImportForm)
        if (self.table.columnCount() < 6):
            self.table.setColumnCount(6)
        __qtablewidgetitem = QTableWidgetItem()
        self.table.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.table.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.table.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.table.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.table.setHorizontalHeaderItem(4, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.table.setHorizontalHeaderItem(5, __qtablewidgetitem5)
        self.table.setObjectName(u"table")
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)

        self.verticalLayout.addWidget(self.table)

        self.policyBox = QGroupBox(ImportForm)
        self.policyBox.setObjectName(u"policyBox")
        self.policyLayout = QHBoxLayout(self.policyBox)
        self.policyLayout.setObjectName(u"policyLayout")
        self.keepRadio = QRadioButton(self.policyBox)
        self.keepRadio.setObjectName(u"keepRadio")
        self.keepRadio.setChecked(True)

        self.policyLayout.addWidget(self.keepRadio)

        self.replaceRadio = QRadioButton(self.policyBox)
        self.replaceRadio.setObjectName(u"replaceRadio")

        self.policyLayout.addWidget(self.replaceRadio)

        self.bothRadio = QRadioButton(self.policyBox)
        self.bothRadio.setObjectName(u"bothRadio")

        self.policyLayout.addWidget(self.bothRadio)


        self.verticalLayout.addWidget(self.policyBox)

        self.everythingBox = QCheckBox(ImportForm)
        self.everythingBox.setObjectName(u"everythingBox")

        self.verticalLayout.addWidget(self.everythingBox)

        self.summaryLabel = QLabel(ImportForm)
        self.summaryLabel.setObjectName(u"summaryLabel")
        self.summaryLabel.setStyleSheet(u"color: #808080;")
        self.summaryLabel.setWordWrap(True)

        self.verticalLayout.addWidget(self.summaryLabel)

        self.buttons = QDialogButtonBox(ImportForm)
        self.buttons.setObjectName(u"buttons")
        self.buttons.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttons)

        QWidget.setTabOrder(self.table, self.keepRadio)
        QWidget.setTabOrder(self.keepRadio, self.replaceRadio)
        QWidget.setTabOrder(self.replaceRadio, self.bothRadio)
        QWidget.setTabOrder(self.bothRadio, self.everythingBox)

        self.retranslateUi(ImportForm)
        self.buttons.accepted.connect(ImportForm.accept)
        self.buttons.rejected.connect(ImportForm.reject)

        QMetaObject.connectSlotsByName(ImportForm)
    # setupUi

    def retranslateUi(self, ImportForm):
        ImportForm.setWindowTitle(QCoreApplication.translate("ImportForm", u"Import files", None))
        self.introLabel.setText(QCoreApplication.translate("ImportForm", u"These are added to what is open. Your files are not changed until you save.", None))
        ___qtablewidgetitem = self.table.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("ImportForm", u"Import", None));
        ___qtablewidgetitem1 = self.table.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("ImportForm", u"File", None));
        ___qtablewidgetitem2 = self.table.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("ImportForm", u"Type", None));
        ___qtablewidgetitem3 = self.table.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("ImportForm", u"New", None));
        ___qtablewidgetitem4 = self.table.horizontalHeaderItem(4)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("ImportForm", u"Already there", None));
        ___qtablewidgetitem5 = self.table.horizontalHeaderItem(5)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("ImportForm", u"Notes", None));
        self.policyBox.setTitle(QCoreApplication.translate("ImportForm", u"When something is already there", None))
        self.keepRadio.setText(QCoreApplication.translate("ImportForm", u"Keep what I have", None))
        self.replaceRadio.setText(QCoreApplication.translate("ImportForm", u"Use the imported one", None))
        self.bothRadio.setText(QCoreApplication.translate("ImportForm", u"Keep both (the imported one gets a new id)", None))
        self.everythingBox.setText(QCoreApplication.translate("ImportForm", u"Import all the text of locale files, not only the text of the quests", None))
        self.summaryLabel.setText("")
    # retranslateUi

