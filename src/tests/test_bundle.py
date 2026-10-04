import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import bundle_database


def test_bundle_copies_and_trims(tmp_path):
	src, dst = tmp_path / "src", tmp_path / "dst"
	(src / "templates").mkdir(parents=True)
	(src / "templates" / "items.json").write_text("{}")
	(src / "globals.json").write_text(json.dumps({"ItemPresets": {"a": 1}, "huge": list(range(100))}))
	(src / "traders" / "t1").mkdir(parents=True)
	(src / "traders" / "t1" / "base.json").write_text("{}")
	(src / "traders" / "t1" / "questassort.json").write_text("{}")
	(src / "traders" / "t1" / "assort.json").write_text("{}")
	(src / "locations").mkdir()
	copied = bundle_database.bundle(src, dst, ["en"])
	assert json.loads((dst / "globals.json").read_text()) == {"ItemPresets": {"a": 1}}
	assert not (dst / "locations").exists()
	assert not (dst / "traders").exists()  # (the traders come from data/traders.json, not from a copy of their folders)
	assert "templates/items.json" in copied
