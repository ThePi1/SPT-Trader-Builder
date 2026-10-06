"""The "Enable debug options" setting and the Debug menu: regenerate a trader assort or a quest assort from what is known."""

import json
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication, QMessageBox

from core.documents import Document
from core.gamedata import GameData
from core.paths import BUNDLED_DATABASE_DIR
from core.settings import BY_KEY, Settings
from schema import assort as A
from ui import dialogs, updates
from ui.main_window import MainWindow

GUN, MAG, STRAY = "1" * 24, "2" * 24, "3" * 24
DEBUT = "5936d90786f7742b1420ba5b"  # a base-game quest
MINE, UNKNOWN = "a" * 24, "9" * 24


@pytest.fixture(scope="module")
def app():
	return QApplication.instance() or QApplication([])


def untidy_assort():
	"""Two offers, plus what an offer doesn't own: a loose item, a price and a level of nothing, a key nobody uses."""
	assort = A.empty_assort()
	for parts in (
		[
			{"_id": "p" + "0" * 23, "_tpl": GUN, "parentId": "hideout", "slotId": "hideout", "upd": {"StackObjectsCount": 3}},
			{"_id": "p1" + "0" * 22, "_tpl": MAG, "parentId": "p" + "0" * 23, "slotId": "mod_magazine"},
		],
		[{"_id": "q" + "0" * 23, "_tpl": MAG, "parentId": "hideout", "slotId": "hideout"}],
	):
		items, barter, level = A.new_offer_from_parts(parts, price=5, level=2)
		A.add_offer(assort, items, barter, level)
	first, second = A.offer_ids(assort)
	del assort["barter_scheme"][second]  # (the second offer has no price: none is made up)
	assort["items"].append({"_id": "l" * 24, "_tpl": STRAY, "parentId": "z" * 24, "slotId": "mod_x"})
	assort["barter_scheme"]["b" * 24] = [[{"count": 1, "_tpl": A.MONEY["roubles"]}]]
	assort["loyal_level_items"]["c" * 24] = 1
	assort["nextResupply"] = 12345
	assort["somethingElse"] = True
	return assort, first, second


def test_the_regenerated_assort_has_only_the_offers_and_what_they_own():
	assort, first, second = untidy_assort()
	new, left_out = A.regenerate_assort(assort)
	assert A.offer_ids(new) == [first, second] and [p["_tpl"] for p in new["items"]] == [GUN, MAG, MAG]
	assert list(new["barter_scheme"]) == [first] and list(new["loyal_level_items"]) == [first, second]  # (no price for the second: none is invented)
	assert new["nextResupply"] == 12345 and "somethingElse" not in new
	assert new["items"][0]["upd"] == assort["items"][0]["upd"] and new["items"][0] is not assort["items"][0]  # (copies)
	assert left_out == [
		"1 item that is not part of an offer", "1 price of something that is not an offer",
		"1 level of something that is not an offer", "the keys somethingElse",
	]
	again, nothing = A.regenerate_assort(new)
	assert nothing == [] and A.offer_ids(again) == [first, second]  # (regenerating a regenerated file leaves nothing out)


def test_the_regenerated_quest_assort_keeps_only_known_links():
	locks = {
		"started": {"o1": MINE}, "success": {"o1": DEBUT, "o2": MINE, "gone": MINE, "o3": UNKNOWN}, "fail": {"o2": MINE}, "weird": {"o1": MINE},
	}
	new, dropped = A.regenerate_questassort(locks, {"o1", "o2", "o3"}, lambda quest: quest in (MINE, DEBUT))
	assert new == {"started": {"o1": MINE}, "success": {"o1": DEBUT, "o2": MINE}, "fail": {"o2": MINE}}
	assert sorted(dropped) == sorted([
		("success", "gone", MINE, "no such offer in the trader assort"), ("success", "o3", UNKNOWN, "the quest is not known"),
		("weird", "", "", "not a section SPT uses"),
	])
	assert A.regenerate_questassort(None, {"o1"}, lambda q: True)[0] == A.empty_questassort()


# --- the setting and the menu --------------------------------------------------------------------------

def make_window(tmp_path, monkeypatch, enabled):
	monkeypatch.setattr("core.references.REFERENCES_FILE", tmp_path / "references.json")
	monkeypatch.setattr(updates, "fetch_remote_version", lambda config: None)
	monkeypatch.setattr("ui.main_window.QMessageBox.question", lambda *a, **k: QMessageBox.StandardButton.Discard)
	settings = Settings()
	settings.enable_debug_options = enabled
	return MainWindow(settings, GameData(None, "en", BUNDLED_DATABASE_DIR))


