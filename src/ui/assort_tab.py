"""The trader tab: what a trader sells (assort.json) and which quests unlock or lock each offer
(questassort.json). Each offer is an item (maybe with mods), a price, a trader level and an optional quest lock."""

import copy
import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
	QCheckBox, QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidgetItem, QMessageBox,
	QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from core import parts as P
from schema import assort as A
from schema.common import Names, short
from schema.copying import with_new_ids
from ui.compiled.ui_assort_tab import Ui_AssortForm
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
WHEN = {"started": "when it is started", "success": "when it is completed", "fail": "when it is failed"}


class AssortTab(QWidget, Ui_AssortForm):
	"""The layout is ui/designer/assort_tab.ui: the trader box, the offer list with its buttons, the pane for an offer."""

	def __init__(self, assort_doc, locks_doc, gamedata=None, picker=None, library=None, quests=None, quests_document=None, parent=None):
		"""quests() gives the open quests' data and quests_document() their Document (to add an unlock reward to a quest)."""
		super().__init__(parent)
		self.setupUi(self)
		self.doc, self.locks = assort_doc, locks_doc
		self.gamedata, self.picker, self.library = gamedata, picker, library
		self.quests = quests or (lambda: {})
		self.quests_document = quests_document
		self._editing = False
		self.search.textChanged.connect(lambda _t: self.refresh())
		self.levelFilter.addItem("All levels", None)
		for level in A.LEVELS:
			self.levelFilter.addItem(f"Level {level}", level)
		self.levelFilter.currentIndexChanged.connect(lambda _i: self.refresh())
		self.list.currentItemChanged.connect(self._select)
		for button, slot in ((self.addButton, self.add_offer), (self.copyButton, self.copy_offer), (self.deleteButton, self.delete_offer)):
			button.clicked.connect(lambda _checked=False, slot=slot: slot())
		self.splitter.setSizes([420, 520])
		# which trader this assort is for: needed to link offers and quest rewards
		self.trader.addItem("(not set)", "")
		for trader_id, name in (gamedata.all_traders().items() if gamedata is not None else ()):
			self.trader.addItem(name, trader_id)
		self.trader.setCurrentIndex(0)
		self.trader.activated.connect(lambda _i: self._trader_changed())
		self.trader.lineEdit().editingFinished.connect(self._trader_changed)
		self._last_trader = self.trader_id
		self.watch(assort_doc, locks_doc)

	@property
	def trader_id(self):
		"""The chosen trader's id: a trader picked from the list, or a pasted id; '' if none."""
		text = self.trader.currentText().strip()
		index = self.trader.findText(text)
		if index >= 0:
			return self.trader.itemData(index)
		return text if re.fullmatch(r"[0-9a-fA-F]{24}", text) else ""

	def _trader_changed(self):
		"""The trader box was used. Only a different trader changes anything (the box also reports losing focus)."""
		if self.trader_id == self._last_trader:
			return
		self._last_trader = self.trader_id
		self.refresh(self.current_id())

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
		level = self.levelFilter.currentData()
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
			if level is not None and data.get("loyal_level_items", {}).get(offer_id) != level:
				continue
			item = QListWidgetItem(text)
			item.setData(ROLE, offer_id)
			self.list.addItem(item)
		self.list.blockSignals(False)
		problems = self._lock_problems()
		self.note.setText(f"{self.list.count()} of {total} offers." + (f" {len(problems)} quest unlock(s) to check." if problems else ""))
		self.note.setToolTip("\n".join(i.message for i in problems[:30]))
		row = next((i for i in range(self.list.count()) if self.list.item(i).data(ROLE) == keep), 0)
		if self.list.count():
			self.list.setCurrentRow(row)
		self._select(self.list.currentItem(), None)

	def current_id(self):
		item = self.list.currentItem()
		return item.data(ROLE) if item else None

	def _lock_problems(self):
		"""Quest locks that don't match the open quests' unlock rewards (nothing to say with no quests open)."""
		quests = self.quests()
		if not quests:
			return []
		return A.lock_problems(quests, self.locks.data, self.doc.data, self.trader_id or None)

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
		find.clicked.connect(lambda: self._add_price(offer_id, self._ctx().pick_item_ids(True, self)))
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
			self._set_lock(offer_id, lock_value, quest_id)

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
		unlock = self._unlock_row(offer_id, lock, quest)
		if unlock is not None:
			layout.addRow(unlock)
		return box

	def _set_lock(self, offer_id, lock_value, quest_id):
		def edit(d):
			for section in A.QUEST_LOCKS:
				(d.setdefault(section, {})).pop(offer_id, None)
			if lock_value and quest_id:
				d.setdefault(lock_value, {})[offer_id] = quest_id

		self._edit("Change quest lock", edit, doc=self.locks)
		self.refresh(offer_id)

	# --- the link between a quest lock and the quest's unlock reward ---------------------------------
	def _unlock_row(self, offer_id, lock, quest_id):
		"""What the open quests say about this offer: whether the locking quest gives the unlock (with a button to
		add it), or, for an offer with no lock, a quest that unlocks this item at this trader (with a button to lock to it)."""
		quests = self.quests()
		if not quests:
			return None
		tpl = A.offer_tpl(self.doc.data, offer_id)
		label = QLabel()
		label.setWordWrap(True)
		label.setStyleSheet("color: #808080;")
		button, action = None, None
		if lock in A.UNLOCKED_BY and quest_id:
			quest = quests.get(quest_id)
			if quest is None:
				label.setText("That quest isn't in the open quest file.")
			elif A.find_unlock(quest, lock, tpl, self.trader_id or None):
				label.setText(f'Linked quest "{quest.get("QuestName") or quest_id}" gives this unlock.')
			else:
				label.setText("The quest doesn't unlock this item yet.")
				button, action = "Add unlock to the quest", lambda: self._add_unlock(offer_id, lock, quest_id)
		elif not lock and self.trader_id:
			match = next(((q, s, r) for q, s, r, t in A.unlocks(quests, self.trader_id) if t == tpl and s in A.UNLOCKED_BY), None)
			if match is None:
				return None
			found_quest, status, _reward = match
			label.setText(f'The quest "{quests[found_quest].get("QuestName", found_quest)}" unlocks this item {WHEN[status]}.')
			button, action = "Lock this offer to it", lambda: self._set_lock(offer_id, status, found_quest)
		else:
			return None
		holder = QWidget()
		row = QHBoxLayout(holder)
		row.setContentsMargins(0, 0, 0, 0)
		row.addWidget(label, 1)
		if button:
			push = QPushButton(button)
			push.clicked.connect(lambda _c=False: action())
			row.addWidget(push)
		return holder

	def _add_unlock(self, offer_id, status, quest_id):
		"""Give the locking quest an unlock reward for this offer's item (same mods, trader and level)."""
		if not self.trader_id:
			QMessageBox.information(self, "Add unlock", "Choose the trader this assort is for first (at the top of this tab).")
			return
		doc = self.quests_document() if self.quests_document else None
		if doc is None or quest_id not in doc.data:
			return
		reward = A.unlock_reward(self.doc.data, offer_id, self.trader_id)
		timing = A.LOCK_TIMING[status]
		doc.change("Add unlock to quest", lambda quest: quest.setdefault("rewards", {}).setdefault(timing, []).append(reward), path=(quest_id,))
		self.refresh(offer_id)

	# --- add, copy, delete ------------------------------------------------------------------
	def add_offer(self):
		ctx = self._ctx()
		last = None
		for picked in ctx.pick("part", True, self):  # (items, and composite items, which are sold whole)
			parts = ctx.composite_parts(picked)
			items, barter, level = A.new_offer_from_parts(parts) if parts else A.new_offer(picked)
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
