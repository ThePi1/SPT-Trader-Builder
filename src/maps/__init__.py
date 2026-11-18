"""The game's maps and quest zones, read from the game's own files: the map import (unity, mapdata, navmesh, geometry),
quest zones and their checks (zones), places found by name (places, with places.json) and buildings (buildings).

Used by the command line (cli/) and by the app's zone checks; it depends only on the shared core and schema
packages, never on cli/ or ui/. No Qt. How it works: cli/DEVELOPING.md.
"""
