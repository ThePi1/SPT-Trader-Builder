"""The settings that change what the window does: copy the text to other languages, show the JSON."""

import json
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication

from core.documents import Document
from core.gamedata import GameData
from core.paths import BUNDLED_DATABASE_DIR
from core.settings import Settings
from schema import locale as L
from ui import updates
from ui.main_window import MainWindow
from ui.quest_outline import QuestOutline

QID = "a" * 24
TID = "b" * 24


@pytest.fixture(scope="module")
def app():
	return QApplication.instance() or QApplication([])


@pytest.fixture
def make_window(app, tmp_path, monkeypatch):
	monkeypatch.setattr(updates, "fetch_remote_version", lambda config: None)  # (no network in tests)

	def make(**values):
		ini = tmp_path / "settings.ini"
		ini.write_text("[general]\ndebug_logging = false\n", encoding="utf-8")
		settings = Settings.load(ini)
		for key, value in values.items():
			setattr(settings, key, value)
		return MainWindow(settings, GameData(None, "en", BUNDLED_DATABASE_DIR))

	return make


def quest():
	return {
		QID: {
			"_id": QID, "QuestName": "Mine",
			"conditions": {"AvailableForStart": [], "Fail": [], "AvailableForFinish": [{"id": TID, "conditionType": "Level"}]},
			"rewards": {"Success": [], "Started": [], "Fail": []},
		}
	}


def text_file(tmp_path, data, name="en.json"):
	path = tmp_path / name
	path.write_text(json.dumps(data), encoding="utf-8")
	return Document.open(path)


def test_saving_the_text_adds_the_open_quests_text_to_the_other_languages(make_window, tmp_path):
	window = make_window(copy_locale_to_all_languages=True)
	window._set_quests(Document(quest()))
	window._set_locale(text_file(tmp_path, {f"{QID} name": "Mine", TID: "Do it", "unrelated": "keep out", f"{QID} description": ""}))
	assert window.save_locale()
	ru = json.loads((tmp_path / "ru.json").read_text(encoding="utf-8"))
	assert ru == {f"{QID} name": "Mine", TID: "Do it"}  # (only the open quests' text, and not the blank one)
	assert not (tmp_path / "unrelated.json").exists() and len(list(tmp_path.glob("*.json"))) == 17  # (every language, en is the file itself)


def test_with_no_quests_open_all_of_the_text_is_copied(make_window, tmp_path):
	window = make_window(copy_locale_to_all_languages=True)
	window._set_locale(text_file(tmp_path, {"x": "one", "y": "two"}))
	window.save_locale()
	assert json.loads((tmp_path / "fr.json").read_text(encoding="utf-8")) == {"x": "one", "y": "two"}


def test_it_does_nothing_when_the_setting_is_off(make_window, tmp_path):
	window = make_window(copy_locale_to_all_languages=False)
	window._set_locale(text_file(tmp_path, {"x": "one"}))
	window.save_locale()
	assert [p.name for p in tmp_path.glob("*.json")] == ["en.json"]


def test_a_failure_is_shown_and_the_rest_still_happen(make_window, tmp_path, monkeypatch):
	shown = []
	monkeypatch.setattr("ui.main_window.QMessageBox.warning", lambda *args: shown.append(args[2]))
	(tmp_path / "ru.json").write_text("not json", encoding="utf-8")
	window = make_window(copy_locale_to_all_languages=True)
	window._set_locale(text_file(tmp_path, {"x": "one"}))
	assert window.save_locale()
	assert len(shown) == 1 and "ru.json" in shown[0]
	assert (tmp_path / "fr.json").is_file()


# --- the JSON preview -----------------------------------------------------------------------


def make_outline(app, show):
	class S:
		show_json_preview, show_all_fields, problems_collapsed = show, False, False

		def update(self, values):
			pass

	outline = QuestOutline(None, S())
	outline.set_document(Document(quest()))
	outline.show()
	return outline


def select(outline, kind):
	for item in outline._walk():
		if item.data(0, 256).kind == kind:
			outline.tree.setCurrentItem(item)
			return item


def test_json_preview_shows_the_selected_node(app):
	outline = make_outline(app, True)
	assert outline.json_view.isVisible()
	select(outline, "task")
	assert json.loads(outline.json_view.toPlainText()) == {"id": TID, "conditionType": "Level"}
	select(outline, "quest")
	assert json.loads(outline.json_view.toPlainText())["QuestName"] == "Mine"


def test_json_preview_follows_edits(app):
	outline = make_outline(app, True)
	select(outline, "quest")
	outline.doc.change("test", lambda node: node.__setitem__("QuestName", "Renamed"), path=(QID,))
	assert json.loads(outline.json_view.toPlainText())["QuestName"] == "Renamed"


def test_json_preview_is_hidden_unless_asked_for_and_follows_the_setting(app):
	outline = make_outline(app, False)
	assert not outline.json_view.isVisible()
	outline.settings.show_json_preview = True
	outline.apply_settings()
	assert outline.json_view.isVisible()
	outline.settings.show_json_preview = False
	outline.apply_settings()
	assert not outline.json_view.isVisible()


def test_unknown_old_settings_in_the_file_are_ignored(tmp_path):
	ini = tmp_path / "settings.ini"
	ini.write_text("[general]\nmerge_locales_on_export = true\ndebug_logging = true\n", encoding="utf-8")
	settings = Settings.load(ini)
	assert settings.debug_logging is True and not hasattr(settings, "merge_locales_on_export")
