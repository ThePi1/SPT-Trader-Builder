# SPT Quest Builder

A tool for building EFT SPT Quests.

## Usage
    pip install -r requirements.txt
    cd src
    python .\trader_builder.py

## Settings
The values in `src/data/settings.ini` (update check URLs and the quest defaults) can be edited from **Settings > Edit Settings...** in the app. Saving only rewrites the lines you changed, so the comments in the file are kept.
The dropdown lists live in `src/data/box_fields.json` and are not editable from the app.

### items.json
The program uses one item database (an `items.json`), loaded when it starts and used everywhere it is needed: the **ID Lookup** tab, the child-item finder (Debug > Get all children of parent ID) and the Settings dialog. By default this is the `data/items.json` included with the program, so you don't need to do anything.
To use a different one (say, from your SPT install, to include modded items), choose it with **Load items.json...** in the Settings dialog (or in the child-item finder). It is remembered in `settings.ini` (`items_file`) and loaded every time the program starts. **Use included file** in Settings goes back to the default.
If the file you chose can't be loaded at startup, the included one is used instead and the status bar says why. The line at the bottom of the ID Lookup tab says whether an items.json is loaded; "No items.json loaded" should only appear if even the included file is missing.

The ID Lookup search matches any column (the id, the data, or the type) and understands regular expressions (case-insensitive). For example, `^trader$` lists every trader.

### Debug log
Turn on **Write a debug log file** in the Settings dialog (or set `debug_logging = true` in `settings.ini`) to save a detailed log to `trader_builder.log`, for troubleshooting or to attach to a bug report. It is off by default, and no log file is written while it's off.
The file is created next to the program: in `src/` when running from source, and next to the `.exe` in the packaged build. It rotates at about 500 KB and keeps two older copies (`trader_builder.log.1` and `.2`).

## GUI
The GUI is currently created using PySide6 and laid out using the Qt Designer tool.

This is included with PySide6 (`pip install -r requirements.txt`) and launched with `pyside6-designer`.

`..\tools\update_gui_py.ps1` is ran from the `src\tb_ui` folder to compile the `.ui` files into their `.py` counterparts.
If you're not developing on Windows feel free to skip this (or make an analogue to it), and just run the commands yourself in that file as needed.

## Project layout
    src/trader_builder.py   entry point
    src/config.py           settings.ini + data/box_fields.json (dropdown lists)
    src/state.py            AppState: data shared by all windows
    src/builders/           plain functions that build the exported JSON (no Qt)
    src/windows/            one module per window (quest, task, reward, assort, ...)
    src/tb_ui/              generated from the .ui files, don't edit by hand
    src/tests/              the test suite (see below)
    src/error_handling.py   shows unexpected errors in a dialog (the packaged program has no console)
    src/paths.py, utils.py, updates.py, table_fields.py   small shared helpers

## Tests
From the repository root:

    pip install -r requirements-dev.txt
    python -m pytest src/tests

`src/tests/test_builders.py` and `src/tests/test_state.py` test the JSON builders and shared state directly (no windows, fast).
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

