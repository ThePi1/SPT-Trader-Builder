"""Editing an item made of parts (a weapon with mods): a tree of the parts, and the details of the selected one.

It edits the list of parts in place and says so with ``changed``. Used for reward items, trader
offers and the composite item builder.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
	QCheckBox, QComboBox, QFormLayout, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QMenu, QMessageBox, QPushButton,
	QToolButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from core import library as library_module
from core import parts as P
from schema import choices
from schema.common import short

ROLE = Qt.ItemDataRole.UserRole


class PartsEditor(QWidget):
	changed = Signal()

	def __init__(self, parts, ctx, parent=None):
		super().__init__(parent)
		self.parts, self.ctx = parts, ctx
		self._loading = False
		self.read_only = False
		layout = QVBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		bar = QHBoxLayout()
		bar.setSpacing(3)
		self.add_button = QPushButton("Add item...")
		self.add_button.setToolTip("Add an item. With a part selected it is attached to it (a mod, ammo).")
		self.add_button.clicked.connect(self.add_item)
		self.remove_button = QPushButton("Remove")
		self.remove_button.clicked.connect(self.remove_selected)
		more = self.more_button = QToolButton()
		more.setText("More")
		more.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
		menu = QMenu(more)
		menu.addAction("Add a composite item...", self.add_composite)
		menu.addSeparator()
		menu.addAction("Save these as my item...", self.save_to_library)
		more.setMenu(menu)
		for widget in (self.add_button, self.remove_button, more):
			bar.addWidget(widget)
		bar.addStretch(1)
		layout.addLayout(bar)
		self.tree = QTreeWidget()
		self.tree.setHeaderHidden(True)
		self.tree.setMinimumHeight(110)
		self.tree.setMaximumHeight(220)
		self.tree.currentItemChanged.connect(self._selected)
		layout.addWidget(self.tree)
		self.detail = QWidget()
		form = QFormLayout(self.detail)
		form.setContentsMargins(0, 0, 0, 0)
		self.name_label = QLabel()
		self.slot = QComboBox()
		self.slot.setEditable(True)
		self.slot.lineEdit().textEdited.connect(self._slot_edited)
		self.slot.activated.connect(lambda _i: self._slot_edited(self.slot.currentText()))
		self.stack = QLineEdit()
		self.stack.textEdited.connect(self._stack_edited)
		self.found = QCheckBox()
		self.found.clicked.connect(self._found_edited)
		self.hint = QLabel()
		self.hint.setStyleSheet("color: #808080;")
		form.addRow("Item", self.name_label)
		self.slot_row_label = QLabel("Slot")
		form.addRow(self.slot_row_label, self.slot)
		form.addRow("Stack size", self.stack)
		form.addRow("Found in raid", self.found)
		form.addRow(self.hint)
		layout.addWidget(self.detail)
		self.rebuild()

	def set_read_only(self, read_only=True):
		"""Show the parts without letting them be changed: the buttons and the fields are disabled, but the tree
		can still be browsed to see each part's details."""
		self.read_only = read_only
		for widget in (self.add_button, self.more_button, self.slot, self.stack, self.found):
			widget.setEnabled(not read_only)
		self.remove_button.setEnabled(not read_only and self.tree.currentItem() is not None)

	# --- helpers ----------------------------------------------------------------------------
	@property
	def items(self):
		return self.ctx.gamedata.items if self.ctx.gamedata is not None else {}

	def _name(self, tpl):
		return self.ctx.names.item(tpl)

	def _current(self):
		item = self.tree.currentItem()
		return P.find(self.parts, item.data(0, ROLE)) if item is not None else None

	def _emit(self):
		self.changed.emit()

	# --- the tree ---------------------------------------------------------------------------
	def rebuild(self, select=None):
		keep = select or (self._current() or {}).get("_id")
		self.tree.blockSignals(True)
		self.tree.clear()
		seen = set()

		def add(parent_item, part):
			if part["_id"] in seen:
				return
			seen.add(part["_id"])
			slot = part.get("slotId")
			text = self._name(part.get("_tpl", "")) + (f"  ({slot})" if slot else "")
			count = (part.get("upd") or {}).get("StackObjectsCount")
			if count not in (None, 1):
				text += f"  x{count}"
			node = QTreeWidgetItem([text])
			node.setData(0, ROLE, part["_id"])
			(parent_item.addChild if parent_item is not None else self.tree.addTopLevelItem)(node)
			for child in P.children(self.parts, part["_id"]):
				add(node, child)

		for root in P.roots(self.parts):
			add(None, root)
		self.tree.expandAll()
		self.tree.blockSignals(False)
		target = next((i for i in self._walk() if i.data(0, ROLE) == keep), None) if keep else None
		if target is None and self.tree.topLevelItemCount():
			target = self.tree.topLevelItem(0)
		if target is not None:
			self.tree.setCurrentItem(target)
		self._selected(self.tree.currentItem(), None)

	def _walk(self, item=None):
		items = [item] if item is not None else [self.tree.topLevelItem(i) for i in range(self.tree.topLevelItemCount())]
		for it in items:
			yield it
			for i in range(it.childCount()):
				yield from self._walk(it.child(i))

	def _selected(self, item, _previous):
		part = P.find(self.parts, item.data(0, ROLE)) if item is not None else None
		self.detail.setVisible(part is not None)
		self.remove_button.setEnabled(part is not None and not self.read_only)
		if part is None:
			return
		self._loading = True
		self.name_label.setText(f"{self._name(part.get('_tpl', ''))}   {short(part.get('_tpl', ''), 12)}")
		parent = P.find(self.parts, part.get("parentId"))
		self.slot.setVisible(parent is not None)
		self.slot_row_label.setVisible(parent is not None)
		self.slot.clear()
		if parent is not None:
			names = P.slot_names(self.items, parent.get("_tpl", "")) or [n for n, _l in choices.mod_slots()]
			self.slot.addItems(names)
		self.slot.setEditText(part.get("slotId", "") or "")
		upd = part.get("upd") or {}
		self.stack.setStyleSheet("")
		self.stack.setText("" if upd.get("StackObjectsCount") is None else str(upd["StackObjectsCount"]))
		self.found.setChecked(bool(upd.get("SpawnedInSession")))
		self._loading = False
		self._update_hint(part, parent)

	def _update_hint(self, part, parent):
		self.hint.setText("")
		if parent is None:
			return
		verdict = P.fits(self.items, parent.get("_tpl", ""), part.get("slotId", ""), part.get("_tpl", ""))
		if verdict is False:
			self.hint.setText("This item doesn't normally go in that slot.")
		elif verdict is True:
			self.hint.setText("Fits in this slot.")

	# --- editing the selected part ----------------------------------------------------------
	def _slot_edited(self, text):
		part = self._current()
		if part is None or self._loading:
			return
		part["slotId"] = text.strip()
		self._update_hint(part, P.find(self.parts, part.get("parentId")))
		self.rebuild(part["_id"])
		self._emit()

	def _stack_edited(self, text):
		part = self._current()
		if part is None or self._loading:
			return
		try:
			value = int(text.strip())
			if value < 1:
				raise ValueError
		except ValueError:
			self.stack.setStyleSheet("border: 1px solid #c0392b; background: #fdecea;")
			return
		self.stack.setStyleSheet("")
		part.setdefault("upd", {})["StackObjectsCount"] = value
		self.rebuild(part["_id"])
		self._emit()

	def _found_edited(self, checked):
		part = self._current()
		if part is None or self._loading:
			return
		part.setdefault("upd", {})["SpawnedInSession"] = bool(checked)
		self._emit()

	# --- adding and removing ----------------------------------------------------------------
	def add_item(self):
		"""Search items (and composite items) and add what is chosen. A composite item is added whole, as its own part."""
		ids = self.ctx.pick("part", True, self)
		parent = self._current()
		last = None
		for tpl in ids:
			composite = self._composite_parts(tpl)
			if composite is not None:
				self._append(composite)
				continue
			if parent is None:
				last = P.add_part(self.parts, tpl)
				continue
			slot = P.free_slot_for(self.items, self.parts, parent, tpl)
			if slot is None:
				slot = self._ask_slot(parent, tpl)
				if slot is None:
					continue
			last = P.add_part(self.parts, tpl, parent["_id"], slot)
		if last is not None:
			self.rebuild(last["_id"])
			self._emit()

	def _ask_slot(self, parent, tpl):
		names = P.slot_names(self.items, parent.get("_tpl", ""))
		text, ok = QInputDialog.getItem(
			self, "Which slot?", f"Where does {self._name(tpl)} go on {self._name(parent.get('_tpl', ''))}?", names, 0, True,
		) if names else QInputDialog.getText(self, "Which slot?", f"Slot name for {self._name(tpl)} (like mod_magazine):")
		return text.strip() if ok else None

	def remove_selected(self):
		part = self._current()
		if part is None:
			return
		P.remove_part(self.parts, part["_id"])
		self.rebuild()
		self._emit()

	def _append(self, new_parts):
		self.parts.extend(new_parts)
		self.rebuild(new_parts[0]["_id"] if new_parts else None)
		self._emit()

	def add_composite(self):
		"""Search the saved composite items and the game's, and add all the parts of the one chosen."""
		lib = self.ctx.library
		presets = self.ctx.gamedata.item_presets if self.ctx.gamedata is not None else {}
		if not (lib and lib.entries) and not presets:
			QMessageBox.information(
				self, "Composite items",
				"There are no composite items yet. Save your own with More > Save these as my item, or set the SPT database folder in Settings for the game's.",
			)
			return
		for entry_id in self.ctx.pick("composite", False, self):
			parts = self._composite_parts(entry_id)
			if parts is not None:
				self._append(parts)

	def _composite_parts(self, entry_id):
		"""A copy (new ids) of the parts of a saved or vanilla composite item with this id, or None if it isn't one."""
		lib = self.ctx.library
		presets = self.ctx.gamedata.item_presets if self.ctx.gamedata is not None else {}
		if lib is not None and entry_id in lib.entries:
			return lib.parts_of(entry_id)
		if entry_id in presets:
			return library_module.preset_parts(presets[entry_id])
		return None

	def save_to_library(self):
		lib = self.ctx.library
		if lib is None or not self.parts:
			return
		first = P.roots(self.parts)[0] if self.parts else None
		suggestion = self._name(first.get("_tpl", "")) if first else "My item"
		name, ok = QInputDialog.getText(self, "Save as my item", "Name:", text=suggestion)
		if ok and name.strip():
			lib.add(name.strip(), self.parts)
