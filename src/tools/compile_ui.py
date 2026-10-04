"""Compile the Qt Designer files (ui/designer/*.ui) into Python (ui/compiled/ui_*.py).

    python tools/compile_ui.py            compile every .ui file
    python tools/compile_ui.py --check    compile nothing; exit 1 if a compiled file is out of date

Edit a window with  pyside6-designer ui/designer/<name>.ui , then compile. The compiled files are
committed (nothing needs compiling to run the program), so commit them with the .ui change.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DESIGNER_DIR = ROOT / "ui" / "designer"
COMPILED_DIR = ROOT / "ui" / "compiled"


def find_uic():
	"""The pyside6-uic program, or None."""
	found = shutil.which("pyside6-uic")
	if found:
		return found
	for folder in (Path(sys.executable).parent / "Scripts", Path(sys.executable).parent):
		for name in ("pyside6-uic.exe", "pyside6-uic"):
			if (folder / name).is_file():
				return str(folder / name)
	try:
		import PySide6
	except ImportError:
		return None
	for name in ("uic.exe", "uic"):
		path = Path(PySide6.__file__).parent / name
		if path.is_file():
			return str(path)
	return None


def compiled_name(ui_file):
	return COMPILED_DIR / f"ui_{Path(ui_file).stem}.py"


def compile_one(uic, ui_file, out_file):
	"""Run uic on one file. Raises RuntimeError with uic's message on failure."""
	result = subprocess.run([uic, "-g", "python", "-o", str(out_file), str(ui_file)], capture_output=True, text=True)
	if result.returncode != 0:
		raise RuntimeError(f"{Path(ui_file).name}: {result.stderr.strip() or result.stdout.strip()}")


def significant_lines(text):
	"""The lines of a compiled file that matter when comparing: the generated header (it names the
	Qt version) and the line endings are left out."""
	return [line.rstrip() for line in text.splitlines() if not line.startswith("##")]


def ui_files():
	return sorted(DESIGNER_DIR.glob("*.ui"))


def out_of_date(uic):
	"""[compiled file] that is missing or differs from what its .ui file compiles to now."""
	stale = []
	with tempfile.TemporaryDirectory() as tmp:
		for ui_file in ui_files():
			fresh = Path(tmp) / compiled_name(ui_file).name
			compile_one(uic, ui_file, fresh)
			current = compiled_name(ui_file)
			if not current.is_file() or significant_lines(current.read_text(encoding="utf-8")) != significant_lines(fresh.read_text(encoding="utf-8")):
				stale.append(current)
	return stale


def main(argv):
	uic = find_uic()
	if uic is None:
		print("pyside6-uic was not found. Install PySide6 (pip install PySide6).")
		return 2
	if "--check" in argv:
		stale = out_of_date(uic)
		for path in stale:
			print(f"out of date: {path.relative_to(ROOT)}")
		return 1 if stale else 0
	COMPILED_DIR.mkdir(exist_ok=True)
	init = COMPILED_DIR / "__init__.py"
	if not init.exists():
		init.write_text('"""Compiled from ui/designer/*.ui by tools/compile_ui.py. Do not edit."""\n', encoding="utf-8")
	for ui_file in ui_files():
		compile_one(uic, ui_file, compiled_name(ui_file))
		print(f"{ui_file.name} -> {compiled_name(ui_file).relative_to(ROOT)}")
	return 0


if __name__ == "__main__":
	sys.exit(main(sys.argv[1:]))
