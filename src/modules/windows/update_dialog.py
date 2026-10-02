from PySide6 import QtCore
from PySide6.QtWidgets import QDialog

from modules.gui.compiled.gui_updates import Ui_UpdateMenu
from modules.windows.common import fill_placeholders


class Gui_UpdatesDlg(QDialog):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.ui = Ui_UpdateMenu()
		self.ui.setupUi(self)

	def updateVersion(self, ver_current, ver_latest, url_text, update_text):
		text = fill_placeholders(
			self.ui.label.text(),
			{
				"V_CUR": ver_current,
				"V_LAT": ver_latest,
				"UPDATE_TEXT": update_text,
				"SRC_URL": url_text,
			},
		)
		self.ui.label.setText(QtCore.QCoreApplication.translate("UpdateMenu", text))
