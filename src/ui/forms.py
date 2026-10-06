"""Forms made from the schema: one control per Field, writing straight into a working copy.

A control only writes when the user changes it, so values it can't show (numbers kept as text,
choices it doesn't list) survive an edit. Keys the spec doesn't know are listed as "Kept as
they are".
"""

import json

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
	QCheckBox, QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QPlainTextEdit, QPushButton,
	QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from core import parts as P
from core.ids import new_id
from schema import choices as choice_lists
from schema import fields as F
from schema.common import short
from ui.help_mark import HelpMark
from ui.more_button import MoreButton

PICKABLE = (F.ITEM, F.QUEST, F.ACHIEVEMENT, F.CUSTOMIZATION)  # ids the Find... button can search for
BAD_STYLE = "border: 1px solid #c0392b; background: #fdecea;"
HINT_STYLE = "color: #808080;"


class Context:
	"""What the controls need to show names and choices: the game data (may be None)."""

	def __init__(self, gamedata=None, names=None, picker=None, library=None, tasks=None):
		from schema.common import PLAIN

		self.library = library  # core.library.Library of the user's saved composite items
		self.tasks = list(tasks or [])  # [(task id, words)] of the other tasks of the quest being edited
		self.picker = picker  # (ref kind, multi, parent widget) -> [ids]; set by the window
		self.gamedata = gamedata
		self.names = names or PLAIN

	def choices(self, field):
		return choice_lists.resolve(field.choices, self.gamedata)

	def pick(self, ref, multi=False, parent=None):
		"""Let the user search for ids of this kind (an F.ITEM, ...). Returns a list of ids, [] if none chosen
		or no search is available."""
		if self.picker is None:
			return []
		return self.picker(ref, multi, parent)

	def composite_parts(self, entry_id):
		"""The parts of the saved or vanilla composite item with this id (as stored), or None if there isn't one."""
		if self.library is not None and entry_id in self.library.entries:
			return self.library.entries[entry_id].get("items")
		presets = self.gamedata.item_presets if self.gamedata is not None else {}
		if entry_id in presets:
			return presets[entry_id].get("_items")
		return None

	def pick_item_ids(self, multi=False, parent=None, ref="part"):
		"""Item ids chosen in the Find an item window, which lists items and composite items (and, for ref "item_id", item categories). A composite item
		gives the id of its main item (its root part's template), as the game's own files do: a list of ids can't
		hold its parts, and the composite's own id is not an item id."""
		ids = []
		for picked in self.pick(ref, multi, parent):  # (ref "item": items only, no composite items to choose)
			parts = self.composite_parts(picked)
			for tpl in [p.get("_tpl", "") for p in P.roots(parts)] if parts is not None else [picked]:
				if tpl and tpl not in ids:
					ids.append(tpl)
		return ids

	def task_label(self, task_id):
		"""Words for a task of the quest being edited ('' if it isn't one)."""
		return next((label for known, label in self.tasks if known == task_id), "")

	def name_of(self, ref, value):
		"""The name of the thing an id points at, or ''."""
		if not isinstance(value, str) or not value:
			return ""
		if ref == F.ITEM:
			return self.names.item(value) if self.names.item(value) != short(value, 12) else ""
		if ref == F.TRADER:
			return self.names.trader(value) if self.names.trader(value) != short(value, 12) else ""
		if ref == F.QUEST:
			return self.names.quest(value) if self.names.quest(value) != short(value, 12) else ""
		return ""


class Control(QWidget):
	"""One field's widget. load() shows a value without writing it; edited(value) fires on user edits."""

	edited = Signal(object)

	def __init__(self, field, ctx):
		super().__init__()
		self.field, self.ctx = field, ctx
		box = QHBoxLayout(self)
		box.setContentsMargins(0, 0, 0, 0)
		self.box = box

	def load(self, value):
		raise NotImplementedError


class TextControl(Control):
	def __init__(self, field, ctx):
		super().__init__(field, ctx)
		self.entry = QLineEdit()
		self.entry.textEdited.connect(self.edited.emit)
		self.box.addWidget(self.entry)

	def load(self, value):
		self.entry.setText("" if value is None else str(value))


