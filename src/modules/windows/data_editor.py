import logging
from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QMainWindow

from modules.gui.compiled.gui_datafiles import Ui_DataEditor
from modules.paths import DATA_DIR
from modules.utils import write_json
from modules.windows.common import safe_file_dialog

log = logging.getLogger(__name__)


class Gui_DataEditor(QMainWindow):
	def __init__(self, state, parent=None):
		super().__init__(parent)
		self.ui = Ui_DataEditor()
		self.ui.setupUi(self)
		self.state = state
		self.on_launch()
		self.show()
		self.ui.pb_wtt_import.released.connect(self.import_wtt)

	def on_launch(self):
		pass

	def import_wtt(self):
		root_folder, ok = safe_file_dialog(
			QFileDialog.getExistingDirectory, "Select WTT root data folder"
		)
		if not ok or not root_folder:
			log.info("No folder selected, aborting WTT import.")
			return
		log.info(f"Finding JSON files in root folder: {root_folder}")
		allfiles = Path(root_folder).rglob("*.json")
		datafiles, datafiles_to_disk = self.state.import_customdata(
			list(allfiles), root_folder=root_folder
		)

		write_json(DATA_DIR / "datafiles.json", datafiles_to_disk, indent=None)
		# (a file is counted once even if its path matches more than one category)
		file_count = len({path for paths in datafiles_to_disk.values() for path in paths})
		self.ui.statusbar.showMessage(
			f"Loaded {file_count} data file{'' if file_count == 1 else 's'}."
		)
