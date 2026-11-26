"""The Zones tab: the quest zones on a 3D view of a map, to look at the game's zones and make and change your own.

Your zones are in one quest zone file (WTT-CommonLib's CustomQuestZones: a list of entries), held as a
core.documents.Document so every change can be undone. The game's zones (from the imported maps), the zones in the
reference files and any other zone files given are shown too, but never changed: "Copy as a new zone" puts a copy in
your file. Each of your zones is checked as it changes (maps.zones.check_zone: its kind, overlaps, and whether a player
can reach it from the floor), and the spots the floor check looked at are drawn under it.

Item spawns work the same way, on the "Item spawns" page beside the zones: your spawns are in one item spawn file
(WTT-CommonLib's CustomLootspawns: {map name: [spawn points]}, see maps.spawns), its own Document; the spawns in the
item spawn files among the references are shown, read only. A spawn is one item at a point, drawn as a small box with
a dot (a pin) and named by its item; it is moved and turned like a zone, and has no size.

The layout is ui/designer/zones_tab.ui; the 3D view is ui/view3d/view.py, and the height slider beside it (to hide
what is above a storey) ui/view3d/cut_slider.py. The maps are read when the tab is first
shown (and a map's floor map and walls when it is first shown, with ui/view3d/loading_panel.py saying how far along), and can be imported again (after a game update, or from another game folder): a notice above the view says when
they aren't from the game as it is now. The same tab is the window of `python -m cli zones edit`.
"""

import copy
import dataclasses
import html
import logging
import uuid
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QCursor, QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QFileDialog, QListWidgetItem, QMainWindow, QMenu, QMessageBox, QTreeWidgetItem, QWidget

from core import jsonio, lookup
from core.documents import Document
from maps import buildings, places
from maps import geometry as G
from maps import mapdata as M
from maps import spawns as S
from maps import zones as Z
from maps.triangles import Triangles
from ui.compiled.ui_zones_tab import Ui_ZonesForm
from ui.view3d import handles as H
from ui.view3d.cut_slider import STOREY_VIEW, CutSlider
from ui.view3d.loading_panel import LoadingPanel
from ui.view3d.view import GAME, MINE, REFERENCE, MapView, ViewZone

log = logging.getLogger(__name__)

BASE, OWN = "base", "mine"  # the first part of a zone's key: (BASE, index in self.base) or (OWN, index in the file)
OTHER_SPAWN, MY_SPAWN = "spawn", "my spawn"  # ... of a spawn's: (OTHER_SPAWN, index in self.other_spawns) or (MY_SPAWN, map name, index)
ZONE, SPAWN = "zone", "spawn"  # what a click on the floor places
SPAWN_HANDLES = (H.LIFT, H.TURN)  # (a spawn is moved by dragging it, and has no size)
SPAWN_FILTER = "Item spawn files (*.json);;All files (*)"
ZONE_HINT = "Drag the zone to move it. Its handles size it (squares), lift it (arrow) and turn it (circle); Shift snaps. Left-drag turns the view, right-drag moves it, the wheel zooms."
SPAWN_HINT = "Drag the spawn (or its dot) to move it. Its handles lift it (arrow) and turn it (circle); Shift snaps. Left-drag turns the view, right-drag moves it, the wheel zooms."
NEW_SIZE = (4.0, 3.0, 4.0)  # metres: a new zone's width, height and depth
FIRST_MAP = "factory4_day"  # shown first when nothing says which: Factory (day), small and quick to read
OPEN_OWNER = "zones tab"  # the name the zone file open here is left out of the references under (core.references.References.set_open)
KEEP_WALLS = 3  # maps whose walls are kept in memory (the last ones shown); the others' are read again if gone back to
JSON_FILTER = "Quest zone files (*.json);;All files (*)"
KINDS = list(Z.CUSTOM_TYPE)  # visit, placeitem, trigger, flarezone, salvage, as the kind box lists them
NOTICE_STYLE = "QLabel { background: rgba(230, 160, 40, 45); border: 1px solid rgba(200, 130, 20, 160); border-radius: 3px; padding: 4px 8px; }"


class _ImportSignals(QObject):
	progress = Signal(str)
	finished = Signal(object)  # the summary, or an Exception


class ImportWorker(QRunnable):
	"""Imports the game's maps in the background (maps.mapdata.import_maps)."""

	def __init__(self, game_dir, out_dir):
		super().__init__()
		self.setAutoDelete(False)
		self.game_dir, self.out_dir = game_dir, out_dir
		self.signals = _ImportSignals()

	def run(self):
		from maps.mapdata import import_maps

		try:
			result = import_maps(self.game_dir, self.out_dir, progress=self.signals.progress.emit)
		except Exception as e:  # (said in the tab: a wrong folder, a game update the reader doesn't know)
			log.exception("Map import failed")
			result = e
		try:
			self.signals.finished.emit(result)
		except RuntimeError:  # (the tab was closed meanwhile)
			pass


