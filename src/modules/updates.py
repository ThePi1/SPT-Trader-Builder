"""Checking whether a newer version of the tool has been released.

The network check runs on a worker thread (``UpdateCheckWorker``) so a slow or
missing connection never delays the window appearing.
"""

import logging
from dataclasses import dataclass

import requests
from PySide6.QtCore import QObject, QRunnable, Signal

from modules.paths import APP_DIR

log = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 5

CHECKING = "checking"
UP_TO_DATE = "up_to_date"
OUTDATED = "outdated"
UNKNOWN = "unknown"  # couldn't reach the server (offline, timeout, bad response)

_STATE_TEXT = {
	CHECKING: "Checking for updates...",
	UP_TO_DATE: "Up to date.",
	OUTDATED: "Program may be out of date!",
	UNKNOWN: "Could not check for updates.",
}


@dataclass(frozen=True)
class UpdateStatus:
	local_version: str
	latest_version: str  # "" unless the check succeeded
	state: str
	project_url: str

	@property
	def text(self):
		return _STATE_TEXT[self.state]

	@property
	def latest_display(self):
		return self.latest_version or "unknown"


def read_local_version(config):
	try:
		with open(APP_DIR / config.version_file, encoding="utf-8") as f:
			return f.read().strip()
	except OSError as e:
		log.error(f"Could not read the local version file: {e}")
		return "unknown"


def fetch_remote_version(config):
	"""The latest released version, or None if it couldn't be fetched."""
	try:
		response = requests.get(config.version_url, timeout=REQUEST_TIMEOUT_SECONDS)
		response.raise_for_status()
		return response.text.strip()
	except requests.RequestException as e:
		log.warning(f"Could not fetch the latest version: {e}")
		return None


def pending_status(config):
	"""Status to show before the network check has finished."""
	return UpdateStatus(read_local_version(config), "", CHECKING, config.project_url)


def check_for_updates(config):
	"""Blocking check. Don't call this on the GUI thread."""
	local = read_local_version(config)
	latest = fetch_remote_version(config)
	if latest is None:
		state, latest = UNKNOWN, ""
	elif latest == local:
		state = UP_TO_DATE
	else:
		state = OUTDATED
	return UpdateStatus(local, latest, state, config.project_url)


class _WorkerSignals(QObject):
	finished = Signal(object)  # UpdateStatus


class UpdateCheckWorker(QRunnable):
	"""Run with ``QThreadPool.globalInstance().start(worker)``; connect to ``worker.signals.finished``."""

	def __init__(self, config):
		super().__init__()
		self.setAutoDelete(False)  # the window keeps the worker (and its signals) alive
		self.config = config
		self.stale = False  # set when a newer check has been started; the result is dropped
		self.signals = _WorkerSignals()

	def run(self):
		try:
			status = check_for_updates(self.config)
		except Exception:
			log.exception("Update check failed")
			status = UpdateStatus(
				read_local_version(self.config), "", UNKNOWN, self.config.project_url
			)
		if not self.stale:
			try:
				self.signals.finished.emit(status)
			except RuntimeError:
				# the window (and with it the signal object) was closed before the check finished;
				# there is nobody left to tell
				log.debug("Update check finished after the window was closed")
