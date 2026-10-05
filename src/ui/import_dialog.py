"""The import window: shows what importing the chosen files would do, before anything changes."""

import dataclasses

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QDialogButtonBox, QDialog, QTableWidgetItem

from core import merge as M
from ui.compiled.ui_import_dialog import Ui_ImportForm

COLUMNS = {"include": 0, "file": 1, "type": 2, "new": 3, "there": 4, "notes": 5}
TYPES = ((None, "Not recognised"), (M.QUESTS, "Quests"), (M.LOCALE, "Locale"), (M.ASSORT, "Trader assort"), (M.LOCKS, "Quest assort"))
NOUN = {M.QUESTS: "quest", M.ASSORT: "offer"}


def _count_words(kind, n):
	if kind in (M.LOCALE, M.LOCKS):
		return f"{n} {'locale' if kind == M.LOCALE else 'quest assort'} {'entry' if n == 1 else 'entries'}"
	return f"{n} {NOUN[kind]}{'' if n == 1 else 's'}"


class ImportDialog(QDialog, Ui_ImportForm):
	"""Items (core.merge.Item) and the workspace ({kind: data}) in; when accepted, .plan says what to apply.
	The layout is ui/designer/import_dialog.ui; the rows of the table are made here."""

	def __init__(self, items, workspace, parent=None):
		super().__init__(parent)
		self.setupUi(self)
		self.items, self.workspace = items, workspace
		self.plan = None
		self.use_as_references = False  # (set by the "Use as references only" button)
		self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Import")
		self.referenceButton = self.buttons.addButton("Use as references only", QDialogButtonBox.ButtonRole.ActionRole)
		self.referenceButton.setToolTip("Keep these files for looking up ids only: nothing is merged into the files you have open")
		self.referenceButton.clicked.connect(self._use_as_references)
		self.table.setRowCount(len(items))
		self.combos = []
		for row, item in enumerate(items):
			check = QTableWidgetItem()
			check.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
			check.setCheckState(Qt.CheckState.Checked if item.include and item.kind else Qt.CheckState.Unchecked)
			self.table.setItem(row, COLUMNS["include"], check)
			name = QTableWidgetItem(item.name)
			name.setToolTip(str(item.path or item.name))
			self.table.setItem(row, COLUMNS["file"], name)
			combo = QComboBox()
			for kind, label in TYPES:
				combo.addItem(label, kind)
			combo.setCurrentIndex(max(0, combo.findData(item.kind)))
			combo.currentIndexChanged.connect(lambda _i: self.refresh())
			self.table.setCellWidget(row, COLUMNS["type"], combo)
			self.combos.append(combo)
			for key in ("new", "there", "notes"):
				self.table.setItem(row, COLUMNS[key], QTableWidgetItem(""))
		self.table.setColumnWidth(COLUMNS["include"], 60)
		self.table.setColumnWidth(COLUMNS["file"], 200)
		self.table.setColumnWidth(COLUMNS["type"], 130)
		self.table.setColumnWidth(COLUMNS["new"], 110)
		self.table.setColumnWidth(COLUMNS["there"], 140)
		self.table.itemChanged.connect(lambda _item: self.refresh())
		for button in (self.keepRadio, self.replaceRadio, self.bothRadio):
			button.toggled.connect(lambda _checked: self.refresh())
		self.everythingBox.toggled.connect(lambda _checked: self.refresh())
		self.refresh()

	@property
	def policy(self):
		return M.REPLACE if self.replaceRadio.isChecked() else M.BOTH if self.bothRadio.isChecked() else M.KEEP

	def _use_as_references(self):
		self.use_as_references = True
		self.accept()

	def chosen_items(self):
		"""The items as the table has them now: kind and include as the user set them."""
		chosen = []
		for row, item in enumerate(self.items):
			kind = self.combos[row].currentData()
			include = self.table.item(row, COLUMNS["include"]).checkState() == Qt.CheckState.Checked and kind is not None
			chosen.append(dataclasses.replace(item, kind=kind, include=include))
		return chosen

	def refresh(self):
		chosen = self.chosen_items()
		self.everythingBox.setEnabled(any(i.kind == M.LOCALE and i.include for i in chosen))
		try:
			plan = M.plan_import(chosen, self.workspace, self.policy, self.everythingBox.isChecked())
		except (KeyError, TypeError, AttributeError, ValueError):
			self.plan = None
			self.summaryLabel.setText("These files can't be combined with the types they are set to. Check the Type column.")
			self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
			return
		self.plan = plan
		self.table.blockSignals(True)
		for row, (item, counts) in enumerate(zip(chosen, plan.counts)):
			notes = self.items[row].error if not item.include else ""
			if counts is None:
				new = there = ""
			else:
				new = _count_words(item.kind, counts.new) if counts.new else "none"
				there = ", ".join(part for part in (f"{counts.same} the same" if counts.same else "", f"{counts.conflicts} differ" if counts.conflicts else "") if part) or "none"
			self.table.item(row, COLUMNS["new"]).setText(new)
			self.table.item(row, COLUMNS["there"]).setText(there)
			self.table.item(row, COLUMNS["notes"]).setText(notes)
		self.table.blockSignals(False)
		parts = [_count_words(kind, plan.adds(kind)) for kind in M.ORDER if plan.adds(kind)]
		conflicts = sum(c.conflicts for c in plan.total.values())
		replaced = {M.KEEP: "kept as they are", M.REPLACE: "replaced by the imported ones", M.BOTH: "kept next to the imported ones"}[self.policy]
		text = ("Will add " + ", ".join(parts) + ".") if parts else "Nothing new to add."
		if conflicts:
			text += f" {conflicts} that differ from what you have will be {replaced}."
		self.summaryLabel.setText(text)
		self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(bool(plan.changed))