class ZonesTab(QWidget, Ui_ZonesForm):
	"""settings: the app's settings (or None). references: core.references.References, whose zone files are shown.
	map_names: {location id: name to show}. maps_folder: where the imported maps are (default: maps.mapdata's).
	zone_files: more zone files to show (not to change). game_dir: the game folder to compare the maps with and import
	them from (default: the game your SPT database is in, else the one the maps came from). gamedata: the game's data
	(core.gamedata.GameData: the items a spawn can be, and their names), or None. spawn_files: more item spawn files to
	show (not to change). pick_item: a function giving the id of an item the user chooses (or None); by default a
	search window over gamedata's items and the references'."""

	zones_changed = Signal()  # your zone file changed (the quests' checks may want to look again)
	spawns_changed = Signal()  # your item spawn file changed

	def __init__(self, settings=None, references=None, map_names=None, maps_folder=None, zone_files=(), game_dir=None, parent=None, gamedata=None, spawn_files=()):
		super().__init__(parent)
		self.setupUi(self)
		self.settings, self.references, self.gamedata = settings, references, gamedata
		self.map_names = dict(map_names or {})
		self.maps_folder = maps_folder
		self.zone_files = [Path(p) for p in zone_files]
		self.spawn_files = [Path(p) for p in spawn_files]
		self.game_dir = Path(game_dir) if game_dir else None
		self.versionLabel.setStyleSheet(NOTICE_STYLE)
		self.versionLabel.hide()
		self.doc = Document([])
		self.doc.on_change(self._doc_changed)
		self.spawn_doc = Document({})
		self.spawn_doc.on_change(self._spawn_doc_changed)
		self.my_spawns = {}  # {(map name, index): Spawn} of your spawn file's entries that can be read
		self.broken_spawns = {}  # {(map name, index): why it can't be read}
		self.other_spawns = []  # the spawns of the reference files and spawn_files, keyed (OTHER_SPAWN, i)
		self.pick_item = self._pick_item
		self._spawn_item = None  # the item the next spawn placed gets (the one chosen or placed last)
		self._placing = ZONE
		self._facts = None  # maps.spawns.ItemFacts, made when first needed
		self._item_rows = None
		self.view = MapView()
		self.loadingPanel = LoadingPanel(self.view)
		self.cutSlider = CutSlider()
		self.viewLayout.addWidget(self.view, 1)
		self.viewLayout.addWidget(self.cutSlider)
		self.splitter.setStretchFactor(1, 1)
		self.splitter.setSizes([290, 860, 340])
		self.kindBox.addItems([Z.CUSTOM_TYPE[k] for k in KINDS])
		self.index = None  # maps.zones.ZoneIndex of everything (the game's, the reference files', yours): for the checks
		self.base = []  # the zones that aren't yours, keyed (BASE, i)
		self.mine = {}  # {index in the file: Zone} of your entries that can be read
		self.broken = {}  # {index in the file: why it can't be read}
		self.location = None
		self.start_map = None  # the map to show first (else the map of your first zone, else FIRST_MAP)
		self.selected = None  # the key of the zone selected
		self.building = None  # what maps.buildings found at the last "Building here"
		self._floors = {}  # {location: Triangles} of the floor map (the walls are the map's own: MapData.walls)
		self._cameras = {}  # {location: the view's camera there}, so going back to a map looks where it looked
		self._recent = []  # the maps shown, the last first (only the first KEEP_WALLS keep their walls in memory)
		self._loaded = False
		self._load_pending = False  # (shown, and about to load: see _first_load)
		self._loading = False  # (a map is being read: see _read_map)
		self._filling = False
		self._worker = None
		self._new_kind = Z.VISIT
		self.hintLabel.setText(ZONE_HINT)
		self._connect()
		self._doc_changed()
		self._spawn_doc_changed()

	def _connect(self):
		v = self.view
		v.zone_clicked.connect(lambda key: self.select(key))
		v.box_changing.connect(self._box_changing)
		v.box_edited.connect(self._box_edited)
		v.place_requested.connect(self._place_requested)
		v.placing_changed.connect(self._placing_changed)
		v.delete_requested.connect(self.delete_selected)
		v.top_down_changed.connect(self._top_down_changed)
		v.view_moved.connect(lambda _target: self._update_storeys())
		self.mapBox.currentIndexChanged.connect(lambda _i: self.set_map(self.mapBox.currentData()))
		self.search.returnPressed.connect(lambda: self.find(choose=True))
		self.topDownButton.toggled.connect(self.view.set_top_down)
		self.wholeMapButton.clicked.connect(lambda _c=False: self.view.look_at_everything())
		self.importButton.clicked.connect(lambda _c=False: self.import_maps())
		self.versionLabel.linkActivated.connect(self._notice_link)
		for box in (self.floorBox, self.wallsBox, self.gameZonesBox, self.referenceZonesBox, self.spawnsBox, self.areasBox, self.labelsBox):
			box.toggled.connect(lambda _checked: self._layers_changed())
		self.cutSlider.cut_changed.connect(self.view.set_cut)
		self.buildingButton.clicked.connect(lambda _c=False: self.find_building())
		self.storeyBox.currentIndexChanged.connect(self._storey_chosen)
		self.zoneFilter.textChanged.connect(lambda _t: self._fill_list())
		self.zoneList.currentItemChanged.connect(self._list_selected)
		self.newFileButton.clicked.connect(lambda _c=False: self.new_file())
		self.openFileButton.clicked.connect(lambda _c=False: self.open_file())
		self.saveFileButton.clicked.connect(lambda _c=False: self.save_file())
		self.saveAsFileButton.clicked.connect(lambda _c=False: self.save_file(as_new=True))
		self.placeButton.toggled.connect(self._place_toggled)
		self.idEdit.textEdited.connect(lambda _t: self._form_edited("id"))
		self.nameEdit.textEdited.connect(lambda _t: self._form_edited("name"))
		self.kindBox.currentIndexChanged.connect(lambda _i: self._form_edited("kind"))
		for name in ("x", "y", "z", "width", "height", "depth", "yaw"):
			getattr(self, f"{name}Spin").valueChanged.connect(lambda _v, n=name: self._form_edited(n))
		self.floorButton.clicked.connect(lambda _c=False: self.sit_on_floor())
		self.slopeButton.clicked.connect(lambda _c=False: self.cover_slope())
		self.lookButton.clicked.connect(lambda _c=False: self._look_at_selected())
		self.copyButton.clicked.connect(lambda _c=False: self.copy_selected())
		self.deleteButton.clicked.connect(lambda _c=False: self.delete_selected())
		self.editTabs.currentChanged.connect(lambda _i: self.hintLabel.setText(SPAWN_HINT if self.editTabs.currentWidget() is self.spawnsPage else ZONE_HINT))
		self.newSpawnFileButton.clicked.connect(lambda _c=False: self.new_spawn_file())
		self.openSpawnFileButton.clicked.connect(lambda _c=False: self.open_spawn_file())
		self.saveSpawnFileButton.clicked.connect(lambda _c=False: self.save_spawn_file())
		self.saveAsSpawnFileButton.clicked.connect(lambda _c=False: self.save_spawn_file(as_new=True))
		self.placeSpawnButton.toggled.connect(self._place_spawn_toggled)
		self.chooseItemButton.clicked.connect(lambda _c=False: self.choose_item())
		self.spawnIdEdit.textEdited.connect(lambda _t: self._spawn_form_edited("id"))
		self.spawnCountSpin.valueChanged.connect(lambda _v: self._spawn_form_edited("count"))
		for name in ("x", "y", "z", "yaw"):
			getattr(self, f"spawn{name.capitalize()}Spin").valueChanged.connect(lambda _v, n=name: self._spawn_form_edited(n))
		self.spawnChanceSpin.valueChanged.connect(lambda _v: self._spawn_form_edited("chance"))
		self.spawnAlwaysBox.toggled.connect(lambda _c: self._spawn_form_edited("always"))
		self.spawnGravityBox.toggled.connect(lambda _c: self._spawn_form_edited("gravity"))
		self.spawnRandomBox.toggled.connect(lambda _c: self._spawn_form_edited("random"))
		self.spawnFloorButton.clicked.connect(lambda _c=False: self.put_spawn_on_floor())
		self.spawnLookButton.clicked.connect(lambda _c=False: self._look_at_selected())
		self.copySpawnButton.clicked.connect(lambda _c=False: self.copy_selected())
		self.deleteSpawnButton.clicked.connect(lambda _c=False: self.delete_selected())

	# --- loading ----------------------------------------------------------------------------------
	def showEvent(self, event):
		super().showEvent(event)
		if not self._loaded and not self._load_pending:
			self._load_pending = True
			QTimer.singleShot(0, self._first_load)

	def _first_load(self):
		"""The first load, just after the tab is first shown: from its show event, the loading panel would never appear,
		as the window doesn't draw the tab until the show is over. The tab is drawn first, then the maps read."""
		self._load_pending = False
		if self._loaded or not self.isVisible():  # (shown and hidden again at once: the next show loads)
			return
		self.repaint()
		self.load()

	def load(self):
		"""Read the imported maps and the zone files (the first time the tab is shown, and after an import)."""
		self._loaded = True
		QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))
		try:
			self._read_zones()
			current = self.location
			if current is not None:  # (imported again: the view looks where it looked)
				self._cameras[current] = copy.copy(self.view.camera)
			self.mapBox.blockSignals(True)
			self.mapBox.clear()
			for key in self.index.game_maps:
				self.mapBox.addItem(self.map_names.get(key, key), key)
			self.mapBox.blockSignals(False)
			self._import_button()
			self.check_maps_version()
			if not self.index.game_maps:
				self.view.message = (
					"No maps have been imported yet.\n\nClick \"Import the game's maps...\" above and choose the game's folder (the one "
					"with EscapeFromTarkov_Data). It takes a few minutes; nothing in the game is changed."
				)
				self.view.update()
				return
			self.view.message = ""
			keys = self.index.game_maps
			self.location = None
			wanted = current if current in keys else self._first_map(keys)
			self.mapBox.setCurrentIndex(keys.index(wanted))
			self.set_map(wanted)
		finally:
			QApplication.restoreOverrideCursor()

	def _first_map(self, keys):
		"""start_map, else the map of your first zone (or spawn), else FIRST_MAP, else the first imported."""
		if self.start_map in keys:
			return self.start_map
		for thing in [*self.mine.values(), *self.my_spawns.values()]:
			if thing.location in keys:
				return thing.location
		return FIRST_MAP if FIRST_MAP in keys else keys[0]

	def _read_zones(self):
		self.index = Z.ZoneIndex(self.maps_folder)
		for path in self.zone_files:
			try:
				self.index.add_file(path)
			except (OSError, ValueError) as e:
				self.statusLabel.setText(f"Couldn't read the zone file {path}: {e}")
		if self.references is not None:
			named = {p.name for p in self.zone_files}
			for records, name in self.references.zone_files():
				if name not in named:
					self.index.add_records(records, name)
		self.base = list(self.index.zones)
		self._mine_changed()
		self._read_other_spawns()

	def _read_other_spawns(self):
		"""The spawns of spawn_files and of the item spawn files among the references."""
		self.other_spawns = []
		for path in self.spawn_files:
			try:
				data = jsonio.read_json(path)
			except (OSError, ValueError) as e:
				self.statusLabel.setText(f"Couldn't read the item spawn file {path}: {e}")
				continue
			self.other_spawns += S.read_spawns(data, path.name, S.file_forced(path) is not False)[0]
		if self.references is not None:
			named = {p.name for p in self.spawn_files}
			for data, name, forced in self.references.spawn_files():
				if name not in named:
					self.other_spawns += S.read_spawns(data, name, forced)[0]

	def references_changed(self):
		"""The reference files changed: their zones and spawns are read again (and the items they know)."""
		self._facts = self._item_rows = None
		if self._loaded:
			self._read_zones()
			self._refresh()

	def set_map(self, location):
		if not location or location == self.location or self.index is None:
			return
		if self.location is not None:
			self._cameras[self.location] = copy.copy(self.view.camera)
		self.location = location
		self._recent = [location] + [key for key in self._recent if key != location]
		for old in self._recent[KEEP_WALLS:]:  # (before this map's are read, so no more than KEEP_WALLS are held at once)
			self.index.map(old).forget_walls()
		self.building = None
		self.view.set_outlines([])
		self._fill_storeys()
		QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))
		try:
			mapdata = self.index.map(location)
			self._read_map(location, mapdata)
			floor, walls = self._floors[location], mapdata.walls
			self.view.set_floor(floor)
			self.view.set_walls(walls)
			self.wallsBox.setEnabled(walls is not None)
			self.wallsBox.setToolTip(
				"The walls, floors and stairs players bump into" if walls is not None
				else "The walls of this map haven't been imported: import the maps again to see them"
			)
			self.view.set_areas([(a["name"], G.Box([(a["min"][i] + a["max"][i]) / 2 for i in range(3)], [a["max"][i] - a["min"][i] for i in range(3)])) for a in mapdata.areas])
			low, high = floor.floor_range()  # (not the rooftops high above everything else: see Triangles.floor_range)
			self.cutSlider.set_range(low, high + STOREY_VIEW)
			self.cutSlider.set_value(None)
		finally:
			QApplication.restoreOverrideCursor()
		if location in self._cameras:
			self.view.camera = self._cameras[location]
			self.view.keep_on_map()
			self.topDownButton.setChecked(self.view.camera.top_down)
		else:
			self.view.camera.top_down = self.topDownButton.isChecked()
			self.view.look_at_everything()
		self._update_storeys()
		thing = self._zone(self.selected) or self._spawn(self.selected)
		if thing is not None and thing.location != location:
			self.selected = None
		self._refresh()

	def _read_map(self, location, mapdata):
		"""Read what showing the map needs and isn't in memory yet (MapData.prepare: the floor map, the walls and the
		floors' lookup), with the loading panel over the view saying how far along it is (it only shows if there is
		something to read). The window's paint events are handled meanwhile, so the view's own signals wait."""
		self._loading = True
		self.loadingPanel.start(f"Loading {self.map_names.get(location, location)}")
		try:
			mapdata.prepare(self.loadingPanel.say)
			if location not in self._floors:
				self._floors[location] = Triangles.from_navmesh(mapdata.navmesh)
		finally:
			self._loading = False
			self.loadingPanel.finish()

	# --- your zone file -----------------------------------------------------------------------------
	def set_document(self, doc):
		"""Edit this zone file (a Document holding a list of entries)."""
		self.doc = doc
		doc.on_change(self._doc_changed)
		self.selected = None
		self._doc_changed()

	def new_file(self):
		if self._confirm_discard():
			self.set_document(Document([]))

	def open_file(self, path=None):
		if path is None:
			if not self._confirm_discard():
				return
			path, _ = QFileDialog.getOpenFileName(self, "Open a quest zone file", str(self.doc.path or ""), JSON_FILTER)
			if not path:
				return
		try:
			doc = Document.open(path)
		except (OSError, ValueError) as e:
			QMessageBox.warning(self, "Open", f"Couldn't read {path}: {e}")
			return
		if not isinstance(doc.data, list) or (doc.data and not Z.is_zone_file(doc.data)):
			QMessageBox.warning(self, "Open", f"{Path(path).name} isn't a quest zone file (a list of zones with ZoneId and ZoneType).")
			return
		self.set_document(doc)
		maps = [z.location for z in self.mine.values() if self.index is not None and z.location in self.index.game_maps]
		if maps and maps[0] != self.location:
			self.mapBox.setCurrentIndex(self.index.game_maps.index(maps[0]))

	def save_file(self, as_new=False):
		path = self.doc.path
		if as_new or path is None:
			path, _ = QFileDialog.getSaveFileName(self, "Save the quest zone file", str(self.doc.path or "zones.json"), JSON_FILTER)
			if not path:
				return False
		try:
			self.doc.save(path)
		except OSError as e:
			QMessageBox.warning(self, "Save", f"Couldn't save {path}: {e}")
			return False
		self.statusLabel.setText(f"Saved {path}.")
		return True

	def _confirm_discard(self):
		if not self.doc.dirty:
			return True
		answer = QMessageBox.question(
			self, "Zones", f"Save the changes to the zone file {self.doc.name}?",
			QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
		)
		if answer == QMessageBox.StandardButton.Save:
			return self.save_file()
		return answer == QMessageBox.StandardButton.Discard

	def _open_changed(self):
		"""Tell the references which files are open here: a zone or spawn file that is also a reference is left out of
		them while it is open (its zones and spawns are the ones being edited). True if that changed what they hold."""
		return self.references is not None and self.references.set_open(OPEN_OWNER, [self.doc.path, getattr(self, "spawn_doc", self.doc).path])

	def _doc_changed(self, _doc=None):
		if self._open_changed() and self._loaded:
			self._read_zones()
		else:
			self._mine_changed()
		dirty = "*" if self.doc.dirty else ""
		count = len(self.doc.data) if isinstance(self.doc.data, list) else 0
		self.fileLabel.setText(f"Zone file: {self.doc.name}{dirty} ({count} zone{'' if count == 1 else 's'})")
		if self.selected and self._zone(self.selected) is None:
			self.selected = None
		self._refresh()
		self.zones_changed.emit()

	def _mine_changed(self):
		"""Read your entries again (after any change), and put them in the index the checks use."""
		self.mine, self.broken = {}, {}
		for i, record in enumerate(self.doc.data if isinstance(self.doc.data, list) else []):
			try:
				self.mine[i] = Z.zone_from_record(record, self.doc.name)
			except ValueError as e:
				self.broken[i] = str(e)
		if self.index is not None:
			self.index.zones = self.base + list(self.mine.values())

	# --- your item spawn file ---------------------------------------------------------------------------
	def set_spawn_document(self, doc):
		"""Edit this item spawn file (a Document holding {map name: [spawn points]})."""
		self.spawn_doc = doc
		doc.on_change(self._spawn_doc_changed)
		if self._is_spawn(self.selected):
			self.selected = None
		self._spawn_doc_changed()

	def new_spawn_file(self):
		if self._confirm_discard_spawns():
			self.set_spawn_document(Document({}))

	def open_spawn_file(self, path=None):
		if path is None:
			if not self._confirm_discard_spawns():
				return
			path, _ = QFileDialog.getOpenFileName(self, "Open an item spawn file", str(self.spawn_doc.path or ""), SPAWN_FILTER)
			if not path:
				return
		try:
			doc = Document.open(path)
		except (OSError, ValueError) as e:
			QMessageBox.warning(self, "Open", f"Couldn't read {path}: {e}")
			return
		if not isinstance(doc.data, dict) or (doc.data and not S.is_spawn_file(doc.data)):
			QMessageBox.warning(self, "Open", f"{Path(path).name} isn't an item spawn file (WTT-CommonLib's CustomLootspawns: {{map name: [spawn points]}}).")
			return
		self.set_spawn_document(doc)
		self.editTabs.setCurrentWidget(self.spawnsPage)
		maps = [s.location for s in self.my_spawns.values() if self.index is not None and s.location in self.index.game_maps]
		if maps and maps[0] != self.location:
			self.mapBox.setCurrentIndex(self.index.game_maps.index(maps[0]))

	def save_spawn_file(self, as_new=False):
		path = self.spawn_doc.path
		if as_new or path is None:
			path, _ = QFileDialog.getSaveFileName(self, "Save the item spawn file", str(self.spawn_doc.path or "item_spawns.json"), SPAWN_FILTER)
			if not path:
				return False
		try:
			self.spawn_doc.save(path)
		except OSError as e:
			QMessageBox.warning(self, "Save", f"Couldn't save {path}: {e}")
			return False
		self.statusLabel.setText(f"Saved {path}.")
		return True

	def _confirm_discard_spawns(self):
		if not self.spawn_doc.dirty:
			return True
		answer = QMessageBox.question(
			self, "Item spawns", f"Save the changes to the item spawn file {self.spawn_doc.name}?",
			QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
		)
		if answer == QMessageBox.StandardButton.Save:
			return self.save_spawn_file()
		return answer == QMessageBox.StandardButton.Discard

	def spawns_forced(self):
		"""True if your spawn file's spawns are forced ones (they spawn every raid): its folder says, else its name;
		a new file's are, as quest items are."""
		return S.file_forced(self.spawn_doc.path) is not False

	def _spawn_doc_changed(self, _doc=None):
		if self._open_changed() and self._loaded:
			self._read_zones()
		self._my_spawns_changed()
		data = self.spawn_doc.data if isinstance(self.spawn_doc.data, dict) else {}
		count = sum(len(entries) for entries in data.values() if isinstance(entries, list))
		forced = S.file_forced(self.spawn_doc.path)
		folders = {p.name.lower() for p in self.spawn_doc.path.parents} if self.spawn_doc.path else set()
		if self.spawn_doc.path is not None and not folders & {S.FORCED_FOLDER.lower(), S.LOOSE_FOLDER.lower()}:
			what = f"WTT reads only the files in db/CustomLootspawns/{S.FORCED_FOLDER} and {S.LOOSE_FOLDER}"
		else:
			what = "forced: they spawn every raid" if forced is not False else "loose loot"
		dirty = "*" if self.spawn_doc.dirty else ""
		self.spawnFileLabel.setText(f"Spawn file: {self.spawn_doc.name}{dirty} ({count} spawn{'' if count == 1 else 's'}; {what})")
		if self._is_spawn(self.selected) and self._spawn(self.selected) is None:
			self.selected = None
		self._refresh()
		self.spawns_changed.emit()

	def _my_spawns_changed(self):
		"""Read your spawn file's entries again (after any change)."""
		found, self.broken_spawns = S.read_spawns(self.spawn_doc.data, self.spawn_doc.name, self.spawns_forced())
		self.my_spawns = {(s.map_name, s.index): s for s in found}

	def facts(self):
		"""What the spawn checks know of items (maps.spawns.ItemFacts)."""
		if self._facts is None:
			self._facts = S.ItemFacts(self.gamedata, self.references.custom_items() if self.references is not None else None)
		return self._facts

	def item_name(self, tpl):
		return self.facts().name(tpl)

	def _pick_item(self):
		"""Ask for an item: the game's, or one of the reference files' (a search window). Its id, or None."""
		from ui.lookup_view import PickerDialog

		if self._item_rows is None:
			self._item_rows = lookup.build_rows(self.gamedata, kinds=(lookup.ITEM, lookup.REF_ITEM), references=self.references) if self.gamedata is not None else []
		if not self._item_rows:
			QMessageBox.information(self, "Item spawns", "No items are known: choose your SPT database in the settings.")
			return None
		dialog = PickerDialog(self._item_rows, (lookup.ITEM, lookup.REF_ITEM), "Find an item", False, self.settings, self)
		return dialog.ids[0] if dialog.exec() and dialog.ids else None

	# --- what is shown ----------------------------------------------------------------------------------
	def _zone(self, key):
		if key is None or key[0] not in (BASE, OWN):
			return None
		kind, i = key
		if kind == OWN:
			return self.mine.get(i)
		return self.base[i] if 0 <= i < len(self.base) else None

	@staticmethod
	def _is_spawn(key):
		return key is not None and key[0] in (OTHER_SPAWN, MY_SPAWN)

	def _spawn(self, key):
		if not self._is_spawn(key):
			return None
		if key[0] == MY_SPAWN:
			return self.my_spawns.get((key[1], key[2]))
		i = key[1]
		return self.other_spawns[i] if 0 <= i < len(self.other_spawns) else None

	def _shown_spawns(self):
		"""[(key, Spawn, style)] of the spawns on this map that are shown."""
		if not self.spawnsBox.isChecked():
			return []
		found = [((OTHER_SPAWN, i), s, REFERENCE) for i, s in enumerate(self.other_spawns) if s.location == self.location]
		return found + [((MY_SPAWN, *where), s, MINE) for where, s in self.my_spawns.items() if s.location == self.location]

	def _check_spawn(self, spawn):
		"""(errors, warnings, notes) of a spawn (maps.spawns.check_spawn), against every other spawn known."""
		floors = self.index.map(spawn.location).floors if self.index is not None and spawn.location in self.index.game_maps else None
		return S.check_spawn(spawn, self.other_spawns + list(self.my_spawns.values()), floors, self.facts())

	def _shown(self):
		"""[(key, Zone, style)] of the zones on this map that are shown."""
		found = []
		for i, zone in enumerate(self.base):
			if zone.location != self.location:
				continue
			if zone.source == Z.GAME:
				if self.gameZonesBox.isChecked():
					found.append(((BASE, i), zone, GAME))
			elif self.referenceZonesBox.isChecked():
				found.append(((BASE, i), zone, REFERENCE))
		found += [((OWN, i), zone, MINE) for i, zone in self.mine.items() if zone.location == self.location]
		return found

	def _refresh(self):
		self._filling = True
		try:
			self.view.set_zones(
				[(ViewZone(key, zone.id, zone.kind, zone.box), style) for key, zone, style in self._shown()]
				+ [(ViewZone(key, self.item_name(s.item), S.SPAWN, s.box, pin=True), style) for key, s, style in self._shown_spawns()]
			)
			self._fill_list()
			self._show_selected()
		finally:
			self._filling = False

	def _layers_changed(self):
		v = self.view
		v.show_floor, v.show_walls = self.floorBox.isChecked(), self.wallsBox.isChecked()
		v.show_areas, v.show_labels = self.areasBox.isChecked(), self.labelsBox.isChecked()
		self._refresh()

	def _update_storeys(self):
		"""Tick the storeys at the middle of the view on the height slider (it stops above them)."""
		if self._loading:  # (the view moved just before; set_map ticks them when the map is read)
			return
		if self.index is None or self.location is None:
			self.cutSlider.set_storeys([])
			return
		x, _y, z = self.view.camera.target
		self.cutSlider.set_storeys(self.index.map(self.location).floors.storeys_at(x, z))

	def _top_down_changed(self, top_down):
		self.topDownButton.blockSignals(True)
		self.topDownButton.setChecked(top_down)
		self.topDownButton.blockSignals(False)

	def _fill_list(self):
		self.zoneList.blockSignals(True)
		self.zoneList.setSortingEnabled(False)
		self.zoneList.clear()
		words = self.zoneFilter.text().lower().split()
		current = None
		for key, zone, style in self._shown():
			if words and not all(w in f"{zone.id} {zone.name} {zone.kind}".lower() for w in words):
				continue
			source = "your file" if style == MINE else "the game" if style == GAME else zone.source
			item = QTreeWidgetItem([zone.id, zone.kind, source])
			item.setData(0, Qt.ItemDataRole.UserRole, key)
			item.setToolTip(0, zone.summary())
			if style == MINE:
				font = item.font(0)
				font.setBold(True)
				item.setFont(0, font)
				errors, warnings = Z.check_zone(zone, self.index) if self.index is not None else ([], [])
				if errors or warnings:
					item.setForeground(0, QBrush(QColor(220, 50, 40) if errors else QColor(210, 130, 0)))
			self.zoneList.addTopLevelItem(item)
			if key == self.selected:
				current = item
		for i, why in self.broken.items():
			item = QTreeWidgetItem([f"(entry {i + 1})", "?", "your file"])
			item.setToolTip(0, why)
			item.setForeground(0, QBrush(QColor(220, 50, 40)))
			self.zoneList.addTopLevelItem(item)
		for key, spawn, style in self._shown_spawns():
			name = self.item_name(spawn.item) or "(no item)"
			if words and not all(w in f"{name} {spawn.id} item spawn".lower() for w in words):
				continue
			source = "your spawn file" if style == MINE else spawn.source
			item = QTreeWidgetItem([name, "item spawn" if spawn.always else "item spawn (chance)", source])
			item.setData(0, Qt.ItemDataRole.UserRole, key)
			item.setToolTip(0, spawn.summary(name))
			if style == MINE:
				font = item.font(0)
				font.setBold(True)
				item.setFont(0, font)
				errors, warnings, _notes = self._check_spawn(spawn)
				if errors or warnings:
					item.setForeground(0, QBrush(QColor(220, 50, 40) if errors else QColor(210, 130, 0)))
			self.zoneList.addTopLevelItem(item)
			if key == self.selected:
				current = item
		for (map_name, i), why in self.broken_spawns.items():
			item = QTreeWidgetItem([f"({map_name} spawn {i + 1})", "?", "your spawn file"])
			item.setToolTip(0, why)
			item.setForeground(0, QBrush(QColor(220, 50, 40)))
			self.zoneList.addTopLevelItem(item)
		self.zoneList.setSortingEnabled(True)
		self.zoneList.sortByColumn(0, Qt.SortOrder.AscendingOrder)
		if current is not None:
			self.zoneList.setCurrentItem(current)
			self.zoneList.scrollToItem(current)
		for column in range(3):
			self.zoneList.resizeColumnToContents(column)
		self.zoneList.blockSignals(False)

	def _list_selected(self, item, _previous):
		if item is not None and not self._filling:
			key = item.data(0, Qt.ItemDataRole.UserRole)
			if key is not None:
				self.select(tuple(key), look=True)

	# --- selecting ----------------------------------------------------------------------------------------
	def select(self, key, look=False):
		self.selected = tuple(key) if key is not None else None
		self._filling = True
		try:
			for i in range(self.zoneList.topLevelItemCount()):
				item = self.zoneList.topLevelItem(i)
				if item.data(0, Qt.ItemDataRole.UserRole) == self.selected:
					self.zoneList.blockSignals(True)
					self.zoneList.setCurrentItem(item)
					self.zoneList.blockSignals(False)
					self.zoneList.scrollToItem(item)
					break
			else:
				self.zoneList.clearSelection()
			self._show_selected()
		finally:
			self._filling = False
		box = self._box_of(self.selected)
		if look and box is not None:
			if not _in_view(self.view, box):
				self.view.look_at_box(box)
		if self._is_spawn(self.selected):
			self.editTabs.setCurrentWidget(self.spawnsPage)
		elif self.selected is not None:
			self.editTabs.setCurrentWidget(self.zonesPage)

	def _box_of(self, key):
		"""The box to bring into view for a zone or spawn (a spawn's is small: a few metres round it)."""
		zone, spawn = self._zone(key), self._spawn(key)
		if spawn is not None:
			return G.Box(spawn.position, NEW_SIZE)
		return zone.box if zone is not None else None

	def _editable(self):
		"""True if the selected one is one of your zones."""
		return self.selected is not None and self.selected[0] == OWN and self.selected[1] in self.mine

	def _spawn_editable(self):
		"""True if the selected one is one of your spawns."""
		return self.selected is not None and self.selected[0] == MY_SPAWN and tuple(self.selected[1:]) in self.my_spawns

	def _show_selected(self):
		zone, spawn = self._zone(self.selected), self._spawn(self.selected)
		if spawn is not None:
			self.view.set_selected(self.selected, spawn.box, S.SPAWN, self._spawn_editable(), handles=SPAWN_HANDLES)
		else:
			self.view.set_selected(self.selected, zone.box if zone else None, zone.kind if zone else "", self._editable())
		was = self._filling
		self._filling = True
		try:
			self._fill_form(zone, self._editable())
			self._fill_spawn_form(spawn, self._spawn_editable())
		finally:
			self._filling = was
		if spawn is not None:
			self._show_spawn_checks(spawn)
		else:
			self._show_checks(zone)

	def _fill_form(self, zone, editable):
		self.zoneGroup.setEnabled(zone is not None)
		self.zoneGroup.setTitle("Zone" if zone is None else ("Your zone" if editable else f"Zone of {'the game' if zone.source == Z.GAME else zone.source} (read only)"))
		for widget in (self.idEdit, self.nameEdit, self.kindBox, self.xSpin, self.ySpin, self.zSpin, self.widthSpin, self.heightSpin, self.depthSpin, self.yawSpin):
			widget.setEnabled(editable)
		for button in (self.floorButton, self.slopeButton, self.deleteButton):
			button.setEnabled(editable)
		self.copyButton.setEnabled(zone is not None and not editable)
		self.lookButton.setEnabled(zone is not None)
		if zone is None:
			return
		_set_text(self.idEdit, zone.id)
		_set_text(self.nameEdit, zone.name)
		self.kindBox.setCurrentIndex(KINDS.index(zone.kind) if zone.kind in KINDS else 0)
		self._fill_box(zone.box)
		upright = G.is_upright(zone.box.rotation)
		self.yawSpin.setEnabled(editable and upright)
		self.yawSpin.setToolTip("Degrees clockwise, seen from above" if upright else "It is tilted, so it can only be turned in its file")

	def _fill_box(self, box):
		values = {"x": box.center[0], "y": box.center[1], "z": box.center[2], "width": box.size[0], "height": box.size[1], "depth": box.size[2], "yaw": G.yaw_of(box.rotation)}
		for name, value in values.items():
			spin = getattr(self, f"{name}Spin")
			if abs(spin.value() - value) > 10 ** -spin.decimals() / 2:
				spin.blockSignals(True)
				spin.setValue(value)
				spin.blockSignals(False)

	def _show_checks(self, zone, box=None):
		"""The checks of the selected zone (of its box being dragged, if box is given), and the floor spots looked at."""
		self.checksList.clear()
		self.view.samples = []
		if zone is None or self.index is None:
			self.view.update()
			return
		if box is not None:
			zone = Z.Zone(zone.id, zone.location, zone.kind, box, zone.source, zone.name, zone.active, zone.custom_class, zone.record)
		if self._editable() or box is not None:
			errors, warnings = Z.check_zone(zone, self.index)
		else:
			errors, warnings = [], []
		for text in errors:
			self._check_item(f"Error: {text}", QColor(220, 50, 40))
		for text in warnings:
			self._check_item(f"Warning: {text}", QColor(210, 130, 0))
		if self._editable() and not errors and not warnings:
			self._check_item("No problems found.", QColor(40, 160, 70))
		if not self._editable():
			self._check_item(zone.summary(), None)
		if zone.location in self.index.game_maps:
			self.view.samples = Z.reach_samples(zone.box, self.index.map(zone.location).floors)
		self.view.update()

	def _check_item(self, text, colour):
		item = QListWidgetItem(text)
		if colour is not None:
			item.setForeground(QBrush(colour))
		self.checksList.addItem(item)

	def _fill_spawn_form(self, spawn, editable):
		self.spawnGroup.setEnabled(spawn is not None)
		self.spawnGroup.setTitle("Item spawn" if spawn is None else ("Your item spawn" if editable else f"Item spawn of {spawn.source} (read only)"))
		for widget in (
			self.chooseItemButton, self.spawnCountSpin, self.spawnIdEdit, self.spawnXSpin, self.spawnYSpin, self.spawnZSpin, self.spawnYawSpin,
			self.spawnChanceSpin, self.spawnGravityBox, self.spawnRandomBox, self.spawnFloorButton, self.deleteSpawnButton,
		):
			widget.setEnabled(editable)
		self.copySpawnButton.setEnabled(spawn is not None and not editable)
		self.spawnLookButton.setEnabled(spawn is not None)
		self.spawnAlwaysBox.setEnabled(editable and spawn is not None and not spawn.forced)
		self.spawnAlwaysBox.setToolTip(
			"Its file is a forced one (in CustomSpawnpointsForced): its spawns come every raid" if spawn is not None and spawn.forced
			else "IsAlwaysSpawn: it spawns every raid. A forced file's spawns always do"
		)
		if spawn is None:
			return
		name = self.item_name(spawn.item)
		_set_text(self.spawnItemEdit, name if name and name != spawn.item else spawn.item or "(none)", start=True)
		self.spawnItemEdit.setToolTip(f"{name} ({spawn.item})" if spawn.item else "No item")
		_set_text(self.spawnIdEdit, spawn.id, start=True)
		for widget, value in (
			(self.spawnXSpin, spawn.position[0]), (self.spawnYSpin, spawn.position[1]), (self.spawnZSpin, spawn.position[2]),
			(self.spawnYawSpin, spawn.yaw), (self.spawnChanceSpin, spawn.probability), (self.spawnCountSpin, spawn.count),
		):
			_set_value(widget, value)
		for box, value in ((self.spawnAlwaysBox, spawn.always), (self.spawnGravityBox, spawn.gravity), (self.spawnRandomBox, spawn.random_rotation)):
			if box.isChecked() != value:
				box.blockSignals(True)
				box.setChecked(value)
				box.blockSignals(False)

	def _show_spawn_checks(self, spawn, box=None):
		"""The checks of the selected spawn (where it is being dragged to, if box is given)."""
		self.checksList.clear()
		self.view.samples = []
		if box is not None:
			spawn = dataclasses.replace(spawn, position=tuple(box.center), rotation=(spawn.rotation[0], G.yaw_of(box.rotation), spawn.rotation[2]))
		editable = self._spawn_editable()
		errors, warnings, notes = self._check_spawn(spawn) if editable or box is not None else ([], [], [])
		for text in errors:
			self._check_item(f"Error: {text}", QColor(220, 50, 40))
		for text in warnings:
			self._check_item(f"Warning: {text}", QColor(210, 130, 0))
		for text in notes:
			self._check_item(f"Note: {text}", None)
		if editable and not errors and not warnings:
			self._check_item("No problems found.", QColor(40, 160, 70))
		if not editable:
			self._check_item(spawn.summary(self.item_name(spawn.item)), None)
		self.view.update()

	def _look_at_selected(self):
		box = self._box_of(self.selected)
		if box is not None:
			self.view.look_at_box(box)

	# --- changing your zones ---------------------------------------------------------------------------------
	def _record(self, i):
		return self.doc.data[i]

	def _set_record(self, i, record, label, coalesce=None):
		"""Put a changed entry in the file, as one undoable step (steps with the same coalesce key one after another are one)."""
		self.doc.watch((i,))
		node = self.doc.data[i]
		node.clear()
		node.update(record)
		self.doc.touch(label, coalesce=coalesce)

	def _changed_record(self, i, box=None, zone_id=None, name=None, kind=None):
		"""Entry i with some of its parts changed (the rest, and anything else in it, kept)."""
		old = self._record(i)
		zone = self.mine[i]
		new = dict(old)
		new.update(Z.zone_record(
			zone.id if zone_id is None else zone_id, str(old.get("ZoneLocation", zone.location)),
			zone.kind if kind is None else kind, zone.box if box is None else box,
			zone.name if name is None else name, old.get("FlareType", ""),
		))
		if name is None and "ZoneName" in old:
			new["ZoneName"] = old["ZoneName"]
		return new

	def _form_box(self):
		zone = self.mine[self.selected[1]]
		rotation = G.yaw_rotation(self.yawSpin.value()) if G.is_upright(zone.box.rotation) else zone.box.rotation
		return G.Box(
			(self.xSpin.value(), self.ySpin.value(), self.zSpin.value()),
			(self.widthSpin.value(), self.heightSpin.value(), self.depthSpin.value()), rotation,
		)

	def _form_edited(self, field):
		if self._filling or not self._editable():
			return
		i = self.selected[1]
		if field == "id":
			text = self.idEdit.text().strip()
			if not text:
				return
			record = self._changed_record(i, zone_id=text)
		elif field == "name":
			record = self._changed_record(i, name=self.nameEdit.text())
		elif field == "kind":
			record = self._changed_record(i, kind=KINDS[self.kindBox.currentIndex()])
			self._new_kind = KINDS[self.kindBox.currentIndex()]
		else:
			record = self._changed_record(i, box=self._form_box())
		self._set_record(i, record, "Change zone", coalesce=("zone form", field))

	def _box_changing(self, box):
		"""A handle is being dragged: the form and the checks follow (the file changes when the drag ends)."""
		if self._spawn_editable():
			spawn = self.my_spawns[tuple(self.selected[1:])]
			for widget, value in ((self.spawnXSpin, box.center[0]), (self.spawnYSpin, box.center[1]), (self.spawnZSpin, box.center[2]), (self.spawnYawSpin, G.yaw_of(box.rotation))):
				_set_value(widget, value)
			self._show_spawn_checks(spawn, box)
			return
		if not self._editable():
			return
		self._filling = True
		try:
			self._fill_box(box)
		finally:
			self._filling = False
		self._show_checks(self.mine[self.selected[1]], box)

	def _box_edited(self, box):
		if self._spawn_editable():
			where = tuple(self.selected[1:])
			spawn = self.my_spawns[where]
			yaw = G.yaw_of(box.rotation)
			turned = abs((yaw - spawn.yaw + 180.0) % 360.0 - 180.0) > 1e-3
			self._set_spawn_record(where, S.changed_record(spawn.record, position=box.center, yaw=yaw if turned else None), "Turn item spawn" if turned else "Move item spawn")
		elif self._editable():
			i = self.selected[1]
			self._set_record(i, self._changed_record(i, box=box), "Move zone")

	def _place_toggled(self, on):
		if on:
			self._placing = ZONE
			self.view.placing_text = "Click the floor where the new zone goes (Esc to stop)"
			_set_checked(self.placeSpawnButton, False)
		self.view.set_placing(on)
		if on:
			self.view.setFocus()

	def _place_spawn_toggled(self, on):
		if on:
			if self._spawn_item is None:
				self._spawn_item = self.pick_item()
			if not self._spawn_item:
				_set_checked(self.placeSpawnButton, False)
				return
			self._placing = SPAWN
			self.view.placing_text = f"Click where the {self.item_name(self._spawn_item)} goes (Esc to stop)"
			_set_checked(self.placeButton, False)
			self.spawnsBox.setChecked(True)
		self.view.set_placing(on)
		if on:
			self.view.setFocus()

	def _placing_changed(self, on):
		_set_checked(self.placeButton, on and self._placing == ZONE)
		_set_checked(self.placeSpawnButton, on and self._placing == SPAWN)

	def _place_requested(self, point):
		if self._placing == SPAWN:
			self.place_spawn_at(point)
		else:
			self.place_at(point)

	def new_id(self, base="new_zone"):
		taken = set(self.index.ids() if self.index is not None else []) | {z.id for z in self.mine.values()}
		if base not in taken and base != "new_zone":
			return base
		n = 1
		while f"{base}_{n}" in taken:
			n += 1
		return f"{base}_{n}"

	def place_at(self, point):
		"""Put a new zone of the last kind used on the floor at point (x, y, z): its bottom just under it."""
		self.view.set_placing(False)
		if self.location is None or self.index is None:
			return None
		try:
			record, _zone, notes = Z.make_zone(self.index, self.new_id(), self.location, self._new_kind, point[0], point[2], y=point[1], size=NEW_SIZE)
		except ValueError as e:
			self.statusLabel.setText(str(e))
			return None
		self._add(record, "Add zone")
		self.statusLabel.setText(" ".join(notes))
		return record

	def _add(self, record, label):
		self.doc.change(label, lambda data: data.append(record))
		self.select((OWN, len(self.doc.data) - 1))

	def copy_selected(self):
		spawn = self._spawn(self.selected)
		if spawn is not None:
			return None if self._spawn_editable() else self._copy_spawn(spawn)
		zone = self._zone(self.selected)
		if zone is None or self._editable():
			return None
		record = Z.zone_record(self.new_id(f"{zone.id}_copy"), zone.location, zone.kind if zone.kind in Z.CUSTOM_TYPE else Z.TRIGGER, zone.box, None)
		self._add(record, "Copy zone")
		return record

	def delete_selected(self):
		if self._spawn_editable():
			map_name, i = self.selected[1:]
			self.selected = None
			self.spawn_doc.change("Delete item spawn", lambda data: data[map_name].pop(i))
			return
		if not self._editable():
			return
		i = self.selected[1]
		self.selected = None
		self.doc.change("Delete zone", lambda data: data.pop(i))

	# --- changing your spawns ----------------------------------------------------------------------------
	def _set_spawn_record(self, where, record, label, coalesce=None):
		"""Put a changed entry in the spawn file, as one undoable step (see _set_record)."""
		map_name, i = where
		self.spawn_doc.watch((map_name, i))
		node = self.spawn_doc.data[map_name][i]
		node.clear()
		node.update(record)
		self.spawn_doc.touch(label, coalesce=coalesce)

	def _spawn_form_edited(self, field):
		if self._filling or not self._spawn_editable():
			return
		where = tuple(self.selected[1:])
		record = self.my_spawns[where].record
		if field == "id":
			text = self.spawnIdEdit.text().strip()
			if not text:
				return
			record = S.changed_record(record, spawn_id=text)
		elif field == "count":
			record = S.changed_record(record, count=self.spawnCountSpin.value())
		elif field in ("x", "y", "z"):
			record = S.changed_record(record, position=(self.spawnXSpin.value(), self.spawnYSpin.value(), self.spawnZSpin.value()))
		elif field == "yaw":
			record = S.changed_record(record, yaw=self.spawnYawSpin.value())
		elif field == "chance":
			record = S.changed_record(record, probability=self.spawnChanceSpin.value())
		elif field == "always":
			record = S.changed_record(record, always=self.spawnAlwaysBox.isChecked())
		elif field == "gravity":
			record = S.changed_record(record, gravity=self.spawnGravityBox.isChecked())
		elif field == "random":
			record = S.changed_record(record, random_rotation=self.spawnRandomBox.isChecked())
		self._set_spawn_record(where, record, "Change item spawn", coalesce=("spawn form", field))

	def _spawn_name(self, item):
		"""The start of a new spawn's template Id: its item's name (as the game's start with an object's name)."""
		return self.item_name(item) or item

	def place_spawn_at(self, point, item=None):
		"""Put a new spawn of item (else the last one placed or chosen) just above point (x, y, z), so it falls onto it."""
		self.view.set_placing(False)
		item = item or self._spawn_item
		if self.location is None or not item:
			return None
		self._spawn_item = item
		record = S.spawn_record(item, (point[0], point[1] + S.LIFT, point[2]), name=self._spawn_name(item))
		self._add_spawn(record, self.location, "Add item spawn")
		self.statusLabel.setText(f"Placed {self.item_name(item)}, {S.LIFT:.2f} m above the spot clicked: it falls onto it when the raid starts.")
		return record

	def _add_spawn(self, record, location, label):
		placed = []
		self.spawn_doc.change(label, lambda data: placed.append(S.add_spawn(data, location, record)))
		self.select((MY_SPAWN, *placed[0]))

	def _copy_spawn(self, spawn):
		record = copy.deepcopy(spawn.record)
		record["locationId"] = S.location_id(spawn.position)
		template = record.setdefault("template", {})
		name = template.get("Id", "").split(" [")[0] or self._spawn_name(spawn.item)
		template["Id"] = f"{name} [{uuid.uuid4()}]"  # (a spawn of its own, not one of its alternatives)
		record = S.changed_record(record)  # (Position and Rotation in small letters)
		self._add_spawn(record, spawn.location, "Copy item spawn")
		return record

	def choose_item(self):
		"""Change the selected spawn's item to one the user chooses (also the item of the next spawn placed)."""
		if not self._spawn_editable():
			return None
		item = self.pick_item()
		if not item:
			return None
		self._spawn_item = item
		where = tuple(self.selected[1:])
		self._set_spawn_record(where, S.changed_record(self.my_spawns[where].record, item=item), "Change item")
		return item

	def put_spawn_on_floor(self):
		"""Put the selected spawn just above the floor (or the top of what is) under it, nearest to where it is."""
		if not self._spawn_editable() or self.index is None:
			return
		where = tuple(self.selected[1:])
		spawn = self.my_spawns[where]
		if spawn.location not in self.index.game_maps:
			return
		x, y, z = spawn.position
		floor = self.index.map(spawn.location).floors.floor_near(x, y, z, below=3.0, above=1.5)
		if floor is None:
			self.statusLabel.setText("No floor is mapped under it near it.")
			return
		self._set_spawn_record(where, S.changed_record(spawn.record, position=(x, floor + S.LIFT, z)), "Put item spawn on floor")
		self.statusLabel.setText(f"It is now {S.LIFT:.2f} m above the floor at {floor:.2f} m.")

	def _floor_under(self, x, z, near):
		"""The floor at (x, z) nearest to height `near` (within 3 m below and 1.5 m above), from the floor map and the
		walls' tops; None if there is none."""
		return self.index.map(self.location).floors.floor_near(x, near, z, below=3.0, above=1.5)

	def sit_on_floor(self):
		if not self._editable():
			return
		i = self.selected[1]
		box = self.mine[i].box
		bottom = box.center[1] - box.size[1] / 2
		floor = self._floor_under(box.center[0], box.center[2], bottom + Z.SINK)
		if floor is None:
			self.statusLabel.setText("No floor is mapped under its middle near its bottom.")
			return
		new = G.Box((box.center[0], floor - Z.SINK + box.size[1] / 2, box.center[2]), box.size, box.rotation)
		self._set_record(i, self._changed_record(i, box=new), "Sit zone on floor")
		self.statusLabel.setText(f"Its bottom is now {Z.SINK:.2f} m under the floor at {floor:.2f} m.")

	def cover_slope(self):
		if not self._editable():
			return
		i = self.selected[1]
		box = self.mine[i].box
		floors = self.index.map(self.location).floors
		bottom = box.center[1] - box.size[1] / 2
		floor = self._floor_under(box.center[0], box.center[2], bottom + Z.SINK)
		low, high = Z.walkable_span(floors, box, floor if floor is not None else bottom + Z.SINK)
		if high - low < 0.3:
			self.statusLabel.setText("The floor under it is level: there is no slope to cover.")
			return
		new_bottom = low - Z.SINK
		top = max(box.center[1] + box.size[1] / 2, high + Z.PLAYER_HEIGHT * 0.5)
		new = G.Box((box.center[0], (new_bottom + top) / 2, box.center[2]), (box.size[0], top - new_bottom, box.size[2]), box.rotation)
		self._set_record(i, self._changed_record(i, box=new), "Cover slope")
		self.statusLabel.setText(f"The walk under it goes from {low:.2f} to {high:.2f} m: it now reaches from {new_bottom:.2f} to {top:.2f} m.")

	# --- finding -------------------------------------------------------------------------------------------
	def find(self, text=None, choose=False):
		"""Look for a zone, place, building or object on this map and go to the best match (with choose, offer a choice
		when there are several). Returns what was found."""
		text = (self.search.text() if text is None else text).strip()
		if not text or self.index is None or self.location is None:
			return []
		results = []
		lowered = text.lower()
		for key, zone, _style in self._shown():
			if lowered in zone.id.lower() or (zone.name and lowered in zone.name.lower()):
				results.append({"kind": "zone", "name": zone.id, "key": key})
		for key, spawn, _style in self._shown_spawns():
			name = self.item_name(spawn.item)
			if lowered in name.lower() or lowered in spawn.id.lower():
				results.append({"kind": "item spawn", "name": name, "key": key})
		try:
			results += places.find(self.index, text, self.location, limit=15)
		except (OSError, ValueError) as e:
			self.statusLabel.setText(f"Couldn't search the places: {e}")
		results = results[:20]
		if not results:
			self.statusLabel.setText(f"Nothing called '{text}' was found on this map.")
		elif len(results) == 1 or not choose:
			self.go_to(results[0])
		else:
			menu = QMenu(self)
			for result in results:
				label = f"{result.get('name', '?')}  ({result['kind']}{', ' + str(result['count']) + ' objects' if result.get('count') else ''})"
				menu.addAction(label, lambda r=result: self.go_to(r))
			menu.exec(self.search.mapToGlobal(self.search.rect().bottomLeft()))
		return results

	def go_to(self, result):
		if result["kind"] in ("zone", "item spawn"):
			self.select(result["key"])
			self.view.look_at_box(self._box_of(result["key"]))
			return
		if result.get("min") and result.get("max"):
			self.view.camera.frame(result["min"], result["max"], margin=1.1)
		at = result.get("at")
		if at:
			x, z = at[0], at[-1]
			y = at[1] if len(at) == 3 else None
			if y is None:
				floors = self.index.map(self.location).floors.floors_at(x, z)
				y = floors[0] if floors else self.view.camera.target[1]
			self.view.markers = [((x, y, z), result.get("name", ""))]
			if not result.get("min"):
				self.view.camera.target = (x, y, z)
				self.view.camera.distance = min(self.view.camera.distance, 60.0)
		self.view.update()
		note = result.get("warning") or result.get("note") or ""
		self.statusLabel.setText(f"{result.get('name', '')} ({result['kind']}). {note}".strip())

	def find_building(self):
		"""Find the building at the middle of the view: outline it and list its storeys."""
		if self.index is None or self.location is None:
			return None
		x, _y, z = self.view.camera.target
		found = buildings.building_at(self.index.map(self.location), x, z)
		self.building = found
		outline = found.get("outline")
		storeys = [s for s in found.get("storeys", []) if not s.get("below_ground")]
		if outline and storeys:
			low, high = min(s["height"] for s in storeys), max(s["height"] for s in storeys) + 3.0
			cx, cz = outline["center"]
			box = G.Box((cx, (low + high) / 2, cz), (outline["size"][0], high - low, outline["size"][1]), G.yaw_rotation(outline["yaw"]))
			self.view.set_outlines([("building", box)])
		else:
			self.view.set_outlines([])
		self._fill_storeys(storeys)
		self.statusLabel.setText(" ".join(n for n in found.get("notes", []) if "--picture" not in n))  # (that one is the command line's)
		return found

	def _fill_storeys(self, storeys=()):
		self.storeyBox.blockSignals(True)
		self.storeyBox.clear()
		self.storeyBox.addItem("Storeys" if storeys else "(Building here first)", None)
		for s in storeys:
			self.storeyBox.addItem(f"Floor at {s['height']:.1f} m", s["height"])
		self.storeyBox.setEnabled(bool(storeys))
		self.storeyBox.blockSignals(False)

	def _storey_chosen(self, index):
		height = self.storeyBox.itemData(index)
		if height is None:
			self.cutSlider.set_value(None)
			return
		self.cutSlider.set_value(height + STOREY_VIEW)
		x, _y, z = self.view.camera.target
		self.view.camera.target = (x, height, z)
		self.view.update()

	# --- importing the maps ---------------------------------------------------------------------------------
	def _records(self):
		"""{location: the imported map's record} (read with the zones, so this costs nothing)."""
		return {key: self.index.map(key).record for key in self.index.game_maps} if self.index is not None else {}

	def _last_import(self):
		"""The record of the map imported last, or None."""
		return max(self._records().values(), key=lambda r: r.get("imported") or "", default=None)

	def _game_dir(self):
		"""The game folder to compare the maps with and import them from: game_dir, else the game your SPT database (in
		the settings) is in, else the one the maps were last imported from; None if there is none."""
		if self.game_dir:
			return self.game_dir
		game = M.game_holding(getattr(self.settings, "database_folder", "")) if self.settings is not None else None
		last = self._last_import()
		return game or (Path(last["source"]) if last and last.get("source") else None)

	def _import_button(self):
		last = self._last_import()
		self.importButton.setText("Import the maps again..." if last else "Import the game's maps...")
		if last:
			version = f" (version {last['game_version']})" if last.get("game_version") else ""
			self.importButton.setToolTip(
				f"The maps were last imported from {last.get('source')}{version} on {last.get('imported')}. Import them "
				"again after a game update, or from another game folder (takes a few minutes; nothing in the game is changed)."
			)
		else:
			self.importButton.setToolTip("Read the maps from the game's own files (takes a few minutes; nothing in the game is changed)")

	def check_maps_version(self):
		"""Show the notice above the view if the maps aren't from the game as it is now (maps.mapdata.older_maps), else hide
		it. Run when the maps are read, and when the settings change (they say which game your SPT database is in)."""
		records = self._records()
		game = self._game_dir() if records else None
		now, older = M.older_maps(records, game) if game else (None, {})
		if not older:
			self.versionLabel.hide()
			return
		which = "The maps are" if len(older) == len(self.index.game_maps) else f"{len(older)} of the {len(self.index.game_maps)} maps are"
		self.versionLabel.setText(
			f"{which} from version {' and '.join(sorted(set(older.values())))} of the game, but the game in "
			f"{html.escape(str(game))} is version {now}. <a href=\"import\">Import them again</a> to see that version's maps, "
			"or <a href=\"hide\">hide this</a>."
		)
		self.versionLabel.show()

	def _notice_link(self, link):
		if link == "import":
			self.import_maps(self._game_dir())
		else:
			self.versionLabel.hide()

	def import_maps(self, game_dir=None):
		"""Import the maps from game_dir, else from the folder chosen (the dialog starts in the game the maps are compared
		with). They are read again when done; the map shown meanwhile stays (maps.mapdata swaps each file in when written)."""
		if self._worker is not None:
			return
		if game_dir is None:
			start = self._game_dir()
			game_dir = QFileDialog.getExistingDirectory(self, "The game's folder (the one with EscapeFromTarkov_Data)", str(start or ""))
			if not game_dir:
				return
		if not (Path(game_dir) / "EscapeFromTarkov_Data").is_dir():
			QMessageBox.warning(self, "Import the maps", f"{game_dir} has no EscapeFromTarkov_Data folder: choose the game's own folder.")
			return
		self.importButton.setEnabled(False)
		self.versionLabel.hide()
		self.statusLabel.setText("Importing the maps...")
		self._worker = ImportWorker(game_dir, self.maps_folder)
		self._worker.signals.progress.connect(lambda text: self.statusLabel.setText(f"Importing the maps: {text}"))
		self._worker.signals.finished.connect(self._imported)
		QThreadPool.globalInstance().start(self._worker)

	def _imported(self, result):
		self._worker = None
		self.importButton.setEnabled(True)
		failed = isinstance(result, Exception)
		self.statusLabel.setText(f"The maps couldn't be imported: {result}" if failed else f"Imported {len(result)} maps.")
		self._floors.clear()
		self.load()  # (after a failure too: the maps imported before it are new)


