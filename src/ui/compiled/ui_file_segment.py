# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'file_segment.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_FileSegmentForm(object):
    def setupUi(self, FileSegmentForm):
        if not FileSegmentForm.objectName():
            FileSegmentForm.setObjectName(u"FileSegmentForm")
        FileSegmentForm.setCursor(QCursor(Qt.PointingHandCursor))
        FileSegmentForm.setFocusPolicy(Qt.StrongFocus)
        FileSegmentForm.setStyleSheet(u"#FileSegmentForm { border-right: 1px solid palette(mid); } #FileSegmentForm:focus, #FileSegmentForm:hover { background: palette(midlight); }")
        self.verticalLayout = QVBoxLayout(FileSegmentForm)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(10, 5, 10, 5)
        self.titleRow = QHBoxLayout()
        self.titleRow.setObjectName(u"titleRow")
        self.titleLabel = QLabel(FileSegmentForm)
        self.titleLabel.setObjectName(u"titleLabel")

        self.titleRow.addWidget(self.titleLabel)

        self.stateLabel = QLabel(FileSegmentForm)
        self.stateLabel.setObjectName(u"stateLabel")
        self.stateLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.titleRow.addWidget(self.stateLabel)

        self.titleRow.setStretch(0, 1)

        self.verticalLayout.addLayout(self.titleRow)

        self.fileLabel = QLabel(FileSegmentForm)
        self.fileLabel.setObjectName(u"fileLabel")
        self.fileLabel.setStyleSheet(u"color: #808080;")

        self.verticalLayout.addWidget(self.fileLabel)


        self.retranslateUi(FileSegmentForm)

        QMetaObject.connectSlotsByName(FileSegmentForm)
    # setupUi

    def retranslateUi(self, FileSegmentForm):
        self.titleLabel.setText(QCoreApplication.translate("FileSegmentForm", u"Quests", None))
        self.stateLabel.setText("")
        self.fileLabel.setText("")
        pass
    # retranslateUi

