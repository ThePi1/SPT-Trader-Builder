"""The window for the reference files: add, remove and reload them, or merge some into the open files."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox, QTableWidgetItem

from core import references as R
from ui.compiled.ui_references_dialog import Ui_ReferencesForm

JSON_FILTER = "JSON files (*.json);;All files (*)"
IMPORTABLE = (R.QUESTS, R.LOCALE, R.ASSORT)  # (the kinds the Import window can merge)


class ReferencesDialog(QDialog, Ui_ReferencesForm):
	"""The layout is ui/designer/references_dialog.ui. changed is sent when the list changes (the program then
	looks up names again); import_requested is sent with the paths of the files to merge into the open files."""

	changed = Signal()
	import_requested = Signal(list)

	def __init__(self, references, parent=None):
		super().__init__(parent)
		self.setupUi(self)
		self.references = references
		self.addFilesButton.clicked.connect(lambda _checked=False: self.add_files())
		self.addFolderButton.clicked.connect(lambda _checked=False: self.add_folder())
		self.removeButton.clicked.connect(lambda _checked=False: self.remove_selected())
		self.reloadButton.clicked.connect(lambda _checked=False: self.reload())
		self.importButton.clicked.connect(lambda _checked=False: self.import_selected())
		self.table.itemSelectionChanged.connect(self._update_buttons)
		self.table.setColumnWidth(0, 200)
		self.table.setColumnWidth(1, 120)
		self.table.setColumnWidth(2, 60)
		self.refresh()

	def refresh(self):
		self.references.read_all()
		files = self.references.files
		self.table.setRowCount(len(files))
		for row, ref in enumerate(files):
			kind = R.KIND_LABEL.get(ref.kind) or "Can't use"
			for column, text in enumerate((ref.name, kind, f"{ref.count:,}" if ref.kind else "", str(ref.path.parent))):
				cell = QTableWidgetItem(text)
				cell.setToolTip(ref.error or str(ref.path))
				self.table.setItem(row, column, cell)
		self._update_buttons()

	def selected(self):
		rows = sorted({i.row() for i in self.table.selectedItems()})
		return [self.references.files[r] for r in rows]

	def _update_buttons(self):
		chosen = self.selected()
		self.removeButton.setEnabled(bool(chosen))
		self.importButton.setEnabled(any(ref.kind in IMPORTABLE for ref in chosen))

	def add_files(self):
		paths, _ = QFileDialog.getOpenFileNames(self, "Add reference files", "", JSON_FILTER)
		if paths:
			self.add(paths)

	def add_folder(self):
		folder = QFileDialog.getExistingDirectory(self, "Add the files in a folder as references")
		if folder:
			self.add([folder])

	def add(self, paths):
		added, skipped = self.references.add(paths)
		if skipped:
			QMessageBox.information(
				self, "Reference files",
				(f"Added {len(added)} file{'' if len(added) == 1 else 's'}. These were left out:\n\n" if added else "Nothing was added. These were left out:\n\n")
				+ "\n".join(f"{name}: {why}" for name, why in skipped[:20]) + ("\n..." if len(skipped) > 20 else ""),
			)
		self.refresh()
		if added:
			self.changed.emit()

	def remove_selected(self):
		chosen = self.selected()
		if chosen:
			self.references.remove(chosen)
			self.refresh()
			self.changed.emit()

	def reload(self):
		self.references.reload()
		self.refresh()
		self.changed.emit()

	def import_selected(self):
		paths = [str(ref.path) for ref in self.selected() if ref.kind in IMPORTABLE]
		if paths:
			self.import_requested.emit(paths)
			self.accept()
