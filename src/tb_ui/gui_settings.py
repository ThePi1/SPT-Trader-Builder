# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'gui_settings.ui'
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
    QDialogButtonBox, QFormLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_SettingsMenu(object):
    def setupUi(self, SettingsMenu):
        if not SettingsMenu.objectName():
            SettingsMenu.setObjectName(u"SettingsMenu")
        SettingsMenu.resize(560, 520)
        SettingsMenu.setMinimumSize(QSize(480, 470))
        icon = QIcon()
        icon.addFile(u"data/icon.ico", QSize(), QIcon.Normal, QIcon.Off)
        SettingsMenu.setWindowIcon(icon)
        self.verticalLayout = QVBoxLayout(SettingsMenu)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.lbl_intro = QLabel(SettingsMenu)
        self.lbl_intro.setObjectName(u"lbl_intro")
        self.lbl_intro.setWordWrap(True)

        self.verticalLayout.addWidget(self.lbl_intro)

        self.grp_updates = QGroupBox(SettingsMenu)
        self.grp_updates.setObjectName(u"grp_updates")
        self.form_updates = QFormLayout(self.grp_updates)
        self.form_updates.setObjectName(u"form_updates")
        self.lbl_version_file = QLabel(self.grp_updates)
        self.lbl_version_file.setObjectName(u"lbl_version_file")

        self.form_updates.setWidget(0, QFormLayout.LabelRole, self.lbl_version_file)

        self.fld_version_file = QLineEdit(self.grp_updates)
        self.fld_version_file.setObjectName(u"fld_version_file")

        self.form_updates.setWidget(0, QFormLayout.FieldRole, self.fld_version_file)

        self.lbl_version_url = QLabel(self.grp_updates)
        self.lbl_version_url.setObjectName(u"lbl_version_url")

        self.form_updates.setWidget(1, QFormLayout.LabelRole, self.lbl_version_url)

        self.fld_version_url = QLineEdit(self.grp_updates)
        self.fld_version_url.setObjectName(u"fld_version_url")

        self.form_updates.setWidget(1, QFormLayout.FieldRole, self.fld_version_url)

        self.lbl_project_url = QLabel(self.grp_updates)
        self.lbl_project_url.setObjectName(u"lbl_project_url")

        self.form_updates.setWidget(2, QFormLayout.LabelRole, self.lbl_project_url)

        self.fld_project_url = QLineEdit(self.grp_updates)
        self.fld_project_url.setObjectName(u"fld_project_url")

        self.form_updates.setWidget(2, QFormLayout.FieldRole, self.fld_project_url)


        self.verticalLayout.addWidget(self.grp_updates)

        self.grp_defaults = QGroupBox(SettingsMenu)
        self.grp_defaults.setObjectName(u"grp_defaults")
        self.form_defaults = QFormLayout(self.grp_defaults)
        self.form_defaults.setObjectName(u"form_defaults")
        self.lbl_default_questicon = QLabel(self.grp_defaults)
        self.lbl_default_questicon.setObjectName(u"lbl_default_questicon")

        self.form_defaults.setWidget(0, QFormLayout.LabelRole, self.lbl_default_questicon)

        self.fld_default_questicon = QLineEdit(self.grp_defaults)
        self.fld_default_questicon.setObjectName(u"fld_default_questicon")

        self.form_defaults.setWidget(0, QFormLayout.FieldRole, self.fld_default_questicon)


        self.verticalLayout.addWidget(self.grp_defaults)

        self.grp_items = QGroupBox(SettingsMenu)
        self.grp_items.setObjectName(u"grp_items")
        self.verticalLayout_items = QVBoxLayout(self.grp_items)
        self.verticalLayout_items.setObjectName(u"verticalLayout_items")
        self.lbl_items_help = QLabel(self.grp_items)
        self.lbl_items_help.setObjectName(u"lbl_items_help")
        self.lbl_items_help.setWordWrap(True)

        self.verticalLayout_items.addWidget(self.lbl_items_help)

        self.horizontalLayout_items_file = QHBoxLayout()
        self.horizontalLayout_items_file.setObjectName(u"horizontalLayout_items_file")
        self.fld_items_file = QLineEdit(self.grp_items)
        self.fld_items_file.setObjectName(u"fld_items_file")
        self.fld_items_file.setReadOnly(True)

        self.horizontalLayout_items_file.addWidget(self.fld_items_file)

        self.pb_load_items = QPushButton(self.grp_items)
        self.pb_load_items.setObjectName(u"pb_load_items")

        self.horizontalLayout_items_file.addWidget(self.pb_load_items)

        self.pb_default_items = QPushButton(self.grp_items)
        self.pb_default_items.setObjectName(u"pb_default_items")

        self.horizontalLayout_items_file.addWidget(self.pb_default_items)


        self.verticalLayout_items.addLayout(self.horizontalLayout_items_file)

        self.lbl_items_status = QLabel(self.grp_items)
        self.lbl_items_status.setObjectName(u"lbl_items_status")
        self.lbl_items_status.setWordWrap(True)

        self.verticalLayout_items.addWidget(self.lbl_items_status)


        self.verticalLayout.addWidget(self.grp_items)

        self.grp_logging = QGroupBox(SettingsMenu)
        self.grp_logging.setObjectName(u"grp_logging")
        self.verticalLayout_logging = QVBoxLayout(self.grp_logging)
        self.verticalLayout_logging.setObjectName(u"verticalLayout_logging")
        self.chk_debug_logging = QCheckBox(self.grp_logging)
        self.chk_debug_logging.setObjectName(u"chk_debug_logging")

        self.verticalLayout_logging.addWidget(self.chk_debug_logging)

        self.lbl_debug_logging_help = QLabel(self.grp_logging)
        self.lbl_debug_logging_help.setObjectName(u"lbl_debug_logging_help")
        self.lbl_debug_logging_help.setWordWrap(True)

        self.verticalLayout_logging.addWidget(self.lbl_debug_logging_help)


        self.verticalLayout.addWidget(self.grp_logging)

        self.lbl_error = QLabel(SettingsMenu)
        self.lbl_error.setObjectName(u"lbl_error")
        self.lbl_error.setStyleSheet(u"color: #c00000;")
        self.lbl_error.setWordWrap(True)

        self.verticalLayout.addWidget(self.lbl_error)

        self.verticalSpacer = QSpacerItem(20, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.buttonBox = QDialogButtonBox(SettingsMenu)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Save)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(SettingsMenu)

        QMetaObject.connectSlotsByName(SettingsMenu)
    # setupUi

    def retranslateUi(self, SettingsMenu):
        SettingsMenu.setWindowTitle(QCoreApplication.translate("SettingsMenu", u"Settings", None))
        self.lbl_intro.setText(QCoreApplication.translate("SettingsMenu", u"These settings are saved to data/settings.ini.", None))
        self.grp_updates.setTitle(QCoreApplication.translate("SettingsMenu", u"Update check", None))
        self.lbl_version_file.setText(QCoreApplication.translate("SettingsMenu", u"Local version file", None))
