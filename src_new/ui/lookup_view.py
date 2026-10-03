"""Finding ids: a search box over everything the game has, as a tab and as a picker dialog."""

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
	QAbstractItemView, QComboBox, QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget,
	QTableWidgetItem, QVBoxLayout, QWidget,
)

from core import lookup

MAX_ROWS = 400


class LookupView(QWidget):
	"""Search box, an optional type filter, and the matching rows. Double-click or Enter picks a row."""

	picked = Signal(list)  # the ids of the chosen rows

	def __init__(self, rows, kinds=None, multi=False, show_filter=True, parent=None):
		super().__init__(parent)
		self.rows, self.kinds = rows, tuple(kinds) if kinds else None
		layout = QVBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		top = QHBoxLayout()
		self.search = QLineEdit()
		self.search.setPlaceholderText("Type a name or id")
		self.search.setClearButtonEnabled(True)
		top.addWidget(self.search, 1)
		self.filter = QComboBox()
		self.filter.addItem("Everything", None)
		present = {r.kind for r in rows}
		for kind, label in lookup.KIND_LABEL.items():
			if kind in present and (not self.kinds or kind in self.kinds):
				self.filter.addItem(label, kind)
		self.filter.setVisible(show_filter and self.filter.count() > 2)
		top.addWidget(self.filter)
		layout.addLayout(top)
		self.table = QTableWidget(0, 4)
		self.table.setHorizontalHeaderLabels(["Name", "Details", "Type", "Id"])
		self.table.horizontalHeader().setStretchLastSection(True)
		self.table.verticalHeader().setVisible(False)
		self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
		self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
		self.table.setSelectionMode(
			QAbstractItemView.SelectionMode.ExtendedSelection if multi else QAbstractItemView.SelectionMode.SingleSelection
		)
		self.table.setColumnWidth(0, 230)
		self.table.setColumnWidth(1, 200)
		self.table.setColumnWidth(2, 110)
		layout.addWidget(self.table, 1)
		self.note = QLabel()
		self.note.setStyleSheet("color: #808080;")
		layout.addWidget(self.note)
		self._timer = QTimer(self)
		self._timer.setSingleShot(True)
		self._timer.setInterval(150)
		self._timer.timeout.connect(self.refresh)
		self.search.textChanged.connect(lambda _t: self._timer.start())
		self.filter.currentIndexChanged.connect(lambda _i: self.refresh())
		self.table.itemDoubleClicked.connect(lambda _i: self.picked.emit(self.selected_ids()))
		self.search.returnPressed.connect(self._enter)
		self.refresh()

	def refresh(self):
		kind = self.filter.currentData()
		kinds = (kind,) if kind else self.kinds
		found = lookup.search(self.rows, self.search.text(), kinds)
		shown = found[:MAX_ROWS]
		self.table.setRowCount(len(shown))
		for i, row in enumerate(shown):
			for column, text in enumerate((row.name or "(no name)", row.detail, lookup.KIND_LABEL[row.kind], row.id)):
				self.table.setItem(i, column, QTableWidgetItem(text))
		if shown:
			self.table.selectRow(0)
		self.note.setText(
			f"Showing the first {MAX_ROWS} of {len(found)}. Type more to narrow it down." if len(found) > MAX_ROWS
			else f"{len(found)} found." if self.search.text() else f"{len(found)} in total."
		)

	def selected_ids(self):
		rows = sorted({i.row() for i in self.table.selectedItems()})
		return [self.table.item(r, 3).text() for r in rows]

	def _enter(self):
		self._timer.stop()
		self.refresh()
		ids = self.selected_ids()
		if ids:
			self.picked.emit(ids)


class PickerDialog(QDialog):
	"""Choose one thing (or several) from a search. ids is the result, empty if cancelled."""

	def __init__(self, rows, kinds, title, multi=False, parent=None):
		super().__init__(parent)
		self.setWindowTitle(title)
		self.resize(760, 480)
		self.ids = []
		layout = QVBoxLayout(self)
		self.view = LookupView(rows, kinds, multi, show_filter=False)
		layout.addWidget(self.view, 1)
		buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
		buttons.accepted.connect(self.accept)
		buttons.rejected.connect(self.reject)
		layout.addWidget(buttons)
		self.view.picked.connect(self._picked)
		self.view.search.setFocus()

	def _picked(self, ids):
		self.ids = ids
		self.accept()

	def accept(self):
		self.ids = self.ids or self.view.selected_ids()
		super().accept()


class LookupTab(QWidget):
	"""The 'Find IDs' tab: search everything, copy an id or a name."""

	def __init__(self, rows, parent=None):
		super().__init__(parent)
		layout = QVBoxLayout(self)
		self.view = LookupView(rows)
		layout.addWidget(self.view, 1)
		row = QHBoxLayout()
		for text, column in (("Copy id", 3), ("Copy name", 0)):
			button = QPushButton(text)
			button.clicked.connect(lambda _c=False, c=column: self._copy(c))
			row.addWidget(button)
		row.addStretch(1)
		layout.addLayout(row)
		self.view.picked.connect(lambda _ids: self._copy(3))

	def _copy(self, column):
		rows = sorted({i.row() for i in self.view.table.selectedItems()})
		if rows:
			QGuiApplication.clipboard().setText("\n".join(self.view.table.item(r, column).text() for r in rows))

	def set_rows(self, rows):
		self.view.rows = rows
		self.view.refresh()
