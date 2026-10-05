"""A small "?" that explains something in a box while the mouse is over it (or it is clicked)."""

from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QLabel


class HelpMark(QLabel):
	"""The "?" next to a label. help_text is the explanation; the box wraps it to a readable width."""

	WIDTH = 320

	def __init__(self, help_text, parent=None):
		super().__init__("?", parent)
		self.help_text = help_text
		self.popup = None
		self.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.setFixedSize(16, 16)
		self.setCursor(Qt.CursorShape.WhatsThisCursor)
		self.setAccessibleDescription(help_text)
		self.setStyleSheet("QLabel { border: 1px solid palette(mid); border-radius: 8px; color: palette(mid); font-size: 10px; font-weight: bold; }")

	def _make_popup(self):
		popup = QLabel(self.help_text, None, Qt.WindowType.ToolTip)
		popup.setWordWrap(True)
		popup.setFixedWidth(self.WIDTH)
		popup.setStyleSheet("QLabel { background: palette(tooltip-base); color: palette(tooltip-text); border: 1px solid palette(dark); padding: 6px; }")
		popup.adjustSize()
		return popup

	def show_help(self):
		"""Show the explanation just below the mark."""
		if self.popup is None:
			self.popup = self._make_popup()
		self.popup.move(self.mapToGlobal(QPoint(0, self.height() + 4)))
		self.popup.show()

	def hide_help(self):
		if self.popup is not None:
			self.popup.hide()

	def enterEvent(self, event):
		self.show_help()
		super().enterEvent(event)

	def leaveEvent(self, event):
		self.hide_help()
		super().leaveEvent(event)

	def mousePressEvent(self, event):
		self.show_help()
		super().mousePressEvent(event)

	def hideEvent(self, event):
		self.hide_help()
		super().hideEvent(event)
