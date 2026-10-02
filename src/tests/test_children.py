"""Finding every item under a parent item: the lookup, and the dialog that replaced the console prompt."""

import builtins
import json

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox

from modules.builders.items import ROOT_ITEM_ID, find_descendants, format_id_list
from modules.utils import read_json
from modules.windows import main_window as mw
from modules.windows.children_dialog import Gui_ChildrenDlg

# A small item tree:   root
#                       ├── weapon ── rifle ── ak
#                       │              └── svd
#                       └── mod ── magazine ── mag30
ITEMS = {
	ROOT_ITEM_ID: {"_parent": ""},
	"weapon": {"_parent": ROOT_ITEM_ID},
	"rifle": {"_parent": "weapon"},
	"ak": {"_parent": "rifle"},
	"svd": {"_parent": "rifle"},
	"mod": {"_parent": ROOT_ITEM_ID},
	"magazine": {"_parent": "mod"},
	"mag30": {"_parent": "magazine"},
}


# --- the lookup ---------------------------------------------------------------------------


def test_finds_everything_below_a_parent_at_any_depth():
	assert find_descendants(ITEMS, "weapon") == ["rifle", "ak", "svd"]


def test_the_direct_children_of_a_parent():
	assert find_descendants(ITEMS, "rifle") == ["ak", "svd"]


def test_results_follow_the_files_order():
	assert find_descendants(ITEMS, ROOT_ITEM_ID) == ["weapon", "rifle", "ak", "svd", "mod", "magazine", "mag30"]


def test_a_parent_with_nothing_below_it_gives_an_empty_list():
	assert find_descendants(ITEMS, "ak") == []


def test_an_unknown_parent_gives_an_empty_list():
	assert find_descendants(ITEMS, "no-such-id") == []


def test_the_parent_itself_is_not_in_the_results():
	assert "weapon" not in find_descendants(ITEMS, "weapon")


def test_an_item_whose_parent_is_missing_from_the_file_is_skipped_not_a_crash():
	items = {"orphan": {"_parent": "not-in-the-file"}, "ok": {"_parent": "top"}, "top": {"_parent": ""}}
	assert find_descendants(items, "top") == ["ok"]


def test_a_loop_in_the_data_does_not_hang():
	items = {"a": {"_parent": "b"}, "b": {"_parent": "a"}}
	assert find_descendants(items, "elsewhere") == []


def test_an_item_with_no_parent_entry_is_fine():
	assert find_descendants({"a": {}, "b": {"_parent": "a"}}, "a") == ["b"]