def _set_text(edit, text, start=False):
	"""Show text in a line edit (only if it shows another: typing there isn't disturbed); start: its start shows."""
	if edit.text() != text:
		edit.setText(text)
		if start:
			edit.setCursorPosition(0)


def _set_value(spin, value):
	"""Show a value in a spin box without it counting as an edit (and only if it shows another)."""
	step = 10 ** -spin.decimals() / 2 if hasattr(spin, "decimals") else 0.5
	if abs(spin.value() - value) > step:
		spin.blockSignals(True)
		spin.setValue(value if hasattr(spin, "decimals") else int(value))
		spin.blockSignals(False)


def _set_checked(button, checked):
	if button.isChecked() != checked:
		button.blockSignals(True)
		button.setChecked(checked)
		button.blockSignals(False)


def _in_view(view, box):
	"""True if the box's middle is on screen and not tiny."""
	spot = view.camera.project(box.center, view.width(), view.height())
	if spot is None or not (0 <= spot[0] <= view.width() and 0 <= spot[1] <= view.height()):
		return False
	return max(box.size) / view.camera.metres_per_pixel(view.height()) > 12


class ZonesWindow(QMainWindow):
	"""The Zones tab as a window of its own (`python -m cli zones edit`): Ctrl+S saves (the zone file and the spawn
	file, whichever has changes), Ctrl+Z and Ctrl+Y undo and redo (the latest change of either), and closing asks to
	save."""

	def __init__(self, tab):
		super().__init__()
		self.tab = tab
		self.setCentralWidget(tab)
		self.resize(1500, 900)
		docs = lambda: (tab.doc, tab.spawn_doc)
		for keys, action in (
			(QKeySequence.StandardKey.Save, self.save),
			(QKeySequence.StandardKey.Undo, lambda: max(docs(), key=lambda d: d.undo_stamp).undo()),
			(QKeySequence.StandardKey.Redo, lambda: max(docs(), key=lambda d: d.redo_stamp).redo()),
		):
			QShortcut(keys, self, activated=action)
		tab.zones_changed.connect(self._title)
		tab.spawns_changed.connect(self._title)
		self._title()

	def save(self):
		if self.tab.doc.dirty or not self.tab.spawn_doc.dirty:
			self.tab.save_file()
		if self.tab.spawn_doc.dirty:
			self.tab.save_spawn_file()

	def _title(self):
		parts = [f"{self.tab.doc.name}{'*' if self.tab.doc.dirty else ''}"]
		if self.tab.spawn_doc.path is not None or self.tab.spawn_doc.data:
			parts.append(f"{self.tab.spawn_doc.name}{'*' if self.tab.spawn_doc.dirty else ''}")
		self.setWindowTitle("Zones - " + ", ".join(parts))

	def closeEvent(self, event):
		if self.tab._confirm_discard() and self.tab._confirm_discard_spawns():
			event.accept()
		else:
			event.ignore()
