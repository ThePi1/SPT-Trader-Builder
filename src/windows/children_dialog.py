import logging

from PySide6.QtWidgets import QApplication, QDialog

from builders.items import find_descendants, format_id_list
from tb_ui.gui_children import Ui_ChildrenMenu

log = logging.getLogger(__name__)


class Gui_ChildrenDlg(QDialog):
	"""Finds every item under a parent item in items.json (replaces the old console prompt).

	get_items returns the loaded items.json dict (or None); load_items asks the user to load
	one (and stores it where get_items will find it).
	"""

	def __init__(self, get_items, load_items, parent=None):
		super().__init__(parent)
		self.ui = Ui_ChildrenMenu()
		self.ui.setupUi(self)
		self.get_items = get_items
		self.load_items = load_items
		self.ui.pb_load.clicked.connect(self.on_load)
		self.ui.pb_find.clicked.connect(self.on_find)
		self.ui.fld_parent_id.returnPressed.connect(self.on_find)
		self.ui.fld_parent_id.textChanged.connect(self.update_buttons)
		self.ui.pb_copy.clicked.connect(self.on_copy)
		self.ui.pb_close.clicked.connect(self.close)
		self.refresh_items_status()

	def refresh_items_status(self):
		items = self.get_items()
		if items:
			self.ui.lbl_items_status.setText(f"items.json loaded ({len(items)} items).")
		else:
			self.ui.lbl_items_status.setText("No items.json loaded yet. Load one to search it.")
		self.ui.pb_load.setText("Load a different items.json..." if items else "Load items.json...")
		self.update_buttons()

	def update_buttons(self):
		has_items = bool(self.get_items())
		self.ui.pb_find.setEnabled(has_items and bool(self.ui.fld_parent_id.text().strip()))
		self.ui.pb_copy.setEnabled(bool(self.ui.txt_results.toPlainText()))

	def on_load(self):
		self.load_items()
		self.refresh_items_status()

	def on_find(self):
		items = self.get_items()
		parent_id = self.ui.fld_parent_id.text().strip()
		if not items or not parent_id:
			return
		found = find_descendants(items, parent_id)
		self.ui.txt_results.setPlainText(format_id_list(found))
		if parent_id not in items:
			note = " (that ID isn't in the loaded items.json)"
		else:
			note = ""
		self.ui.lbl_result.setText(f"{len(found)} item{'' if len(found) == 1 else 's'} found{note}.")
		log.info(f"Found {len(found)} items under {parent_id}")
		self.update_buttons()

	def on_copy(self):
		QApplication.clipboard().setText(self.ui.txt_results.toPlainText())
		self.ui.lbl_result.setText(self.ui.lbl_result.text().rstrip(".") + ". Copied to the clipboard.")
