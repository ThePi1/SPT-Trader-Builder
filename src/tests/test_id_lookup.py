"""The ID Lookup tab: every column is searchable, and what the table shows."""

import pytest

from builders.lookup import COLUMNS, compile_search, filter_rows, lookup_rows

# --- the rows and the search (no windows needed) ---------------------------------------------------

CUSTOM = {"Cool Custom Gun": "aaaa00000000000000000001"}
QUESTS = {"bbbb00000000000000000002": {"QuestName": "Debut Of The Quest"}}
ITEMS = {
	"cccc00000000000000000003": {"_name": "weapon_ak74"},
	"dddd00000000000000000004": {"_name": "weapon_m4a1"},
}
LOCATIONS = {"Customs": "eeee00000000000000000005"}
TRADERS = {"Prapor": "ffff00000000000000000006"}

def rows():
	return lookup_rows(CUSTOM, QUESTS, ITEMS, LOCATIONS, TRADERS)


def test_the_columns_are_id_data_and_type():
	assert COLUMNS == ("id", "data", "type")


def test_every_source_becomes_rows_in_order():
	assert rows() == [
		("aaaa00000000000000000001", "Cool Custom Gun", "wtt_custom"),
		("bbbb00000000000000000002", "Debut Of The Quest", "new_quest"),
		("cccc00000000000000000003", "weapon_ak74", "eft_item"),
		("dddd00000000000000000004", "weapon_m4a1", "eft_item"),
		("eeee00000000000000000005", "Customs", "location"),
		("ffff00000000000000000006", "Prapor", "trader"),
	]


def test_an_item_without_a_name_still_gets_a_row():
	assert lookup_rows({}, {}, {"x" * 24: {"_parent": "p"}}, {}, {}) == [("x" * 24, "", "eft_item")]


def test_items_that_share_a_name_each_keep_their_own_id():
	shared = {"id1": {"_name": "same"}, "id2": {"_name": "same"}}
	found = [r[0] for r in lookup_rows({}, {}, shared, {}, {})]
	assert found == ["id1", "id2"]


@pytest.mark.parametrize(
	"term, expected_ids",
	[
		# the id column
		("aaaa0000", ["aaaa00000000000000000001"]),
		("dddd00000000000000000004", ["dddd00000000000000000004"]),
		("00000005$", ["eeee00000000000000000005"]),
		# the data column
		("Cool Custom", ["aaaa00000000000000000001"]),
		("ak74", ["cccc00000000000000000003"]),
		("^Prapor$", ["ffff00000000000000000006"]),
		# the type column
		("^wtt_custom$", ["aaaa00000000000000000001"]),
		("^new_quest$", ["bbbb00000000000000000002"]),
		("^location$", ["eeee00000000000000000005"]),
		("^trader$", ["ffff00000000000000000006"]),
		("^eft_item$", ["cccc00000000000000000003", "dddd00000000000000000004"]),
	],
)
def test_every_column_is_searchable(term, expected_ids):
	assert [r[0] for r in filter_rows(rows(), term)] == expected_ids


def test_a_search_matches_if_any_one_column_matches():
	# "Customs" is a location's name; "wtt_custom" is a type; both contain "custom"
	found = {r[0] for r in filter_rows(rows(), "custom")}
	assert found == {"aaaa00000000000000000001", "eeee00000000000000000005"}


def test_the_search_ignores_case():
	assert filter_rows(rows(), "PRAPOR") == filter_rows(rows(), "prapor") == filter_rows(rows(), "^Prapor$")


def test_the_search_is_a_regex():
	assert [r[1] for r in filter_rows(rows(), "weapon_(ak74|m4a1)")] == ["weapon_ak74", "weapon_m4a1"]


def test_an_empty_search_shows_everything():
	assert filter_rows(rows(), "") == rows()


def test_a_search_with_no_matches_shows_nothing():
	assert filter_rows(rows(), "zzzzzz") == []


@pytest.mark.parametrize("text", ["(", "[", "*", "a(b", "\\", "?"])
def test_text_that_is_not_a_valid_regex_is_searched_for_as_plain_text(text):
	assert filter_rows(rows(), text) == []  # nothing contains it, and it must not raise or match everything
	extra = rows() + [("id", f"has {text} in it", "eft_item")]
	assert filter_rows(extra, text) == [("id", f"has {text} in it", "eft_item")]


def test_compile_search_is_case_insensitive():
	assert compile_search("abc").search("xABCx")


# --- the table in the window -----------------------------------------------------------------------------


@pytest.fixture
def lookup(main_window):
	"""Type into the search box and read back the table as (id, data, type) tuples."""

	def search(text):
		main_window.ui.fld_idlookup.setText(text)
		main_window.update_idlookup()  # (typing does this itself; setting the same text again doesn't)
		table = main_window.ui.id_table
		return [
			(table.item(r, 0).text(), table.item(r, 1).text(), table.item(r, 2).text())
			for r in range(table.rowCount())
		]

	return search


