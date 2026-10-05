"""Reference files: files that are only looked at (other mods' quests, items, traders), for names, checks and Find IDs."""

import json
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from core import lookup
from core import references as R
from core.gamedata import GameData
from core.paths import BUNDLED_DATABASE_DIR
from schema import assort as A
from schema import choices, registry, validate
from schema.quest import make_quest

QUEST_ID, ITEM_ID, TRADER_ID, OFFER_ID, PART_ID = "1" * 24, "2" * 24, "3" * 24, "4" * 24, "5" * 24
ASSORT_ITEM = "6" * 24


def write(path, data):
	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_text(json.dumps(data), encoding="utf-8")
	return path


def mod_files(folder):
	"""A small mod: quests, a locale (two languages), a trader assort, item templates and a trader base file."""
	return {
		"quests": write(folder / "quests.json", {QUEST_ID: {"_id": QUEST_ID, "QuestName": "Mod quest", "conditions": {}, "rewards": {}}}),
		"en": write(folder / "locale" / "en.json", {f"{ITEM_ID} Name": "Mod rifle", f"{TRADER_ID} Nickname": "Mod trader", f"{QUEST_ID} name": "Mod quest (en)"}),
		"ru": write(folder / "locale" / "ru.json", {f"{ITEM_ID} Name": "Модная винтовка"}),
		"assort": write(folder / "assort.json", {
			"items": [{"_id": OFFER_ID, "_tpl": ASSORT_ITEM, "parentId": "hideout", "slotId": "hideout", "upd": {}}],
			"barter_scheme": {OFFER_ID: [[{"count": 1, "_tpl": A.MONEY["roubles"]}]]}, "loyal_level_items": {OFFER_ID: 1},
		}),
		"items": write(folder / "items.json", {ITEM_ID: {"_id": ITEM_ID, "_name": "mod_rifle", "_parent": "9" * 24, "_type": "Item", "_props": {}}}),
		"trader": write(folder / "base.json", {"_id": TRADER_ID, "name": "Mod", "nickname": "Modder", "currency": "RUB", "loyaltyLevels": []}),
		"questassort": write(folder / "questassort.json", {"started": {}, "success": {OFFER_ID: QUEST_ID}, "fail": {}}),
		"junk": write(folder / "notes.json", [1, 2, 3]),
	}


def test_each_kind_of_file_is_recognised(tmp_path):
	files = mod_files(tmp_path)
	kinds = {name: R.detect_kind(json.loads(path.read_text(encoding="utf-8"))) for name, path in files.items()}
	assert kinds == {
		"quests": R.QUESTS, "en": R.LOCALE, "ru": R.LOCALE, "assort": R.ASSORT, "items": R.ITEMS, "trader": R.TRADER,
		"questassort": "questassort", "junk": None,
	}


def test_adding_files_and_folders_keeps_the_useful_ones_and_says_why_not_for_the_rest(tmp_path):
	files = mod_files(tmp_path / "mod")
	refs = R.References(tmp_path / "list.json")
	added, skipped = refs.add([tmp_path / "mod"])
	assert sorted(ref.kind for ref in added) == sorted([R.QUESTS, R.LOCALE, R.LOCALE, R.ASSORT, R.ITEMS, R.TRADER])
	reasons = dict(skipped)
	assert "no ids of its own" in reasons["questassort.json"] and "Not a quest" in reasons["notes.json"]
	again, skipped_again = refs.add([files["quests"]])
	assert not again and skipped_again == [("quests.json", "Already added.")]
	assert refs.add([tmp_path / "gone.json"])[1][0][1].startswith("Couldn't be read")


def test_the_list_is_remembered_and_a_missing_file_does_not_break_anything(tmp_path):
	files = mod_files(tmp_path / "mod")
	refs = R.References(tmp_path / "list.json")
	refs.add([files["quests"], files["items"]])
	again = R.References(tmp_path / "list.json")
	assert [ref.name for ref in again.files] == ["quests.json", "items.json"] and not again.files[0].read  # (read when needed)
	files["items"].unlink()
	assert again.quest_name(QUEST_ID) == "Mod quest" and again.item_name(ITEM_ID) == ""
	assert again.files[1].error.startswith("Couldn't be read") and again.files[1].kind is None
	refs.remove(refs.files[:1])
	assert [ref.name for ref in R.References(tmp_path / "list.json").files] == ["items.json"]


