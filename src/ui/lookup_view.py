"""Finding ids: a search box over everything the game has, as a tab and as a picker dialog."""

from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QAbstractItemView, QDialog, QTableWidgetItem, QWidget

from core import lookup
from core import settings as S
from ui.compiled.ui_lookup_tab import Ui_LookupTabForm
from ui.compiled.ui_lookup_view import Ui_LookupForm
from ui.compiled.ui_picker_dialog import Ui_PickerForm


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


class PickerDialog(QDialog, Ui_PickerForm):
	"""Choose one thing (or several) from a search. ids is the result, empty if cancelled.
	The window and its OK / Cancel buttons are ui/designer/picker_dialog.ui; the search view goes above them."""

	def __init__(self, rows, kinds, title, multi=False, settings=None, parent=None):
		super().__init__(parent)
		self.setupUi(self)
		self.setWindowTitle(title)
		self.ids = []
		self.view = LookupView(rows, kinds, multi, show_filter=False, settings=settings)
		self.verticalLayout.insertWidget(0, self.view, 1)
		self.view.picked.connect(self._picked)
		self.view.search.setFocus()

	def _picked(self, ids):
		self.ids = ids
		self.accept()

	def accept(self):
		self.ids = self.ids or self.view.selected_ids()
		super().accept()


class LookupTab(QWidget, Ui_LookupTabForm):
	"""The 'Find IDs' tab: search everything, copy an id or a name. The buttons are ui/designer/lookup_tab.ui."""

	def __init__(self, rows, settings=None, parent=None):
		super().__init__(parent)
		self.setupUi(self)
		self.view = LookupView(rows, settings=settings)
		self.verticalLayout.insertWidget(0, self.view, 1)
		self.copy_id_button.clicked.connect(lambda _checked=False: self._copy(3))
		self.copy_name_button.clicked.connect(lambda _checked=False: self._copy(0))
		self.view.picked.connect(lambda _ids: self._copy(3))

	def _copy(self, column):
		rows = sorted({i.row() for i in self.view.table.selectedItems()})
		if rows:
			QGuiApplication.clipboard().setText("\n".join(self.view.table.item(r, column).text() for r in rows))

	def set_rows(self, rows):
		self.view.rows = rows
		self.view.refresh()
