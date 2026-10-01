import logging, os, sys, ctypes
from PySide6.QtWidgets import QApplication, QMessageBox
from config import ConfigError, load_config
from gui import Gui_MainWindow
from paths import APP_DIR
from state import AppState
from utils import setup_logging

setup_logging()
log = logging.getLogger(__name__)


def fix_win_taskbar():
	app_id = "spt-tbt-tool"
	ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)


# Main method
def main():
	# The compiled UI files reference the window icon as "data/icon.ico", relative to the
	# working directory, so make sure we're running from the app folder.
	os.chdir(APP_DIR)

	# Use this on Windows to add the icon back to the taskbar
	# No idea how this works on Mac/Linux for now, haha
	if sys.platform == "win32":
		fix_win_taskbar()

	# Create the application and main window
	app = QApplication(sys.argv)
	try:
		config = load_config()
	except ConfigError as e:
		log.error(str(e))
		QMessageBox.critical(None, "Trader Builder - settings error", str(e))
		sys.exit(1)
	win = Gui_MainWindow(AppState.load(config))

	# # Set up triggers
	win.ui.actionAbout.triggered.connect(win.onAbout)
	win.ui.actionUpdateCheck.triggered.connect(win.onUpdateWindow)
	win.ui.actionQuest_Builder.triggered.connect(win.onQuestWindow)
	win.ui.actionAssort_Builder.triggered.connect(win.onAssortWindow)
	win.ui.actionEdit_Tracked_Data_Files_locale_quest.triggered.connect(win.editDataFiles)

	win.show()
	win.start_update_check()
	# Run the application's main loop
	sys.exit(app.exec())


if __name__ == "__main__":
	main()
