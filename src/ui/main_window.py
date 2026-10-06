"""The main window: menus, one tab per kind of file, and opening / saving them.

A quest file and a locale file are opened (or started from nothing) and saved on their own;
there is no project folder.
"""

import re
from pathlib import Path

from PySide6.QtCore import QThreadPool, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileDialog, QInputDialog, QMainWindow, QMessageBox

from core import lookup
from core import jsonio
from core import merge as M
from core.export import export_selection
from core.locale_copy import copy_to_other_languages
from core.documents import Document
from core.last_files import LastFiles
from core.paths import ICON_FILE
from core.references import References
from ui import dialogs, updates
from core.library import Library
from schema import assort as assort_schema
from schema import locale as locale_schema
from ui.assort_tab import AssortTab
from ui.compiled.ui_main_window import Ui_MainWindowForm
from ui.composite_tab import CompositeTab
from ui.explorer_tab import ExplorerTab
from ui.export_dialog import ExportDialog
from ui.files_strip import FilesStrip
from ui.import_dialog import ImportDialog
from ui.references_dialog import ReferencesDialog
from ui.locale_tab import LocaleTab
from ui.lookup_view import LookupTab, PickerDialog
from ui.quest_graph_tab import QuestGraphTab, Sources
from ui.quest_outline import QuestOutline
from ui.tabs import fill_tabs

JSON_FILTER = "JSON files (*.json);;All files (*)"
# (key = the attribute holding its Document, the strip's title, the name used in dialogs, the kind core.merge knows it as)
KINDS = (
	("quests", "Quests", "quest", M.QUESTS), ("locale", "Locale", "locale", M.LOCALE),
	("assort", "Trader assort", "trader assort", M.ASSORT), ("locks", "Quest assort", "quest assort", M.LOCKS),
)
KEY_OF_KIND = {kind: key for key, _title, _label, kind in KINDS}
LAST_KEYS = ("quests", "locale", "assort", "locks")  # (the sections whose file is remembered)


def app_icon():
	"""The window icon (an empty icon, so no icon, if the file is missing)."""
	return QIcon(str(ICON_FILE)) if ICON_FILE.is_file() else QIcon()


