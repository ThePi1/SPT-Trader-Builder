"""Importing and exporting quests, locales and items.json from the main window."""

import json

import pytest
from PySide6.QtWidgets import QMessageBox

from builders import quests as quest_builder
from utils import read_json
from windows import main_window as mw

RUSSIAN = "Привет, Прапор! Задание №1"


def make_quest(quest_id="q1", name="My Quest", condition_id="c1"):
	quest = quest_builder.quest(
		quest_id,
		name=name,
		can_show_notifications=True,
		finish_conditions=[{"id": condition_id}],
		start_conditions=[],
		fail_conditions=[],
		image="/i.jpg",
		instant_complete=False,
		location="any",
		restartable=False,
		rewards={"Fail": [], "Started": [], "Success": []},
		secret_quest=False,
		side="pmc",
		trader_id="trader",
		quest_type="Completion",
	)
	return {quest_id: quest}


@pytest.fixture
def win(main_window, monkeypatch):
	"""The main window with every message box recorded instead of shown."""
	main_window.errors = []
	main_window.popups = []
	monkeypatch.setattr(
		QMessageBox, "critical", staticmethod(lambda parent, title, text: main_window.errors.append((title, text)))
	)
	monkeypatch.setattr(main_window, "popup", lambda message: main_window.popups.append(message))
	return main_window


def choose(monkeypatch, *paths):
	"""Successive answers from the main window's file dialogs (None = the user cancelled)."""
	queue = list(paths)

	def fake(method, title, **options):
		path = queue.pop(0)
		return (str(path), True) if path is not None else (None, False)

	monkeypatch.setattr(mw, "safe_file_dialog", fake)
	return queue


def write(path, data, encoding="utf-8"):
	path.write_bytes(json.dumps(data, ensure_ascii=False).encode(encoding))
	return path


def quest_list_texts(win):
	return [win.ui.questList.item(i).text() for i in range(win.ui.questList.count())]


# --- importing quests --------------------------------------------------------------------


def test_importing_a_quest_file_adds_the_quests(win, monkeypatch, tmp_path):
	choose(monkeypatch, write(tmp_path / "q.json", make_quest("q1", "First")))
	win.importQuests()
	assert quest_list_texts(win) == ["First, q1"]
	assert "q1" in win.state.quests and win.errors == []


def test_a_file_that_is_not_json_shows_an_error_instead_of_crashing(win, monkeypatch, tmp_path):
	bad = tmp_path / "bad.json"
	bad.write_text("{ this is not json", encoding="utf-8")
	choose(monkeypatch, bad)
	win.importQuests()  # must not raise
	assert quest_list_texts(win) == [] and win.state.quests == {}
	assert len(win.errors) == 1 and "bad.json" in win.errors[0][1]


@pytest.mark.parametrize(
	"content",
	[[1, 2, 3], {"q1": "not a quest"}, {"q1": {"no_name": True}}, "just a string", 42],
	ids=["list", "value-not-a-dict", "no-QuestName", "string", "number"],
)
def test_json_that_is_not_a_quest_file_shows_an_error(win, monkeypatch, tmp_path, content):
	choose(monkeypatch, write(tmp_path / "x.json", content))
	win.importQuests()
	assert win.state.quests == {} and len(win.errors) == 1
	assert "quest file" in win.errors[0][1]


def test_a_missing_file_shows_an_error(win, monkeypatch, tmp_path):
	choose(monkeypatch, tmp_path / "gone.json")
	win.importQuests()
	assert len(win.errors) == 1


def test_cancelling_the_import_does_nothing(win, monkeypatch):
	choose(monkeypatch, None)
	win.importQuests()
	assert win.errors == [] and quest_list_texts(win) == []


def test_importing_the_same_file_twice_does_not_duplicate_the_list(win, monkeypatch, tmp_path):
	f = write(tmp_path / "q.json", make_quest("q1", "First"))
	choose(monkeypatch, f, f)
	win.importQuests()
	win.importQuests()
	assert quest_list_texts(win) == ["First, q1"]
	assert len(win.state.quests) == 1


def test_importing_an_updated_quest_replaces_the_old_one(win, monkeypatch, tmp_path):
	choose(monkeypatch, write(tmp_path / "a.json", make_quest("q1", "Old name")), write(tmp_path / "b.json", make_quest("q1", "New name")))
	win.importQuests()
	win.importQuests()
	assert quest_list_texts(win) == ["New name, q1"]
	assert win.state.quests["q1"]["QuestName"] == "New name"


def test_a_cancelled_analysis_and_a_bad_file_do_not_crash(win, monkeypatch, tmp_path):
	choose(monkeypatch, None)
	win.analyze_cc()
	bad = tmp_path / "bad.json"
	bad.write_text("[[[", encoding="utf-8")
	choose(monkeypatch, bad)
	win.analyze_cc()
	assert len(win.errors) == 1


# --- russian text ----------------------------------------------------------------------------


