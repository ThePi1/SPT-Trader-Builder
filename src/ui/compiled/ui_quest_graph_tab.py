# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'quest_graph_tab.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QSpacerItem, QSpinBox, QVBoxLayout, QWidget)

class Ui_QuestGraphForm(object):
    def setupUi(self, QuestGraphForm):
        if not QuestGraphForm.objectName():
            QuestGraphForm.setObjectName(u"QuestGraphForm")
        self.verticalLayout = QVBoxLayout(QuestGraphForm)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.topRow = QHBoxLayout()
        self.topRow.setObjectName(u"topRow")
        self.search = QLineEdit(QuestGraphForm)
        self.search.setObjectName(u"search")
        self.search.setClearButtonEnabled(True)

        self.topRow.addWidget(self.search)

        self.traderBox = QComboBox(QuestGraphForm)
        self.traderBox.setObjectName(u"traderBox")

        self.topRow.addWidget(self.traderBox)

        self.openBox = QCheckBox(QuestGraphForm)
        self.openBox.setObjectName(u"openBox")
        self.openBox.setChecked(True)

        self.topRow.addWidget(self.openBox)

        self.referenceBox = QCheckBox(QuestGraphForm)
        self.referenceBox.setObjectName(u"referenceBox")
        self.referenceBox.setChecked(True)

        self.topRow.addWidget(self.referenceBox)

        self.gameBox = QCheckBox(QuestGraphForm)
        self.gameBox.setObjectName(u"gameBox")
        self.gameBox.setChecked(False)

        self.topRow.addWidget(self.gameBox)


        self.verticalLayout.addLayout(self.topRow)

        self.optionsRow = QHBoxLayout()
        self.optionsRow.setObjectName(u"optionsRow")
        self.showLabel = QLabel(QuestGraphForm)
        self.showLabel.setObjectName(u"showLabel")

        self.optionsRow.addWidget(self.showLabel)

        self.modeBox = QComboBox(QuestGraphForm)
        self.modeBox.setObjectName(u"modeBox")

        self.optionsRow.addWidget(self.modeBox)

        self.stepsLabel = QLabel(QuestGraphForm)
        self.stepsLabel.setObjectName(u"stepsLabel")

        self.optionsRow.addWidget(self.stepsLabel)

        self.stepsBox = QSpinBox(QuestGraphForm)
        self.stepsBox.setObjectName(u"stepsBox")
        self.stepsBox.setMaximum(12)
        self.stepsBox.setValue(1)

        self.optionsRow.addWidget(self.stepsBox)

        self.lanesBox = QCheckBox(QuestGraphForm)
        self.lanesBox.setObjectName(u"lanesBox")

        self.optionsRow.addWidget(self.lanesBox)

        self.failsBox = QCheckBox(QuestGraphForm)
        self.failsBox.setObjectName(u"failsBox")
        self.failsBox.setChecked(True)

        self.optionsRow.addWidget(self.failsBox)

        self.finishBox = QCheckBox(QuestGraphForm)
        self.finishBox.setObjectName(u"finishBox")
        self.finishBox.setChecked(True)

        self.optionsRow.addWidget(self.finishBox)

        self.fitButton = QPushButton(QuestGraphForm)
        self.fitButton.setObjectName(u"fitButton")

        self.optionsRow.addWidget(self.fitButton)

        self.spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.optionsRow.addItem(self.spacer)


        self.verticalLayout.addLayout(self.optionsRow)

        self.viewHost = QWidget(QuestGraphForm)
        self.viewHost.setObjectName(u"viewHost")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.viewHost.sizePolicy().hasHeightForWidth())
        self.viewHost.setSizePolicy(sizePolicy)
        self.viewLayout = QVBoxLayout(self.viewHost)
        self.viewLayout.setObjectName(u"viewLayout")
        self.viewLayout.setContentsMargins(0, 0, 0, 0)

        self.verticalLayout.addWidget(self.viewHost)

        self.detailRow = QHBoxLayout()
        self.detailRow.setObjectName(u"detailRow")
        self.details = QLabel(QuestGraphForm)
        self.details.setObjectName(u"details")
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.details.sizePolicy().hasHeightForWidth())
        self.details.setSizePolicy(sizePolicy1)
        self.details.setWordWrap(True)

        self.detailRow.addWidget(self.details)

        self.openButton = QPushButton(QuestGraphForm)
        self.openButton.setObjectName(u"openButton")
        self.openButton.setVisible(False)

        self.detailRow.addWidget(self.openButton)


        self.verticalLayout.addLayout(self.detailRow)

        self.info = QLabel(QuestGraphForm)
        self.info.setObjectName(u"info")
        self.info.setStyleSheet(u"color: #808080;")
        self.info.setWordWrap(True)

        self.verticalLayout.addWidget(self.info)


        self.retranslateUi(QuestGraphForm)

        QMetaObject.connectSlotsByName(QuestGraphForm)
    # setupUi

    def retranslateUi(self, QuestGraphForm):
        self.search.setPlaceholderText(QCoreApplication.translate("QuestGraphForm", u"Find a quest by name or id (Enter to go to it)", None))
