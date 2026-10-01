import requests

import updates
from config import load_config


class FakeResponse:
	def __init__(self, text="", error=None):
		self.text = text
		self._error = error

	def raise_for_status(self):
		if self._error:
			raise self._error


def _local_version():
	return updates.read_local_version(load_config())


def test_up_to_date(monkeypatch):
	monkeypatch.setattr(requests, "get", lambda url, timeout: FakeResponse(_local_version() + "\n"))
	status = updates.check_for_updates(load_config())
	assert status.state == updates.UP_TO_DATE
	assert status.text == "Up to date."


def test_outdated(monkeypatch):
	monkeypatch.setattr(requests, "get", lambda url, timeout: FakeResponse("99.0.0"))
	status = updates.check_for_updates(load_config())
	assert status.state == updates.OUTDATED
	assert status.latest_version == "99.0.0"


def test_offline_is_unknown_not_outdated(monkeypatch):
	def boom(url, timeout):
		raise requests.ConnectionError("offline")

	monkeypatch.setattr(requests, "get", boom)
	status = updates.check_for_updates(load_config())
	assert status.state == updates.UNKNOWN
	assert status.latest_display == "unknown"


def test_http_error_is_unknown(monkeypatch):
	monkeypatch.setattr(
		requests, "get", lambda url, timeout: FakeResponse("<html>404</html>", requests.HTTPError("404"))
	)
	assert updates.check_for_updates(load_config()).state == updates.UNKNOWN


def test_request_has_a_timeout(monkeypatch):
	seen = {}

	def fake_get(url, timeout):
		seen["timeout"] = timeout
		return FakeResponse(_local_version())

	monkeypatch.setattr(requests, "get", fake_get)
	updates.check_for_updates(load_config())
	assert seen["timeout"] == updates.REQUEST_TIMEOUT_SECONDS


def test_window_starts_pending_and_updates_from_worker(main_window, monkeypatch):
	assert main_window.update_status.state == updates.CHECKING
	monkeypatch.setattr(requests, "get", lambda url, timeout: FakeResponse("99.0.0"))
	worker = updates.UpdateCheckWorker(main_window.controller)
	worker.signals.finished.connect(main_window.set_update_status)
	worker.run()  # synchronously, instead of via the thread pool
	assert main_window.update_status.state == updates.OUTDATED
	assert "99.0.0" in main_window.statusBar().currentMessage()
