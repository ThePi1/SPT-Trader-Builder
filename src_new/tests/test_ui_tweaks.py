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


def test_the_more_buttons_are_outlined_buttons_without_a_caret(app):
	panel = QuestTextPanel(Document({}), quest("a" * 24, "Q"))
	form = FormWidget(registry.spec_of({"conditionType": "Level"}, "task"))
	for button in (panel.more_button, form.more_button):
		assert isinstance(button, MoreButton) and button.isCheckable()
		assert "border" in button.styleSheet() and button.cursor().shape() == Qt.CursorShape.PointingHandCursor
		assert button.arrowType() == Qt.ArrowType.NoArrow  # (no caret: the outline says it is a button)
		assert button.toolButtonStyle() == Qt.ToolButtonStyle.ToolButtonTextOnly
		button.setChecked(True)
		assert button.isChecked()
		button.setChecked(False)
	assert form.more_button.text() == "More options"
	panel.more_button.setChecked(True)
	assert panel.more_box.isVisibleTo(panel)
	panel.resize(600, 300)
	panel.show()
	assert panel.more_button.width() < 200  # (it is not stretched across the panel)


# --- Spec.common, the explorer's line about it, and the setting that greys uncommon fields ------

def spec_item(page, common):
	"""The tree item of the first type whose Spec.common is this."""
	for i in range(page.tree.topLevelItemCount()):
		top = page.tree.topLevelItem(i)
		for j in range(top.childCount()):
			if top.child(j).data(0, 256).common is common:
				return top.child(j)


def grey_rows(page):
	return [r for r in range(page.table.rowCount()) if page.table.item(r, 0).foreground().style() != Qt.BrushStyle.NoBrush]


def test_spec_common_replaces_everyday():
	from schema.fields import Spec
	from schema import registry

	assert "common" in Spec.__dataclass_fields__ and "everyday" not in Spec.__dataclass_fields__
	assert Spec.__dataclass_fields__["common"].default is True
	kinds = registry.kinds("task")
	assert all(s.common for s in registry.kinds("task", common_only=True))
	flags = [s.common for s in kinds]
	assert flags == sorted(flags, reverse=True) and False in flags  # (the common kinds come first)
	assert registry.kinds("reward")[0].common and not registry.spec_for("task", "SellItemToTrader").common


def test_the_type_list_has_no_rare_tag_and_a_line_says_whether_it_is_common(app):
	from ui.explorer_tab import BrowsePage

	page = BrowsePage()
	labels = [page.tree.topLevelItem(i).child(j).text(0) for i in range(page.tree.topLevelItemCount()) for j in range(page.tree.topLevelItem(i).childCount())]
	assert labels and not [text for text in labels if "(rare)" in text or "(less common)" in text]
	page.tree.setCurrentItem(spec_item(page, True))
	assert page.commonLabel.text() == "This type is marked as commonly used."
	page.tree.setCurrentItem(spec_item(page, False))
	assert page.commonLabel.text() == "This type is marked as not commonly used."
	page.tree.setCurrentItem(None)
	assert page.commonLabel.text() == ""
	# it sits under the "Can be used" / "Filled in by the app" line
	layout = page.column
	order = [layout.itemAt(i).widget() for i in range(layout.count())]
	assert order.index(page.commonLabel) == order.index(page.where) + 1


def test_the_setting_greys_the_uncommon_fields_or_leaves_them_normal(app):
	from core.settings import Settings
	from ui.explorer_tab import BrowsePage
	from schema import explorer

	settings = Settings()
	assert settings.mark_uncommon_fields is True  # (on to start)
	page = BrowsePage(settings)
	quest = page.tree.topLevelItem(0).child(0)  # Quest: several uncommon fields
	page.tree.setCurrentItem(quest)
	expected = [r for r, row in enumerate(explorer.field_rows(quest.data(0, 256))) if row[5]]
	assert expected and grey_rows(page) == expected
	settings.mark_uncommon_fields = False
	page.refresh()
	assert grey_rows(page) == []  # (the same fields, in normal text)
	assert page.table.rowCount() > len(expected)
	settings.mark_uncommon_fields = True
	page.refresh()
	assert grey_rows(page) == expected


def test_the_setting_is_in_the_settings_window_and_the_file(app, tmp_path):
	import configparser

	from core import settings as S
	from ui.dialogs import SettingsDialog
	from PySide6.QtWidgets import QCheckBox

	dialog = SettingsDialog(S.Settings(), None)
	box = dialog.controls["mark_uncommon_fields"]
	assert isinstance(box, QCheckBox) and box.isChecked()
	parser = configparser.ConfigParser(interpolation=None)
	parser.read(S.SETTINGS_FILE, encoding="utf-8")
	assert parser.has_option("display", "mark_uncommon_fields")


def test_changing_the_setting_in_the_main_window_redraws_the_open_description(app, tmp_path, monkeypatch):
	from core.gamedata import GameData
	from core.paths import BUNDLED_DATABASE_DIR
	from core.settings import Settings
	from ui import updates
	from ui.main_window import MainWindow

	monkeypatch.setattr(updates, "fetch_remote_version", lambda config: None)
	win = MainWindow(Settings.load(tmp_path / "none.ini"), GameData(None, "en", BUNDLED_DATABASE_DIR))
	page = win.explorer_tab.browse
	page.tree.setCurrentItem(page.tree.topLevelItem(0).child(0))
	assert grey_rows(page)
	win.settings.mark_uncommon_fields = False
	page.refresh()
	assert grey_rows(page) == []
