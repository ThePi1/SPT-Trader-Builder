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
    QPushButton, QSizePolicy, QSpacerItem, QSplitter,
    QToolButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout,
    QWidget)

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
        self.mapBox.setMinimumContentsLength(14)

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
        self.fileLabel = QLabel(self.rightPanel)
        self.fileLabel.setObjectName(u"fileLabel")
        self.fileLabel.setWordWrap(True)

        self.rightLayout.addWidget(self.fileLabel)

        self.fileRow = QHBoxLayout()
        self.fileRow.setObjectName(u"fileRow")
        self.newFileButton = QPushButton(self.rightPanel)
        self.newFileButton.setObjectName(u"newFileButton")

        self.fileRow.addWidget(self.newFileButton)

        self.openFileButton = QPushButton(self.rightPanel)
        self.openFileButton.setObjectName(u"openFileButton")

        self.fileRow.addWidget(self.openFileButton)

        self.saveFileButton = QPushButton(self.rightPanel)
        self.saveFileButton.setObjectName(u"saveFileButton")

        self.fileRow.addWidget(self.saveFileButton)

        self.saveAsFileButton = QPushButton(self.rightPanel)
        self.saveAsFileButton.setObjectName(u"saveAsFileButton")

        self.fileRow.addWidget(self.saveAsFileButton)


        self.rightLayout.addLayout(self.fileRow)

        self.placeButton = QPushButton(self.rightPanel)
        self.placeButton.setObjectName(u"placeButton")
        self.placeButton.setCheckable(True)

        self.rightLayout.addWidget(self.placeButton)

        self.zoneGroup = QGroupBox(self.rightPanel)
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


        self.rightLayout.addWidget(self.zoneGroup)

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
        self.zoneFilter.setPlaceholderText(QCoreApplication.translate("ZonesForm", u"Filter the zones", None))
        ___qtreewidgetitem = self.zoneList.headerItem()
        ___qtreewidgetitem.setText(2, QCoreApplication.translate("ZonesForm", u"From", None));
        ___qtreewidgetitem.setText(1, QCoreApplication.translate("ZonesForm", u"Kind", None));
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("ZonesForm", u"Zone", None));
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
        self.checksLabel.setText(QCoreApplication.translate("ZonesForm", u"Checks", None))
        self.hintLabel.setText(QCoreApplication.translate("ZonesForm", u"Drag the zone to move it. Its handles size it (squares), lift it (arrow) and turn it (circle); Shift snaps. Left-drag turns the view, right-drag moves it, the wheel zooms.", None))
        self.statusLabel.setText("")
        pass
    # retranslateUi