#if QT_CONFIG(tooltip)
        self.fld_version_file.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.lbl_version_url.setText(QCoreApplication.translate("SettingsMenu", u"Latest version URL", None))
#if QT_CONFIG(tooltip)
        self.fld_version_url.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.lbl_project_url.setText(QCoreApplication.translate("SettingsMenu", u"Project URL", None))
#if QT_CONFIG(tooltip)
        self.fld_project_url.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.grp_defaults.setTitle(QCoreApplication.translate("SettingsMenu", u"Quest defaults", None))
        self.lbl_default_questicon.setText(QCoreApplication.translate("SettingsMenu", u"Default quest icon", None))
#if QT_CONFIG(tooltip)
        self.fld_default_questicon.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.grp_items.setTitle(QCoreApplication.translate("SettingsMenu", u"Item database (items.json)", None))
        self.lbl_items_help.setText(QCoreApplication.translate("SettingsMenu", u"The item database used by the ID Lookup tab and the child-item finder (Debug menu). By default it is the items.json included with the program; load a different one (say, from your SPT install) to use that instead. It is remembered next time.", None))
        self.fld_items_file.setPlaceholderText(QCoreApplication.translate("SettingsMenu", u"data/items.json", None))
#if QT_CONFIG(tooltip)
        self.fld_items_file.setToolTip(QCoreApplication.translate("SettingsMenu", u"The items.json used every time the program starts.", None))
#endif // QT_CONFIG(tooltip)
        self.pb_load_items.setText(QCoreApplication.translate("SettingsMenu", u"Load items.json...", None))
        self.pb_default_items.setText(QCoreApplication.translate("SettingsMenu", u"Use included file", None))
        self.lbl_items_status.setText(QCoreApplication.translate("SettingsMenu", u"No items.json loaded.", None))
        self.grp_logging.setTitle(QCoreApplication.translate("SettingsMenu", u"Troubleshooting", None))
        self.chk_debug_logging.setText(QCoreApplication.translate("SettingsMenu", u"Write a debug log file", None))
        self.lbl_debug_logging_help.setText(QCoreApplication.translate("SettingsMenu", u"Saves a detailed log (trader_builder.log, next to the program) that you can send along with a bug report. Off by default.", None))
        self.lbl_error.setText("")
    # retranslateUi

