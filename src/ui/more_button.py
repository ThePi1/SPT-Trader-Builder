"""The "More options" / "More locale" button: it opens and closes a part of a form, and looks like a button."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QToolButton


class MoreButton(QToolButton):
	"""A checkable, outlined button: a hand cursor and a highlight say it can be clicked."""

	def __init__(self, text, parent=None):
		super().__init__(parent)
		self.setText(text)
		self.setCheckable(True)
		self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
		self.setCursor(Qt.CursorShape.PointingHandCursor)
		self.setStyleSheet(
			"QToolButton { border: 1px solid palette(mid); border-radius: 3px; padding: 3px 10px; }"
			" QToolButton:hover { background: palette(midlight); }"
			" QToolButton:checked { background: palette(midlight); }"
		)
