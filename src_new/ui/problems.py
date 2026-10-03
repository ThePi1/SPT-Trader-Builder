"""The Problems list: what is wrong with the open quests, with a click to jump to it."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from schema.issues import ERROR

ERROR_COLOR = QColor("#c0392b")
WARNING_COLOR = QColor("#b9770e")
ROLE = Qt.ItemDataRole.UserRole


def node_path(path):
	"""The path of the quest, task, subtask or reward an issue is inside (the issue's path cut down to it)."""
	if len(path) >= 7 and path[1] == "conditions" and path[4] == "counter" and path[5] == "conditions":
		return tuple(path[:7])
	if len(path) >= 4 and path[1] in ("conditions", "rewards"):
		return tuple(path[:4])
	return tuple(path[:1])


class ProblemsPanel(QWidget):
	activated = Signal(tuple)  # the node path of the clicked problem

	def __init__(self, parent=None):
		super().__init__(parent)
		layout = QVBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		layout.setSpacing(2)
		self.header = QLabel()
		layout.addWidget(self.header)
		self.list = QListWidget()
		self.list.setMaximumHeight(130)
		self.list.itemActivated.connect(self._activated)
		self.list.itemClicked.connect(self._activated)
		layout.addWidget(self.list)

	def show_issues(self, issues, describe):
		"""issues: [Issue]. describe(path) -> the words that say where it is (quest and task names)."""
		self.list.clear()
		errors = sum(1 for i in issues if i.level == ERROR)
		if not issues:
			self.header.setText("No problems found.")
			return
		warnings = len(issues) - errors
		parts = ([f"{errors} to fix"] if errors else []) + ([f"{warnings} to check"] if warnings else [])
		self.header.setText("Problems: " + ", ".join(parts))
		for issue in sorted(issues, key=lambda i: i.level != ERROR)[:300]:
			where = describe(issue.path)
			item = QListWidgetItem(f"{where}: {issue.message}" if where else issue.message)
			item.setForeground(ERROR_COLOR if issue.level == ERROR else WARNING_COLOR)
			item.setData(ROLE, node_path(issue.path) if issue.path else ())
			item.setToolTip(str(issue))
			self.list.addItem(item)

	def _activated(self, item):
		path = item.data(ROLE)
		if path:
			self.activated.emit(path)
