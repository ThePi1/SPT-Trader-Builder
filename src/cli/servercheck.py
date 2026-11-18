"""Running tools/server_check (the SPT server's own code reading a quests file) from the command line: finding the
SPT install's SPT_Runtime folder, running the tool with --json and turning its report into problems. Needs the .NET
SDK (`dotnet`). See cli/DEVELOPING.md, "Checking files with the server's code"."""

import json
import os
import shutil
import subprocess
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "tools" / "server_check"
CORE_DLL = "SPTarkov.Server.Core.dll"


def find_runtime(ws, given=None):
	"""The SPT_Runtime folder to use, or None: `given`, else the SPT_RUNTIME environment variable, else the project's
	"spt" folder, else the project's "game" folder. Each may be the SPT_Runtime folder or the folder holding it."""
	candidates = [given, os.environ.get("SPT_RUNTIME"), ws.path("spt"), ws.path("game")]
	for value in candidates:
		if not value:
			continue
		folder = Path(value)
		for path in (folder, folder / "SPT_Runtime"):
			if (path / CORE_DLL).is_file():
				return path
	return None


def run(quests_path, locale_path, runtime, timeout=900):
	"""The tool's report for the files: {ok, quests, dropped, changed, added, unknown, locale_entries, error}."""
	dotnet = shutil.which("dotnet")
	if dotnet is None:
		return {"ok": False, "error": "The .NET SDK (dotnet) isn't installed, so the server's code can't be run."}
	command = [dotnet, "run", "-c", "Release", "--project", str(TOOL), f"-p:SptRuntime={runtime}", "--", str(quests_path)]
	if locale_path is not None and Path(locale_path).is_file():
		command.append(str(locale_path))
	command.append("--json")
	try:
		done = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
	except subprocess.TimeoutExpired:
		return {"ok": False, "error": f"The server check took longer than {timeout} s."}
	return parse(done.stdout, done.stderr, done.returncode)


def parse(stdout, stderr="", returncode=0):
	"""The tool's report from its output: the last line that is a JSON object, else an error with the output's end
	(a build error, say)."""
	for line in reversed(stdout.strip().splitlines()):
		line = line.strip()
		if line.startswith("{"):
			try:
				return json.loads(line)
			except ValueError:
				break
	tail = "\n".join((stdout + "\n" + stderr).strip().splitlines()[-8:])
	return {"ok": False, "error": f"The server check didn't run (exit code {returncode}): {tail}"}


def problems(report):
	"""The report as problems for `check`: [{level, file, message}]."""
	found = []
	if report.get("error"):
		found.append({"level": "error", "file": "server", "message": report["error"]})
	for key, level, words in (
		("dropped", "error", "The server drops this key when it reads the file (the game never sees it)"),
		("changed", "error", "The server reads this value differently"),
		("unknown", "warning", "No server model has this key: the server keeps it but nothing reads it"),
	):
		for entry in report.get(key) or []:
			found.append({"level": level, "file": "server", "message": f"{words}: {entry}"})
	return found
