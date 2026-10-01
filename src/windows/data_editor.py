import json
import logging
from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QMainWindow

from tb_ui.gui_datafiles import Ui_DataEditor
from paths import DATA_DIR
from windows.common import safe_file_dialog

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
		if root_folder is None:
			log.info("No folder selected, aborting WTT import.")
			return
		log.info(f"Finding JSON files in root folder: {root_folder}")
		allfiles = Path(root_folder).rglob("*.json")
		datafiles, datafiles_to_disk = self.state.import_customdata(
			list(allfiles), root_folder=root_folder
		)

		with open(DATA_DIR / "datafiles.json", "w") as f:
			json.dump(datafiles_to_disk, f)
		self.ui.statusbar.showMessage(
			f"Loaded {sum(len(sublist) for sublist in datafiles)} data files."
		)
