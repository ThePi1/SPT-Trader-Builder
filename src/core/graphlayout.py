"""Where each quest goes in the quest graph: columns by how long a chain of quests comes before it, rows ordered to keep the
links short. No Qt. Positions are in grid units (column, row); the view decides how big a unit is.
"""

from dataclasses import dataclass, field

from core.questgraph import ORDERING, START

ISOLATED_PER_ROW = 8  # (quests with no links at all are put in a block of their own)
SWEEPS = 8


@dataclass
class Layout:
	positions: dict = field(default_factory=dict)  # quest id -> (column, row)
	columns: int = 0
	rows: float = 0.0
	lanes: list = field(default_factory=list)  # [(trader id, first row, last row)] when laid out in lanes
	backwards: set = field(default_factory=set)  # {(source, target)} of links that go back, to close a loop of quests that need each other


def _split(graph, ids):
	"""(prereqs, dependents, backwards): the ordering links among ids with the ones that close a loop taken out."""
	forward = {i: [] for i in ids}
	for edge in graph.edges:
		if edge.kind in ORDERING and edge.list == START and edge.source in forward and edge.target in forward and edge.source != edge.target:
			forward[edge.source].append(edge.target)
	state, backwards = {}, set()
	for root in ids:  # (depth-first, without recursion: a link back to a quest on the way down closes a loop)
		if root in state:
			continue
		state[root] = 1
		work = [(root, iter(forward[root]))]
		while work:
			node, children = work[-1]
			for child in children:
				if state.get(child) == 1:
					backwards.add((node, child))
				elif child not in state:
					state[child] = 1
					work.append((child, iter(forward[child])))
					break
			else:
				state[node] = 2
				work.pop()
	prereqs = {i: [] for i in ids}
	dependents = {i: [] for i in ids}
	for source, targets in forward.items():
		for target in set(targets):
			if (source, target) not in backwards:
				prereqs[target].append(source)
				dependents[source].append(target)
	return prereqs, dependents, backwards


def _layers(ids, prereqs, dependents):
	"""{id: column}: the length of the longest chain of quests before it."""
	missing = {i: len(prereqs[i]) for i in ids}
	layer = {i: 0 for i in ids}
	ready = [i for i in ids if missing[i] == 0]
	while ready:
		node = ready.pop()
		for after in dependents[node]:
			layer[after] = max(layer[after], layer[node] + 1)
			missing[after] -= 1
			if missing[after] == 0:
				ready.append(after)
	return layer


def _sweep(columns, prereqs, dependents):
	"""Order each column by where the quests it is linked to are, going back and forth, to cut the crossings."""
	fraction = {}
	for column in columns:
		for n, quest_id in enumerate(column):
			fraction[quest_id] = (n + 0.5) / len(column)
	for sweep in range(SWEEPS):
		forward = sweep % 2 == 0
		order = columns[1:] if forward else columns[-2::-1]
		for column in order:
			links = prereqs if forward else dependents
			key = {}
			for quest_id in column:
				near = [fraction[o] for o in links[quest_id] if o in fraction]
				key[quest_id] = sum(near) / len(near) if near else fraction[quest_id]
			column.sort(key=key.__getitem__)
			for n, quest_id in enumerate(column):
				fraction[quest_id] = (n + 0.5) / len(column)


def _place_group(graph, ids, name_of):
	"""(positions {id: (column, row)}, columns, rows, backwards) for one connected group."""
	prereqs, dependents, backwards = _split(graph, ids)
	layer = _layers(ids, prereqs, dependents)
	columns = [[] for _ in range(max(layer.values()) + 1)]
	for quest_id in sorted(ids, key=name_of):
		columns[layer[quest_id]].append(quest_id)
	for column in columns:
		column.sort(key=lambda i: (graph.nodes[i].trader, name_of(i)))
	_sweep(columns, prereqs, dependents)
	tallest = max(len(c) for c in columns)
	positions = {}
	for x, column in enumerate(columns):
		start = (tallest - len(column)) / 2
		for n, quest_id in enumerate(column):
			positions[quest_id] = (x, start + n)
	return positions, len(columns), tallest, backwards


