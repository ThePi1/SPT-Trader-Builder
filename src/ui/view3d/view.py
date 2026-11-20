"""The 3D view of a map, drawn with OpenGL: the floor (the navmesh, coloured by height and darker where it slopes), the
walls when they have been imported, the quest zones as see-through boxes, and the handles of the zone being edited.

Mouse: left-drag turns the view (pans it in the top-down view), right- or middle-drag (or Shift+left) pans, the wheel
zooms toward the mouse, a click selects a zone (or, while placing, puts the new zone where it lands), a double-click
looks at that spot. Dragging the selected zone moves it; its handles size, lift and turn it (Shift snaps). F frames
the selected zone, T switches to the top-down view and back, Delete asks to delete the selected zone.

The cut (set_cut, from the height slider beside the view: ui.view3d.cut_slider) hides everything above a height. Where
it slices through the walls, they are drawn as solid, like a floor plan: their outline at the cut is drawn in
CAP_COLOUR (Triangles.section; this is what shows from straight above, where a wall's sides are edge on), and so is the
inside of a wall where it shows (the back of its faces: Unity's faces go round clockwise as seen from the front).

What a click hits and how a drag changes a box are worked out by maps.triangles, ui.view3d.camera and
ui.view3d.handles (no Qt, tested on their own); this module draws and passes the mouse on.
"""

import math
from dataclasses import dataclass

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QMatrix4x4, QPainter, QPen, QSurfaceFormat, QVector2D, QVector3D, QVector4D
from PySide6.QtOpenGL import QOpenGLBuffer, QOpenGLShader, QOpenGLShaderProgram
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from maps import geometry as G
from maps.triangles import box_edges, box_faces, ray_box
from maps.zones import KIND_COLOURS, NEW_COLOUR
from ui.view3d import handles as H
from ui.view3d.camera import Camera

GL_FLOAT, GL_TRIANGLES, GL_LINES = 0x1406, 0x0004, 0x0001
GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT = 0x4000, 0x0100
GL_DEPTH_TEST, GL_BLEND, GL_POLYGON_OFFSET_FILL, GL_MULTISAMPLE = 0x0B71, 0x0BE2, 0x8037, 0x809D
GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_LEQUAL, GL_VERSION, GL_RENDERER = 0x0302, 0x0303, 0x0203, 0x1F02, 0x1F01
GL_CW = 0x0900

NO_CUT = 1.0e6
BACKGROUND = (0.11, 0.12, 0.14)
WALL_COLOUR = (0.62, 0.63, 0.66)
CAP_COLOUR = (0.30, 0.19, 0.17)  # the walls the cut slices through: their outline there and their inside
SECTION_LIFT = 0.02  # metres the outline is drawn above the cut
AREA_COLOUR = QColor(200, 200, 200)
HANDLE_PIXELS = 9  # how near (in pixels) the mouse must be to a handle to take it
BIG_ZONE = 15.0  # metres: a zone longer than this is drawn fainter, the longer the fainter
MOST_LABELS = 60  # the zones named on screen at once (the nearest to what the view looks at)
ON_MAP = 50.0  # metres past the floor's edges the view can look at (see keep_on_map)

# GLSL 1.20, so it runs on any OpenGL from 2.1 (and on the software renderer)
VERTEX_SHADER = """#version 120
attribute vec3 position;
uniform mat4 matrix;
varying vec3 world;
void main() {
	world = position;
	gl_Position = matrix * vec4(position, 1.0);
}
"""
FRAGMENT_SHADER = """#version 120
uniform float cut;
uniform float shading;
uniform float by_height;
uniform vec2 heights;
uniform vec4 colour;
uniform float caps;
uniform vec3 cap_colour;
varying vec3 world;
void main() {
	if (world.y > cut) discard;
	if (caps > 0.5 && !gl_FrontFacing) {  // (the inside of a wall the cut slices through: flat, so it reads as solid)
		gl_FragColor = vec4(cap_colour, colour.a);
		return;
	}
	vec3 base = colour.rgb;
	if (by_height > 0.5) {
		float t = clamp((world.y - heights.x) / max(heights.y - heights.x, 0.001), 0.0, 1.0);
		base = vec3(30.0 + 200.0 * t, 50.0 + 180.0 * t, 110.0 - 40.0 * t) / 255.0;
	}
	float light = 1.0;
	if (shading > 0.5) {  // (each triangle's slope, from how its position changes across the screen)
		vec3 n = normalize(cross(dFdx(world), dFdy(world)) + vec3(0.0, 1e-9, 0.0));
		light = 0.42 + 0.58 * abs(n.y) + 0.15 * abs(dot(n, vec3(0.53, 0.0, 0.85)));
	}
	gl_FragColor = vec4(base * light, colour.a);
}
"""