def test_names_and_what_is_known_come_from_the_files(tmp_path):
	files = mod_files(tmp_path / "mod")
	refs = R.References(tmp_path / "list.json")
	refs.add(list(files.values()))
	assert refs.knows_quest(QUEST_ID) and refs.quest_name(QUEST_ID) == "Mod quest (en)"  # (the locale's name wins)
	assert refs.item_name(ITEM_ID) == "Mod rifle"  # (English: en.json comes before ru.json)
	assert refs.knows_item(ITEM_ID) and refs.knows_item(ASSORT_ITEM) and not refs.knows_item("7" * 24)
	assert refs.item_name(ASSORT_ITEM) == ""  # (only its id is known)
	assert refs.knows_trader(TRADER_ID) and refs.trader_name(TRADER_ID) == "Mod trader"
	assert refs.offer_rows() == [(OFFER_ID, "", "assort.json")]
	refs.set_language("ru")
	assert refs.item_name(ITEM_ID) == "Модная винтовка"  # (the file for the chosen language first)


def reference_data(tmp_path):
	files = mod_files(tmp_path / "mod")
	data = GameData(None, "en", BUNDLED_DATABASE_DIR)
	data.references = R.References(tmp_path / "list.json")
	data.references.add(list(files.values()))
	return data


def test_game_data_asks_the_references_last(tmp_path):
	data = reference_data(tmp_path)
	assert data.knows_item(ITEM_ID) and data.item_name(ITEM_ID) == "Mod rifle" and data.knows_quest(QUEST_ID)
	assert data.quest_name(QUEST_ID) == "Mod quest (en)" and data.trader_name(TRADER_ID) == "Mod trader"
	debut = "5936d90786f7742b1420ba5b"
	assert data.knows_quest(debut) and data.quest_name(debut) == "Debut"  # (the game's names are not overridden)
	assert TRADER_ID in data.all_traders() and TRADER_ID not in data.traders
	assert (TRADER_ID, "Mod trader") in choices.get("traders", data)
	assert not GameData(None, "en", BUNDLED_DATABASE_DIR).knows_item(ITEM_ID)


def test_unknown_item_and_trader_warnings_go_away_when_a_reference_knows_them(tmp_path):
	data = reference_data(tmp_path)
	plain = GameData(None, "en", BUNDLED_DATABASE_DIR)
	quest = make_quest(name="Q")
	quest["traderId"] = "54cb50c76803fa8b248b4571"
	task = registry.new_item("task", "HandoverItem")
	task["target"] = [ITEM_ID]
	quest["conditions"]["AvailableForFinish"].append(task)
	messages = lambda game: [i.message for i in validate.validate_quests({quest["_id"]: quest}, None, game)]
	assert any("isn't in the game's item list" in m for m in messages(plain))
	assert not any("isn't in the game's item list" in m for m in messages(data))
	reward = registry.new_item("reward", "TraderUnlock")
	reward["target"] = TRADER_ID
	quest["rewards"]["Success"].append(reward)
	assert any(f"Trader {TRADER_ID}" in m for m in messages(plain)) and not any(f"Trader {TRADER_ID}" in m for m in messages(data))


def test_find_ids_lists_what_the_references_know_and_not_what_the_game_or_the_open_file_has(tmp_path):
	data = reference_data(tmp_path)
	rows = lookup.build_rows(data, quests={QUEST_ID: {"QuestName": "Open"}}, references=data.references)
	by_kind = {}
	for row in rows:
		by_kind.setdefault(row.kind, []).append(row)
	assert lookup.KIND_LABEL[lookup.REF_ITEM] == "Item (reference)" and lookup.KIND_LABEL[lookup.REF_OFFER] == "Trader offer (reference)"
	assert not by_kind.get(lookup.REF_QUEST)  # (that quest is open: it is listed once, as yours)
	assert {r.id for r in by_kind[lookup.REF_ITEM]} == {ITEM_ID, ASSORT_ITEM}
	assert [(r.id, r.name, r.detail) for r in by_kind[lookup.REF_TRADER]] == [(TRADER_ID, "Mod trader", "base.json")]
	assert [(r.id, r.detail) for r in by_kind[lookup.REF_OFFER]] == [(OFFER_ID, "assort.json")]
	assert [r.id for r in lookup.search(rows, "mod rifle", kinds=(lookup.REF_ITEM,))] == [ITEM_ID]
	closed = lookup.build_rows(data, kinds=(lookup.REF_QUEST,), references=data.references)
	assert [(r.id, r.name, r.detail) for r in closed] == [(QUEST_ID, "Mod quest (en)", "quests.json")]


# --- the window ------------------------------------------------------------------------------

