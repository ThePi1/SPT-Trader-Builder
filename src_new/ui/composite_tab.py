"""The composite items tab: items made of parts that you save once and reuse in rewards and trader offers.

Your saved items are listed first and can be edited. The base game's own composite items are in a
separate read-only list; copy one to make it yours.
"""

from PySide6.QtWidgets import (
	QGroupBox, QHBoxLayout, QInputDialog, QLabel, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QSplitter,
	QVBoxLayout, QWidget,
)
from PySide6.QtCore import Qt

from core import library as library_module
from schema import assort as assort_schema
from schema.common import Names
from ui.forms import Context
from ui.parts_editor import PartsEditor
from ui.quest_outline import _clear

ROLE = Qt.ItemDataRole.UserRole


class CompositeTab(QWidget):
	def __init__(self, library, gamedata=None, picker=None, parent=None):
		super().__init__(parent)
		self.library, self.gamedata, self.picker = library, gamedata, picker
		self.editor = None
		split = QSplitter(self)
		left = QWidget()
		column = QVBoxLayout(left)
		column.setContentsMargins(0, 0, 0, 0)
		column.addWidget(QLabel("<b>My items</b>"))
		self.mine = QListWidget()
		self.mine.currentItemChanged.connect(self._select)
		column.addWidget(self.mine, 2)
		row = QHBoxLayout()
		for text, slot in (("New", self.new), ("Rename", self.rename), ("Delete", self.delete)):
			button = QPushButton(text)
			button.clicked.connect(slot)
			row.addWidget(button)
		column.addLayout(row)
		column.addWidget(QLabel("<b>Base game items</b> (read only)"))
		self.vanilla = QListWidget()
		column.addWidget(self.vanilla, 2)
		copy = QPushButton("Make my own copy")
		copy.clicked.connect(self.copy_vanilla)
		column.addWidget(copy)
		split.addWidget(left)
		self.right = QWidget()
		self.right_layout = QVBoxLayout(self.right)
		split.addWidget(self.right)
		split.setSizes([300, 600])
		outer = QHBoxLayout(self)
		outer.setContentsMargins(0, 0, 0, 0)
		outer.addWidget(split)
		self.refresh()

	def _ctx(self):
		return Context(self.gamedata, Names(self.gamedata), self.picker, self.library)

	def refresh(self, select=None):
		keep = select or self.current_id()
		self.mine.blockSignals(True)
		self.mine.clear()
		for entry_id, name in self.library.names():
			item = QListWidgetItem(name or "(unnamed)")
			item.setData(ROLE, entry_id)
			self.mine.addItem(item)
		self.mine.blockSignals(False)
		self.vanilla.clear()
		presets = self.gamedata.item_presets if self.gamedata is not None else {}
		for preset_id, preset in sorted(presets.items(), key=lambda kv: kv[1].get("_name", "").lower()):
			item = QListWidgetItem(preset.get("_name", preset_id))
			item.setData(ROLE, preset_id)
			self.vanilla.addItem(item)
		row = next((i for i in range(self.mine.count()) if self.mine.item(i).data(ROLE) == keep), 0)
		if self.mine.count():
			self.mine.setCurrentRow(row)
		self._select(self.mine.currentItem(), None)

	def current_id(self):
		item = self.mine.currentItem()
		return item.data(ROLE) if item else None

	def _clear_right(self):
		_clear(self.right_layout)

	def _select(self, item, _previous):
		self._clear_right()
		self.editor = None
		if item is None:
			hint = QLabel("Press New to build an item from parts, or copy one of the base game's.")
			hint.setStyleSheet("color: #808080;")
			self.right_layout.addWidget(hint)
			self.right_layout.addStretch(1)
			return
		entry = self.library.entries[item.data(ROLE)]
		self.problem = QLabel()
		self.problem.setStyleSheet("color: #b9770e;")
		self.editor = PartsEditor(entry["items"], self._ctx())
		self.editor.changed.connect(lambda e=entry, i=item.data(ROLE): self._changed(i))
		self.right_layout.addWidget(QLabel(f"<b>{entry.get('name', '')}</b>"))
		self.right_layout.addWidget(self.editor)
		self.right_layout.addWidget(self.problem)
		self.right_layout.addStretch(1)
		self._check(entry)

	def _check(self, entry):
		issues = assort_schema.validate_composite(entry)
		self.problem.setText("\n".join(i.message for i in issues[:3]))

	def _changed(self, entry_id):
		self.library.update(entry_id)
		self._check(self.library.entries[entry_id])

	def new(self):
		name, ok = QInputDialog.getText(self, "New item", "Name:")
		if ok and name.strip():
			entry_id = self.library.add(name.strip(), [])
			self.refresh(entry_id)

	def rename(self):
		entry_id = self.current_id()
		if entry_id is None:
			return
		name, ok = QInputDialog.getText(self, "Rename", "Name:", text=self.library.entries[entry_id].get("name", ""))
		if ok and name.strip():
			self.library.update(entry_id, name=name.strip())
			self.refresh(entry_id)

	def delete(self):
		entry_id = self.current_id()
		if entry_id is None:
			return
		name = self.library.entries[entry_id].get("name", "this item")
		if QMessageBox.question(self, "Delete", f"Delete \"{name}\" from your saved items?") == QMessageBox.StandardButton.Yes:
			self.library.remove(entry_id)
			self.refresh()

	def copy_vanilla(self):
		item = self.vanilla.currentItem()
		if item is None or self.gamedata is None:
			return
		preset = self.gamedata.item_presets[item.data(ROLE)]
		entry_id = self.library.add(preset.get("_name", "Copy"), library_module.preset_parts(preset))
		self.refresh(entry_id)
