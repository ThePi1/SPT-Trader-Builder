import logging

from PySide6.QtWidgets import QDialog, QFileDialog

from config import (
	BOOL_SETTING_NAMES,
	DEFAULT_ITEMS_FILE,
	SETTING_NAMES,
	resolve_items_path,
	validate_settings,
)
from state import load_items_file
from tb_ui.gui_settings import Ui_SettingsMenu
from utils import LOG_FILE
from windows.common import safe_file_dialog

log = logging.getLogger(__name__)

# How a bad field is marked (the same look as the assort builder's required fields)
ERROR_STYLE = "border: 2px solid red; background-color: #ffe6e6;"

# The settings edited in a text box (the others are tick boxes)
TEXT_SETTING_NAMES = tuple(name for name in SETTING_NAMES if name not in BOOL_SETTING_NAMES)

# Setting name -> how it's called in error messages
LABELS = {
	"debug_logging": "Debug log",
	"merge_locales_on_export": "Merge locales on export",
	"version_file": "Local version file",
	"version_url": "Latest version URL",
	"project_url": "Project URL",
	"items_file": "items.json",
	"default_questicon": "Default quest icon",
}


class Gui_SettingsDlg(QDialog):
	"""Edits the values in settings.ini. Saving updates the config it was given.

	state and apply_items connect the items.json section to the program: state holds the item
	database that is in use now, and apply_items(items, path) makes a newly chosen one the one in
	use. Without them the section is hidden.
	"""

	def __init__(self, config, parent=None, state=None, apply_items=None):
		super().__init__(parent)
		self.ui = Ui_SettingsMenu()
		self.ui.setupUi(self)
		self.config = config
		self.state = state
		self.apply_items = apply_items
		self.pending_items = None  # an items.json chosen in this window, used when Save is pressed
		self.items_changed = False  # whether Save has to switch to a different items.json
		self.ui.grp_items.setVisible(state is not None and apply_items is not None)
		self.ui.pb_load_items.clicked.connect(self.on_load_items)
		self.ui.pb_default_items.clicked.connect(self.on_use_included_items)
		self.ui.lbl_error.setVisible(False)
		for name, value in config.settings().items():
			if name in BOOL_SETTING_NAMES:
				self.checkbox(name).setChecked(value == "true")
				continue
			field = self.field(name)
			field.setText(value)
			field.setCursorPosition(0)
			# stop marking a field as bad as soon as the user edits it
			field.textEdited.connect(lambda _text, f=field: f.setStyleSheet(""))
		self.ui.chk_debug_logging.setToolTip(f"The log is written to {LOG_FILE}")
		self.ui.buttonBox.accepted.connect(self.save)
		self.ui.buttonBox.rejected.connect(self.reject)
		self.refresh_items_status()

	def field(self, name):
		return getattr(self.ui, f"fld_{name}")

	def checkbox(self, name):
		return getattr(self.ui, f"chk_{name}")

	def values(self):
		return {
			name: (
				("true" if self.checkbox(name).isChecked() else "false")
				if name in BOOL_SETTING_NAMES
				else self.field(name).text().strip()
			)
			for name in SETTING_NAMES
		}

	def using_included_items(self):
		"""Whether the items.json box holds the file that ships with the program."""
		return resolve_items_path(self.ui.fld_items_file.text()) == resolve_items_path(DEFAULT_ITEMS_FILE)

	def refresh_items_status(self):
		"""Say what the items.json section currently stands for, and which buttons make sense."""
		state = self.state
		if self.items_changed and self.pending_items is not None:
			text = f"{len(self.pending_items)} items ready. Press Save to use them."
		elif state is not None and state.loaded_items is not None:
			count = len(state.items)
			if state.items_error:
				text = f"Using the included items.json ({count} items): the chosen file could not be read ({state.items_error})."
			elif self.using_included_items():
				text = f"Using the included items.json ({count} items)."
			else:
				text = f"Loaded ({count} items)."
		else:
			text = "No items.json loaded."
			if state is not None and state.items_error:
				text += f" {state.items_error}"
		self.ui.lbl_items_status.setText(text)
		self.ui.pb_default_items.setEnabled(not self.using_included_items())

	def choose_items(self, path, shown_as):
		"""Load an items.json for a preview; it is only used once Save is pressed."""
		try:
			items = load_items_file(path)
		except (OSError, ValueError) as e:
			log.error(f"Could not read {path}: {e}")
			self.show_error(f"Could not read {path}:\n{e}")
			return
		self.ui.lbl_error.setVisible(False)
		self.pending_items = items
		self.items_changed = True
		self.ui.fld_items_file.setText(shown_as)
		self.ui.fld_items_file.setCursorPosition(0)
		self.refresh_items_status()

	def on_load_items(self):
		filename, ok = safe_file_dialog(QFileDialog.getOpenFileName, "Import items.json")
		if not ok or filename is None:
			return
		self.choose_items(filename, filename)

	def on_use_included_items(self):
		self.choose_items(resolve_items_path(DEFAULT_ITEMS_FILE), DEFAULT_ITEMS_FILE)

	def save(self):
		values = self.values()
		errors = validate_settings(values)
		for name in TEXT_SETTING_NAMES:
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
		if self.items_changed and self.pending_items is not None and self.apply_items:
			self.apply_items(self.pending_items, str(resolve_items_path(values["items_file"])))
		self.accept()

	def show_error(self, message):
		self.ui.lbl_error.setText(message)
		self.ui.lbl_error.setVisible(True)
