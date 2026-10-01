# SPT Quest Builder

A tool for building EFT SPT Quests.

## Usage
    pip install -r requirements.txt
    cd src
    python .\trader_builder.py

## Settings
The values in `src/data/settings.ini` (update check URLs and the quest defaults) can be edited from **Settings > Edit Settings...** in the app. Saving only rewrites the lines you changed, so the comments in the file are kept.
The dropdown lists live in `src/data/box_fields.json` and are not editable from the app.

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
    src/paths.py, utils.py, updates.py, table_fields.py   small shared helpers

## Tests
    pip install -r requirements-dev.txt
    python -m pytest tests

`tests/test_builders.py` and `tests/test_state.py` test the JSON builders and shared state directly (no windows, fast).
The other tests drive the real windows offscreen and compare the generated quest, assort and locale JSON to the files in `tests/golden/`.
If you change the output on purpose, regenerate them with `UPDATE_GOLDEN=1 python -m pytest tests` and review the diff.

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

