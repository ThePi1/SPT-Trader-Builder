# Compiles the Qt Designer .ui files (modules\gui\ui) into Python modules (modules\gui\compiled).
# Works from any folder: paths are relative to src\, one level above this script.
$src = Split-Path -Parent $PSScriptRoot
$ui = Join-Path $src "modules\gui\ui"
$out = Join-Path $src "modules\gui\compiled"

foreach ($name in "main", "about", "updates", "quests", "tasks", "assort", "rewards", "datafiles", "settings", "children") {
	pyside6-uic -o (Join-Path $out "gui_$name.py") (Join-Path $ui "gui_$name.ui")
}
