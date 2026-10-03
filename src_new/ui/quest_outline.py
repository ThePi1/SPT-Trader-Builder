"""The quest outline: every quest of a file as a tree (quest > tasks and rewards by timing,
a Counter's subtasks under it), and the form for whichever node is selected.

All changes go through the Document so they can be undone. The tree is rebuilt when the data
changes under it (add, delete, undo); it only refreshes its labels while a form is being typed in.
"""

import json

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import (
	QComboBox, QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QMenu, QMessageBox, QPlainTextEdit, QPushButton,
	QTreeWidgetItem, QVBoxLayout, QWidget,
)

from core.documents import duplicate, move
from core.ids import new_id
from schema import choices, copying, registry
from schema import locale as L
from schema.common import Names
from schema.fields import get_path
from schema.quest import QUEST, make_quest
from schema import validate
from schema.issues import ERROR
from ui.compiled.ui_quest_outline import Ui_OutlineForm
from ui.problems import ERROR_COLOR, WARNING_COLOR, ProblemsPanel, node_path
from ui.forms import Context, FormWidget
from ui.text_panels import QuestTextPanel, TaskTextPanel, task_has_text

ROLE = Qt.ItemDataRole.UserRole
TASK_TIMINGS = tuple(t for t, _k in choices.TASK_TIMINGS)
REWARD_TIMINGS = tuple(t for t, _k in choices.REWARD_TIMINGS)


def _get(data, path):
	for part in path:
		data = data[part]
	return data


class Address:
	"""Where a tree item's data is. kind: quest, group (a list of tasks or rewards), task, subtask, reward."""

	def __init__(self, kind, path, group=None, timing=None):
		self.kind, self.path, self.group, self.timing = kind, tuple(path), group, timing

	def key(self):
		return (self.kind, self.path)


def task_path(qid, timing):
	return (qid, "conditions", choices.TASK_LIST_KEY[timing])


def reward_path(qid, timing):
	return (qid, "rewards", timing)


