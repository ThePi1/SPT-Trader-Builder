"""Small dialogs: About, Check for updates, Settings."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
	QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
	QMessageBox, QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

from core import settings as S
from schema import choices
from ui import updates

APP_NAME = "SPT Quest Builder"


def _link(url):
	return f'<a href="{url}">{url}</a>'


class AboutDialog(QDialog):
	def __init__(self, version, project_url, parent=None):
		super().__init__(parent)
		self.setWindowTitle("About")
		layout = QVBoxLayout(self)
		label = QLabel(f"<p>Made with \u2665 by the SPT Trader Builder Team</p><p>{version}</p><p>{_link(project_url)}</p>")
		label.setOpenExternalLinks(True)
		label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
		layout.addWidget(label)
		buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
		buttons.rejected.connect(self.reject)
		layout.addWidget(buttons)


class UpdatesDialog(QDialog):
	def __init__(self, status, parent=None):
		super().__init__(parent)
		self.setWindowTitle("Check for updates")
		layout = QVBoxLayout(self)
		self.label = QLabel()
		self.label.setOpenExternalLinks(True)
		layout.addWidget(self.label)
		buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
		buttons.rejected.connect(self.reject)
		layout.addWidget(buttons)
		self.show_status(status)

	def show_status(self, status):
		text = (
			f"<p>Current version: {status.local_version}</p><p>Latest version: {status.latest_display}</p>"
			f"<p>{status.text}</p><p>{_link(status.project_url)}</p>"
		)
		self.label.setText(text)


_LABELS = {
	"debug_logging": "Write a detailed log",
	"copy_locale_to_all_languages": "Copy text into every language file",
	"database_folder": "SPT database folder",
	"language": "Language for names",
	"quest_icon": "Icon",
	"side": "Available to",
	"trader": "Trader",
	"show_all_fields": "Show every option",
	"show_json_preview": "Show the JSON",
	"version_file": "Version file",
	"version_url": "Latest version address",
	"project_url": "Project address",
}
_TIPS = {
	"debug_logging": "Writes spt_builder.log next to the program, for troubleshooting.",
	"copy_locale_to_all_languages": "When you save the text file, also add the text of the open quests to the other languages' files in the same folder. Entries those files already have are kept.",
	"database_folder": "Your SPT_Data/database folder. Empty uses the data that comes with the program. It is only read, never changed.",
	"language": "Language used for item and trader names (en, ru, de, ...).",
	"quest_icon": "The icon new quests start with.",
	"show_all_fields": "Show rarely used options without clicking More options.",
}
_TABS = (
	("General", ("debug_logging", "copy_locale_to_all_languages", "show_all_fields", "show_json_preview")),
	("Game data", ("database_folder", "language")),
	("New quests", ("quest_icon", "side", "trader")),
	("Updates", ("version_file", "version_url", "project_url")),
)


class SettingsDialog(QDialog):
	"""Edits the settings; OK saves them to settings.ini."""

	def __init__(self, settings, gamedata=None, parent=None):
		super().__init__(parent)
		self.setWindowTitle("Settings")
		self.settings, self.controls = settings, {}
		layout = QVBoxLayout(self)
		tabs = QTabWidget()
		layout.addWidget(tabs)
		for title, keys in _TABS:
			page = QWidget()
			form = QFormLayout(page)
			for key in keys:
				control = self._make(S.BY_KEY[key], gamedata)
				control.setToolTip(_TIPS.get(key, ""))
				self.controls[key] = control
				form.addRow(_LABELS[key], control)
			tabs.addTab(page, title)
		buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
		buttons.accepted.connect(self.accept)
		buttons.rejected.connect(self.reject)
		layout.addWidget(buttons)

	def _make(self, setting, gamedata):
		value = getattr(self.settings, setting.key)
		if setting.kind == "bool":
			box = QCheckBox()
			box.setChecked(value)
			return box
		if setting.key == "side":
			combo = QComboBox()
			for v, label in choices.SIDES:
				combo.addItem(label, v)
			combo.setCurrentIndex(max(0, combo.findData(value)))
			return combo
		if setting.key == "trader":
			combo = QComboBox()
			combo.addItem("(none)", "")
			for v, label in choices.get("traders", gamedata):
				combo.addItem(label, v)
			combo.setCurrentIndex(max(0, combo.findData(value)))
			return combo
		if setting.key == "database_folder":
			return _FolderEdit(value)
		entry = QLineEdit(str(value))
		return entry

	def values(self):
		out = {}
		for key, control in self.controls.items():
			if isinstance(control, QCheckBox):
				out[key] = control.isChecked()
			elif isinstance(control, QComboBox):
				out[key] = control.currentData()
			elif isinstance(control, _FolderEdit):
				out[key] = control.text()
			else:
				out[key] = control.text().strip()
		return out

	def accept(self):
		try:
			self.settings.update(self.values())
		except ValueError as e:
			QMessageBox.warning(self, "Settings", str(e))
			return
		except OSError as e:
			QMessageBox.warning(self, "Settings", f"The settings could not be saved.\n\n{e}")
			return
		super().accept()


class _FolderEdit(QWidget):
	def __init__(self, value):
		super().__init__()
		row = QHBoxLayout(self)
		row.setContentsMargins(0, 0, 0, 0)
		self.entry = QLineEdit(value)
		browse = QPushButton("Browse...")
		browse.clicked.connect(self._browse)
		row.addWidget(self.entry, 1)
		row.addWidget(browse)

	def _browse(self):
		folder = QFileDialog.getExistingDirectory(self, "SPT database folder", self.entry.text())
		if folder:
			self.entry.setText(folder)

	def text(self):
		return self.entry.text().strip()
