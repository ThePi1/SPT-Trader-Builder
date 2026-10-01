"""The assort export asks where to save, instead of writing to a fixed folder."""

import json

import pytest
from PySide6.QtWidgets import QFileDialog, QMessageBox

import paths
from windows import assort


@pytest.fixture
def form(main_window):
	dlg = main_window.spawnWindow("AssortBuilder")
	for item_id, qty, cost in (("5449016a4bdc2d6f028b456f", "5", "500"), ("590c661e86f7741e566b646a", "2", "75")):
		dlg.ui.ab_Item_Id.setText(item_id)
		dlg.ui.ab_quantity.setText(qty)
		dlg.ui.ab_cost_edit.setText(cost)
		dlg.add_item()
	return dlg


@pytest.fixture
def popups(monkeypatch):
	"""Record the message boxes instead of showing them."""
	shown = []
	monkeypatch.setattr(
		QMessageBox, "information", staticmethod(lambda parent, title, text: shown.append(("info", title, text)))
	)
	monkeypatch.setattr(
		QMessageBox, "critical", staticmethod(lambda parent, title, text: shown.append(("error", title, text)))
	)
	return shown


def _choose(monkeypatch, path):
	"""Make the save dialog return `path` (None = the user cancelled). Returns the calls made."""
	calls = []

	def fake(method, title):
		calls.append((method, title))
		return (str(path), True) if path is not None else (None, False)

	monkeypatch.setattr(assort, "safe_file_dialog", fake)
	return calls


def test_the_exported_file_goes_where_the_user_chose(form, popups, monkeypatch, tmp_path):
	target = tmp_path / "my folder" / "my_assort.json"
	target.parent.mkdir()
	_choose(monkeypatch, target)
	form.onExportAssort()
	saved = json.loads(target.read_text(encoding="utf-8"))
	assert saved == {
		"items": form.itemlist,
		"barter_scheme": form.barterlist,
		"loyal_level_items": form.loyaltylist,
	}
	assert len(saved["items"]) == 2 and len(saved["barter_scheme"]) == 2


def test_it_asks_with_a_save_dialog(form, popups, monkeypatch, tmp_path):
	calls = _choose(monkeypatch, tmp_path / "a.json")
	form.onExportAssort()
	assert calls == [(QFileDialog.getSaveFileName, "Export Assort JSON")]


def test_a_confirmation_names_the_file(form, popups, monkeypatch, tmp_path):
	target = tmp_path / "a.json"
	_choose(monkeypatch, target)
	form.onExportAssort()
	(kind, title, text) = popups[0]
	assert (kind, title) == ("info", "Export Assort JSON")
	assert str(target) in text and len(popups) == 1


def test_cancelling_writes_nothing_and_shows_nothing(form, popups, monkeypatch, tmp_path):
	before = sorted(p.name for p in tmp_path.iterdir())  # (the test config files are already here)
	_choose(monkeypatch, None)
	form.onExportAssort()
	assert popups == []
	assert sorted(p.name for p in tmp_path.iterdir()) == before


def test_a_file_that_cannot_be_written_shows_an_error(form, popups, monkeypatch, tmp_path):
	_choose(monkeypatch, tmp_path / "no_such_folder" / "a.json")
	form.onExportAssort()  # must not raise
	assert [kind for kind, *_ in popups] == ["error"]
	assert "no_such_folder" in popups[0][2]


def test_exporting_again_to_another_file_works(form, popups, monkeypatch, tmp_path):
	for name in ("one.json", "two.json"):
		_choose(monkeypatch, tmp_path / name)
		form.onExportAssort()
	one = json.loads((tmp_path / "one.json").read_text(encoding="utf-8"))
	two = json.loads((tmp_path / "two.json").read_text(encoding="utf-8"))
	assert one == two and len(one["items"]) == 2


def test_an_empty_assort_exports_empty_sections(main_window, popups, monkeypatch, tmp_path):
	empty = main_window.spawnWindow("AssortBuilder")
	target = tmp_path / "empty.json"
	_choose(monkeypatch, target)
	empty.onExportAssort()
	assert json.loads(target.read_text(encoding="utf-8")) == {
		"items": [],
		"barter_scheme": {},
		"loyal_level_items": {},
	}


def test_the_exported_file_can_be_imported_again(main_window, form, popups, monkeypatch, tmp_path):
	target = tmp_path / "round_trip.json"
	_choose(monkeypatch, target)
	form.onExportAssort()
	fresh = main_window.spawnWindow("AssortBuilder")
	monkeypatch.setattr(QFileDialog, "getOpenFileName", staticmethod(lambda *a, **k: (str(target), "")))
	fresh.onImportAssort()
	assert fresh.itemlist == form.itemlist
	assert fresh.ui.ab_table.rowCount() == 2


def test_there_is_no_fixed_export_folder_any_more(form, popups, monkeypatch, tmp_path):
	assert not hasattr(paths, "EXPORT_DIR")
	assert not hasattr(assort, "EXPORT_DIR")
	_choose(monkeypatch, tmp_path / "a.json")
	form.onExportAssort()
	assert not (paths.APP_DIR / "exports").exists()
	assert not (paths.APP_DIR / "Exported Files" / "assort.json").exists()
