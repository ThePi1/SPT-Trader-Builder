"""SPT Quest Builder: run with  python main.py"""

import logging
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from core.gamedata import GameData
from core.paths import BUNDLED_DATABASE_DIR
from core.settings import Settings, SettingsError
from ui.main_window import MainWindow


def main():
	app = QApplication(sys.argv)
	try:
		settings = Settings.load()
	except SettingsError as e:
		QMessageBox.critical(None, "Settings", str(e))
		return 1
	if settings.debug_logging:
		logging.basicConfig(filename="spt_builder.log", level=logging.DEBUG)
	database = settings.resolve("database_folder")
	gamedata = GameData(database, settings.language, BUNDLED_DATABASE_DIR if BUNDLED_DATABASE_DIR.is_dir() else None)
	window = MainWindow(settings, gamedata)
	window.show()
	return app.exec()


if __name__ == "__main__":
	sys.exit(main())
