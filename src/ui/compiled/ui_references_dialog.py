# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'references_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QApplication, QDialog,
    QDialogButtonBox, QHBoxLayout, QHeaderView, QLabel,
    QPushButton, QSizePolicy, QSpacerItem, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_ReferencesForm(object):
    def setupUi(self, ReferencesForm):
        if not ReferencesForm.objectName():
            ReferencesForm.setObjectName(u"ReferencesForm")
        ReferencesForm.setMinimumSize(QSize(720, 360))
        self.verticalLayout = QVBoxLayout(ReferencesForm)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.hint = QLabel(ReferencesForm)
        self.hint.setObjectName(u"hint")
        self.hint.setWordWrap(True)

        self.verticalLayout.addWidget(self.hint)

        self.table = QTableWidget(ReferencesForm)
        if (self.table.columnCount() < 4):
            self.table.setColumnCount(4)
        __qtablewidgetitem = QTableWidgetItem()
        self.table.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.table.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.table.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.table.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        self.table.setObjectName(u"table")
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)

        self.verticalLayout.addWidget(self.table)

        self.buttonRow = QHBoxLayout()
        self.buttonRow.setObjectName(u"buttonRow")
        self.addFilesButton = QPushButton(ReferencesForm)
        self.addFilesButton.setObjectName(u"addFilesButton")

        self.buttonRow.addWidget(self.addFilesButton)

        self.addFolderButton = QPushButton(ReferencesForm)
        self.addFolderButton.setObjectName(u"addFolderButton")

        self.buttonRow.addWidget(self.addFolderButton)

        self.removeButton = QPushButton(ReferencesForm)
        self.removeButton.setObjectName(u"removeButton")

        self.buttonRow.addWidget(self.removeButton)

        self.reloadButton = QPushButton(ReferencesForm)
        self.reloadButton.setObjectName(u"reloadButton")

        self.buttonRow.addWidget(self.reloadButton)

        self.importButton = QPushButton(ReferencesForm)
        self.importButton.setObjectName(u"importButton")

        self.buttonRow.addWidget(self.importButton)

        self.spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.buttonRow.addItem(self.spacer)


        self.verticalLayout.addLayout(self.buttonRow)

        self.buttons = QDialogButtonBox(ReferencesForm)
        self.buttons.setObjectName(u"buttons")
        self.buttons.setStandardButtons(QDialogButtonBox.Close)

        self.verticalLayout.addWidget(self.buttons)


        self.retranslateUi(ReferencesForm)
        self.buttons.rejected.connect(ReferencesForm.reject)

        QMetaObject.connectSlotsByName(ReferencesForm)
    # setupUi

    def retranslateUi(self, ReferencesForm):
        ReferencesForm.setWindowTitle(QCoreApplication.translate("ReferencesForm", u"Reference files", None))
        self.hint.setText(QCoreApplication.translate("ReferencesForm", u"Reference files are only looked at: the quests, items, traders and trader offers in them are named and can be found in Find IDs and the Find windows. They are never edited, merged, saved or exported.", None))
        ___qtablewidgetitem = self.table.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("ReferencesForm", u"File", None));
        ___qtablewidgetitem1 = self.table.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("ReferencesForm", u"Type", None));
        ___qtablewidgetitem2 = self.table.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("ReferencesForm", u"Ids", None));
        ___qtablewidgetitem3 = self.table.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("ReferencesForm", u"Folder", None));
        self.addFilesButton.setText(QCoreApplication.translate("ReferencesForm", u"Add files...", None))
        self.addFolderButton.setText(QCoreApplication.translate("ReferencesForm", u"Add folder...", None))
        self.removeButton.setText(QCoreApplication.translate("ReferencesForm", u"Remove", None))
        self.reloadButton.setText(QCoreApplication.translate("ReferencesForm", u"Reload", None))
#if QT_CONFIG(tooltip)
        self.importButton.setToolTip(QCoreApplication.translate("ReferencesForm", u"Merge the selected quest, locale or trader assort files into the files you have open", None))
#endif // QT_CONFIG(tooltip)
        self.importButton.setText(QCoreApplication.translate("ReferencesForm", u"Import into the open files...", None))
    # retranslateUi