@pytest.fixture
def window(tmp_path, monkeypatch):
	pytest.importorskip("PySide6")
	from PySide6.QtWidgets import QApplication

	from core.settings import Settings
	from ui import updates
	from ui.main_window import MainWindow

	QApplication.instance() or QApplication([])
	monkeypatch.setattr("core.references.REFERENCES_FILE", tmp_path / "references.json")
	monkeypatch.setattr(updates, "fetch_remote_version", lambda config: None)
	win = MainWindow(Settings.load(tmp_path / "none.ini"), GameData(None, "en", BUNDLED_DATABASE_DIR))
	yield win
	win.close()


def test_the_window_has_a_references_part_and_menu(window, tmp_path):
	files = mod_files(tmp_path / "mod")
	segment = window.files_strip.segment("references")
	assert "References" in segment.titleLabel.text() and "none" in segment.fileLabel.text()
	assert [a.text().replace("&", "") for a in window.menuReferences.actions()] == ["Add reference files...", "Manage reference files...", "Reload reference files"]
	assert [a.text().replace("&", "") for a in segment.menu.actions()] == ["Add reference files...", "Manage reference files...", "Reload reference files"]
	added = window.add_references([str(files["quests"]), str(files["items"]), str(files["trader"])])
	assert len(added) == 3 and "3 files" in segment.fileLabel.text() and "quests.json" in segment.toolTip()
	assert json.loads((tmp_path / "references.json").read_text(encoding="utf-8"))["files"][0].endswith("quests.json")
	assert {QUEST_ID, ITEM_ID, TRADER_ID} <= {r.id for r in window.rows()}  # (Find IDs)
	assert QUEST_ID in {r.id for r in window.rows(("quest", "ref_quest")) if r.kind == "ref_quest"}
	assert ITEM_ID in {r.id for r in window.rows(("item", "ref_item")) if r.kind == "ref_item"}
	assert window.gamedata.item_name(ITEM_ID) == "mod_rifle"
	window.references.remove(window.references.files[:])  # (nothing left over for the real data folder)


def test_the_find_windows_search_the_references_too(window, tmp_path, monkeypatch):
	window.add_references([str(mod_files(tmp_path / "mod")["quests"])])
	seen = []

	class FakeDialog:
		def __init__(self, rows, kinds, title, multi, settings, parent):
			seen.append((sorted({r.kind for r in rows}), kinds, title))
			self.ids = []

		def exec(self):
			return False

	monkeypatch.setattr("ui.main_window.PickerDialog", FakeDialog)
	window.pick("quest")
	window.pick("item")
	window.pick("part")
	assert seen[0][1:] == (("quest", "ref_quest"), "Find a quest") and "ref_quest" in seen[0][0]
	assert seen[1][1] == ("item", "ref_item") and seen[2][1] == ("item", "ref_item", "my_composite", "composite")


def test_the_import_window_can_keep_files_as_references_without_merging(window, tmp_path, monkeypatch):
	from ui.import_dialog import ImportDialog

	files = mod_files(tmp_path / "mod")
	monkeypatch.setattr(ImportDialog, "exec", lambda self: self.referenceButton.click() or True)
	before = dict(window.quests.data)
	window.import_files([str(files["quests"]), str(files["items"])])  # (an item template file can't be merged, but can be a reference)
	assert window.quests.data == before and not window.quests.dirty
	assert sorted(ref.name for ref in window.references.files) == ["items.json", "quests.json"]
	window.references.remove(window.references.files[:])


def test_the_manage_window_adds_removes_reloads_and_hands_files_to_import(window, tmp_path, monkeypatch):
	from ui.references_dialog import ReferencesDialog

	files = mod_files(tmp_path / "mod")
	monkeypatch.setattr("ui.references_dialog.QMessageBox.information", lambda *a, **k: None)
	dialog = ReferencesDialog(window.references)
	changes, imports = [], []
	dialog.changed.connect(lambda: changes.append(1))
	dialog.import_requested.connect(imports.append)
	dialog.add([str(files["quests"]), str(files["items"]), str(files["junk"])])
	assert dialog.table.rowCount() == 2 and changes == [1]
	assert [dialog.table.item(r, 1).text() for r in range(2)] == ["Quests", "Item templates"]
	assert not dialog.removeButton.isEnabled() and not dialog.importButton.isEnabled()
	dialog.table.selectRow(1)
	assert dialog.removeButton.isEnabled() and not dialog.importButton.isEnabled()  # (item templates can't be merged)
	dialog.table.selectRow(0)
	assert dialog.importButton.isEnabled()
	dialog.import_selected()
	assert imports == [[str(files["quests"])]]
	files["quests"].unlink()
	dialog.reload()
	assert dialog.table.item(0, 1).text() == "Can't use" and changes[-1] == 1
	dialog.table.selectRow(0)
	dialog.remove_selected()
	assert dialog.table.rowCount() == 1
	window.references.remove(window.references.files[:])
