import html
import logging
import re

log = logging.getLogger(__name__)


def fill_placeholders(template, values):
	"""Replace placeholder words in an HTML template ({placeholder: value}) with their values.

	Values are inserted as plain text (HTML-escaped, nothing in them is treated as markup or
	as a replacement pattern), and in a single pass so a value can't be substituted again.
	"""
	pattern = re.compile("|".join(re.escape(name) for name in values))
	return pattern.sub(lambda m: html.escape(str(values[m.group(0)]), quote=True), template)


def safe_file_dialog(method, window_title, **options):
	"""Run a QFileDialog static method. Returns (path, True) if something was chosen, else (None, False).

	options are passed on to it, e.g. dir= to start at a particular file or folder.
	"""
	try:
		result = method(caption=window_title, **options)
		# getOpenFileName / getSaveFileName return (path, selected_filter); getExistingDirectory
		# returns just the path. A cancelled dialog gives an empty path ("") or None.
		path = result[0] if isinstance(result, tuple) else result
		if path:
			return path, True
		return None, False
	except Exception as e:
		log.error(f"Error opening file dialog: {e}")
		return None, False
