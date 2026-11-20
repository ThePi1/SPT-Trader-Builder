"""The height slider beside the 3D view: everything above its height is hidden, to look inside buildings.

At the top ("All") nothing is hidden. Dragging it down peels the map from the top; it snaps to the storeys at the
middle of the view (set_storeys: the floors' heights, ticked on the track), stopping STOREY_VIEW metres above a storey's
floor so that storey shows with its walls and the one above is hidden. Shift drags it freely. The wheel and the arrow
keys go a storey at a time; Home or a double-click shows everything again.

The track spans the map, from its lowest floor to STOREY_VIEW above its highest (set_range; the tab leaves out
rooftops high above everything else, see maps.triangles.Triangles.floor_range): it stays the same wherever the view
looks; only the storeys ticked on it change.
"""

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPalette, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

STOREY_VIEW = 2.2  # metres above a storey's floor that the slider stops at: that storey shows, the one above is hidden
UNDER_NEXT = 0.3  # metres under the next storey's floor it stops at when that is nearer than STOREY_VIEW
FREE_STEP = 1.0  # metres a wheel step or arrow key moves it where no storeys are known
LABEL_GAP = 12  # pixels: a storey's height is written only this far from the last one written
SNAP_PIXELS = 10  # how near (in pixels) a drag must come to a storey's stop to land on it
WIDTH = 58
TOP, ALL_GAP, BOTTOM = 14, 26, 14  # pixels: "All" sits TOP down, the heights start ALL_GAP below it and end BOTTOM above the edge


