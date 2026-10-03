"""The Schema Explorer: browse what a quest, task, reward ... is made of, and check any JSON file."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
	QCheckBox, QComboBox, QFileDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QSplitter,
	QTabWidget, QTableWidget, QTableWidgetItem, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from core import jsonio
from core import settings as S
from schema import explorer
from schema.issues import ERROR
from ui.problems import ERROR_COLOR, WARNING_COLOR

ROLE = Qt.ItemDataRole.UserRole


class BrowsePage(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent)
		layout = QHBoxLayout(self)
		split = QSplitter()
		layout.addWidget(split)
		self.tree = QTreeWidget()
		self.tree.setHeaderHidden(True)
		for title, specs in explorer.all_specs():
			top = QTreeWidgetItem([title])
			font = top.font(0)
			font.setBold(True)
			top.setFont(0, font)
			self.tree.addTopLevelItem(top)
			for spec in specs:
				child = QTreeWidgetItem([spec.label + ("" if spec.everyday else " (rare)")])
				child.setData(0, ROLE, spec)
				top.addChild(child)
		self.tree.expandAll()
		split.addWidget(self.tree)
		right = QWidget()
		column = QVBoxLayout(right)
		self.title = QLabel()
		self.title.setStyleSheet("font-weight: bold;")
		self.note = QLabel()
		self.note.setWordWrap(True)
		self.where = QLabel()
		self.where.setStyleSheet("color: #808080;")
		self.table = QTableWidget(0, 5)
		self.table.setHorizontalHeaderLabels(["Field", "Key in the file", "Kind", "Needed", "Starts as"])
		self.table.verticalHeader().setVisible(False)
		self.table.horizontalHeader().setStretchLastSection(True)
		for i, width in enumerate((170, 170, 120, 70)):
			self.table.setColumnWidth(i, width)
		for widget in (self.title, self.note, self.where, self.table):
			column.addWidget(widget)
		split.addWidget(right)
		split.setSizes([260, 640])
		self.tree.currentItemChanged.connect(self._selected)

	def _selected(self, item, _previous):
		spec = item.data(0, ROLE) if item else None
		self.table.setRowCount(0)
		if spec is None:
			self.title.setText("")
			self.note.setText("")
			self.where.setText("")
			return
		self.title.setText(spec.label)
		self.note.setText(spec.note)
		self.where.setText(("Can be used: " + ", ".join(spec.timings)) if spec.timings else "")
		rows = explorer.field_rows(spec)
		self.table.setRowCount(len(rows))
		for r, row in enumerate(rows):
			for c, value in enumerate(row[:5]):
				cell = QTableWidgetItem(value)
				if row[5]:
					cell.setForeground(Qt.GlobalColor.gray)
				self.table.setItem(r, c, cell)
		managed = ", ".join(spec.managed)
		if managed:
			self.where.setText((self.where.text() + "   " if self.where.text() else "") + f"Filled in by the app: {managed}")


class CheckPage(QWidget):
	"""Open any JSON file and see what is wrong with it."""

	def __init__(self, get_quests, get_locale, gamedata=None, settings=None, parent=None):
		super().__init__(parent)
		self.get_quests, self.get_locale, self.gamedata, self.settings = get_quests, get_locale, gamedata, settings
		layout = QVBoxLayout(self)
		row = QHBoxLayout()
		button = QPushButton("Open a file to check...")
		button.clicked.connect(self.open_file)
		self.kind = QComboBox()
		self.kind.addItem("Work out what it is", None)
		for value, label in explorer.FILE_KINDS:
			self.kind.addItem(label, value)
		self.kind.currentIndexChanged.connect(lambda _i: self.run())
		self.with_open = QCheckBox("Check against the quests and locale that are open")
		self.with_open.stateChanged.connect(lambda _s: self.run())
		for widget in (button, self.kind, self.with_open):
			row.addWidget(widget)
		row.addStretch(1)
		layout.addLayout(row)
		self.summary = QLabel("Open a quest, locale, assort or quest-lock file. Nothing is changed in it.")
		self.summary.setWordWrap(True)
		layout.addWidget(self.summary)
		self.list = QListWidget()
		layout.addWidget(self.list, 1)
		self.data, self.name = None, ""

	def open_file(self):
		path, _ = QFileDialog.getOpenFileName(self, "Open a file to check", "", "JSON files (*.json);;All files (*)")
		if path:
			self.load(path)

	def load(self, path):
		try:
			self.data = jsonio.read_json(path)
		except (OSError, ValueError) as e:
			self.data = None
			self.summary.setText(f"The file could not be read: {e}")
			self.list.clear()
			return
		self.name = path
		self.run()

	def run(self):
		self.list.clear()
		if self.data is None:
			return
		kind = self.kind.currentData() or explorer.detect_kind(self.data)
		if kind is None:
			self.summary.setText("This doesn't look like a quest, locale, assort or quest-lock file. Pick what it is above.")
			return
		quests = self.get_quests() if self.with_open.isChecked() else None
		locale = self.get_locale() if self.with_open.isChecked() else None
		issues = explorer.check(self.data, kind, quests or None, locale or None, self.gamedata)
		label = dict(explorer.FILE_KINDS)[kind]
		errors = sum(1 for i in issues if i.level == ERROR)
		self.summary.setText(
			f"{self.name}\nChecked as: {label}. " + ("No problems found." if not issues else f"{errors} to fix, {len(issues) - errors} to check.")
		)
		most = S.limit(self.settings, "explorer_max_problems")
		for issue in sorted(issues, key=lambda i: i.level != ERROR)[:most]:
			item = QListWidgetItem(f"{issue.where() or 'File'}: {issue.message}")
			item.setForeground(ERROR_COLOR if issue.level == ERROR else WARNING_COLOR)
			self.list.addItem(item)
		if len(issues) > most:
			self.list.addItem(QListWidgetItem(f"...and {len(issues) - most} more not shown (Settings > Lists changes this)."))


class ExplorerTab(QTabWidget):
	def __init__(self, get_quests, get_locale, gamedata=None, settings=None, parent=None):
		super().__init__(parent)
		self.browse = BrowsePage()
		self.check = CheckPage(get_quests, get_locale, gamedata, settings)
		self.addTab(self.browse, "What things are made of")
		self.addTab(self.check, "Check a file")
