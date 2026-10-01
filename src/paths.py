"""Where the app's files live, independent of the current working directory.

``APP_DIR`` is the folder holding ``data/`` and ``Exported Files/``: the ``src/``
folder when running from source, or the folder containing the .exe when packaged
with PyInstaller (``tools/pack.py`` ships ``data/`` next to the binary).
"""

import sys
from pathlib import Path

if getattr(sys, "frozen", False):
	APP_DIR = Path(sys.executable).resolve().parent
else:
	APP_DIR = Path(__file__).resolve().parent

DATA_DIR = APP_DIR / "data"
EXPORT_DIR = APP_DIR / "exports"
