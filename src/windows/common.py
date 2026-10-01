import logging

log = logging.getLogger(__name__)


def safe_file_dialog(method, window_title):
	try:
		result = method(caption=window_title)
		if isinstance(result, tuple) and len(result) == 2:
			filename, ok = result
		elif result:
			filename, ok = result, True
		else:
			# None, or "" (what a cancelled folder dialog returns)
			return None, False
		if ok:
			return filename, ok
		else:
			return None, False
	except Exception as e:
		log.error(f"Error opening file dialog: {e}")
		return None, False
