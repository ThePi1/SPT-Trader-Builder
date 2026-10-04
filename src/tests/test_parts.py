from core import parts as P

ITEMS = {
	"gun": {"_props": {"Slots": [{"_name": "mod_magazine", "_props": {"filters": [{"Filter": ["mag"]}]}}, {"_name": "mod_stock", "_props": {"filters": [{"Filter": ["stock"]}]}}]}},
	"mag": {"_props": {"Cartridges": [{"_name": "cartridges", "_props": {"filters": [{"Filter": ["bullet"]}]}}]}},
}


def test_add_children_roots_and_remove():
	parts = []
	gun = P.add_part(parts, "gun")
	mag = P.add_part(parts, "mag", gun["_id"], "mod_magazine")
	P.add_part(parts, "bullet", mag["_id"], "cartridges", stack=30)
	assert P.roots(parts) == [gun] and gun["upd"] == {"StackObjectsCount": 1} and "upd" not in mag
	assert len(P.children(parts, mag["_id"])) == 1
	assert P.remove_part(parts, mag["_id"]) == 2 and parts == [gun]


def test_slots_and_fit():
	assert P.slot_names(ITEMS, "gun") == ["mod_magazine", "mod_stock"]
	assert P.slot_names(ITEMS, "mag") == ["cartridges"]
	assert P.fits(ITEMS, "gun", "mod_magazine", "mag") is True
	assert P.fits(ITEMS, "gun", "mod_magazine", "stock") is False
	assert P.fits({}, "gun", "mod_magazine", "mag") is None
	parts = []
	gun = P.add_part(parts, "gun")
	assert P.free_slot_for(ITEMS, parts, gun, "stock") == "mod_stock"
	P.add_part(parts, "stock", gun["_id"], "mod_stock")
	assert P.free_slot_for(ITEMS, parts, gun, "stock") is None
