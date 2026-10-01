"""Shared test setup.

Tests import from ``src/`` but run with an unrelated working directory (to prove
the app doesn't depend on it), and Qt is forced into offscreen mode so no real
windows are needed.
"""

import json
import os
import re
import sys
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

SRC = Path(__file__).resolve().parent.parent / "src"
GOLDEN = Path(__file__).resolve().parent / "golden"
sys.path.insert(0, str(SRC))


@pytest.fixture(autouse=True)
def _run_from_elsewhere(monkeypatch, tmp_path):
	# The app must not depend on the current working directory.
	monkeypatch.chdir(tmp_path)


@pytest.fixture(scope="session")
def qapp():
	from PySide6.QtWidgets import QApplication

	return QApplication.instance() or QApplication([])


@pytest.fixture
def fixed_ids(monkeypatch):
	"""Make generated IDs deterministic (000...001, 000...002, ...)."""
	import secrets

	counter = iter(range(1, 10_000))
	monkeypatch.setattr(secrets, "token_hex", lambda nbytes: f"{next(counter):0{nbytes * 2}x}")


@pytest.fixture
def main_window(qapp, fixed_ids):
	from config import load_config
	from state import AppState
	from windows.main_window import Gui_MainWindow

	win = Gui_MainWindow(AppState.load(load_config()))
	yield win
	for w in win.windows:
		w.close()
	win.close()


@pytest.fixture
def check_golden():
	"""Compare a JSON-able object to tests/golden/<name>.json.

	Run with UPDATE_GOLDEN=1 to (re)write the golden file instead.
	"""

	def _check(name, obj):
		path = GOLDEN / f"{name}.json"
		text = json.dumps(obj, indent=2, sort_keys=True) + "\n"
		if os.environ.get("UPDATE_GOLDEN"):
			path.write_text(text, encoding="utf-8")
			return
		assert path.exists(), f"missing golden file {path} (run with UPDATE_GOLDEN=1)"
		assert text == path.read_text(encoding="utf-8")

	return _check
