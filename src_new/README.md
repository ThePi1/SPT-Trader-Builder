# SPT Quest Builder (rebuild)

Work in progress. Everything for the rebuild lives in this folder; the old program in `src/` is untouched.

## Run

    pip install -r requirements.txt
    python main.py

In Settings > Game data, point "SPT database folder" at your SPT_Data/database folder to see item and trader names
(it is only read, never changed).

## Tabs

Quests (outline tree and forms, text boxes, problems list), Text (the whole locale file), Trader (assort and quest locks),
Composite items (your saved items, plus the base game's), Find IDs, Schema Explorer. Each file (quests, text, assort,
quest locks) is opened and saved on its own from the File menu; any of them can be started from nothing.

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
- `tools/`: scripts that rebuild `schema/server_models.json` (from the server's C# source) and `schema/vanilla_profile.json`
  (from the base game's quests).
- `PLAN.md`: the implementation plan.
