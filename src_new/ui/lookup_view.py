"""Finding ids: a search box over everything the game has, as a tab and as a picker dialog."""

from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
	QAbstractItemView, QDialog, QDialogButtonBox, QHBoxLayout, QPushButton, QTableWidgetItem, QVBoxLayout, QWidget,
)

from core import lookup
from core import settings as S
from ui.compiled.ui_lookup_view import Ui_LookupForm


class LookupView(QWidget, Ui_LookupForm):
	"""Search box, an optional type filter, and the matching rows. Double-click or Enter picks a row.
	The layout is ui/designer/lookup_view.ui."""

	picked = Signal(list)  # the ids of the chosen rows

	def __init__(self, rows, kinds=None, multi=False, show_filter=True, settings=None, parent=None):
		super().__init__(parent)
		self.setupUi(self)
		self.rows, self.kinds, self.settings = rows, tuple(kinds) if kinds else None, settings
		self.filter.addItem("Everything", None)
		present = {r.kind for r in rows}
		for kind, label in lookup.KIND_LABEL.items():
			if kind in present and (not self.kinds or kind in self.kinds):
				self.filter.addItem(label, kind)
		self.filter.setVisible(show_filter and self.filter.count() > 2)
		self.table.setSelectionMode(
			QAbstractItemView.SelectionMode.ExtendedSelection if multi else QAbstractItemView.SelectionMode.SingleSelection
		)
		self.table.setColumnWidth(0, 230)
		self.table.setColumnWidth(1, 200)
		self.table.setColumnWidth(2, 110)
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
		most = S.limit(self.settings, "lookup_max_rows")
		shown = found[:most]
		self.table.setRowCount(len(shown))
		for i, row in enumerate(shown):
			for column, text in enumerate((row.name or "(no name)", row.detail, lookup.KIND_LABEL[row.kind], row.id)):
				self.table.setItem(i, column, QTableWidgetItem(text))
		if shown:
			self.table.selectRow(0)
		self.note.setText(
			f"Showing the first {most} of {len(found)}. Type more to narrow it down." if len(found) > most
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

	def __init__(self, rows, kinds, title, multi=False, settings=None, parent=None):
		super().__init__(parent)
		self.setWindowTitle(title)
		self.resize(760, 480)
		self.ids = []
		layout = QVBoxLayout(self)
		self.view = LookupView(rows, kinds, multi, show_filter=False, settings=settings)
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

	def __init__(self, rows, settings=None, parent=None):
		super().__init__(parent)
		layout = QVBoxLayout(self)
		self.view = LookupView(rows, settings=settings)
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
