"""Quest conditions (tasks), and the sub-conditions inside a CounterCreator."""


def _group_by_org(entries):
	"""[{"id", "org"}, ...] -> [[ids of org A], [ids of org B]]: (these items) OR (those items)."""
	groups = {}
	for entry in entries:
		groups.setdefault(entry["org"], []).append(entry["id"])
	return list(groups.values())


def visibility_condition(cond_id, target):
	"""Only show a task once the task whose id is target has been completed (vanilla's "CompleteCondition")."""
	return {"conditionType": "CompleteCondition", "id": cond_id, "target": target}


# --- CounterCreator sub-conditions ------------------------------------------------


def visit_place(cond_id, target):
	return {
		"conditionType": "VisitPlace",
		"dynamicLocale": False,
		"globalQuestCounterId": "",
		"id": cond_id,
		"target": target,
		"value": 1,
	}


def kills(
	cond_id,
	*,
	weapon_ids,
	target,
	target_roles,
	body_parts,
	mods_inclusive,
	mods_exclusive,
	distance,
	distance_compare,
	time_from,
	time_to,
	reset_on_session_end,
):
	return {
		"bodyPart": body_parts,
		"compareMethod": ">=",  # hard code for kill quest
		"conditionType": "Kills",
		"daytime": {"from": time_from, "to": time_to},
		"distance": {"compareMethod": distance_compare, "value": distance},
		"dynamicLocale": False,
		"enemyEquipmentExclusive": [],
		"enemyEquipmentInclusive": [],
		"enemyHealthEffects": [],
		"id": cond_id,
		"resetOnSessionEnd": reset_on_session_end,
		"savageRole": target_roles,
		"target": target,
		"value": 1,
		"weapon": weapon_ids,
		"weaponCaliber": [],
		"weaponModsExclusive": [[mod] for mod in mods_exclusive],
		"weaponModsInclusive": [[mod] for mod in mods_inclusive],
	}


def exit_status(cond_id, statuses):
	return {
		"conditionType": "ExitStatus",
		"dynamicLocale": False,
		"id": cond_id,
		"status": statuses,
	}


def exit_name(cond_id, name):
	return {
		"conditionType": "ExitName",
		"dynamicLocale": False,
		"id": cond_id,
		"exitName": name,
	}


def location(cond_id, locations):
	return {
		"conditionType": "Location",
		"dynamicLocale": False,
		"id": cond_id,
		"target": locations,
	}


def equipment(cond_id, *, inclusive, exclusive, include_not_equipped):
	"""inclusive / exclusive are lists of {"id": item id, "org": or-group name}."""
	return {
		"IncludeNotEquippedItems": include_not_equipped,
		"conditionType": "Equipment",
		"dynamicLocale": False,
		"equipmentExclusive": _group_by_org(exclusive),
		"equipmentInclusive": _group_by_org(inclusive),
		"id": cond_id,
	}


def shots(
	cond_id,
	*,
	weapon_ids,
	body_parts,
	target_roles,
	mods_inclusive,
	mods_exclusive,
	distance,
	distance_compare,
	time_from,
	time_to,
	value,
	target,
	reset_on_session_end,
):
	return {
		"bodyPart": body_parts,
		"compareMethod": ">=",
		"conditionType": "Shots",
		"daytime": {"from": time_from, "to": time_to},
		"distance": {"compareMethod": distance_compare, "value": distance},
		"dynamicLocale": False,
		"enemyEquipmentExclusive": [],
		"enemyEquipmentInclusive": [],
		"enemyHealthEffects": [],
		"id": cond_id,
		"resetOnSessionEnd": reset_on_session_end,
		"savageRole": target_roles,
		"target": target,
		"value": value,
		"weapon": weapon_ids,
		"weaponCaliber": [],
		"weaponModsExclusive": mods_exclusive,
		"weaponModsInclusive": mods_inclusive,
	}


def health_effect(
	cond_id,
	*,
	body_parts,
	effects,
	energy,
	energy_compare,
	hydration,
	hydration_compare,
	time,
	time_compare,
):
	return {
		"bodyPartsWithEffects": [{"bodyParts": body_parts, "effects": effects}],
		"conditionType": "HealthEffect",
		"dynamicLocale": False,
		"energy": {"compareMethod": energy_compare, "value": energy},
		"hydration": {"compareMethod": hydration_compare, "value": hydration},
		"id": cond_id,
		"time": {"compareMethod": time_compare, "value": time},
	}


def health_buff(cond_id, buffs):
	return {
		"conditionType": "HealthBuff",
		"dynamicLocale": False,
		"id": cond_id,
		"target": buffs,
	}


def launch_flare(cond_id, zone):
	return {
		"conditionType": "LaunchFlare",
		"dynamicLocale": False,
		"id": cond_id,
		"target": zone,
	}


def in_zone(cond_id, zone_ids):
	return {
		"conditionType": "InZone",
		"dynamicLocale": False,
		"id": cond_id,
		"zoneIds": zone_ids,
	}


# --- Top-level conditions ----------------------------------------------------------
# Three different ids are involved in a CounterCreator, all unique:
#   one, each sub-condition has its own id
#   two, the whole counter has an id
#   three, the top-level CounterCreator condition has an id
# Number three is the one used in the internal datastore and shown in the task list.


