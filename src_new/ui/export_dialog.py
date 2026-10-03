"""The export window: which of a selection's files to write, and where."""

from pathlib import Path

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFileDialog

from ui.compiled.ui_export_dialog import Ui_ExportForm

SUFFIXES = {"locale": "_locale.json", "assort": "_assort.json", "locks": "_questassort.json"}


class ExportDialog(QDialog, Ui_ExportForm):
	"""names: the selected quests' names. export: a core.export.Export. folder: where the file names start.
	The layout is ui/designer/export_dialog.ui. paths() says what to write."""

	def __init__(self, names, export, folder="", parent=None):
		super().__init__(parent)
		self.setupUi(self)
		self.export, self.folder = export, folder
		self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Export")
		shown = ", ".join(names[:4]) + (f" and {len(names) - 4} more" if len(names) > 4 else "")
		self.summaryLabel.setText(f"Export {len(names)} quest{'' if len(names) == 1 else 's'}: {shown}")
		self.rows = {
			"locale": (self.localeBox, self.localeEdit, self.localeBrowse, len(export.locale), "Their text ({n} entries)"),
			"assort": (self.assortBox, self.assortEdit, self.assortBrowse, export.offer_count(), "Their trader offers ({n})"),
			"locks": (self.locksBox, self.locksEdit, self.locksBrowse, export.lock_count(), "Their quest locks ({n})"),
		}
		self._typed = set()  # the paths the user has typed or browsed to (they are not derived from the quests file any more)
		self.questsEdit.setText(str(Path(folder or ".") / "exported_quests.json") if folder else "exported_quests.json")
		for kind, (box, edit, browse, count, label) in self.rows.items():
			box.setText(label.format(n=count))
			if count == 0:
				box.setChecked(False)
				box.setEnabled(False)
				box.setToolTip("There is nothing open for these quests.")
			box.toggled.connect(lambda _c: self._update())
			edit.textEdited.connect(lambda _t, kind=kind: self._typed.add(kind) or self._update())
			edit.textChanged.connect(lambda _t: self._update())
			browse.clicked.connect(lambda _c=False, kind=kind: self._browse(kind))
		self.questsEdit.textChanged.connect(lambda _t: self._derive())
		self.questsBrowse.clicked.connect(lambda _c=False: self._browse("quests"))
		self._derive()

	def _edit(self, kind):
		return self.questsEdit if kind == "quests" else self.rows[kind][1]

	def _derive(self):
		"""Name the other files after the quests file, unless they were named by hand."""
		text = self.questsEdit.text().strip()
		for kind, suffix in SUFFIXES.items():
			if kind in self._typed:
				continue
			try:
				derived = str(Path(text).with_suffix("")) + suffix if text else ""
			except ValueError:  # (a name that is only a folder)
				derived = ""
			self.rows[kind][1].setText(derived)
		self._update()

	def _browse(self, kind):
		chosen, _ = QFileDialog.getSaveFileName(self, "Export to", self._edit(kind).text(), "JSON files (*.json);;All files (*)")
		if chosen:
			self._edit(kind).setText(chosen)
			if kind != "quests":
				self._typed.add(kind)
			self._update()

	def paths(self):
		"""{'quests': path, 'locale': path, ...} for the files to write."""
		found = {"quests": self.questsEdit.text().strip()}
		for kind, (box, edit, _browse, _count, _label) in self.rows.items():
			if box.isChecked():
				found[kind] = edit.text().strip()
		return found

	def _update(self):
		for kind, (box, edit, browse, _count, _label) in self.rows.items():
			edit.setEnabled(box.isChecked())
			browse.setEnabled(box.isChecked())
		paths = list(self.paths().values())
		ok = all(paths) and len(set(paths)) == len(paths)
		self.noteLabel.setText(
			"Only these files are written. What is open is not changed." if ok or not all(paths)
			else "Each file needs its own name."
		)
		self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(bool(ok))