class NumberControl(Control):
	"""A whole number or a number with decimals. Text that isn't a number is marked and not written."""

	def __init__(self, field, ctx):
		super().__init__(field, ctx)
		self.whole = field.kind == F.INT
		self.entry = QLineEdit()
		self.entry.textEdited.connect(self._edited)
		self.box.addWidget(self.entry)

	def _parse(self, text):
		text = text.strip()
		value = int(text) if self.whole else float(text)
		if not self.whole and value == int(value) and "." not in text and "e" not in text.lower():
			value = int(value)
		f = self.field
		if (f.minimum is not None and value < f.minimum) or (f.maximum is not None and value > f.maximum):
			raise ValueError("out of range")
		return value

	def _edited(self, text):
		try:
			value = self._parse(text)
		except ValueError:
			self.entry.setStyleSheet(BAD_STYLE)
			return
		self.entry.setStyleSheet("")
		self.edited.emit(value)

	def load(self, value):
		self.entry.setStyleSheet("")
		self.entry.setText("" if value is None else str(value))


class BoolControl(Control):
	def __init__(self, field, ctx):
		super().__init__(field, ctx)
		self.check = QCheckBox()
		self.check.clicked.connect(lambda checked: self.edited.emit(bool(checked)))  # (not connected straight to emit: PySide then calls it with no value)
		self.box.addWidget(self.check)
		self.box.addStretch(1)

	def load(self, value):
		self.check.setChecked(bool(value))


class ChoiceControl(Control):
	"""A drop-down. A value it doesn't list is added so it is shown and kept."""

	def __init__(self, field, ctx):
		super().__init__(field, ctx)
		self.combo = QComboBox()
		for value, label in ctx.choices(field):
			self.combo.addItem(label, value)
		self.combo.activated.connect(lambda i: self.edited.emit(self.combo.itemData(i)))
		self.box.addWidget(self.combo, 1)

	def load(self, value):
		index = self.combo.findData(value)
		if index < 0:
			self.combo.addItem(str(value), value)
			index = self.combo.count() - 1
		self.combo.setCurrentIndex(index)


class RefControl(Control):
	"""An id (text), with the name it points at shown beside it. Traders are a drop-down."""

	def __init__(self, field, ctx):
		super().__init__(field, ctx)
		self.entry = QLineEdit()
		self.entry.textEdited.connect(self._edited)
		self.name = QLabel()
		self.name.setStyleSheet(HINT_STYLE)
		self.box.addWidget(self.entry, 1)
		self.box.addWidget(self.name)
		if ctx.picker is not None and field.ref in PICKABLE:
			find = QPushButton("Find...")
			find.clicked.connect(self._find)
			self.box.addWidget(find)

	def _find(self):
		ids = self.ctx.pick_item_ids(False, self, "item_id") if self.field.ref == F.ITEM else self.ctx.pick(self.field.ref, False, self)
		if ids:
			self.entry.setText(ids[0])
			self._edited(ids[0])

	def _edited(self, text):
		text = text.strip()
		self.name.setText(self.ctx.name_of(self.field.ref, text))
		self.edited.emit(text)

	def load(self, value):
		self.entry.setText("" if value is None else str(value))
		self.name.setText(self.ctx.name_of(self.field.ref, value))


class TraderControl(ChoiceControl):
	def __init__(self, field, ctx):
		super().__init__(F.Field(field.key, field.label, F.CHOICE, choices="traders", open=True), ctx)
		self.field = field


