"""The quests as a graph: which quest needs which. No Qt.

Every quest the program knows is a node: the quests open in the Quests tab (opened or imported), the quests in the reference
files, and the base game's. A link is a "Quest" condition: a quest that has to be in some state (completed, started, failed)
before this one can start (or be finished), or whose completion makes this one fail. Anything else a quest needs to start
(player level, trader level, trader standing) is kept on the node as a note.
"""

from dataclasses import dataclass, field

OPEN, REFERENCE, GAME, UNKNOWN = "open", "reference", "game", "unknown"
SOURCE_LABEL = {OPEN: "Your quests", REFERENCE: "Reference files", GAME: "Base game", UNKNOWN: "Not found"}

# the kinds of link
COMPLETED, STARTED, FAILED, ANY, FAILS = "completed", "started", "failed", "any", "fails"
KIND_LABEL = {
	COMPLETED: "after completing", STARTED: "after starting", FAILED: "after failing", ANY: "after it reaches a state",
	FAILS: "fails this quest when it is done",
}
ORDERING = (COMPLETED, STARTED, FAILED, ANY)  # (the kinds of link that put one quest after another; "fails" does not)
# where in the quest the condition is
START, FINISH, FAIL = "start", "finish", "fail"
LIST_OF = {"AvailableForStart": START, "AvailableForFinish": FINISH, "Fail": FAIL}

STATUS_WORDS = {
	1: "available", 2: "started", 3: "ready to hand in", 4: "completed", 5: "failed", 6: "failed (can be redone)",
	7: "marked as failed", 8: "expired", 9: "available after a wait",
}


@dataclass(frozen=True)
class Edge:
	"""`source` has to be in one of `statuses` before `target` can start (list "start") or be finished ("finish"); with
	kind "fails", `target` fails when `source` reaches one of them (list "fail"). wait is seconds (0: none)."""

	source: str
	target: str
	kind: str
	list: str = START
	statuses: tuple = (4,)
	wait: int = 0

	def words(self):
		states = " or ".join(STATUS_WORDS.get(s, str(s)) for s in self.statuses)
		return f"{states}" + (f", then a wait of {wait_words(self.wait)}" if self.wait else "")


@dataclass
class QuestNode:
	id: str
	name: str = ""
	trader: str = ""  # trader id
	level: int = None  # the player level it needs, if it says
	source: str = UNKNOWN
	source_name: str = ""  # the file it came from (open and imported quests: the file it was imported from, else ""; reference: the file)
	notes: list = field(default_factory=list)  # other things it needs to start: "Level 12", "Prapor loyalty level 2"
	also_in: list = field(default_factory=list)  # other sources that have a quest with this id

	@property
	def label(self):
		return self.name or f"{self.id[:10]}..."

	@property
	def where(self):
		"""Where the quest is from, in words."""
		if self.source == OPEN:
			return "your quest" + (f" (imported from {self.source_name})" if self.source_name else "")
		if self.source == REFERENCE:
			return f"reference file {self.source_name}"
		return "base game" if self.source == GAME else "not found in any file"


def wait_words(seconds):
	"""'45 min', '21 h', '2 days' for a wait in seconds."""
	seconds = int(seconds or 0)
	if seconds >= 86400 and seconds % 86400 == 0:
		days = seconds // 86400
		return f"{days} day{'' if days == 1 else 's'}"
	if seconds >= 3600:
		hours = seconds / 3600
		return f"{hours:g} h"
	if seconds >= 60:
		return f"{seconds // 60} min"
	return f"{seconds} s"


def kind_of(statuses):
	"""The kind of link for the states a quest has to be in."""
	states = set(statuses)
	if states == {4}:
		return COMPLETED
	if states == {2}:
		return STARTED
	if states == {5}:
		return FAILED
	return ANY


def _statuses(condition):
	raw = condition.get("status")
	if isinstance(raw, list) and raw and all(isinstance(s, int) and not isinstance(s, bool) for s in raw):
		return tuple(raw)
	return (4,)  # (no state given: the quest has to be completed)


def _targets(condition):
	target = condition.get("target")
	if isinstance(target, str):
		return [target]
	return [t for t in target if isinstance(t, str)] if isinstance(target, list) else []


def _compare(method):
	return {">=": "at least", ">": "above", "<=": "at most", "<": "below", "==": "exactly", "!=": "not"}.get(method, "")


