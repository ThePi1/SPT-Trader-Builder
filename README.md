# SPT Quest Builder

A tool for building SPT Quests/Assorts.

## Usage
    pip install -r requirements.txt
    cd src
    python .\trader_builder.py

## Settings
Settings can be edited from **Settings > Edit Settings...** in the app. Changes are saved and loaded to/from the `settings.ini` file.

## GUI
The GUI is currently created using PySide6 and laid out using the Qt Designer tool.

This is included with PySide6 (`pip install -r requirements.txt`) and launched with `pyside6-designer`.

The Designer files are in `src\modules\gui\ui`. `src\tools\update_gui_py.ps1` compiles them into the `.py` files in `src\modules\gui\compiled` (run it from anywhere: `.\src\tools\update_gui_py.ps1`).
If you're not developing on Windows feel free to skip this (or make an analogue to it), and just run the commands yourself in that file as needed.

## Project layout
    src/trader_builder.py          entry point
    src/modules/                   everything else, imported as `modules.<name>`
    src/modules/config.py          settings.ini + data/box_fields.json (dropdown lists)
    src/modules/state.py           AppState: data shared by all windows
    src/modules/builders/          plain functions that build the exported JSON (no Qt)
    src/modules/windows/           one module per window (quest, task, reward, assort, ...)
    src/modules/gui/ui/            the Qt Designer .ui files
    src/modules/gui/compiled/      generated from the .ui files, don't edit by hand
    src/modules/error_handling.py  shows unexpected errors in a dialog (the packaged program has no console)
    src/modules/paths.py, utils.py, updates.py, table_fields.py   small shared helpers
    src/data/                      settings.ini, dropdown lists, items.json, ...
    src/tests/                     the test suite (see below)

## Tests
From the repository root:

    pip install -r requirements-dev.txt
    python -m pytest src/tests

`src/tests/test_builders.py` and `src/tests/test_state.py` test the JSON builders and shared state directly.
The other tests drive the real windows offscreen and compare the generated quest, assort and locale JSON to the files in `src/tests/golden/`.
If you change the output on purpose, regenerate them with `UPDATE_GOLDEN=1 python -m pytest src/tests` and review the diff.

## Packaging binary
Packaged with Python 3.11.6.

Run the packaging tool from the src/ folder as follows:

    python .\tools\pack.py


Alternatively, manually, you can pack as follows:

    pip install pyinstaller
    pyinstaller .\trader_builder.py --onefile --icon=data/icon.ico --hide-console=hide-early
    > Go into dist/ folder and grab trader_builder.exe
    > Copy trader_builder.exe, LICENSE, and data/ folder to new folder.
    > Zip up and release

I don't have it packaged for Linux/Mac on hand, but if you want to, you can.

