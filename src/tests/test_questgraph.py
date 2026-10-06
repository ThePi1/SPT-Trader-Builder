"""The quest graph (which quest needs which) and where each quest goes in it."""

import json
import time

import pytest

from core import graphlayout as L
from core import questgraph as G
from core import references as R


def quest(name, requires=(), trader="t1", level=None, fails_with=(), finish_after=(), notes=()):
	"""A quest with 'Quest' conditions: requires is [(id, statuses, wait)], fails_with and finish_after are [(id, statuses)]."""
	start = [{"conditionType": "Quest", "target": q, "status": list(s), "availableAfter": w} for q, s, w in requires]
	if level is not None:
		start.append({"conditionType": "Level", "value": level, "compareMethod": ">="})
	start.extend(notes)
	return {
		"QuestName": name, "traderId": trader,
		"conditions": {
			"AvailableForStart": start,
			"AvailableForFinish": [{"conditionType": "Quest", "target": q, "status": list(s)} for q, s in finish_after],
			"Fail": [{"conditionType": "Quest", "target": q, "status": list(s)} for q, s in fails_with],
		},
		"rewards": {},
	}


def chain():
	return {
		"a": quest("A"), "b": quest("B", [("a", (4,), 0)]), "c": quest("C", [("a", (2,), 0)], level=12),
		"d": quest("D", [("b", (4,), 0), ("c", (4,), 3600)], trader="t2"),
	}


# --- building the graph ------------------------------------------------------------------------------

def test_conditions_become_links_of_the_right_kind():
	quests = chain()
	quests["e"] = quest("E", [("b", (5,), 0), ("c", (2, 4), 0)], fails_with=[("d", (4,))], finish_after=[("a", (4,))])
	graph = G.build_graph(open_quests=quests)
	links = {(e.source, e.target, e.kind, e.list) for e in graph.edges}
	assert ("a", "b", G.COMPLETED, G.START) in links and ("a", "c", G.STARTED, G.START) in links
	assert ("b", "e", G.FAILED, G.START) in links and ("c", "e", G.ANY, G.START) in links  # (two states: any)
	assert ("d", "e", G.FAILS, G.FAIL) in links and ("a", "e", G.COMPLETED, G.FINISH) in links
	wait = next(e for e in graph.edges if (e.source, e.target) == ("c", "d"))
	assert wait.wait == 3600 and "1 h" in wait.words() and "completed" in wait.words()
	assert G.wait_words(86400 * 2) == "2 days" and G.wait_words(90) == "1 min" and G.wait_words(75600) == "21 h"


def test_a_missing_state_means_completed_and_a_link_to_itself_is_ignored():
	quests = {"a": quest("A"), "b": {"QuestName": "B", "conditions": {"AvailableForStart": [
		{"conditionType": "Quest", "target": "a"}, {"conditionType": "Quest", "target": "b", "status": [4]},
	]}}}
	graph = G.build_graph(open_quests=quests)
	assert [(e.source, e.target, e.statuses) for e in graph.edges] == [("a", "b", (4,))]


def test_what_a_quest_needs_besides_other_quests_is_kept_as_notes():
	notes = [
		{"conditionType": "TraderLoyalty", "target": "t9", "value": 2, "compareMethod": ">="},
		{"conditionType": "TraderStanding", "target": "t9", "value": 0.5, "compareMethod": ">="},
	]
	graph = G.build_graph(open_quests={"a": quest("A", level=12, notes=notes)}, trader_name=lambda trader: {"t9": "Prapor"}.get(trader, ""))
	node = graph.nodes["a"]
	assert node.level == 12 and node.notes == ["Player level at least 12", "Prapor loyalty level at least 2", "Prapor standing at least 0.5"]


def test_a_quest_in_more_than_one_place_is_the_open_one_and_the_others_are_noted(tmp_path):
	path = tmp_path / "mod.json"
	path.write_text(json.dumps({"a": quest("A in reference"), "r": quest("Reference only")}), encoding="utf-8")
	references = R.References(tmp_path / "list.json")
	references.add([path])
	graph = G.build_graph(
		open_quests={"a": quest("A open")}, references=references, game={"a": quest("A game"), "g": quest("Game only")},
		imported={"a": "imported.json"}, game_name=lambda quest_id: {"g": "Game quest"}.get(quest_id, ""),
	)
	node = graph.nodes["a"]
	assert (node.name, node.source, node.source_name) == ("A open", G.OPEN, "imported.json")
	assert node.also_in == ["Reference files (mod.json)", "Base game"]
	assert (graph.nodes["r"].source, graph.nodes["r"].source_name) == (G.REFERENCE, "mod.json")
	assert (graph.nodes["g"].source, graph.nodes["g"].name) == (G.GAME, "Game quest")  # (the game's name in the chosen language)


def test_a_quest_nobody_has_is_a_node_of_its_own_so_the_link_to_it_is_not_lost():
	graph = G.build_graph(open_quests={"b": quest("B", [("gone", (4,), 0)])})
	assert graph.unknown() == ["gone"] and graph.nodes["gone"].source == G.UNKNOWN and graph.nodes["gone"].label.startswith("gone")
	assert [(e.source, e.target) for e in graph.edges] == [("gone", "b")]


# --- asking the graph -----------------------------------------------------------------------------------

