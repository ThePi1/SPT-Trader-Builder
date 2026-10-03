"""The files strip along the bottom of the window: for each kind of file the program holds (quests, locale,
trader assort, quest locks) how much there is, whether it is saved, and which file Save writes to.
Clicking a segment opens its menu (New, Open, Import, Save, Save as)."""

from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QFrame, QMenu

from ui.compiled.ui_file_segment import Ui_FileSegmentForm
from ui.compiled.ui_files_strip import Ui_FilesStripForm

TONES = {"ok": "#2e7d32", "warn": "#b9770e", "muted": "#808080"}


class FileSegment(QFrame, Ui_FileSegmentForm):
	"""One kind of file. The layout is ui/designer/file_segment.ui; the numbers and words are set from the window."""

	def __init__(self, title, parent=None):
		super().__init__(parent)
		self.setupUi(self)
		self.title = title
		self.menu = QMenu(self)
		self.set_info(0, "empty", "muted", "empty")

	def set_info(self, count, state, tone, file_text, tip=""):
		self.titleLabel.setText(f"<b>{self.title}</b> &nbsp;{count:,}".replace(",", " "))
		self.stateLabel.setText(f'<span style="color: {TONES.get(tone, TONES["muted"])};">{state}</span>' if state else "")
		self.fileLabel.setText(file_text)
		self.setToolTip(tip or file_text)

	def show_menu(self):
		"""Open the menu above the segment (the strip is at the bottom of the window)."""
		height = self.menu.sizeHint().height()
		self.menu.exec(self.mapToGlobal(QPoint(0, -height)))

	def mousePressEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton:
			self.show_menu()
		else:
			super().mousePressEvent(event)

	def keyPressEvent(self, event):
		if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space, Qt.Key.Key_Down, Qt.Key.Key_Up):
			self.show_menu()
		else:
			super().keyPressEvent(event)


class FilesStrip(QFrame, Ui_FilesStripForm):
	"""The row of segments. The frame is ui/designer/files_strip.ui; the segments are added here."""

	def __init__(self, kinds, parent=None):
		"""kinds: [(key, title)] in the order they are shown."""
		super().__init__(parent)
		self.setupUi(self)
		self.segments = {}
		for key, title in kinds:
			segment = FileSegment(title)
			self.segments[key] = segment
			self.segmentsLayout.addWidget(segment, 1)

	def segment(self, key):
		return self.segments[key]
