"""The Locale tab: every entry of the locale file, with the quest each one belongs to."""

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QBrush, QPalette
from PySide6.QtWidgets import QApplication, QInputDialog, QWidget

from core import settings as S
from core.documents import MISSING
from schema import locale as L
from ui.compiled.ui_locale_tab import Ui_LocaleForm

COLUMNS = ("Belongs to", "Key", "Text", "File")
FILTERS = (
	("all", "All text"),
	("mine", "Text of the quests in the open quest file"),
	("missing", "Text still missing for those quests"),
	("unused", "Text those quests don't use"),
)


class LocaleModel(QAbstractTableModel):
	def __init__(self, locale_doc, quests_doc, settings=None, references=None):
		super().__init__()
		self.locale, self.quests, self.settings, self.references = locale_doc, quests_doc, settings, references
		self.keys, self.owner = [], {}
		self.reference = {}  # {key: (text, file name)} of the shown entries that are only in a reference file: they are looked at, not edited
		self.truncated, self.total = False, 0

	def set_documents(self, locale_doc, quests_doc):
		self.beginResetModel()
		self.locale, self.quests = locale_doc, quests_doc
		self.keys = []
		self.endResetModel()

	def _owners(self):
		"""{key: name of the quest it belongs to} for every key the open quests use or could use."""
		return L.key_owners(self.quests.data)

	def refresh(self, mode="all", text=""):
		self.beginResetModel()
		owners = self._owners()
		data = self.locale.data
		if mode == "mine":
			keys = [k for k in data if k in owners]
		elif mode == "missing":
			keys = list(L.missing_keys(self.quests.data, data))
		elif mode == "unused":
			keys = L.unused_keys(self.quests.data, data)
		else:
			keys = list(data)
		known = self.references.locale_entries() if self.references is not None and mode in ("all", "mine") else {}
		known = {k: v for k, v in known.items() if k not in data and (mode == "all" or k in owners)}  # (what the open file has is its own: shown as it)
		keys += list(known)
		words = text.lower().split()
		if words:
			keys = [k for k in keys if all(w in f"{k} {data.get(k) if k in data else known.get(k, ('',))[0]} {owners.get(k, '')}".lower() for w in words)]
		most = S.limit(self.settings, "locale_max_entries")
		self.keys, self.owner = keys[:most], owners
		self.reference = {k: known[k] for k in self.keys if k in known}
		self.truncated = len(keys) > most
		self.total = len(keys)
		self.endResetModel()

	def rowCount(self, parent=QModelIndex()):
		return 0 if parent.isValid() else len(self.keys)

	def columnCount(self, parent=QModelIndex()):
		return len(COLUMNS)

	def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
		if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
			return COLUMNS[section]

	def data(self, index, role=Qt.ItemDataRole.DisplayRole):
		if not index.isValid() or role not in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole, Qt.ItemDataRole.ToolTipRole, Qt.ItemDataRole.ForegroundRole):
			return None
		key = self.keys[index.row()]
		if role == Qt.ItemDataRole.ForegroundRole:  # (an entry of a reference file is greyed out: it can't be edited here)
			return QBrush(QApplication.palette().color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text)) if key in self.reference else None
		if index.column() == 0:
			return self.owner.get(key, "")
		if index.column() == 1:
			return key
		if index.column() == 3:
			return f"Reference: {self.reference[key][1]}" if key in self.reference else ""
		text = self.reference[key][0] if key in self.reference else self.locale.data.get(key, "")
		if role == Qt.ItemDataRole.ToolTipRole and key in self.reference:
			return f"From the reference file {self.reference[key][1]}. Reference files can't be edited.\n\n{text}"
		return text if role == Qt.ItemDataRole.EditRole or role == Qt.ItemDataRole.ToolTipRole else text.replace("\n", " ↵ ")

	def is_reference(self, row):
		return self.keys[row] in self.reference

	def flags(self, index):
		base = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
		return base | Qt.ItemFlag.ItemIsEditable if index.column() == 2 and not self.is_reference(index.row()) else base

	def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
		if role != Qt.ItemDataRole.EditRole or index.column() != 2 or self.is_reference(index.row()):
			return False
		key = self.keys[index.row()]
		self.locale.set_value("Edit text", (key,), str(value), coalesce=key)
		self.dataChanged.emit(index, index)
		return True


class LocaleTab(QWidget, Ui_LocaleForm):
	"""The layout is ui/designer/locale_tab.ui: search, mode, table, note, and the four buttons."""

	def __init__(self, locale_doc, quests_doc, settings=None, parent=None, references=None):
		super().__init__(parent)
		self.setupUi(self)
		self.model = LocaleModel(locale_doc, quests_doc, settings, references)
		for value, label in FILTERS:
			self.mode.addItem(label, value)
		self.table.setModel(self.model)
		self.table.setColumnWidth(0, 180)
		self.table.setColumnWidth(1, 260)
		for button, slot in (
			(self.addMissingButton, self.add_missing), (self.addEntryButton, self.add_entry),
			(self.deleteButton, self.delete_selected), (self.fixSpellingButton, self.fix_spelling),
		):
			button.clicked.connect(lambda _checked=False, slot=slot: slot())
		self.search.textChanged.connect(lambda _t: self.refresh())
		self.mode.currentIndexChanged.connect(lambda _i: self.refresh())
		self.refresh()

	def set_documents(self, locale_doc, quests_doc):
		self.model.set_documents(locale_doc, quests_doc)
		self.refresh()

	def refresh(self):
		self.model.refresh(self.mode.currentData(), self.search.text())
		shown = len(self.model.keys)
		self.note.setText(
			f"Showing the first {shown} of {self.model.total}. Search to narrow it down." if self.model.truncated
			else f"{self.model.total} entries."
		)

	@property
	def doc(self):
		return self.model.locale

	def add_missing(self):
		"""Add an empty entry for every text field the open quests can have (the optional ones too), then show them."""
		missing = L.missing_keys(self.model.quests.data, self.doc.data, optional=True)
		for key in missing:
			if key not in self.doc.data:
				self.doc.set_value("Add all missing fields", (key,), "")
		self.mode.setCurrentIndex(self.mode.findData("mine"))  # (the "missing" list only shows the needed text)
		self.refresh()

	def add_entry(self):
		key, ok = QInputDialog.getText(self, "Add an entry", "Key:")
		key = key.strip()
		if ok and key and key not in self.doc.data:
			self.doc.set_value("Add entry", (key,), "")
			self.search.setText(key)

	def delete_selected(self):
		rows = sorted({i.row() for i in self.table.selectionModel().selectedIndexes() if not self.model.is_reference(i.row())}, reverse=True)  # (not a reference's entry)
		for row in rows:
			self.doc.set_value("Delete entry", (self.model.keys[row],), MISSING)
		self.refresh()

	def fix_spelling(self):
		fixed = L.fix_misspelled(self.doc.data)
		if fixed != self.doc.data:
			self.doc.change("Fix old spellings", lambda data: (data.clear(), data.update(fixed)))
			self.refresh()
