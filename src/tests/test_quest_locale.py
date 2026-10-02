"""The Quest Builder's Locale tab, and saving the locale when quests are exported."""

import json

import pytest
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox, QPlainTextEdit

from modules.builders import quests
from modules.builders.quests import LOCALE_FIELDS
from modules.config import load_config
from modules.table_fields import find_row
from modules.utils import read_json
from modules.windows import main_window as mw
from modules.windows.quest import TASK_TEXT_COLUMN
from modules.windows.settings import Gui_SettingsDlg

# What each of LOCALE_FIELDS is called on the Locale tab
LABELS = {
	"name": "Name",
	"note": "Note",
	"acceptPlayerMessage": "Accept Player Message",
	"changeQuestMessageText": "Change Quest Message Text",
	"completePlayerMessage": "Complete Player Message",
	"declinePlayerMessage": "Decline Player Message",
	"description": "Description",
	"failMessageText": "Fail Message Text",
	"startedMessageText": "Started Message Text",
	"successMessageText": "Success Message Text",
}

NOT_SAVED = "The locale was not saved, because no locale file was chosen."


@pytest.fixture
def win(main_window, monkeypatch):
	"""The main window with every message box recorded instead of shown."""
	main_window.errors = []
	main_window.popups = []
	monkeypatch.setattr(
		QMessageBox, "critical", staticmethod(lambda parent, title, text: main_window.errors.append((title, text)))
	)
	monkeypatch.setattr(main_window, "popup", lambda title, message: main_window.popups.append(message))
	return main_window


def set_merging(window, on):
	"""Turn "Merge locales on export" on or off (whatever the shipped settings.ini says)."""
	config = window.state.config
	config.update_settings({**config.settings(), "merge_locales_on_export": "true" if on else "false"})


@pytest.fixture
def merge(win):
	"""The main window with "Merge locales on export" turned on."""
	set_merging(win, True)
	return win


@pytest.fixture
def no_merge(win):
	"""The main window with "Merge locales on export" turned off."""
	set_merging(win, False)
	return win


class Dialogs:
	"""Stands in for the main window's file dialogs: answers them in turn (None = the user
	cancelled) and records each one shown, as (title, options)."""

	def __init__(self, monkeypatch, *answers):
		self.answers = list(answers)
		self.asked = []
		monkeypatch.setattr(mw, "safe_file_dialog", self)

	def __call__(self, method, title, **options):
		self.asked.append((title, options))
		path = self.answers.pop(0)
		return (str(path), True) if path is not None else (None, False)

	@property
	def titles(self):
		return [title for title, _ in self.asked]


def write(path, data):
	path.write_text(json.dumps(data), encoding="utf-8")
	return path


def type_text(quest, field, text):
	box = quest.locale_field(field)
	if isinstance(box, QPlainTextEdit):
		box.setPlainText(text)
	else:
		box.setText(text)


def add_level_task(quest, level="10"):
	"""Add a Level task to the quest; returns the task's id."""
	task = quest.open_task_window()
	task.ui.fld_value_lv.setText(level)
	task.finalize("Level")
	return task.id


def set_task_text(quest, task_id, text):
	table = quest.ui.tb_cond_locale
	table.item(find_row(table, task_id), TASK_TEXT_COLUMN).setText(text)


def build_quest(win, texts=None, task_text=None):
	"""Make a quest with one Level task in the Quest Builder, type its locale text, and finalize it.

	Returns (quest id, task id).
	"""
	quest = win.spawnWindow("QuestBuilder")
	quest.ui.fld_quest_name.setText("My Quest")
	task_id = add_level_task(quest)
	for field, text in (texts or {}).items():
		type_text(quest, field, text)
	if task_text is not None:
		set_task_text(quest, task_id, task_text)
	quest.finalize()
	return quest.quest_id, task_id


