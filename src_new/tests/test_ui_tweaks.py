"""The quest search, the trader level filter, the Locale panel and the More buttons."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel

from core.documents import Document
from schema import assort as A
from schema import locale as L
from schema import registry
from ui.assort_tab import AssortTab
from ui.forms import FormWidget
from ui.more_button import MoreButton
from ui.quest_outline import QuestOutline
from ui.text_panels import DEFAULT_FIELDS, QuestTextPanel, TaskTextPanel, TextBox

IDS = {name: str(i) * 24 for i, name in enumerate(("Debut", "Checking", "Shootout Picnic", "Delivery from the Past"), start=1)}


@pytest.fixture(scope="module")
def app():
	return QApplication.instance() or QApplication([])


def quest(quest_id, name):
	return {
		"_id": quest_id, "QuestName": name,
		"conditions": {"AvailableForStart": [], "Fail": [], "AvailableForFinish": []},
		"rewards": {"Success": [], "Started": [], "Fail": []},
	}


def make_outline(app):
	outline = QuestOutline(None, None)
	outline.set_document(Document({qid: quest(qid, name) for name, qid in IDS.items()}))
	outline.show()
	return outline


def shown(outline):
	return [outline.doc.data[outline.tree.topLevelItem(i).data(0, 256).path[0]]["QuestName"] for i in range(outline.tree.topLevelItemCount()) if not outline.tree.topLevelItem(i).isHidden()]


# --- the quest search -----------------------------------------------------------------------

def test_the_search_box_filters_the_quests_by_name(app):
	outline = make_outline(app)
	assert outline.search.placeholderText() == "Search quests by name" and len(shown(outline)) == 4
	outline.search.setText("check")
	assert shown(outline) == ["Checking"]
	outline.search.setText("DELIVERY past")  # (any case, every word must match)
	assert shown(outline) == ["Delivery from the Past"]
	outline.search.setText("")
	assert len(shown(outline)) == 4


def test_the_selection_follows_the_filter(app):
	outline = make_outline(app)
	outline._select_key(("quest", (IDS["Debut"],)))
	outline.search.setText("picnic")
	assert outline._current().path[0] == IDS["Shootout Picnic"]  # (the open quest was hidden: the first one shown opens)
	outline.search.setText("nothing like this")
	assert shown(outline) == [] and outline.tree.currentItem() is None
	assert "No quest matches" in outline.pane.findChild(QLabel).text()
	outline.search.setText("")
	assert len(shown(outline)) == 4


def test_hidden_quests_are_not_part_of_a_selection(app):
	outline = make_outline(app)
	outline.tree.selectAll()
	assert len(outline.selected_quest_ids()) == 4
	outline.search.setText("debut")
	assert outline.selected_quest_ids() == [IDS["Debut"]]


def test_the_filter_stays_when_the_quests_change_and_matches_the_source_file(app):
	outline = make_outline(app)
	outline.search.setText("debut")
	outline.doc.change("Add quest", lambda data: data.__setitem__("f" * 24, quest("f" * 24, "Another Debut")))
	assert sorted(shown(outline)) == ["Another Debut", "Debut"]
	outline.set_sources({IDS["Checking"]: "side_jobs.json"})
	outline.search.setText("side_jobs")
	assert shown(outline) == ["Checking"]


# --- the level filter on the Trader tab -----------------------------------------------------

def make_assort(levels):
	data = A.empty_assort()
	for i, level in enumerate(levels):
		A.add_offer(data, *A.new_offer(f"{i + 1:024x}", level=level, ids=lambda i=i: f"{i + 1:024d}"[:24]))
	return data


def test_the_level_filter_lists_only_the_offers_of_that_level(app):
	tab = AssortTab(Document(make_assort([1, 2, 2, 3, 4, 4, 4])), Document(A.empty_questassort()))
	assert [tab.levelFilter.itemText(i) for i in range(tab.levelFilter.count())] == ["All levels", "Level 1", "Level 2", "Level 3", "Level 4"]
	assert tab.list.count() == 7 and tab.note.text().startswith("7 of 7 offers.")
	for level, expected in ((1, 1), (2, 2), (3, 1), (4, 3)):
		tab.levelFilter.setCurrentIndex(tab.levelFilter.findData(level))
		assert tab.list.count() == expected and tab.note.text().startswith(f"{expected} of 7 offers.")
		assert all(tab.doc.data["loyal_level_items"][tab.list.item(i).data(256)] == level for i in range(tab.list.count()))
		assert tab.current_id() is not None  # (an offer of that level is open)
	tab.levelFilter.setCurrentIndex(0)
	assert tab.list.count() == 7


def test_the_level_filter_combines_with_the_search_and_handles_an_empty_result(app):
	tab = AssortTab(Document(make_assort([1, 2, 3])), Document(A.empty_questassort()))
	tab.levelFilter.setCurrentIndex(tab.levelFilter.findData(2))
	tab.search.setText("zzz")
	assert tab.list.count() == 0 and tab.current_id() is None
	tab.search.setText("")
	assert tab.list.count() == 1
	tab.levelFilter.setCurrentIndex(tab.levelFilter.findData(4))
	assert tab.list.count() == 0 and tab.note.text().startswith("0 of 3 offers.")


# --- the Locale panel and the More buttons --------------------------------------------------

def test_the_locale_panel_shows_four_fields_in_order_and_the_rest_under_more_locale(app):
	locale = Document({})
	panel = QuestTextPanel(locale, quest("a" * 24, "Q"))
	assert panel.title() == "Locale"
	form = panel.layout().itemAt(0).layout()
	assert [form.itemAt(i, form.ItemRole.LabelRole).widget().text() for i in range(form.rowCount())] == [
		"Quest name", "Description", "Message on start", "Message on completion",
	]
	assert DEFAULT_FIELDS == ("name", "description", "startedMessageText", "successMessageText")
	assert panel.more_button.text() == "More locale" and not panel.more_box.isVisible()
	more = panel.more_box.layout()
	hidden = [more.itemAt(i, more.ItemRole.LabelRole).widget().text() for i in range(more.rowCount())]
	assert hidden == ["Reply when accepting", "Reply when declining", "Reply when completing", "Message on failure", "Message on change", "Note"]
	assert len(hidden) + 4 == len(L.QUEST_TEXT)  # (every kind of text is somewhere)


def test_the_text_boxes_of_the_panel_write_to_the_right_keys(app):
	locale = Document({})
	panel = QuestTextPanel(locale, quest("a" * 24, "Q"))
	boxes = {box.key: box for box in panel.findChildren(TextBox)}
	boxes[L.quest_key("a" * 24, "startedMessageText")].edit.setPlainText("Go!")
	assert locale.data[L.quest_key("a" * 24, "startedMessageText")] == "Go!"


def test_the_task_panel_is_called_locale_too(app):
	assert TaskTextPanel(Document({}), "b" * 24, "Finish").title() == "Locale"


def test_the_more_buttons_look_like_buttons_and_open_their_part(app):
	panel = QuestTextPanel(Document({}), quest("a" * 24, "Q"))
	form = FormWidget(registry.spec_of({"conditionType": "Level"}, "task"))
	for button in (panel.more_button, form.more_button):
		assert isinstance(button, MoreButton) and button.isCheckable()
		assert "border" in button.styleSheet() and button.cursor().shape() == Qt.CursorShape.PointingHandCursor
		assert button.arrowType() == Qt.ArrowType.DownArrow  # (a caret says it opens)
		assert button.toolButtonStyle() == Qt.ToolButtonStyle.ToolButtonTextBesideIcon  # (the caret sits beside the text)
		button.setChecked(True)
		assert button.arrowType() == Qt.ArrowType.UpArrow
		button.setChecked(False)
		assert button.arrowType() == Qt.ArrowType.DownArrow
	assert form.more_button.text() == "More options"
	panel.more_button.setChecked(True)
	assert panel.more_box.isVisibleTo(panel)
	panel.resize(600, 300)
	panel.show()
	assert panel.more_button.width() < 200  # (it is not stretched across the panel)
