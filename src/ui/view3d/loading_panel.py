"""A panel in the middle of the 3D view saying what is being loaded and how far along it is (the Zones tab shows it
while it reads a map: seconds for a big one, during which the window can't be used).

The loading runs on the window's own thread, so each change is painted straight away: the window handles its waiting
paint events (not clicks or keys, which wait until the loading is done) at most every PAINT_EVERY seconds. That
also keeps Windows from greying the window out as not responding.
"""

import time

from PySide6.QtCore import QEvent, QEventLoop
from PySide6.QtWidgets import QApplication, QFrame, QLabel, QProgressBar, QVBoxLayout

PAINT_EVERY = 0.05  # seconds
STEPS = 1000  # the bar's range


class LoadingPanel(QFrame):
	"""start(title), then say(text, fraction) as the work goes on (the panel shows at the first), then finish()."""

	def __init__(self, parent):
		super().__init__(parent)
		self.setObjectName("loadingPanel")
		self.setStyleSheet("#loadingPanel { background: palette(window); border: 1px solid palette(mid); border-radius: 6px; }")
		self.setFixedWidth(340)
		layout = QVBoxLayout(self)
		layout.setContentsMargins(16, 12, 16, 12)
		self.title = QLabel()
		font = self.title.font()
		font.setBold(True)
		self.title.setFont(font)
		self.bar = QProgressBar()
		self.bar.setRange(0, STEPS)
		self.bar.setTextVisible(False)
		self.step = QLabel()
		for widget in (self.title, self.bar, self.step):
			layout.addWidget(widget)
		self.hide()
		self._painted = 0.0
		parent.installEventFilter(self)

	def start(self, title):
		self.title.setText(title)
		self.bar.setValue(0)
		self.step.setText("")

	def say(self, text, fraction):
		"""What is being done, and how far along the whole is (0 to 1)."""
		first = self.isHidden()
		if first:
			self._place()
			self.show()
			self.raise_()
		self.step.setText(text)
		self.bar.setValue(round(min(max(fraction, 0.0), 1.0) * STEPS))
		now = time.monotonic()
		if first or now - self._painted >= PAINT_EVERY:
			self._painted = now
			QApplication.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)

	def finish(self):
		self.hide()

	def _place(self):
		self.adjustSize()
		parent = self.parentWidget()
		self.move((parent.width() - self.width()) // 2, (parent.height() - self.height()) // 2)

	def eventFilter(self, watched, event):
		if watched is self.parentWidget() and event.type() == QEvent.Type.Resize and not self.isHidden():
			self._place()
		return False
