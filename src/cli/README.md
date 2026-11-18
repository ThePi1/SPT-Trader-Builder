# Command line

Make, change and check quests and quest zones without the window, using the same schema and checks as the app.
Run from this repository's `src` folder (Python 3.11 with the packages in `src/requirements.txt`; PySide6 draws the
map pictures, and `check --server` needs the .NET SDK):

    python -m cli [--project FILE] [--maps FOLDER] <command> ...

Every command prints JSON. A failed command prints `{"error": ...}` (and `"problems"` for a spec) and exits with 1.
Commands that change files are a **dry run** unless given `--write`: run once to see the result and the problems, then
again with `--write`. `python -m cli <command> --help` lists each command's options; this file covers what `--help`
can't. How it works inside, and what to do after a game update: [DEVELOPING.md](DEVELOPING.md).

## The project file

The files to work on are named in a project file (`--project`, or the `TB_PROJECT` environment variable). Paths are
relative to it:

```json
{
	"quests": "db/CustomQuests/x/Quests/quests.json",
	"locale": "db/CustomQuests/x/Locales/en.json",
	"assort": "data/assort.json",
	"questassort": "db/CustomQuests/x/QuestAssort/questassort.json",
	"trader": "Prapor",
	"zones": "db/CustomQuestZones/new_zones.json",
	"zone_files": ["db/CustomQuestZones"],
	"references": ["db/CustomItems", "db/CustomQuests/y/Quests/quests.json"],
	"language": "en",
	"game": "I:/Games/SPT"
}
```

Only `quests` and `locale` are needed; a missing file is made when written. `assort` and `questassort` are needed for
assort unlocks. `zones` is the file `zones make --write` adds to; `zone_files` (files or folders) are read for checks.
`references` are files and folders whose ids are looked up too, so their names work in specs and `find`: other
traders' quests and text, item templates, WTT `CustomItems` files, trader `base.json` files, assorts, zone files.
`game` is the game's folder: `maps import` reads it, names are looked up in its SPT database
(`SPT_Runtime/SPT_Data/database`, or give `"database"`), and `check --server` uses its `SPT_Runtime` (or give `"spt"`).

What isn't in the project file comes from the app's own settings (`data/settings.ini`: database folder, language,
new-quest icon and side) and reference list (`data/references.json`), as in the window; with neither, names come from
the copy of the SPT 4.1.6 database bundled with the program. `project show` says what a project uses. Done when it
names the database and references you expect.

## Using it on another project

The tool stays in this repository; another project only needs project files pointing at its own files.

1. **Write the project files**: `python -m cli project init --mod <the mod's folder> --out <folder> --game <game folder>`
   finds the traders of a WTT-CommonLib mod (`db/CustomQuests/<trader id>/`), and for each one its quests, text and
   quest locks, the mod's zone folder, its trader file and assort (a `*base.json` with the trader's id, and the
   `*assort.json` beside it), and makes the other traders' quests, the mod's custom items and trader files references.
   Read the plan, then add `--write`. Put the project files in the mod (`--out <mod>/questtools`, say) to keep paths
   relative to it; elsewhere they are absolute. `--trader <id>` starts a project for a trader with no quests yet.