def test_the_setting_is_off_by_default_and_in_the_settings_window(app):
	assert BY_KEY["enable_debug_options"].default is False and Settings().enable_debug_options is False
	dialog = dialogs.SettingsDialog(Settings(), None)
	assert "enable_debug_options" in dialog.controls and dialogs._LABELS["enable_debug_options"] == "Enable debug options"


def test_the_debug_menu_is_next_to_help_and_only_shows_when_the_setting_is_on(app, tmp_path, monkeypatch):
	window = make_window(tmp_path, monkeypatch, enabled=False)
	names = [a.text().replace("&", "") for a in window.menubar.actions()]
	assert names == ["File", "Edit", "Settings", "Help", "Debug"] and not window.menuDebug.menuAction().isVisible()
	assert [a.text() for a in window.menuDebug.actions()] == ["Regenerate trader assort using known data...", "Regenerate quest assort using known data..."]
	window.settings.enable_debug_options = True
	window.apply_debug_option()
	assert window.menuDebug.menuAction().isVisible()
	window.settings.enable_debug_options = False
	window.apply_debug_option()
	assert not window.menuDebug.menuAction().isVisible()
	window.close()
	other = make_window(tmp_path, monkeypatch, enabled=True)
	assert other.menuDebug.menuAction().isVisible()
	other.close()


# --- the two tools ------------------------------------------------------------------------------------------

def test_regenerating_the_trader_assort_saves_a_new_file_and_changes_nothing_open(app, tmp_path, monkeypatch):
	window = make_window(tmp_path, monkeypatch, enabled=True)
	assort, first, second = untidy_assort()
	window._set_other("assort", Document(json.loads(json.dumps(assort))))
	target = tmp_path / "regenerated.json"
	asked = []
	monkeypatch.setattr("ui.main_window.QFileDialog.getSaveFileName", lambda parent, title, start, *a: asked.append((title, start)) or (str(target), ""))
	window.actionRegenerateAssort.trigger()
	assert asked[0][0] == "Save the regenerated trader assort" and asked[0][1].endswith("assort.json")
	saved = json.loads(target.read_text(encoding="utf-8"))
	assert A.offer_ids(saved) == [first, second] and "somethingElse" not in saved and "l" * 24 not in {p["_id"] for p in saved["items"]}
	assert window.assort.data == assort and not window.assort.dirty  # (the open assort is as it was)
	message = window.statusBar().currentMessage()
	assert "Saved 2 offers to regenerated.json" in message and "Left out" in message
	window.close()


def test_regenerating_the_quest_assort_removes_the_links_it_does_not_know(app, tmp_path, monkeypatch):
	window = make_window(tmp_path, monkeypatch, enabled=True)
	assort, first, second = untidy_assort()
	window._set_other("assort", Document(assort))
	window._set_quests(Document({MINE: {"_id": MINE, "QuestName": "Mine", "conditions": {}, "rewards": {}}}))
	locks = {"started": {}, "success": {first: MINE, second: DEBUT, "gone": MINE}, "fail": {first: UNKNOWN}}
	window._set_other("locks", Document(json.loads(json.dumps(locks))))
	target = tmp_path / "questassort_new.json"
	monkeypatch.setattr("ui.main_window.QFileDialog.getSaveFileName", lambda *a, **k: (str(target), ""))
	window.actionRegenerateLocks.trigger()
	assert json.loads(target.read_text(encoding="utf-8")) == {"started": {}, "success": {first: MINE, second: DEBUT}, "fail": {}}
	assert window.locks.data == locks and not window.locks.dirty
	message = window.statusBar().currentMessage()
	assert "Saved 2 links to questassort_new.json" in message and "no such offer in the trader assort" in message and "the quest is not known" in message
	window.close()


def test_with_no_trader_assort_open_nothing_is_asked_or_saved(app, tmp_path, monkeypatch):
	window = make_window(tmp_path, monkeypatch, enabled=True)
	told = []
	monkeypatch.setattr("ui.main_window.QMessageBox.information", lambda parent, title, text, *a: told.append(title))
	monkeypatch.setattr("ui.main_window.QFileDialog.getSaveFileName", lambda *a, **k: pytest.fail("no file should be asked for"))
	window.actionRegenerateAssort.trigger()
	window.actionRegenerateLocks.trigger()
	assert told == ["Regenerate trader assort", "Regenerate quest assort"]
	window.close()


def test_cancelling_the_save_dialog_saves_nothing(app, tmp_path, monkeypatch):
	window = make_window(tmp_path, monkeypatch, enabled=True)
	window._set_other("assort", Document(untidy_assort()[0]))
	monkeypatch.setattr("ui.main_window.QFileDialog.getSaveFileName", lambda *a, **k: ("", ""))
	assert window.debug_regenerate_assort() is None and window.debug_regenerate_locks() is None
	assert list(tmp_path.glob("*.json")) == []
	window.close()
