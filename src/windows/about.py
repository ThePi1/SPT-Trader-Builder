import re

from PySide6 import QtCore
from PySide6.QtWidgets import QDialog

from tb_ui.gui_about import Ui_AboutMenu


class Gui_AboutDlg(QDialog):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.ui = Ui_AboutMenu()
		self.ui.setupUi(self)

	def updateAbout(self, ver_current, url_text):
		text = self.ui.label.text()
		text = re.sub("V_CUR", ver_current, text)
		text = re.sub("SRC_URL", url_text, text)
		self.ui.label.setText(QtCore.QCoreApplication.translate("AboutMenu", text))
