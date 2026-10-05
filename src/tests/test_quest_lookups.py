"""A quest lock to a quest that is in the base game or a reference file is fine; only a quest nobody knows is flagged."""

import json
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication, QLabel

from core import references as R
from core.documents import Document
from core.gamedata import GameData
from core.paths import BUNDLED_DATABASE_DIR
from schema import assort as A
from schema import explorer
from ui.assort_tab import AssortTab

DEBUT = "5936d90786f7742b1420ba5b"  # a base-game quest
MOD_QUEST, OPEN_QUEST, NOBODY = "1" * 24, "2" * 24, "9" * 24
TPL = "5449016a4bdc2d6f028b456f"


@pytest.fixture(scope="module")
def app():
	return QApplication.instance() or QApplication([])


def game(tmp_path):
	quest_file = tmp_path / "other_mod.json"
	quest_file.write_text(json.dumps({MOD_QUEST: {"_id": MOD_QUEST, "QuestName": "Other mod quest", "conditions": {}, "rewards": {}}}), encoding="utf-8")
	data = GameData(None, "en", BUNDLED_DATABASE_DIR)
	data.references = R.References(tmp_path / "list.json")
	data.references.add([quest_file])
	return data


def lock_labels(tmp_path, lock_to, gamedata):
	items, barter, level = A.new_offer(TPL)
	offer = items[0]["_id"]
	assort_doc = Document({"items": items, "barter_scheme": {offer: barter}, "loyal_level_items": {offer: level}})
	locks = Document(A.empty_questassort())
	locks.data["success"][offer] = lock_to
	quests = Document({OPEN_QUEST: {"_id": OPEN_QUEST, "QuestName": "Open", "rewards": {"Success": [], "Started": [], "Fail": []}}})
	tab = AssortTab(assort_doc, locks, gamedata, None, None, lambda: quests.data, lambda: quests)
	tab.refresh(offer)
	return [label.text() for label in tab.right.findChildren(QLabel)]


def test_where_a_quest_comes_from(tmp_path):
	data = game(tmp_path)
	assert data.quest_source(DEBUT) == "the base game" and data.quest_source(MOD_QUEST) == "other_mod.json"
	assert data.quest_source(NOBODY) == "" and data.knows_quest(MOD_QUEST) and not data.knows_quest(NOBODY)


def test_a_lock_to_a_quest_from_elsewhere_is_not_a_problem_but_a_lock_to_a_quest_nobody_knows_is(app, tmp_path):
	data = game(tmp_path)
	assert "This quest is in the base game, not in the open quest file." in lock_labels(tmp_path, DEBUT, data)
	assert "This quest is in other_mod.json, not in the open quest file." in lock_labels(tmp_path, MOD_QUEST, data)
	unknown = lock_labels(tmp_path, NOBODY, data)
	assert "That quest isn't in the open quest file, the base game or the reference files." in unknown
	assert not any("This quest is in" in text for text in unknown)
	assert "That quest isn't in the open quest file." in lock_labels(tmp_path, NOBODY, None)  # (no game data: nothing else to look in)


def test_the_check_of_a_quest_assort_file_only_flags_quests_nobody_knows(tmp_path):
	data = game(tmp_path)
	locks = {"started": {}, "success": {"a" * 24: DEBUT, "b" * 24: MOD_QUEST, "c" * 24: OPEN_QUEST, "d" * 24: NOBODY}, "fail": {}}
	issues = explorer.check(locks, "questassort", {OPEN_QUEST: {}}, None, data)
	assert [i.path for i in issues] == [("success", "d" * 24)] and "isn't known" in issues[0].message
	# (with no quest file open the base game and the references are still looked in)
	assert [i.path for i in explorer.check(locks, "questassort", None, None, data)] == [("success", "c" * 24), ("success", "d" * 24)]
	assert explorer.check(locks, "questassort", None, None, None) == []  # (nothing to look in: nothing to say)