def test_matches_the_old_console_tool_on_the_real_items_file():
	from modules.paths import DATA_DIR

	items = read_json(DATA_DIR / "items.json")

	def old_tool(items, parent_id):  # the algorithm the console prompt used
		found_ids = []
		for item_id in items.keys():
			chain_top = False
			current_id = item_id
			while not chain_top:
				current_parent = items[current_id]["_parent"]
				if current_parent == parent_id:
					chain_top = True
					found_ids.append(item_id)
				if current_id == ROOT_ITEM_ID:
					chain_top = True
				current_id = current_parent
		return found_ids

	parents = sorted({item["_parent"] for item in items.values() if item.get("_parent")})
	for parent_id in parents[:: max(1, len(parents) // 25)] + [ROOT_ITEM_ID, "nope"]:
		assert find_descendants(items, parent_id) == old_tool(items, parent_id), parent_id


def test_the_text_format_is_what_the_console_printed():
	assert format_id_list(["a", "b"]) == '[\n"a",\n"b",\n]'
	assert format_id_list([]) == "[\n]"


# --- the dialog -------------------------------------------------------------------------------


class Holder:
	"""Stands in for the main window's items.json storage and loader."""

	def __init__(self, items=None, loads=None):
		self.items = items
		self.loads = loads
		self.load_calls = 0

	def get(self):
		return self.items

	def load(self):
		self.load_calls += 1
		if self.loads is not None:
			self.items = self.loads


@pytest.fixture
def make_dialog(qapp):
	def make(items=None, loads=None):
		holder = Holder(items, loads)
		return Gui_ChildrenDlg(holder.get, holder.load), holder

	return make


def test_without_an_items_file_it_says_so_and_cannot_search(make_dialog):
	dlg, _ = make_dialog()
	assert "No items.json" in dlg.ui.lbl_items_status.text()
	dlg.ui.fld_parent_id.setText("weapon")
	assert not dlg.ui.pb_find.isEnabled()


def test_with_items_it_shows_how_many(make_dialog):
	dlg, _ = make_dialog(ITEMS)
	assert f"{len(ITEMS)} items" in dlg.ui.lbl_items_status.text()


def test_find_needs_an_id_typed(make_dialog):
	dlg, _ = make_dialog(ITEMS)
	assert not dlg.ui.pb_find.isEnabled()
	dlg.ui.fld_parent_id.setText("   ")
	assert not dlg.ui.pb_find.isEnabled()
	dlg.ui.fld_parent_id.setText("weapon")
	assert dlg.ui.pb_find.isEnabled()


def test_the_load_button_loads_and_then_searching_works(make_dialog):
	dlg, holder = make_dialog(None, loads=ITEMS)
	dlg.ui.pb_load.click()
	assert holder.load_calls == 1
	assert f"{len(ITEMS)} items" in dlg.ui.lbl_items_status.text()
	dlg.ui.fld_parent_id.setText("weapon")
	assert dlg.ui.pb_find.isEnabled()


def test_cancelling_the_load_leaves_it_unloaded(make_dialog):
	dlg, holder = make_dialog(None, loads=None)
	dlg.ui.pb_load.click()
	assert holder.load_calls == 1 and "No items.json" in dlg.ui.lbl_items_status.text()


def test_finding_children_lists_them_and_counts_them(make_dialog):
	dlg, _ = make_dialog(ITEMS)
	dlg.ui.fld_parent_id.setText("weapon")
	dlg.ui.pb_find.click()
	assert dlg.ui.txt_results.toPlainText() == '[\n"rifle",\n"ak",\n"svd",\n]'
	assert dlg.ui.lbl_result.text() == "3 items found."


def test_pressing_enter_in_the_id_box_searches(make_dialog):
	dlg, _ = make_dialog(ITEMS)
	dlg.ui.fld_parent_id.setText("rifle")
	dlg.ui.fld_parent_id.returnPressed.emit()
	assert dlg.ui.txt_results.toPlainText() == '[\n"ak",\n"svd",\n]'


def test_the_id_is_trimmed(make_dialog):
	dlg, _ = make_dialog(ITEMS)
	dlg.ui.fld_parent_id.setText("  rifle  ")
	dlg.ui.pb_find.click()
	assert dlg.ui.lbl_result.text() == "2 items found."


def test_one_result_is_singular(make_dialog):
	dlg, _ = make_dialog(ITEMS)
	dlg.ui.fld_parent_id.setText("magazine")
	dlg.ui.pb_find.click()
	assert dlg.ui.lbl_result.text() == "1 item found."


def test_an_id_that_is_not_in_the_file_says_so(make_dialog):
	dlg, _ = make_dialog(ITEMS)
	dlg.ui.fld_parent_id.setText("typo")
	dlg.ui.pb_find.click()
	assert "0 items found" in dlg.ui.lbl_result.text() and "isn't in the loaded items.json" in dlg.ui.lbl_result.text()
	assert dlg.ui.txt_results.toPlainText() == "[\n]"


def test_a_known_id_with_no_children_does_not_blame_the_id(make_dialog):
	dlg, _ = make_dialog(ITEMS)
	dlg.ui.fld_parent_id.setText("ak")
	dlg.ui.pb_find.click()
	assert dlg.ui.lbl_result.text() == "0 items found."


def test_copy_puts_the_list_on_the_clipboard(make_dialog):
	dlg, _ = make_dialog(ITEMS)
	assert not dlg.ui.pb_copy.isEnabled()
	dlg.ui.fld_parent_id.setText("weapon")
	dlg.ui.pb_find.click()
	assert dlg.ui.pb_copy.isEnabled()
	dlg.ui.pb_copy.click()
	assert QApplication.clipboard().text() == '[\n"rifle",\n"ak",\n"svd",\n]'
	assert "Copied" in dlg.ui.lbl_result.text()


def test_the_results_box_is_read_only(make_dialog):
	dlg, _ = make_dialog(ITEMS)
	assert dlg.ui.txt_results.isReadOnly()


def test_close_closes_the_dialog(make_dialog):
	dlg, _ = make_dialog(ITEMS)
	dlg.show()
	dlg.ui.pb_close.click()
	assert not dlg.isVisible()


# --- from the main window -----------------------------------------------------------------------


@pytest.fixture
def no_console(monkeypatch):
	def refuse(*args, **kwargs):
		raise AssertionError("the old console prompt was used")

	monkeypatch.setattr(builtins, "input", refuse)


def test_the_menu_item_opens_a_dialog_not_a_console_prompt(main_window, no_console):
	main_window.ui.actionGet_all_children_of_parent_ID.trigger()
	(dlg,) = [w for w in main_window.windows if isinstance(w, Gui_ChildrenDlg)]
	assert dlg.isVisible() and dlg.parent() is main_window


def test_the_dialog_uses_the_items_loaded_in_the_main_window(main_window, no_console):
	main_window.apply_items(ITEMS, "x.json")
	dlg = main_window.getAllChildrenCalc()
	dlg.ui.fld_parent_id.setText("rifle")
	dlg.ui.pb_find.click()
	assert dlg.ui.lbl_result.text() == "2 items found."


def test_loading_from_inside_the_dialog_loads_into_the_main_window(main_window, monkeypatch, tmp_path, no_console):
	f = tmp_path / "items.json"
	f.write_text(json.dumps(ITEMS), encoding="utf-8")
	monkeypatch.setattr(mw, "safe_file_dialog", lambda method, title: (str(f), True))
	dlg = main_window.getAllChildrenCalc()
	dlg.ui.pb_load.click()
	assert main_window.state.items == ITEMS
	dlg.ui.fld_parent_id.setText("weapon")
	dlg.ui.pb_find.click()
	assert dlg.ui.lbl_result.text() == "3 items found."


def test_the_main_window_stays_usable_while_the_dialog_is_open(main_window, no_console):
	dlg = main_window.getAllChildrenCalc()
	assert dlg.isVisible() and not dlg.isModal()


def test_there_is_no_separate_load_items_menu_item_any_more(main_window):
	# (loading is done from inside the child-item finder)
	assert not hasattr(main_window.ui, "actionLoad_items_json_for_below")
	debug_menu_items = [a.text() for a in main_window.ui.menuDebug.actions() if not a.isSeparator()]
	assert all("items.json" not in text for text in debug_menu_items)
	assert any("children" in text for text in debug_menu_items)