def counter_creator(
	cond_id,
	*,
	counter_id,
	sub_conditions,
	parent_id,
	quest_type,
	value,
	visibility_conditions,
):
	return {
		"completeInSeconds": 0,
		"conditionType": "CounterCreator",
		"counter": {"conditions": sub_conditions, "id": counter_id},
		"doNotResetIfCounterCompleted": False,  # TODO: implement gui for this
		"dynamicLocale": False,
		"globalQuestCounterId": "",
		"id": cond_id,
		"index": 0,
		"isNecessary": False,  # TODO: implement gui for this
		"isResetOnConditionFailed": False,  # TODO: implement gui for this
		"oneSessionOnly": False,
		"parentId": parent_id,
		"type": quest_type,
		"value": value,
		"visibilityConditions": visibility_conditions,
	}


def find_item(
	cond_id,
	*,
	parent_id,
	targets,
	value,
	min_durability,
	max_durability,
	only_found_in_raid,
	visibility_conditions,
):
	return {
		"conditionType": "FindItem",
		"countInRaid": False,
		"dogtagLevel": 0,
		"dynamicLocale": False,
		"globalQuestCounterId": "",
		"id": cond_id,
		"index": 0,
		"isEncoded": False,
		"maxDurability": max_durability,
		"minDurability": min_durability,
		"onlyFoundInRaid": only_found_in_raid,
		"parentId": parent_id,
		"target": targets,
		"value": value,
		"visibilityConditions": visibility_conditions,
	}


def handover_item(
	cond_id,
	*,
	parent_id,
	targets,
	value,
	min_durability,
	max_durability,
	only_found_in_raid,
	visibility_conditions,
):
	return {
		"conditionType": "HandoverItem",
		"dogtagLevel": 0,
		"dynamicLocale": False,
		"globalQuestCounterId": "",
		"id": cond_id,
		"index": 0,
		"isEncoded": False,
		"minDurability": min_durability,
		"maxDurability": max_durability,
		"onlyFoundInRaid": only_found_in_raid,
		"parentId": parent_id,
		"target": targets,
		"value": value,
		"visibilityConditions": visibility_conditions,
	}


def skill(cond_id, *, compare_method, parent_id, target, value, visibility_conditions):
	return {
		"compareMethod": compare_method,
		"conditionType": "Skill",
		"dynamicLocale": False,
		"globalQuestCounterId": "",
		"id": cond_id,
		"index": 0,
		"parentId": parent_id,
		"target": target,
		"value": value,
		"visibilityConditions": visibility_conditions,
	}


def leave_item_at_location(
	cond_id,
	*,
	parent_id,
	targets,
	value,
	plant_time,
	min_durability,
	max_durability,
	only_found_in_raid,
	zone_id,
	visibility_conditions,
):
	return {
		"conditionType": "LeaveItemAtLocation",
		"dogtagLevel": 0,
		"dynamicLocale": False,
		"globalQuestCounterId": "",
		"id": cond_id,
		"index": 0,
		"isEncoded": False,
		"minDurability": min_durability,
		"maxDurability": max_durability,
		"onlyFoundInRaid": only_found_in_raid,
		"parentId": parent_id,
		"plantTime": plant_time,
		"target": targets,
		"value": value,
		"visibilityConditions": visibility_conditions,
		"zoneId": zone_id,
	}


# ItemID for the MS2000 marker, can also use Radio Repeater (63a0b2eabea67a6d93009e52) according to docs
MS2000_MARKER_TPL = "5991b51486f77447b112d44f"


def place_beacon(cond_id, *, parent_id, plant_time, value, zone_id, visibility_conditions):
	return {
		"conditionType": "PlaceBeacon",
		"dynamicLocale": False,
		"globalQuestCounterId": "",
		"id": cond_id,
		"index": 0,
		"parentId": parent_id,
		"plantTime": plant_time,
		"target": [MS2000_MARKER_TPL],
		"value": value,
		"visibilityConditions": visibility_conditions,
		"zoneId": zone_id,
	}


def weapon_assembly():
	# TODO: implement
	return {"weapon_assembly_placeholder": "add_weapon_assembly_object_here"}


def trader_loyalty(
	cond_id,
	*,
	compare_method,
	parent_id,
	trader_id,
	value,
	visibility_conditions,
):
	return {
		"compareMethod": compare_method,
		"conditionType": "TraderLoyalty",
		"dynamicLocale": False,
		"globalQuestCounterId": "",
		"id": cond_id,
		"index": 0,
		"parentId": parent_id,  # TODO: this isn't actually in the docs, does it work?? remove if not
		"target": trader_id,
		"value": value,
		"visibilityConditions": visibility_conditions,
	}


# The next three are start-only


def level(cond_id, *, compare_method, value):
	return {
		"compareMethod": compare_method,
		"conditionType": "Level",
		"dynamicLocale": False,
		"globalQuestCounterId": "",
		"id": cond_id,
		"index": 0,
		"parentId": "",
		"value": value,
		"visibilityConditions": [],
	}


def quest_status(cond_id, *, available_after, status_ids, target):
	return {
		"availableAfter": available_after,
		"conditionType": "Quest",
		"dispersion": 0,
		"dynamicLocale": False,
		"globalQuestCounterId": "",
		"id": cond_id,
		"index": 0,
		"parentId": "",
		"status": status_ids,
		"target": target,
		"visibilityConditions": [],
	}


def trader_standing(cond_id, *, compare_method, trader_id, value):
	return {
		"compareMethod": compare_method,
		"conditionType": "TraderStanding",
		"dynamicLocale": False,
		"globalQuestCounterId": "",
		"id": cond_id,
		"index": 0,
		"parentId": "",
		"target": trader_id,
		"value": value,
		"visibilityConditions": [],
	}
