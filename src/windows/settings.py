import logging

from PySide6.QtWidgets import QDialog

from config import SETTING_NAMES, validate_settings
from tb_ui.gui_settings import Ui_SettingsMenu

log = logging.getLogger(__name__)

# How a bad field is marked (the same look as the assort builder's required fields)
ERROR_STYLE = "border: 2px solid red; background-color: #ffe6e6;"

# Setting name -> how it's called in error messages
LABELS = {
	"version_file": "Local version file",
	"version_url": "Latest version URL",
	"project_url": "Project URL",
	"default_questicon": "Default quest icon",
}


class Gui_SettingsDlg(QDialog):
	"""Edits the values in settings.ini. Saving updates the config it was given."""

	def __init__(self, config, parent=None):
		super().__init__(parent)
		self.ui = Ui_SettingsMenu()
		self.ui.setupUi(self)
		self.config = config
		self.ui.lbl_error.setVisible(False)
		for name, value in config.settings().items():
			field = self.field(name)
			field.setText(value)
			field.setCursorPosition(0)
			# stop marking a field as bad as soon as the user edits it
			field.textEdited.connect(lambda _text, f=field: f.setStyleSheet(""))
		self.ui.buttonBox.accepted.connect(self.save)
		self.ui.buttonBox.rejected.connect(self.reject)

	def field(self, name):
		return getattr(self.ui, f"fld_{name}")

	def values(self):
		return {name: self.field(name).text().strip() for name in SETTING_NAMES}

	def save(self):
		values = self.values()
		errors = validate_settings(values)
		for name in SETTING_NAMES:
			self.field(name).setStyleSheet(ERROR_STYLE if name in errors else "")
		if errors:
			self.show_error("\n".join(f"{LABELS[name]}: {msg}" for name, msg in errors.items()))
			return
		try:
			self.config.update_settings(values)
		except OSError as e:
			log.error(f"Could not save settings: {e}")
			self.show_error(f"Could not save settings.ini:\n{e}")
			return
		log.info("Settings saved.")
		self.accept()

	def show_error(self, message):
		self.ui.lbl_error.setText(message)
		self.ui.lbl_error.setVisible(True)
