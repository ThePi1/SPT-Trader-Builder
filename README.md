# SPT Trader Builder

Build quests, quest text and trader offers for SPT mods.
<img width="1093" height="725" alt="image" src="https://github.com/user-attachments/assets/aefd4e70-f978-4119-875a-197bc7f835aa" />


## What it does

- Make quests, with their objectives and rewards
- Write the quest text (names, descriptions, messages)
- Build what a trader sells, and lock items behind quests
- Warn you about mistakes as you work
- Open and combine files from other mods

## Get it

1. Download the latest release from the [Releases page](https://github.com/ThePi1/SPT-Trader-Builder/releases) and unzip it.
2. Run `SPTTraderBuilder.exe`.

While the included data is from SPT 4.0.13, this should work with later versions as well.

To run from source:
```
pip install -r requirements.txt
# then:
python .\src\main.py (win)
python ./src/main.py (mac/linux)
```
## Quick start

1. Click **New quest** and fill in the form on the right.
2. Click **Add** to give the quest objectives (tasks) and rewards.
3. Open the **Locale** tab to write the quest's name and description. **Add missing text** creates the empty entries for you.
4. Choose **File > Quests > Save as...** to save the quest file.

The **Problems** list at the bottom left tells you what still needs fixing. Click it to open it, and click a problem to jump to it.

## Sections

- **Quests**: your quests, with their objectives and rewards. Use the search box to find a quest by name, and the **+** and **−** buttons to open or close everything.
- **Locale**: the text the game shows for your quests.
- **Trader**: what a trader sells, at what price and trader level, and which quest unlocks each item. Pick the trader at the top so quest unlocks can be added.
- **Composite items**: items made of parts, like a gun with its mods. Save one once and reuse it in rewards and trader offers. The game's own items are listed too: you can look at them, and make your own copy to change.
- **Find IDs**: search for items, quests, traders and more, and copy their ids.
- **Schema Explorer**: shows what each kind of objective and reward is made of, and can check any file for mistakes.

## Your files

The program works with four kinds of file. The bar along the bottom shows each one, how many entries it has, and whether it is saved:

- **Quests**: the quests themselves
- **Locale**: the text for the quests
- **Trader assort**: what a trader sells
- **Quest assort**: which quest unlocks which trader offer

For each kind, use the menu under **File**, or click its section in the bottom bar:

- **Open** replaces what you have with a file. **Save** then writes back to that file.
- **Import** adds a file to what you have. You can import several files at once, or drag files or a folder onto the window. A window shows what will be added and what clashes (for example, the same quest in two files) before anything changes, and you choose whether to keep yours, use the imported one, or keep both. Locale files only bring in the text of your quests unless you tick the box for all of it.
- **Export** saves just some of your quests. Select them (Ctrl-click for several), then use **File > Quests > Export selected quests...** or right-click. It can include their text and trader offers too.
- **New (empty)** starts that kind of file again.

A `*` after the program's name in the title bar means something is not saved. Undo and redo are in the **Edit** menu (Ctrl+Z and Ctrl+Y).

## Using your files in SPT

The files are built to be compatible with vanilla SPT - but you will need to create a mod itself to load new traders and use these files. Then, load the quests and quest locales in some way - the easiest way is to use WTT-CommonLib. See https://github.com/WelcomeToThursday/WTT-CommonLib for more details.

The assumption is that if you're here, you probably know how to use these files - but more detail is planned to be added on this later.

## Settings

Open **Settings > Settings...** to change:

- **SPT database folder**: point this at your own `SPT_Data/database` folder to use your game's files, and to see names in another language. It is only read, never changed.
- **Language for names**: only English is included. Other languages need the folder above.
- **New quests**: the icon, side and trader new quests start with.
- **Always ask for a file name when saving**: by default, Save writes to the file you opened.
- **Copy locale into every language file**: when you save the locale, also add your quests' text to the other languages' files in the same folder.

Restart the program after changing the folder or the language.

## Updates and help

- **Help > Check for updates** tells you if there is a newer release.
- Found a problem or have an idea? [Open an issue](https://github.com/ThePi1/SPT-Trader-Builder/issues). If something goes wrong, turn on **Write a detailed log** in Settings and attach the `spt_trader_builder.log` file that appears next to the program.

When you update, keep a copy of `data/settings.ini` (your settings) and `data/my_items.json` (your saved composite items) before you replace the old folder, then put them back.

## Build

To build the program yourself (Windows), run these from the main folder of the repository:

```
pip install -r requirements.txt
cd src
python tools/build.py
```

The finished program is in `src/dist/SPTTraderBuilder/`. That folder holds `SPTTraderBuilder.exe`, the `lib` folder (the program needs it to run), the `data` folder and `LICENSE`. To make a release, zip the whole `SPTTraderBuilder` folder.

To check everything first, run `python -m pytest -q tests` from the `src` folder.

To refresh the included game data from a newer SPT before building, run this once from the `src` folder:

```
python tools/bundle_database.py "C:\path\to\SPT_Data\database"
```

## Credits and license

The program's own code is under the MIT License. It also includes game data from [Single Player Tarkov](https://github.com/sp-tarkov/server-csharp) (SPT), which is licensed under CC BY-NC-SA 4.0. The SPT Trader Builder Team is not associated with the SPT project. See [LICENSE](LICENSE) for the full details.
