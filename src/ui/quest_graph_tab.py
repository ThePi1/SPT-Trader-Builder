"""The Quest Graph tab: every quest the program knows as a flowchart of which quest needs which.

The quests are the ones open in the Quests tab (opened or imported), the ones in the reference files and the base game's. The
graph is built when the tab is shown (and again, a moment after a change, while it is showing). The layout of the tab is
ui/designer/quest_graph_tab.ui; the drawing is ui/graph_view.py.
"""

from dataclasses import dataclass, field

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QApplication, QWidget

from core import graphlayout, questgraph as G
from ui.compiled.ui_quest_graph_tab import Ui_QuestGraphForm
from ui.graph_view import GraphView, swatch, trader_colors

EVERYTHING, AROUND = "everything", "around"


@dataclass
class Sources:
	"""What the graph is built from (the window fills this in each time)."""

	open_quests: dict = field(default_factory=dict)  # {id: quest} in the Quests tab
	imported: dict = field(default_factory=dict)  # {id: file name} for the ones that were imported
	references: object = None  # core.references.References
	game: dict = field(default_factory=dict)  # {id: quest} of the base game
	trader_names: dict = field(default_factory=dict)  # {trader id: name}
	game_name: object = lambda quest_id: ""  # quest id -> its name in the chosen language


def _plural(n, word):
	return f"{n:,} {word}{'' if n == 1 else 's'}".replace(",", " ")


