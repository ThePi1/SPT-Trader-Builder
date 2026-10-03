"""The Schema Explorer: browse what a quest, task, reward ... is made of, and check any JSON file."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog, QListWidgetItem, QTabWidget, QTableWidgetItem, QTreeWidgetItem, QWidget

from core import jsonio
from core import settings as S
from schema import explorer
from schema.issues import ERROR
from ui.compiled.ui_browse_page import Ui_BrowseForm
from ui.compiled.ui_check_page import Ui_CheckForm
from ui.compiled.ui_explorer_tab import Ui_ExplorerForm
from ui.problems import ERROR_COLOR, WARNING_COLOR
from ui.tabs import fill_tabs

ROLE = Qt.ItemDataRole.UserRole


class BrowsePage(QWidget, Ui_BrowseForm):
	"""The layout is ui/designer/browse_page.ui: the tree on the left, the description and field table on the right."""

	def __init__(self, parent=None):
		super().__init__(parent)
		self.setupUi(self)
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
		for i, width in enumerate((170, 170, 120, 70)):
			self.table.setColumnWidth(i, width)
		self.splitter.setSizes([260, 640])
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


class CheckPage(QWidget, Ui_CheckForm):
	"""Open any JSON file and see what is wrong with it. The layout is ui/designer/check_page.ui."""

	def __init__(self, get_quests, get_locale, gamedata=None, settings=None, parent=None):
		super().__init__(parent)
		self.setupUi(self)
		self.get_quests, self.get_locale, self.gamedata, self.settings = get_quests, get_locale, gamedata, settings
		self.openButton.clicked.connect(lambda _checked=False: self.open_file())
		self.kind.addItem("Work out what it is", None)
		for value, label in explorer.FILE_KINDS:
			self.kind.addItem(label, value)
		self.kind.currentIndexChanged.connect(lambda _i: self.run())
		self.with_open.stateChanged.connect(lambda _s: self.run())
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
			self.summary.setText("This doesn't look like a quest, locale, trader assort or quest assort file. Pick what it is above.")
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


class ExplorerTab(QTabWidget, Ui_ExplorerForm):
	"""The two pages (names and order) are in ui/designer/explorer_tab.ui."""

	def __init__(self, get_quests, get_locale, gamedata=None, settings=None, parent=None):
		super().__init__(parent)
		self.setupUi(self)
		self.browse = BrowsePage()
		self.check = CheckPage(get_quests, get_locale, gamedata, settings)
		fill_tabs(self, self, {"page_browse": self.browse, "page_check": self.check})
