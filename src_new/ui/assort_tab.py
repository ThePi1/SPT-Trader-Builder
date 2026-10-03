"""The trader tab: what a trader sells (assort.json) and which quests unlock or lock each offer
(questassort.json). Each offer is an item (maybe with mods), a price, a trader level and an optional quest lock."""

import copy

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
	QCheckBox, QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
	QMessageBox, QPushButton, QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from core import parts as P
from schema import assort as A
from schema.common import Names, short
from schema.copying import with_new_ids
from ui.forms import Context
from ui.parts_editor import PartsEditor
from ui.quest_outline import _clear

ROLE = Qt.ItemDataRole.UserRole
LOCK_LABELS = (
	(None, "Always for sale"),
	("started", "For sale once the quest is started"),
	("success", "For sale once the quest is completed"),
	("fail", "Removed if the quest is failed"),
)
MONEY_NAMES = {v: k.capitalize() for k, v in A.MONEY.items()}


class AssortTab(QWidget):
	def __init__(self, assort_doc, locks_doc, gamedata=None, picker=None, library=None, quests=None, parent=None):
		super().__init__(parent)
		self.doc, self.locks = assort_doc, locks_doc
		self.gamedata, self.picker, self.library = gamedata, picker, library
		self.quests = quests or (lambda: {})
		self._editing = False
		split = QSplitter(self)
		left = QWidget()
		column = QVBoxLayout(left)
		column.setContentsMargins(0, 0, 0, 0)
		self.search = QLineEdit()
		self.search.setPlaceholderText("Search the offers")
		self.search.textChanged.connect(lambda _t: self.refresh())
		column.addWidget(self.search)
		self.list = QListWidget()
		self.list.currentItemChanged.connect(self._select)
		column.addWidget(self.list, 1)
		self.note = QLabel()
		self.note.setStyleSheet("color: #808080;")
		column.addWidget(self.note)
		row = QHBoxLayout()
		for text, slot in (("Add offer...", self.add_offer), ("Copy", self.copy_offer), ("Delete", self.delete_offer)):
			button = QPushButton(text)
			button.clicked.connect(slot)
			row.addWidget(button)
		column.addLayout(row)
		split.addWidget(left)
		self.right = QWidget()
		self.right_layout = QVBoxLayout(self.right)
		split.addWidget(self.right)
		split.setSizes([420, 520])
		outer = QHBoxLayout(self)
		outer.setContentsMargins(0, 0, 0, 0)
		outer.addWidget(split)
		self.watch(assort_doc, locks_doc)

	# --- documents --------------------------------------------------------------------------
	def watch(self, assort_doc, locks_doc):
		self.doc, self.locks = assort_doc, locks_doc
		assort_doc.on_change(self._changed)
		locks_doc.on_change(self._changed)
		self.refresh()

	def _changed(self, _doc):
		if not self._editing:
			self.refresh()

	def _ctx(self):
		return Context(self.gamedata, Names(self.gamedata), self.picker, self.library)

	def _names(self):
		return self._ctx().names

	def _edit(self, label, fn, coalesce=None, doc=None):
		doc = doc or self.doc
		doc.watch(())
		self._editing = True
		try:
			fn(doc.data)
			doc.touch(label, coalesce=coalesce)
		finally:
			self._editing = False

	# --- the list ---------------------------------------------------------------------------
	def _lock_of(self, offer_id):
		for lock in A.QUEST_LOCKS:
			quest = (self.locks.data.get(lock) or {}).get(offer_id)
			if quest:
				return lock, quest
		return None, None

	def _price_text(self, offer_id):
		options = self.doc.data.get("barter_scheme", {}).get(offer_id) or []
		if not options or not options[0]:
			return "no price"
		names = self._names()
		parts = []
		for entry in options[0]:
			tpl = entry.get("_tpl", "")
			parts.append(f"{entry.get('count', 1):,}".replace(",", " ") + " " + MONEY_NAMES[tpl] if tpl in MONEY_NAMES else f"{entry.get('count', 1)}x {names.item(tpl)}")
		return " + ".join(parts) + (" (or other ways)" if len(options) > 1 else "")

	def refresh(self, select=None):
		keep = select or self.current_id()
		words = self.search.text().lower().split()
		self.list.blockSignals(True)
		self.list.clear()
		names = self._names()
		data = self.doc.data
		total = 0
		for offer_id in A.offer_ids(data):
			part = P.find(data["items"], offer_id)
			lock, quest = self._lock_of(offer_id)
			text = f"{names.item(part.get('_tpl', ''))}  -  {self._price_text(offer_id)}  -  level {data.get('loyal_level_items', {}).get(offer_id, '?')}"
			if lock:
				text += "  [quest]"
			total += 1
			if words and not all(w in text.lower() for w in words):
				continue
			item = QListWidgetItem(text)
			item.setData(ROLE, offer_id)
			self.list.addItem(item)
		self.list.blockSignals(False)
		self.note.setText(f"{self.list.count()} of {total} offers.")
		row = next((i for i in range(self.list.count()) if self.list.item(i).data(ROLE) == keep), 0)
		if self.list.count():
			self.list.setCurrentRow(row)
		self._select(self.list.currentItem(), None)

	def current_id(self):
		item = self.list.currentItem()
		return item.data(ROLE) if item else None

	# --- the offer --------------------------------------------------------------------------
	def _select(self, item, _previous):
		_clear(self.right_layout)
		if item is None:
			hint = QLabel("Press Add offer... to put an item on sale.")
			hint.setStyleSheet("color: #808080;")
			self.right_layout.addWidget(hint)
			self.right_layout.addStretch(1)
			return
		offer_id = item.data(ROLE)
		self._build_offer(offer_id)

	def _build_offer(self, offer_id):
		data = self.doc.data
		root = P.find(data["items"], offer_id)
		layout = self.right_layout
		layout.addWidget(QLabel(f"<b>{self._names().item(root.get('_tpl', ''))}</b>"))
		# the item and its mods
		offer_parts = copy.deepcopy(A.offer_parts(data, offer_id))  # edited here, written back through the document
		editor = PartsEditor(offer_parts, self._ctx())
		editor.changed.connect(lambda: self._parts_changed(offer_id, offer_parts))
		box = QGroupBox("Item")
		QVBoxLayout(box).addWidget(editor)
		layout.addWidget(box)
		# price
		layout.addWidget(self._price_box(offer_id))
		# the rest
		form = QFormLayout()
		level = QComboBox()
		for n in A.LEVELS:
			level.addItem(f"Level {n}", n)
		current = data.get("loyal_level_items", {}).get(offer_id, 1)
		if level.findData(current) < 0:
			level.addItem(f"Level {current}", current)
		level.setCurrentIndex(level.findData(current))
		level.activated.connect(lambda _i: self._edit("Change level", lambda d: d["loyal_level_items"].__setitem__(offer_id, level.currentData())))
		form.addRow("Trader level", level)
		upd = root.get("upd") or {}
		unlimited = QCheckBox()
		unlimited.setChecked(bool(upd.get("UnlimitedCount")))
		unlimited.clicked.connect(lambda c: self._edit("Change stock", lambda d: P.find(d["items"], offer_id).setdefault("upd", {}).__setitem__("UnlimitedCount", bool(c))))
		form.addRow("Unlimited stock", unlimited)
		for label, key in (("Stock", "StackObjectsCount"), ("Limit per player", "BuyRestrictionMax")):
			entry = QLineEdit("" if upd.get(key) is None else str(upd[key]))
			entry.textEdited.connect(lambda text, k=key: self._upd_number(offer_id, k, text, entry))
			form.addRow(label, entry)
		layout.addLayout(form)
		layout.addWidget(self._lock_box(offer_id))
		layout.addStretch(1)

	def _upd_number(self, offer_id, key, text, entry):
		text = text.strip()
		if text == "":
			self._edit("Change " + key, lambda d: (P.find(d["items"], offer_id).get("upd") or {}).pop(key, None), coalesce=(offer_id, key))
			entry.setStyleSheet("")
			return
		try:
			value = int(text)
			if value < 0:
				raise ValueError
		except ValueError:
			entry.setStyleSheet("border: 1px solid #c0392b; background: #fdecea;")
			return
		entry.setStyleSheet("")
		extra = {"BuyRestrictionCurrent": 0} if key == "BuyRestrictionMax" else {}
		self._edit(
			"Change " + key,
			lambda d: P.find(d["items"], offer_id).setdefault("upd", {}).update({key: value, **{k: v for k, v in extra.items() if k not in P.find(d["items"], offer_id)["upd"]}}),
			coalesce=(offer_id, key),
		)

	def _parts_changed(self, offer_id, offer_parts):
		def edit(data):
			gone = {p["_id"] for p in A.offer_parts(data, offer_id)}
			data["items"] = [p for p in data["items"] if p["_id"] not in gone] + [dict(p) for p in offer_parts]
			root = P.find(data["items"], offer_id)
			if root is not None:
				root["parentId"] = root["slotId"] = A.ROOT

		self._edit("Change item", edit)

	# --- price ------------------------------------------------------------------------------
	def _price_box(self, offer_id):
		box = QGroupBox("Price")
		layout = QVBoxLayout(box)
		options = self.doc.data.get("barter_scheme", {}).get(offer_id) or [[]]
		option = options[0]
		table = QTableWidget(len(option), 2)
		table.setHorizontalHeaderLabels(["Item", "How many"])
		table.verticalHeader().setVisible(False)
		table.horizontalHeader().setStretchLastSection(True)
		table.setMaximumHeight(130)
		names = self._names()
		for r, entry in enumerate(option):
			tpl = entry.get("_tpl", "")
			name = QTableWidgetItem(MONEY_NAMES.get(tpl) or names.item(tpl))
			name.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
			table.setItem(r, 0, name)
			table.setItem(r, 1, QTableWidgetItem(str(entry.get("count", 1))))
		table.itemChanged.connect(lambda cell: self._price_count(offer_id, cell))
		layout.addWidget(table)
		row = QHBoxLayout()
		for label, tpl in ((k.capitalize(), v) for k, v in A.MONEY.items()):
			button = QPushButton(label)
			button.clicked.connect(lambda _c=False, t=tpl: self._add_price(offer_id, [t]))
			row.addWidget(button)
		find = QPushButton("Item...")
		find.clicked.connect(lambda: self._add_price(offer_id, self.picker("item", True, self) if self.picker else []))
		remove = QPushButton("Remove")
		remove.clicked.connect(lambda: self._remove_price(offer_id, table.currentRow()))
		row.addWidget(find)
		row.addWidget(remove)
		layout.addLayout(row)
		if len(options) > 1:
			layout.addWidget(QLabel(f"This offer has {len(options) - 1} other way(s) to pay, kept as they are."))
		return box

	def _option(self, data, offer_id):
		"""The first way to pay for an offer (a list of {count, _tpl}), made if there is none."""
		options = data["barter_scheme"].setdefault(offer_id, [])
		if not options:
			options.append([])
		return options[0]

	def _price_count(self, offer_id, cell):
		if cell.column() != 1:
			return
		try:
			value = float(cell.text())
			value = int(value) if value == int(value) else value
			if value <= 0:
				raise ValueError
		except ValueError:
			return
		row = cell.row()
		self._edit("Change price", lambda d: self._option(d, offer_id)[row].__setitem__("count", value), coalesce=(offer_id, "price", row))

	def _add_price(self, offer_id, tpls):
		if not tpls:
			return

		def edit(d):
			option = self._option(d, offer_id)
			for tpl in tpls:
				existing = next((e for e in option if e.get("_tpl") == tpl), None)
				if existing is None:
					option.append({"count": 1, "_tpl": tpl})

		self._edit("Add to price", edit)
		self.refresh(offer_id)

	def _remove_price(self, offer_id, row):
		if row >= 0:
			self._edit("Remove from price", lambda d: self._option(d, offer_id).pop(row))
			self.refresh(offer_id)

	# --- quest lock -------------------------------------------------------------------------
	def _lock_box(self, offer_id):
		box = QGroupBox("Quest")
		layout = QFormLayout(box)
		lock, quest = self._lock_of(offer_id)
		combo = QComboBox()
		for value, label in LOCK_LABELS:
			combo.addItem(label, value)
		combo.setCurrentIndex(combo.findData(lock))
		quest_row = QHBoxLayout()
		entry = QLineEdit(quest or "")
		name = QLabel(self._ctx().name_of("quest", quest or ""))
		name.setStyleSheet("color: #808080;")
		find = QPushButton("Find...")
		for widget, stretch in ((entry, 1), (name, 0), (find, 0)):
			quest_row.addWidget(widget, stretch)

		def apply(lock_value, quest_id):
			def edit(d):
				for section in A.QUEST_LOCKS:
					(d.setdefault(section, {})).pop(offer_id, None)
				if lock_value and quest_id:
					d.setdefault(lock_value, {})[offer_id] = quest_id

			self._edit("Change quest lock", edit, doc=self.locks)
			self.refresh(offer_id)

		def pick():
			ids = self.picker("quest", False, self) if self.picker else []
			if ids:
				entry.setText(ids[0])
				apply(combo.currentData() or "success", ids[0])

		combo.activated.connect(lambda _i: apply(combo.currentData(), entry.text().strip()))
		entry.editingFinished.connect(lambda: apply(combo.currentData(), entry.text().strip()))
		find.clicked.connect(pick)
		layout.addRow("Availability", combo)
		layout.addRow("Quest", quest_row)
		return box

	# --- add, copy, delete ------------------------------------------------------------------
	def add_offer(self):
		ids = self.picker("item", True, self) if self.picker else []
		last = None
		for tpl in ids:
			items, barter, level = A.new_offer(tpl)
			self._edit("Add offer", lambda d, i=items, b=barter, l=level: A.add_offer(d, i, b, l))
			last = items[0]["_id"]
		if last:
			self.refresh(last)

	def copy_offer(self):
		offer_id = self.current_id()
		if offer_id is None:
			return
		holder = {}

		def edit(d):
			parts = with_new_ids(A.offer_parts(d, offer_id))
			new_root = parts[0]["_id"]
			d["items"].extend(parts)
			d["barter_scheme"][new_root] = with_new_ids(d["barter_scheme"].get(offer_id, [[]]))
			d["loyal_level_items"][new_root] = d["loyal_level_items"].get(offer_id, 1)
			holder["id"] = new_root

		self._edit("Copy offer", edit)
		self.refresh(holder.get("id"))

	def delete_offer(self):
		offer_id = self.current_id()
		if offer_id is None:
			return
		if QMessageBox.question(self, "Delete offer", "Delete this offer?") != QMessageBox.StandardButton.Yes:
			return
		self._edit("Delete offer", lambda d: A.remove_offer(d, offer_id))
		self._edit("Remove quest lock", lambda d: [d.get(s, {}).pop(offer_id, None) for s in A.QUEST_LOCKS], doc=self.locks)
		self.refresh()
