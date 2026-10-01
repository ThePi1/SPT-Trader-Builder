import re

from PySide6 import QtCore
from PySide6.QtWidgets import QDialog

from tb_ui.gui_updates import Ui_UpdateMenu


class Gui_UpdatesDlg(QDialog):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.ui = Ui_UpdateMenu()
		self.ui.setupUi(self)

	def updateVersion(self, ver_current, ver_latest, url_text, update_text):
		text = self.ui.label.text()
		text = re.sub("V_CUR", ver_current, text)
		text = re.sub("V_LAT", ver_latest, text)
		text = re.sub("UPDATE_TEXT", update_text, text)
		text = re.sub("SRC_URL", url_text, text)
		self.ui.label.setText(QtCore.QCoreApplication.translate("UpdateMenu", text))
