import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication

from core.library import Library
from ui.composite_tab import CompositeTab


def test_new_edit_saves(tmp_path, monkeypatch):
	app = QApplication.instance() or QApplication([])
	lib = Library(tmp_path / "l.json")
	entry = lib.add("Gun", [])
	tab = CompositeTab(lib, None, lambda ref, multi, parent: ["a" * 24])
	assert tab.current_id() == entry
	tab.editor.add_item()
	assert Library(tmp_path / "l.json").entries[entry]["items"][0]["_tpl"] == "a" * 24
