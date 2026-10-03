"""The text tab: every entry of the locale file, with the quest each one belongs to."""

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import (
	QComboBox, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QPushButton, QTableView, QVBoxLayout, QWidget,
)

from core.documents import MISSING
from schema import locale as L

COLUMNS = ("Belongs to", "Key", "Text")
FILTERS = (
	("all", "All text"),
	("mine", "Text of the quests in the open quest file"),
	("missing", "Text still missing for those quests"),
	("unused", "Text those quests don't use"),
)
MAX_SHOWN = 5000


class LocaleModel(QAbstractTableModel):
	def __init__(self, locale_doc, quests_doc):
		super().__init__()
		self.locale, self.quests = locale_doc, quests_doc
		self.keys, self.owner = [], {}

	def set_documents(self, locale_doc, quests_doc):
		self.beginResetModel()
		self.locale, self.quests = locale_doc, quests_doc
		self.keys = []
		self.endResetModel()

	def _owners(self):
		"""{key: name of the quest it belongs to} for every key the open quests use or could use."""
		owners = {}
		for quest in self.quests.data.values():
			if not isinstance(quest, dict):
				continue
			name = quest.get("QuestName", "")
			for key in L.QUEST_TEXT_KEYS:
				owners[L.quest_key(quest.get("_id", ""), key)] = name
			for task_id, _timing, _task in L.quest_tasks(quest):
				owners[task_id] = name
		return owners

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
		words = text.lower().split()
		if words:
			keys = [k for k in keys if all(w in f"{k} {data.get(k, '')} {owners.get(k, '')}".lower() for w in words)]
		self.keys, self.owner = keys[:MAX_SHOWN], owners
		self.truncated = len(keys) > MAX_SHOWN
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
		if not index.isValid() or role not in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole, Qt.ItemDataRole.ToolTipRole):
			return None
		key = self.keys[index.row()]
		if index.column() == 0:
			return self.owner.get(key, "")
		if index.column() == 1:
			return key
		text = self.locale.data.get(key, "")
		return text if role == Qt.ItemDataRole.EditRole or role == Qt.ItemDataRole.ToolTipRole else text.replace("\n", " ↵ ")

	def flags(self, index):
		base = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
		return base | Qt.ItemFlag.ItemIsEditable if index.column() == 2 else base

	def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
		if role != Qt.ItemDataRole.EditRole or index.column() != 2:
			return False
		key = self.keys[index.row()]
		self.locale.set_value("Edit text", (key,), str(value), coalesce=key)
		self.dataChanged.emit(index, index)
		return True


class LocaleTab(QWidget):
	def __init__(self, locale_doc, quests_doc, parent=None):
		super().__init__(parent)
		self.model = LocaleModel(locale_doc, quests_doc)
		layout = QVBoxLayout(self)
		top = QHBoxLayout()
		self.search = QLineEdit()
		self.search.setPlaceholderText("Search the text, keys or quest names")
		self.search.setClearButtonEnabled(True)
		self.mode = QComboBox()
		for value, label in FILTERS:
			self.mode.addItem(label, value)
		top.addWidget(self.search, 1)
		top.addWidget(self.mode)
		layout.addLayout(top)
		self.table = QTableView()
		self.table.setModel(self.model)
		self.table.verticalHeader().setVisible(False)
		self.table.horizontalHeader().setStretchLastSection(True)
		self.table.setColumnWidth(0, 180)
		self.table.setColumnWidth(1, 260)
		layout.addWidget(self.table, 1)
		self.note = QLabel()
		self.note.setStyleSheet("color: #808080;")
		layout.addWidget(self.note)
		row = QHBoxLayout()
		for text, slot in (
			("Add missing text", self.add_missing), ("Add an entry...", self.add_entry), ("Delete", self.delete_selected),
			("Fix old spellings", self.fix_spelling),
		):
			button = QPushButton(text)
			button.clicked.connect(slot)
			row.addWidget(button)
		row.addStretch(1)
		layout.addLayout(row)
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
		missing = L.missing_keys(self.model.quests.data, self.doc.data)
		for key in missing:
			if key not in self.doc.data:
				self.doc.set_value("Add missing text", (key,), "")
		self.mode.setCurrentIndex(self.mode.findData("missing"))
		self.refresh()

	def add_entry(self):
		key, ok = QInputDialog.getText(self, "Add an entry", "Key:")
		key = key.strip()
		if ok and key and key not in self.doc.data:
			self.doc.set_value("Add entry", (key,), "")
			self.search.setText(key)

	def delete_selected(self):
		rows = sorted({i.row() for i in self.table.selectionModel().selectedIndexes()}, reverse=True)
		for row in rows:
			self.doc.set_value("Delete entry", (self.model.keys[row],), MISSING)
		self.refresh()

	def fix_spelling(self):
		fixed = L.fix_misspelled(self.doc.data)
		if fixed != self.doc.data:
			self.doc.change("Fix old spellings", lambda data: (data.clear(), data.update(fixed)))
			self.refresh()