#if QT_CONFIG(tooltip)
        self.traderBox.setToolTip(QCoreApplication.translate("QuestGraphForm", u"Show only the quests of one trader", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.openBox.setToolTip(QCoreApplication.translate("QuestGraphForm", u"The quests open in the Quests tab (opened or imported)", None))
#endif // QT_CONFIG(tooltip)
        self.openBox.setText(QCoreApplication.translate("QuestGraphForm", u"Your quests", None))
#if QT_CONFIG(tooltip)
        self.referenceBox.setToolTip(QCoreApplication.translate("QuestGraphForm", u"The quests in the reference files", None))
#endif // QT_CONFIG(tooltip)
        self.referenceBox.setText(QCoreApplication.translate("QuestGraphForm", u"Reference files", None))
#if QT_CONFIG(tooltip)
        self.gameBox.setToolTip(QCoreApplication.translate("QuestGraphForm", u"The quests of the base game", None))
#endif // QT_CONFIG(tooltip)
        self.gameBox.setText(QCoreApplication.translate("QuestGraphForm", u"Base game", None))
        self.showLabel.setText(QCoreApplication.translate("QuestGraphForm", u"Show", None))
#if QT_CONFIG(tooltip)
        self.modeBox.setToolTip(QCoreApplication.translate("QuestGraphForm", u"Everything at once, or only what is around the quest you have selected", None))
#endif // QT_CONFIG(tooltip)
        self.stepsLabel.setText(QCoreApplication.translate("QuestGraphForm", u"Steps", None))
#if QT_CONFIG(tooltip)
        self.stepsBox.setToolTip(QCoreApplication.translate("QuestGraphForm", u"How many quests before and after the selected one to show (0 is all of them)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.lanesBox.setToolTip(QCoreApplication.translate("QuestGraphForm", u"Give each trader a row of its own", None))
#endif // QT_CONFIG(tooltip)
        self.lanesBox.setText(QCoreApplication.translate("QuestGraphForm", u"Lanes by trader", None))
#if QT_CONFIG(tooltip)
        self.failsBox.setToolTip(QCoreApplication.translate("QuestGraphForm", u"The links between quests that fail each other", None))
#endif // QT_CONFIG(tooltip)
        self.failsBox.setText(QCoreApplication.translate("QuestGraphForm", u"Fail links", None))
#if QT_CONFIG(tooltip)
        self.finishBox.setToolTip(QCoreApplication.translate("QuestGraphForm", u"The links for quests that can only be finished after another", None))
#endif // QT_CONFIG(tooltip)
        self.finishBox.setText(QCoreApplication.translate("QuestGraphForm", u"Needed to finish", None))
#if QT_CONFIG(tooltip)
        self.fitButton.setToolTip(QCoreApplication.translate("QuestGraphForm", u"Zoom so everything shown is in view", None))
#endif // QT_CONFIG(tooltip)
        self.fitButton.setText(QCoreApplication.translate("QuestGraphForm", u"Fit", None))
        self.details.setText("")
        self.openButton.setText(QCoreApplication.translate("QuestGraphForm", u"Open in the Quests tab", None))
        self.info.setText("")
        pass
    # retranslateUi

