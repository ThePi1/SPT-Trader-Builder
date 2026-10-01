"""Checking whether a newer version of the tool has been released."""

import logging

import requests

from paths import APP_DIR

log = logging.getLogger(__name__)


def get_version_from_file(config):
	with open(APP_DIR / config.version_file) as local_version_file:
		return local_version_file.read()


def get_version_from_remote(config):
	try:
		return requests.get(config.version_url).text
	except Exception:
		log.error("Error fetching remote version")
		return ""


def get_update_stats(config):
	"""Returns (local_version, latest_version, update_text, project_url)."""
	latest_version = get_version_from_remote(config)
	local_version = get_version_from_file(config)
	if local_version != latest_version:
		update_text = "Program may be out of date!"
	else:
		update_text = "Up to date."
	return (local_version, latest_version, update_text, config.project_url)