class ListControl(Control):
	"""A list of text values (or ids): a small list to add to and remove from. With choices the
	entry is a drop-down."""

	def __init__(self, field, ctx):
		super().__init__(field, ctx)
		self.values = []
		self.pairs = ctx.choices(field) if field.choices else None
		column = QVBoxLayout()
		column.setSpacing(2)
		self.list = QListWidget()
		self.list.setMinimumHeight(44)
		self.list.setMaximumHeight(72)
		column.addWidget(self.list)
		row = QHBoxLayout()
		row.setSpacing(4)
		if self.pairs:
			self.entry = QComboBox()
			for value, label in self.pairs:
				self.entry.addItem(label, value)
		else:
			self.entry = QLineEdit()
			self.entry.returnPressed.connect(self._add)
		add, remove = QPushButton("Add"), QPushButton("Remove")
		add.clicked.connect(self._add)
		remove.clicked.connect(self._remove)
		widgets = [(self.entry, 1), (add, 0), (remove, 0)]
		if ctx.picker is not None and field.ref in PICKABLE and not self.pairs:
			find = QPushButton("Find...")
			find.clicked.connect(self._find)
			widgets.insert(1, (find, 0))
		for widget, stretch in widgets:
			row.addWidget(widget, stretch)
		column.addLayout(row)
		self.box.addLayout(column, 1)

	def _label(self, value):
		if isinstance(value, str) and self.field.ref:
			name = self.ctx.name_of(self.field.ref, value)
			return f"{name} ({short(value, 12)})" if name else value
		for known, label in self.pairs or ():
			if known == value:
				return label
		return str(value)

	def _fill(self):
		self.list.clear()
		for value in self.values:
			self.list.addItem(self._label(value))

	def load(self, value):
		self.values = list(value) if isinstance(value, list) else []
		self._fill()

	def _add(self):
		value = self.entry.currentData() if self.pairs else self.entry.text().strip()
		if value in (None, ""):
			return
		self.values.append(value)
		if not self.pairs:
			self.entry.clear()
		self._fill()
		self.edited.emit(list(self.values))

	def _find(self):
		ids = self.ctx.pick_item_ids(True, self, "item_id") if self.field.ref == F.ITEM else self.ctx.pick(self.field.ref, True, self)
		if ids:
			self.values.extend(i for i in ids if i not in self.values)
			self._fill()
			self.edited.emit(list(self.values))

	def _remove(self):
		row = self.list.currentRow()
		if row >= 0:
			del self.values[row]
			self._fill()
			self.edited.emit(list(self.values))


class GroupsControl(Control):
	"""Groups of items where any one group will do and a group needs all of its items (what a quest wants
	worn, the mods a weapon must have). A tree of groups with their items under them. Ids are typed
	(several can be separated by spaces or commas) or found with Find..."""

	def __init__(self, field, ctx):
		super().__init__(field, ctx)
		self.groups = []
		column = QVBoxLayout()
		column.setSpacing(2)
		hint = QLabel("Any one group is enough. A group needs all of its items.")
		hint.setStyleSheet(HINT_STYLE + " font-size: 11px;")
		column.addWidget(hint)
		self.tree = QTreeWidget()
		self.tree.setHeaderHidden(True)
		self.tree.setIndentation(14)
		self.tree.setMinimumHeight(60)
		self.tree.setMaximumHeight(160)
		column.addWidget(self.tree)
		row = QHBoxLayout()
		row.setSpacing(4)
		self.entry = QLineEdit()
		self.entry.setPlaceholderText("Item id")
		row.addWidget(self.entry, 1)
		if ctx.picker is not None:
			find = QPushButton("Find...")
			find.clicked.connect(self._find)
			row.addWidget(find)
		for text, slot in (("New group", self._new_group), ("Add to group", self._add_to_group), ("Remove", self._remove)):
			button = QPushButton(text)
			button.clicked.connect(slot)
			row.addWidget(button)
		column.addLayout(row)
		self.box.addLayout(column, 1)

	def _name(self, tpl):
		name = self.ctx.name_of(F.ITEM, tpl)
		return f"{name} ({short(tpl, 12)})" if name else str(tpl)

	def _fill(self, select=None):
		"""Rebuild the tree; select is (group number, item number or None)."""
		self.tree.clear()
		chosen = None
		for g, group in enumerate(self.groups):
			top = QTreeWidgetItem([f"Group {g + 1}"])
			font = top.font(0)
			font.setBold(True)
			top.setFont(0, font)
			self.tree.addTopLevelItem(top)
			for i, tpl in enumerate(group):
				child = QTreeWidgetItem([self._name(tpl)])
				top.addChild(child)
				if select == (g, i):
					chosen = child
			if select == (g, None):
				chosen = top
			top.setExpanded(True)
		if chosen is not None:
			self.tree.setCurrentItem(chosen)

	def load(self, value):
		self.groups = [list(g) if isinstance(g, list) else [g] for g in value] if isinstance(value, list) else []
		self._fill()

	def _changed(self, select=None):
		self.groups = [g for g in self.groups if g]  # (a group with nothing in it goes)
		self._fill(select)
		self.edited.emit([list(g) for g in self.groups])

	def _find(self):
		ids = self.ctx.pick_item_ids(True, self, "item_id")
		if ids:
			self.entry.setText(", ".join(ids))

	def _typed(self):
		ids = [part for part in self.entry.text().replace(",", " ").split() if part]
		self.entry.clear()
		return ids

	def _new_group(self):
		ids = self._typed()
		if ids:
			self.groups.append(ids)
			self._changed((len(self.groups) - 1, None))

	def _selected(self):
		item = self.tree.currentItem()
		if item is None:
			return None, None
		parent = item.parent()
		if parent is None:
			return self.tree.indexOfTopLevelItem(item), None
		return self.tree.indexOfTopLevelItem(parent), parent.indexOfChild(item)

	def _add_to_group(self):
		ids = self._typed()
		if not ids:
			return
		g, _i = self._selected()
		if g is None:
			self.groups.append(ids)
			g = len(self.groups) - 1
		else:
			self.groups[g].extend(i for i in ids if i not in self.groups[g])
		self._changed((g, None))

	def _remove(self):
		g, i = self._selected()
		if g is None:
			return
		if i is None:
			del self.groups[g]
		else:
			del self.groups[g][i]
		self._changed()


