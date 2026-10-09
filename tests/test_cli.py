import gzip
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

import serbeval.cli as cli
from serbeval.cli import main


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")


def valid_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "id": "srb-grammar-padezi-0001",
        "task": "srb_grammar",
        "category": "padezi",
        "question": "Dopuni rečenicu: Pišem ____.",
        "choices": ["olovkom", "sa olovkom", "olovka", "olovku"],
        "answer_index": 0,
        "explanation": "Instrumental sredstva ide bez predloga 'sa'.",
        "script": "latin",
        "source": "handwritten-claude",
    }
    row.update(overrides)
    return row


def test_validate_clean_file_exits_zero(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "items.jsonl"
    write_jsonl(path, [valid_row()])
    assert main(["validate", str(path)]) == 0
    assert "OK" in capsys.readouterr().out


def test_validate_broken_file_exits_one(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "items.jsonl"
    write_jsonl(path, [valid_row(), valid_row()])  # duplicate id
    assert main(["validate", str(path)]) == 1
    assert "duplicate id" in capsys.readouterr().out


def test_validate_schema_error_exits_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "items.jsonl"
    write_jsonl(path, [valid_row(answer_index=9)])
    assert main(["validate", str(path)]) == 1


def test_generate_subcommand_wiring(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from serbeval.generate import CandidateBatch, CandidateItem

    batch = CandidateBatch(
        items=[
            CandidateItem(
                question="Q?", choices=["a", "b", "c", "d"], answer_index=0, explanation="x"
            )
        ]
    )
    client = Mock()
    client.messages.parse.return_value = Mock(parsed_output=batch)
    monkeypatch.setattr(cli, "_make_client", lambda: client)

    code = main(
        ["generate", "--task", "srb_grammar", "--category", "padezi", "-n", "1",
         "--data-dir", str(tmp_path)]
    )
    assert code == 0
    assert "wrote 1 new candidate" in capsys.readouterr().out
    assert (tmp_path / "srb_grammar" / "candidates.jsonl").exists()


def test_selfcheck_subcommand_wiring(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    write_jsonl(
        tmp_path / "srb_grammar" / "candidates.jsonl",
        [valid_row(id="srb-grammar-padezi-0001", source="generated-claude-x")],
    )
    replies = iter(["A", "A", "A"])
    client = Mock()
    client.messages.create.side_effect = lambda **_: Mock(
        content=[Mock(type="text", text=next(replies))]
    )
    monkeypatch.setattr(cli, "_make_client", lambda: client)

    code = main(["selfcheck", "--task", "srb_grammar", "--runs", "3", "--data-dir", str(tmp_path)])
    assert code == 0
    assert "kept 1, discarded 0" in capsys.readouterr().out


def test_stats_subcommand(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write_jsonl(tmp_path / "srb_grammar" / "items.jsonl", [valid_row(verified=True)])
    assert main(["stats", "--data-dir", str(tmp_path)]) == 0
    assert "1/1" in capsys.readouterr().out


def test_report_subcommand_writes_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    results = {
        "results": {"srb_grammar": {"alias": "srb_grammar", "exact_match,extract_answer": 0.5}},
        "config": {"model": "anthropic-chat", "model_args": "model=claude-haiku-4-5"},
    }
    run_dir = tmp_path / "results" / "haiku-4-5"
    run_dir.mkdir(parents=True)
    (run_dir / "results_2026-06-14T12-00-00.json").write_text(json.dumps(results))
    out = tmp_path / "SUMMARY.md"
    assert main(["report", "--results-dir", str(tmp_path / "results"), "--out", str(out)]) == 0
    assert "claude-haiku-4-5" in out.read_text(encoding="utf-8")
    assert "OK: wrote" in capsys.readouterr().out


def test_review_subcommand_wiring(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    write_jsonl(tmp_path / "srb_grammar" / "items.jsonl", [valid_row()])
    monkeypatch.setattr("builtins.input", lambda _prompt: "y")
    assert main(["review", "--task", "srb_grammar", "--data-dir", str(tmp_path)]) == 0
    assert "verified 1" in capsys.readouterr().out
def test_lint_exits_zero_even_when_it_finds_problems(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # lint is advisory by design: it must never fail a build the way validate does.
    path = tmp_path / "items.jsonl"
    write_jsonl(
        path,
        [
            valid_row(
                choices=[
                    "Pišem pismo olovkom koju si mi poklonio.",
                    "Juče je padala kiša ceo dan bez prestanka.",
                    "Sutra putujemo na more ako bude lepo vreme.",
                    "Voz za Novi Sad kasni petnaest minuta.",
                ]
            )
        ],
    )
    assert main(["lint", str(path)]) == 0
    out = capsys.readouterr().out
    assert "two-way-mcq" in out


def test_lint_reports_a_clean_file_as_clean(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "items.jsonl"
    write_jsonl(
        path,
        [
            valid_row(
                choices=[
                    "Pišem pismo olovkom koju si mi poklonio.",
                    "Pišem pismo sa olovkom koju si mi poklonio.",
                    "Pišem pismo o olovkom koju si mi poklonio.",
                    "Pišem pismo za olovkom koju si mi poklonio.",
                ]
            )
        ],
    )
    assert main(["lint", str(path)]) == 0
    assert "no weak items" in capsys.readouterr().out


def test_lint_fails_on_a_malformed_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "items.jsonl"
    path.write_text("{not json}\n", encoding="utf-8")
    assert main(["lint", str(path)]) == 1
    assert "FAIL" in capsys.readouterr().out


def test_report_prints_the_table_and_the_statistics_together(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run_dir = tmp_path / "haiku" / "claude-haiku-4-5"
    run_dir.mkdir(parents=True)
    (run_dir / "results_2026-09-02T00-00-00.json").write_text(
        json.dumps(
            {
                "results": {
                    "srb_grammar": {
                        "alias": "srb_grammar",
                        "exact_match,extract_answer": 0.5,
                    }
                },
                "config": {"model": "anthropic-chat", "model_args": "model=claude-haiku-4-5"},
            }
        ),
        encoding="utf-8",
    )
    write_jsonl(
        run_dir / "samples_srb_grammar_2026-09-02T00-00-00.jsonl",
        [
            {"doc_id": 0, "doc": valid_row(), "exact_match": 1.0},
            {"doc_id": 1, "doc": valid_row(id="b"), "exact_match": 0.0},
        ],
    )
    assert main(["report", "--results-dir", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "| Model | Task |" in out       # aggregate table
    assert "claude-haiku-4-5" in out
    assert "95% CI" in out                 # statistics appended below it


def test_report_without_logged_samples_says_so_instead_of_faking_intervals(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run_dir = tmp_path / "haiku"
    run_dir.mkdir(parents=True)
    (run_dir / "results_2026-09-02T00-00-00.json").write_text(
        json.dumps(
            {
                "results": {"srb_grammar": {"exact_match,extract_answer": 0.5}},
                "config": {},
            }
        ),
        encoding="utf-8",
    )
    assert main(["report", "--results-dir", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "No per-sample logs found" in out
    assert "95% CI" not in out


def test_report_on_an_empty_directory_reports_no_results(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["report", "--results-dir", str(tmp_path)]) == 0
    assert "No results found" in capsys.readouterr().out


def test_mine_writes_candidates_not_items(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Mined items are unverified like generated ones, so they land in candidates.jsonl
    # and only a human moves them into items.jsonl.
    conllu = tmp_path / "c.conllu"
    conllu.write_text(
        "".join(
            f"# sent_id = s{i}\n# text = t\n"
            f"1\tRadnici{i}\tradnik{i}\tNOUN\tNcmpn\tCase=Nom|Number=Plur\t3\tnsubj\t_\t_\n"
            f"2\tsu\tbiti\tAUX\tVar3p\tTense=Pres\t3\taux\t_\t_\n"
            f"3\tprotestovali\tprotestovati\tVERB\tVmp-pm\tTense=Past\t0\troot\t_\t_\n"
            f"4\tzbog\tzbog\tADP\tSg\tCase=Gen\t5\tcase\t_\t_\n"
            f"5\tplate{i}\tplata{i}\tNOUN\tNcfsg\tCase=Gen|Number=Sing\t3\tobl\t_\tSpaceAfter=No\n"
            f"6\t.\t.\tPUNCT\tZ\t_\t3\tpunct\t_\t_\n\n"
            for i in range(25)
        ),
        encoding="utf-8",
    )
    data_dir = tmp_path / "data"
    assert main(["mine", "--conllu", str(conllu), "--data-dir", str(data_dir), "-n", "5"]) == 0

    written = data_dir / "srb_grammar_cloze" / "candidates.jsonl"
    assert written.exists()
    assert not (data_dir / "srb_grammar_cloze" / "items.jsonl").exists()
    rows = [json.loads(line) for line in written.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 5
    assert all(r["verified"] is False for r in rows)
    assert all(r["license"] == "CC-BY-SA-4.0" for r in rows)
    assert "5 candidate" in capsys.readouterr().out


def test_mine_reports_a_corpus_with_nothing_minable(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    conllu = tmp_path / "empty.conllu"
    conllu.write_text(
        "# sent_id = s1\n# text = t\n1\ta\ta\tNOUN\tN\t_\t0\troot\t_\t_\n",
        encoding="utf-8",
    )
    assert main(["mine", "--conllu", str(conllu), "--data-dir", str(tmp_path / "d")]) == 0
    assert "0 candidate" in capsys.readouterr().out


def test_synth_writes_its_own_candidates_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Synthetic and mined candidates stay in separate files: comparing accuracy across
    # the two is the contamination measurement, so they must not be merged by accident.
    lexicon = tmp_path / "lex.tsv"
    lexicon.write_text(
        "".join(
            f"{lemma}e\t{lemma}\tNcfsg\t_\tNOUN\tCase=Gen|Number=Sing\t100\t0.1\n"
            for lemma in ("nevreme", "kiša", "kvar", "štrajk", "kriza")
        ),
        encoding="utf-8",
    )
    data_dir = tmp_path / "data"
    assert main(["synth", "--lexicon", str(lexicon), "--data-dir", str(data_dir)]) == 0

    written = data_dir / "srb_grammar_cloze" / "candidates-synth.jsonl"
    assert written.exists()
    assert not (data_dir / "srb_grammar_cloze" / "candidates.jsonl").exists()
    rows = [json.loads(line) for line in written.read_text(encoding="utf-8").splitlines()]
    assert rows and all(r["source"] == "synthetic-srlex" for r in rows)
    assert "candidate" in capsys.readouterr().out


def test_baseline_new_then_score_round_trip(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    data_dir = tmp_path / "data" / "srb_grammar"
    data_dir.mkdir(parents=True)
    write_jsonl(data_dir / "items.jsonl", [valid_row(id=f"g{i}") for i in range(5)])

    sheet = tmp_path / "sheet.txt"
    assert main(
        ["baseline", "--new", "-n", "3", "--data-dir", str(tmp_path / "data"),
         "--out", str(sheet)]
    ) == 0
    text = sheet.read_text(encoding="utf-8")
    assert text.count("ODGOVOR:") == 4  # 3 items + the word in the instructions
    # gold must never appear in a worksheet being answered
    assert "Instrumental sredstva" not in text

    # answer them all correctly (gold is A for valid_row)
    sheet.write_text(text.replace("ODGOVOR:\n", "ODGOVOR: A\n"), encoding="utf-8")
    assert main(["baseline", "--score", str(sheet), "--data-dir", str(tmp_path / "data")]) == 0
    out = capsys.readouterr().out
    assert "3/3" in out


def test_probe_synth_writes_one_file_per_synthesised_phenomenon(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    lexicon = tmp_path / "lex.tsv"
    lexicon.write_text(
        "majci\tmajka\tNcfsd\t_\tNOUN\tCase=Dat|Gender=Fem|Number=Sing\t3869\t0.1\n"
        "dođoh\tdoći\tVma1s\tType=main|VForm=aorist|Person=first|Number=singular\tVERB\t"
        "Mood=Ind|Number=Sing|Person=1|Tense=Past|VerbForm=Fin\t540\t0.1\n",
        encoding="utf-8",
    )
    data_dir = tmp_path / "data"
    assert main(["probe", "--lexicon", str(lexicon), "--data-dir", str(data_dir)]) == 0

    sib = data_dir / "srb_probe" / "sibilarizacija.synth.jsonl"
    aor = data_dir / "srb_probe" / "aorist-imperfekat.synth.jsonl"
    sib_rows = [json.loads(line) for line in sib.read_text(encoding="utf-8").splitlines()]
    aor_rows = [json.loads(line) for line in aor.read_text(encoding="utf-8").splitlines()]
    assert [r["answers"] for r in sib_rows] == [["majci"]]
    assert [r["answers"] for r in aor_rows] == [["dođoh"]]
    assert "missing" in capsys.readouterr().out


def test_correction_builds_one_file_per_category_from_the_data_dir(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    def row(i: int, task: str, question: str, cue: str, answer: str, cat: str) -> str:
        return json.dumps({
            "id": f"{task}-{i}", "task": task, "category": cat, "question": question,
            "cue": cue, "answers": [answer], "explanation": "e", "script": "latin",
            "source": "s",
        }, ensure_ascii=False) + "\n"

    data = tmp_path / "data"
    (data / "srb_pravopis").mkdir(parents=True)
    (data / "srb_pravopis" / "poluslozenice.jsonl").write_text("".join(
        row(i, "srb_pravopis", f"Rečenica {i} ima ____.", "kontakt + osoba",
            "kontakt-osobu", "poluslozenice") for i in range(6)), encoding="utf-8")
    (data / "srb_grammar_cloze").mkdir()
    (data / "srb_grammar_cloze" / "items.jsonl").write_text("".join(
        row(i, "srb_grammar_cloze", f"{word} {i} je kod ____.", "reka", "reke", "padezi")
        for i, word in enumerate(["Kuća", "Noć", "Ključ", "Čaša", "Ćebe", "Čamac"])),
        encoding="utf-8")
    index = tmp_path / "forms.txt.gz"
    index.write_bytes(gzip.compress("kuća\nreke\n".encode()))

    assert main([
        "correction", "--data-dir", str(data), "--index", str(index), "-n", "2",
    ]) == 0
    out = data / "srb_correction"
    assert sorted(p.name for p in out.glob("*.jsonl")) == [
        "c-c.jsonl", "ispravno.jsonl", "razmak-crtica.jsonl",
    ]
    assert "OK" in capsys.readouterr().out


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                    encoding="utf-8")


def _cloze_row(item_id: str, task: str, answer: str) -> dict[str, object]:
    return {"id": item_id, "task": task, "category": "c", "question": f"{item_id} ____.",
            "cue": "x", "answers": [answer], "explanation": "e", "script": "latin",
            "source": "s"}


def test_verify_builds_a_sheet_and_applies_marks_back_to_the_data(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    data = tmp_path / "data"
    _write_rows(data / "srb_probe" / "jat.jsonl",
                [_cloze_row(f"p{i}", "srb_probe", "vremena") for i in range(3)])
    _write_rows(data / "srb_pravopis" / "poluslozenice.jsonl",
                [_cloze_row("q1", "srb_pravopis", "kontakt-osoba")])
    _write_rows(data / "srb_grammar_cloze" / "items.jsonl",
                [_cloze_row(f"g{i}", "srb_grammar_cloze", "bašti") for i in range(4)])
    sheet = tmp_path / "provera.txt"

    assert main(["verify", "--new", "-n", "6", "--data-dir", str(data),
                 "--out", str(sheet)]) == 0
    text = sheet.read_text(encoding="utf-8")
    assert text.count("PROVERA:") == 6
    for item_id in ("p0", "p1", "p2", "q1"):
        assert f"] {item_id} " in text

    marks = iter(["ok", "x vrijemena / vremena", "-", "?", "+ baštu", "ok"])
    text = "\n".join(
        f"PROVERA: {next(marks)}" if line == "PROVERA:" else line for line in text.splitlines()
    )
    sheet.write_text(text, encoding="utf-8")
    assert main(["verify", "--apply", str(sheet), "--data-dir", str(data)]) == 0

    jat = {r["id"]: r for r in map(json.loads,
           (data / "srb_probe" / "jat.jsonl").read_text(encoding="utf-8").splitlines())}
    assert jat["p0"]["verified"] is True
    assert jat["p1"]["answers"] == ["vrijemena", "vremena"] and jat["p1"]["verified"]
    assert "p2" not in jat
    discarded = (data / "srb_probe" / "discarded.jsonl").read_text(encoding="utf-8")
    assert '"p2"' in discarded
    pravopis = json.loads((data / "srb_pravopis" / "poluslozenice.jsonl").read_text())
    assert pravopis["verified"] is False
    out = capsys.readouterr().out
    assert "verified" in out and "dropped" in out


def test_verify_disputed_puts_only_contested_items_on_the_sheet(tmp_path: Path) -> None:
    data = tmp_path / "data"
    _write_rows(data / "srb_probe" / "jat.jsonl",
                [_cloze_row(f"p{i}", "srb_probe", "vremena") for i in range(3)])
    results = tmp_path / "results"
    for model, wrong in (("m1", {"p1"}), ("m2", {"p1", "p2"})):
        out = results / model / "x" / "samples_srb_probe_jat.jsonl"
        out.parent.mkdir(parents=True)
        out.write_text("".join(
            json.dumps({"doc": {"id": f"p{i}"}, "exact_match": 0.0 if f"p{i}" in wrong else 1.0,
                        "resps": [["vrijemena"]]}) + "\n" for i in range(3)), encoding="utf-8")
    sheet = tmp_path / "sporni.txt"
    assert main(["verify", "--new", "--data-dir", str(data), "--out", str(sheet),
                 "--disputed", str(results), "--models", "m1,m2", "--min-dissent", "2"]) == 0
    text = sheet.read_text(encoding="utf-8")
    assert "] p1 " in text and "] p0 " not in text and "] p2 " not in text
    assert "Modeli umesto toga: vrijemena (m1), vrijemena (m2)" in text
