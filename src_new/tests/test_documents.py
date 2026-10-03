from core import documents
from core.documents import Document


def test_change_undo_redo_dirty():
	doc = Document({"a": 1})
	assert not doc.dirty
	assert doc.change("Set a", lambda d: d.update(a=2))
	assert doc.dirty and doc.data == {"a": 2} and doc.undo_label == "Set a"
	doc.undo()
	assert doc.data == {"a": 1} and not doc.dirty and doc.redo_label == "Set a"
	doc.redo()
	assert doc.data == {"a": 2}


def test_no_change_is_not_recorded():
	doc = Document({"a": 1})
	assert not doc.change("Nothing", lambda d: d.update(a=1))
	assert doc.undo_label is None


def test_new_edit_clears_redo():
	doc = Document({"a": 1})
	doc.change("x", lambda d: d.update(a=2))
	doc.undo()
	doc.change("y", lambda d: d.update(a=3))
	assert not doc.redo()


def test_save_and_open_round_trip(tmp_path):
	doc = Document({"k": {"x": [1, "é"]}})
	doc.change("edit", lambda d: d["k"]["x"].append(2))
	doc.save(tmp_path / "f.json")
	assert not doc.dirty and doc.name == "f.json"
	assert Document.open(tmp_path / "f.json").data == doc.data


def test_listener_called():
	seen = []
	doc = Document({})
	doc.on_change(lambda d: seen.append(1))
	doc.change("x", lambda d: d.update(a=1))
	doc.undo()
	assert len(seen) == 2


def test_list_helpers():
	items = [1, 2, 3]
	assert documents.move(items, 0, 1) == 1 and items == [2, 1, 3]
	assert documents.move(items, 0, -1) == 0
	assert documents.duplicate([{"id": 1}], 0, lambda c: c.update(id=2)) == {"id": 2}


def test_scoped_change_and_undo():
	doc = Document({"a": {"x": 1}, "b": {"y": [1]}})
	doc.change("Add", lambda quest: quest["y"].append(2), path=("b",))
	assert doc.data["b"]["y"] == [1, 2]
	doc.undo()
	assert doc.data == {"a": {"x": 1}, "b": {"y": [1]}}
	doc.redo()
	assert doc.data["b"]["y"] == [1, 2]


def test_form_edits_are_recorded_and_coalesced():
	doc = Document({"q": {"name": ""}})
	doc.watch(("q",))
	for text in ("a", "ab", "abc"):
		doc.data["q"]["name"] = text
		doc.touch("Edit name", coalesce="name")
	assert len(doc._undo) == 1
	doc.undo()
	assert doc.data["q"]["name"] == ""
	doc.redo()
	assert doc.data["q"]["name"] == "abc"


def test_a_different_field_is_a_new_step():
	doc = Document({"q": {"a": 0, "b": 0}})
	doc.watch(("q",))
	doc.data["q"]["a"] = 1
	doc.touch("A", coalesce="a")
	doc.data["q"]["b"] = 1
	doc.touch("B", coalesce="b")
	doc.undo()
	assert doc.data["q"] == {"a": 1, "b": 0}


def test_set_value_undo_and_missing_key():
	doc = Document({"a": "x"})
	doc.set_value("Edit a", ("a",), "y", coalesce="a")
	doc.set_value("Edit a", ("a",), "yz", coalesce="a")
	doc.set_value("Add b", ("b",), "new")
	assert doc.data == {"a": "yz", "b": "new"}
	doc.undo()
	assert doc.data == {"a": "yz"}
	doc.undo()
	assert doc.data == {"a": "x"}
	doc.redo()
	doc.redo()
	assert doc.data == {"a": "yz", "b": "new"}


def test_undo_stamp_orders_documents():
	one, two = Document({"a": 1}), Document({"a": 1})
	one.change("one", lambda d: d.update(a=2))
	two.change("two", lambda d: d.update(a=2))
	assert two.undo_stamp > one.undo_stamp
