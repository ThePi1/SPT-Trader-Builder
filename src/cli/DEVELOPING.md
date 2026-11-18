# Developer notes: the command line, the map import and quest zones

How the code behind `python -m cli` works, what it relies on in the game, and how to keep it right. For using it, see
[README.md](README.md). Everything here is Qt-free except `cli/render.py`.

## Layout

| Module | What it does |
| --- | --- |
| `cli/main.py` | The commands (argparse). Each `cmd_*` prints JSON and returns an exit code. |
| `cli/workspace.py` | `Workspace`: the project file's documents (`core.documents.Document`), the app's settings, game data, references and saved composite items, and the zone index. |
| `cli/spec.py` | Quest specs: `build_quest` (spec to quest JSON), `describe_quest` (quest JSON to spec), `Resolver` (names to ids), `apply_quest` (into the workspace). |
| `cli/render.py` | Top-down PNGs of a map (Qt, off screen). |
| `cli/usage.py` | `usage`: the values the base game's quests give a field, with worked-out fields (`PSEUDO`: a counter's `steps`, a reward's `money`). |
| `cli/servercheck.py` | `check --server`: finds `SPT_Runtime`, runs `tools/server_check --json`, turns its report into problems. |
| `cli/package.py` | `package`: the project's files in WTT-CommonLib's folder layout. |
| `core/unity.py` | A read-only reader of the game's Unity files: serialized files, the objects the import needs, navmesh tiles. |
| `core/mapdata.py` | `import_maps` (game files to `data/maps`), `MapData` (reading it back), `ObjectIndex` (a map's named objects), `LOCATIONS` (which scenes make up each map), `find_objects` (live). |
| `core/navmesh.py` | `NavMesh`: floor heights at a point, polygons near an area, sampling a box. |
| `core/geometry.py` | Vectors, quaternions, `Box` (an oriented box: contains, overlaps, footprint). |
| `core/zones.py` | `Zone`, `ZoneIndex`, the WTT zone file format, which zone kinds each condition takes (`ZONE_FIELDS`), the quest and zone checks, `make_zone`. |
| `core/places.py` | `zones find`: places by the names players use, from `data/places.json`, the areas and the object index. |
| `core/buildings.py` | `zones building`, `make --building`, `check --rooms`: a building's outline, storeys and rooms. |
| `data/places.json` | Hand-written: other words for search words (`synonyms`) and named places with their anchors (`places`). |
| `tools/server_check/` | A .NET program that loads quest files with the SPT server's own code (see below). |

The app uses the same pieces: `schema/validate.validate_quests(..., zones=)` adds the zone checks, `MainWindow.zone_index()` builds the index (imported maps plus zone files among the references, rebuilt when the references change), and quest zone files are a reference kind (`core/references.ZONES`).

## Command conventions

- Output is JSON on stdout. Failure is `{"error": ...}` with exit code 1 (`CommandError`); a spec with problems also has `"problems"`. `--strict` turns errors found by a check into exit code 1.
- Changing commands are dry runs until `--write`. They change the workspace's `Document`s in memory, report, and save only with `--write` (`Workspace.save` writes the dirty documents).
- A new command is a `cmd_*` function plus its parser entry in `parser()`. Test it through `main([...])` (see `run()` in `tests/test_cli.py`).

## Quest specs (`cli/spec.py`)

**Building.** `build_quest` starts from `schema.quest.make_quest` and `schema.registry.new_item` for every condition and reward, so new items look exactly like the app's. Each spec key is a schema field, converted by `convert()` by the field's kind (`schema/fields.py`). Keys the kind's base has but no field shows (`index`, `parentId`, ...) are set as given; anything else is a problem. Problems are collected (`_Problems`) and raised together as `SpecError`, each with a path like `finish[1].conditions[0].target`.

**Names.** `Resolver` looks names up in the same rows as Find IDs (`core.lookup.build_rows`, so reference files count). A name must match exactly (any case, items also by short name). An id is kept as is. Several matches or none is an error listing candidates. Special cases:

- A quest's `location` is a map's `_id` (`data/locations.json`); a `Location` condition's `target` is a map key (`bigmap`). The game compares the raid's map key with `Location` targets exactly (`EFT.Quests.ConditionLocationProgressChecker`), so a map `_id` there never matches. The app's Location field and `schema/validate._check_map_keys` follow this too.
- `Quest` targets can name another quest of the same spec file (`Resolver(batch=...)`).
- Item rewards: parts are built from `items` / `composite` / `parts`; `value` is always `schema.rewards.item_count(parts)`.
- Assort unlocks: `offer` (an existing offer) or `item` / `composite` with a price (a new offer via `schema.assort.new_offer_from_parts`). Either way the quest lock goes in `locks` and `apply_quest` writes it to the questassort.

**Shorthands, ref and after.** `expand()` runs on the condition lists before anything is built: it gives every `ref` an id (the condition's own `id` if it has one), writes out the shorthands (`SHORTHANDS`: `Visit`, `Kill`, `SurviveAndExtract`, each a CounterCreator spec) and turns `after` into `visibilityConditions` (CompleteCondition entries with new ids). The rest of the build sees only ordinary specs, so a shorthand's problems are reported at the written-out keys. `describe_quest` never writes shorthands. Their defaults follow `usage`: survive-and-extract counters are Completion with ExitStatus Survived and Transit (37 of 109 base-game ExitStatus steps; 65 of the 82 ExitStatus + Location counters are Completion).

**Money rewards.** A new Item reward whose items are all money gets `findInRaid: false` (431 of the base game's 456 money rewards), set before the spec's own keys. `describe_reward` mirrors it: for a money-only reward it writes `findInRaid` only when it is true, so the round trip still holds. A count over the item's stack limit is left alone: the server splits it (`RewardHelper.ProcessReward` "fixes stack sizes"; 63 base-game rewards rely on it).

**Describing.** `describe_quest` writes only what differs from a new item. Values of the wrong type for their field (the base game has a few, like a count written as `"1"`) go under `extra` (`_fits`); keys a new item has that the quest lacks go under `omit`; plain item rewards become `items` entries with their part ids.

`quest show` also describes base-game and reference quests (`cli/main._other_quest`), with their own text, so an agent can copy how the base game builds something; those are only read, never written.

**The invariant.** `build_quest(describe_quest(q)) == q` for every base-game quest, enforced by `test_every_vanilla_quest_is_described_and_built_again_unchanged`. That is what makes `quest show` then `quest update` safe: only the edit changes. A change to either side must keep that test passing.

## The map import (`core/unity.py`, `core/mapdata.py`)

The maps are the game's built-in scenes. Scene N of the build is the file `EscapeFromTarkov_Data/levelN`; its assets (meshes, the navmesh) are in `sharedassetsN.assets`. The scene list is the first field of `BuildSettings` (class 141) in `globalgamemanagers`.

**File format.** Unity 2022.3 serialized files, format 22, *without type trees*, so every object layout is written out by hand in `core/unity.py`. Header: big-endian `u32 metadataSize, fileSize, version, dataOffset`, an endianness byte, 3 reserved bytes, then (format 22) `u32 metadataSize, i64 fileSize, i64 dataOffset, i64 unused`. Metadata (little-endian): Unity version string, platform, type-tree flag (must be 0), types (`classId, stripped, scriptIndex`, a 16-byte script hash for MonoBehaviours, a 16-byte type hash), objects (aligned `pathId i64, start i64, size u32, typeIndex i32`), scripts (`fileIndex, pathId`), externals (file names; file index n means `externals[n-1]`). Strings are length-prefixed and padded to 4 bytes; references are `(fileIndex i32, pathId i64)`.

**Objects read**, with their class ids: GameObject 1, Transform 4 (and RectTransform 224), BoxCollider 65, MonoBehaviour 114 (only its common start; the reader is left at the script's own fields), MonoScript 115 (for the class name), BuildSettings 141, NavMeshData 238. One quirk found by dumping raw bytes: a 2022.3 BoxCollider has `IsTrigger, ProvidesContacts` in one aligned block and `Enabled` in the next, so the size and centre start 8 bytes after the layer fields. `TransformCache.world` composes parent transforms (rotation, scaled position, lossy scale).

**Zones.** A zone is a MonoBehaviour whose script class is in `TRIGGER_CLASSES` (`EFT.Interactive.ExperienceTrigger`, `PlaceItemTrigger`, `QuestTrigger`, `TriggerWithId`; the id is their first field `_id`) or `FlareShootDetectorZone` (`zoneID`, then the flare type and its trigger handlers, whose objects can hold the colliders). The zone's box is every BoxCollider on its object: center = position + rotation × (center × lossy scale), size = size × lossy scale. One zone id can have several boxes and kinds.

**Which scenes make up a map.** `LOCATIONS` maps each location id to its scene folder, minus some scenes. The game's own description is in `StreamingAssets/Windows/maps/*_preset.bundle`, but presets nest other presets by GUID, so the folder rule is used and was checked instead: every zone the base game's quests use is found on the quest's own map. Factory day and night are `Factory_Rework` with different quest scenes (the old `Factory` folder is unused); Sandbox and Sandbox_high differ by their `_AI` scene.

**Floor.** The bots' navigation mesh: the largest NavMeshData in the sharedassets of the map's `_AI` scene (Woods has two). Each tile starts `VAND` (`DNAV` little-endian) version 16 with a 72-byte header: at offset 20, `polyCount, vertCount, detailMeshCount, detailVertCount, detailTriCount, bvNodeCount`, then the bounds and a quantisation factor. Then `vertCount` float triples (world coordinates: the game's zones sit on it), then `polyCount` 32-byte polygons (`u16 verts[6], u16 neighbours[6], u32 flags, u8 vertCount, u8 area, 2 bytes`). Only vertices and polygons are read; heights come from each polygon's plane.

**Areas.** `scene_area`: a scene whose name doesn't say it holds lighting, sound, bots and so on is a place (`custom_Obshezhitie` is the Customs dorms). Its extent is the 2nd to 98th percentile of its objects' positions.

**Objects.** `scene_objects`: every GameObject with a name, at its Transform's world position, leaving out the copies models have for levels of detail, shadows, ballistics and colliders (`_COPY_NAMES`). Across a map's scenes, one object per (name, position to 0.1 m). Reserve has about 394,000 objects and keeps 200,000 (1.6 MB compressed). Scenes are read once for zones, area and objects together; a scene's objects are let go once no later map uses the scene (Factory and Sandbox share scenes).

**Output.** `data/maps/<location>.json` (zones, areas; small, read by the app's checks), `<location>.navmesh.json.gz` (read only when a floor is needed) and `<location>.objects.json.gz` (`{format, scenes, names, objects: flat [name index, scene index, x, y, z in cm, ...]}`, read only when objects are searched). `FORMAT` is stored in each; bump it when the records change, and `MapData.load` refuses old files with "import the maps again". A map imported before objects were indexed has no objects file: `MapData.objects` is None and the commands say to import again. The import takes about two minutes for every map. The data comes from the game, so `data/maps/` is git-ignored and never shipped.

## Places and buildings (`core/places.py`, `core/buildings.py`)

**Places.** The game's files rarely use players' names: the White Knight on Reserve is the objects `Reserv_Base_PTOR2_*`, its sound rooms `rem_block_01_*` and a marker `white_horse` (in `Reserve_Base_Scripts`, beside `white_bishop`, `black_pawn`, ...); Reserve's chess signs are `reserve_sign_chess_horse` (knight), `_elephant` (bishop), `_ferz` (queen), `_rook`, `_pawn`. `find` tries each search word as itself and as its `synonyms`, then ranks: named places (`data/places.json`), areas, then groups of matching objects within 20 m (whole-word matches and short names first; objects at the origin are scene folders and are skipped). A named place's `at` is checked by hand; its `objects` anchor shows it is still in the game (`anchors`, or a warning). Add a place only once it is checked, and say how in its note.

**Buildings.** Walls aren't in the import: a probe of the White Knight's scene found its BoxColliders are doors and props, the walls being mesh colliders. So `building_at` works from the floor map and the objects:

1. The ground is the middle of the lowest floors on rings 24 to 40 m around the spot.
2. The building is the connected patch of floor more than `UP` (2 m) above the ground nearest the spot, sampled every `STEP` (0.75 m): upper storeys and roofs. A building with no upper floor bots walk has no outline (its rooms are still listed).
3. The outline is the smallest rectangle around the patch over every angle in 0.5 degree steps, ignoring the outermost 0.2% of samples each side (1% cut the corners and turned a test building 1.5 degrees).
4. Storeys are peaks of the floor heights inside it (quarter-metre bins, at least `MIN_STOREY` 10 m², 1.8 m apart). Stairs and ramps join storeys, so splitting by gaps doesn't work. A storey more than 2 m below the ground is marked `below_ground` and left out of the zone (under the White Knight runs a tunnel at -15.5 m).
5. Rooms are objects inside the outline whose name has a room word (`ROOM_WORDS`, whole words: Broom isn't a room) or says a storey (`floor_number`: Floor_2, f2, 2nd floor, 2F), not in a lighting scene (its light groups are called Floor1, Floor2, ...). A storey only the names give (a 2F bots never walk) is added at the median height of its rooms less 0.3 m.
6. The zone spans the outline plus a margin, from the lowest storey less `SINK` to the top storey plus `REACH_ABOVE` (2.5 m).

On the White Knight this gives 23.4 x 11.8 x 34.4 m at 15.5 degrees, matching a zone placed by hand.

## Zone rules and where they come from

From the client (`Assembly-CSharp`, readable in the 4.1.6 decompile):

- `TriggerWithId.TriggerEnter` adds the zone id to `Player.TriggerZones`, which the InZone checks read (kills, damage, exit, item use, health effects: `BaseStatisticsManager`, `Player`). `ExperienceTrigger` calls it and also fires `SpecialPlaceVisited` (VisitPlace).
- `PlaceItemTrigger.TriggerEnter` doesn't call the base: it sets `Player.PlaceItemZone` and never joins `TriggerZones`, so a placeitem zone can't satisfy InZone. Leaving any placeitem zone sets `PlaceItemZone` to null, hence the overlap warning.
- `FlareShootDetectorZone` isn't a `TriggerWithId`: the game's own flare zones never count as inside.

From WTT-CommonLib (`WTTClientCommonLib.Services.QuestZones`): a zone is a new object with a trigger BoxCollider of size 1, positioned at `Position`, turned by `Rotation`, scaled by `Scale` (so Scale is the box size), numbers parsed from strings; `ZoneLocation` is compared with the raid's map id ignoring case. `visit` is an ExperienceTrigger, `placeitem` a PlaceItemTrigger, `botkillzone` a TriggerWithId, `flarezone` a `ZoneFlareTrigger` (a TriggerWithId that calls the base, so it counts as inside) with a `FlareShootDetectorZone`, `salvage` a `SalvageItemTrigger`.

`ZONE_FIELDS` in `core/zones.py` encodes these per condition. A zone of the wrong kind is an error (the condition can't be done); an unknown id is a warning only when maps are imported (it may come from a file the program isn't told about).

**Floor checks are warnings only.** A trigger fires when the player's body touches the box, so a box is reachable when a floor lies between its bottom minus a player's height and its top. The navmesh leaves out rooms bots never enter, upper floors and crate tops: 20 boxes of the game's own zones are metres from any floor it has. `floor_report` therefore never returns errors.

**Slopes.** A new zone's bottom sits `SINK` below the floor at its middle, which on stairs is halfway down the flight. `walkable_span` follows the floor from there across the zone's footprint, sample to sample (0.5 m), up or down less than `STEP_DOWN` (1.6 m): the floor map draws stairs in coarse steps (the old gas station's on Customs has a 1.47 m step), but storeys are further apart. `make_zone(slope=True)` (`zones make --slope`) puts the bottom at the lowest floor of that walk; without it a note says when the walk goes below the zone. It is opt-in: a room zone beside a stairwell would otherwise reach down to the storey below.

## After a game update

1. `python -m cli maps import "<game folder>"`. A `FormatError` means the Unity version or a layout changed: dump the failing object's bytes (`SerializedFile.reader`) and re-check the layout, as was done for BoxCollider.
2. `python -m cli maps verify "<that SPT's SPT_Data/database>"`. Expect only the ids the game itself lacks (in 4.1.6: `bunker2`, `Check_cinema`, `Labs_transits`, `1`). Many missing ids on one map point at `LOCATIONS` (a renamed or new scene folder).
3. Re-run the tests: `test_importing_a_real_map_finds_its_zones_and_floor` reads the real game when `SPT_GAME` (or the default path in `tests/test_zones.py`) is a game folder.

## Checking files with the server's code

`tools/server_check` loads a quests file the way the SPT 4.1 server does, using the server's DLLs from an install (it targets .NET 10, as SPT 4.1 does):

    cd src/tools/server_check
    dotnet run -c Release -p:SptRuntime="<SPT install>\SPT_Runtime" -- <quests.json> [<en.json>]

(or set the `SPT_RUNTIME` environment variable). It deserializes into `Dictionary<MongoId, Quest>` with the server's `JsonUtil` and converters; a bad id, enum value or missing required field fails there, as it would on server start. It then writes the quests back with the server's settings and compares, and lists keys no model has: the shipped server DLL gives every model an `ExtensionData` property (a Mono.Cecil patch at build time), which keeps unknown keys without any code reading them. The server's own 558 quests come out clean, which is the baseline.

With `--json` it prints one JSON object (`ok`, `quests`, `dropped`, `changed`, `added`, `unknown`, `locale_entries`, `error`). `python -m cli check --server` runs it that way (`cli/servercheck.py`): dropped keys and changed values are errors, unknown keys warnings. It finds `SPT_Runtime` from `--spt`, `SPT_RUNTIME`, the project's `spt`, then the project's `game` folder (SPT 4.1 installs into the game folder).

## Packaging (`cli/package.py`)

WTT-ServerCommonLib's CustomQuestService reads `db/CustomQuests/<trader key>/{Quests,Locales,QuestAssort}` next to the mod's DLL (its log lines say "Loading quests for trader"; a trader key may be the id), and CustomQuestZoneService reads `db/CustomQuestZones`. rtt2-traders uses that layout with trader ids and an empty QuestAssort file per trader, and `package` writes the same: per trader the quests, the text of their keys, and the project's quest locks for those quests; and one zone file with every custom zone the quests use (from the project's zone files and reference files). It doesn't package the assort (new offers for a base-game trader need the mod's code) or quest images.

What the server does with a loaded quest (4.1 source): `QuestHelper.GetClientQuests` shows a quest with no start conditions to everyone (side comes from the quest config's lists, not the quest's `side`); accepting sends the description as the start message when there's no `startedMessageText`; `CompleteQuest` doesn't re-check conditions (the client does); `RewardHelper.ApplyRewards` handles each reward type.

## Tests

- `tests/test_map_geometry.py`: boxes, the navmesh, tile parsing, and the Unity layouts on a serialized file built in the test (`_serialized`).
- `tests/test_zones.py`: zone files, the rules, the checks, `make_zone` (on small maps written by `_map`), and a live import of Labyrinth.
- `tests/test_cli.py`: the vanilla round trip, every command, shorthands, the money default, `usage`, `package`, and the server-free parts of `maps verify` and `check --server`.
- `tests/test_places_and_buildings.py`: the object index, `zones find`, and the building at a spot on a made-up map (a building turned 20 degrees with a storey, a roof, a tunnel under it and named rooms), through the commands too.
- Isolation: `conftest.py` points the reference list and `data/maps` at empty temp folders for every test; `test_cli.py`'s `plain_program` gives the app's default settings and no saved composite items.

## Known limits

- The navmesh is the only floor information and there is none for walls (MeshColliders would need Mesh parsing): building outlines come from upper floors, so a building bots never walk upstairs can't be outlined, and one on a slope may be confused with the hill.
- Areas are a heuristic named after scenes, often in transliterated Russian. Room names are a heuristic too: each map names its rooms its own way.
- `data/places.json` names only places that were checked (some of Reserve's so far).
- The game client reading a quest isn't checked beyond matching the base game's shapes, and WTT-CommonLib's quest loader isn't checked.