2. **Check what it sees**: `TB_PROJECT=<project file> python -m cli project show`, then `quest list` and `check`. Done
   when `project show` names the database and references you expect and `check` reports what you know of (warnings
   about the base game's style are common in hand-written quests).
3. **Work as below**, one trader's project at a time. The maps import (`data/maps`) is shared by every project.

For the other project's agent, add to its `CLAUDE.md` or `AGENTS.md`:

```markdown
- To make, change or check quests, quest text or quest zones, use the SPT Trader Builder command line rather than
  editing the JSON by hand: from `<path to SPT-Trader-Builder>/src`, run
  `python -m cli --project <path to this mod>/questtools/project.<trader>.json <command>`.
  Read `<path to SPT-Trader-Builder>/src/cli/README.md` first.
```

## Workflow for a new quest

1. **Model it on the base game.** `quest show "Bad Rep Evidence"` shows any base-game or reference quest as a spec
   (marked `"from"`; read-only). `usage` answers how the base game fills a field across all its quests, with quests
   that use each value: `usage subtask ExitStatus status`, `usage task CounterCreator steps` (which counter steps go
   together), `usage reward Item findInRaid --where money=true`. Copy the common value unless the quest needs another.
2. **Look up what you need**: `find "salewa" --kind item`, `find prapor --kind trader`, `kinds task` (condition kinds),
   `kinds task HandoverItem` (its fields, defaults and choices), `kinds shorthand`, `kinds reward`.
3. **Place its zones** (below), if it has any.
4. **Write a spec** (below) and dry-run it: `quest add spec.json` (`--show` also prints the quest JSON and the text it
   would write). Done when it reports no `"error"` and no `"problems"`: names are matched exactly, and an unclear one
   lists the candidates with their ids.
5. **Write it**: `quest add spec.json --write`, then `check --server`. Done when `check` reports 0 errors and every
   warning is fixed or is one you can explain (to the user, when you are working for one). `--server` also loads the
   saved files with the SPT server's own code (needs the .NET SDK); without an SPT install, run plain `check`.
6. **Change a quest**: `quest show <name or id> --out q.json`, edit it, `quest update q.json --write`. A shown spec builds
   back into exactly the same quest (all 558 base-game quests do), so only the edit changes. Use `--out` rather than a
   shell redirect, which can write the file in an encoding `quest update` can't read.
7. **Hand it over**: `package --out <mod folder> --write` writes the quests, their text, quest locks and the custom
   zones they use in the folders WTT-CommonLib reads (`db/CustomQuests/<trader id>/...`, `db/CustomQuestZones`). It
   refuses while `check` has errors.

## Quest specs

A spec is a quest written the short way: names instead of ids, and only what differs from a new quest. A spec file
holds one spec, a list of them, or `{"quests": [...]}`; quests in one file can name each other (a `Quest` condition's
`target` can be another quest's `name` from the same file).

```json
{
	"name": "Supply run",
	"trader": "Prapor",
	"location": "Customs",
	"type": "Completion",
	"text": {"name": "Supply run", "description": "...", "successMessageText": "...", "failMessageText": "..."},
	"start": [{"kind": "Level", "value": 5}, {"kind": "Quest", "target": "Debut", "status": ["Completed"]}],
	"finish": [
		{"kind": "Visit", "ref": "found", "zone": "my_dorm_room", "text": "Find the room in the dorms"},
		{"kind": "PlaceBeacon", "ref": "marked", "after": "found", "zoneId": "my_dorm_mark", "text": "Mark the room"},
		{"kind": "Kill", "ref": "kills", "count": 5, "target": "Scavs", "distance": 50, "text": "Eliminate Scavs on Customs"},
		{"kind": "HandoverItem", "target": ["Bolts"], "value": 5, "onlyFoundInRaid": true, "text": "auto"},
		{"kind": "SurviveAndExtract", "after": ["marked", "kills"]}
	],
	"fail": [],
	"rewards": {
		"success": [
			{"kind": "Experience", "value": 8000},
			{"kind": "Item", "items": [{"item": "Roubles", "count": 50000}]},
			{"kind": "Item", "items": [{"item": "Bolts", "count": 2}]},
			{"kind": "TraderStanding", "target": "Prapor", "value": 0.03},
			{"kind": "AssortmentUnlock", "item": "Bolts", "price": 12000, "currency": "roubles", "loyaltyLevel": 2}
		],
		"started": []
	}
}
```

- **Quest keys**: `name` (the QuestName, for you; also the player-visible name until `text.name` is given), `trader`,
  `text` (the locale: `name`, `description`, `successMessageText`, `failMessageText`, `startedMessageText`, ...), the
  condition lists `start` / `finish` / `fail`, `rewards` with `success` / `started` / `fail`, and any of the quest's own
  JSON keys (`location`, `type`, `side`, `image`, `restartable`, ...: `kinds quest` lists them).
- **Conditions and rewards** have a `kind` and their JSON keys (`kinds task <Kind>`, `kinds subtask <Kind>`,
  `kinds reward <Kind>`). A `CounterCreator` holds its steps in `conditions` (subtask kinds). A condition's `text` is its
  locale line; `"auto"` writes it for FindItem, HandoverItem and Skill.
- **Shorthands** write the base game's fixed patterns (`kinds shorthand <Kind>` lists their keys):
  - `Visit` (`zone`): an Exploration counter with a VisitPlace step. The top-level VisitPlace kind doesn't work in SPT.
  - `Kill` (`count`, `target`, optional `zone`, `map`, and any Kills field such as `distance` or `weapon`): an
    Elimination counter with Kills, InZone and Location steps. `map` defaults to the quest's `location`.
  - `SurviveAndExtract` (optional `map`, `status`, `exit`): a Completion counter with ExitStatus (Survived and Transit,
    the base game's most common) and Location steps, with the base game's text.
- **ref and after**: any condition can have a `"ref"` name; `"after": "found"` (or a list) makes a condition show only
  once those are complete (its visibilityConditions), as the base game reveals the next step. Ids are made for you.
- **Values**: ids, or names. Items, traders and quests by exact name (any case; an item's short name works too);
  `find` shows the names. Maps by name (`Customs`) or key (`bigmap`). Choice fields take the value or its label
  (`"Scavs"` for `Savage`, `"Completed"` for quest status 4). A `{compareMethod, value}` field takes a number for "at
  least" (`"distance": 50`).
- **Item rewards**: `"items": [{"item": name, "count": n, "foundInRaid": bool}]` (one stack each; a count over the
  item's stack limit is fine, the server splits it), or `"composite": "<saved or vanilla composite item>"`, or raw
  `"parts"` with `"target"`. Found in raid defaults to the reward's `findInRaid`, which is false for a reward of only
  money (as the base game gives money) and true otherwise. The reward's `value` is worked out from the stacks.
- **Assort unlocks**: `"offer": "<offer id>"` unlocks an offer of the project's assort; `"item"` (or `"composite"`) with
  `"price"` and `"currency"` (or `"barter": [{"item", "count"}]`), optional `"loyaltyLevel"`, `"stack"`, `"buyLimit"`,
  makes the offer. Either way the quest lock is added to the questassort (success list: `success`, started list:
  `started`). The trader is `traderId`, else the project's `trader`.
- **Escape hatches**: `"extra": {...}` sets keys as given (anything the schema doesn't know); `"omit": [keys]` leaves
  out keys a new item would have. `quest show` uses both to describe odd quests exactly.
- **Ids**: give `"id"` to keep one (a quest, condition, reward or item entry); otherwise a new one is made.

## Maps and quest zones

Conditions point at zones by id: `PlaceBeacon` and `LeaveItemAtLocation` (`zoneId`), `VisitPlace` (`target`),
`InZone` (`zoneIds`, inside a CounterCreator), `LaunchFlare` (`target`). Custom zones are WTT-CommonLib
`CustomQuestZones` entries; `zones make` writes them.

`maps import [game folder]` reads the game client's scenes once (about two minutes) into `data/maps`: every map's
quest zones, its walkable floor (the bots' navigation mesh), its areas and every named object. It stays on this
computer. Re-run it after a game update, then `maps verify <SPT_Data/database folder>`: every zone that version's own
quests use should be found (a few ids the game itself lacks are listed). Without an import, `check` can't tell a
misspelt zone id from a game one; `maps list` says what is imported.

What the client does with each zone kind (from its code), which `check` enforces:

- `visit` (ExperienceTrigger): VisitPlace; it also counts for InZone.
- `placeitem` (PlaceItemTrigger): PlaceBeacon, LeaveItemAtLocation. Never counts for InZone. Two overlapping
  placeitem zones confuse the game (it forgets the zone when the player leaves either).
- `botkillzone` (`trigger` in the game's own zones): InZone, including kill counters.
- `flarezone`: LaunchFlare. The game's own flare zones don't count for InZone; WTT's custom ones do.
- A `Location` condition names maps by key (`bigmap`): a map's `_id` there never matches (an error in `check`).

Placing a zone:

1. **Find the place by the name players use**: `zones find "White Knight"` (or `--map Reserve`). It searches the named
   places (`maps/places.json`), the map's areas (named after its scenes, often transliterated Russian: Obshezhitie is
   the Customs dorms) and its objects, trying the words the game uses instead ("knight" is horse, "dorms" is
   obshezhitie). Each result has a `"next"` command. Done when one result is the place you want; if none is, try
   `zones areas --map ...` and `zones objects --map ... "<part of a name>"`.
2. **A whole building**: `zones building --map Reserve --place "White Knight" --picture b.png` (or `--at x,z`) gives its
   outline and angle, its storeys (the floor map's, and storeys only its room names show, like a 2F bots never walk),
   its rooms, and a zone covering it all. Read the picture (the suggested zone is green). Then
   `zones make --map Reserve --id <id> --kind visit --at <x,z> --building` makes that zone. A storey far below the
   ground (a tunnel or bunker under the building) is left out and noted.
3. **A spot inside**: look at it with `zones render --map Reserve --at 87,-18 --radius 10 --floor -0.7 --out r.png` (the
   floor from above, dark low to light high; holes are walls and furniture; `--floor` keeps one storey, as the
   building's storeys give them). `zones at --map Reserve 87,-18` gives the floor heights and zones there. Then
   `zones make --map Reserve --id <id> --kind placeitem --at 87,-18,-0.7 --size 2.5,2.5,3 --yaw 15 --picture z.png
   --one-floor`: the zone is centred on the spot with its bottom 0.25 m below the floor (`x,z,y` picks the storey
   nearest y); give it the building's yaw. On stairs or a ramp add `--slope`: the bottom then follows the walk under
   the zone down to its lowest floor (without it, `notes` says when the floor runs below the zone). Read the picture
   and the `errors` / `warnings`, adjust, then add `--write`.
   Positions are Unity's: x east, z north, y up; `--yaw` turns clockwise from north. Give each zone an id no other zone
   uses. Coordinates may be negative (`--at -60,-20`).
4. **Check it**: `zones check --rooms` (or `check`). Done when the new zone has no errors, its `covers` lists the rooms
   and storeys it is meant to cover (and no others; `floor_range` for a slope), and the picture shows it where it was
   meant to be.

The floor map misses some places a player can reach (rooms bots never enter, upper floors, crate tops), so "no floor
mapped" is a warning to check in game, never an error: a few of the game's own zones are in such places.
