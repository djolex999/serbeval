import json
import shutil
import subprocess

import pytest

from serbeval.passage_review import (
    build_passage_review_html,
    parse_passage_review,
    review_rows,
)

DRAFT = {"id": "srb-v2-passage-0001", "script": "latin", "errors": 1,
         "markup": "Ja {ne bih|nebih} to uradio.", "pravopis_2010": {"ne bih": "t. 124a (p. 92)"}}
GOV = {"id": "srb-v2-gov-0001", "script": "cyrillic", "errors": 1, "body": "Grad Niš",
       "doc_type": "saopštenje", "source": "https://www.ni.rs/x",
       "markup": "Постављена је {спомен-плоча|спомен плоча} и {ниједан/ни један|ни један} венац.",
       "natural_errors": ["спомен плоча"],
       "pravopis_2010": {"спомен плоча → спомен-плоча": "spomen p. 457; t. 82b",
                         "ни један → ниједан/ни један": "t. 111 (p. 89)"}}


def test_rows_carry_source_gold_sites_and_citations() -> None:
    [d, g] = review_rows([DRAFT, GOV])
    assert d["source"] == "Ja nebih to uradio." and d["gold"] == "Ja ne bih to uradio."
    assert d["sites"] == [{"wrong": "nebih", "right": ["ne bih"], "free": False,
                           "natural": False, "cite": "t. 124a (p. 92)"}]
    assert g["link"] == "https://www.ni.rs/x" and g["set"] == "gov"
    assert [s["natural"] for s in g["sites"]] == [True, False]
    assert [s["free"] for s in g["sites"]] == [False, True]
    assert g["sites"][0]["cite"] == "spomen p. 457; t. 82b"


def test_html_embeds_every_passage() -> None:
    html = build_passage_review_html(review_rows([DRAFT, GOV]), title="v2-pregled")
    assert "srb-v2-passage-0001" in html and "srb-v2-gov-0001" in html
    assert "<title>v2-pregled</title>" in html


def test_html_cannot_be_broken_out_of_by_passage_text() -> None:
    evil = {**DRAFT, "markup": "Tekst </script><script>alert(1)</script> {ne bih|nebih}."}
    html = build_passage_review_html(review_rows([evil]), title="t")
    assert "</script><script>alert(1)" not in html


def test_parses_every_mark() -> None:
    text = ("[1] a\nPROVERA: ok\n\n[2] b\nPROVERA: x rečenica 3 zvuči nespretno\n\n"
            "[3] c\nPROVERA: ?\n\n[4] d\nPROVERA: -\n\n[5] e\nPROVERA:\n")
    assert parse_passage_review(text) == {
        "a": ("ok", ""), "b": ("x", "rečenica 3 zvuči nespretno"), "c": ("?", ""), "d": ("-", "")}


def test_an_unknown_mark_names_the_passage() -> None:
    with pytest.raises(ValueError, match="b"):
        parse_passage_review("[1] b\nPROVERA: možda\n")


def test_x_needs_a_note() -> None:
    with pytest.raises(ValueError, match="b"):
        parse_passage_review("[1] b\nPROVERA: x\n")


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_the_page_export_is_read_back_by_the_python_parser() -> None:
    html = build_passage_review_html(review_rows([DRAFT, GOV]), title="t")
    logic = html.split("/* LOGIC-START */")[1].split("/* LOGIC-END */")[0]
    items = [{"id": DRAFT["id"]}, {"id": GOV["id"]}]
    marks = {DRAFT["id"]: {"kind": "x", "note": "„uradio“ → „uradila“"}, GOV["id"]: {"kind": "ok"}}
    call = f"serializeMarks({json.dumps(items)}, {json.dumps(marks)})"
    program = logic + f"\nprocess.stdout.write({call});"
    out = subprocess.run(["node", "-e", program], capture_output=True, text=True, check=True)
    assert parse_passage_review(out.stdout) == {
        DRAFT["id"]: ("x", "„uradio“ → „uradila“"), GOV["id"]: ("ok", "")}