class QuestOutline(QWidget, Ui_OutlineForm):
	export_requested = Signal()  # the context menu's "Export selected quests..."

	def __init__(self, gamedata=None, settings=None, parent=None):
		super().__init__(parent)
		self.gamedata, self.settings, self.doc = gamedata, settings, None
		self.library = None  # the user's saved composite items
		self.locale = None  # the open locale Document, for the text boxes
		self.sources = {}  # quest id -> the file it was imported from, shown next to the quest
		self.picker = None  # (ref kind, multi, parent) -> [ids]: the window's search dialog
		self._editing = False
		self.setupUi(self)  # (the layout: the buttons, tree, form pane and JSON view are in ui/designer/quest_outline.ui)
		self.add_menu = QMenu(self.add_button)
		self.add_menu.aboutToShow.connect(self._fill_add_menu)
		self.add_button.setMenu(self.add_menu)
		for button, slot in (
			(self.new_quest_button, self.add_quest), (self.copy_button, self.copy_selected),
			(self.delete_button, self.delete_selected), (self.up_button, lambda: self.move_selected(-1)),
			(self.down_button, lambda: self.move_selected(1)),
		):
			button.clicked.connect(lambda _checked=False, slot=slot: slot())
		self.tree.currentItemChanged.connect(self._selected)
		self.search.textChanged.connect(lambda _text: self.apply_filter())
		self.up_button.setToolTip("Move the selected quest, task, subtask or reward up")
		self.down_button.setToolTip("Move the selected quest, task, subtask or reward down")
		self.expandAllButton.clicked.connect(lambda _checked=False: self.expand_all())
		self.collapseAllButton.clicked.connect(lambda _checked=False: self.collapse_all())
		self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
		self.tree.customContextMenuRequested.connect(self._context_menu)
		self.problems = ProblemsPanel(settings)  # (under the tree)
		self.problems.activated.connect(self._jump)
		self.leftLayout.addWidget(self.problems)
		self._check_timer = QTimer(self)
		self._check_timer.setSingleShot(True)
		self._check_timer.setInterval(400)
		self._check_timer.timeout.connect(self.check)
		self.json_view.setVisible(bool(settings and settings.show_json_preview))  # what is selected, as it will be saved
		self.rightSplitter.setStretchFactor(0, 3)
		self.rightSplitter.setStretchFactor(1, 1)
		self.rightSplitter.setSizes([560, 200])
		self.splitter.setSizes([360, 505])  # (puts the divider where it was before the layout moved to the .ui file)
		self._show_hint("Add a quest to begin, or open a quest file.")

	# --- the document -----------------------------------------------------------------------
	def set_document(self, doc):
		self.doc = doc
		doc.on_change(self._doc_changed)
		self.rebuild()
		self.check()

	def _ctx(self, quest_id=None, task_id=None):
		"""What the forms need. With a quest, the other tasks of that quest (not task_id) are offered for "Only show after"."""
		quest_names = {q: v.get("QuestName", "") for q, v in self.doc.data.items() if isinstance(v, dict)} if self.doc else {}
		names = Names(self.gamedata, quest_names)
		return Context(self.gamedata, names, self.picker, self.library, self._task_choices(quest_id, task_id, names))

	def _task_choices(self, quest_id, skip_id, names):
		quest = self.doc.data.get(quest_id) if self.doc and quest_id else None
		if not isinstance(quest, dict):
			return []
		found = []
		for timing, list_key in choices.TASK_LIST_KEY.items():
			for task in (quest.get("conditions") or {}).get(list_key, []) or []:
				if not isinstance(task, dict) or not task.get("id") or task["id"] == skip_id:
					continue
				spec = registry.spec_of(task, "task")
				try:
					words = spec.summary(task, names) if spec.summary else spec.label
				except (KeyError, TypeError, IndexError):
					words = spec.label
				found.append((task["id"], f"{words} ({timing})"))
		return found

	def _names(self):
		return self._ctx().names

	def _doc_changed(self, _doc):
		if self._editing:
			self._refresh_labels()
		else:
			self.rebuild()
		self._update_json()
		self.check_soon()

	def apply_settings(self):
		"""Settings changed: show or hide the JSON, and rebuild the open form (it may show more or fewer fields)."""
		self.json_view.setVisible(bool(self.settings and self.settings.show_json_preview))
		item = self.tree.currentItem()
		if item is not None:
			self._selected(item, None)
		self._update_json()
		self.check()  # (the Problems list may now show more or fewer)

	def _update_json(self):
		"""The selected node as JSON (when the preview is on)."""
		if not self.json_view.isVisible() or self.doc is None:
			return
		address = self._current()
		try:
			text = json.dumps(_get(self.doc.data, address.path), indent=2, ensure_ascii=False) if address else ""
		except (KeyError, IndexError, TypeError):
			text = ""
		if text != self.json_view.toPlainText():
			bar = self.json_view.verticalScrollBar().value()
			self.json_view.setPlainText(text)
			self.json_view.verticalScrollBar().setValue(bar)

	def check_soon(self):
		self._check_timer.start()

	def check(self):
		"""Look for problems in the quests (and their text) and show them in the list and on the tree."""
		self._check_timer.stop()
		if self.doc is None:
			return
		locale = self.locale.data if self.locale is not None else None
		issues = validate.validate_quests(self.doc.data, locale, self.gamedata)
		names = self._names()
		self.problems.show_issues(issues, lambda path: self._where(path, names))
		worst = {}
		for issue in issues:
			key = node_path(issue.path) if issue.path else ()
			if worst.get(key) != ERROR:
				worst[key] = issue.level
		for item in self._walk():
			level = worst.get(item.data(0, ROLE).path)
			item.setForeground(0, ERROR_COLOR if level == ERROR else WARNING_COLOR if level else self.tree.palette().text())
		self.issues = issues

	def _where(self, path, names):
		"""Words for where an issue is: the quest's name, and the task or reward."""
		if not path or path[0] not in self.doc.data:
			return "Text" if path else ""
		quest = self.doc.data[path[0]]
		name = quest.get("QuestName") or "(unnamed quest)" if isinstance(quest, dict) else str(path[0])
		node = node_path(path)
		try:
			data = _get(self.doc.data, node)
			if len(node) == 1:
				spec, summary = QUEST, name
			else:
				kind = "subtask" if len(node) == 7 else "task" if node[1] == "conditions" else "reward"
				spec = registry.spec_of(data, kind)
				summary = f"{name} > {spec.summary(data, names)}"
		except (KeyError, IndexError, TypeError):
			return name
		field = spec.field(str(path[len(node)])) if len(path) > len(node) else None
		return f"{summary} > {field.label}" if field else summary

	def _jump(self, path):
		for item in self._walk():
			if item.data(0, ROLE).path == tuple(path) and item.data(0, ROLE).kind != "group":
				self.tree.setCurrentItem(item)
				return

	# --- building the tree ------------------------------------------------------------------
	def _add_item(self, parent, text, address, bold=False):
		item = QTreeWidgetItem([text])
		item.setData(0, ROLE, address)
		if bold:
			font = item.font(0)
			font.setBold(True)
			item.setFont(0, font)
		(parent.addChild if isinstance(parent, QTreeWidgetItem) else parent.addTopLevelItem)(item)
		return item

	def _label(self, address):
		data = _get(self.doc.data, address.path)
		names = self._names()
		if address.kind == "quest":
			source = self.sources.get(address.path[0])
			return QUEST.summary(data, names) + (f"  [{source}]" if source else "")
		if address.kind == "group":
			return f"{address.timing} ({len(data)})" if address.group != "rewards" else "Rewards"
		return registry.spec_of(data, address.kind).summary(data, names)

	def expand_all(self):
		self.tree.expandAll()

	def collapse_all(self):
		"""Fold every quest up to its own row (the open item stays: it moves to its quest if it was inside one)."""
		current = self.tree.currentItem()
		self.tree.collapseAll()
		if current is not None:
			top = current
			while top.parent() is not None:
				top = top.parent()
			if top is not current:
				self.tree.setCurrentItem(top)

	def rebuild(self):
		keep = self._current_key()
		self.tree.blockSignals(True)
		before = {item.data(0, ROLE).key(): item.isExpanded() for item in self._walk()}  # (what was open and shut)
		self.tree.clear()
		if self.doc is not None:
			for qid, quest in self.doc.data.items():
				if not isinstance(quest, dict):
					continue
				self._build_quest(qid, quest)
		for item in self._walk():  # (new things start open; what was shut stays shut)
			item.setExpanded(before.get(item.data(0, ROLE).key(), True))
		self.tree.blockSignals(False)
		self.apply_filter()
		if not self._select_key(keep):
			if self.tree.topLevelItemCount():
				self.tree.setCurrentItem(self.tree.topLevelItem(0))
			else:
				self._show_hint("Add a quest to begin, or open a quest file.")
		self._update_move_buttons()

	def _build_quest(self, qid, quest):
		root = self._add_item(self.tree, "", Address("quest", (qid,)), bold=True)
		root.setText(0, self._label(root.data(0, ROLE)))
		tasks = (quest.get("conditions") or {})
		for timing in TASK_TIMINGS:
			path = task_path(qid, timing)
			if choices.TASK_LIST_KEY[timing] not in tasks:
				continue
			group = self._add_item(root, "", Address("group", path, "task", timing), bold=True)
			group.setText(0, self._label(group.data(0, ROLE)))
			for i, task in enumerate(tasks[choices.TASK_LIST_KEY[timing]] or []):
				node = self._add_item(group, "", Address("task", path + (i,), "task", timing))
				node.setText(0, self._label(node.data(0, ROLE)))
				counter = task.get("counter") if isinstance(task, dict) else None
				if isinstance(counter, dict) and isinstance(counter.get("conditions"), list):
					for j in range(len(counter["conditions"])):
						sub = self._add_item(node, "", Address("subtask", path + (i, "counter", "conditions", j), "subtask", timing))
						sub.setText(0, self._label(sub.data(0, ROLE)))
		rewards_item = self._add_item(root, "Rewards", Address("group", (qid, "rewards"), "rewards"), bold=True)
		rewards = quest.get("rewards") or {}
		for timing in REWARD_TIMINGS:
			if timing not in rewards:
				continue
			path = reward_path(qid, timing)
			group = self._add_item(rewards_item, "", Address("group", path, "reward", timing), bold=True)
			group.setText(0, self._label(group.data(0, ROLE)))
			for i in range(len(rewards[timing] or [])):
				node = self._add_item(group, "", Address("reward", path + (i,), "reward", timing))
				node.setText(0, self._label(node.data(0, ROLE)))

	def selected_quest_ids(self):
		"""The ids of the quests that are selected, or that have something selected inside them, in tree order."""
		chosen = {item.data(0, ROLE).path[0] for item in self.tree.selectedItems()}
		return [q for q in (self.doc.data if self.doc else {}) if q in chosen]

	def _context_actions(self, item):
		"""[(text, what to do)] for the right-click menu on this tree item."""
		actions = []
		if item is not None:
			quest_id = item.data(0, ROLE).path[0]
			if quest_id not in self.selected_quest_ids():
				self.tree.setCurrentItem(item)
				self.tree.clearSelection()
				item.setSelected(True)
			count = len(self.selected_quest_ids())
			actions.append((f"Export {count} selected quests..." if count > 1 else "Export this quest...", self.export_requested.emit))
			source = self.sources.get(quest_id)
			if source:
				actions.append((f"Remove the quests imported from {source}", lambda source=source: self.remove_from_source(source)))
		return actions + [("Expand all", self.expand_all), ("Collapse all", self.collapse_all)]

	def _context_menu(self, pos):
		actions = self._context_actions(self.tree.itemAt(pos))
		if not actions:
			return
		menu = QMenu(self.tree)
		for text, slot in actions:
			menu.addAction(text).triggered.connect(lambda _checked=False, slot=slot: slot())
		menu.exec(self.tree.viewport().mapToGlobal(pos))

	def remove_from_source(self, source):
		"""Delete the quests that were imported from this file (after asking). Their text stays in the locale."""
		ids = [q for q, file in self.sources.items() if file == source and self.doc and q in self.doc.data]
		if not ids:
			return 0
		answer = QMessageBox.question(
			self, "Remove quests",
			f"Remove the {len(ids)} quest{'' if len(ids) == 1 else 's'} imported from {source}?\n\nTheir text stays in the locale file.",
		)
		if answer != QMessageBox.StandardButton.Yes:
			return 0
		self.doc.change(f"Remove quests from {source}", lambda data: [data.pop(q, None) for q in ids])
		for q in ids:
			self.sources.pop(q, None)
		self.set_sources(self.sources)
		return len(ids)

	def apply_filter(self):
		"""Show only the quests whose name (or the file they were imported from) has all the words in the search box."""
		words = self.search.text().lower().split()
		current = self.tree.currentItem()
		first_shown = None
		for i in range(self.tree.topLevelItemCount()):
			item = self.tree.topLevelItem(i)
			qid = item.data(0, ROLE).path[0]
			quest = self.doc.data.get(qid) if self.doc else None
			text = f"{(quest or {}).get('QuestName', '')} {self.sources.get(qid, '')}".lower()
			hidden = bool(words) and not all(word in text for word in words)
			item.setHidden(hidden)
			if hidden:
				for part in self._walk(item):
					part.setSelected(False)
			elif first_shown is None:
				first_shown = item
		if current is not None:
			top = current
			while top.parent() is not None:
				top = top.parent()
			if top.isHidden():
				self.tree.setCurrentItem(first_shown)
				if first_shown is None:
					self._show_hint("No quest matches the search.")
		self._update_move_buttons()

	def set_sources(self, sources):
		"""Show which file each imported quest came from (quest id -> file name)."""
		self.sources = sources
		self._refresh_labels()

	def _walk(self, item=None):
		items = [item] if item is not None else [self.tree.topLevelItem(i) for i in range(self.tree.topLevelItemCount())]
		for it in items:
			yield it
			yield from self._walk_children(it)

	def _walk_children(self, item):
		for i in range(item.childCount()):
			child = item.child(i)
			yield child
			yield from self._walk_children(child)

	def _refresh_labels(self):
		for item in self._walk():
			address = item.data(0, ROLE)
			if address.group != "rewards" or address.kind != "group":
				try:
					item.setText(0, self._label(address))
				except (KeyError, IndexError, TypeError):
					pass

	def _current(self):
		item = self.tree.currentItem()
		return item.data(0, ROLE) if item is not None else None

	def _current_key(self):
		address = self._current()
		return address.key() if address else None

	def _select_key(self, key):
		if key is None:
			return False
		for item in self._walk():
			if item.data(0, ROLE).key() == key:
				self.tree.setCurrentItem(item)
				self._selected(item, None)
				return True
		return False

	# --- the property pane ------------------------------------------------------------------
	def _clear_pane(self):
		_clear(self.pane_layout)

	def _show_hint(self, text):
		self._clear_pane()
		label = QLabel(text)
		label.setStyleSheet("color: #808080;")
		label.setWordWrap(True)
		self.pane_layout.addWidget(label)
		self.pane_layout.addStretch(1)

	def _selected(self, item, _previous):
		self._update_json()
		self._update_move_buttons()
		self._clear_pane()
		if item is None:
			return self._show_hint("Add a quest to begin, or open a quest file.")
		address = item.data(0, ROLE)
		if address.kind == "group":
			return self._show_hint("Press Add to put a " + ("task" if address.group == "task" else "reward") + " here." if address.group != "rewards" else "The rewards of this quest, by when they are given.")
		data = _get(self.doc.data, address.path)
		spec = QUEST if address.kind == "quest" else registry.spec_of(data, address.kind)
		qpath = address.path[:1]
		title = QLabel(f"<b>{spec.label}</b>")
		title.setToolTip(spec.note)
		self.pane_layout.addWidget(title)
		if spec.note and spec.kind not in ("quest",) and not spec.fields and address.kind != "quest":
			note = QLabel(spec.note)
			note.setWordWrap(True)
			note.setStyleSheet("color: #808080;")
			self.pane_layout.addWidget(note)
		if address.kind in ("task", "reward") and len(spec.timings) > 1:
			self.pane_layout.addLayout(self._timing_row(address, spec))
		own_id = data.get("id") if isinstance(data, dict) else None
		form = FormWidget(spec, self._ctx(qpath[0] if qpath else None, own_id), show_advanced=bool(self.settings and self.settings.show_all_fields))
		form.bind(data)
		self.doc.watch(qpath)
		form.field_changed.connect(lambda key, a=address: self._form_edited(a, key))
		self.pane_layout.addWidget(form)
		if self.locale is not None:
			if address.kind == "quest":
				self.pane_layout.addWidget(QuestTextPanel(self.locale, data))
			elif address.kind == "task" and task_has_text(address.timing) and data.get("id"):
				self.pane_layout.addWidget(TaskTextPanel(self.locale, data["id"], address.timing))
		json_button = QPushButton("Edit as JSON...")
		json_button.clicked.connect(lambda: self.edit_json(address))
		row = QHBoxLayout()
		row.addWidget(json_button)
		row.addStretch(1)
		self.pane_layout.addLayout(row)
		self.pane_layout.addStretch(1)

	def _timing_row(self, address, spec):
		row = QHBoxLayout()
		row.addWidget(QLabel("When"))
		combo = QComboBox()
		combo.addItems(spec.timings)
		if address.timing not in spec.timings:
			combo.addItem(address.timing)
		combo.setCurrentText(address.timing)
		combo.activated.connect(lambda _i: self.retime(address, combo.currentText()))
		row.addWidget(combo)
		row.addStretch(1)
		return row

	def _form_edited(self, address, key):
		self._editing = True
		try:
			self.doc.touch(f"Edit {key}", coalesce=(address.path, key))
		finally:
			self._editing = False

	def edit_json(self, address):
		data = _get(self.doc.data, address.path)
		dialog = JsonDialog(data, self)
		if dialog.exec() and dialog.result_value is not None:
			value = dialog.result_value
			self.doc.change("Edit as JSON", lambda node: _replace(node, value), path=address.path)

	# --- adding, copying, deleting, moving --------------------------------------------------
	def _fill_add_menu(self):
		self.add_menu.clear()
		address = self._current()
		if address is None:
			return
		if self._counter_path(address) is not None:
			sub = self.add_menu.addMenu("Subtask (in this objective)")
			for spec in registry.kinds("subtask"):
				sub.addAction(spec.label, lambda s=spec: self.add_item("subtask", s.kind))
		for group, heading in (("task", "Task"), ("reward", "Reward")):
			menu = self.add_menu.addMenu(heading)
			common = registry.kinds(group, common_only=True)
			for spec in common:
				menu.addAction(spec.label, lambda g=group, s=spec: self.add_item(g, s.kind))
			uncommon = [s for s in registry.kinds(group) if not s.common]
			if uncommon:
				more = menu.addMenu("Less common")
				for spec in uncommon:
					more.addAction(spec.label, lambda g=group, s=spec: self.add_item(g, s.kind))

	def _counter_path(self, address):
		"""The path of the Counter task's subtask list if the address is that Counter or one of its subtasks."""
		if address.kind == "subtask":
			return address.path[:-1]
		if address.kind == "task":
			task = _get(self.doc.data, address.path)
			if isinstance(task, dict) and task.get("conditionType") == "CounterCreator":
				return address.path + ("counter", "conditions")
		return None

	def add_quest(self):
		if self.doc is None:
			return
		defaults = {}
		trader = ""
		if self.settings is not None:
			defaults = {"image": self.settings.quest_icon, "side": self.settings.side}
			trader = self.settings.trader
		if not trader:
			known = choices.get("traders", self.gamedata)
			trader = known[0][0] if known else ""
		quest = make_quest(name="New quest", trader_id=trader, defaults=defaults)
		self.doc.change("Add quest", lambda data: data.__setitem__(quest["_id"], quest))
		self._select_key(("quest", (quest["_id"],)))

	def _quest_path(self):
		address = self._current()
		return address.path[:1] if address else None

	def add_item(self, group, kind):
		address = self._current()
		if address is None:
			return
		qid = address.path[0]
		item = registry.new_item(group, kind)
		spec = registry.spec_for(group, kind)
		if group == "subtask":
			path = self._counter_path(address)
			self.doc.change("Add subtask", lambda items: items.append(item), path=path)
			return self._select_key(("subtask", path + (len(_get(self.doc.data, path)) - 1,)))
		timing = address.timing if address.group == group and address.timing in spec.timings else spec.timings[0]
		path = task_path(qid, timing) if group == "task" else reward_path(qid, timing)
		container = self.doc.data[qid].get("conditions" if group == "task" else "rewards")
		key = path[-1]

		def edit(quest):
			quest.setdefault("conditions" if group == "task" else "rewards", {}).setdefault(key, []).append(item)

		self.doc.change(f"Add {spec.label.lower()}", edit, path=(qid,))
		self._select_key((group, path + (len(_get(self.doc.data, path)) - 1,)))

	def copy_selected(self):
		address = self._current()
		if address is None or address.kind == "group":
			return
		if address.kind == "quest":
			original = _get(self.doc.data, address.path)
			quest, id_map = copying.copy_quest(original)
			self._copy_text(original, quest, id_map)
			quest["QuestName"] = f"{quest.get('QuestName', 'Quest')} (copy)"
			self.doc.change("Copy quest", lambda data: data.__setitem__(quest["_id"], quest))
			return self._select_key(("quest", (quest["_id"],)))
		list_path, index = address.path[:-1], address.path[-1]
		self.doc.change("Copy", lambda items: duplicate(items, index, fresh=lambda c: self._renew(c)), path=list_path)
		self._select_key((address.kind, list_path + (index + 1,)))

	def _copy_text(self, original, copy_, id_map):
		"""Give the copy of a quest the same text as the original, under its new keys."""
		if self.locale is None:
			return
		old_id, new_id_ = original.get("_id", ""), copy_["_id"]
		for key, text in list(self.locale.data.items()):
			parts = L.split_quest_key(key)
			if parts and parts[0] == old_id:
				self.locale.set_value("Copy text", (L.quest_key(new_id_, parts[1]),), text)
			elif key in id_map and key != old_id:
				self.locale.set_value("Copy text", (id_map[key],), text)

	def _renew(self, clone):
		new = copying.with_new_ids(clone)
		clone.clear()
		clone.update(new)

	def delete_selected(self):
		address = self._current()
		if address is None or address.kind == "group":
			return
		if address.kind == "quest":
			name = _get(self.doc.data, address.path).get("QuestName", "this quest")
			if QMessageBox.question(self, "Delete quest", f"Delete the quest \"{name}\"?") != QMessageBox.StandardButton.Yes:
				return
			self.doc.change("Delete quest", lambda data: data.pop(address.path[0], None))
			return
		list_path, index = address.path[:-1], address.path[-1]
		self.doc.change("Delete", lambda items: items.pop(index), path=list_path)

	def _visible_quest_ids(self):
		"""The ids of the quests shown in the tree (the search may hide some), in order."""
		return [
			self.tree.topLevelItem(i).data(0, ROLE).path[0] for i in range(self.tree.topLevelItemCount())
			if not self.tree.topLevelItem(i).isHidden()
		]

	def _can_move(self, address):
		"""(can move up, can move down) for the selected node: a quest among the shown quests, or an item in its list."""
		if address is None or address.kind == "group" or self.doc is None:
			return False, False
		try:
			if address.kind == "quest":
				shown = self._visible_quest_ids()
				if address.path[0] not in shown:
					return False, False
				i = shown.index(address.path[0])
				return i > 0, i < len(shown) - 1
			items = _get(self.doc.data, address.path[:-1])
			return address.path[-1] > 0, address.path[-1] < len(items) - 1
		except (KeyError, IndexError, TypeError):
			return False, False

	def _update_move_buttons(self):
		up, down = self._can_move(self._current())
		self.up_button.setEnabled(up)
		self.down_button.setEnabled(down)

	def _move_quest(self, quest_id, offset):
		"""Move a quest past the next quest that is shown (so it works while the search hides some)."""
		shown = self._visible_quest_ids()
		if quest_id not in shown or not 0 <= shown.index(quest_id) + offset < len(shown):
			return
		neighbour = shown[shown.index(quest_id) + offset]
		order = [q for q in self.doc.data if q != quest_id]
		order.insert(order.index(neighbour) + (1 if offset > 0 else 0), quest_id)

		def reorder(data):
			items = {q: data[q] for q in order}
			data.clear()
			data.update(items)

		self.doc.change("Move quest", reorder)
		self._select_key(("quest", (quest_id,)))

	def move_selected(self, offset):
		address = self._current()
		if address is None or address.kind == "group":
			return
		if address.kind == "quest":
			return self._move_quest(address.path[0], offset)
		list_path, index = address.path[:-1], address.path[-1]
		result = []
		self.doc.change("Move", lambda items: result.append(move(items, index, offset)), path=list_path)
		self._select_key((address.kind, list_path + (result[0],)))

	def retime(self, address, timing):
		qid = address.path[0]
		item = _get(self.doc.data, address.path)
		new_path = task_path(qid, timing) if address.kind == "task" else reward_path(qid, timing)
		old_key = address.path[-2]

		def edit(quest):
			section = "conditions" if address.kind == "task" else "rewards"
			quest[section][old_key].remove(item) if item in quest[section][old_key] else None
			quest[section].setdefault(new_path[-1], []).append(item)

		self.doc.change("Change when", edit, path=(qid,))
		self._select_key((address.kind, new_path + (len(_get(self.doc.data, new_path)) - 1,)))