@dataclass
class ViewZone:
	"""A zone as the view draws it. key: what the tab knows it by. style: GAME, REFERENCE or MINE (stronger)."""

	key: object
	label: str
	kind: str
	box: G.Box


GAME, REFERENCE, MINE = "game", "reference", "mine"
_ALPHA = {GAME: (0.10, 0.55), REFERENCE: (0.14, 0.75), MINE: (0.22, 0.95)}  # (faces, edges)


def _matrix(m):
	return QMatrix4x4(*[float(v) for v in np.asarray(m).flatten()])


def _rgb(kind):
	return tuple(c / 255 for c in KIND_COLOURS.get(kind, (255, 255, 255)))


class _Buffer:
	"""A vertex buffer on the graphics card: what to draw and how many corners it has."""

	def __init__(self):
		self.buffer = None
		self.count = 0
		self.pending = None  # an array waiting to be sent (sent when next drawn: the context is current then)

	def set(self, array):
		self.pending = np.ascontiguousarray(array, dtype=np.float32) if array is not None else np.zeros((0, 3), np.float32)

	def upload(self):
		if self.pending is None:
			return
		array, self.pending = self.pending, None
		if self.buffer is None:
			self.buffer = QOpenGLBuffer(QOpenGLBuffer.Type.VertexBuffer)
			self.buffer.create()
		self.buffer.bind()
		data = array.tobytes()
		self.buffer.allocate(data, len(data))
		self.buffer.release()
		self.count = len(array)

	def destroy(self):
		if self.buffer is not None:
			self.buffer.destroy()
			self.buffer = None