class QuestGraphTab(QWidget, Ui_QuestGraphForm):
	"""provider() gives the Sources. open_requested(quest id) is sent for a quest of yours that should be opened in the Quests tab."""

	open_requested = Signal(str)

	def __init__(self, provider, parent=None):
		super().__init__(parent)
		self.setupUi(self)
		self.provider = provider
		self.graph = G.QuestGraph()
		self.layout_ = None
		self.shown = set()
		self.sources = Sources()
		self.hues = {}
		self._stale, self._busy = True, False
		self._focus = ""  # the quest the picture is drawn around (when it is)
		self.view = GraphView()
		self.viewLayout.addWidget(self.view)
		self.modeBox.addItem("Everything", EVERYTHING)
		self.modeBox.addItem("Around the selected quest", AROUND)
		self.traderBox.addItem("All traders", "")
		self._timer = QTimer(self)
		self._timer.setSingleShot(True)
		self._timer.setInterval(300)
		self._timer.timeout.connect(self.refresh)
		self.view.node_selected.connect(self._selected)
		self.view.node_activated.connect(self._activated)
		self.search.returnPressed.connect(self.go_to_match)
		for box in (self.traderBox, self.modeBox):
			box.currentIndexChanged.connect(lambda _i: self._render())
		self.stepsBox.valueChanged.connect(lambda _n: self._render() if self._around() else None)
		for box in (self.openBox, self.referenceBox, self.gameBox, self.lanesBox):
			box.toggled.connect(lambda _checked: self._render())
		for box in (self.failsBox, self.finishBox):
			box.toggled.connect(lambda _checked: self._show_kinds())
		self.fitButton.clicked.connect(lambda _checked=False: self.view.fit())
		self.openButton.clicked.connect(lambda _checked=False: self.open_requested.emit(self._current_id()))
		self._show_legend()

	# --- keeping up with the quests ---------------------------------------------------------------
	def invalidate(self):
		"""The quests may have changed: build the graph again (a moment later if the tab is showing, else when it is next shown)."""
		self._stale = True
		if self.isVisible():
			self._timer.start()

	def refresh_if_stale(self):
		if self._stale:
			self.refresh()

	def showEvent(self, event):
		super().showEvent(event)
		self.refresh_if_stale()

	def refresh(self):
		"""Build the graph from what is known now, and draw it."""
		self._stale = False
		self.sources = self.provider()
		source = self.sources
		self.graph = G.build_graph(
			open_quests=source.open_quests, references=source.references, game=source.game, imported=source.imported,
			trader_name=lambda trader_id: source.trader_names.get(trader_id, ""), game_name=source.game_name,
		)
		counts = {}
		for node in self.graph.nodes.values():
			counts[node.trader] = counts.get(node.trader, 0) + 1
		ordered = sorted(counts, key=lambda t: (t == "", -counts[t], t))
		self.hues = trader_colors(ordered)
		keep = self.traderBox.currentData()
		self.traderBox.blockSignals(True)
		self.traderBox.clear()
		self.traderBox.addItem("All traders", "")
		for trader in ordered:
			name = source.trader_names.get(trader) or ("No trader" if not trader else f"{trader[:8]}...")
			self.traderBox.addItem(f"{name} ({counts[trader]})", trader)
		self.traderBox.setCurrentIndex(max(0, self.traderBox.findData(keep)))
		self.traderBox.blockSignals(False)
		self._render(fit=True)

	# --- what is drawn ----------------------------------------------------------------------------------
	def _around(self):
		return self.modeBox.currentData() == AROUND

	def _current_id(self):
		chosen = self.view.graph_scene.selectedItems() if self.view.graph_scene else []
		return chosen[0].node.id if chosen else ""

	def _wanted(self):
		"""The ids to draw: the sources and the trader chosen, or the quests around the selected one."""
		allowed = {G.OPEN: self.openBox.isChecked(), G.REFERENCE: self.referenceBox.isChecked(), G.GAME: self.gameBox.isChecked()}
		graph, selected = self.graph, self._current_id()
		ids = {i for i, n in graph.nodes.items() if allowed.get(n.source, False)}
		if self._around() and selected in graph.nodes:
			steps = self.stepsBox.value() or None
			ids &= graph.reach(selected, steps, steps) | {selected}
			ids |= graph.neighbours_failing({selected}) & {i for i, n in graph.nodes.items() if allowed.get(n.source, False)}
		else:
			trader = self.traderBox.currentData()
			if trader:
				ids = {i for i in ids if graph.nodes[i].trader == trader}
		for node_id in [i for i in graph.nodes if graph.nodes[i].source == G.UNKNOWN]:
			if any(e.source in ids or e.target in ids for e in graph.needs(node_id) + graph.opens(node_id)):
				ids.add(node_id)  # (a quest nobody has, but one that is drawn needs it or is needed by it)
		return ids

	def _render(self, fit=True):
		if self._busy:
			return
		self._busy = True
		try:
			selected = self._current_id()
			self._focus = selected if self._around() and selected in self.graph.nodes else ""
			self.shown = self._wanted()
			sub = self.graph.subgraph(self.shown)
			self.layout_ = graphlayout.layout(sub, lanes=self.lanesBox.isChecked())
			QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))
			try:
				self.view.show_graph(sub, self.layout_, self.sources.trader_names, self.hues, fit=fit)
			finally:
				QApplication.restoreOverrideCursor()
			self._show_kinds()
			if selected in self.shown:
				self.view.select(selected, center=False)
			self._summary()
			self._selected(self._current_id(), render=False)
		finally:
			self._busy = False

	def _show_kinds(self):
		if self.view.graph_scene is not None:
			self.view.graph_scene.show_kinds(fails=self.failsBox.isChecked(), finish=self.finishBox.isChecked())

	def _summary(self):
		sub_edges = sum(1 for e in self.graph.edges if e.source in self.shown and e.target in self.shown)
		text = f"{_plural(len(self.shown), 'quest')} drawn of {_plural(len(self.graph.nodes), 'quest')}, {_plural(sub_edges, 'link')}."
		missing = [self.graph.nodes[i].label for i in self.graph.unknown() if i in self.shown]
		if missing:
			text += f" {_plural(len(missing), 'quest')} that a link names but no file has."
		loops = self.graph.loops()
		if loops:
			text += " These quests need each other to start, so none of them can start: " + "; ".join(
				", ".join(self.graph.nodes[i].label for i in loop[:4]) for loop in loops[:3]) + "."
		self.info.setText(text)

	# --- the selected quest ----------------------------------------------------------------------------------
	def _selected(self, quest_id, render=True):
		scene = self.view.graph_scene
		if self._busy and render:
			return
		if quest_id and quest_id in self.graph.nodes:
			self._show_quest(self.graph.nodes[quest_id])
			if scene is not None and not self._around():
				scene.highlight(self.graph.reach(quest_id, None, None) | self.graph.neighbours_failing({quest_id}))
			if render and self._around() and quest_id != self._focus:  # (draw what is around this quest now)
				self._render(fit=True)
				item = self.view.graph_scene.items_by_id.get(quest_id)
				if item is not None:
					self.view.centerOn(item)
		else:
			if scene is not None:
				scene.highlight(None)
			self.openButton.setVisible(False)
			self._show_legend()

	def _show_legend(self):
		dark = self.view.dark
		keys = " &nbsp; ".join(
			f'<span style="color: {swatch(hue, dark)[1].name()};">&#9632;</span> {name}'
			for trader, hue in self.hues.items() if (name := self.sources.trader_names.get(trader) or (not trader and "no trader"))
		)
		self.details.setText(
			(f"{keys}<br>" if keys else "") +
			"Thick border: your quest. Dashed: a reference file. Thin: the base game. Dotted: nobody has it. "
			"Solid arrow: after completing. Dashed: after starting. Dotted: needed to finish. Red dotted: fails the other quest. "
			"Click a quest to follow its chain; double-click one of yours to open it."
		)

	def _show_quest(self, node):
		graph = self.graph
		name = lambda i: graph.nodes[i].label
		needs = [e for e in graph.needs(node.id) if e.kind != G.FAILS]
		opens = [e for e in graph.opens(node.id) if e.kind != G.FAILS]
		fails = {e.source if e.target == node.id else e.target for e in graph.edges if e.kind == G.FAILS and node.id in (e.source, e.target)}
		trader = self.sources.trader_names.get(node.trader, "")
		lines = [f"<b>{_esc(node.label)}</b> &middot; {_esc(trader) or 'no trader'}" + (f" &middot; level {node.level}" if node.level is not None else "")
			+ f" &middot; {_esc(node.where)}"]
		if node.notes:
			lines.append("Needs " + _esc("; ".join(node.notes)))
		if needs:
			lines.append("Comes after: " + _esc(", ".join(f"{name(e.source)} ({e.words()})" for e in needs[:6])) + (f" and {len(needs) - 6} more" if len(needs) > 6 else ""))
		if opens:
			lines.append(f"Opens {len(opens)}: " + _esc(", ".join(name(e.target) for e in opens[:6])) + (" ..." if len(opens) > 6 else ""))
		if fails:
			lines.append("Fails with: " + _esc(", ".join(name(i) for i in sorted(fails)[:4])))
		if node.also_in:
			lines.append("Also in: " + _esc(", ".join(node.also_in)))
		if node.source == G.UNKNOWN:
			lines.append("No file the program has holds this quest.")
		self.details.setText("<br>".join(lines))
		self.openButton.setVisible(node.source == G.OPEN)

	def _activated(self, quest_id):
		node = self.graph.nodes.get(quest_id)
		if node is not None and node.source == G.OPEN:
			self.open_requested.emit(quest_id)

	# --- finding a quest -------------------------------------------------------------------------------------
	def matches(self, text):
		"""The ids of the quests whose name or id has all the words of text, open quests first."""
		words = text.lower().split()
		found = [i for i, n in self.graph.nodes.items() if words and all(w in f"{n.label} {i}".lower() for w in words)]
		rank = {G.OPEN: 0, G.REFERENCE: 1, G.GAME: 2, G.UNKNOWN: 3}
		return sorted(found, key=lambda i: (rank[self.graph.nodes[i].source], self.graph.nodes[i].label.lower()))

	def go_to_match(self):
		"""Select the first quest that matches the search (and show everything if it is not drawn now)."""
		found = self.matches(self.search.text())
		if not found:
			self.info.setText("No quest matches that.")
			return None
		target = found[0]
		if target not in self.shown:
			self._busy = False
			for box in (self.openBox, self.referenceBox, self.gameBox):
				box.blockSignals(True)
				box.setChecked(True)
				box.blockSignals(False)
			self.traderBox.blockSignals(True)
			self.traderBox.setCurrentIndex(0)
			self.traderBox.blockSignals(False)
			self.modeBox.blockSignals(True)
			self.modeBox.setCurrentIndex(0)
			self.modeBox.blockSignals(False)
			self._render()
		self._busy = True  # (the selection is made here: nothing to draw again)
		try:
			self.view.select(target)
		finally:
			self._busy = False
		self._selected(target, render=False)
		if len(found) > 1:
			self.info.setText(f"{_plural(len(found), 'quest')} match; showing the first. Press Enter again after changing the words to narrow it.")
		return target


def _esc(text):
	return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