class VisibilityControl(Control):
	"""'Only show after' these tasks of the quest are done. The conditions that are already there keep
	their own ids; a new one gets a new id."""

	def __init__(self, field, ctx):
		super().__init__(field, ctx)
		self.entries = []
		column = QVBoxLayout()
		column.setSpacing(2)
		self.list = QListWidget()
		self.list.setMinimumHeight(40)
		self.list.setMaximumHeight(72)
		column.addWidget(self.list)
		row = QHBoxLayout()
		row.setSpacing(4)
		self.combo = QComboBox()
		for task_id, label in ctx.tasks:
			self.combo.addItem(label, task_id)
		add, remove = QPushButton("Add"), QPushButton("Remove")
		add.clicked.connect(self._add)
		remove.clicked.connect(self._remove)
		for widget, stretch in ((self.combo, 1), (add, 0), (remove, 0)):
			row.addWidget(widget, stretch)
		column.addLayout(row)
		self.box.addLayout(column, 1)

	@staticmethod
	def _target(entry):
		return entry.get("target", "") if isinstance(entry, dict) else str(entry)

	def _fill(self):
		self.list.clear()
		for entry in self.entries:
			target = self._target(entry)
			self.list.addItem(self.ctx.task_label(target) or short(target, 24))

	def load(self, value):
		self.entries = list(value) if isinstance(value, list) else []
		self._fill()

	def _add(self):
		target = self.combo.currentData()
		if not target or any(self._target(e) == target for e in self.entries):
			return
		self.entries.append({"conditionType": "CompleteCondition", "id": new_id(), "target": target})
		self._fill()
		self.edited.emit(list(self.entries))

	def _remove(self):
		row = self.list.currentRow()
		if row >= 0:
			del self.entries[row]
			self._fill()
			self.edited.emit(list(self.entries))


class PartsControl(Control):
	"""The parts of an item (a reward's items): a tree of parts with their details."""

	def __init__(self, field, ctx):
		super().__init__(field, ctx)
		self.editor = None

	def load(self, value):
		from ui.parts_editor import PartsEditor

		if self.editor is not None:
			self.editor.hide()
			self.editor.setParent(None)
			self.editor.deleteLater()
		self.parts = value if isinstance(value, list) else []
		self.editor = PartsEditor(self.parts, self.ctx)
		self.editor.changed.connect(lambda: self.edited.emit(self.parts))
		self.box.addWidget(self.editor, 1)


class JsonControl(Control):
	"""Anything without its own control: edited as JSON text. Invalid JSON is marked and not written."""

	def __init__(self, field, ctx):
		super().__init__(field, ctx)
		self.text = QPlainTextEdit()
		self.text.setMaximumHeight(90)
		self.text.setStyleSheet("font-family: Consolas, monospace;")
		self.text.textChanged.connect(self._edited)
		self._loading = False
		self.box.addWidget(self.text, 1)

	def _edited(self):
		if self._loading:
			return
		try:
			value = json.loads(self.text.toPlainText() or "null")
		except ValueError:
			self.text.setStyleSheet(BAD_STYLE + " font-family: Consolas, monospace;")
			return
		self.text.setStyleSheet("font-family: Consolas, monospace;")
		self.edited.emit(value)

	def load(self, value):
		self._loading = True
		self.text.setPlainText("" if value is None else json.dumps(value, indent=2, ensure_ascii=False))
		self._loading = False


_CONTROLS = {
	F.TEXT: TextControl, F.MULTILINE: TextControl, F.INT: NumberControl, F.NUMBER: NumberControl, F.BOOL: BoolControl,
	F.CHOICE: ChoiceControl, F.LIST: ListControl, F.IDLIST: ListControl,
}


