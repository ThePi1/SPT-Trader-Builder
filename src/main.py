"""SPT Trader Builder: run with  python main.py"""

import logging
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from core.gamedata import GameData
from core.paths import BUNDLED_DATABASE_DIR
from core.settings import Settings, SettingsError
from ui.main_window import MainWindow, app_icon


def main():
	app = QApplication(sys.argv)
	app.setWindowIcon(app_icon())  # (every window and dialog, the message boxes before the main window too)
	try:
		settings = Settings.load()
	except SettingsError as e:
		QMessageBox.critical(None, "Settings", str(e))
		return 1
	if settings.debug_logging:
		logging.basicConfig(filename="spt_trader_builder.log", level=logging.DEBUG)
	database = settings.resolve("database_folder")
	gamedata = GameData(database, settings.language, BUNDLED_DATABASE_DIR if BUNDLED_DATABASE_DIR.is_dir() else None)
	window = MainWindow(settings, gamedata)
	window.show()
	return app.exec()


if __name__ == "__main__":
	sys.exit(main())
