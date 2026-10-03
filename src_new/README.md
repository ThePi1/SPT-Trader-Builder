# SPT Quest Builder (rebuild)

Work in progress. Everything for the rebuild lives in this folder; the old program in `src/` is untouched.

## Run

    pip install -r requirements.txt
    python main.py

In Settings > Game data, point "SPT database folder" at your SPT_Data/database folder to see item and trader names
(it is only read, never changed).

## Tabs

Quests (outline tree and forms, text boxes, problems list), Locale (the whole locale file), Trader (assort and quest locks),
Composite items (your saved items, plus the base game's), Find IDs, Schema Explorer. Each file (quests, locale, assort,
quest locks) is opened and saved on its own from the File menu; any of them can be started from nothing.

## Version and update check

`data/version.txt` is the program's version. Help > Check for updates compares it with the file at `version_url`
(Settings file, `[updates]`), exactly as the old program does, and says "out of date" when they differ. Keep the two
equal for a released build, and change `version_url`'s path when the rebuild takes the old program's place in the repo
(it points at `src/data/version.txt` on the main branch now).

## Game data and building

    python tools/bundle_database.py "<your SPT_Data/database folder>" --languages en
    python tools/build.py        (needs pip install pyinstaller; build is untested so far)

## Test

    python -m pytest -q

The tests that check against the base game use the game data bundled in `data/database` (and one trader assort in
`tests/fixtures`), so they run anywhere.

## Layout

- `core/`: settings, file reading/writing, ids, game data lookup, the open-file model with undo. No Qt.
- `schema/`: what a quest, task, reward, text, assort and composite item are. The forms, the checks and the
  Schema Explorer are all made from this. No Qt.
- `ui/`: the window, the outline editor, the generated forms, dialogs.
  - `ui/designer/`: Qt Designer files (`.ui`) for the fixed layouts: the main window (menus and tab bar), the Settings,
    About and Check for updates windows, the Quests, Locale, Trader and Composite items tabs, Find IDs and its picker
    window, and the Schema Explorer (both pages).
  - `ui/compiled/`: those files compiled to Python (`ui_*.py`). Generated: don't edit them by hand.
- `tools/`: scripts that rebuild `schema/server_models.json` (from the server's C# source) and `schema/vanilla_profile.json`
  (from the base game's quests), and compile the Designer files.

## Changing a window's layout

Open the file in Qt Designer, save it, then compile and commit both files:

    pyside6-designer ui/designer/locale_tab.ui
    python tools/compile_ui.py

The compiled files are committed, so the program runs without compiling. A test fails if a compiled file is out of date
(`python tools/compile_ui.py --check` says which). Only the fixed parts of a window are in the `.ui` files: the quest,
task and reward forms are generated from `schema/`, and the Settings pages, lists and the item editors are filled in
by code.
The tabs along the top are the empty `page_*` pages in `main_window.ui`: rename, reorder or add a tooltip or icon to
a page there, and the program puts that tab's real widget in its place (a page needs a matching entry in
`MainWindow._fill_tabs`, or the program says so on start).
Widgets keep the names code uses (`search`, `table`, `note`, ...), so rename them in Designer only together with the code.
