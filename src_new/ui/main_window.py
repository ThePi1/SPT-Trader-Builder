"""The main window: menus, one tab per kind of file, and opening / saving them.

A quest file and a locale file are opened (or started from nothing) and saved on their own;
there is no project folder.
"""

from pathlib import Path

from PySide6.QtCore import QThreadPool
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QFileDialog, QLabel, QMainWindow, QMessageBox, QTabWidget

from core import lookup
from core.locale_copy import copy_to_other_languages
from core.documents import Document
from ui import dialogs, updates
from core.library import Library
from schema import assort as assort_schema
from schema import locale as locale_schema
from ui.assort_tab import AssortTab
from ui.composite_tab import CompositeTab
from ui.explorer_tab import ExplorerTab
from ui.locale_tab import LocaleTab
from ui.lookup_view import LookupTab, PickerDialog
from ui.quest_outline import QuestOutline

JSON_FILTER = "JSON files (*.json);;All files (*)"


class MainWindow(QMainWindow):
	def __init__(self, settings, gamedata=None):
		super().__init__()
		self.settings, self.gamedata = settings, gamedata
		self.update_status = updates.pending_status(settings)
		self._workers = []
		self.quests = Document({})
		self.locale = Document({})
		self.assort = Document(assort_schema.empty_assort())
		self.locks = Document(assort_schema.empty_questassort())
		self.tabs = QTabWidget()
		self.setCentralWidget(self.tabs)
		self.quest_outline = QuestOutline(gamedata, settings)
		self.quest_outline.set_document(self.quests)
		self.quest_outline.picker = self.pick
		self.quest_outline.locale = self.locale
		self.locale_tab = LocaleTab(self.locale, self.quests)
		self._base_rows = None
		self.lookup_tab = LookupTab([])
		self.library = Library()
		self.quest_outline.library = self.library
		self.composite_tab = CompositeTab(self.library, gamedata, self.pick)
		self.assort_tab = AssortTab(self.assort, self.locks, gamedata, self.pick, self.library, lambda: self.quests.data)
		self.explorer_tab = ExplorerTab(lambda: self.quests.data, lambda: self.locale.data, gamedata)
		for widget, title in (
			(self.quest_outline, "Quests"), (self.locale_tab, "Text"), (self.assort_tab, "Trader"), (self.composite_tab, "Composite items"), (self.lookup_tab, "Find IDs"), (self.explorer_tab, "Schema Explorer"),
		):
			self.tabs.addTab(widget, title)
		self.tabs.currentChanged.connect(self._tab_changed)
		for doc in (self.quests, self.locale, self.assort, self.locks):
			doc.on_change(lambda _d: self._update_title())
		self.locale.on_change(lambda _d: self._update_title())
		self.locale.on_change(lambda _d: self.quest_outline.check_soon())
		self._build_menus()
		self.resize(1100, 700)
		self._update_title()
		self.start_update_check()

	# --- finding ids --------------------------------------------------------------------------
	def rows(self, kinds=None):
		"""Everything searchable (the game's data, then the quests being edited), for the kinds asked for."""
		if self._base_rows is None:
			self._base_rows = [] if self.gamedata is None else lookup.build_rows(
				self.gamedata, kinds=tuple(k for k in lookup.KIND_LABEL if k != lookup.QUEST)
			)
		mine = lookup.build_rows(self.gamedata, quests=self.quests.data, kinds=(lookup.QUEST,)) if self.gamedata is not None else []
		rows = mine + self._base_rows
		return [r for r in rows if not kinds or r.kind in kinds]

	def pick(self, ref, multi=False, parent=None):
		title = {"item": "Find an item", "quest": "Find a quest", "achievement": "Find an achievement", "customization": "Find clothing"}.get(ref, "Find")
		dialog = PickerDialog(self.rows((ref,)), (ref,), title, multi, parent or self)
		return dialog.ids if dialog.exec() else []

	def _tab_changed(self, index):
		widget = self.tabs.widget(index)
		if widget is self.lookup_tab:
			self.lookup_tab.set_rows(self.rows())
		elif widget is self.locale_tab:
			self.locale_tab.refresh()

	# --- menus ------------------------------------------------------------------------------
	def _action(self, menu, text, slot, shortcut=None):
		action = QAction(text, self)
		action.triggered.connect(slot)
		if shortcut:
			action.setShortcut(QKeySequence(shortcut))
		menu.addAction(action)
		return action

	def _build_menus(self):
		bar = self.menuBar()
		file_menu = bar.addMenu("&File")
		self._action(file_menu, "&New quest file", self.new_quests, "Ctrl+N")
		self._action(file_menu, "&Open quest file...", self.open_quests, "Ctrl+O")
		self._action(file_menu, "&Save quest file", self.save_quests, "Ctrl+S")
		self._action(file_menu, "Save quest file &as...", self.save_quests_as, "Ctrl+Shift+S")
		file_menu.addSeparator()
		self._action(file_menu, "New &text file", self.new_locale)
		self._action(file_menu, "Open t&ext file...", self.open_locale)
		self._action(file_menu, "Save text &file", self.save_locale, "Ctrl+Alt+S")
		self._action(file_menu, "Save text file as...", self.save_locale_as)
		for title, label, setter_name in (("Trader assort", "assort", "assort"), ("Quest locks", "locks", "locks")):
			sub = file_menu.addMenu(title)
			self._action(sub, "New", lambda _c=False, n=setter_name: self._new_other(n))
			self._action(sub, "Open...", lambda _c=False, n=setter_name: self._open_other(n))
			self._action(sub, "Save", lambda _c=False, n=setter_name: self._save_other(n))
			self._action(sub, "Save as...", lambda _c=False, n=setter_name: self._save_other(n, True))
		file_menu.addSeparator()
		self._action(file_menu, "E&xit", self.close, "Alt+F4")
		edit = bar.addMenu("&Edit")
		self.undo_action = self._action(edit, "&Undo", self.undo, "Ctrl+Z")
		self.redo_action = self._action(edit, "&Redo", self.redo, "Ctrl+Y")
		edit.aboutToShow.connect(self._update_edit_menu)
		settings = bar.addMenu("&Settings")
		self._action(settings, "&Settings...", self.show_settings)
		help_menu = bar.addMenu("&Help")
		self._action(help_menu, "&About", self.show_about)
		self._action(help_menu, "Check for &updates", self.show_updates)

	def _update_edit_menu(self):
		undo_doc = self._latest()
		redo_doc = max(self._docs(), key=lambda d: d.redo_stamp)
		self.undo_action.setEnabled(undo_doc.undo_label is not None)
		self.undo_action.setText(f"&Undo {undo_doc.undo_label}" if undo_doc.undo_label else "&Undo")
		self.redo_action.setEnabled(redo_doc.redo_label is not None)
		self.redo_action.setText(f"&Redo {redo_doc.redo_label}" if redo_doc.redo_label else "&Redo")

	def _update_title(self):
		def label(doc):
			return doc.name + ("*" if doc.dirty else "")

		shown = [label(d) for d in self._docs() if d.path is not None or d.dirty]
		self.setWindowTitle(f"{', '.join(shown) or 'Untitled'} - {dialogs.APP_NAME}")

	# --- files ------------------------------------------------------------------------------
	def _confirm_discard(self, doc, label):
		"""True if it is fine to replace this open file (saved, or the user chose to drop the changes)."""
		if not doc.dirty:
			return True
		answer = QMessageBox.question(
			self, "Unsaved changes", f"Save your changes to {doc.name}?",
			QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
		)
		if answer == QMessageBox.StandardButton.Save:
			return self._save(doc, label)
		return answer == QMessageBox.StandardButton.Discard

	def _set_quests(self, doc):
		self.quests = doc
		doc.on_change(lambda _d: self._update_title())
		self.quest_outline.set_document(doc)
		self.locale_tab.set_documents(self.locale, doc)
		self._update_title()

	def _set_locale(self, doc):
		self.locale = doc
		doc.on_change(lambda _d: self._update_title())
		doc.on_change(lambda _d: self.quest_outline.check_soon())
		self.quest_outline.locale = doc
		self.quest_outline.rebuild()
		self.quest_outline.check()
		self.locale_tab.set_documents(doc, self.quests)
		self._update_title()

	def _new(self, doc, label, setter):
		if self._confirm_discard(doc, label):
			setter(Document({}))

	def _open(self, doc, label, setter):
		if not self._confirm_discard(doc, label):
			return
		path, _ = QFileDialog.getOpenFileName(self, f"Open {label} file", "", JSON_FILTER)
		if not path:
			return
		try:
			opened = Document.open(path)
		except (OSError, ValueError) as e:
			QMessageBox.warning(self, f"Open {label} file", f"The file could not be opened.\n\n{e}")
			return
		if not isinstance(opened.data, dict):
			QMessageBox.warning(self, f"Open {label} file", f"This doesn't look like a {label} file.")
			return
		setter(opened)

	def _save(self, doc, label, as_new=False):
		path = None if as_new or doc.path is None else doc.path
		if path is None:
			start = doc.name if doc.path else f"{label}s.json"
			chosen, _ = QFileDialog.getSaveFileName(self, f"Save {label} file", start, JSON_FILTER)
			if not chosen:
				return False
			path = chosen
		try:
			doc.save(path)
		except OSError as e:
			QMessageBox.warning(self, "Save", f"The file could not be saved.\n\n{e}")
			return False
		if doc is self.locale and self.settings.copy_locale_to_all_languages:
			self.copy_text_to_other_languages()
		return True

	def copy_text_to_other_languages(self):
		"""Add the saved text (that of the open quests, or all of it when no quests are open) to the other
		languages' files next to it. Entries those files already have are kept."""
		folder = Path(self.locale.path).parent
		entries = dict(self.locale.data)
		if self.quests.data:
			mine = locale_schema.key_owners(self.quests.data)
			entries = {key: text for key, text in entries.items() if key in mine}
		languages = self.gamedata.languages if self.gamedata is not None else {"en": "English"}
		changed, failed = copy_to_other_languages(entries, folder, Path(self.locale.path).name, languages)
		if changed:
			self.statusBar().showMessage(f"The text was also added to {len(changed)} other language file(s).", 8000)
		if failed:
			QMessageBox.warning(
				self, "Copy text",
				"The text could not be added to some language files:\n\n" + "\n".join(f"{name}: {why}" for name, why in failed.items()),
			)

	def new_quests(self):
		self._new(self.quests, "quest", self._set_quests)

	def open_quests(self):
		self._open(self.quests, "quest", self._set_quests)

	def save_quests(self):
		return self._save(self.quests, "quest")

	def save_quests_as(self):
		return self._save(self.quests, "quest", as_new=True)

	def new_locale(self):
		self._new(self.locale, "text", self._set_locale)

	def open_locale(self):
		self._open(self.locale, "text", self._set_locale)

	def save_locale(self):
		return self._save(self.locale, "text")

	def save_locale_as(self):
		return self._save(self.locale, "text", as_new=True)

	_OTHER = {"assort": ("trader assort", assort_schema.empty_assort), "locks": ("quest locks", assort_schema.empty_questassort)}

	def _set_other(self, name, doc):
		setattr(self, name, doc)
		doc.on_change(lambda _d: self._update_title())
		self.assort_tab.watch(self.assort, self.locks)
		self._update_title()

	def _new_other(self, name):
		label, empty = self._OTHER[name]
		if self._confirm_discard(getattr(self, name), label):
			self._set_other(name, Document(empty()))

	def _open_other(self, name):
		label, empty = self._OTHER[name]
		self._open(getattr(self, name), label, lambda doc: self._set_other(name, doc))

	def _save_other(self, name, as_new=False):
		return self._save(getattr(self, name), self._OTHER[name][0], as_new)

	def _docs(self):
		return (self.quests, self.locale, self.assort, self.locks)

	def _latest(self):
		"""The document whose last edit was most recent (what Undo undoes)."""
		return max(self._docs(), key=lambda d: d.undo_stamp)

	def undo(self):
		self._latest().undo()

	def redo(self):
		max(self._docs(), key=lambda d: d.redo_stamp).redo()

	def closeEvent(self, event):
		if all(self._confirm_discard(d, l) for d, l in zip(self._docs(), ("quest", "text", "trader assort", "quest locks"))):
			event.accept()
		else:
			event.ignore()

	# --- settings, about, updates -----------------------------------------------------------
	def show_settings(self):
		before = {k: getattr(self.settings, k) for k in ("version_file", "version_url", "project_url")}
		if dialogs.SettingsDialog(self.settings, self.gamedata, self).exec():
			if before != {k: getattr(self.settings, k) for k in before}:
				self.update_status = updates.pending_status(self.settings)
				self.start_update_check()
			self.quest_outline.apply_settings()

	def show_about(self):
		dialogs.AboutDialog(self.update_status.local_version, self.update_status.project_url, self).exec()

	def show_updates(self):
		dialogs.UpdatesDialog(self.update_status, self).exec()

	def start_update_check(self):
		for old in self._workers:
			old.stale = True
		worker = updates.UpdateCheckWorker(self.settings)
		worker.signals.finished.connect(self._set_update_status)
		self._workers.append(worker)
		QThreadPool.globalInstance().start(worker)

	def _set_update_status(self, status):
		self.update_status = status
		if status.state == updates.OUTDATED:
			self.statusBar().showMessage(f"A newer version ({status.latest_version}) is available.", 10000)