def _quest_conditions(quest):
	"""[(list name, condition dict)] of a quest's conditions that are well-formed."""
	conditions = quest.get("conditions") if isinstance(quest, dict) else None
	if not isinstance(conditions, dict):
		return []
	return [(key, c) for key, items in conditions.items() if isinstance(items, list) for c in items if isinstance(c, dict)]


def node_from(quest_id, quest, source, source_name="", name="", trader_name=lambda trader_id: ""):
	"""The node for a quest dict (its notes are what it needs to start besides other quests)."""
	node = QuestNode(
		quest_id, name or (quest.get("QuestName") or "" if isinstance(quest, dict) else ""),
		(quest.get("traderId") or "") if isinstance(quest, dict) else "", None, source, source_name,
	)
	for list_name, condition in _quest_conditions(quest):
		if list_name != "AvailableForStart":
			continue
		kind, value = condition.get("conditionType"), condition.get("value")
		if kind == "Level" and isinstance(value, (int, float)) and not isinstance(value, bool):
			node.notes.append(f"Player level {_compare(condition.get('compareMethod'))} {value:g}".replace("  ", " "))
			if node.level is None and condition.get("compareMethod") in (">=", ">", "==", None):
				node.level = int(value)
		elif kind in ("TraderLoyalty", "TraderStanding") and isinstance(value, (int, float)):
			who = trader_name(condition.get("target")) or "A trader"
			what = "loyalty level" if kind == "TraderLoyalty" else "standing"
			node.notes.append(f"{who} {what} {_compare(condition.get('compareMethod'))} {value:g}".replace("  ", " "))
	return node


def edges_from(quest_id, quest):
	"""The links a quest's "Quest" conditions make, as Edges (the other quest first)."""
	found = []
	for list_name, condition in _quest_conditions(quest):
		if condition.get("conditionType") != "Quest" or list_name not in LIST_OF:
			continue
		statuses = _statuses(condition)
		wait = condition.get("availableAfter") if isinstance(condition.get("availableAfter"), (int, float)) else 0
		for other in _targets(condition):
			if other == quest_id:
				continue
			if list_name == "Fail":
				found.append(Edge(other, quest_id, FAILS, FAIL, statuses, int(wait or 0)))
			else:
				found.append(Edge(other, quest_id, kind_of(statuses), LIST_OF[list_name], statuses, int(wait or 0)))
	return found


