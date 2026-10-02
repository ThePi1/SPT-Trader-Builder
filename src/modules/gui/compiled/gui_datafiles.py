# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'gui_datafiles.ui'
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
from PySide6.QtWidgets import (QApplication, QLabel, QMainWindow, QMenuBar,
    QPushButton, QSizePolicy, QStatusBar, QTabWidget,
    QWidget)

class Ui_DataEditor(object):
    def setupUi(self, DataEditor):
        if not DataEditor.objectName():
            DataEditor.setObjectName(u"DataEditor")
        DataEditor.resize(676, 449)
        self.centralwidget = QWidget(DataEditor)
        self.centralwidget.setObjectName(u"centralwidget")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setGeometry(QRect(0, 0, 661, 401))
        self.tab_3 = QWidget()
        self.tab_3.setObjectName(u"tab_3")
        self.pb_wtt_import = QPushButton(self.tab_3)
        self.pb_wtt_import.setObjectName(u"pb_wtt_import")
        self.pb_wtt_import.setGeometry(QRect(10, 70, 75, 24))
        self.pb_wtt_import.setFocusPolicy(Qt.NoFocus)
        self.label_3 = QLabel(self.tab_3)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(10, 10, 351, 51))
        self.label_3.setWordWrap(True)
        self.tabWidget.addTab(self.tab_3, "")
        DataEditor.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(DataEditor)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 676, 22))
        DataEditor.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(DataEditor)
        self.statusbar.setObjectName(u"statusbar")
        DataEditor.setStatusBar(self.statusbar)

        self.retranslateUi(DataEditor)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(DataEditor)
    # setupUi

    def retranslateUi(self, DataEditor):
        DataEditor.setWindowTitle(QCoreApplication.translate("DataEditor", u"Data File Editor", None))
        self.pb_wtt_import.setText(QCoreApplication.translate("DataEditor", u"Import", None))
        self.label_3.setText(QCoreApplication.translate("DataEditor", u"If using WTTCommonLib, you can use this to import all valid files. Select the top-level folder in the structure.", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), QCoreApplication.translate("DataEditor", u"WTTCommonLib Settings", None))
    # retranslateUi

