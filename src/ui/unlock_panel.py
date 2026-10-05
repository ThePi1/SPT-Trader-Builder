"""For an Assort unlock reward in the Quests tab: what the open trader assort says about the reward's preview,
and buttons to fill the preview from an offer or bring it up to date."""

from PySide6.QtWidgets import QComboBox, QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

TONES = {"ok": "#2e7d32", "note": "#808080", "warn": "#b9770e"}


class UnlockOfferPanel(QGroupBox):
	"""state: (tone, message, offer id or None, differs) from schema.assort.unlock_state. offers: [(offer id, text)] of the open
	assort. on_fill(offer id) copies that offer into the preview; on_update(offer id) brings the preview in line with the offer
	the reward belongs to."""

	def __init__(self, state, offers, on_fill, on_update, parent=None):
		super().__init__("Trader offer", parent)
		tone, message, offer_id, differs = state
		layout = QVBoxLayout(self)
		self.status = QLabel(message)
		self.status.setWordWrap(True)
		self.status.setStyleSheet(f"color: {TONES.get(tone, TONES['note'])};")
		layout.addWidget(self.status)
		row = QHBoxLayout()
		self.combo = QComboBox()
		for offer, text in offers:
			self.combo.addItem(text, offer)
		self.fillButton = QPushButton("Use this offer's item")
		self.fillButton.setToolTip("Copy the offer's item and mods, trader level and trader into the preview")
		self.fillButton.setEnabled(bool(offers))
		self.fillButton.clicked.connect(lambda _checked=False: on_fill(self.combo.currentData()))
		self.updateButton = QPushButton("Update preview")
		self.updateButton.setToolTip("Make the preview the same as the offer it belongs to")
		self.updateButton.setVisible(bool(differs) and offer_id is not None)
		self.updateButton.clicked.connect(lambda _checked=False: on_update(offer_id))
		row.addWidget(self.combo, 1)
		row.addWidget(self.fillButton)
		row.addWidget(self.updateButton)
		layout.addLayout(row)
