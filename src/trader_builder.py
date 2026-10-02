import logging, os, sys, ctypes
from PySide6.QtWidgets import QApplication, QMessageBox
from modules.config import ConfigError, load_config
from modules.error_handling import install_excepthook, report_exception
from modules.paths import APP_DIR
from modules.state import AppState
from modules.utils import LOG_FILE, set_debug_logging, setup_logging
from modules.windows.main_window import Gui_MainWindow

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
	app = QApplication.instance() or QApplication(sys.argv)
	# From here on, an unexpected error is shown to the user (the packaged program has no console)
	install_excepthook()
	try:
		config = load_config()
	except ConfigError as e:
		log.error(str(e))
		QMessageBox.critical(None, "Trader Builder - settings error", str(e))
		sys.exit(1)
	try:
		set_debug_logging(config.debug_logging)
	except OSError as e:
		log.warning(f"Could not open the debug log file {LOG_FILE}: {e}")
	try:
		win = Gui_MainWindow(AppState.load(config))

		# # Set up triggers
		win.ui.actionAbout.triggered.connect(win.onAbout)
		win.ui.actionUpdateCheck.triggered.connect(win.onUpdateWindow)
		win.ui.actionQuest_Builder.triggered.connect(win.onQuestWindow)
		win.ui.actionAssort_Builder.triggered.connect(win.onAssortWindow)
		win.ui.actionEdit_Tracked_Data_Files_locale_quest.triggered.connect(win.editDataFiles)

		win.show()
		win.start_update_check()
	except Exception:
		# e.g. a missing or damaged data file
		report_exception(*sys.exc_info(), title="Trader Builder - could not start")
		sys.exit(1)
	# Run the application's main loop
	sys.exit(app.exec())


if __name__ == "__main__":
	main()
