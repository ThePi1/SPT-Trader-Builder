import logging

log = logging.getLogger(__name__)


def safe_file_dialog(method, window_title):
	"""Run a QFileDialog static method. Returns (path, True) if something was chosen, else (None, False)."""
	try:
		result = method(caption=window_title)
		# getOpenFileName / getSaveFileName return (path, selected_filter); getExistingDirectory
		# returns just the path. A cancelled dialog gives an empty path ("") or None.
		path = result[0] if isinstance(result, tuple) else result
		if path:
			return path, True
		return None, False
	except Exception as e:
		log.error(f"Error opening file dialog: {e}")
		return None, False
