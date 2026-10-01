import logging, os, sys, ctypes
from PySide6.QtWidgets import QApplication, QMessageBox
from config import ConfigError, load_config
from gui import Gui_MainWindow
from paths import APP_DIR
from updates import get_update_stats
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
	win = Gui_MainWindow(config)
	ver_current, ver_latest, update_text, project_url = get_update_stats(config)

	# # Set up triggers that need specific data
	win.ui.actionAbout.triggered.connect(
		lambda: Gui_MainWindow.onAbout(win, ver_current, project_url)
	)
	win.ui.actionUpdateCheck.triggered.connect(
		lambda: Gui_MainWindow.onUpdateWindow(
			win, ver_current, ver_latest, project_url, update_text
		)
	)
	win.ui.actionQuest_Builder.triggered.connect(
		lambda: Gui_MainWindow.onQuestWindow(win)
	)
	win.ui.actionAssort_Builder.triggered.connect(
		lambda: Gui_MainWindow.onAssortWindow(win)
	)
	win.ui.actionEdit_Tracked_Data_Files_locale_quest.triggered.connect(
		lambda: Gui_MainWindow.editDataFiles(win)
	)

	win.show()
	# Run the application's main loop
	sys.exit(app.exec())


if __name__ == "__main__":
	main()
