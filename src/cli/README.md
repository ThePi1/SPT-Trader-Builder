# Command line

Make, change and check quests and quest zones without the window, using the same schema and checks as the app.
Run from the `src` folder:

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
	"game": "I:/Games/SPT"
}
```

Only `quests` and `locale` are needed; a missing file is made when written. `assort` and `questassort` are needed for
assort unlocks. `zones` is the file `zones make --write` adds to; `zone_files` (files or folders) are read for checks.
`game` is the game's folder, for `maps import` and `zones objects`. The app's own settings (`data/settings.ini`: SPT
database folder, language, new-quest icon and side) and reference files (`data/references.json`) apply as in the window.

## Workflow for a new quest

1. **Model it on the base game.** Find a base-game quest that does the same thing and read how it is built:
   `quest show "Bad Rep Evidence"` shows any base-game or reference quest as a spec (marked `"from"`; read-only).
   The base game has fixed patterns, for example "survive and extract" is its own CounterCreator (`ExitStatus`
   Survived / Runner / Transit plus `Location`), separate from the kill counter and shown after it through
   `visibilityConditions`.
2. **Look up what you need**: `find "salewa" --kind item`, `find prapor --kind trader`, `kinds task` (condition kinds),
   `kinds task HandoverItem` (its fields, defaults and choices), `kinds reward`.
3. **Write a spec** (below) and dry-run it: `quest add spec.json` (`--show` also prints the quest JSON and the text it
   would write). Done when it reports no `"error"` and no `"problems"`: names are matched exactly, and an unclear one
   lists the candidates with their ids.
4. **Write it**: `quest add spec.json --write`, then `check`. Done when `check` reports 0 errors and every warning is
   fixed or is one you can explain (to the user, when you are working for one).
5. **Change a quest**: `quest show <name or id> --out q.json`, edit it, `quest update q.json --write`. A shown spec builds
   back into exactly the same quest (all 558 base-game quests do), so only the edit changes. Use `--out` rather than a
   shell redirect, which can write the file in an encoding `quest update` can't read.
6. **Optionally, confirm the SPT server loads it**: `tools/server_check` loads a quests file with the server's own code
   (see [DEVELOPING.md](DEVELOPING.md#checking-files-with-the-servers-code)).

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
		{"kind": "HandoverItem", "target": ["Bolts"], "value": 5, "onlyFoundInRaid": true, "text": "auto"},
		{"kind": "CounterCreator", "type": "Elimination", "value": 5, "text": "Eliminate Scavs on Customs",
			"conditions": [{"kind": "Kills", "target": "Scavs", "distance": 50}, {"kind": "Location", "target": ["Customs"]}]},
		{"kind": "PlaceBeacon", "zoneId": "my_gas_station_mark", "text": "Mark the gas station"}
	],
	"fail": [],
	"rewards": {
		"success": [
			{"kind": "Experience", "value": 8000},
			{"kind": "Item", "items": [{"item": "Roubles", "count": 50000}, {"item": "Bolts", "count": 2}]},
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
- **Values**: ids, or names. Items, traders and quests by exact name (any case; an item's short name works too);
  `find` shows the names. Maps by name (`Customs`) or key (`bigmap`). Choice fields take the value or its label
  (`"Scavs"` for `Savage`, `"Completed"` for quest status 4). A `{compareMethod, value}` field takes a number for "at
  least" (`"distance": 50`).
- **Item rewards**: `"items": [{"item": name, "count": n, "foundInRaid": bool}]` (one stack each; found in raid
  defaults to the reward's `findInRaid`, money has none), or `"composite": "<saved or vanilla composite item>"`, or raw
  `"parts"` with `"target"`. The reward's `value` is worked out from the stacks.
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

`maps import [game folder]` reads the game client's scenes once (about a minute) into `data/maps`: every map's quest
zones, its walkable floor (the bots' navigation mesh) and its areas. It stays on this computer. Re-run it after a game
update, then `maps verify <SPT_Data/database folder>`: every zone that version's own quests use should be found (a few
ids the game itself lacks are listed). Without an import, `check` can't tell a misspelt zone id from a game one;
`maps list` says what is imported.

What the client does with each zone kind (from its code), which `check` enforces:

- `visit` (ExperienceTrigger): VisitPlace; it also counts for InZone.
- `placeitem` (PlaceItemTrigger): PlaceBeacon, LeaveItemAtLocation. Never counts for InZone. Two overlapping
  placeitem zones confuse the game (it forgets the zone when the player leaves either).
- `botkillzone` (`trigger` in the game's own zones): InZone, including kill counters.
- `flarezone`: LaunchFlare. The game's own flare zones don't count for InZone; WTT's custom ones do.
- A `Location` condition names maps by key (`bigmap`): a map's `_id` there never matches (an error in `check`).

Placing a zone:

1. Find the place: `zones areas --map Customs` (the map's areas with their extents, named after the game's scenes,
   often in transliterated Russian: Obshezhitie is the dorms, AZS the gas station, Tamozhnya the customs office),
   `zones list --map Customs --near 395,20` (zones nearby), `zones objects --map Customs "room 214"` (objects by name,
   read live from the game).
2. Look at it: `zones render --map Customs --at 395,20 --radius 40 --out place.png` draws the floor from above (dark
   is low, light is high; holes are walls and furniture), the zones and the areas, with coordinates every 5-10 m.
   Add `--floor <height>` for one storey of a building. Read the PNG to judge the spot.
3. `zones at --map Customs 395,20` gives the floor heights there and the zones around.
4. `zones make --map Customs --id my_mark --kind placeitem --at 395,20 --size 3,2.5,3 --yaw 10 --picture z.png`. Read
   the picture (the new zone is green) and the `errors` / `warnings`; adjust and repeat, then add `--write`. The zone is
   centred on the spot with its bottom 0.25 m below the floor (`--at x,z,y` picks the storey nearest y). Positions are
   Unity's: x east, z north, y up; `--yaw` turns clockwise from north. Give each zone an id no other zone uses.
5. `check` (or `zones check`) checks every custom zone. Done when the new zone has no errors and the picture shows it
   where it was meant to be.

The floor map misses some places a player can reach (rooms bots never enter, upper floors, crate tops), so "no floor
mapped" is a warning to check in game, never an error: a few of the game's own zones are in such places.