def make_control(field, ctx):
	if field.kind == F.REF:
		return TraderControl(field, ctx) if field.ref == F.TRADER else RefControl(field, ctx)
	if field.kind == F.REWARD_ITEMS:
		return PartsControl(field, ctx)
	if field.kind == F.GROUPS:
		return GroupsControl(field, ctx)
	if field.kind == F.VISIBILITY:
		return VisibilityControl(field, ctx)
	if field.kind == F.LIST and not field.choices:
		return ListControl(field, ctx)
	return _CONTROLS.get(field.kind, JsonControl)(field, ctx)


def flatten(fields, prefix=""):
	"""The fields to show: an object field becomes one row per inner field ('distance.value')."""
	rows = []
	for field in fields:
		if field.kind == F.OBJECT and field.fields:
			for inner in flatten(field.fields, f"{prefix}{field.key}."):
				rows.append(F.Field(**{**inner.__dict__, "label": f"{field.label}: {inner.label}", "advanced": inner.advanced or field.advanced}))
		else:
			rows.append(F.Field(**{**field.__dict__, "key": prefix + field.key}) if prefix else field)
	return rows


class FormWidget(QWidget):
	"""The form for one spec. bind(item) shows a dict and from then on writes edits straight into it."""

	changed = Signal()
	field_changed = Signal(str)  # the key that was edited

	def __init__(self, spec, ctx=None, show_advanced=False, parent=None):
		super().__init__(parent)
		self.spec, self.ctx, self.item = spec, ctx or Context(), None
		self.controls = []
		outer = QVBoxLayout(self)
		outer.setContentsMargins(0, 0, 0, 0)
		main, more = QFormLayout(), QFormLayout()
		for layout in (main, more):
			layout.setContentsMargins(0, 0, 0, 0)
			layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
		for field in flatten(spec.fields):
			control = make_control(field, self.ctx)
			control.edited.connect(lambda value, key=field.key: self._write(key, value))
			self.controls.append(control)
			(more if field.advanced else main).addRow(self._label_for(field), control)
		outer.addLayout(main)
		self.more_button = MoreButton("More options", self)  # (given a parent now: with none, setVisible below would open it as a window)
		self.more_box = QWidget(self)
		self.more_box.setLayout(more)
		self.more_box.setVisible(False)
		has_more = more.rowCount() > 0
		self.more_button.setVisible(has_more)
		self.more_button.toggled.connect(self.more_box.setVisible)
		outer.addWidget(self.more_button, 0, Qt.AlignmentFlag.AlignLeft)
		outer.addWidget(self.more_box)
		self.extras = QLabel()
		self.extras.setWordWrap(True)
		self.extras.setStyleSheet(HINT_STYLE + " font-size: 11px;")
		outer.addWidget(self.extras)
		if show_advanced and has_more:
			self.more_button.setChecked(True)

	@staticmethod
	def _label_for(field):
		"""The label of a row: its text, with a ? mark that explains it when the field has a longer explanation."""
		if not field.help:
			return field.label
		holder = QWidget()
		box = QHBoxLayout(holder)
		box.setContentsMargins(0, 0, 0, 0)
		box.setSpacing(4)
		box.addWidget(QLabel(field.label))
		box.addWidget(HelpMark(field.help))
		box.addStretch(1)
		return holder

	def bind(self, item):
		self.item = item
		for control in self.controls:
			control.load(F.get_path(item, control.field.key, control.field.default))
		self._update_extras()

	def _write(self, key, value):
		F.set_path(self.item, key, value)
		if isinstance(value, list) and "target" in self.item and self.spec.field(key) is not None and self.spec.field(key).kind == F.REWARD_ITEMS:
			from core import parts as P

			if self.item["target"] not in P.ids_of(value):
				main = P.roots(value)
				self.item["target"] = main[0]["_id"] if main else ""
		self._update_extras()
		self.field_changed.emit(key)
		self.changed.emit()

	def _update_extras(self):
		known = self.spec.known_keys()
		kept = [f"{k} = {short(v, 22)}" for k, v in self.item.items() if k not in known]
		shown = ", ".join(kept[:5]) + (f" (+{len(kept) - 5} more)" if len(kept) > 5 else "")
		self.extras.setText(f"Kept as they are: {shown}" if kept else "")
		self.extras.setToolTip("\n".join(kept))
