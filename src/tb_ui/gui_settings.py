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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QFormLayout, QGroupBox, QLabel, QLineEdit,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_SettingsMenu(object):
    def setupUi(self, SettingsMenu):
        if not SettingsMenu.objectName():
            SettingsMenu.setObjectName(u"SettingsMenu")
        SettingsMenu.resize(560, 360)
        SettingsMenu.setMinimumSize(QSize(480, 340))
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
        self.lbl_error.setText("")
    # retranslateUi

