"""The "More options" / "More locale" button: it opens and closes a part of a form, and looks like a button."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QToolButton


class MoreButton(QToolButton):
	"""A checkable button with an outline and a caret (down when closed, up when open) beside its text."""

	def __init__(self, text, parent=None):
		super().__init__(parent)
		self.setText(text)
		self.setCheckable(True)
		self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
		self.setCursor(Qt.CursorShape.PointingHandCursor)
		self.setStyleSheet(
			"QToolButton { border: 1px solid palette(mid); border-radius: 3px; padding: 3px 8px; }"
			" QToolButton:hover { background: palette(midlight); }"
			" QToolButton:checked { background: palette(midlight); }"
		)
		self.toggled.connect(self._update_caret)
		self._update_caret(False)

	def _update_caret(self, open_):
		self.setArrowType(Qt.ArrowType.UpArrow if open_ else Qt.ArrowType.DownArrow)