def _clear(layout):
	while layout.count():
		child = layout.takeAt(0)
		widget = child.widget()
		if widget is not None:
			widget.hide()  # (a visible widget that loses its parent becomes a window, and flashes)
			widget.setParent(None)
			widget.deleteLater()
		elif child.layout() is not None:
			_clear(child.layout())


def _replace(node, value):
	if isinstance(node, dict):
		node.clear()
		node.update(value)
	else:
		node[:] = value


class JsonDialog(QDialog):
	"""Edit one item as JSON text. OK is refused while the text isn't valid JSON of the same shape.
	With read_only the text can only be looked at (and copied), and the window has just a Close button."""

	def __init__(self, data, parent=None, read_only=False):
		super().__init__(parent)
		self.setWindowTitle("View as JSON" if read_only else "Edit as JSON")
		self.resize(560, 480)
		self.result_value, self._is_list = None, isinstance(data, list)
		layout = QVBoxLayout(self)
		self.text = QPlainTextEdit(json.dumps(data, indent=2, ensure_ascii=False))
		self.text.setStyleSheet("font-family: Consolas, monospace;")
		self.text.setReadOnly(read_only)
		layout.addWidget(self.text)
		self.message = QLabel()
		self.message.setStyleSheet("color: #c0392b;")
		layout.addWidget(self.message)
		buttons = QDialogButtonBox(
			QDialogButtonBox.StandardButton.Close if read_only else QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
		)
		buttons.accepted.connect(self._ok)
		buttons.rejected.connect(self.reject)
		layout.addWidget(buttons)

	def _ok(self):
		try:
			value = json.loads(self.text.toPlainText())
		except ValueError as e:
			self.message.setText(f"This isn't valid JSON: {e}")
			return
		if not isinstance(value, list if self._is_list else dict):
			self.message.setText("This should be a list." if self._is_list else "This should be an object { ... }.")
			return
		self.result_value = value
		self.accept()