class QuestGraph:
	"""nodes {id: QuestNode} and edges [Edge]. A quest that a link names but nobody has is a node with source UNKNOWN."""

	def __init__(self, nodes=None, edges=None):
		self.nodes = dict(nodes or {})
		self.edges = list(edges or [])
		self._into, self._out = None, None

	def _index(self):
		if self._into is None:
			self._into, self._out = {}, {}
			for edge in self.edges:
				self._out.setdefault(edge.source, []).append(edge)
				self._into.setdefault(edge.target, []).append(edge)

	def needs(self, quest_id, kinds=None):
		"""The links into this quest (what it needs, and what makes it fail)."""
		self._index()
		return [e for e in self._into.get(quest_id, []) if kinds is None or e.kind in kinds]

	def opens(self, quest_id, kinds=None):
		"""The links out of this quest (what needs it)."""
		self._index()
		return [e for e in self._out.get(quest_id, []) if kinds is None or e.kind in kinds]

	def reach(self, quest_id, back=1, forward=1):
		"""The ids within `back` steps before this quest and `forward` steps after it (None: all the way), through the conditions
		that decide when a quest can start, and the quest itself. The quests this one is linked to some other way (it can only
		be finished after them, or it fails with them) are added too."""
		found = {quest_id}
		for direction, limit in (("back", back), ("forward", forward)):
			frontier, steps = {quest_id}, 0
			while frontier and (limit is None or steps < limit):
				step = set()
				for node in frontier:
					for edge in (self.needs(node, ORDERING) if direction == "back" else self.opens(node, ORDERING)):
						other = edge.source if direction == "back" else edge.target
						if edge.list == START and other not in found:
							step.add(other)
				found |= step
				frontier, steps = step, steps + 1
		for edge in self.needs(quest_id) + self.opens(quest_id):
			if edge.list != START:
				found.add(edge.source)
				found.add(edge.target)
		return found

	def neighbours_failing(self, ids):
		"""The ids joined by a "fails" link to any of these."""
		self._index()
		found = set()
		for quest_id in ids:
			for edge in self._out.get(quest_id, []) + self._into.get(quest_id, []):
				if edge.kind == FAILS:
					found.add(edge.source)
					found.add(edge.target)
		return found

	def subgraph(self, ids):
		ids = set(ids)
		return QuestGraph({i: n for i, n in self.nodes.items() if i in ids}, [e for e in self.edges if e.source in ids and e.target in ids])

	def groups(self):
		"""The connected groups of quests (any kind of link), biggest first, each a set of ids."""
		neighbours = {}
		for edge in self.edges:
			neighbours.setdefault(edge.source, set()).add(edge.target)
			neighbours.setdefault(edge.target, set()).add(edge.source)
		seen, groups = set(), []
		for start in self.nodes:
			if start in seen:
				continue
			group, stack = set(), [start]
			while stack:
				node = stack.pop()
				if node in group:
					continue
				group.add(node)
				stack.extend(neighbours.get(node, set()) - group)
			seen |= group
			groups.append(group)
		return sorted(groups, key=len, reverse=True)

	def loops(self):
		"""The sets of quests that need each other in a circle to start (so none of them can ever start). Each is a list of ids.
		A quest that can only be finished after another is not a loop: it can still start."""
		adjacent = {i: [e.target for e in self.opens(i, ORDERING) if e.list == START and e.target in self.nodes] for i in self.nodes}
		index, low, on, stack, found, counter = {}, {}, set(), [], [], [0]
		for root in self.nodes:  # (Tarjan's strongly connected components, without recursion)
			if root in index:
				continue
			work = [(root, iter(adjacent[root]))]
			index[root] = low[root] = counter[0]
			counter[0] += 1
			stack.append(root)
			on.add(root)
			while work:
				node, children = work[-1]
				advanced = False
				for child in children:
					if child not in index:
						index[child] = low[child] = counter[0]
						counter[0] += 1
						stack.append(child)
						on.add(child)
						work.append((child, iter(adjacent[child])))
						advanced = True
						break
					if child in on:
						low[node] = min(low[node], index[child])
				if advanced:
					continue
				work.pop()
				if work:
					low[work[-1][0]] = min(low[work[-1][0]], low[node])
				if low[node] == index[node]:
					part = []
					while True:
						member = stack.pop()
						on.discard(member)
						part.append(member)
						if member == node:
							break
					if len(part) > 1 or node in adjacent[node]:
						found.append(part)
		return found

	def unknown(self):
		return [i for i, n in self.nodes.items() if n.source == UNKNOWN]


def build_graph(open_quests=None, references=None, game=None, imported=None, trader_name=lambda trader_id: "", game_name=lambda quest_id: ""):
	"""The graph of every quest known.

	open_quests: {id: quest} open in the Quests tab; imported: {id: file name} for those that came from an imported file.
	references: a core.references.References (its quest files). game: {id: quest} of the base game; game_name(id) gives a
	quest's name in the chosen language. A quest in more than one place is the first of: open, reference, game (the others
	are noted on it)."""
	nodes, quests = {}, {}
	imported = imported or {}

	def add(quest_id, quest, source, source_name, name=""):
		if not isinstance(quest, dict):
			return
		if quest_id in nodes:
			nodes[quest_id].also_in.append(SOURCE_LABEL[source] + (f" ({source_name})" if source_name else ""))
			return
		nodes[quest_id] = node_from(quest_id, quest, source, source_name, name, trader_name)
		quests[quest_id] = quest

	for quest_id, quest in (open_quests or {}).items():
		add(quest_id, quest, OPEN, imported.get(quest_id, ""))
	if references is not None:
		for quest_id, (quest, file_name) in references.quest_data().items():
			add(quest_id, quest, REFERENCE, file_name)
	for quest_id, quest in (game or {}).items():
		add(quest_id, quest, GAME, "", game_name(quest_id))
	edges = []
	for quest_id, quest in quests.items():
		edges.extend(edges_from(quest_id, quest))
	for edge in edges:  # (a quest nobody has: shown, so the link to it is not lost)
		for other in (edge.source, edge.target):
			if other not in nodes:
				nodes[other] = QuestNode(other, "", "", None, UNKNOWN)
	return QuestGraph(nodes, edges)
