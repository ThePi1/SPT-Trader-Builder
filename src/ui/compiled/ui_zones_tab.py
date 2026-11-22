# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'zones_tab.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox,
    QFormLayout, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QSizePolicy, QSpacerItem, QSpinBox,
    QSplitter, QTabWidget, QToolButton, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget)

class Ui_ZonesForm(object):
    def setupUi(self, ZonesForm):
        if not ZonesForm.objectName():
            ZonesForm.setObjectName(u"ZonesForm")
        self.verticalLayout = QVBoxLayout(ZonesForm)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.topRow = QHBoxLayout()
        self.topRow.setObjectName(u"topRow")
        self.mapLabel = QLabel(ZonesForm)
        self.mapLabel.setObjectName(u"mapLabel")

        self.topRow.addWidget(self.mapLabel)

        self.mapBox = QComboBox(ZonesForm)
        self.mapBox.setObjectName(u"mapBox")
        self.mapBox.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.topRow.addWidget(self.mapBox)

        self.search = QLineEdit(ZonesForm)
        self.search.setObjectName(u"search")
        self.search.setClearButtonEnabled(True)

        self.topRow.addWidget(self.search)

        self.topDownButton = QToolButton(ZonesForm)
        self.topDownButton.setObjectName(u"topDownButton")
        self.topDownButton.setCheckable(True)

        self.topRow.addWidget(self.topDownButton)

        self.wholeMapButton = QToolButton(ZonesForm)
        self.wholeMapButton.setObjectName(u"wholeMapButton")

        self.topRow.addWidget(self.wholeMapButton)

        self.importButton = QPushButton(ZonesForm)
        self.importButton.setObjectName(u"importButton")

        self.topRow.addWidget(self.importButton)


        self.verticalLayout.addLayout(self.topRow)

        self.versionLabel = QLabel(ZonesForm)
        self.versionLabel.setObjectName(u"versionLabel")
        self.versionLabel.setTextFormat(Qt.RichText)
        self.versionLabel.setWordWrap(True)

        self.verticalLayout.addWidget(self.versionLabel)

        self.layersRow = QHBoxLayout()
        self.layersRow.setObjectName(u"layersRow")
        self.showLabel = QLabel(ZonesForm)
        self.showLabel.setObjectName(u"showLabel")

        self.layersRow.addWidget(self.showLabel)

        self.floorBox = QCheckBox(ZonesForm)
        self.floorBox.setObjectName(u"floorBox")
        self.floorBox.setChecked(True)

        self.layersRow.addWidget(self.floorBox)

        self.wallsBox = QCheckBox(ZonesForm)
        self.wallsBox.setObjectName(u"wallsBox")
        self.wallsBox.setChecked(True)

        self.layersRow.addWidget(self.wallsBox)

        self.gameZonesBox = QCheckBox(ZonesForm)
        self.gameZonesBox.setObjectName(u"gameZonesBox")
        self.gameZonesBox.setChecked(True)

        self.layersRow.addWidget(self.gameZonesBox)

        self.referenceZonesBox = QCheckBox(ZonesForm)
        self.referenceZonesBox.setObjectName(u"referenceZonesBox")
        self.referenceZonesBox.setChecked(True)

        self.layersRow.addWidget(self.referenceZonesBox)

        self.spawnsBox = QCheckBox(ZonesForm)
        self.spawnsBox.setObjectName(u"spawnsBox")
        self.spawnsBox.setChecked(True)

        self.layersRow.addWidget(self.spawnsBox)

        self.areasBox = QCheckBox(ZonesForm)
        self.areasBox.setObjectName(u"areasBox")

        self.layersRow.addWidget(self.areasBox)

        self.labelsBox = QCheckBox(ZonesForm)
        self.labelsBox.setObjectName(u"labelsBox")
        self.labelsBox.setChecked(True)

        self.layersRow.addWidget(self.labelsBox)

        self.layersSpacer = QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.layersRow.addItem(self.layersSpacer)

        self.buildingButton = QPushButton(ZonesForm)
        self.buildingButton.setObjectName(u"buildingButton")

        self.layersRow.addWidget(self.buildingButton)

        self.storeyBox = QComboBox(ZonesForm)
        self.storeyBox.setObjectName(u"storeyBox")
        self.storeyBox.setMinimumContentsLength(12)

        self.layersRow.addWidget(self.storeyBox)


        self.verticalLayout.addLayout(self.layersRow)

        self.splitter = QSplitter(ZonesForm)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.leftPanel = QWidget(self.splitter)
        self.leftPanel.setObjectName(u"leftPanel")
        self.leftLayout = QVBoxLayout(self.leftPanel)
        self.leftLayout.setObjectName(u"leftLayout")
        self.leftLayout.setContentsMargins(0, 0, 0, 0)
        self.zoneFilter = QLineEdit(self.leftPanel)
        self.zoneFilter.setObjectName(u"zoneFilter")
        self.zoneFilter.setClearButtonEnabled(True)

        self.leftLayout.addWidget(self.zoneFilter)

        self.zoneList = QTreeWidget(self.leftPanel)
        self.zoneList.setObjectName(u"zoneList")
        self.zoneList.setRootIsDecorated(False)
        self.zoneList.setUniformRowHeights(True)
        self.zoneList.setSortingEnabled(True)

        self.leftLayout.addWidget(self.zoneList)

        self.splitter.addWidget(self.leftPanel)
        self.viewHost = QWidget(self.splitter)
        self.viewHost.setObjectName(u"viewHost")
        self.viewLayout = QHBoxLayout(self.viewHost)
        self.viewLayout.setSpacing(0)
        self.viewLayout.setObjectName(u"viewLayout")
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.splitter.addWidget(self.viewHost)
        self.rightPanel = QWidget(self.splitter)
        self.rightPanel.setObjectName(u"rightPanel")
        self.rightLayout = QVBoxLayout(self.rightPanel)
        self.rightLayout.setObjectName(u"rightLayout")
        self.rightLayout.setContentsMargins(0, 0, 0, 0)
        self.editTabs = QTabWidget(self.rightPanel)
        self.editTabs.setObjectName(u"editTabs")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.editTabs.sizePolicy().hasHeightForWidth())
        self.editTabs.setSizePolicy(sizePolicy)
        self.zonesPage = QWidget()
        self.zonesPage.setObjectName(u"zonesPage")
        self.zonesPageLayout = QVBoxLayout(self.zonesPage)
        self.zonesPageLayout.setObjectName(u"zonesPageLayout")
        self.zonesPageLayout.setContentsMargins(4, 4, 4, 4)
        self.fileLabel = QLabel(self.zonesPage)
        self.fileLabel.setObjectName(u"fileLabel")
        self.fileLabel.setWordWrap(True)

        self.zonesPageLayout.addWidget(self.fileLabel)

        self.fileRow = QHBoxLayout()
        self.fileRow.setObjectName(u"fileRow")
        self.newFileButton = QPushButton(self.zonesPage)
        self.newFileButton.setObjectName(u"newFileButton")

        self.fileRow.addWidget(self.newFileButton)

        self.openFileButton = QPushButton(self.zonesPage)
        self.openFileButton.setObjectName(u"openFileButton")

        self.fileRow.addWidget(self.openFileButton)

        self.saveFileButton = QPushButton(self.zonesPage)
        self.saveFileButton.setObjectName(u"saveFileButton")

        self.fileRow.addWidget(self.saveFileButton)

        self.saveAsFileButton = QPushButton(self.zonesPage)
        self.saveAsFileButton.setObjectName(u"saveAsFileButton")

        self.fileRow.addWidget(self.saveAsFileButton)


        self.zonesPageLayout.addLayout(self.fileRow)

        self.placeButton = QPushButton(self.zonesPage)
        self.placeButton.setObjectName(u"placeButton")
        self.placeButton.setCheckable(True)

        self.zonesPageLayout.addWidget(self.placeButton)

        self.zoneGroup = QGroupBox(self.zonesPage)
        self.zoneGroup.setObjectName(u"zoneGroup")
        self.zoneForm = QFormLayout(self.zoneGroup)
        self.zoneForm.setObjectName(u"zoneForm")
        self.idLabel = QLabel(self.zoneGroup)
        self.idLabel.setObjectName(u"idLabel")

        self.zoneForm.setWidget(0, QFormLayout.LabelRole, self.idLabel)

        self.idEdit = QLineEdit(self.zoneGroup)
        self.idEdit.setObjectName(u"idEdit")

        self.zoneForm.setWidget(0, QFormLayout.FieldRole, self.idEdit)

        self.nameLabel = QLabel(self.zoneGroup)
        self.nameLabel.setObjectName(u"nameLabel")

        self.zoneForm.setWidget(1, QFormLayout.LabelRole, self.nameLabel)

        self.nameEdit = QLineEdit(self.zoneGroup)
        self.nameEdit.setObjectName(u"nameEdit")

        self.zoneForm.setWidget(1, QFormLayout.FieldRole, self.nameEdit)

        self.kindLabel = QLabel(self.zoneGroup)
        self.kindLabel.setObjectName(u"kindLabel")

        self.zoneForm.setWidget(2, QFormLayout.LabelRole, self.kindLabel)

        self.kindBox = QComboBox(self.zoneGroup)
        self.kindBox.setObjectName(u"kindBox")

        self.zoneForm.setWidget(2, QFormLayout.FieldRole, self.kindBox)

        self.positionLabel = QLabel(self.zoneGroup)
        self.positionLabel.setObjectName(u"positionLabel")

        self.zoneForm.setWidget(3, QFormLayout.LabelRole, self.positionLabel)

        self.positionRow = QHBoxLayout()
        self.positionRow.setObjectName(u"positionRow")
        self.xSpin = QDoubleSpinBox(self.zoneGroup)
        self.xSpin.setObjectName(u"xSpin")
        self.xSpin.setDecimals(2)
        self.xSpin.setMinimum(-5000.000000000000000)
        self.xSpin.setMaximum(5000.000000000000000)
        self.xSpin.setSingleStep(0.250000000000000)

        self.positionRow.addWidget(self.xSpin)

        self.ySpin = QDoubleSpinBox(self.zoneGroup)
        self.ySpin.setObjectName(u"ySpin")
        self.ySpin.setDecimals(2)
        self.ySpin.setMinimum(-5000.000000000000000)
        self.ySpin.setMaximum(5000.000000000000000)
        self.ySpin.setSingleStep(0.250000000000000)

        self.positionRow.addWidget(self.ySpin)

        self.zSpin = QDoubleSpinBox(self.zoneGroup)
        self.zSpin.setObjectName(u"zSpin")
        self.zSpin.setDecimals(2)
        self.zSpin.setMinimum(-5000.000000000000000)
        self.zSpin.setMaximum(5000.000000000000000)
        self.zSpin.setSingleStep(0.250000000000000)

        self.positionRow.addWidget(self.zSpin)


        self.zoneForm.setLayout(3, QFormLayout.FieldRole, self.positionRow)

        self.sizeLabel = QLabel(self.zoneGroup)
        self.sizeLabel.setObjectName(u"sizeLabel")

        self.zoneForm.setWidget(4, QFormLayout.LabelRole, self.sizeLabel)

        self.sizeRow = QHBoxLayout()
        self.sizeRow.setObjectName(u"sizeRow")
        self.widthSpin = QDoubleSpinBox(self.zoneGroup)
        self.widthSpin.setObjectName(u"widthSpin")
        self.widthSpin.setDecimals(2)
        self.widthSpin.setMinimum(0.200000000000000)
        self.widthSpin.setMaximum(2000.000000000000000)
        self.widthSpin.setSingleStep(0.250000000000000)

        self.sizeRow.addWidget(self.widthSpin)

        self.heightSpin = QDoubleSpinBox(self.zoneGroup)
        self.heightSpin.setObjectName(u"heightSpin")
        self.heightSpin.setDecimals(2)
        self.heightSpin.setMinimum(0.200000000000000)
        self.heightSpin.setMaximum(2000.000000000000000)
        self.heightSpin.setSingleStep(0.250000000000000)

        self.sizeRow.addWidget(self.heightSpin)

        self.depthSpin = QDoubleSpinBox(self.zoneGroup)
        self.depthSpin.setObjectName(u"depthSpin")
        self.depthSpin.setDecimals(2)
        self.depthSpin.setMinimum(0.200000000000000)
        self.depthSpin.setMaximum(2000.000000000000000)
        self.depthSpin.setSingleStep(0.250000000000000)

        self.sizeRow.addWidget(self.depthSpin)


        self.zoneForm.setLayout(4, QFormLayout.FieldRole, self.sizeRow)

        self.yawLabel = QLabel(self.zoneGroup)
        self.yawLabel.setObjectName(u"yawLabel")

        self.zoneForm.setWidget(5, QFormLayout.LabelRole, self.yawLabel)

        self.yawSpin = QDoubleSpinBox(self.zoneGroup)
        self.yawSpin.setObjectName(u"yawSpin")
        self.yawSpin.setDecimals(1)
        self.yawSpin.setMaximum(360.000000000000000)
        self.yawSpin.setSingleStep(5.000000000000000)
        self.yawSpin.setWrapping(True)

        self.zoneForm.setWidget(5, QFormLayout.FieldRole, self.yawSpin)

        self.zoneButtonsRow = QHBoxLayout()
        self.zoneButtonsRow.setObjectName(u"zoneButtonsRow")
        self.floorButton = QPushButton(self.zoneGroup)
        self.floorButton.setObjectName(u"floorButton")

        self.zoneButtonsRow.addWidget(self.floorButton)

        self.slopeButton = QPushButton(self.zoneGroup)
        self.slopeButton.setObjectName(u"slopeButton")

        self.zoneButtonsRow.addWidget(self.slopeButton)

        self.lookButton = QPushButton(self.zoneGroup)
        self.lookButton.setObjectName(u"lookButton")

        self.zoneButtonsRow.addWidget(self.lookButton)


        self.zoneForm.setLayout(6, QFormLayout.SpanningRole, self.zoneButtonsRow)

        self.zoneButtonsRow2 = QHBoxLayout()
        self.zoneButtonsRow2.setObjectName(u"zoneButtonsRow2")
        self.copyButton = QPushButton(self.zoneGroup)
        self.copyButton.setObjectName(u"copyButton")

        self.zoneButtonsRow2.addWidget(self.copyButton)

        self.deleteButton = QPushButton(self.zoneGroup)
        self.deleteButton.setObjectName(u"deleteButton")

        self.zoneButtonsRow2.addWidget(self.deleteButton)


        self.zoneForm.setLayout(7, QFormLayout.SpanningRole, self.zoneButtonsRow2)


        self.zonesPageLayout.addWidget(self.zoneGroup)

        self.zonesPageSpacer = QSpacerItem(10, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.zonesPageLayout.addItem(self.zonesPageSpacer)

        self.editTabs.addTab(self.zonesPage, "")
        self.spawnsPage = QWidget()
        self.spawnsPage.setObjectName(u"spawnsPage")
        self.spawnsPageLayout = QVBoxLayout(self.spawnsPage)
        self.spawnsPageLayout.setObjectName(u"spawnsPageLayout")
        self.spawnsPageLayout.setContentsMargins(4, 4, 4, 4)
        self.spawnFileLabel = QLabel(self.spawnsPage)
        self.spawnFileLabel.setObjectName(u"spawnFileLabel")
        self.spawnFileLabel.setWordWrap(True)

        self.spawnsPageLayout.addWidget(self.spawnFileLabel)

        self.spawnFileRow = QHBoxLayout()
        self.spawnFileRow.setObjectName(u"spawnFileRow")
        self.newSpawnFileButton = QPushButton(self.spawnsPage)
        self.newSpawnFileButton.setObjectName(u"newSpawnFileButton")

        self.spawnFileRow.addWidget(self.newSpawnFileButton)

        self.openSpawnFileButton = QPushButton(self.spawnsPage)
        self.openSpawnFileButton.setObjectName(u"openSpawnFileButton")

        self.spawnFileRow.addWidget(self.openSpawnFileButton)

        self.saveSpawnFileButton = QPushButton(self.spawnsPage)
        self.saveSpawnFileButton.setObjectName(u"saveSpawnFileButton")

        self.spawnFileRow.addWidget(self.saveSpawnFileButton)

        self.saveAsSpawnFileButton = QPushButton(self.spawnsPage)
        self.saveAsSpawnFileButton.setObjectName(u"saveAsSpawnFileButton")

        self.spawnFileRow.addWidget(self.saveAsSpawnFileButton)


        self.spawnsPageLayout.addLayout(self.spawnFileRow)

        self.placeSpawnButton = QPushButton(self.spawnsPage)
        self.placeSpawnButton.setObjectName(u"placeSpawnButton")
        self.placeSpawnButton.setCheckable(True)

        self.spawnsPageLayout.addWidget(self.placeSpawnButton)

        self.spawnGroup = QGroupBox(self.spawnsPage)
        self.spawnGroup.setObjectName(u"spawnGroup")
        self.spawnForm = QFormLayout(self.spawnGroup)
        self.spawnForm.setObjectName(u"spawnForm")
        self.spawnItemLabel = QLabel(self.spawnGroup)
        self.spawnItemLabel.setObjectName(u"spawnItemLabel")

        self.spawnForm.setWidget(0, QFormLayout.LabelRole, self.spawnItemLabel)

        self.spawnItemRow = QHBoxLayout()
        self.spawnItemRow.setObjectName(u"spawnItemRow")
        self.spawnItemEdit = QLineEdit(self.spawnGroup)
        self.spawnItemEdit.setObjectName(u"spawnItemEdit")
        self.spawnItemEdit.setReadOnly(True)

        self.spawnItemRow.addWidget(self.spawnItemEdit)

        self.chooseItemButton = QPushButton(self.spawnGroup)
        self.chooseItemButton.setObjectName(u"chooseItemButton")

        self.spawnItemRow.addWidget(self.chooseItemButton)


        self.spawnForm.setLayout(0, QFormLayout.FieldRole, self.spawnItemRow)

        self.spawnCountLabel = QLabel(self.spawnGroup)
        self.spawnCountLabel.setObjectName(u"spawnCountLabel")

        self.spawnForm.setWidget(1, QFormLayout.LabelRole, self.spawnCountLabel)

        self.spawnCountSpin = QSpinBox(self.spawnGroup)
        self.spawnCountSpin.setObjectName(u"spawnCountSpin")
        self.spawnCountSpin.setMinimum(1)
        self.spawnCountSpin.setMaximum(1000000)

        self.spawnForm.setWidget(1, QFormLayout.FieldRole, self.spawnCountSpin)

        self.spawnIdLabel = QLabel(self.spawnGroup)
        self.spawnIdLabel.setObjectName(u"spawnIdLabel")

        self.spawnForm.setWidget(2, QFormLayout.LabelRole, self.spawnIdLabel)

        self.spawnIdEdit = QLineEdit(self.spawnGroup)
        self.spawnIdEdit.setObjectName(u"spawnIdEdit")

        self.spawnForm.setWidget(2, QFormLayout.FieldRole, self.spawnIdEdit)

        self.spawnPositionLabel = QLabel(self.spawnGroup)
        self.spawnPositionLabel.setObjectName(u"spawnPositionLabel")

        self.spawnForm.setWidget(3, QFormLayout.LabelRole, self.spawnPositionLabel)

        self.spawnPositionRow = QHBoxLayout()
        self.spawnPositionRow.setObjectName(u"spawnPositionRow")
        self.spawnXSpin = QDoubleSpinBox(self.spawnGroup)
        self.spawnXSpin.setObjectName(u"spawnXSpin")
        self.spawnXSpin.setDecimals(3)
        self.spawnXSpin.setMinimum(-5000.000000000000000)
        self.spawnXSpin.setMaximum(5000.000000000000000)
        self.spawnXSpin.setSingleStep(0.050000000000000)

        self.spawnPositionRow.addWidget(self.spawnXSpin)

        self.spawnYSpin = QDoubleSpinBox(self.spawnGroup)
        self.spawnYSpin.setObjectName(u"spawnYSpin")
        self.spawnYSpin.setDecimals(3)
        self.spawnYSpin.setMinimum(-5000.000000000000000)
        self.spawnYSpin.setMaximum(5000.000000000000000)
        self.spawnYSpin.setSingleStep(0.050000000000000)

        self.spawnPositionRow.addWidget(self.spawnYSpin)

        self.spawnZSpin = QDoubleSpinBox(self.spawnGroup)
        self.spawnZSpin.setObjectName(u"spawnZSpin")
        self.spawnZSpin.setDecimals(3)
        self.spawnZSpin.setMinimum(-5000.000000000000000)
        self.spawnZSpin.setMaximum(5000.000000000000000)
        self.spawnZSpin.setSingleStep(0.050000000000000)

        self.spawnPositionRow.addWidget(self.spawnZSpin)


        self.spawnForm.setLayout(3, QFormLayout.FieldRole, self.spawnPositionRow)

        self.spawnYawLabel = QLabel(self.spawnGroup)
        self.spawnYawLabel.setObjectName(u"spawnYawLabel")

        self.spawnForm.setWidget(4, QFormLayout.LabelRole, self.spawnYawLabel)

        self.spawnYawSpin = QDoubleSpinBox(self.spawnGroup)
        self.spawnYawSpin.setObjectName(u"spawnYawSpin")
        self.spawnYawSpin.setDecimals(1)
        self.spawnYawSpin.setMinimum(0.000000000000000)
        self.spawnYawSpin.setMaximum(360.000000000000000)
        self.spawnYawSpin.setSingleStep(5.000000000000000)
        self.spawnYawSpin.setWrapping(True)

        self.spawnForm.setWidget(4, QFormLayout.FieldRole, self.spawnYawSpin)

        self.spawnChanceLabel = QLabel(self.spawnGroup)
        self.spawnChanceLabel.setObjectName(u"spawnChanceLabel")

        self.spawnForm.setWidget(5, QFormLayout.LabelRole, self.spawnChanceLabel)

        self.spawnChanceRow = QHBoxLayout()
        self.spawnChanceRow.setObjectName(u"spawnChanceRow")
        self.spawnAlwaysBox = QCheckBox(self.spawnGroup)
        self.spawnAlwaysBox.setObjectName(u"spawnAlwaysBox")

        self.spawnChanceRow.addWidget(self.spawnAlwaysBox)

        self.spawnChanceSpin = QDoubleSpinBox(self.spawnGroup)
        self.spawnChanceSpin.setObjectName(u"spawnChanceSpin")
        self.spawnChanceSpin.setDecimals(3)
        self.spawnChanceSpin.setMinimum(0.000000000000000)
        self.spawnChanceSpin.setMaximum(1.000000000000000)
        self.spawnChanceSpin.setSingleStep(0.050000000000000)

        self.spawnChanceRow.addWidget(self.spawnChanceSpin)


        self.spawnForm.setLayout(5, QFormLayout.FieldRole, self.spawnChanceRow)

        self.spawnOptionsRow = QHBoxLayout()
        self.spawnOptionsRow.setObjectName(u"spawnOptionsRow")
        self.spawnGravityBox = QCheckBox(self.spawnGroup)
        self.spawnGravityBox.setObjectName(u"spawnGravityBox")

        self.spawnOptionsRow.addWidget(self.spawnGravityBox)

        self.spawnRandomBox = QCheckBox(self.spawnGroup)
        self.spawnRandomBox.setObjectName(u"spawnRandomBox")

        self.spawnOptionsRow.addWidget(self.spawnRandomBox)


        self.spawnForm.setLayout(6, QFormLayout.SpanningRole, self.spawnOptionsRow)

        self.spawnButtonsRow = QHBoxLayout()
        self.spawnButtonsRow.setObjectName(u"spawnButtonsRow")
        self.spawnFloorButton = QPushButton(self.spawnGroup)
        self.spawnFloorButton.setObjectName(u"spawnFloorButton")

        self.spawnButtonsRow.addWidget(self.spawnFloorButton)

        self.spawnLookButton = QPushButton(self.spawnGroup)
        self.spawnLookButton.setObjectName(u"spawnLookButton")

        self.spawnButtonsRow.addWidget(self.spawnLookButton)


        self.spawnForm.setLayout(7, QFormLayout.SpanningRole, self.spawnButtonsRow)

        self.spawnButtonsRow2 = QHBoxLayout()
        self.spawnButtonsRow2.setObjectName(u"spawnButtonsRow2")
        self.copySpawnButton = QPushButton(self.spawnGroup)
        self.copySpawnButton.setObjectName(u"copySpawnButton")

        self.spawnButtonsRow2.addWidget(self.copySpawnButton)

        self.deleteSpawnButton = QPushButton(self.spawnGroup)
        self.deleteSpawnButton.setObjectName(u"deleteSpawnButton")

        self.spawnButtonsRow2.addWidget(self.deleteSpawnButton)


        self.spawnForm.setLayout(8, QFormLayout.SpanningRole, self.spawnButtonsRow2)


        self.spawnsPageLayout.addWidget(self.spawnGroup)

        self.spawnsPageSpacer = QSpacerItem(10, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.spawnsPageLayout.addItem(self.spawnsPageSpacer)

        self.editTabs.addTab(self.spawnsPage, "")

        self.rightLayout.addWidget(self.editTabs)

        self.checksLabel = QLabel(self.rightPanel)
        self.checksLabel.setObjectName(u"checksLabel")

        self.rightLayout.addWidget(self.checksLabel)

        self.checksList = QListWidget(self.rightPanel)
        self.checksList.setObjectName(u"checksList")
        self.checksList.setWordWrap(True)

        self.rightLayout.addWidget(self.checksList)

        self.hintLabel = QLabel(self.rightPanel)
        self.hintLabel.setObjectName(u"hintLabel")
        self.hintLabel.setWordWrap(True)

        self.rightLayout.addWidget(self.hintLabel)

        self.splitter.addWidget(self.rightPanel)

        self.verticalLayout.addWidget(self.splitter)

        self.statusLabel = QLabel(ZonesForm)
        self.statusLabel.setObjectName(u"statusLabel")
        self.statusLabel.setWordWrap(True)

        self.verticalLayout.addWidget(self.statusLabel)

        self.verticalLayout.setStretch(3, 1)
        QWidget.setTabOrder(self.mapBox, self.search)
        QWidget.setTabOrder(self.search, self.zoneFilter)
        QWidget.setTabOrder(self.zoneFilter, self.zoneList)
        QWidget.setTabOrder(self.zoneList, self.idEdit)
        QWidget.setTabOrder(self.idEdit, self.nameEdit)
        QWidget.setTabOrder(self.nameEdit, self.kindBox)
        QWidget.setTabOrder(self.kindBox, self.xSpin)
        QWidget.setTabOrder(self.xSpin, self.ySpin)
        QWidget.setTabOrder(self.ySpin, self.zSpin)
        QWidget.setTabOrder(self.zSpin, self.widthSpin)
        QWidget.setTabOrder(self.widthSpin, self.heightSpin)
        QWidget.setTabOrder(self.heightSpin, self.depthSpin)
        QWidget.setTabOrder(self.depthSpin, self.yawSpin)
        QWidget.setTabOrder(self.yawSpin, self.chooseItemButton)
        QWidget.setTabOrder(self.chooseItemButton, self.spawnCountSpin)
        QWidget.setTabOrder(self.spawnCountSpin, self.spawnIdEdit)
        QWidget.setTabOrder(self.spawnIdEdit, self.spawnXSpin)
        QWidget.setTabOrder(self.spawnXSpin, self.spawnYSpin)
        QWidget.setTabOrder(self.spawnYSpin, self.spawnZSpin)
        QWidget.setTabOrder(self.spawnZSpin, self.spawnYawSpin)
        QWidget.setTabOrder(self.spawnYawSpin, self.spawnAlwaysBox)
        QWidget.setTabOrder(self.spawnAlwaysBox, self.spawnChanceSpin)

        self.retranslateUi(ZonesForm)

        QMetaObject.connectSlotsByName(ZonesForm)
    # setupUi

    def retranslateUi(self, ZonesForm):
        self.mapLabel.setText(QCoreApplication.translate("ZonesForm", u"Map", None))
#if QT_CONFIG(tooltip)
        self.mapBox.setToolTip(QCoreApplication.translate("ZonesForm", u"The map to show (the maps imported from the game)", None))
#endif // QT_CONFIG(tooltip)
        self.search.setPlaceholderText(QCoreApplication.translate("ZonesForm", u"Find a place, building, object or zone on this map (Enter)", None))
#if QT_CONFIG(tooltip)
        self.topDownButton.setToolTip(QCoreApplication.translate("ZonesForm", u"Look straight down, as on a map (T)", None))
#endif // QT_CONFIG(tooltip)
        self.topDownButton.setText(QCoreApplication.translate("ZonesForm", u"Top-down", None))
#if QT_CONFIG(tooltip)
        self.wholeMapButton.setToolTip(QCoreApplication.translate("ZonesForm", u"Show the whole map", None))
#endif // QT_CONFIG(tooltip)
        self.wholeMapButton.setText(QCoreApplication.translate("ZonesForm", u"Whole map", None))
#if QT_CONFIG(tooltip)
        self.importButton.setToolTip(QCoreApplication.translate("ZonesForm", u"Read the maps from the game's own files (takes a few minutes; nothing in the game is changed)", None))
#endif // QT_CONFIG(tooltip)
        self.importButton.setText(QCoreApplication.translate("ZonesForm", u"Import the game's maps...", None))
        self.versionLabel.setText("")
        self.showLabel.setText(QCoreApplication.translate("ZonesForm", u"Show", None))
#if QT_CONFIG(tooltip)
        self.floorBox.setToolTip(QCoreApplication.translate("ZonesForm", u"The floor bots walk on (the game's navigation mesh), coloured by height", None))
#endif // QT_CONFIG(tooltip)
        self.floorBox.setText(QCoreApplication.translate("ZonesForm", u"Floor", None))
#if QT_CONFIG(tooltip)
        self.wallsBox.setToolTip(QCoreApplication.translate("ZonesForm", u"The walls, floors and stairs players bump into (imported with the maps' walls)", None))
#endif // QT_CONFIG(tooltip)
        self.wallsBox.setText(QCoreApplication.translate("ZonesForm", u"Walls", None))
#if QT_CONFIG(tooltip)
        self.gameZonesBox.setToolTip(QCoreApplication.translate("ZonesForm", u"The game's own quest zones", None))
#endif // QT_CONFIG(tooltip)
        self.gameZonesBox.setText(QCoreApplication.translate("ZonesForm", u"Game zones", None))
#if QT_CONFIG(tooltip)
        self.referenceZonesBox.setToolTip(QCoreApplication.translate("ZonesForm", u"The zones in the quest zone files among your reference files", None))
#endif // QT_CONFIG(tooltip)
        self.referenceZonesBox.setText(QCoreApplication.translate("ZonesForm", u"Reference zones", None))
#if QT_CONFIG(tooltip)
        self.spawnsBox.setToolTip(QCoreApplication.translate("ZonesForm", u"Item spawns: yours, and those in the item spawn files among your reference files", None))
#endif // QT_CONFIG(tooltip)
        self.spawnsBox.setText(QCoreApplication.translate("ZonesForm", u"Item spawns", None))
#if QT_CONFIG(tooltip)
        self.areasBox.setToolTip(QCoreApplication.translate("ZonesForm", u"The parts the map is made of (each a scene of the game), outlined", None))
#endif // QT_CONFIG(tooltip)
        self.areasBox.setText(QCoreApplication.translate("ZonesForm", u"Areas", None))
#if QT_CONFIG(tooltip)
        self.labelsBox.setToolTip(QCoreApplication.translate("ZonesForm", u"The zones' ids over them", None))
#endif // QT_CONFIG(tooltip)
        self.labelsBox.setText(QCoreApplication.translate("ZonesForm", u"Names", None))
#if QT_CONFIG(tooltip)
        self.buildingButton.setToolTip(QCoreApplication.translate("ZonesForm", u"Find the building in the middle of the view: its outline, and its storeys to hide the ones above", None))
#endif // QT_CONFIG(tooltip)
        self.buildingButton.setText(QCoreApplication.translate("ZonesForm", u"Building here", None))
#if QT_CONFIG(tooltip)
        self.storeyBox.setToolTip(QCoreApplication.translate("ZonesForm", u"Show one storey of the building found (and hide the ones above it)", None))
#endif // QT_CONFIG(tooltip)
        self.zoneFilter.setPlaceholderText(QCoreApplication.translate("ZonesForm", u"Filter the zones and spawns", None))
        ___qtreewidgetitem = self.zoneList.headerItem()
        ___qtreewidgetitem.setText(2, QCoreApplication.translate("ZonesForm", u"From", None));
        ___qtreewidgetitem.setText(1, QCoreApplication.translate("ZonesForm", u"Kind", None));
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("ZonesForm", u"Zone or item", None));
#if QT_CONFIG(tooltip)
        self.fileLabel.setToolTip(QCoreApplication.translate("ZonesForm", u"The quest zone file (WTT-CommonLib's CustomQuestZones) your zones are in", None))
#endif // QT_CONFIG(tooltip)
        self.fileLabel.setText(QCoreApplication.translate("ZonesForm", u"Zone file: none", None))
#if QT_CONFIG(tooltip)
        self.newFileButton.setToolTip(QCoreApplication.translate("ZonesForm", u"Start an empty zone file", None))
#endif // QT_CONFIG(tooltip)
        self.newFileButton.setText(QCoreApplication.translate("ZonesForm", u"New", None))
#if QT_CONFIG(tooltip)
        self.openFileButton.setToolTip(QCoreApplication.translate("ZonesForm", u"Open a quest zone file to change its zones", None))
#endif // QT_CONFIG(tooltip)
        self.openFileButton.setText(QCoreApplication.translate("ZonesForm", u"Open...", None))
        self.saveFileButton.setText(QCoreApplication.translate("ZonesForm", u"Save", None))
        self.saveAsFileButton.setText(QCoreApplication.translate("ZonesForm", u"Save as...", None))
#if QT_CONFIG(tooltip)
        self.placeButton.setToolTip(QCoreApplication.translate("ZonesForm", u"Then click the floor where the new zone goes (Esc to stop)", None))
#endif // QT_CONFIG(tooltip)
        self.placeButton.setText(QCoreApplication.translate("ZonesForm", u"Place a new zone", None))
        self.zoneGroup.setTitle(QCoreApplication.translate("ZonesForm", u"Zone", None))
        self.idLabel.setText(QCoreApplication.translate("ZonesForm", u"Id", None))
#if QT_CONFIG(tooltip)
        self.idEdit.setToolTip(QCoreApplication.translate("ZonesForm", u"ZoneId: what quest conditions name the zone by", None))
#endif // QT_CONFIG(tooltip)
        self.nameLabel.setText(QCoreApplication.translate("ZonesForm", u"Name", None))
#if QT_CONFIG(tooltip)
        self.nameEdit.setToolTip(QCoreApplication.translate("ZonesForm", u"ZoneName (only for you to tell zones apart)", None))
#endif // QT_CONFIG(tooltip)
        self.kindLabel.setText(QCoreApplication.translate("ZonesForm", u"Kind", None))
#if QT_CONFIG(tooltip)
        self.kindBox.setToolTip(QCoreApplication.translate("ZonesForm", u"What the zone is for: visit (Visit zone, Inside zone), placeitem (Place marker, Leave items), botkillzone (Inside zone, kills in a zone), flarezone (Launch a flare), salvage", None))
#endif // QT_CONFIG(tooltip)
        self.positionLabel.setText(QCoreApplication.translate("ZonesForm", u"Middle (x, y, z)", None))
#if QT_CONFIG(tooltip)
        self.xSpin.setToolTip(QCoreApplication.translate("ZonesForm", u"East (metres)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.ySpin.setToolTip(QCoreApplication.translate("ZonesForm", u"Up (metres)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.zSpin.setToolTip(QCoreApplication.translate("ZonesForm", u"North (metres)", None))
#endif // QT_CONFIG(tooltip)
        self.sizeLabel.setText(QCoreApplication.translate("ZonesForm", u"Size (w, h, d)", None))
#if QT_CONFIG(tooltip)
        self.widthSpin.setToolTip(QCoreApplication.translate("ZonesForm", u"Width (metres, across before turning)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.heightSpin.setToolTip(QCoreApplication.translate("ZonesForm", u"Height (metres)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.depthSpin.setToolTip(QCoreApplication.translate("ZonesForm", u"Depth (metres, north to south before turning)", None))
#endif // QT_CONFIG(tooltip)
        self.yawLabel.setText(QCoreApplication.translate("ZonesForm", u"Turned", None))
#if QT_CONFIG(tooltip)
        self.yawSpin.setToolTip(QCoreApplication.translate("ZonesForm", u"Degrees clockwise, seen from above", None))
#endif // QT_CONFIG(tooltip)
        self.yawSpin.setSuffix(QCoreApplication.translate("ZonesForm", u"\u00b0", None))
#if QT_CONFIG(tooltip)
        self.floorButton.setToolTip(QCoreApplication.translate("ZonesForm", u"Put its bottom just under the floor it is over", None))
#endif // QT_CONFIG(tooltip)
        self.floorButton.setText(QCoreApplication.translate("ZonesForm", u"Sit on floor", None))
#if QT_CONFIG(tooltip)
        self.slopeButton.setToolTip(QCoreApplication.translate("ZonesForm", u"For stairs or a ramp: reach down to the lowest floor of the walk under it", None))
#endif // QT_CONFIG(tooltip)
        self.slopeButton.setText(QCoreApplication.translate("ZonesForm", u"Cover the slope", None))
#if QT_CONFIG(tooltip)
        self.lookButton.setToolTip(QCoreApplication.translate("ZonesForm", u"Bring it into view (F)", None))
#endif // QT_CONFIG(tooltip)
        self.lookButton.setText(QCoreApplication.translate("ZonesForm", u"Look at it", None))
#if QT_CONFIG(tooltip)
        self.copyButton.setToolTip(QCoreApplication.translate("ZonesForm", u"Add a copy of this zone to your zone file, to change", None))
#endif // QT_CONFIG(tooltip)
        self.copyButton.setText(QCoreApplication.translate("ZonesForm", u"Copy as a new zone", None))
#if QT_CONFIG(tooltip)
        self.deleteButton.setToolTip(QCoreApplication.translate("ZonesForm", u"Take this zone out of your zone file (Delete)", None))
#endif // QT_CONFIG(tooltip)
        self.deleteButton.setText(QCoreApplication.translate("ZonesForm", u"Delete", None))
        self.editTabs.setTabText(self.editTabs.indexOf(self.zonesPage), QCoreApplication.translate("ZonesForm", u"Zones", None))
#if QT_CONFIG(tooltip)
        self.spawnFileLabel.setToolTip(QCoreApplication.translate("ZonesForm", u"The item spawn file (WTT-CommonLib's CustomLootspawns) your spawns are in. Its folder says what they are: CustomSpawnpointsForced spawns every raid (as quest items do), CustomSpawnpoints is loose loot", None))
#endif // QT_CONFIG(tooltip)
        self.spawnFileLabel.setText(QCoreApplication.translate("ZonesForm", u"Spawn file: none", None))
#if QT_CONFIG(tooltip)
        self.newSpawnFileButton.setToolTip(QCoreApplication.translate("ZonesForm", u"Start an empty item spawn file", None))
#endif // QT_CONFIG(tooltip)
        self.newSpawnFileButton.setText(QCoreApplication.translate("ZonesForm", u"New", None))
#if QT_CONFIG(tooltip)
        self.openSpawnFileButton.setToolTip(QCoreApplication.translate("ZonesForm", u"Open an item spawn file to change its spawns", None))
#endif // QT_CONFIG(tooltip)
        self.openSpawnFileButton.setText(QCoreApplication.translate("ZonesForm", u"Open...", None))
        self.saveSpawnFileButton.setText(QCoreApplication.translate("ZonesForm", u"Save", None))
        self.saveAsSpawnFileButton.setText(QCoreApplication.translate("ZonesForm", u"Save as...", None))
#if QT_CONFIG(tooltip)
        self.placeSpawnButton.setToolTip(QCoreApplication.translate("ZonesForm", u"Then click where the item goes (Esc to stop). It is the item last placed; the first time, you choose it", None))
#endif // QT_CONFIG(tooltip)
        self.placeSpawnButton.setText(QCoreApplication.translate("ZonesForm", u"Place a new item spawn", None))
        self.spawnGroup.setTitle(QCoreApplication.translate("ZonesForm", u"Item spawn", None))
        self.spawnItemLabel.setText(QCoreApplication.translate("ZonesForm", u"Item", None))
#if QT_CONFIG(tooltip)
        self.spawnItemEdit.setToolTip(QCoreApplication.translate("ZonesForm", u"The item that spawns", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.chooseItemButton.setToolTip(QCoreApplication.translate("ZonesForm", u"Choose the item: the game's, or a custom item in your reference files", None))
#endif // QT_CONFIG(tooltip)
        self.chooseItemButton.setText(QCoreApplication.translate("ZonesForm", u"Choose...", None))
        self.spawnCountLabel.setText(QCoreApplication.translate("ZonesForm", u"Count", None))
#if QT_CONFIG(tooltip)
        self.spawnCountSpin.setToolTip(QCoreApplication.translate("ZonesForm", u"How many in its stack (money and ammo get a random stack from the server instead)", None))
#endif // QT_CONFIG(tooltip)
        self.spawnIdLabel.setText(QCoreApplication.translate("ZonesForm", u"Id", None))
#if QT_CONFIG(tooltip)
        self.spawnIdEdit.setToolTip(QCoreApplication.translate("ZonesForm", u"The spawn's template Id. Spawns that come every raid and share an Id are alternatives: the server spawns one of them each raid", None))
#endif // QT_CONFIG(tooltip)
        self.spawnPositionLabel.setText(QCoreApplication.translate("ZonesForm", u"Position (x, y, z)", None))
#if QT_CONFIG(tooltip)
        self.spawnXSpin.setToolTip(QCoreApplication.translate("ZonesForm", u"East (metres)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.spawnYSpin.setToolTip(QCoreApplication.translate("ZonesForm", u"Up (metres)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.spawnZSpin.setToolTip(QCoreApplication.translate("ZonesForm", u"North (metres)", None))
#endif // QT_CONFIG(tooltip)
        self.spawnYawLabel.setText(QCoreApplication.translate("ZonesForm", u"Turned", None))
#if QT_CONFIG(tooltip)
        self.spawnYawSpin.setToolTip(QCoreApplication.translate("ZonesForm", u"Degrees clockwise, seen from above (its y rotation)", None))
#endif // QT_CONFIG(tooltip)
        self.spawnYawSpin.setSuffix(QCoreApplication.translate("ZonesForm", u"\u00b0", None))
        self.spawnChanceLabel.setText(QCoreApplication.translate("ZonesForm", u"Spawns", None))
#if QT_CONFIG(tooltip)
        self.spawnAlwaysBox.setToolTip(QCoreApplication.translate("ZonesForm", u"IsAlwaysSpawn: it spawns every raid. A forced file's spawns always do", None))
#endif // QT_CONFIG(tooltip)
        self.spawnAlwaysBox.setText(QCoreApplication.translate("ZonesForm", u"Every raid", None))
#if QT_CONFIG(tooltip)
        self.spawnChanceSpin.setToolTip(QCoreApplication.translate("ZonesForm", u"Its probability. Loose loot: its weight against the map's own loose loot points (1: every raid). Spawns every raid that share an Id: how likely this one is the one that spawns", None))
#endif // QT_CONFIG(tooltip)
        self.spawnChanceSpin.setPrefix(QCoreApplication.translate("ZonesForm", u"chance ", None))
#if QT_CONFIG(tooltip)
        self.spawnGravityBox.setToolTip(QCoreApplication.translate("ZonesForm", u"useGravity: it falls onto what is under it when the raid starts. Off: it stays where it is put", None))
#endif // QT_CONFIG(tooltip)
        self.spawnGravityBox.setText(QCoreApplication.translate("ZonesForm", u"Falls into place", None))
#if QT_CONFIG(tooltip)
        self.spawnRandomBox.setToolTip(QCoreApplication.translate("ZonesForm", u"randomRotation: it is turned at random", None))
#endif // QT_CONFIG(tooltip)
        self.spawnRandomBox.setText(QCoreApplication.translate("ZonesForm", u"Random turn", None))
#if QT_CONFIG(tooltip)
        self.spawnFloorButton.setToolTip(QCoreApplication.translate("ZonesForm", u"Put it on the floor, or the top of what is under it (a table, a shelf)", None))
#endif // QT_CONFIG(tooltip)
        self.spawnFloorButton.setText(QCoreApplication.translate("ZonesForm", u"Put on floor", None))
#if QT_CONFIG(tooltip)
        self.spawnLookButton.setToolTip(QCoreApplication.translate("ZonesForm", u"Bring it into view (F)", None))
#endif // QT_CONFIG(tooltip)
        self.spawnLookButton.setText(QCoreApplication.translate("ZonesForm", u"Look at it", None))
#if QT_CONFIG(tooltip)
        self.copySpawnButton.setToolTip(QCoreApplication.translate("ZonesForm", u"Add a copy of this spawn to your spawn file, to change", None))
#endif // QT_CONFIG(tooltip)
        self.copySpawnButton.setText(QCoreApplication.translate("ZonesForm", u"Copy as a new spawn", None))
#if QT_CONFIG(tooltip)
        self.deleteSpawnButton.setToolTip(QCoreApplication.translate("ZonesForm", u"Take this spawn out of your spawn file (Delete)", None))
#endif // QT_CONFIG(tooltip)
        self.deleteSpawnButton.setText(QCoreApplication.translate("ZonesForm", u"Delete", None))
        self.editTabs.setTabText(self.editTabs.indexOf(self.spawnsPage), QCoreApplication.translate("ZonesForm", u"Item spawns", None))
        self.checksLabel.setText(QCoreApplication.translate("ZonesForm", u"Checks", None))
        self.hintLabel.setText(QCoreApplication.translate("ZonesForm", u"Drag the zone to move it. Its handles size it (squares), lift it (arrow) and turn it (circle); Shift snaps. Left-drag turns the view, right-drag moves it, the wheel zooms.", None))
        self.statusLabel.setText("")
        pass
    # retranslateUi