class MainWindow(QMainWindow, Ui_MainWindowForm):
	"""The window, its menus and the (empty) tab bar are ui/designer/main_window.ui; the tabs are added here."""

	def __init__(self, settings, gamedata=None):
		super().__init__()
		self.setupUi(self)
		self.settings, self.gamedata = settings, gamedata
		self.setWindowIcon(app_icon())
		self.update_status = updates.pending_status(settings)
		self._workers = []
		self.quest_sources = {}  # quest id -> the file it was imported from
		self.references = References(language=settings.language)  # files that are only looked at
		self.last_files = LastFiles()  # the files that are open, kept for "Load last files on open"
		self._restoring = False
		if gamedata is not None:
			gamedata.references = self.references
		self.quests = Document({})
		self.locale = Document({})
		self.assort = Document(assort_schema.empty_assort())
		self.locks = Document(assort_schema.empty_questassort())
		self.quest_outline = QuestOutline(gamedata, settings)
		self.quest_outline.set_document(self.quests)
		self.quest_outline.picker = self.pick
		self.quest_outline.assort_source = lambda: (self.assort.data, self.locks.data, self.assort_tab.trader_id)
		self.quest_outline.locale = self.locale
		self.locale_tab = LocaleTab(self.locale, self.quests, settings)
		self._base_rows = None
		self.lookup_tab = LookupTab([], settings)
		self.library = Library()
		self.quest_outline.library = self.library
		self.composite_tab = CompositeTab(self.library, gamedata, self.pick)
		self.assort_tab = AssortTab(
			self.assort, self.locks, gamedata, self.pick, self.library, lambda: self.quests.data, lambda: self.quests
		)
		self.graph_tab = QuestGraphTab(self._graph_sources)
		self.graph_tab.open_requested.connect(self.show_quest)
		self.explorer_tab = ExplorerTab(lambda: self.quests.data, lambda: self.locale.data, gamedata, settings)
		fill_tabs(self.tabs, self, {
			"page_quests": self.quest_outline, "page_locale": self.locale_tab, "page_trader": self.assort_tab,
			"page_composite": self.composite_tab, "page_quest_graph": self.graph_tab, "page_find_ids": self.lookup_tab,
			"page_explorer": self.explorer_tab,
		})
		self.tabs.currentChanged.connect(self._tab_changed)
		self.files_strip = FilesStrip([(key, title) for key, title, _label, _kind in KINDS] + [("references", "References")])
		self.files_strip.segment("references").fileLabel.setVisible(False)  # (nothing to say under "References" but the count)
		self.centralLayout.addWidget(self.files_strip)
		for doc in (self.quests, self.locale, self.assort, self.locks):
			doc.on_change(self._doc_changed)
		self.locale.on_change(lambda _d: self.quest_outline.check_soon())
		self._connect_menus()
		self.setAcceptDrops(True)
		self._doc_changed()
		self.start_update_check()

	# --- finding ids --------------------------------------------------------------------------
	def rows(self, kinds=None):
		"""Everything searchable (the game's data, then the quests and saved composite items being edited), for the kinds asked for."""
		if self._base_rows is None:
			self._base_rows = [] if self.gamedata is None else lookup.build_rows(
				self.gamedata, kinds=tuple(k for k in lookup.KIND_LABEL if k not in (lookup.QUEST, lookup.MINE, lookup.REF_QUEST)),
				references=self.references,
			)
		mine = lookup.build_rows(
			self.gamedata, quests=self.quests.data, kinds=(lookup.QUEST, lookup.REF_QUEST), references=self.references,
		) if self.gamedata is not None else []
		rows = mine + lookup.library_rows(self.library) + self._base_rows
		return [r for r in rows if not kinds or r.kind in kinds]

	def pick(self, ref, multi=False, parent=None):
		title = {
			"item": "Find an item", "quest": "Find a quest", "achievement": "Find an achievement", "customization": "Find clothing",
			"composite": "Find a composite item", "part": "Find an item", "item_id": "Find an item", "item_list": "Find an item",
		}.get(ref, "Find")
		kinds = {
			"composite": (lookup.MINE, lookup.PRESET),  # (saved ones and the game's)
			"part": (lookup.ITEM, lookup.REF_ITEM, lookup.MINE, lookup.PRESET),  # (what a list of item parts can take)
			"item_id": (lookup.ITEM, lookup.REF_ITEM, lookup.MINE, lookup.PRESET, lookup.CATEGORY),  # (the list that takes categories as they are)
			"item_list": (lookup.ITEM, lookup.REF_ITEM, lookup.MINE, lookup.PRESET, lookup.CATEGORY),  # (an item list: a category stands for the items under it)
			"item": (lookup.ITEM, lookup.REF_ITEM), "quest": (lookup.QUEST, lookup.REF_QUEST),  # (the game's, and the reference files')
		}.get(ref, (ref,))
		dialog = PickerDialog(self.rows(kinds), kinds, title, multi, self.settings, parent or self)
		return dialog.ids if dialog.exec() else []

	def _graph_sources(self):
		"""What the Quest Graph is built from: the quests open now, the reference files and the base game."""
		game = self.gamedata
		return Sources(
			open_quests=self.quests.data, imported=dict(self.quest_sources), references=self.references,
			game=game.vanilla_quests if game is not None else {}, trader_names=game.all_traders() if game is not None else {},
			game_name=game.quest_name if game is not None else (lambda quest_id: ""),
		)

	def show_quest(self, quest_id):
		"""Go to the Quests tab and select this quest."""
		self.tabs.setCurrentWidget(self.quest_outline)
		self.quest_outline._select_key(("quest", (quest_id,)))

	def _tab_changed(self, index):
		widget = self.tabs.widget(index)
		if widget is self.graph_tab:
			self.graph_tab.refresh_if_stale()
		elif widget is self.lookup_tab:
			self.lookup_tab.set_rows(self.rows())
		elif widget is self.locale_tab:
			self.locale_tab.refresh()
		elif widget is self.assort_tab:
			self.assort_tab.refresh(self.assort_tab.current_id())  # (the quests may have changed)

	# --- menus ------------------------------------------------------------------------------
	def _connect_menus(self):
		"""The menus and their actions are in main_window.ui (names, shortcuts); this says what each one does.
		The same actions are the menus of the files strip's segments."""
		sections = {
			"quests": (self.actionNewQuests, self.actionOpenQuests, self.actionImportQuests, self.actionSaveQuests, self.actionSaveQuestsAs),
			"locale": (self.actionNewLocale, self.actionOpenLocale, self.actionImportLocale, self.actionSaveLocale, self.actionSaveLocaleAs),
			"assort": (self.actionAssortNew, self.actionAssortOpen, self.actionAssortImport, self.actionAssortSave, self.actionAssortSaveAs),
			"locks": (self.actionLocksNew, self.actionLocksOpen, self.actionLocksImport, self.actionLocksSave, self.actionLocksSaveAs),
		}
		doing = {
			"quests": (self.new_quests, self.open_quests, self.save_quests, self.save_quests_as),
			"locale": (self.new_locale, self.open_locale, self.save_locale, self.save_locale_as),
			"assort": (lambda: self._new_other("assort"), lambda: self._open_other("assort"), lambda: self._save_other("assort"), lambda: self._save_other("assort", True)),
			"locks": (lambda: self._new_other("locks"), lambda: self._open_other("locks"), lambda: self._save_other("locks"), lambda: self._save_other("locks", True)),
		}
		for key, (new, open_, import_, save, save_as) in sections.items():
			do_new, do_open, do_save, do_save_as = doing[key]
			for action, slot in ((new, do_new), (open_, do_open), (import_, lambda key=key: self.import_into(key)), (save, do_save), (save_as, do_save_as)):
				action.triggered.connect(lambda _checked=False, slot=slot: slot())
			menu = self.files_strip.segment(key).menu
			for action in (new, open_, import_):
				menu.addAction(action)
			menu.addSeparator()
			menu.addAction(save)
			menu.addAction(save_as)
		reference_menu = self.files_strip.segment("references").menu
		for action, slot in (
			(self.actionAddReferences, self.add_references), (self.actionManageReferences, self.manage_references),
			(self.actionReloadReferences, self.reload_references),
		):
			action.triggered.connect(lambda _checked=False, slot=slot: slot())
			reference_menu.addAction(action)
		for action, slot in (
			(self.actionImportFiles, self.import_any), (self.actionExit, self.close), (self.actionUndo, self.undo),
			(self.actionRedo, self.redo), (self.actionSettings, self.show_settings), (self.actionAbout, self.show_about),
			(self.actionUpdates, self.show_updates),
		):
			action.triggered.connect(lambda _checked=False, slot=slot: slot())
		self.actionExportQuests.triggered.connect(lambda _checked=False: self.export_quests())
		self.quest_outline.export_requested.connect(self.export_quests)
		self.undo_action, self.redo_action = self.actionUndo, self.actionRedo
		self.actionRegenerateAssort.triggered.connect(lambda _checked=False: self.debug_regenerate_assort())
		self.actionRegenerateLocks.triggered.connect(lambda _checked=False: self.debug_regenerate_locks())
		self.apply_debug_option()
		self.menuEdit.aboutToShow.connect(self._update_edit_menu)

	def apply_debug_option(self):
		"""The Debug menu is there only while "Enable debug options" is on."""
		self.menuDebug.menuAction().setVisible(bool(getattr(self.settings, "enable_debug_options", False)))

	def _folder_of(self, doc):
		return str(Path(doc.path).parent) if doc.path else ""

	def debug_regenerate_assort(self):
		"""Debug: save a new trader assort file made only of the offers the program knows (the open assort's offers, with their
		items, prices and levels). The open assort is not changed."""
		offers = assort_schema.offer_ids(self.assort.data)
		if not offers:
			QMessageBox.information(self, "Regenerate trader assort", "There is no trader assort open yet: open or import one first.")
			return None
		path, _ = QFileDialog.getSaveFileName(self, "Save the regenerated trader assort", str(Path(self._folder_of(self.assort)) / "assort.json"), JSON_FILTER)
		if not path:
			return None
		new, left_out = assort_schema.regenerate_assort(self.assort.data)
		return self._save_debug_file(path, new, f"{len(offers)} offer{'' if len(offers) == 1 else 's'}", left_out)

	def debug_regenerate_locks(self):
		"""Debug: save a new quest assort file with only the links to offers (in the open trader assort) and quests (open, in the
		base game or in a reference file) that are known. The open quest assort is not changed."""
		offers = set(assort_schema.offer_ids(self.assort.data))
		if not offers:
			QMessageBox.information(self, "Regenerate quest assort", "There is no trader assort open, so no offer is known and every link would be removed. Open or import one first.")
			return None
		path, _ = QFileDialog.getSaveFileName(self, "Save the regenerated quest assort", str(Path(self._folder_of(self.locks)) / "questassort.json"), JSON_FILTER)
		if not path:
			return None
		known = self.quests.data
		new, dropped = assort_schema.regenerate_questassort(
			self.locks.data, offers, lambda quest_id: quest_id in known or (self.gamedata is not None and self.gamedata.knows_quest(quest_id)),
		)
		kept = sum(len(links) for links in new.values())
		left_out = [f"{section}: {offer or '(section)'} -> {quest or '-'} ({why})" for section, offer, quest, why in dropped]
		return self._save_debug_file(path, new, f"{kept} link{'' if kept == 1 else 's'}", left_out)

	def _save_debug_file(self, path, data, what, left_out):
		try:
			jsonio.write_json(path, data)
		except OSError as e:
			QMessageBox.warning(self, "Save", f"The file could not be saved.\n\n{e}")
			return None
		text = f"Saved {what} to {Path(path).name}."
		if left_out:
			text += f" Left out: {'; '.join(left_out[:4])}" + (f" (and {len(left_out) - 4} more)" if len(left_out) > 4 else "") + "."
		self.statusBar().showMessage(text, 20000)
		return {"path": path, "data": data, "left_out": left_out}

	def _update_edit_menu(self):
		undo_doc = self._latest()
		redo_doc = max(self._docs(), key=lambda d: d.redo_stamp)
		self.undo_action.setEnabled(undo_doc.undo_label is not None)
		self.undo_action.setText(f"&Undo {undo_doc.undo_label}" if undo_doc.undo_label else "&Undo")
		self.redo_action.setEnabled(redo_doc.redo_label is not None)
		self.redo_action.setText(f"&Redo {redo_doc.redo_label}" if redo_doc.redo_label else "&Redo")

	def _update_title(self):
		"""The title is the program's name, with * when anything is unsaved (the files strip says which)."""
		self.setWindowTitle(dialogs.APP_NAME + ("*" if any(d.dirty for d in self._docs()) else ""))

	def _doc_changed(self, _doc=None):
		self.graph_tab.invalidate()
		self._update_title()
		self._refresh_strip()

	def imported_files(self, key):
		"""The names of the files imported into this section that are still in it (undoing an import takes them out)."""
		names = []
		for note in getattr(self, key).applied_notes():
			names.extend(name for name in note if name not in names)
		return names

	def _count(self, key):
		data = getattr(self, key).data
		if key == "assort":
			return len(assort_schema.offer_ids(data))
		if key == "locks":
			return sum(len(v) for v in data.values() if isinstance(v, dict))
		return len(data)

	# --- reference files ----------------------------------------------------------------------
	def add_references(self, paths=None):
		if paths is None:
			paths, _ = QFileDialog.getOpenFileNames(self, "Add reference files", "", JSON_FILTER)
		if not paths:
			return None
		added, skipped = self.references.add(paths)
		self._references_changed()
		text = f"Added {len(added)} reference file{'' if len(added) == 1 else 's'}."
		if skipped:
			text += f" Left out: {', '.join(f'{name} ({why})' for name, why in skipped[:3])}" + (" ..." if len(skipped) > 3 else "")
		self.statusBar().showMessage(text, 15000)
		return added

	def manage_references(self):
		dialog = ReferencesDialog(self.references, self)
		dialog.changed.connect(self._references_changed)
		dialog.import_requested.connect(lambda paths: QTimer.singleShot(0, lambda: self.import_files(paths)))
		dialog.exec()

	def reload_references(self):
		self.references.reload()
		self._references_changed()
		self.statusBar().showMessage("Reference files read again.", 8000)

	def _references_changed(self):
		"""The reference files changed: names, checks and the id lists have to look again."""
		self._base_rows = None
		if self.tabs.currentWidget() is self.lookup_tab:
			self.lookup_tab.set_rows(self.rows())
		self.quest_outline.rebuild()
		self.quest_outline.check()
		self.assort_tab.refresh(self.assort_tab.current_id())
		self._doc_changed()

	def _refresh_strip(self):
		for key, _title, _label, _kind in KINDS:
			doc, count, names = getattr(self, key), self._count(key), self.imported_files(key)
			imports = f"{len(names)} file{'' if len(names) == 1 else 's'} imported" if names else ""
			if doc.path:
				file_text = doc.name + (f" \u00b7 +{imports}" if imports else "")
			else:
				file_text = ("not saved yet" if count else "empty") + (f" \u00b7 {imports}" if imports else "")
			state, tone = ("unsaved", "warn") if doc.dirty else (("saved", "ok") if doc.path else ("", "muted"))
			self.files_strip.segment(key).set_info(count, state, tone, file_text, str(doc.path) if doc.path else "")
		files = self.references.files
		names = "\n".join(ref.name for ref in files)
		self.files_strip.segment("references").set_info(len(files), "", "muted", "", names or "No reference files yet")  # (the count in the title says it; the file names are the tooltip)

	# --- files ------------------------------------------------------------------------------
	def _confirm_discard(self, doc, label):
		"""True if it is fine to replace this open file (saved, or the user chose to drop the changes)."""
		if not doc.dirty:
			return True
		answer = QMessageBox.question(
			self, "Unsaved changes", f"Save your changes to {label} file {doc.name}?",
			QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
		)
		if answer == QMessageBox.StandardButton.Save:
			return self._save(doc, label)
		return answer == QMessageBox.StandardButton.Discard

	def _set_quests(self, doc):
		self.quests = doc
		self.quest_sources.clear()
		doc.on_change(self._doc_changed)
		self.quest_outline.set_document(doc)
		self.locale_tab.set_documents(self.locale, doc)
		self._doc_changed()
		self._remember_files()

	def _set_locale(self, doc):
		self.locale = doc
		doc.on_change(self._doc_changed)
		doc.on_change(lambda _d: self.quest_outline.check_soon())
		self.quest_outline.locale = doc
		self.quest_outline.rebuild()
		self.quest_outline.check()
		self.locale_tab.set_documents(doc, self.quests)
		self._doc_changed()
		self._remember_files()

	def _new(self, doc, label, setter):
		if self._confirm_discard(doc, label):
			setter(Document({}))

	def _open(self, doc, label, setter, path=None):
		"""Open a file in place of this section's: the one at path, or the one the user picks."""
		if not self._confirm_discard(doc, label):
			return
		if path is None:
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
		path = doc.path
		if as_new or path is None or self.settings.save_asks_for_file:
			start = str(doc.path) if doc.path else f"{self.settings.language}.json" if doc is self.locale else f"{label}s.json"
			chosen, _ = QFileDialog.getSaveFileName(self, f"Save {label} file", start, JSON_FILTER)
			if not chosen:
				return False
			path = chosen
		try:
			doc.save(path)
		except OSError as e:
			QMessageBox.warning(self, "Save", f"The file could not be saved.\n\n{e}")
			return False
		self._remember_files()
		if doc is self.locale and self.settings.copy_locale_to_all_languages:
			self.copy_text_to_other_languages()
		return True

	# --- the files that were open last time ----------------------------------------------------
	def _remember_files(self):
		"""Keep the file each section was opened from or saved to, for "Load last files on open" (only while that is on)."""
		if not getattr(self.settings, "load_last_files", False) or self._restoring:
			return
		self.last_files.write({key: str(getattr(self, key).path) if getattr(self, key).path else None for key in LAST_KEYS})

	def restore_last_files(self):
		"""Open the files that were open when the program was last closed, if the setting is on. They open the way File > Open
		opens them (so an assort asks which trader it is for). Imported files are not part of this. Returns the paths opened."""
		if not getattr(self.settings, "load_last_files", False):
			return []
		last = self.last_files.read()
		openers = {
			"quests": self.open_quests, "locale": self.open_locale,
			"assort": lambda path: self._open_other("assort", path), "locks": lambda path: self._open_other("locks", path),
		}
		opened, missing = [], []
		self._restoring = True  # (what is kept is only updated when all are done: opening the first must not forget the rest)
		try:
			for key in LAST_KEYS:
				path = last.get(key)
				if not path:
					continue
				if not Path(path).is_file():
					missing.append(Path(path).name)
					continue
				openers[key](path)
				if getattr(self, key).path == Path(path):
					opened.append(path)
		finally:
			self._restoring = False
		self._remember_files()
		if missing:
			self.statusBar().showMessage(f"Not opened again, because they are gone: {', '.join(missing)}.", 15000)
		return opened

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

	def open_quests(self, path=None):
		self._open(self.quests, "quest", self._set_quests, path)

	def save_quests(self):
		return self._save(self.quests, "quest")

	def save_quests_as(self):
		return self._save(self.quests, "quest", as_new=True)

	def new_locale(self):
		self._new(self.locale, "locale", self._set_locale)

	def open_locale(self, path=None):
		self._open(self.locale, "locale", self._set_locale, path)

	def save_locale(self):
		return self._save(self.locale, "locale")

	def save_locale_as(self):
		return self._save(self.locale, "locale", as_new=True)

	_OTHER = {"assort": ("trader assort", assort_schema.empty_assort), "locks": ("quest assort", assort_schema.empty_questassort)}

	def _set_other(self, name, doc):
		setattr(self, name, doc)
		doc.on_change(self._doc_changed)
		self.assort_tab.watch(self.assort, self.locks)
		self._doc_changed()
		self._remember_files()

	def _new_other(self, name):
		label, empty = self._OTHER[name]
		if self._confirm_discard(getattr(self, name), label):
			self._set_other(name, Document(empty()))

	def _open_other(self, name, path=None):
		label, empty = self._OTHER[name]

		def opened(doc):
			self._set_other(name, doc)
			if name == "assort":
				self.ask_trader(doc.path)

		self._open(getattr(self, name), label, opened, path)

	def ask_trader(self, path=None):
		"""Ask which trader an assort file is for (starting from where the file is, else the trader chosen now) and put the
		answer in the Trader box. Cancelling leaves the Trader box as it is."""
		traders = self.gamedata.all_traders() if self.gamedata is not None else {}
		current = (M.guess_trader(path, traders) if path else "") or self.assort_tab.trader_id
		choices = [("(not set)", "")] + [(name, trader_id) for trader_id, name in traders.items()]
		if current and current not in traders:
			choices.append((current, current))  # (a trader the list doesn't know: shown by its id)
		labels = [label for label, _id in choices]
		start = next((i for i, (_label, trader_id) in enumerate(choices) if trader_id == current), 0)
		text, ok = QInputDialog.getItem(self, "Trader", "Which trader is this assort for? (You can also paste a trader id.)", labels, start, True)
		if not ok:
			return False
		text = text.strip()
		chosen = dict(choices).get(text) if text in dict(choices) else (text if re.fullmatch(r"[0-9a-fA-F]{24}", text) else "")
		return self.assort_tab.set_trader(chosen)

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
		if all(self._confirm_discard(d, l) for d, l in zip(self._docs(), ("quest", "locale", "trader assort", "quest assort"))):
			self._remember_files()
			event.accept()
		else:
			event.ignore()

	# --- importing ---------------------------------------------------------------------------
	def _workspace(self):
		return {M.QUESTS: self.quests.data, M.LOCALE: self.locale.data, M.ASSORT: self.assort.data, M.LOCKS: self.locks.data}

	def import_any(self):
		"""File > Import files...: pick any number of files of any kind; their kinds are worked out."""
		paths, _ = QFileDialog.getOpenFileNames(self, "Import files", "", JSON_FILTER)
		if paths:
			self.import_files(paths)

	def import_into(self, key):
		"""Import... in one section's menu: only files of that kind are ticked."""
		label = {k: lab for k, _t, lab, _m in KINDS}[key]
		paths, _ = QFileDialog.getOpenFileNames(self, f"Import {label} files", "", JSON_FILTER)
		if paths:
			self.import_files(paths, only=dict((k, kind) for k, _t, _l, kind in KINDS)[key])

	def import_files(self, paths, only=None):
		"""Show the import window for these files (and the .json files in these folders); apply it if accepted."""
		items = M.load_items(paths)
		if not items:
			QMessageBox.information(self, "Import files", "There are no .json files to import there.")
			return None
		if only:
			for item in items:
				if item.kind and item.kind != only:
					item.include = False
					item.error = f"This looks like a {M.KIND_LABEL[item.kind].lower()} file."
		dialog = ImportDialog(
			items, self._workspace(), self,
			traders=self.gamedata.all_traders() if self.gamedata is not None else None, trader=self.assort_tab.trader_id,
		)
		accepted = dialog.exec()
		if accepted and dialog.use_as_references:  # (kept for looking up ids; nothing is merged)
			self.add_references([str(i.path) for i in items if i.path is not None and not i.error.startswith("Couldn't")])
			return None
		if not accepted or dialog.plan is None:
			return None
		trader = dialog.chosen_trader()
		plan = self.apply_import(dialog.plan, dialog.chosen_items())
		if trader:  # (the assort that came in is this trader's: the Trader box says so, after asking if another trader is set)
			self.assort_tab.set_trader(trader)
		return plan

	def apply_import(self, plan, items):
		"""Put an import's result in the open sections, one undo step each, and say what happened."""
		included = [i for i in items if i.include and i.kind]
		label = f"Import {len(included)} file{'' if len(included) == 1 else 's'}"
		for kind in M.ORDER:
			if kind in plan.data:
				names = [item.name for item in included if item.kind == kind]
				getattr(self, KEY_OF_KIND[kind]).replace(label, plan.data[kind], note=names)  # (the note follows undo and redo)
		self.quest_sources.update(plan.sources)
		self.quest_outline.set_sources(self.quest_sources)
		self._doc_changed()
		parts = [f"{plan.adds(kind)} {M.KIND_LABEL[kind].lower()}" for kind in M.ORDER if plan.adds(kind)]
		text = ("Imported " + ", ".join(parts) + ".") if parts else "Imported."
		bare = [qid for qid in plan.sources if locale_schema.missing_keys({qid: self.quests.data[qid]}, self.locale.data)] if self.quests.data else []
		if bare:
			text += f" {len(bare)} imported quest{'' if len(bare) == 1 else 's'} {'has' if len(bare) == 1 else 'have'} no text yet: import a locale file."
		self.statusBar().showMessage(text, 15000)
		return plan

	# --- exporting ---------------------------------------------------------------------------
	def export_quests(self):
		"""Write the selected quests (and, if wanted, their text, trader offers and locks) as files of their own."""
		ids = self.quest_outline.selected_quest_ids()
		if not ids:
			QMessageBox.information(self, "Export quests", "Select one or more quests in the outline first (Ctrl-click to pick several).")
			return None
		result = export_selection(ids, self.quests.data, self.locale.data, self.assort.data, self.locks.data)
		names = [q.get("QuestName") or qid for qid, q in result.quests.items()]
		folder = str(self.quests.path.parent) if self.quests.path else ""
		dialog = ExportDialog(names, result, folder, self)
		if not dialog.exec():
			return None
		data = {"quests": result.quests, "locale": result.locale, "assort": result.assort, "locks": result.locks}
		written = []
		try:
			for kind, path in dialog.paths().items():
				jsonio.write_json(path, data[kind])
				written.append(Path(path).name)
		except OSError as e:
			QMessageBox.warning(self, "Export quests", f"A file could not be written.\n\n{e}")
			return None
		self.statusBar().showMessage(f"Exported {len(result.quests)} quest{'' if len(result.quests) == 1 else 's'} to {', '.join(written)}.", 12000)
		return written

	@staticmethod
	def _droppable(mime):
		from pathlib import Path as _Path

		return mime.hasUrls() and any(
			u.isLocalFile() and (u.toLocalFile().lower().endswith(".json") or _Path(u.toLocalFile()).is_dir()) for u in mime.urls()
		)

	def dragEnterEvent(self, event):
		if self._droppable(event.mimeData()):
			event.acceptProposedAction()

	def dragMoveEvent(self, event):
		if self._droppable(event.mimeData()):
			event.acceptProposedAction()

	def dropEvent(self, event):
		paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
		event.acceptProposedAction()
		QTimer.singleShot(0, lambda: self.import_files(paths))  # (so the drop finishes before the window opens)

	# --- settings, about, updates -----------------------------------------------------------
	def show_settings(self):
		before = {k: getattr(self.settings, k) for k in ("version_file", "version_url", "project_url")}
		if dialogs.SettingsDialog(self.settings, self.gamedata, self).exec():
			if before != {k: getattr(self.settings, k) for k in before}:
				self.update_status = updates.pending_status(self.settings)
				self.start_update_check()
			self.quest_outline.apply_settings()
			self.apply_debug_option()
			self.explorer_tab.browse.refresh()
			self.locale_tab.refresh()
			self.lookup_tab.view.refresh()

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