def layout(graph, lanes=False):
	"""A Layout for the whole graph. With lanes=True each trader's quests keep to a band of rows of their own."""
	name_of = lambda i: graph.nodes[i].label.lower()
	result = Layout()
	if not graph.nodes:
		return result
	if lanes:
		return _layout_lanes(graph, name_of)
	row, isolated = 0.0, []
	for group in graph.groups():
		if len(group) == 1:
			isolated.append(next(iter(group)))
			continue
		positions, columns, rows, backwards = _place_group(graph, sorted(group), name_of)
		for quest_id, (x, y) in positions.items():
			result.positions[quest_id] = (x, row + y)
		result.backwards |= backwards
		result.columns = max(result.columns, columns)
		row += rows + 1
	if isolated:
		for n, quest_id in enumerate(sorted(isolated, key=name_of)):
			result.positions[quest_id] = (n % ISOLATED_PER_ROW, row + n // ISOLATED_PER_ROW)
		result.columns = max(result.columns, min(len(isolated), ISOLATED_PER_ROW))
		row += (len(isolated) + ISOLATED_PER_ROW - 1) // ISOLATED_PER_ROW + 1
	result.rows = max(row - 1, 0.0)
	return result


def _layout_lanes(graph, name_of):
	ids = list(graph.nodes)
	prereqs, dependents, backwards = _split(graph, ids)
	layer = _layers(ids, prereqs, dependents)
	count = {}
	for quest_id in ids:
		trader = graph.nodes[quest_id].trader
		count[trader] = count.get(trader, 0) + 1
	lane_order = sorted(count, key=lambda t: (t == "", -count[t], t))
	columns = [[] for _ in range(max(layer.values()) + 1)]
	for quest_id in sorted(ids, key=name_of):
		columns[layer[quest_id]].append(quest_id)
	for column in columns:
		column.sort(key=lambda i: (lane_order.index(graph.nodes[i].trader), name_of(i)))
	fraction = {}
	for sweep in range(SWEEPS):  # (order inside each lane by the links, the lanes themselves stay as they are)
		forward = sweep % 2 == 0
		for x in (range(1, len(columns)) if forward else range(len(columns) - 2, -1, -1)):
			links = prereqs if forward else dependents
			for n, quest_id in enumerate(columns[x]):
				fraction.setdefault(quest_id, (n + 0.5) / len(columns[x]))
			key = {}
			for quest_id in columns[x]:
				near = [fraction[o] for o in links[quest_id] if o in fraction]
				key[quest_id] = sum(near) / len(near) if near else fraction.get(quest_id, 0.5)
			columns[x].sort(key=lambda i: (lane_order.index(graph.nodes[i].trader), key[i]))
			for n, quest_id in enumerate(columns[x]):
				fraction[quest_id] = (n + 0.5) / len(columns[x])
	height = {}  # the rows a lane needs: the most quests it has in any column
	for column in columns:
		per_lane = {}
		for quest_id in column:
			trader = graph.nodes[quest_id].trader
			per_lane[trader] = per_lane.get(trader, 0) + 1
		for trader, n in per_lane.items():
			height[trader] = max(height.get(trader, 0), n)
	result, top = Layout(columns=len(columns), backwards=backwards), 0.0
	first = {}
	for trader in lane_order:
		first[trader] = top
		result.lanes.append((trader, top, top + height[trader] - 1))
		top += height[trader] + 1
	for x, column in enumerate(columns):
		used = {}
		for quest_id in column:
			trader = graph.nodes[quest_id].trader
			result.positions[quest_id] = (x, first[trader] + used.get(trader, 0))
			used[trader] = used.get(trader, 0) + 1
	result.rows = max(top - 1, 0.0)
	return result
