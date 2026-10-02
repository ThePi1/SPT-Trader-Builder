from PySide6 import QtCore
from PySide6.QtWidgets import QDialog

from modules.gui.compiled.gui_about import Ui_AboutMenu
from modules.windows.common import fill_placeholders


class Gui_AboutDlg(QDialog):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.ui = Ui_AboutMenu()
		self.ui.setupUi(self)

	def updateAbout(self, ver_current, url_text):
		text = fill_placeholders(
			self.ui.label.text(), {"V_CUR": ver_current, "SRC_URL": url_text}
		)
		self.ui.label.setText(QtCore.QCoreApplication.translate("AboutMenu", text))