def test_what_is_within_reach_of_a_quest():
	graph = G.build_graph(open_quests=chain())
	assert graph.reach("b", back=1, forward=0) == {"a", "b"}
	assert graph.reach("a", back=0, forward=1) == {"a", "b", "c"}
	assert graph.reach("a", back=0, forward=None) == {"a", "b", "c", "d"}
	assert graph.reach("d", back=None, forward=0) == {"a", "b", "c", "d"}
	assert graph.reach("d", back=1, forward=1) == {"b", "c", "d"}
	quests = chain()
	quests["x"] = quest("X", fails_with=[("d", (4,))], finish_after=[("a", (4,))])
	assert G.build_graph(open_quests=quests).reach("x", back=0, forward=0) == {"x", "d", "a"}  # (finish and fail links are always shown)


def test_groups_and_loops():
	quests = chain()
	quests.update(lone=quest("Lonely"), p=quest("P", [("q", (4,), 0)]), q=quest("Q", [("p", (4,), 0)]))
	graph = G.build_graph(open_quests=quests)
	assert [len(g) for g in graph.groups()] == [4, 2, 1]
	assert sorted(sorted(loop) for loop in graph.loops()) == [["p", "q"]]
	interleaved = {"a": quest("A", [("b", (2,), 0)], finish_after=[]), "b": quest("B", finish_after=[("a", (4,))])}
	assert G.build_graph(open_quests=interleaved).loops() == []  # (A starts after B starts, B finishes after A completes: fine)


# --- the base game ------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def base_graph(vanilla_quests):
	return G.build_graph(game=vanilla_quests)


def test_the_base_game_graph(base_graph, vanilla_quests):
	assert len(base_graph.nodes) == len(vanilla_quests) and not base_graph.unknown() and base_graph.loops() == []
	by_name = {n.name: i for i, n in base_graph.nodes.items()}
	debut, search = by_name["Debut"], by_name["Search Mission"]
	assert any(e.source == debut and e.target == search and e.kind == G.COMPLETED for e in base_graph.edges)
	assert len(base_graph.groups()[0]) > 500  # (almost all of the quests hang together)
	fails = {(base_graph.nodes[e.source].name, base_graph.nodes[e.target].name) for e in base_graph.edges if e.kind == G.FAILS}
	assert ("Supply Plans", "Kind of Sabotage") in fails and ("Kind of Sabotage", "Supply Plans") in fails
	assert any(e.wait for e in base_graph.edges) and base_graph.nodes[debut].level == 1


# --- the layout --------------------------------------------------------------------------------------------------

def test_every_quest_is_in_a_column_after_the_quests_it_needs_and_no_two_share_a_place():
	graph = G.build_graph(open_quests=chain())
	placed = L.layout(graph)
	assert {i: placed.positions[i][0] for i in "abcd"} == {"a": 0, "b": 1, "c": 1, "d": 2}
	assert len(set(placed.positions.values())) == 4 and placed.columns == 3 and placed.rows == 2


def test_a_loop_is_drawn_with_one_link_backwards_and_everything_still_gets_a_place():
	quests = {"p": quest("P", [("q", (4,), 0)]), "q": quest("Q", [("p", (4,), 0)]), "r": quest("R", [("q", (4,), 0)])}
	placed = L.layout(G.build_graph(open_quests=quests))
	assert len(placed.positions) == 3 and len(placed.backwards) == 1


def test_groups_are_stacked_and_quests_with_no_links_are_put_in_a_block_of_their_own():
	quests = chain()
	quests.update({f"solo{n}": quest(f"Solo {n}") for n in range(10)})
	placed = L.layout(G.build_graph(open_quests=quests))
	assert len(set(placed.positions.values())) == 14
	solos = [placed.positions[f"solo{n}"] for n in range(10)]
	assert max(row for _x, row in solos) > max(placed.positions[i][1] for i in "abcd")  # (below the chain)
	assert max(x for x, _row in solos) == L.ISOLATED_PER_ROW - 1


def test_lanes_keep_each_trader_in_rows_of_its_own():
	quests = chain()
	quests["e"] = quest("E", [("a", (4,), 0)], trader="t2")
	graph = G.build_graph(open_quests=quests)
	placed = L.layout(graph, lanes=True)
	lanes = {trader: (first, last) for trader, first, last in placed.lanes}
	assert set(lanes) == {"t1", "t2"} and lanes["t1"][1] < lanes["t2"][0]
	for quest_id, node in graph.nodes.items():
		first, last = lanes[node.trader]
		assert first <= placed.positions[quest_id][1] <= last
	assert len(set(placed.positions.values())) == 5


def test_the_base_game_lays_out_fast_and_in_order(base_graph):
	started = time.perf_counter()
	placed = L.layout(base_graph)
	lanes = L.layout(base_graph, lanes=True)
	assert time.perf_counter() - started < 3
	for result in (placed, lanes):
		assert len(set(result.positions.values())) == len(base_graph.nodes)
		for edge in base_graph.edges:
			if edge.kind in G.ORDERING and edge.list == G.START:
				assert result.positions[edge.source][0] < result.positions[edge.target][0]
	assert placed.columns >= 39


def test_reference_files_give_their_quests_to_the_graph(tmp_path):
	path = tmp_path / "mod.json"
	path.write_text(json.dumps({"x": quest("X")}), encoding="utf-8")
	references = R.References(tmp_path / "list.json")
	references.add([path])
	assert list(references.quest_data()) == ["x"] and references.quest_data()["x"][1] == "mod.json"
