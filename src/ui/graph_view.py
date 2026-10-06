"""The quest graph, drawn: a zoomable, pannable view of quest cards and the links between them.

How much of a quest is drawn depends on the zoom: a card (name, trader, level) when it is big enough to read, a coloured bar with
its name a little smaller, and a dot when the whole graph is in view. Colour is the trader; the border says where the quest is
from (thick: yours, dashed: a reference file, thin: the base game, dotted: nobody has it).
"""

import math

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QFontMetrics, QMouseEvent, QPainter, QPainterPath, QPen, QPolygonF
from PySide6.QtWidgets import QApplication, QGraphicsItem, QGraphicsRectItem, QGraphicsScene, QGraphicsSimpleTextItem, QGraphicsView

from core import questgraph as G

COLUMN_WIDTH, ROW_HEIGHT = 250.0, 66.0  # (one grid unit of the layout, in scene units)
CARD_WIDTH, CARD_HEIGHT = 190.0, 46.0
PILL_ZOOM, CARD_ZOOM = 0.28, 0.55  # (below the first: a dot; below the second: a bar)
MIN_ZOOM, MAX_ZOOM = 0.02, 2.5
DOT_MAX = 130.0  # (the biggest a dot gets, in scene units)
FAILS_COLOR = QColor("#E24B4A")

# distinct hues for the traders (assigned in order of how many quests each has; more traders than colours repeat with a lighter shade)
HUES = (30, 175, 275, 5, 215, 95, 330, 50, 245, 150, 15, 300)


def trader_colors(trader_ids):
	"""{trader id: hue (0-359)}: the traders with the most quests get the first colours. '' (no trader) is grey (-1)."""
	colors = {"": -1}
	for n, trader in enumerate(t for t in trader_ids if t):
		colors[trader] = HUES[n % len(HUES)]
	return colors


def swatch(hue, dark):
	"""(fill, border, text) colours for a quest of this hue (-1: grey)."""
	s = 0.0 if hue < 0 else 0.55
	h = max(hue, 0) / 360
	if dark:
		return QColor.fromHslF(h, s, 0.24), QColor.fromHslF(h, s, 0.62), QColor.fromHslF(h, s * 0.5, 0.9)
	return QColor.fromHslF(h, s, 0.9), QColor.fromHslF(h, s * 1.2 if s else 0, 0.38), QColor.fromHslF(h, s, 0.16)


def _html(node, trader, needs, opens, fails):
	lines = [f"<b>{_esc(node.label)}</b>"]
	lines.append(f"{_esc(trader) or 'No trader'} &middot; {_esc(node.where)}")
	lines.extend(_esc(n) for n in node.notes)
	if node.also_in:
		lines.append("Also in: " + _esc(", ".join(node.also_in)))
	counts = [f"needs {needs}" if needs else "", f"opens {opens}" if opens else "", f"fails with {fails}" if fails else ""]
	if any(counts):
		lines.append(", ".join(c for c in counts if c).capitalize())
	return "<br>".join(lines)


