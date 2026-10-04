import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication, QTableWidget

from core.documents import Document
from schema import assort as A
from schema.issues import errors
from ui.assort_tab import AssortTab


@pytest.fixture(scope="module")
def app():
	return QApplication.instance() or QApplication([])


def make(assort=None):
	picks = {"item": ["a" * 24], "part": ["a" * 24], "quest": ["b" * 24]}
	assort_doc = Document(assort or A.empty_assort())
	locks = Document(A.empty_questassort())
	tab = AssortTab(assort_doc, locks, None, lambda ref, multi, parent: picks[ref])
	return tab, assort_doc, locks


def test_add_copy_delete_offer_and_undo(app):
	tab, doc, locks = make()
	tab.add_offer()
	assert len(A.offer_ids(doc.data)) == 1 and not A.validate_assort(doc.data)
	tab.copy_offer()
	assert len(A.offer_ids(doc.data)) == 2 and not A.validate_assort(doc.data)
	doc.undo()
	assert len(A.offer_ids(doc.data)) == 1
	tab.refresh()
	from PySide6.QtWidgets import QMessageBox

	QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)
	tab.delete_offer()
	assert doc.data == A.empty_assort()


def test_price_level_and_quest_lock(app):
	tab, doc, locks = make()
	tab.add_offer()
	offer = tab.current_id()
	tab._add_price(offer, [A.MONEY["dollars"]])
	assert doc.data["barter_scheme"][offer][0][-1] == {"count": 1, "_tpl": A.MONEY["dollars"]}
	table = tab.right.findChild(QTableWidget)
	table.item(0, 1).setText("2500")
	assert doc.data["barter_scheme"][offer][0][0]["count"] == 2500
	from PySide6.QtWidgets import QComboBox, QPushButton

	box = tab._lock_box(offer)
	combo = box.findChild(QComboBox)
	combo.setCurrentIndex(combo.findData("success"))
	combo.activated.emit(combo.currentIndex())
	find = next(b for b in box.findChildren(QPushButton) if b.text() == "Find...")
	find.click()
	assert locks.data["success"] == {offer: "b" * 24}
	assert not errors(A.validate_questassort(locks.data, doc.data))
	assert "[quest]" in tab.list.item(0).text()


def test_vanilla_assort_opens(app, vanilla_assort):
	tab, doc, locks = make(vanilla_assort)
	assert tab.list.count() == 589
	before = repr(doc.data)
	for i in range(0, 589, 60):
		tab.list.setCurrentRow(i)
	assert repr(doc.data) == before
