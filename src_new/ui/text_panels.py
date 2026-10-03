"""Text boxes for the words the game shows (a quest's name and description, a task's text),
kept in the locale file. They write to the open locale document."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFormLayout, QGroupBox, QLabel, QLineEdit, QPlainTextEdit, QVBoxLayout, QWidget

from core.documents import MISSING
from schema import locale as L
from ui.more_button import MoreButton


class TextBox(QWidget):
	"""One piece of text: a line or a few lines, stored under key in the locale document."""

	def __init__(self, doc, key, multiline, parent=None):
		super().__init__(parent)
		self.doc, self.key = doc, key
		box = QVBoxLayout(self)
		box.setContentsMargins(0, 0, 0, 0)
		if multiline:
			self.edit = QPlainTextEdit()
			self.edit.setFixedHeight(64)
			self.edit.textChanged.connect(lambda: self._edited(self.edit.toPlainText()))
		else:
			self.edit = QLineEdit()
			self.edit.textEdited.connect(self._edited)
		self._loading = True
		self._show(doc.data.get(key, ""))
		self._loading = False
		box.addWidget(self.edit)

	def _show(self, text):
		(self.edit.setPlainText if isinstance(self.edit, QPlainTextEdit) else self.edit.setText)(text)

	def _edited(self, text):
		if self._loading:
			return
		if text == "" and self.key not in self.doc.data:
			return
		self.doc.set_value("Edit text", (self.key,), text, coalesce=self.key)


DEFAULT_FIELDS = ("name", "description", "startedMessageText", "successMessageText")  # shown first, in this order


class QuestTextPanel(QGroupBox):
	"""The locale of a quest: name, description and the start and completion messages; the rest is under More locale."""

	def __init__(self, doc, quest, parent=None):
		super().__init__("Locale", parent)
		qid = quest.get("_id", "")
		layout = QVBoxLayout(self)
		main, more = QFormLayout(), QFormLayout()
		fields = {field.key: field for field in L.QUEST_TEXT}
		for field in [fields[k] for k in DEFAULT_FIELDS] + [f for f in L.QUEST_TEXT if f.key not in DEFAULT_FIELDS]:
			key = quest.get(field.key) or L.quest_key(qid, field.key)
			if not isinstance(key, str):
				continue
			box = TextBox(doc, key, field.multiline)
			(main if field.key in DEFAULT_FIELDS else more).addRow(field.label, box)
		layout.addLayout(main)
		self.more_button = MoreButton("More locale", self)
		self.more_box = QWidget(self)
		self.more_box.setLayout(more)
		self.more_box.setVisible(False)
		self.more_button.toggled.connect(self.more_box.setVisible)
		layout.addWidget(self.more_button, 0, Qt.AlignmentFlag.AlignLeft)
		layout.addWidget(self.more_box)


class TaskTextPanel(QGroupBox):
	"""What the quest screen says for a task. Start tasks have none (the game writes it itself)."""

	def __init__(self, doc, task_id, timing, parent=None):
		super().__init__("Locale", parent)
		layout = QVBoxLayout(self)
		layout.addWidget(TextBox(doc, task_id, True))
		if timing == "Fail":
			hint = QLabel("Optional for tasks that fail the quest.")
			hint.setStyleSheet("color: #808080;")
			layout.addWidget(hint)


def task_has_text(timing):
	return L.task_text_needed(timing) != "none"