def _esc(text):
	return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class QuestItem(QGraphicsItem):
	"""One quest."""

	def __init__(self, node, trader_name, hue, dark, tip):
		super().__init__()
		self.node, self.trader_name, self.hue, self.dark = node, trader_name, hue, dark
		self.fill, self.border, self.text = swatch(hue, dark)
		self.hover = False
		self.edges = []
		self.setAcceptHoverEvents(True)
		self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
		self.setToolTip(tip)

	def boundingRect(self):
		return QRectF(-DOT_MAX - 3, -DOT_MAX - 3, CARD_WIDTH + 2 * DOT_MAX + 6, CARD_HEIGHT + 2 * DOT_MAX + 6)  # (room for the big dot of a far-out view)

	def zoom(self):
		"""How far the view this is drawn in is zoomed in (1 when it isn't in one)."""
		scene = self.scene()
		views = scene.views() if scene is not None else []
		return views[0].transform().m11() if views else 1.0

	def shape(self):
		"""What the mouse can hit: only what is drawn (the card, or the dot when far out), not all the room the dot may need."""
		path = QPainterPath()
		if self.zoom() < PILL_ZOOM:
			radius = min(DOT_MAX, 4.5 / max(self.zoom(), 0.001))
			path.addEllipse(QPointF(CARD_WIDTH / 2, CARD_HEIGHT / 2), radius, radius)
		else:
			path.addRoundedRect(QRectF(0, 0, CARD_WIDTH, CARD_HEIGHT), 7, 7)
		return path

	def center(self):
		return self.pos() + QPointF(CARD_WIDTH / 2, CARD_HEIGHT / 2)

	def _pen(self, width_px):
		pen = QPen(self.border)
		pen.setCosmetic(True)
		node = self.node
		if node.source == G.OPEN:
			pen.setWidthF(width_px * 2)
		elif node.source == G.REFERENCE:
			pen.setWidthF(width_px)
			pen.setStyle(Qt.PenStyle.DashLine)
		elif node.source == G.UNKNOWN:
			pen.setWidthF(width_px)
			pen.setStyle(Qt.PenStyle.DotLine)
		else:
			pen.setWidthF(width_px * 0.7)
		if self.isSelected() or self.hover:
			pen.setColor(self.text)
			pen.setWidthF(max(pen.widthF(), 2.5))
		return pen

	def paint(self, painter, option, widget=None):
		lod = option.levelOfDetailFromTransform(painter.worldTransform())
		node, rect = self.node, QRectF(0, 0, CARD_WIDTH, CARD_HEIGHT)
		unknown = node.source == G.UNKNOWN
		fill = QColor(self.fill)
		if unknown:
			fill.setAlphaF(0.35)
		if lod < PILL_ZOOM:  # (a dot, as big as a few pixels whatever the zoom)
			radius = min(DOT_MAX, 4.5 / max(lod, 0.001))
			painter.setBrush(QBrush(self.border if not unknown else fill))
			painter.setPen(QPen(self.text, 1.5) if self.isSelected() else Qt.PenStyle.NoPen)
			painter.drawEllipse(rect.center(), radius, radius)
			return
		painter.setRenderHint(QPainter.RenderHint.Antialiasing)
		painter.setBrush(QBrush(fill))
		painter.setPen(self._pen(1.2))
		painter.drawRoundedRect(rect, 7, 7)
		painter.setPen(self.text)
		if lod < CARD_ZOOM:  # (a bar with the name, big enough to read at this size)
			font = QFont(painter.font())
			font.setPixelSize(int(CARD_HEIGHT * 0.45))
			painter.setFont(font)
			metrics = QFontMetrics(font)
			painter.drawText(rect.adjusted(10, 0, -8, 0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, metrics.elidedText(node.label, Qt.TextElideMode.ElideRight, int(CARD_WIDTH - 18)))
			return
		title = QFont(painter.font())
		title.setPixelSize(15)
		title.setBold(True)
		painter.setFont(title)
		painter.drawText(QRectF(10, 4, CARD_WIDTH - 18, 22), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, QFontMetrics(title).elidedText(node.label, Qt.TextElideMode.ElideRight, int(CARD_WIDTH - 20)))
		small = QFont(painter.font())
		small.setPixelSize(12)
		small.setBold(False)
		painter.setFont(small)
		parts = [self.trader_name or ("not found" if unknown else "no trader")]
		if node.level is not None:
			parts.append(f"Lv {node.level}")
		painter.setPen(self.border if not self.dark else self.text)
		painter.drawText(QRectF(10, 25, CARD_WIDTH - 18, 18), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, QFontMetrics(small).elidedText(" · ".join(parts), Qt.TextElideMode.ElideRight, int(CARD_WIDTH - 20)))

	def hoverEnterEvent(self, event):
		self.hover = True
		self.update()
		for edge in self.edges:
			edge.update()

	def hoverLeaveEvent(self, event):
		self.hover = False
		self.update()
		for edge in self.edges:
			edge.update()

	def mouseDoubleClickEvent(self, event):
		scene = self.scene()
		if scene is not None:
			scene.activated.emit(self.node.id)
		super().mouseDoubleClickEvent(event)


class EdgeItem(QGraphicsItem):
	"""One link: a curve from the right of the quest that is needed to the left of the quest that needs it."""

	def __init__(self, edge, source, target, dark):
		super().__init__()
		self.edge, self.source, self.target, self.dark = edge, source, target, dark
		self.setZValue(-1)
		self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
		self.setToolTip(f"{_esc(source.node.label)} → {_esc(target.node.label)}: " + (G.KIND_LABEL[G.FAILS] if edge.kind == G.FAILS else edge.words()) + (" (needed to finish)" if edge.list == G.FINISH else ""))
		self._path = None
		source.edges.append(self)
		target.edges.append(self)

	def _build(self):
		start = self.source.pos() + QPointF(CARD_WIDTH, CARD_HEIGHT / 2)
		end = self.target.pos() + QPointF(0, CARD_HEIGHT / 2)
		reach = max(40.0, min(abs(end.x() - start.x()) / 2, 160.0))
		path = QPainterPath(start)
		if end.x() > start.x():
			path.cubicTo(start + QPointF(reach, 0), end - QPointF(reach, 0), end)
		else:  # (back or sideways: swing out around)
			path.cubicTo(start + QPointF(reach + 60, 0), end - QPointF(reach + 60, 0), end)
		self._path = path
		return path

	def boundingRect(self):
		path = self._path or self._build()
		return path.boundingRect().adjusted(-14, -14, 14, 14)

	def _style(self):
		edge = self.edge
		color = QColor("#9a9a94") if not self.dark else QColor("#8a8a85")
		style, width = Qt.PenStyle.SolidLine, 1.3
		if edge.kind == G.FAILS:
			color, style, width = FAILS_COLOR, Qt.PenStyle.DotLine, 1.6
		elif edge.list == G.FINISH:
			style, width = Qt.PenStyle.DotLine, 1.0
		elif edge.kind == G.STARTED:
			style = Qt.PenStyle.DashLine
		elif edge.kind == G.FAILED:
			style = Qt.PenStyle.DashDotLine
		elif edge.kind == G.ANY:
			style = Qt.PenStyle.DashLine
			color = QColor("#7f77dd")
		if self.source.hover or self.target.hover or self.source.isSelected() or self.target.isSelected():
			color, width = (QColor("#f2f2ee") if self.dark else QColor("#222")), width + 0.8
		return color, style, width

	def paint(self, painter, option, widget=None):
		lod = option.levelOfDetailFromTransform(painter.worldTransform())
		path = self._path or self._build()
		color, style, width = self._style()
		pen = QPen(color, width if lod >= 0.12 else 0.6, style)
		pen.setCosmetic(True)
		painter.setRenderHint(QPainter.RenderHint.Antialiasing)
		painter.setBrush(Qt.BrushStyle.NoBrush)
		painter.setPen(pen)
		painter.drawPath(path)
		if lod >= 0.3:
			end = path.pointAtPercent(1.0)
			angle = math.radians(path.angleAtPercent(1.0))
			size = 10.0 / max(lod, 0.3) * 0.55 + 4
			back = QPointF(math.cos(angle), -math.sin(angle))
			side = QPointF(-back.y(), back.x())
			tip = QPolygonF([end, end - back * size + side * size * 0.45, end - back * size - side * size * 0.45])
			painter.setBrush(QBrush(color))
			painter.setPen(Qt.PenStyle.NoPen)
			painter.drawPolygon(tip)
		if lod >= 0.5 and self.edge.wait:
			middle = path.pointAtPercent(0.5)
			font = QFont(painter.font())
			font.setPixelSize(11)
			painter.setFont(font)
			painter.setPen(color)
			painter.drawText(middle + QPointF(4, -4), "wait " + G.wait_words(self.edge.wait))


class GraphScene(QGraphicsScene):
	activated = Signal(str)  # a quest was double-clicked

	def __init__(self, graph, layout, trader_names, hues, dark):
		super().__init__()
		self.items_by_id, self.edge_items, self.dark = {}, [], dark
		degrees = {}
		for edge in graph.edges:
			degrees.setdefault(edge.target, [0, 0, 0])
			degrees.setdefault(edge.source, [0, 0, 0])
			if edge.kind == G.FAILS:
				degrees[edge.source][2] += 1
				degrees[edge.target][2] += 1
			else:
				degrees[edge.target][0] += 1
				degrees[edge.source][1] += 1
		for lane, first, last in layout.lanes:
			band = QGraphicsRectItem(-30, first * ROW_HEIGHT - 52, max(layout.columns, 1) * COLUMN_WIDTH + 30, (last - first) * ROW_HEIGHT + CARD_HEIGHT + 76)
			band.setBrush(QBrush(QColor(255, 255, 255, 14) if dark else QColor(0, 0, 0, 10)))
			band.setPen(QPen(Qt.PenStyle.NoPen))
			band.setZValue(-3)
			self.addItem(band)
			label = QGraphicsSimpleTextItem(trader_names.get(lane, "") or "No trader")
			font = QFont()
			font.setPixelSize(26)
			font.setBold(True)
			label.setFont(font)
			label.setBrush(QBrush(QColor(swatch(hues.get(lane, -1), dark)[1])))
			label.setPos(-20, first * ROW_HEIGHT - 50)
			label.setZValue(-2)
			self.addItem(label)
		for quest_id, node in graph.nodes.items():
			column, row = layout.positions[quest_id]
			needs, opens, fails = degrees.get(quest_id, (0, 0, 0))
			item = QuestItem(node, trader_names.get(node.trader, ""), hues.get(node.trader, -1), dark, _html(node, trader_names.get(node.trader, ""), needs, opens, fails))
			item.setPos(column * COLUMN_WIDTH, row * ROW_HEIGHT)
			self.addItem(item)
			self.items_by_id[quest_id] = item
		for edge in graph.edges:
			if edge.source in self.items_by_id and edge.target in self.items_by_id:
				item = EdgeItem(edge, self.items_by_id[edge.source], self.items_by_id[edge.target], dark)
				self.addItem(item)
				self.edge_items.append(item)
		self.setSceneRect(QRectF(-60, -90, max(layout.columns, 1) * COLUMN_WIDTH + 120, max(layout.rows, 0) * ROW_HEIGHT + CARD_HEIGHT + 120))

	def show_kinds(self, fails=True, finish=True):
		"""Show or hide the links that make a quest fail, and the ones that are only needed to finish."""
		for item in self.edge_items:
			edge = item.edge
			item.setVisible(not ((edge.kind == G.FAILS and not fails) or (edge.list == G.FINISH and edge.kind != G.FAILS and not finish)))

	def highlight(self, ids):
		"""Dim everything but these quests (None: nothing is dimmed)."""
		for quest_id, item in self.items_by_id.items():
			item.setOpacity(1.0 if ids is None or quest_id in ids else 0.18)
		for item in self.edge_items:
			item.setOpacity(1.0 if ids is None or (item.edge.source in ids and item.edge.target in ids) else 0.08)


class GraphView(QGraphicsView):
	"""Shows a GraphScene. Wheel zooms, dragging pans, double-click on a quest asks for it to be opened."""

	# Dragging always moves the view, even when it starts on a quest (the quest is not selected by it). Set this to True to let a
	# press on a quest act on the quest instead (so a drag that starts on one does not pan).
	ITEMS_BLOCK_PANNING = False

	node_selected = Signal(str)  # the id of the selected quest, '' when none
	node_activated = Signal(str)

	def __init__(self, parent=None):
		super().__init__(parent)
		self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
		self.setDragMode(QGraphicsView.DragMode.NoDrag)  # (panning is done below, so it works over a quest too)
		self.viewport().setCursor(Qt.CursorShape.OpenHandCursor)
		self._press = None  # (the left press that may become a click or a pan: the event, then where the scroll bars were)
		self._panning = False
		self._padding = False
		self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
		self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
		self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)
		self.setFrameShape(QGraphicsView.Shape.StyledPanel)
		self.graph_scene = None

	@property
	def dark(self):
		return self.palette().window().color().lightness() < 128

	def show_graph(self, graph, layout, trader_names, hues, fit=True):
		old = self.graph_scene
		if old is not None:  # (it is going away: what happens to its selection then is nobody's business)
			old.selectionChanged.disconnect(self._selection_changed)
			old.activated.disconnect(self.node_activated)
		self.graph_scene = GraphScene(graph, layout, trader_names, hues, self.dark)
		self.graph_scene.selectionChanged.connect(self._selection_changed)
		self.graph_scene.activated.connect(self.node_activated)
		self.setSceneRect(QRectF())  # (the room the last picture had is not this one's)
		self.setScene(self.graph_scene)
		if old is not None:
			old.deleteLater()
		if fit:
			self.fit()
		else:
			self._pad()

	def _selection_changed(self):
		scene = self.graph_scene
		if scene is None:
			return
		try:
			for edge in scene.edge_items:  # (a link next to the selected quest is drawn darker)
				edge.update()
			chosen = scene.selectedItems()
		except RuntimeError:  # (the scene is already gone: the program is closing)
			return
		self.node_selected.emit(chosen[0].node.id if chosen else "")

	def zoom(self):
		return self.transform().m11()

	def zoom_by(self, factor):
		target = min(MAX_ZOOM, max(MIN_ZOOM, self.zoom() * factor))
		self.scale(target / self.zoom(), target / self.zoom())
		self._pad()

	def mousePressEvent(self, event):
		if event.button() != Qt.MouseButton.LeftButton or (self.ITEMS_BLOCK_PANNING and self.itemAt(event.position().toPoint()) is not None):
			self._press = None
			super().mousePressEvent(event)
			return
		# Not given to the scene yet: it is a click if the mouse is let go without moving, and a pan if it moves.
		self._press = (QMouseEvent(event), self.horizontalScrollBar().value(), self.verticalScrollBar().value())
		self._panning = False
		event.accept()

	def mouseMoveEvent(self, event):
		if self._press is None or not (event.buttons() & Qt.MouseButton.LeftButton):
			super().mouseMoveEvent(event)
			return
		first, x, y = self._press
		moved = event.position().toPoint() - first.position().toPoint()
		if not self._panning and moved.manhattanLength() < QApplication.startDragDistance():
			return
		if not self._panning:
			self._panning = True
			self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
		self.horizontalScrollBar().setValue(x - moved.x())
		self.verticalScrollBar().setValue(y - moved.y())
		event.accept()

	def mouseReleaseEvent(self, event):
		press, panned, self._press, self._panning = self._press, self._panning, None, False
		if press is None or event.button() != Qt.MouseButton.LeftButton:
			super().mouseReleaseEvent(event)
			return
		self.viewport().setCursor(Qt.CursorShape.OpenHandCursor)
		if not panned:  # (a click after all: the scene gets it now)
			super().mousePressEvent(press[0])
			super().mouseReleaseEvent(event)
		event.accept()

	def mouseDoubleClickEvent(self, event):
		self._press = None
		super().mouseDoubleClickEvent(event)

	def wheelEvent(self, event):
		self.zoom_by(1.0015 ** event.angleDelta().y())

	def fit(self):
		"""Zoom so everything is in view (never bigger than life size)."""
		if self.graph_scene is None:
			return
		self.resetTransform()
		self.fitInView(self.graph_scene.itemsBoundingRect().adjusted(-40, -40, 40, 40), Qt.AspectRatioMode.KeepAspectRatio)
		if self.zoom() > 1.0:
			self.resetTransform()
		elif self.zoom() < MIN_ZOOM:
			self.zoom_by(MIN_ZOOM / self.zoom())
		self._pad()

	def _pad(self):
		"""Give the view room to move: half a screen beyond the drawing on every side, so any quest can be brought to the middle (also when all of it is in view)."""
		scene = self.graph_scene
		if scene is None or self._padding:
			return
		self._padding = True
		try:
			middle = self.mapToScene(self.viewport().rect().center())  # (what is in the middle stays there)
			across, down = self.viewport().width() / 2 / self.zoom(), self.viewport().height() / 2 / self.zoom()
			self.setSceneRect(scene.sceneRect().adjusted(-across, -down, across, down))
			self.centerOn(middle)
		finally:
			self._padding = False

	def resizeEvent(self, event):
		super().resizeEvent(event)
		self._pad()

	def select(self, quest_id, center=True):
		"""Select this quest (and bring it to the middle). False if it isn't drawn."""
		item = self.graph_scene.items_by_id.get(quest_id) if self.graph_scene else None
		if item is None:
			return False
		self.graph_scene.clearSelection()
		item.setSelected(True)
		if center:
			self.centerOn(item)
		return True
