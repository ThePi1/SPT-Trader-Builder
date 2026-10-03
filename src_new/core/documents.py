"""An open file being edited: a working copy of its data, with undo and a changed flag.

The file on disk is only written when the user saves. Every edit goes through ``change`` so it
can be undone; keys the app doesn't know stay in the data untouched.
"""

import copy
from pathlib import Path

from core import jsonio

import itertools

UNDO_LIMIT = 200
_clock = itertools.count(1)  # orders edits across documents, so Undo can pick the latest one


class _Leaf:
	"""An undo snapshot of one value (not a whole subtree); value MISSING means the key wasn't there."""

	def __init__(self, value):
		self.value = value


MISSING = object()


class Document:
	def __init__(self, data=None, path=None):
		self.data = data if data is not None else {}
		self.path = Path(path) if path else None
		self._saved = copy.deepcopy(self.data)
		self._undo = []  # (label, path, subtree before, coalesce key)
		self._redo = []
		self._watched = None
		self._listeners = []

	# --- opening and saving ---------------------------------------------------------------
	@classmethod
	def open(cls, path):
		return cls(jsonio.read_json(path), path)

	def save(self, path=None):
		"""Write the data to path (or the file it was opened from)."""
		target = Path(path) if path else self.path
		if target is None:
			raise ValueError("no file name to save to")
		jsonio.write_json(target, self.data)
		self.path = target
		self._saved = copy.deepcopy(self.data)
		self._notify()

	@property
	def dirty(self):
		return self.data != self._saved

	@property
	def name(self):
		return self.path.name if self.path else "Untitled"

	# --- editing --------------------------------------------------------------------------
	# An undo step remembers the part of the data it changed (the subtree at ``path``), so a
	# change inside one quest of a big file only copies that quest.
	def change(self, label, edit, path=()):
		"""Run edit(subtree) as one undoable step on the data at path. Nothing is recorded if edit changes nothing."""
		node = _get(self.data, path)
		before = copy.deepcopy(node)
		edit(node)
		if node == before:
			return False
		self._record(label, path, before)
		return True

	def watch(self, path=()):
		"""Start following edits made directly to the data at path (by a form); touch() records them."""
		self._watched = (tuple(path), copy.deepcopy(_get(self.data, path)))

	def touch(self, label, coalesce=None):
		"""Record what changed since watch() / the last touch() as an undo step. Edits with the same
		coalesce key one after another (typing in one field) become one step."""
		if self._watched is None:
			return False
		path, before = self._watched
		node = _get(self.data, path)
		if node == before:
			return False
		merge = coalesce is not None and self._undo and self._undo[-1][3] == (path, coalesce)
		if merge:
			self._redo.clear()
			self._watched = (path, copy.deepcopy(node))
			self._notify()
			return True
		self._record(label, path, before, coalesce)
		return True

	def _record(self, label, path, before, coalesce=None):
		self._undo.append((label, path, before, (path, coalesce) if coalesce is not None else None, next(_clock)))
		del self._undo[:-UNDO_LIMIT]
		self._redo.clear()
		self._watched = (path, copy.deepcopy(_get(self.data, path)))
		self._notify()

	def set_value(self, label, path, value, coalesce=None):
		"""Set one value of a dict (deleting the key when value is MISSING) as an undoable step.
		Typing in the same field again (same coalesce key) stays one step."""
		parent = _get(self.data, path[:-1])
		before = parent.get(path[-1], MISSING)
		if before == value and before is not MISSING:
			return False
		key = (path, coalesce) if coalesce is not None else None
		if value is MISSING:
			parent.pop(path[-1], None)
		else:
			parent[path[-1]] = value
		if key is not None and self._undo and self._undo[-1][3] == key:
			self._redo.clear()
			self._notify()
			return True
		self._undo.append((label, path, _Leaf(before), key, next(_clock)))
		del self._undo[:-UNDO_LIMIT]
		self._redo.clear()
		self._notify()
		return True

	@property
	def undo_stamp(self):
		return self._undo[-1][4] if self._undo else 0

	@property
	def redo_stamp(self):
		return self._redo[-1][4] if self._redo else 0

	def replace(self, label, data):
		return self.change(label, lambda node: _swap(node, data))

	@property
	def undo_label(self):
		return self._undo[-1][0] if self._undo else None

	@property
	def redo_label(self):
		return self._redo[-1][0] if self._redo else None

	def undo(self):
		return self._step(self._undo, self._redo)

	def redo(self):
		return self._step(self._redo, self._undo)

	def _step(self, source, target):
		if not source:
			return False
		label, path, snapshot, _key, _stamp = source.pop()
		if isinstance(snapshot, _Leaf):
			parent = _get(self.data, path[:-1])
			target.append((label, path, _Leaf(parent.get(path[-1], MISSING)), None, next(_clock)))
			if snapshot.value is MISSING:
				parent.pop(path[-1], None)
			else:
				parent[path[-1]] = snapshot.value
			self._notify()
			return True
		node = _get(self.data, path)
		target.append((label, path, copy.deepcopy(node), None, next(_clock)))
		_swap(node, snapshot)
		self._watched = (path, copy.deepcopy(node))
		self._notify()
		return True

	# --- listeners ------------------------------------------------------------------------
	def on_change(self, callback):
		self._listeners.append(callback)

	def _notify(self):
		for callback in list(self._listeners):
			callback(self)


def _get(data, path):
	for part in path:
		data = data[part]
	return data


def _swap(node, new):
	"""Make node (a dict or list) hold what new holds, in place."""
	new = copy.deepcopy(new)
	if isinstance(node, dict):
		node.clear()
		node.update(new)
	else:
		node[:] = new
	return node


# --- list helpers for the outline: move / duplicate / remove inside a list ------------------

def move(items, index, offset):
	"""Move items[index] by offset places; returns the new index (unchanged if it can't move)."""
	new = index + offset
	if not 0 <= new < len(items):
		return index
	items.insert(new, items.pop(index))
	return new


def duplicate(items, index, fresh=None):
	"""Insert a copy after items[index] and return it; fresh(copy) may give it new ids."""
	clone = copy.deepcopy(items[index])
	if fresh:
		fresh(clone)
	items.insert(index + 1, clone)
	return clone
