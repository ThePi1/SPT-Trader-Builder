"""Trader assort entries (items for sale), and weapon presets."""

ROUBLES_TPL = "5449016a4bdc2d6f028b456f"
USD_TPL = "5696686a4bdc2da3298b456a"
EUROS_TPL = "569668774bdc2da2298b4568"

CURRENCY_TPL = {"Roubles": ROUBLES_TPL, "USD": USD_TPL, "Euros": EUROS_TPL}


def currency_name(tpl):
	"""Display name for a payment item (anything that is not roubles or USD is shown as Euro)."""
	if tpl == ROUBLES_TPL:
		return "Roubles"
	elif tpl == USD_TPL:
		return "USD"
	return "Euro"


def weapon_part_item(item_id, tpl, parent_id, slot_id, *, ammo_count=None):
	"""A mod attached to a weapon; ammo_count makes it a stack of cartridges instead."""
	if ammo_count is None:
		return {
			"_id": item_id,
			"_tpl": tpl,
			"parentId": parent_id,
			"slotId": slot_id,
		}
	return {
		"_id": item_id,
		"_tpl": tpl,
		"parentId": parent_id,
		"slotId": "cartridges",
		"location": 0,
		"upd": {"StackObjectsCount": ammo_count},
	}


def assort_item(
	item_id,
	tpl,
	*,
	unlimited,
	quantity=None,
	buy_restriction=None,
	quest_id=None,
):
	"""A root item for sale. quantity is ignored when unlimited; quest_id locks it behind a quest."""
	item = {
		"_id": item_id,
		"_tpl": tpl,
		"parentId": "hideout",
		"slotId": "hideout",
		"upd": {},
	}
	if unlimited:
		item["upd"].update({"UnlimitedCount": True, "StackObjectsCount": 9999})
	else:
		item["upd"].update({"UnlimitedCount": False, "StackObjectsCount": int(quantity)})
	if buy_restriction is not None:
		item["upd"].update(
			{"BuyRestrictionMax": int(buy_restriction), "BuyRestrictionCurrent": 0}
		)
	if quest_id is not None:
		item.update({"unlockedOn": "success", "questID": quest_id})
	return item


def barter_scheme(item_id, cost, *, currency=None, barter_item_tpl=None):
	"""What an item costs: a currency name (Roubles/USD/Euros), or barter_item_tpl for a trade."""
	if barter_item_tpl is not None:
		tpl = barter_item_tpl
	else:
		tpl = CURRENCY_TPL.get(currency, "cash")
	return {item_id: [[{"count": int(cost), "_tpl": tpl}]]}


def weapon_preset_part(item_id, tpl, parent_id, slot_id, *, is_base):
	"""One entry of a weapon preset; the base weapon sits in the hideout, mods hang off a parent."""
	if is_base:
		return {  # sets initial item key structure for editing in logic.
			"_id": item_id,
			"_tpl": tpl,
			"parentId": "hideout",
			"slotId": "hideout",
			"upd": {},
		}
	return {
		"_id": item_id,
		"_tpl": tpl,
		"parentId": parent_id,
		"slotId": slot_id,
	}
