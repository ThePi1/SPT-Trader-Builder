"""The Zones tab: the quest zones on a 3D view of a map, to look at the game's zones and make and change your own.

Your zones are in one quest zone file (WTT-CommonLib's CustomQuestZones: a list of entries), held as a
core.documents.Document so every change can be undone. The game's zones (from the imported maps), the zones in the
reference files and any other zone files given are shown too, but never changed: "Copy as a new zone" puts a copy in
your file. Each of your zones is checked as it changes (maps.zones.check_zone: its kind, overlaps, and whether a player
can reach it from the floor), and the spots the floor check looked at are drawn under it.

The layout is ui/designer/zones_tab.ui; the 3D view is ui/view3d/view.py, and the height slider beside it (to hide
what is above a storey) ui/view3d/cut_slider.py. The maps are read when the tab is first
shown (and a map's floor map and walls when it is first shown, with ui/view3d/loading_panel.py saying how far along), and can be imported again (after a game update, or from another game folder): a notice above the view says when
they aren't from the game as it is now. The same tab is the window of `python -m cli zones edit`.
"""

import copy
import html
import logging
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QCursor, QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QFileDialog, QListWidgetItem, QMainWindow, QMenu, QMessageBox, QTreeWidgetItem, QWidget

from core.documents import Document
from maps import buildings, places
from maps import geometry as G
from maps import mapdata as M
from maps import zones as Z
from maps.triangles import Triangles
from ui.compiled.ui_zones_tab import Ui_ZonesForm
from ui.view3d.cut_slider import STOREY_VIEW, CutSlider
from ui.view3d.loading_panel import LoadingPanel
from ui.view3d.view import GAME, MINE, REFERENCE, MapView, ViewZone

log = logging.getLogger(__name__)

BASE, OWN = "base", "mine"  # the first part of a zone's key: (BASE, index in self.base) or (OWN, index in the file)
NEW_SIZE = (4.0, 3.0, 4.0)  # metres: a new zone's width, height and depth
FIRST_MAP = "factory4_day"  # shown first when nothing says which: Factory (day), small and quick to read
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
	them from (default: the game your SPT database is in, else the one the maps came from)."""

	zones_changed = Signal()  # your zone file changed (the quests' checks may want to look again)

	def __init__(self, settings=None, references=None, map_names=None, maps_folder=None, zone_files=(), game_dir=None, parent=None):
		super().__init__(parent)
		self.setupUi(self)
		self.settings, self.references = settings, references
		self.map_names = dict(map_names or {})
		self.maps_folder = maps_folder
		self.zone_files = [Path(p) for p in zone_files]
		self.game_dir = Path(game_dir) if game_dir else None
		self.versionLabel.setStyleSheet(NOTICE_STYLE)
		self.versionLabel.hide()
		self.doc = Document([])
		self.doc.on_change(self._doc_changed)
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
		self._connect()
		self._doc_changed()

	def _connect(self):
		v = self.view
		v.zone_clicked.connect(lambda key: self.select(key))
		v.box_changing.connect(self._box_changing)
		v.box_edited.connect(self._box_edited)
		v.place_requested.connect(self.place_at)
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
		for box in (self.floorBox, self.wallsBox, self.gameZonesBox, self.referenceZonesBox, self.areasBox, self.labelsBox):
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
		"""start_map, else the map of your first zone, else FIRST_MAP, else the first imported."""
		if self.start_map in keys:
			return self.start_map
		for zone in self.mine.values():
			if zone.location in keys:
				return zone.location
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

	def references_changed(self):
		"""The reference files changed: their zones are read again."""
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
		if self.selected and self._zone(self.selected) is not None and self._zone(self.selected).location != location:
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

	def _doc_changed(self, _doc=None):
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

	# --- what is shown ----------------------------------------------------------------------------------
	def _zone(self, key):
		if key is None:
			return None
		kind, i = key
		if kind == OWN:
			return self.mine.get(i)
		return self.base[i] if 0 <= i < len(self.base) else None

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
			self.view.set_zones([(ViewZone(key, zone.id, zone.kind, zone.box), style) for key, zone, style in self._shown()])
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
		zone = self._zone(self.selected)
		if look and zone is not None:
			if not _in_view(self.view, zone.box):
				self.view.look_at_box(zone.box)

	def _editable(self):
		return self.selected is not None and self.selected[0] == OWN and self.selected[1] in self.mine

	def _show_selected(self):
		zone = self._zone(self.selected)
		editable = self._editable()
		self.view.set_selected(self.selected, zone.box if zone else None, zone.kind if zone else "", editable)
		was = self._filling
		self._filling = True
		try:
			self._fill_form(zone, editable)
		finally:
			self._filling = was
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

	def _look_at_selected(self):
		zone = self._zone(self.selected)
		if zone is not None:
			self.view.look_at_box(zone.box)

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
		if not self._editable():
			return
		self._filling = True
		try:
			self._fill_box(box)
		finally:
			self._filling = False
		self._show_checks(self.mine[self.selected[1]], box)

	def _box_edited(self, box):
		if self._editable():
			i = self.selected[1]
			self._set_record(i, self._changed_record(i, box=box), "Move zone")

	def _place_toggled(self, on):
		self.view.set_placing(on)
		if on:
			self.view.setFocus()

	def _placing_changed(self, on):
		self.placeButton.blockSignals(True)
		self.placeButton.setChecked(on)
		self.placeButton.blockSignals(False)

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
		zone = self._zone(self.selected)
		if zone is None or self._editable():
			return None
		record = Z.zone_record(self.new_id(f"{zone.id}_copy"), zone.location, zone.kind if zone.kind in Z.CUSTOM_TYPE else Z.TRIGGER, zone.box, None)
		self._add(record, "Copy zone")
		return record

	def delete_selected(self):
		if not self._editable():
			return
		i = self.selected[1]
		self.selected = None
		self.doc.change("Delete zone", lambda data: data.pop(i))

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
		if result["kind"] == "zone":
			self.select(result["key"])
			self.view.look_at_box(self._zone(result["key"]).box)
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


def _set_text(edit, text):
	if edit.text() != text:
		edit.setText(text)


def _in_view(view, box):
	"""True if the box's middle is on screen and not tiny."""
	spot = view.camera.project(box.center, view.width(), view.height())
	if spot is None or not (0 <= spot[0] <= view.width() and 0 <= spot[1] <= view.height()):
		return False
	return max(box.size) / view.camera.metres_per_pixel(view.height()) > 12


class ZonesWindow(QMainWindow):
	"""The Zones tab as a window of its own (`python -m cli zones edit`): Ctrl+S saves, Ctrl+Z and Ctrl+Y undo and
	redo, and closing asks to save."""

	def __init__(self, tab):
		super().__init__()
		self.tab = tab
		self.setCentralWidget(tab)
		self.resize(1500, 900)
		for keys, action in (
			(QKeySequence.StandardKey.Save, lambda: tab.save_file()), (QKeySequence.StandardKey.Undo, lambda: tab.doc.undo()),
			(QKeySequence.StandardKey.Redo, lambda: tab.doc.redo()),
		):
			QShortcut(keys, self, activated=action)
		tab.zones_changed.connect(self._title)
		self._title()

	def _title(self):
		self.setWindowTitle(f"Zones - {self.tab.doc.name}{'*' if self.tab.doc.dirty else ''}")

	def closeEvent(self, event):
		if self.tab._confirm_discard():
			event.accept()
		else:
			event.ignore()
