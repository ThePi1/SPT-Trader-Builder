"""Where the app's files live, independent of the current working directory.

``APP_DIR`` is the folder holding ``data/``: the ``src_new/`` folder when running from source,
or the folder containing the .exe when packaged with PyInstaller (``data/`` ships next to it).
"""

import sys
from pathlib import Path

if getattr(sys, "frozen", False):
	APP_DIR = Path(sys.executable).resolve().parent
else:
	APP_DIR = Path(__file__).resolve().parent.parent  # this file is src_new/core/paths.py

DATA_DIR = APP_DIR / "data"

# The game data that ships with the app, laid out like SPT's own SPT_Data/database folder
# (only the files the app reads). Used when no SPT database folder is chosen in Settings.
BUNDLED_DATABASE_DIR = DATA_DIR / "database"

# The user's saved composite items
LIBRARY_FILE = DATA_DIR / "my_items.json"

SETTINGS_FILE = DATA_DIR / "settings.ini"

# The window icon (also the icon of the packaged .exe)
ICON_FILE = DATA_DIR / "icon.ico"