def test_the_table_has_the_three_columns(main_window):
	table = main_window.ui.id_table
	assert [table.horizontalHeaderItem(i).text() for i in range(3)] == ["id", "data", "type"]


def test_searching_by_a_name_finds_it(lookup, main_window):
	trader_id = main_window.state.traders["Prapor"]
	assert (trader_id, "Prapor", "trader") in lookup("^Prapor$")


def test_searching_by_an_id_finds_it(lookup, main_window):
	trader_id = main_window.state.traders["Prapor"]
	assert lookup(trader_id) == [(trader_id, "Prapor", "trader")]


def test_searching_by_part_of_an_id_finds_it(lookup, main_window):
	trader_id = main_window.state.traders["Prapor"]
	found = lookup(trader_id[:12])
	assert (trader_id, "Prapor", "trader") in found
	assert all(trader_id[:12] in row[0] or trader_id[:12] in row[1] for row in found)


def test_searching_by_a_type_finds_all_of_that_type(lookup, main_window):
	found = lookup("^trader$")
	assert len(found) == len(main_window.state.traders)
	assert {row[2] for row in found} == {"trader"}
	found = lookup("^location$")
	assert len(found) == len(main_window.state.locations)


def test_searching_by_the_bundled_item_type(lookup, main_window):
	assert len(lookup("^eft_item$")) == len(main_window.state.items)


def test_a_quest_made_this_session_is_searchable_by_all_three_columns(lookup, main_window):
	main_window.state.quests["abcdef0123456789abcdef01"] = {"QuestName": "My Test Quest"}
	expected = ("abcdef0123456789abcdef01", "My Test Quest", "new_quest")
	assert lookup("abcdef0123456789abcdef01") == [expected]  # by id
	assert lookup("My Test Quest") == [expected]  # by data
	assert expected in lookup("^new_quest$")  # by type
	assert lookup("^new_quest$") == [expected]


def test_imported_wtt_data_is_searchable_by_all_three_columns(lookup, main_window):
	main_window.state.id_search["Shiny Custom Rifle"] = "0123456789abcdef01234567"
	expected = ("0123456789abcdef01234567", "Shiny Custom Rifle", "wtt_custom")
	assert lookup("0123456789abcdef01234567") == [expected]
	assert lookup("Shiny Custom") == [expected]
	assert lookup("^wtt_custom$") == [expected]


def test_the_loaded_items_file_is_what_the_lookup_searches(lookup, main_window):
	main_window.apply_items({"0123456789abcdef0123abcd": {"_name": "modded_blaster", "_parent": ""}}, "x.json")
	expected = ("0123456789abcdef0123abcd", "modded_blaster", "eft_item")
	assert lookup("0123456789abcdef0123abcd") == [expected]  # by id
	assert lookup("modded_blaster") == [expected]  # by data
	assert lookup("^eft_item$") == [expected]  # by type
	assert lookup("weapon_ak74") == []  # (the file it replaced is no longer in use)


def test_items_that_share_a_name_are_each_listed_with_their_own_id(lookup, main_window):
	names = {}
	for item_id, item in main_window.state.items.items():
		names.setdefault(item["_name"], []).append(item_id)
	shared = next((n, ids) for n, ids in names.items() if len(ids) > 1)
	found = [row for row in lookup(f"^{shared[0]}$") if row[2] == "eft_item"]
	assert sorted(row[0] for row in found) == sorted(shared[1])


def test_the_cells_hold_the_right_things_in_the_right_columns(lookup, main_window):
	table = main_window.ui.id_table
	lookup("^Prapor$")
	assert table.item(0, 0).text() == main_window.state.traders["Prapor"]
	assert table.item(0, 1).text() == "Prapor" and table.item(0, 1).toolTip() == "Prapor"
	assert table.item(0, 2).text() == "trader"


def test_an_empty_search_lists_everything_and_the_table_repaints(lookup, main_window):
	everything = lookup("")
	state = main_window.state
	assert len(everything) == len(state.items) + len(state.locations) + len(state.traders)
	assert main_window.ui.id_table.updatesEnabled()


def test_clearing_the_search_brings_everything_back(lookup, main_window):
	everything = lookup("")
	assert len(lookup("zzzzzz")) == 0
	assert lookup("") == everything


def test_a_half_typed_pattern_does_not_hide_or_break_the_table(lookup, main_window):
	assert lookup("(((") == []  # (nothing contains it) rather than every row


def test_a_new_search_replaces_the_old_rows(lookup, main_window):
	lookup("^Prapor$")
	assert main_window.ui.id_table.rowCount() == 1
	lookup("^Therapist$")
	assert main_window.ui.id_table.rowCount() == 1
	assert main_window.ui.id_table.item(0, 1).text() == "Therapist"
