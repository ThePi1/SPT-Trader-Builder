"""The quest outline: every quest of a file as a tree (quest > tasks and rewards by timing,
a Counter's subtasks under it), and the form for whichever node is selected.

All changes go through the Document so they can be undone. The tree is rebuilt when the data
changes under it (add, delete, undo); it only refreshes its labels while a form is being typed in.
"""

import json

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
	QComboBox, QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QMenu, QMessageBox, QPlainTextEdit, QPushButton,
	QScrollArea, QSplitter, QToolButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
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


class QuestOutline(QWidget):
	def __init__(self, gamedata=None, settings=None, parent=None):
		super().__init__(parent)
		self.gamedata, self.settings, self.doc = gamedata, settings, None
		self.library = None  # the user's saved composite items
		self.locale = None  # the open locale Document, for the text boxes
		self.picker = None  # (ref kind, multi, parent) -> [ids]: the window's search dialog
		self._editing = False
		splitter = QSplitter(self)
		left = QWidget()
		lay = QVBoxLayout(left)
		lay.setContentsMargins(0, 0, 0, 0)
		tools = QHBoxLayout()
		tools.setSpacing(3)
		self.new_quest_button = QPushButton("New quest")
		self.new_quest_button.clicked.connect(self.add_quest)
		self.add_button = QToolButton()
		self.add_button.setText("Add")
		self.add_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
		self.add_menu = QMenu(self.add_button)
		self.add_menu.aboutToShow.connect(self._fill_add_menu)
		self.add_button.setMenu(self.add_menu)
		tools.addWidget(self.new_quest_button)
		tools.addWidget(self.add_button)
		for text, slot in (("Copy", self.copy_selected), ("Delete", self.delete_selected), ("Up", lambda: self.move_selected(-1)), ("Down", lambda: self.move_selected(1))):
			button = QPushButton(text)
			button.clicked.connect(slot)
			tools.addWidget(button)
		tools.addStretch(1)
		lay.addLayout(tools)
		self.tree = QTreeWidget()
		self.tree.setHeaderHidden(True)
		self.tree.setIndentation(16)
		self.tree.currentItemChanged.connect(self._selected)
		lay.addWidget(self.tree, 1)
		self.problems = ProblemsPanel(settings)
		self.problems.activated.connect(self._jump)
		lay.addWidget(self.problems)
		self._check_timer = QTimer(self)
		self._check_timer.setSingleShot(True)
		self._check_timer.setInterval(400)
		self._check_timer.timeout.connect(self.check)
		splitter.addWidget(left)
		self.pane = QWidget()
		self.pane_layout = QVBoxLayout(self.pane)
		scroll = QScrollArea()
		scroll.setWidgetResizable(True)
		scroll.setWidget(self.pane)
		right = QSplitter(Qt.Orientation.Vertical)
		right.addWidget(scroll)
		self.json_view = QPlainTextEdit()  # what is selected, as it will be saved
		self.json_view.setReadOnly(True)
		self.json_view.setStyleSheet("font-family: Consolas, monospace; font-size: 11px;")
		self.json_view.setVisible(bool(settings and settings.show_json_preview))
		right.addWidget(self.json_view)
		right.setStretchFactor(0, 3)
		right.setStretchFactor(1, 1)
		right.setSizes([560, 200])
		splitter.addWidget(right)
		splitter.setSizes([360, 620])
		outer = QHBoxLayout(self)
		outer.setContentsMargins(0, 0, 0, 0)
		outer.addWidget(splitter)
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
			return QUEST.summary(data, names)
		if address.kind == "group":
			return f"{address.timing} ({len(data)})" if address.group != "rewards" else "Rewards"
		return registry.spec_of(data, address.kind).summary(data, names)

	def rebuild(self):
		keep = self._current_key()
		self.tree.blockSignals(True)
		self.tree.clear()
		if self.doc is not None:
			for qid, quest in self.doc.data.items():
				if not isinstance(quest, dict):
					continue
				self._build_quest(qid, quest)
		self.tree.expandAll()
		self.tree.blockSignals(False)
		if not self._select_key(keep):
			if self.tree.topLevelItemCount():
				self.tree.setCurrentItem(self.tree.topLevelItem(0))
			else:
				self._show_hint("Add a quest to begin, or open a quest file.")

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
			everyday = registry.kinds(group, everyday_only=True)
			for spec in everyday:
				menu.addAction(spec.label, lambda g=group, s=spec: self.add_item(g, s.kind))
			rare = [s for s in registry.kinds(group) if not s.everyday]
			if rare:
				more = menu.addMenu("Less common")
				for spec in rare:
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

	def move_selected(self, offset):
		address = self._current()
		if address is None or address.kind in ("group", "quest"):
			return
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
	"""Edit one item as JSON text. OK is refused while the text isn't valid JSON of the same shape."""

	def __init__(self, data, parent=None):
		super().__init__(parent)
		self.setWindowTitle("Edit as JSON")
		self.resize(560, 480)
		self.result_value, self._is_list = None, isinstance(data, list)
		layout = QVBoxLayout(self)
		self.text = QPlainTextEdit(json.dumps(data, indent=2, ensure_ascii=False))
		self.text.setStyleSheet("font-family: Consolas, monospace;")
		layout.addWidget(self.text)
		self.message = QLabel()
		self.message.setStyleSheet("color: #c0392b;")
		layout.addWidget(self.message)
		buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
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
