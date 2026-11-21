"""The 3D view of a map (view.py), its camera (camera.py) and the handles of the zone being edited (handles.py)."""

import os


def choose_opengl(software=False):
	"""Pick how OpenGL is drawn, before the QApplication is made: on the graphics card, or in software when asked (the
	Settings > General choice). Qt on its own falls back to software on some PCs whose graphics card works fine (one
	with two graphics chips, for one), which makes the 3D view slow. A QT_OPENGL the user has set is left alone."""
	if "QT_OPENGL" not in os.environ:
		os.environ["QT_OPENGL"] = "software" if software else "desktop"
