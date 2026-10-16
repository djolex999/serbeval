import json
from pathlib import Path

from serbeval.cli import main

ROW = {"id": "srb-x-0001", "task": "srb_grammar_cloze", "category": "padezi", "question": "A ____.",
       "cue": "b", "answers": ["b"], "explanation": "", "script": "latin", "difficulty": "easy",
       "source": "handwritten", "verified": True, "license": "CC-BY-4.0"}


def test_rebuilding_the_official_set_keeps_version_and_errata(tmp_path: Path) -> None:
    # v1.1 errata live in MANIFEST.json; a rebuild must not silently reset them to "v1".
    data = tmp_path / "data"
    (data / "srb_grammar_cloze").mkdir(parents=True)
    (data / "srb_grammar_cloze" / "items.jsonl").write_text(json.dumps(ROW) + "\n")
    (data / "official").mkdir()
    errata = {"date": "2026-10-17", "dropped": {"srb-x-0002": "bad cue"}}
    (data / "official" / "MANIFEST.json").write_text(
        json.dumps({"version": "v1.1", "errata": errata, "items": {}}))
    core = tmp_path / "core.txt"
    core.write_text("")
    assert main(["official", "--data-dir", str(data), "--core", str(core),
                 "--disputed", str(tmp_path / "none"), "--models", "m"]) == 0
    manifest = json.loads((data / "official" / "MANIFEST.json").read_text())
    assert manifest["version"] == "v1.1"
    assert manifest["errata"] == errata
    assert manifest["items"] == {"srb-x-0001": "human"}
