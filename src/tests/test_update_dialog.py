"""The Update and About windows fill their text from version strings, including ones read from the internet."""

import html

import pytest

from windows.about import Gui_AboutDlg
from windows.common import fill_placeholders
from windows.update_dialog import Gui_UpdatesDlg


@pytest.fixture(autouse=True)
def _gui(qapp):
	"""The dialogs are widgets, so a QApplication has to exist."""


def update_text(*args):
	dlg = Gui_UpdatesDlg()
	dlg.updateVersion(*args)
	return dlg.ui.label.text()


def about_text(*args):
	dlg = Gui_AboutDlg()
	dlg.updateAbout(*args)
	return dlg.ui.label.text()


# --- the template filler ------------------------------------------------------------------------


def test_placeholders_are_replaced():
	assert fill_placeholders("a V b U", {"V": "1", "U": "2"}) == "a 1 b 2"


def test_a_backslash_in_a_value_is_just_a_backslash():
	assert fill_placeholders("version V", {"V": r"1.0\x\1"}) == r"version 1.0\x\1"


def test_a_value_is_never_substituted_again():
	assert fill_placeholders("A and B", {"A": "B", "B": "ok"}) == "B and ok"


def test_values_are_html_escaped():
	assert fill_placeholders("<p>V</p>", {"V": "<b>bold</b> & more"}) == "<p>&lt;b&gt;bold&lt;/b&gt; &amp; more</p>"


def test_quotes_are_escaped_so_a_value_cannot_break_out_of_an_attribute():
	assert fill_placeholders('<a href="U">', {"U": 'x" onclick="evil'}) == '<a href="x&quot; onclick=&quot;evil">'


def test_non_text_values_are_converted():
	assert fill_placeholders("V", {"V": 42}) == "42"


# --- the Update window ----------------------------------------------------------------------------


def test_the_update_window_shows_the_versions_and_status():
	text = update_text("0.1.0", "0.2.0", "https://example.com/p", "Program may be out of date!")
	assert "Current version: 0.1.0" in text and "Latest version: 0.2.0" in text
	assert "Program may be out of date!" in text
	assert 'href="https://example.com/p"' in text
	for placeholder in ("V_CUR", "V_LAT", "UPDATE_TEXT", "SRC_URL"):
		assert placeholder not in text


@pytest.mark.parametrize("latest", [r"v\x1", r"1.0\g<0>", r"\1", "C:\\path\\to", "trailing\\"])
def test_a_backslash_in_the_latest_version_no_longer_crashes(latest):
	# (this used to raise "re.error: bad escape" because the text was used as a regex replacement)
	text = update_text("0.1.0", latest, "https://example.com", "Up to date.")
	assert f"Latest version: {html.escape(latest)}" in text


def test_markup_in_the_latest_version_is_shown_as_text_not_rendered():
	text = update_text("0.1.0", "<h1>pwned</h1>", "https://example.com", "Up to date.")
	assert "<h1>" not in text and "&lt;h1&gt;pwned&lt;/h1&gt;" in text


def test_the_unknown_version_text_still_works():
	assert "Latest version: unknown" in update_text("0.1.0", "unknown", "https://example.com", "Could not check for updates.")


def test_the_current_version_is_escaped_too():
	assert "&lt;b&gt;" in update_text("<b>", "2", "https://example.com", "x")


# --- the About window --------------------------------------------------------------------------------


def test_the_about_window_shows_the_version_and_link():
	text = about_text("0.1.0", "https://example.com/project")
	assert "0.1.0" in text and 'href="https://example.com/project"' in text
	assert "V_CUR" not in text and "SRC_URL" not in text


def test_the_about_window_handles_a_backslash_and_markup():
	text = about_text(r"1\x", "<i>x</i>")
	assert r"1\x" in text and "<i>" not in text
