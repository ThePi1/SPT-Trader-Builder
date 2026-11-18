"""Finding a place on a map by the name players use for it ("White Knight", "dorms", "gas station").

The game's files rarely use those names: the White Knight on Reserve is the scene objects Reserv_Base_PTOR2_* and a
marker called white_horse, the Customs dorms are the scene custom_Obshezhitie. So a search looks in three places:

- the list of named places in maps/places.json, written by hand: a place's names, its map, where it is and the
  objects that anchor it in the game's files;
- the map's areas (its scenes, see maps.mapdata.scene_area);
- the map's named objects (maps.mapdata.ObjectIndex), grouped by where they are.

Words are also tried as the other words maps/places.json gives for them ("knight" -> horse, "dorms" ->
obshezhitie), as the game names things in transliterated Russian or by other words. No Qt.
"""

import re
import statistics
from pathlib import Path

from core import jsonio

PLACES_FILE = Path(__file__).with_name("places.json")
CLUSTER = 20.0  # metres: objects that match a search and lie closer than this are one result
SERVICE_SCENES = re.compile(r"(?i)light|sound")


def load(path=None):
	"""(synonyms {word: [other words]}, places [dict]) from maps/places.json."""
	data = jsonio.read_json(path or PLACES_FILE)
	return {k.lower(): [w.lower() for w in v] for k, v in (data.get("synonyms") or {}).items()}, data.get("places") or []


def terms(text, synonyms):
	"""The search's terms, each a set of words any of which may stand for it: "white knight" -> [{white},
	{knight, horse, kon}]. A phrase with a synonym ("gas station") is one term."""
	lowered = " ".join(text.lower().split())
	found = []
	for phrase in sorted((p for p in synonyms if " " in p), key=len, reverse=True):
		if phrase in lowered:
			found.append({phrase.replace(" ", ""), phrase.replace(" ", "_"), *synonyms[phrase]})
			lowered = lowered.replace(phrase, " ")
	for word in lowered.split():
		found.append({word, *synonyms.get(word, [])})
	return found


def _tokens(name):
	return [t for t in re.split(r"[^a-z0-9]+|(?<=[a-z])(?=[0-9])|(?<=[0-9])(?=[a-z])", name.lower()) if t]


def matches(name, search_terms):
	"""(True if every term is in the name, how many terms are whole words of it)."""
	lowered = name.lower()
	if not all(any(word in lowered for word in term) for term in search_terms):
		return False, 0
	tokens = set(_tokens(name))
	return True, sum(1 for term in search_terms if term & tokens)


def find(index, text, location=None, limit=10, path=None):
	"""Places matching text on one map (location) or every imported map, best first: dicts with kind 'place', 'area' or
	'objects', the map, and where it is ('at': [x, y, z] or [x, z])."""
	synonyms, places = load(path)
	search = terms(text, synonyms)
	if not search:
		return []
	maps = [location] if location else list(index.game_maps)
	results = []
	for place in places:
		if location and place.get("map") != location:
			continue
		names = [place.get("name", "")] + list(place.get("aka") or [])
		hits = [matches(n, search) for n in names]
		if any(ok for ok, _w in hits):
			results.append((200 + max(w for ok, w in hits if ok), _place(index, place)))
	for key in maps:
		if key not in index.game_maps:
			continue
		m = index.map(key)
		for area in m.areas:
			ok, whole = matches(area["name"], search)
			if ok:
				center = [round((area["min"][i] + area["max"][i]) / 2, 1) for i in range(3)]
				results.append((100 + whole, {"kind": "area", "map": key, "name": area["name"], "at": center, "min": area["min"], "max": area["max"]}))
		if m.objects is not None:
			for score, cluster in _object_clusters(m.objects, search, key):
				results.append((score, cluster))
	results.sort(key=lambda pair: -pair[0])
	return [r for _score, r in results[:limit]]


def _place(index, place):
	"""A hand-written place, with where its anchor objects are found on the imported map."""
	found = {"kind": "place", "map": place.get("map", ""), "name": place.get("name", "")}
	for key in ("aka", "note"):
		if place.get(key):
			found[key] = place[key]
	anchors = []
	key = place.get("map", "")
	term = place.get("objects")
	if term and key in index.game_maps and index.map(key).objects is not None:
		objects = index.map(key).objects
		exact = objects.name_indexes(lambda n: n.lower() == term.lower())
		wanted = exact or objects.name_indexes(lambda n: term.lower() in n.lower())
		anchors = [position for _n, _s, position in objects.rows(wanted)]
		found["anchors"] = len(anchors)
		if not anchors:
			found["warning"] = f"No object called '{term}' is on the imported map: the game may have changed, so check where it is."
	if place.get("at"):
		found["at"] = place["at"]
	elif anchors:
		found["at"] = [round(statistics.median(p[i] for p in anchors), 1) for i in range(3)]
	return found


def _object_clusters(objects, search, key):
	"""(score, result) per group of matching objects that lie together."""
	scored = {}
	for i, name in enumerate(objects.names):
		ok, whole = matches(name, search)
		if ok:
			scored[i] = whole
	if not scored:
		return []
	by_name = {objects.names[i]: whole for i, whole in scored.items()}
	clusters = []  # [best score, [(name, scene, position)]]
	for name, scene, position in objects.rows(set(scored)):
		if all(abs(c) < 0.01 for c in position):
			continue  # (a scene's folder objects sit at the origin: they name a scene, not a place)
		score = by_name[name]
		for cluster in clusters:
			cx, _cy, cz = cluster[1][0][2]
			if abs(position[0] - cx) <= CLUSTER and abs(position[2] - cz) <= CLUSTER:
				cluster[1].append((name, scene, position))
				cluster[0] = max(cluster[0], score)
				break
		else:
			clusters.append([score, [(name, scene, position)]])
		if len(clusters) > 200:
			break
	results = []
	for score, members in clusters:
		names = list(dict.fromkeys(n for n, _s, _p in members))
		scenes = list(dict.fromkeys(s for _n, s, _p in members))
		at = [round(statistics.median(p[i] for _n, _s, p in members), 1) for i in range(3)]
		# whole-word matches first, then the fewer and shorter names (a marker called white_horse beats lamp posts)
		rank = 50 + score * 10 - min(len(_tokens(n)) for n in names)
		if any(matches(s, search)[0] for s in scenes):
			rank += 25  # (objects of a scene named after the search, such as custom_AZS_old: the place itself)
		if all(SERVICE_SCENES.search(s) for s in scenes):
			rank -= 15  # (a lighting or sound scene's groups are named after places, but not always where they are)
		rank += min(8, len(members) // 3)
		results.append((rank, {
			"kind": "objects", "map": key, "at": at, "count": len(members), "names": names[:6],
			"scenes": list(dict.fromkeys(s for _n, s, _p in members))[:4],
		}))
	return results