def test_a_utf8_quest_file_with_russian_text_imports(win, monkeypatch, tmp_path):
	choose(monkeypatch, write(tmp_path / "q.json", make_quest("q1", RUSSIAN)))
	win.importQuests()
	assert quest_list_texts(win) == [f"{RUSSIAN}, q1"]


def test_a_quest_file_in_the_russian_code_page_imports(win, monkeypatch, tmp_path):
	choose(monkeypatch, write(tmp_path / "q.json", make_quest("q1", RUSSIAN), encoding="cp866"))
	win.importQuests()
	assert quest_list_texts(win) == [f"{RUSSIAN}, q1"] and win.errors == []


def test_exporting_quests_keeps_russian_readable_in_the_file(win, monkeypatch, tmp_path):
	out = tmp_path / "out.json"
	choose(monkeypatch, out, None)  # save here; then decline the locale step
	win.exportAll(make_quest("q1", RUSSIAN))
	assert RUSSIAN in out.read_bytes().decode("utf-8")
	assert read_json(out)["q1"]["QuestName"] == RUSSIAN


def test_a_locale_file_with_russian_text_keeps_it(win, monkeypatch, tmp_path):
	quest_file = write(tmp_path / "q.json", make_quest("q1"))
	locale_file = write(tmp_path / "ru.json", {"existing key": RUSSIAN})
	assert win.createLocaleFromJSON(str(quest_file), str(locale_file)) == "updated"
	text = locale_file.read_bytes().decode("utf-8")
	assert RUSSIAN in text  # still readable, not turned into \u escapes
	assert read_json(locale_file)["existing key"] == RUSSIAN
	assert "q1 name" in read_json(locale_file)


def test_a_locale_file_in_the_russian_code_page_is_read_and_saved_as_utf8(win, monkeypatch, tmp_path):
	quest_file = write(tmp_path / "q.json", make_quest("q1"))
	locale_file = write(tmp_path / "ru.json", {"existing key": RUSSIAN}, encoding="cp866")
	assert win.createLocaleFromJSON(str(quest_file), str(locale_file)) == "updated"
	assert json.loads(locale_file.read_bytes().decode("utf-8"))["existing key"] == RUSSIAN


def test_items_json_with_russian_names_loads(win, monkeypatch, tmp_path):
	items = {"a": {"_parent": "root", "_name": RUSSIAN}}
	choose(monkeypatch, write(tmp_path / "items.json", items, encoding="cp866"))
	assert win.loadItemsJSON() is True
	assert win.state.items["a"]["_name"] == RUSSIAN


# --- the locale step: what it reports -----------------------------------------------------------


def test_locale_update_reports_updated(win, tmp_path):
	quest_file = write(tmp_path / "q.json", make_quest("q1"))
	locale_file = write(tmp_path / "en.json", {"keep": "me"})
	assert win.createLocaleFromJSON(str(quest_file), str(locale_file)) == "updated"
	locale = read_json(locale_file)
	assert locale["keep"] == "me" and locale["q1 name"] == "" and locale["c1"] == ""


def test_a_cancelled_locale_dialog_reports_cancelled(win, monkeypatch, tmp_path):
	quest_file = write(tmp_path / "q.json", make_quest("q1"))
	choose(monkeypatch, None)
	assert win.createLocaleFromJSON(q_file=str(quest_file)) == "cancelled"
	assert win.errors == []


def test_a_cancelled_quest_dialog_reports_cancelled(win, monkeypatch):
	choose(monkeypatch, None)
	assert win.createLocaleFromJSON() == "cancelled"


@pytest.mark.parametrize(
	"locale_text",
	["{ not json", "[1, 2]", '"just text"'],
	ids=["bad-json", "not-a-dict", "string"],
)
def test_an_unusable_locale_file_reports_failed_with_an_error(win, tmp_path, locale_text):
	quest_file = write(tmp_path / "q.json", make_quest("q1"))
	locale_file = tmp_path / "en.json"
	locale_file.write_text(locale_text, encoding="utf-8")
	assert win.createLocaleFromJSON(str(quest_file), str(locale_file)) == "failed"
	assert len(win.errors) == 1 and "en.json" in win.errors[0][1]
	assert locale_file.read_text(encoding="utf-8") == locale_text  # left as it was


def test_a_missing_locale_file_reports_failed(win, tmp_path):
	quest_file = write(tmp_path / "q.json", make_quest("q1"))
	assert win.createLocaleFromJSON(str(quest_file), str(tmp_path / "gone.json")) == "failed"
	assert len(win.errors) == 1


def test_a_bad_quest_file_reports_failed(win, tmp_path):
	bad = tmp_path / "bad.json"
	bad.write_text("{{", encoding="utf-8")
	locale_file = write(tmp_path / "en.json", {})
	assert win.createLocaleFromJSON(str(bad), str(locale_file)) == "failed"
	assert read_json(locale_file) == {}


