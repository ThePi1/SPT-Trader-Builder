"""Top-down pictures of part of a map: the walkable floor shaded by height, the quest zones as outlines with their ids,
and a metre grid with coordinates. Drawn with Qt off screen (no window), saved as PNG."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
if os.name == "nt":
	os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QGuiApplication, QImage, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QApplication

from maps.zones import KIND_COLOURS as _KIND_RGB, NEW_COLOUR as _NEW_RGB

KIND_COLOURS = {kind: QColor(*rgb) for kind, rgb in _KIND_RGB.items()}
NEW = QColor(*_NEW_RGB)


def _app():
	# (a QApplication, not a bare QGuiApplication: a widget made later in the same process, as in the app's tests,
	# needs one, and an existing application is reused)
	return QGuiApplication.instance() or QApplication([])


def _height_colour(h, low, high):
	"""Dark blue (low) to light yellow (high)."""
	t = 0.5 if high - low < 1e-6 else max(0.0, min(1.0, (h - low) / (high - low)))
	return QColor(int(30 + 200 * t), int(50 + 180 * t), int(110 - 40 * t))


def render(path, navmesh, zones, center, radius=40.0, size=900, floor=None, highlight=(), labels=True, areas=()):
	"""Draw the square of 2 * radius metres around center (x, z) to the PNG at path.

	floor (a height) shows only the floor within 2.5 m of it, for one storey of a building; zones are maps.zones.Zone;
	highlight is ids drawn thicker (a zone being made or checked); areas are maps.mapdata areas, outlined."""
	_app()
	cx, cz = center
	scale = size / (2 * radius)
	image = QImage(size, size + 28, QImage.Format.Format_RGB32)
	image.fill(QColor(24, 24, 28))
	p = QPainter(image)
	p.setRenderHint(QPainter.RenderHint.Antialiasing)

	def to_px(x, z):  # (north is up, east is right)
		return QPointF((x - cx) * scale + size / 2, (cz - z) * scale + size / 2)

	x0, z0, x1, z1 = cx - radius, cz - radius, cx + radius, cz + radius
	polys = navmesh.polygons_near(x0, z0, x1, z1) if navmesh is not None else []
	drawn = []
	for index in polys:
		corners = navmesh.outline(index)
		height = sum(c[1] for c in corners) / len(corners)
		if floor is not None and abs(height - floor) > 2.5:
			continue
		drawn.append((height, corners))
	if drawn:
		low, high = min(d[0] for d in drawn), max(d[0] for d in drawn)
		for height, corners in sorted(drawn, key=lambda d: d[0]):
			colour = _height_colour(height, low, high)
			p.setPen(QPen(colour.darker(130), 0.5))
			p.setBrush(QBrush(colour))
			p.drawPolygon(QPolygonF([to_px(c[0], c[2]) for c in corners]))
	else:
		low = high = 0.0

	# a grid every 10 m (5 m when close in), with its coordinates
	step = 5 if radius <= 30 else 10 if radius <= 80 else 50
	p.setFont(QFont("Segoe UI", 8))
	grid = QPen(QColor(255, 255, 255, 40), 1)
	for gx in range(int(x0 // step) * step, int(x1) + step, step):
		p.setPen(grid)
		p.drawLine(to_px(gx, z0), to_px(gx, z1))
		p.setPen(QColor(200, 200, 200))
		p.drawText(to_px(gx, z1) + QPointF(2, 12), str(gx))
	for gz in range(int(z0 // step) * step, int(z1) + step, step):
		p.setPen(grid)
		p.drawLine(to_px(x0, gz), to_px(x1, gz))
		p.setPen(QColor(200, 200, 200))
		p.drawText(to_px(x0, gz) + QPointF(2, -2), str(gz))

	for area in areas:
		(ax0, _ay0, az0), (ax1, _ay1, az1) = area["min"], area["max"]
		if ax1 < x0 or ax0 > x1 or az1 < z0 or az0 > z1:
			continue
		p.setPen(QPen(QColor(255, 255, 255, 110), 1, Qt.PenStyle.DashLine))
		p.setBrush(Qt.BrushStyle.NoBrush)
		p.drawRect(QRectF(to_px(ax0, az1), to_px(ax1, az0)))
		p.drawText(to_px(ax0, az1) + QPointF(3, 12), area["name"])

	for zone in zones:
		outline = zone.box.footprint()
		if all(px < x0 or px > x1 or pz < z0 or pz > z1 for px, pz in outline):
			continue
		colour = NEW if zone.source == "(new)" else KIND_COLOURS.get(zone.kind, QColor(255, 255, 255))
		thick = zone.id in highlight or zone.source == "(new)"
		p.setPen(QPen(colour, 3 if thick else 1.5, Qt.PenStyle.SolidLine if zone.source == "game" or thick else Qt.PenStyle.DashLine))
		fill = QColor(colour)
		fill.setAlpha(70 if thick else 35)
		p.setBrush(QBrush(fill))
		p.drawPolygon(QPolygonF([to_px(px, pz) for px, pz in outline]))
		if labels:
			c = zone.box.center
			p.setPen(QColor(255, 255, 255))
			p.drawText(to_px(c[0], c[2]) + QPointF(4, -4), f"{zone.id} ({c[1]:.1f})")

	# the key along the bottom
	p.setPen(QColor(220, 220, 220))
	key = f"centre {cx:.1f}, {cz:.1f}  |  {2 * radius:.0f} m across, north up  |  floor {low:.1f} m (dark) to {high:.1f} m (light)"
	if floor is not None:
		key += f"  |  only floor near {floor:.1f} m"
	p.drawText(QPointF(6, size + 18), key + "  |  zones: blue visit, orange placeitem, purple trigger, red flare; dashed = custom")
	p.end()
	image.save(str(path))
	return path