class CutSlider(QWidget):
	cut_changed = Signal(object)  # the height everything above is hidden from, or None for nothing hidden

	def __init__(self, parent=None):
		super().__init__(parent)
		self.low, self.high = 0.0, 10.0
		self.storeys = []
		self._value = None
		self._dragging = False
		self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
		self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
		self.setAccessibleName("Hide above")
		self.setToolTip(
			"Hide everything above a height, to see inside buildings.\n"
			"Drag it down: it stops at the storeys at the middle of the view (Shift: anywhere).\n"
			"Wheel or arrow keys: a storey at a time. Double-click or Home: show everything."
		)

	def sizeHint(self):
		return QSize(WIDTH, 320)

	def minimumSizeHint(self):
		return QSize(WIDTH, 140)

	# --- what it shows ------------------------------------------------------------------------------------
	def set_range(self, low, high):
		"""The heights the track spans: the map's lowest floor to above its highest."""
		self.low, self.high = float(low), max(float(high), float(low) + 1.0)
		self.update()

	def set_storeys(self, storeys):
		"""The floors' heights of the storeys at the middle of the view, ticked on the track (it stops above them)."""
		self.storeys = sorted(float(s) for s in storeys)
		self.update()

	def value(self):
		return self._value

	def set_value(self, value, emit=True):
		"""Hide above this height, or None: nothing hidden."""
		if value is not None:
			value = round(float(value), 2)
		if value == self._value:
			return
		self._value = value
		self.update()
		if emit:
			self.cut_changed.emit(value)

	def stops(self):
		"""Where it stops for each storey: STOREY_VIEW above its floor, or just under the next storey's floor."""
		found = []
		for i, floor in enumerate(self.storeys):
			stop = floor + STOREY_VIEW
			if i + 1 < len(self.storeys):
				stop = min(stop, max(self.storeys[i + 1] - UNDER_NEXT, floor + UNDER_NEXT))
			if self.low <= stop <= self.high:
				found.append(round(stop, 2))
		return found

	def step(self, up):
		"""Up or down to the next stop (a storey, or FREE_STEP metres where there are none); up from the top one shows everything."""
		stops = self.stops()
		current = self._value
		if not stops:
			if current is None:
				target = None if up else self.high
			else:
				target = current + FREE_STEP if up else current - FREE_STEP
				target = None if target > self.high else target
		elif up:
			above = [s for s in stops if current is not None and s > current + 0.05]
			target = above[0] if above else None
		else:
			below = [s for s in stops if current is None or s < current - 0.05]
			target = below[-1] if below else stops[0]
		self.set_value(target)

	# --- heights and pixels -------------------------------------------------------------------------------
	def _track(self):
		"""(y of the top of the heights, y of the bottom) in pixels."""
		return TOP + ALL_GAP, max(TOP + ALL_GAP + 20, self.height() - BOTTOM)

	def y_of(self, height):
		"""The pixel row of a height (None: the "All" stop at the top)."""
		if height is None:
			return TOP
		top, bottom = self._track()
		t = (height - self.low) / (self.high - self.low)
		return bottom - min(max(t, 0.0), 1.0) * (bottom - top)

	def height_at(self, y, free=False):
		"""The height at a pixel row (None above the track: nothing hidden), on a storey's stop when near one unless free."""
		top, bottom = self._track()
		if y < top - ALL_GAP / 2:
			return None
		height = self.low + (bottom - min(max(y, top), bottom)) / (bottom - top) * (self.high - self.low)
		if not free:
			near = [(abs(self.y_of(s) - y), s) for s in self.stops()]
			if near and min(near)[0] <= SNAP_PIXELS:
				return min(near)[1]
		return height

	# --- mouse and keys -----------------------------------------------------------------------------------
	def mousePressEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton:
			self._dragging = True
			self._drag_to(event)
		event.accept()

	def mouseMoveEvent(self, event):
		if self._dragging and event.buttons() & Qt.MouseButton.LeftButton:
			self._drag_to(event)

	def mouseReleaseEvent(self, event):
		self._dragging = False

	def mouseDoubleClickEvent(self, event):
		self.set_value(None)

	def _drag_to(self, event):
		free = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
		self.set_value(self.height_at(event.position().y(), free=free))

	def wheelEvent(self, event):
		steps = round(event.angleDelta().y() / 120)
		for _ in range(abs(steps)):
			self.step(steps > 0)
		event.accept()

	def keyPressEvent(self, event):
		key = event.key()
		if key in (Qt.Key.Key_Up, Qt.Key.Key_PageUp):
			self.step(True)
		elif key in (Qt.Key.Key_Down, Qt.Key.Key_PageDown):
			self.step(False)
		elif key == Qt.Key.Key_Home:
			self.set_value(None)
		elif key == Qt.Key.Key_End:
			stops = self.stops()
			self.set_value(stops[0] if stops else self.low)
		else:
			super().keyPressEvent(event)

	# --- drawing ------------------------------------------------------------------------------------------
	def paintEvent(self, event):
		painter = QPainter(self)
		painter.setRenderHint(QPainter.RenderHint.Antialiasing)
		pal = self.palette()
		painter.fillRect(self.rect(), pal.color(QPalette.ColorRole.Window))
		text, shown, hidden = pal.color(QPalette.ColorRole.WindowText), pal.color(QPalette.ColorRole.Highlight), QColor(pal.color(QPalette.ColorRole.Mid))
		font = QFont(self.font())
		font.setPointSizeF(max(6.5, font.pointSizeF() * 0.85))
		painter.setFont(font)
		x = self.width() - 14.0
		top, bottom = self._track()
		handle = self.y_of(self._value)
		# the track: what is shown (below the handle) strong, what is hidden (above it) faint
		painter.setPen(QPen(hidden, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
		painter.drawLine(QPointF(x, top), QPointF(x, bottom))
		painter.setPen(QPen(shown, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
		painter.drawLine(QPointF(x, min(max(handle, top), bottom)), QPointF(x, bottom))
		painter.setPen(Qt.PenStyle.NoPen)
		painter.setBrush(shown if self._value is None else hidden)
		painter.drawEllipse(QPointF(x, TOP), 4, 4)  # (the "All" stop)
		muted = QColor(text)
		muted.setAlphaF(0.75)
		if self._value is not None:
			painter.setPen(muted)
			painter.drawText(QRectF(0, TOP - 8, x - 10, 16), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, "All")
		# the storeys at the middle of the view (from the top, so the highest ones' heights are written when they're close)
		written = None
		for floor in reversed(self.storeys):
			if not self.low <= floor <= self.high:
				continue
			y = self.y_of(floor)
			painter.setPen(QPen(text, 1.5))
			painter.drawLine(QPointF(x - 7, y), QPointF(x + 7, y))
			if written is not None and y - written < LABEL_GAP:
				continue
			written = y
			painter.setPen(muted)
			painter.drawText(QRectF(0, y - 8, x - 10, 16), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"{floor:.1f}")
		# the handle, with what it hides above
		label = "All" if self._value is None else f"{self._value:.1f} m"
		rect = QRectF(2, handle - 9, self.width() - 4, 18)
		painter.setPen(QPen(shown.darker(130), 1))
		painter.setBrush(shown)
		painter.drawRoundedRect(rect, 5, 5)
		painter.setPen(pal.color(QPalette.ColorRole.HighlightedText))
		painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, label)
		if self.hasFocus():
			painter.setPen(QPen(shown, 1, Qt.PenStyle.DotLine))
			painter.setBrush(Qt.BrushStyle.NoBrush)
			painter.drawRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5))
		painter.end()
