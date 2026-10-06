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
	"""offer=True is a trader offer: one main item that can be swapped (New root item...), and the items added go onto it."""

	changed = Signal()

	def __init__(self, parts, ctx, parent=None, offer=False):
		super().__init__(parent)
		self.parts, self.ctx, self.offer = parts, ctx, offer
		self._loading = False
		self.read_only = False
		layout = QVBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		bar = QHBoxLayout()
		bar.setSpacing(3)
		self.add_button = QPushButton("Add child item..." if offer else "Add item...")
		self.add_button.setToolTip(
			"Add an item onto the selected part (a mod, ammo); with nothing selected it goes on the main item." if offer
			else "Add an item. With a part selected it is attached to it (a mod, ammo)."
		)
		self.add_button.clicked.connect(self.add_item)
		self.root_button = QPushButton("New root item...")
		self.root_button.setToolTip("Swap the main item for another item, or for a composite item. The price, level, stock and quest lock stay; mods that fit the new item stay, and a composite item brings its own.")
		self.root_button.clicked.connect(self.swap_root)
		self.remove_button = QPushButton("Remove")
		self.remove_button.clicked.connect(self.remove_selected)
		more = self.more_button = QToolButton()
		more.setText("More")
		more.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
		menu = QMenu(more)
		if not offer:  # (a composite item has a main item of its own: a trader offer has one main item, which New root item... swaps for it)
			menu.addAction("Add a composite item...", self.add_composite)
			menu.addSeparator()
		menu.addAction("Save these as my item...", self.save_to_library)
		more.setMenu(menu)
		for widget in (self.add_button, self.root_button if offer else None, self.remove_button, more):  # (only an offer has a main item to swap)
			if widget is not None:
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
		for widget in (self.add_button, self.root_button, self.more_button, self.slot, self.stack, self.found):
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
		ids = self.ctx.pick("item" if self.offer else "part", True, self)  # (a trader offer takes plain items: its main item is the one thing it is)
		parent = self._current()
		if parent is None and self.offer:
			parent = next(iter(P.roots(self.parts)), None)  # (nothing selected: onto the main item)
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

	def swap_root(self):
		"""Replace the main item with another one (or with a composite item: its main item and all its mods). The main part
		keeps its id, stack size and other fields. For an item, the mods stay where the new item has a slot for them and
		the ones that don't fit are removed (after asking)."""
		roots = P.roots(self.parts)
		if len(roots) != 1:
			QMessageBox.information(self, "New root item", "This has more than one main item, so there isn't one to swap.")
			return
		picked = self.ctx.pick("part", False, self)  # (items, and composite items)
		root = roots[0]
		if not picked:
			return
		built = self._composite_parts(picked[0])
		if built is not None:
			return self._swap_root_for(root, built)
		if picked[0] == root.get("_tpl"):
			QMessageBox.information(self, "New root item", f"{self._name(picked[0])} is already the main item, so nothing was changed.")
			return
		tpl = picked[0]
		loose = [
			child for child in P.children(self.parts, root["_id"])
			if tpl in self.items and P.fits(self.items, tpl, child.get("slotId", ""), child.get("_tpl", "")) is False
		]
		if loose:
			names = ", ".join(self._name(child.get("_tpl", "")) for child in loose[:5]) + (" ..." if len(loose) > 5 else "")
			answer = QMessageBox.question(
				self, "New root item",
				f"{len(loose)} part{'' if len(loose) == 1 else 's'} (and anything on {'it' if len(loose) == 1 else 'them'}) don't fit {self._name(tpl)} and will be removed: {names}. Continue?",
			)
			if answer != QMessageBox.StandardButton.Yes:
				return
			for child in loose:
				P.remove_part(self.parts, child["_id"])
		root["_tpl"] = tpl
		self.rebuild(root["_id"])
		self._emit()

	def _swap_root_for(self, root, built):
		"""Make the main part the main item of a composite item, with all its mods (the mods it had are replaced)."""
		main = next(iter(P.roots(built)), None)
		if main is None:
			return
		inside, grew = {main["_id"]}, True
		while grew:  # (the main item and everything attached to it: a composite can hold other main parts too)
			grew = False
			for part in built:
				if part.get("parentId") in inside and part["_id"] not in inside:
					inside.add(part["_id"])
					grew = True
		old = P.children(self.parts, root["_id"])
		if old and QMessageBox.question(
			self, "New root item",
			f"The composite item replaces the main item and its {len(old)} part{'' if len(old) == 1 else 's'} (with what is on {'it' if len(old) == 1 else 'them'}). Continue?",
		) != QMessageBox.StandardButton.Yes:
			return
		for child in old:
			P.remove_part(self.parts, child["_id"])
		root["_tpl"] = main["_tpl"]
		for key, value in (main.get("upd") or {}).items():
			root.setdefault("upd", {}).setdefault(key, value)  # (what the part already has stays)
		for part in built:
			if part["_id"] in inside and part["_id"] != main["_id"]:
				if part.get("parentId") == main["_id"]:
					part["parentId"] = root["_id"]
				self.parts.append(part)
		self.rebuild(root["_id"])
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