def imported_quest_file(path):
	"""A quest file with quest q1 (one task, c1), as made outside this program."""
	quest = quests.quest(
		"q1",
		name="Imported",
		can_show_notifications=True,
		finish_conditions=[{"id": "c1"}],
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
	return write(path, {"q1": quest})


# --- the Locale tab ------------------------------------------------------------------------------


def test_the_quest_builder_has_a_quest_tab_and_a_locale_tab(main_window):
	tabs = main_window.spawnWindow("QuestBuilder").ui.tabs_quest
	assert [tabs.tabText(i) for i in range(tabs.count())] == ["Quest", "Locale"]


def test_every_locale_field_has_a_box_with_its_name(main_window):
	quest = main_window.spawnWindow("QuestBuilder")
	assert list(LABELS) == list(LOCALE_FIELDS)
	for field, label in LABELS.items():
		assert getattr(quest.ui, f"lb_loc_{field}").text() == label
		assert quest.locale_field(field).isEnabled()


def test_each_box_says_which_locale_key_it_is_saved_as(main_window):
	quest = main_window.spawnWindow("QuestBuilder")
	assert f'"{quest.quest_id} description"' in quest.locale_field("description").toolTip()


def test_the_quest_builder_is_big_enough_for_both_tabs(main_window):
	quest = main_window.spawnWindow("QuestBuilder")
	needed = quest.minimumSizeHint()
	assert needed.width() <= quest.width() and needed.height() <= quest.height()


def test_the_text_typed_is_saved_with_the_quest(win):
	quest_id, task_id = build_quest(
		win,
		texts={"name": "Debut", "description": "First line\nSecond line", "successMessageText": "Well done."},
		task_text="Reach level 10",
	)
	locale = win.state.quest_locales[quest_id]
	assert locale[f"{quest_id} name"] == "Debut"
	assert locale[f"{quest_id} description"] == "First line\nSecond line"
	assert locale[f"{quest_id} successMessageText"] == "Well done."
	assert locale[task_id] == "Reach level 10"
	assert locale[f"{quest_id} note"] == ""


def test_blank_text_does_not_stop_a_quest_being_finalized(win):
	quest_id, task_id = build_quest(win)
	assert quest_id in win.state.quests
	locale = win.state.quest_locales[quest_id]
	assert sorted(locale) == sorted([f"{quest_id} {field}" for field in LOCALE_FIELDS] + [task_id])
	assert set(locale.values()) == {""}


def test_each_task_gets_a_row_where_only_its_text_can_be_edited(main_window):
	quest = main_window.spawnWindow("QuestBuilder")
	task_id = add_level_task(quest)
	table = quest.ui.tb_cond_locale
	row = find_row(table, task_id)
	assert [table.item(row, col).text() for col in range(3)] == [task_id, "Start", "Level"]
	editable = [bool(table.item(row, col).flags() & Qt.ItemFlag.ItemIsEditable) for col in range(4)]
	assert editable == [False, False, False, True]


def test_removing_a_task_removes_its_text(win):
	quest = win.spawnWindow("QuestBuilder")
	kept, removed = add_level_task(quest, "5"), add_level_task(quest, "6")
	set_task_text(quest, kept, "kept text")
	set_task_text(quest, removed, "removed text")
	quest.ui.tb_cond.selectRow(find_row(quest.ui.tb_cond, removed))
	quest.ui.pb_rem_task.released.emit()
	assert quest.ui.tb_cond.rowCount() == 1 and quest.ui.tb_cond_locale.rowCount() == 1
	quest.finalize()
	locale = win.state.quest_locales[quest.quest_id]
	assert locale[kept] == "kept text" and removed not in locale


def test_remove_task_with_nothing_selected_does_nothing(main_window):
	quest = main_window.spawnWindow("QuestBuilder")
	add_level_task(quest)
	quest.ui.pb_rem_task.released.emit()
	assert quest.ui.tb_cond.rowCount() == 1 and quest.ui.tb_cond_locale.rowCount() == 1


def test_two_quest_builders_keep_their_text_separate(win):
	one, two = win.spawnWindow("QuestBuilder"), win.spawnWindow("QuestBuilder")
	type_text(one, "name", "one")
	type_text(two, "name", "two")
	one.finalize()
	two.finalize()
	assert win.state.quest_locales[one.quest_id][f"{one.quest_id} name"] == "one"
	assert win.state.quest_locales[two.quest_id][f"{two.quest_id} name"] == "two"


# --- the main window -------------------------------------------------------------------------------


def test_the_main_window_has_no_locale_tab(main_window):
	tabs = main_window.ui.main_tab
	assert [tabs.tabText(i) for i in range(tabs.count())] == ["Quests", "Weapon Builder", "ID Lookup"]
	assert not hasattr(main_window.ui, "locale_tab")
	assert not hasattr(main_window.ui, "actionLocale_Builder")


def test_removing_a_quest_drops_its_text(win):
	quest_id, _ = build_quest(win, texts={"name": "Gone"})
	win.ui.questList.item(0).setSelected(True)
	win.remove_selected_quest()
	assert quest_id not in win.state.quests and quest_id not in win.state.quest_locales


# --- exporting, merging into an existing locale ----------------------------------------------------


def test_merging_adds_the_entries_the_file_lacks_and_keeps_the_ones_it_has(merge, monkeypatch, tmp_path):
	quest_id, task_id = build_quest(
		merge, texts={"name": "Typed name", "description": "Typed description"}, task_text="Typed task"
	)
	existing = {"existing key": "existing value", f"{quest_id} name": "Name in the file"}
	base = write(tmp_path / "en.json", existing)
	merged = tmp_path / "merged.json"
	dialogs = Dialogs(monkeypatch, tmp_path / "quests.json", base, merged)
	merge.onExportQuests()
	assert dialogs.titles == ["Export Quest JSON", "Open Locale JSON to merge into", "Export Locale JSON"]
	locale = read_json(merged)
	assert locale["existing key"] == "existing value"
	assert locale[f"{quest_id} name"] == "Name in the file"  # (the file's text wins)
	assert locale[f"{quest_id} description"] == "Typed description"
	assert locale[task_id] == "Typed task"
	assert locale[f"{quest_id} note"] == ""
	assert read_json(base) == existing  # (saved somewhere else, so the opened file is left alone)
	assert merge.popups[1] == f"The locale export has completed successfully and can be found at {merged}."


def test_the_save_dialog_starts_at_the_opened_file_so_it_can_be_saved_over(merge, monkeypatch, tmp_path):
	quest_id, _ = build_quest(merge, texts={"name": "Typed name"})
	base = write(tmp_path / "en.json", {"existing key": "existing value"})
	dialogs = Dialogs(monkeypatch, tmp_path / "quests.json", base, base)
	merge.onExportQuests()
	assert dialogs.asked[2] == ("Export Locale JSON", {"dir": str(base)})
	locale = read_json(base)
	assert locale["existing key"] == "existing value" and locale[f"{quest_id} name"] == "Typed name"


def test_imported_quests_keep_the_text_already_in_the_locale_file(merge, monkeypatch, tmp_path):
	Dialogs(monkeypatch, imported_quest_file(tmp_path / "imported.json"))
	merge.importQuests()
	base = write(tmp_path / "en.json", {"q1 name": "Their name", "c1": "Their task"})
	Dialogs(monkeypatch, tmp_path / "quests.json", base, base)
	merge.onExportQuests()
	locale = read_json(base)
	assert locale["q1 name"] == "Their name" and locale["c1"] == "Their task"
	assert locale["q1 description"] == ""  # (added, blank)


@pytest.mark.parametrize("cancel_at", ["open", "save"])
def test_cancelling_a_locale_dialog_saves_no_locale(merge, monkeypatch, tmp_path, cancel_at):
	build_quest(merge)
	base = write(tmp_path / "en.json", {"a": "b"})
	answers = [None] if cancel_at == "open" else [base, None]
	Dialogs(monkeypatch, tmp_path / "quests.json", *answers)
	merge.onExportQuests()
	assert (tmp_path / "quests.json").exists()
	assert read_json(base) == {"a": "b"}
	assert merge.popups[1:] == [NOT_SAVED] and merge.errors == []


@pytest.mark.parametrize("content", ["{ not json", "[1, 2]"], ids=["bad-json", "not-a-dict"])
def test_a_locale_file_that_cannot_be_used_is_reported_and_nothing_is_saved(merge, monkeypatch, tmp_path, content):
	build_quest(merge)
	base = tmp_path / "en.json"
	base.write_text(content, encoding="utf-8")
	dialogs = Dialogs(monkeypatch, tmp_path / "quests.json", base)
	merge.onExportQuests()
	assert dialogs.titles == ["Export Quest JSON", "Open Locale JSON to merge into"]  # (no save dialog)
	assert len(merge.errors) == 1 and "en.json" in merge.errors[0][1]
	assert base.read_text(encoding="utf-8") == content
	assert len(merge.popups) == 1  # (just the quest file's)


# --- exporting without merging ---------------------------------------------------------------------


def test_without_merging_only_the_quests_entries_are_saved(no_merge, monkeypatch, tmp_path):
	quest_id, task_id = build_quest(no_merge, texts={"name": "Typed name"}, task_text="Typed task")
	out = tmp_path / "en.json"
	dialogs = Dialogs(monkeypatch, tmp_path / "quests.json", out)
	no_merge.onExportQuests()
	assert dialogs.asked == [("Export Quest JSON", {}), ("Export Locale JSON", {})]  # (no locale file is opened)
	expected = {f"{quest_id} {field}": "" for field in LOCALE_FIELDS}
	expected.update({f"{quest_id} name": "Typed name", task_id: "Typed task"})
	assert read_json(out) == expected
	assert no_merge.popups[1] == f"The locale export has completed successfully and can be found at {out}."


def test_without_merging_an_existing_file_is_replaced_not_merged_into(no_merge, monkeypatch, tmp_path):
	quest_id, _ = build_quest(no_merge)
	out = write(tmp_path / "en.json", {"something else": "gone afterwards"})
	Dialogs(monkeypatch, tmp_path / "quests.json", out)
	no_merge.onExportQuests()
	locale = read_json(out)
	assert "something else" not in locale and f"{quest_id} name" in locale


def test_without_merging_imported_quests_get_blank_entries(no_merge, monkeypatch, tmp_path):
	Dialogs(monkeypatch, imported_quest_file(tmp_path / "imported.json"))
	no_merge.importQuests()
	out = tmp_path / "en.json"
	Dialogs(monkeypatch, tmp_path / "quests.json", out)
	no_merge.onExportQuests()
	assert read_json(out) == {**{f"q1 {field}": "" for field in LOCALE_FIELDS}, "c1": ""}


def test_without_merging_cancelling_saves_no_locale(no_merge, monkeypatch, tmp_path):
	build_quest(no_merge)
	exports = tmp_path / "exports"
	exports.mkdir()
	Dialogs(monkeypatch, exports / "quests.json", None)
	no_merge.onExportQuests()
	assert no_merge.popups[1:] == [NOT_SAVED]
	assert list(exports.iterdir()) == [exports / "quests.json"]


def test_a_locale_that_cannot_be_written_is_reported(no_merge, monkeypatch, tmp_path):
	build_quest(no_merge)
	Dialogs(monkeypatch, tmp_path / "quests.json", tmp_path / "no_such_folder" / "en.json")
	no_merge.onExportQuests()
	assert len(no_merge.errors) == 1 and "could not be saved" in no_merge.errors[0][1]
	assert len(no_merge.popups) == 1  # (just the quest file's)


def test_a_task_without_an_id_is_reported_before_any_locale_dialog(win, monkeypatch, tmp_path):
	quest = win.spawnWindow("QuestBuilder")
	quest.open_task_window().finalize("WeaponAssembly")  # (a placeholder that has no id yet)
	quest.finalize()
	dialogs = Dialogs(monkeypatch, tmp_path / "quests.json")
	win.onExportQuests()
	assert dialogs.titles == ["Export Quest JSON"]
	assert len(win.errors) == 1 and len(win.popups) == 1


# --- the export messages ---------------------------------------------------------------------------


@pytest.fixture
def press_ok(qapp):
	"""Press OK on each message as it is shown. Records (title, text, whether it had an OK button)."""
	shown = []

	def answer():
		box = QApplication.activeModalWidget()
		if box is None:
			return
		is_message_box = isinstance(box, QMessageBox)
		ok = box.button(QMessageBox.StandardButton.Ok) if is_message_box else None
		shown.append((box.windowTitle(), box.text() if is_message_box else "", ok is not None))
		if ok is not None:
			ok.click()
		else:
			box.done(0)  # (a window without one is closed anyway, so it can't hang the test)

	timer = QTimer()
	timer.timeout.connect(answer)
	timer.start(10)
	yield shown
	timer.stop()


def test_the_quest_and_locale_export_messages_have_an_ok_button(main_window, press_ok, monkeypatch, tmp_path):
	set_merging(main_window, True)
	build_quest(main_window)
	quests_file = tmp_path / "quests.json"
	locale_file = write(tmp_path / "en.json", {})
	Dialogs(monkeypatch, quests_file, locale_file, locale_file)
	main_window.onExportQuests()
	assert press_ok == [
		("Export Quest JSON", f"The quest export has completed successfully and can be found at {quests_file}.", True),
		("Export Locale JSON", f"The locale export has completed successfully and can be found at {locale_file}.", True),
	]


# --- the setting -----------------------------------------------------------------------------------


def test_merging_is_on_in_the_shipped_settings():
	assert load_config().merge_locales_on_export is True


def test_a_settings_file_without_the_entry_merges(config):
	lines = config.settings_path.read_text(encoding="utf-8").splitlines()
	text = "\n".join(line for line in lines if not line.startswith("merge_locales_on_export"))
	assert len(text.splitlines()) == len(lines) - 1
	config.settings_path.write_text(text, encoding="utf-8")
	reloaded = load_config(config.settings_path, config.settings_path.with_name("box_fields.json"))
	assert reloaded.merge_locales_on_export is True


def test_the_settings_dialog_turns_merging_off_and_it_is_remembered(qapp, config):
	config.update_settings({**config.settings(), "merge_locales_on_export": "true"})
	dlg = Gui_SettingsDlg(config)
	box = dlg.checkbox("merge_locales_on_export")
	assert box.isChecked() and box.text() == "Merge locales on export"
	box.setChecked(False)
	dlg.save()
	assert config.merge_locales_on_export is False
	assert "merge_locales_on_export = false" in config.settings_path.read_text(encoding="utf-8")
	reloaded = load_config(config.settings_path, config.settings_path.with_name("box_fields.json"))
	assert reloaded.merge_locales_on_export is False