def test_the_menu_item_only_celebrates_a_real_update(win, monkeypatch, tmp_path):
	quest_file = write(tmp_path / "q.json", make_quest("q1"))
	locale_file = write(tmp_path / "en.json", {})
	choose(monkeypatch, quest_file, locale_file)
	win.onCreateLocale()
	assert win.popups == ["The locale has been successfully updated."]

	win.popups.clear()
	choose(monkeypatch, quest_file, None)  # no locale chosen
	win.onCreateLocale()
	assert win.popups == []


# --- exporting quests: what the user is told ------------------------------------------------------


def test_a_good_export_reports_both_steps(win, monkeypatch, tmp_path):
	out = tmp_path / "out.json"
	locale_file = write(tmp_path / "en.json", {})
	choose(monkeypatch, out, locale_file, locale_file)  # save the quests; open the locale, save it over itself
	win.exportAll(make_quest("q1"))
	assert len(win.popups) == 2
	assert str(out) in win.popups[0] and "successfully" in win.popups[0]
	assert str(locale_file) in win.popups[1] and "successfully" in win.popups[1]
	assert "q1 name" in read_json(locale_file)


def test_export_without_a_locale_file_does_not_claim_the_locale_was_updated(win, monkeypatch, tmp_path):
	out = tmp_path / "out.json"
	choose(monkeypatch, out, None)
	win.exportAll(make_quest("q1"))
	assert out.exists()
	assert win.popups[1:] == ["The locale was not saved, because no locale file was chosen."]


def test_export_with_a_broken_locale_file_shows_the_error_not_a_success(win, monkeypatch, tmp_path):
	out = tmp_path / "out.json"
	bad_locale = tmp_path / "en.json"
	bad_locale.write_text("{ nope", encoding="utf-8")
	choose(monkeypatch, out, bad_locale)
	win.exportAll(make_quest("q1"))
	assert len(win.popups) == 1  # (just the quest file's)
	assert len(win.errors) == 1 and "en.json" in win.errors[0][1]


def test_a_quest_file_that_cannot_be_written_skips_the_locale_step(win, monkeypatch, tmp_path):
	queue = choose(monkeypatch, tmp_path / "no_such_folder" / "out.json", tmp_path / "en.json")
	win.exportAll(make_quest("q1"))
	assert len(win.errors) == 1 and win.popups == []
	assert len(queue) == 1  # the locale dialog was never asked for


def test_cancelling_the_export_does_nothing(win, monkeypatch):
	choose(monkeypatch, None)
	win.exportAll(make_quest("q1"))
	assert win.popups == [] and win.errors == []


def test_the_exported_quest_file_is_the_same_json_as_before(win, monkeypatch, tmp_path):
	quests = make_quest("q1", "Plain")
	out = tmp_path / "out.json"
	choose(monkeypatch, out, None)
	win.exportAll(quests)
	assert out.read_text(encoding="utf-8") == json.dumps(quests, indent=4)


# --- items.json ------------------------------------------------------------------------------------


def test_loading_items_json_replaces_the_previous_one(win, monkeypatch, tmp_path):
	choose(monkeypatch, write(tmp_path / "a.json", {"x": {"_parent": ""}}), write(tmp_path / "b.json", {"y": {"_parent": ""}, "z": {"_parent": ""}}))
	assert win.loadItemsJSON() is True
	assert win.loadItemsJSON() is True
	assert set(win.state.items) == {"y", "z"}


def test_cancelling_keeps_the_items_already_loaded(win, monkeypatch, tmp_path):
	choose(monkeypatch, write(tmp_path / "a.json", {"x": {"_parent": ""}}), None)
	win.loadItemsJSON()
	assert win.loadItemsJSON() is False
	assert set(win.state.items) == {"x"}


def test_a_bad_items_file_keeps_the_items_already_loaded(win, monkeypatch, tmp_path):
	bad = tmp_path / "bad.json"
	bad.write_text("{ nope", encoding="utf-8")
	choose(monkeypatch, write(tmp_path / "a.json", {"x": {"_parent": ""}}), bad)
	win.loadItemsJSON()
	assert win.loadItemsJSON() is False
	assert set(win.state.items) == {"x"} and len(win.errors) == 1


def test_a_file_that_is_not_an_items_dictionary_is_rejected(win, monkeypatch, tmp_path):
	before = win.state.items
	choose(monkeypatch, write(tmp_path / "list.json", [1, 2]))
	assert win.loadItemsJSON() is False
	assert win.state.items is before and len(win.errors) == 1  # (what was in use stays in use)


# --- weapon presets ------------------------------------------------------------------------------------


def test_a_weapon_preset_that_cannot_be_saved_shows_an_error_and_asks_again_next_time(win, tmp_path):
	win.weapon_preset_filename = str(tmp_path / "no_such_folder" / "preset.json")
	win.exportWeaponPresets([{"a": {}}])
	assert len(win.errors) == 1
	assert win.weapon_preset_filename is None