class MapView(QOpenGLWidget):
	zone_clicked = Signal(object)  # the key of the zone clicked, or None for a click on no zone
	box_changing = Signal(object)  # the selected zone's box (maps.geometry.Box) while it is dragged
	box_edited = Signal(object)  # ... and when the drag ends
	place_requested = Signal(object)  # (x, y, z) on the floor or a wall, clicked while placing
	placing_changed = Signal(bool)
	hovered = Signal(object)  # (x, y, z) under the mouse, or None
	delete_requested = Signal()
	top_down_changed = Signal(bool)
	view_moved = Signal(object)  # (x, y, z) the view looks at, once it has stopped moving

	def __init__(self, parent=None):
		super().__init__(parent)
		fmt = QSurfaceFormat()
		fmt.setDepthBufferSize(24)
		fmt.setSamples(4)
		self.setFormat(fmt)
		self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
		self.setMouseTracking(True)
		self.setMinimumSize(200, 150)
		self.camera = Camera()
		self.floor = None  # maps.triangles.Triangles
		self.walls = None
		self.show_floor, self.show_walls, self.show_zones, self.show_areas, self.show_labels = True, True, True, False, True
		self.cut = NO_CUT
		self.zones = []  # [(ViewZone, style)]
		self.areas = []  # [(name, maps.geometry.Box)]: the parts of the map, outlined when show_areas is on
		self.outlines = []  # [(name, maps.geometry.Box)]: always outlined (the building found)
		self.markers = []  # [((x, y, z), label)]
		self.samples = []  # [((x, y, z), ok)]: where the checks looked for floor under the selected zone
		self.selected_key = None
		self.selected_box = None
		self.selected_kind = ""
		self.selected_editable = False
		self.placing = False
		self.message = ""  # said in the middle when there is nothing to draw
		self.gl_problem = ""  # why the view can't draw, if it can't
		self.renderer = ""  # the OpenGL version and renderer in use
		self._heights = (0.0, 10.0)
		self._floor_buffer, self._wall_buffer = _Buffer(), _Buffer()
		self._zone_faces, self._zone_edges, self._area_edges, self._outline_edges = _Buffer(), _Buffer(), _Buffer(), _Buffer()
		self._selected_faces, self._selected_edges = _Buffer(), _Buffer()
		self._section_lines = _Buffer()  # the walls' outline at the cut
		self._program = None
		self._press = None
		self._last = None
		self._moved = False
		self._drag = None
		self._hover_pos = None
		self.hover_point = None
		self._hover_timer = QTimer(self)
		self._hover_timer.setSingleShot(True)
		self._hover_timer.setInterval(40)
		self._hover_timer.timeout.connect(self._hover)
		self._looked_at = None
		self._moved_timer = QTimer(self)
		self._moved_timer.setSingleShot(True)
		self._moved_timer.setInterval(200)
		self._moved_timer.timeout.connect(lambda: self.view_moved.emit(self._looked_at))

	# --- what to draw -------------------------------------------------------------------------------
	def set_floor(self, triangles):
		"""The floor (maps.triangles.Triangles), or None. The colours by height run between its 2nd and 98th percentile."""
		self.floor = triangles
		if triangles is not None and len(triangles):
			ys = triangles.heights()
			self._heights = (float(np.percentile(ys, 2)), float(np.percentile(ys, 98)))
		self._floor_buffer.set(triangles.vertex_array() if triangles is not None else None)
		self.update()

	def set_walls(self, triangles):
		self.walls = triangles
		self._wall_buffer.set(triangles.vertex_array() if triangles is not None else None)
		self._section_changed()
		self.update()

	def _section_changed(self):
		if self.walls is None or self.cut >= NO_CUT:
			self._section_lines.set(None)
		else:  # (a little above the cut, so the walls' faces don't hide it)
			self._section_lines.set(self.walls.section(self.cut).reshape(-1, 3) + np.float32([0.0, SECTION_LIFT, 0.0]))

	def set_zones(self, zones):
		"""zones: [(ViewZone, style)]. The selected one is drawn on its own (see set_selected)."""
		self.zones = list(zones)
		self._zone_faces.set(np.concatenate([box_faces(z.box) for z, _s in self.zones]) if self.zones else None)
		self._zone_edges.set(np.concatenate([box_edges(z.box) for z, _s in self.zones]) if self.zones else None)
		self.update()

	def set_areas(self, areas):
		"""areas: [(name, maps.geometry.Box)], outlined when show_areas is on."""
		self.areas = list(areas)
		self._area_edges.set(np.concatenate([box_edges(b) for _n, b in self.areas]) if self.areas else None)
		self.update()

	def set_outlines(self, outlines):
		"""outlines: [(name, maps.geometry.Box)], always outlined (a building found)."""
		self.outlines = list(outlines)
		self._outline_edges.set(np.concatenate([box_edges(b) for _n, b in self.outlines]) if self.outlines else None)
		self.update()

	def set_top_down(self, top_down):
		if top_down != self.camera.top_down:
			self.camera.top_down = top_down
			self.top_down_changed.emit(top_down)
			self.update()

	def set_selected(self, key, box=None, kind="", editable=False):
		"""The zone being looked at (key), with its box drawn on its own; editable ones get handles."""
		self.selected_key, self.selected_box, self.selected_kind, self.selected_editable = key, box, kind, editable
		self._drag = None
		self._selected_changed()

	def set_selected_box(self, box):
		"""The selected zone's box changed (from the form, or undo)."""
		self.selected_box = box
		self._selected_changed()

	def _selected_changed(self):
		box = self.selected_box
		self._selected_faces.set(box_faces(box) if box is not None else None)
		self._selected_edges.set(box_edges(box) if box is not None else None)
		self.update()

	def set_cut(self, height):
		"""Draw nothing above this height (None: everything)."""
		self.cut = NO_CUT if height is None else float(height)
		self._section_changed()
		self.update()

	def set_placing(self, placing):
		if placing != self.placing:
			self.placing = placing
			self.setCursor(Qt.CursorShape.CrossCursor if placing else Qt.CursorShape.ArrowCursor)
			self.placing_changed.emit(placing)
			self.update()

	def look_at_box(self, box, keep_angle=True):
		low, high = box.bounds()
		self.camera.frame(low, high, margin=2.2)
		self.update()

	def keep_on_map(self):
		"""Keep what the view looks at over the map (up to ON_MAP metres past the floor's edges) and between its lowest
		and highest floor, so the view turns about a point on the map and the height slider has something to show."""
		shape = self.floor if self.floor is not None and len(self.floor) else self.walls
		if shape is None or not len(shape):
			return
		low, high = shape.bounds()
		target = tuple(min(max(float(v), lo - m), hi + m) for v, lo, hi, m in zip(self.camera.target, low, high, (ON_MAP, 0.0, ON_MAP)))
		if target != tuple(self.camera.target):
			self.camera.target = target
			self.update()

	def look_at_everything(self):
		"""Frame the floor (the walls reach out past the playable map: borders, scenery)."""
		ranges = [t.bounds() for t in ((self.floor,) if self.floor is not None and len(self.floor) else (self.walls,)) if t is not None and len(t)]
		if ranges:
			low = np.min([r[0] for r in ranges], axis=0)
			high = np.max([r[1] for r in ranges], axis=0)
			self.camera.frame(low, (high[0], low[1], high[2]), margin=1.0)
			self.update()

	# --- OpenGL -------------------------------------------------------------------------------------
	def initializeGL(self):
		f = self.context().functions()
		try:
			self.renderer = f"{f.glGetString(GL_VERSION)} ({f.glGetString(GL_RENDERER)})"
		except Exception:  # (some bindings give nothing back here)
			self.renderer = ""
		program = QOpenGLShaderProgram(self)
		ok = program.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Vertex, VERTEX_SHADER)
		ok = ok and program.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Fragment, FRAGMENT_SHADER)
		program.bindAttributeLocation("position", 0)
		if not (ok and program.link()):
			self.gl_problem = (
				"The 3D view needs OpenGL 2.1 or later" + (f"; this computer gives {self.renderer}" if self.renderer else "")
				+ ". Settings > General > 'Draw the 3D map without the graphics card' may help."
			)
			return
		self._program = program
		self.context().aboutToBeDestroyed.connect(self._release)

	def _release(self):
		self.makeCurrent()
		for buffer in self._buffers():
			buffer.destroy()
			buffer.pending = None
		self.doneCurrent()

	def _buffers(self):
		return (
			self._floor_buffer, self._wall_buffer, self._zone_faces, self._zone_edges, self._area_edges, self._outline_edges,
			self._selected_faces, self._selected_edges, self._section_lines,
		)

	def paintGL(self):
		if tuple(self.camera.target) != self._looked_at:  # (every move ends in a drawing: say where it stopped, once it has)
			self._looked_at = tuple(self.camera.target)
			self._moved_timer.start()
		f = self.context().functions()
		f.glColorMask(True, True, True, True)
		f.glClearColor(*BACKGROUND, 1.0)
		f.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		if self._program is not None:
			for buffer in self._buffers():
				buffer.upload()
			f.glColorMask(True, True, True, False)  # (the picture stays opaque where see-through zones are drawn)
			self._draw(f)
			f.glColorMask(True, True, True, True)
		self._overlay()

	def _draw(self, f):
		p = self._program
		aspect = self.width() / max(self.height(), 1)
		p.bind()
		p.setUniformValue("matrix", _matrix(self.camera.matrix(aspect)))
		low, high = self._heights
		if self.cut < NO_CUT:
			high = min(high, self.cut)
			low = min(low, high - 1.0)
		p.setUniformValue("heights", QVector2D(low, high))
		p.setUniformValue("cap_colour", QVector3D(*CAP_COLOUR))
		f.glFrontFace(GL_CW)  # (Unity's front faces)
		f.glEnable(GL_DEPTH_TEST)
		f.glDepthFunc(GL_LEQUAL)
		f.glEnable(GL_MULTISAMPLE)
		f.glDisable(GL_BLEND)
		f.glDepthMask(True)
		self._uniforms(cut=self.cut, shading=1, by_height=1, colour=(1, 1, 1, 1), caps=self.cut < NO_CUT)
		if self.show_floor:
			self._triangles(f, self._floor_buffer)
		if self.show_walls:
			self._uniforms(by_height=0, colour=(*WALL_COLOUR, 1.0))
			f.glEnable(GL_POLYGON_OFFSET_FILL)
			f.glPolygonOffset(1.0, 1.0)  # (the floor wins where a wall's floor and the navmesh are at one height)
			self._triangles(f, self._wall_buffer)
			f.glDisable(GL_POLYGON_OFFSET_FILL)
			if self._section_lines.count:
				self._uniforms(cut=NO_CUT, caps=False, shading=0, colour=(*CAP_COLOUR, 1.0))
				self._lines(f, self._section_lines, 0, self._section_lines.count, width=2.5)
		self._uniforms(caps=False)
		f.glEnable(GL_BLEND)
		f.glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		if self.show_areas and self._area_edges.count:
			self._uniforms(cut=NO_CUT, shading=0, by_height=0, colour=(0.8, 0.8, 0.8, 0.5))
			self._lines(f, self._area_edges, 0, self._area_edges.count)
		if self._outline_edges.count:
			self._uniforms(cut=NO_CUT, shading=0, by_height=0, colour=(1.0, 1.0, 1.0, 0.9))
			self._lines(f, self._outline_edges, 0, self._outline_edges.count, width=2.0)
		if self.show_zones and self.zones:
			f.glDepthMask(False)
			for i, (zone, style) in enumerate(self.zones):
				if zone.key == self.selected_key:
					continue
				faces, edges = _ALPHA[style]
				faces *= min(1.0, max(0.12, BIG_ZONE / max(zone.box.size)))  # (a zone over a whole area is barely tinted)
				self._uniforms(cut=self.cut, shading=1, by_height=0, colour=(*_rgb(zone.kind), faces))
				self._triangles(f, self._zone_faces, i * 36, 36)
				self._uniforms(shading=0, colour=(*_rgb(zone.kind), edges))
				self._lines(f, self._zone_edges, i * 24, 24, width=1.5)
			f.glDepthMask(True)
		if self.selected_box is not None:
			rgb = tuple(c / 255 for c in NEW_COLOUR) if self.selected_editable else _rgb(self.selected_kind)
			f.glDepthMask(False)
			self._uniforms(cut=NO_CUT, shading=1, by_height=0, colour=(*rgb, 0.30))
			self._triangles(f, self._selected_faces)
			f.glDisable(GL_DEPTH_TEST)  # (its edges show through walls and floors, faintly)
			self._uniforms(shading=0, colour=(*rgb, 0.35))
			self._lines(f, self._selected_edges, 0, self._selected_edges.count, width=1.5)
			f.glEnable(GL_DEPTH_TEST)
			self._uniforms(colour=(*rgb, 1.0))
			self._lines(f, self._selected_edges, 0, self._selected_edges.count, width=2.5)
			f.glDepthMask(True)
		p.release()

	def _uniforms(self, cut=None, shading=None, by_height=None, colour=None, caps=None):
		p = self._program
		if caps is not None:
			p.setUniformValue1f("caps", 1.0 if caps else 0.0)
		if cut is not None:
			p.setUniformValue1f("cut", float(cut))
		if shading is not None:
			p.setUniformValue1f("shading", float(shading))
		if by_height is not None:
			p.setUniformValue1f("by_height", float(by_height))
		if colour is not None:
			p.setUniformValue("colour", QVector4D(*colour))

	def _bind(self, buffer):
		buffer.buffer.bind()
		self._program.enableAttributeArray(0)
		self._program.setAttributeBuffer(0, GL_FLOAT, 0, 3, 12)

	def _triangles(self, f, buffer, first=0, count=None):
		if buffer.buffer is None or not buffer.count:
			return
		self._bind(buffer)
		f.glDrawArrays(GL_TRIANGLES, first, buffer.count if count is None else count)
		buffer.buffer.release()

	def _lines(self, f, buffer, first, count, width=1.0):
		if buffer.buffer is None or not buffer.count:
			return
		self._bind(buffer)
		f.glLineWidth(width)
		f.glDrawArrays(GL_LINES, first, count)
		buffer.buffer.release()

	# --- what is drawn over the picture -----------------------------------------------------------
	def _overlay(self):
		painter = QPainter(self)
		painter.setRenderHint(QPainter.RenderHint.Antialiasing)
		w, h = self.width(), self.height()
		self._taken = []  # (the label boxes drawn so far: a label that would cover one is left out)
		font = QFont(self.font())
		font.setPointSizeF(max(font.pointSizeF(), 8.5))
		painter.setFont(font)
		if self.gl_problem or self.message:
			painter.setPen(QColor(220, 220, 220))
			painter.drawText(QRectF(20, 20, w - 40, h - 40), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, self.gl_problem or self.message)
			painter.end()
			return
		if self.show_areas:
			for name, box in self.areas:
				self._box_label(painter, box, name, AREA_COLOUR)
		for name, box in self.outlines:
			self._box_label(painter, box, name, QColor(255, 255, 255))
		if self.show_zones and self.show_labels:
			target = np.asarray(self.camera.target)
			shown = [
				(float(np.linalg.norm(np.subtract(z.box.center, target))), z) for z, _s in self.zones
				if z.key != self.selected_key and z.box.center[1] - z.box.size[1] / 2 <= self.cut
			]
			for _d, zone in sorted(shown, key=lambda pair: pair[0])[:MOST_LABELS]:
				top = (zone.box.center[0], zone.box.center[1] + zone.box.size[1] / 2, zone.box.center[2])
				spot = self.camera.project(top, w, h)
				if spot and 0 <= spot[0] <= w and 0 <= spot[1] <= h:
					self._label(painter, spot, zone.label, QColor(*KIND_COLOURS.get(zone.kind, (255, 255, 255))))
		if self.samples:
			pixels, front = self.camera.project_many([point for point, _ok in self.samples], w, h)
			shown = front & (pixels[:, 0] >= 0) & (pixels[:, 0] <= w) & (pixels[:, 1] >= 0) & (pixels[:, 1] <= h)
			reached = np.array([ok for _point, ok in self.samples], dtype=bool)
			painter.setPen(Qt.PenStyle.NoPen)
			for ok, colour in ((True, QColor(60, 220, 90)), (False, QColor(240, 70, 60))):
				painter.setBrush(colour)
				for x, y in pixels[shown & (reached == ok)].tolist():
					painter.drawEllipse(QPointF(x, y), 2.5, 2.5)
		for point, label in self.markers:
			spot = self.camera.project(point, w, h)
			if spot and 0 <= spot[0] <= w and 0 <= spot[1] <= h:
				painter.setPen(QPen(QColor(255, 255, 255), 1.5))
				painter.setBrush(QColor(255, 220, 60))
				painter.drawEllipse(QPointF(*spot), 4, 4)
				self._label(painter, (spot[0], spot[1] - 6), label, QColor(255, 220, 60), always=True)
		if self.selected_box is not None and self.selected_editable:
			self._draw_handles(painter)
		self._compass(painter, w)
		self._status(painter, w, h)
		painter.end()

	def _box_label(self, painter, box, text, colour):
		spot = self.camera.project((box.center[0], box.center[1] + box.size[1] / 2, box.center[2]), self.width(), self.height())
		if spot and 0 <= spot[0] <= self.width() and 0 <= spot[1] <= self.height():
			self._label(painter, spot, text, colour)

	def _label(self, painter, spot, text, colour, always=False):
		metrics = painter.fontMetrics()
		width = metrics.horizontalAdvance(text) + 8
		rect = QRectF(spot[0] - width / 2, spot[1] - metrics.height() - 4, width, metrics.height() + 2)
		taken = getattr(self, "_taken", [])
		if not always and any(rect.intersects(other) for other in taken):
			return
		taken.append(rect)
		painter.setPen(Qt.PenStyle.NoPen)
		painter.setBrush(QColor(0, 0, 0, 150))
		painter.drawRoundedRect(rect, 3, 3)
		painter.setPen(colour)
		painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

	def _draw_handles(self, painter):
		w, h = self.width(), self.height()
		box = self.selected_box
		top = G.add(box.center, G.rotate(box.rotation, (0.0, box.size[1] / 2, 0.0)))
		front = G.add(box.center, G.rotate(box.rotation, (0.0, -box.size[1] / 2, box.size[2] / 2)))
		for handle in H.handles(box):
			spot = self.camera.project(handle.position, w, h)
			if spot is None:
				continue
			start = top if handle.kind == H.LIFT else front if handle.kind == H.TURN else None
			if start is not None:
				base = self.camera.project(start, w, h)
				if base:
					painter.setPen(QPen(QColor(255, 255, 255, 200), 1.5, Qt.PenStyle.DashLine))
					painter.drawLine(QPointF(*base), QPointF(*spot))
			painter.setPen(QPen(QColor(20, 20, 20), 1.5))
			if handle.kind == H.SIZE:
				painter.setBrush(QColor(255, 255, 255))
				painter.drawRect(QRectF(spot[0] - 5, spot[1] - 5, 10, 10))
			elif handle.kind == H.LIFT:
				painter.setBrush(QColor(90, 200, 255))
				painter.drawPolygon([QPointF(spot[0], spot[1] - 8), QPointF(spot[0] - 6, spot[1] + 4), QPointF(spot[0] + 6, spot[1] + 4)])
			else:
				painter.setBrush(QColor(255, 200, 60))
				painter.drawEllipse(QPointF(*spot), 6, 6)

	def _compass(self, painter, w):
		c = self.camera
		here = c.project(c.target, self.width(), self.height())
		north = c.project(G.add(c.target, (0.0, 0.0, c.distance * 0.05)), self.width(), self.height())
		if not here or not north:
			return
		dx, dy = north[0] - here[0], north[1] - here[1]
		length = math.hypot(dx, dy)
		if length < 1e-6:
			return
		dx, dy = dx / length, dy / length
		centre = QPointF(w - 30, 30)
		painter.setPen(QPen(QColor(230, 230, 230), 2))
		painter.drawLine(centre - QPointF(dx * 12, dy * 12), centre + QPointF(dx * 12, dy * 12))
		painter.setBrush(QColor(240, 80, 70))
		tip = centre + QPointF(dx * 14, dy * 14)
		painter.drawEllipse(tip, 3, 3)
		painter.drawText(QRectF(tip.x() + dx * 6 - 8, tip.y() + dy * 8 - 8, 16, 16), Qt.AlignmentFlag.AlignCenter, "N")

	def _status(self, painter, w, h):
		parts = []
		if self.hover_point is not None:
			x, y, z = self.hover_point
			parts.append(f"x {x:.2f}   y {y:.2f}   z {z:.2f}")
		if self.placing:
			parts.append("Click the floor where the new zone goes (Esc to stop)")
		if parts:
			text = "      ".join(parts)
			metrics = painter.fontMetrics()
			rect = QRectF(8, h - metrics.height() - 12, metrics.horizontalAdvance(text) + 16, metrics.height() + 6)
			painter.setPen(Qt.PenStyle.NoPen)
			painter.setBrush(QColor(0, 0, 0, 160))
			painter.drawRoundedRect(rect, 4, 4)
			painter.setPen(QColor(235, 235, 235))
			painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

	# --- the mouse ------------------------------------------------------------------------------------
	def ray_at(self, x, y):
		return self.camera.ray(x, y, self.width(), self.height())

	def ground_at(self, x, y):
		"""The nearest floor or wall under the pixel (a maps.triangles.Hit), below the cut, or None."""
		origin, direction = self.ray_at(x, y)
		cut = None if self.cut >= NO_CUT else self.cut
		hits = [
			t.pick(origin, direction, below=cut)
			for t, shown in ((self.floor, self.show_floor), (self.walls, self.show_walls)) if t is not None and shown
		]
		hits = [hit for hit in hits if hit is not None]
		return min(hits, key=lambda hit: hit.distance) if hits else None

	def zone_at(self, x, y):
		"""The key of the zone under the pixel (the smallest, where several are; one behind a floor or wall doesn't
		count), or None."""
		origin, direction = self.ray_at(x, y)
		ground = self.ground_at(x, y)
		reach = ground.distance + 0.5 if ground is not None else math.inf
		found = []
		candidates = [(z.key, z.box) for z, _s in self.zones] if self.show_zones else []
		if self.selected_box is not None:
			candidates = [c for c in candidates if c[0] != self.selected_key] + [(self.selected_key, self.selected_box)]
		for key, box in candidates:
			if box.center[1] - box.size[1] / 2 > self.cut and key != self.selected_key:
				continue
			t = ray_box(origin, direction, box)
			if t is not None and t <= reach:
				found.append((box.size[0] * box.size[1] * box.size[2], t, key))
		return min(found, key=lambda f: (f[0], f[1]))[2] if found else None

	def handle_at(self, x, y):
		"""The selected zone's handle within a few pixels of (x, y), or None."""
		if self.selected_box is None or not self.selected_editable:
			return None
		best = None
		for handle in H.handles(self.selected_box):
			spot = self.camera.project(handle.position, self.width(), self.height())
			if spot is None:
				continue
			d = math.hypot(spot[0] - x, spot[1] - y)
			if d <= HANDLE_PIXELS and (best is None or d < best[0]):
				best = (d, handle)
		return best[1] if best else None

	def mousePressEvent(self, event):
		self.setFocus()
		pos = event.position()
		self._press = self._last = pos
		self._moved = False
		self._drag = None
		shift = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
		if event.button() == Qt.MouseButton.LeftButton and not self.placing and not shift and self.selected_editable and self.selected_box is not None:
			origin, direction = self.ray_at(pos.x(), pos.y())
			handle = self.handle_at(pos.x(), pos.y())
			if handle is not None:
				self._drag = H.Drag(self.selected_box, handle.kind, origin, direction, handle=handle)
			elif self.zone_at(pos.x(), pos.y()) == self.selected_key:
				t = ray_box(origin, direction, self.selected_box)
				grab = tuple(o + t * d for o, d in zip(origin, direction))
				self._drag = H.Drag(self.selected_box, H.MOVE, origin, direction, grab=grab)
			if self._drag is not None and not self._drag.ok:
				self._drag = None
		event.accept()

	def mouseMoveEvent(self, event):
		pos = event.position()
		buttons = event.buttons()
		if not buttons:
			self._hover_pos = pos
			self._hover_timer.start()
			return
		if self._press is None:
			return
		if abs(pos.x() - self._press.x()) + abs(pos.y() - self._press.y()) > 3:
			self._moved = True
		if not self._moved:
			return
		dx, dy = pos.x() - self._last.x(), pos.y() - self._last.y()
		self._last = pos
		shift = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
		if self._drag is not None:
			box = self._drag.box_at(*self.ray_at(pos.x(), pos.y()), snap=shift)
			self.selected_box = box
			self._selected_changed()
			self.box_changing.emit(box)
			return
		if buttons & Qt.MouseButton.LeftButton and not shift and not self.camera.top_down:
			self.camera.orbit(dx * 0.4, dy * 0.3)
		else:
			self.camera.pan(dx, dy, self.height())
			self.keep_on_map()
		self.update()

	def mouseReleaseEvent(self, event):
		pos = event.position()
		drag, self._drag = self._drag, None
		if drag is not None and self._moved:
			self.box_edited.emit(self.selected_box)
		elif not self._moved and event.button() == Qt.MouseButton.LeftButton:
			self.click(pos.x(), pos.y())
		self._press = None

	def click(self, x, y):
		"""A click (no drag) at the pixel (x, y): place the new zone there, or select the zone there."""
		if self.placing:
			hit = self.ground_at(x, y)
			if hit is not None:
				self.place_requested.emit(hit.point)
			return
		self.zone_clicked.emit(self.zone_at(x, y))

	def mouseDoubleClickEvent(self, event):
		pos = event.position()
		hit = self.ground_at(pos.x(), pos.y())
		if hit is not None and not self.placing:
			self.camera.target = hit.point
			self.update()

	def wheelEvent(self, event):
		steps = event.angleDelta().y() / 120.0
		if not steps:
			return
		pos = event.position()
		toward = None
		if self.camera.top_down:
			origin, direction = self.ray_at(pos.x(), pos.y())
			toward = H.on_level(origin, direction, self.camera.target[1])
		else:
			hit = self.ground_at(pos.x(), pos.y())
			toward = hit.point if hit is not None else None
		self.camera.zoom(0.85 ** steps, toward=toward)
		self.keep_on_map()
		self.update()

	def keyPressEvent(self, event):
		key = event.key()
		if key == Qt.Key.Key_Escape and self.placing:
			self.set_placing(False)
		elif key == Qt.Key.Key_F:
			if self.selected_box is not None:
				self.look_at_box(self.selected_box)
			else:
				self.look_at_everything()
		elif key == Qt.Key.Key_T:
			self.set_top_down(not self.camera.top_down)
		elif key == Qt.Key.Key_Delete and self.selected_editable:
			self.delete_requested.emit()
		else:
			super().keyPressEvent(event)

	def leaveEvent(self, event):
		self._hover_timer.stop()
		if self.hover_point is not None:
			self.hover_point = None
			self.hovered.emit(None)
			self.update()
		super().leaveEvent(event)

	def _hover(self):
		if self._hover_pos is None:
			return
		hit = self.ground_at(self._hover_pos.x(), self._hover_pos.y())
		self.hover_point = hit.point if hit is not None else None
		self.hovered.emit(self.hover_point)
		self.update()

