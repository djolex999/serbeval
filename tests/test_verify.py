import pytest

from serbeval.schema import ClozeItem, EvalItem
from serbeval.verify import (
    Verdict,
    apply_verdict,
    build_verification_sheet,
    parse_verification_sheet,
    select_for_verification,
)


def cloze(**overrides: object) -> ClozeItem:
    raw: dict[str, object] = {
        "id": "srb-probe-jat-0003", "task": "srb_probe", "category": "jat",
        "question": "U ovoj kući nikad nije bilo ____ za odmor.",
        "cue": "vremena → ijekavski", "answers": ["vremena"],
        "explanation": "Kratki jat iza r daje e.", "script": "latin",
        "source": "handwritten-claude",
    }
    raw.update(overrides)
    return ClozeItem.model_validate(raw)


def mcq(**overrides: object) -> EvalItem:
    raw: dict[str, object] = {
        "id": "srb-grammar-padezi-0007", "task": "srb_grammar", "category": "padezi",
        "question": "Koja je rečenica ispravna?",
        "choices": ["Idem u baštu.", "Idem u bašti.", "Idem na bašti.", "Idem baštom."],
        "answer_index": 0, "explanation": "Kretanje: akuzativ.", "script": "latin",
        "source": "handwritten-claude",
    }
    raw.update(overrides)
    return EvalItem.model_validate(raw)


# --- the sheet shows the gold, unlike the blind baseline ----------------------


def test_sheet_shows_item_gold_and_explanation_with_an_empty_check_line() -> None:
    sheet = build_verification_sheet([cloze(), mcq()])
    assert "[1] srb-probe-jat-0003" in sheet
    assert "(vremena → ijekavski)" in sheet
    assert "TAČNO: vremena" in sheet
    assert "Kratki jat iza r daje e." in sheet
    assert "TAČNO: A) Idem u baštu." in sheet
    assert sheet.count("PROVERA:") == 2


def test_sheet_lists_every_accepted_cloze_form() -> None:
    sheet = build_verification_sheet([cloze(answers=["beše", "bejaše", "bijaše"])])
    assert "TAČNO: beše / bejaše / bijaše" in sheet


# --- parsing the marks ---------------------------------------------------------


def sheet_with(*marks: str) -> str:
    items = [cloze(id=f"srb-probe-jat-{i:04d}") for i in range(1, len(marks) + 1)]
    text = build_verification_sheet(items)
    for mark in marks:
        text = text.replace("PROVERA:\n", f"PROVERA: {mark}\n", 1)
    return text


def test_parses_every_mark_and_skips_blank_lines() -> None:
    parsed = parse_verification_sheet(
        sheet_with("ok", "x vrijemena / vremena", "+ vremenâ", "?", "-", "")
    )
    assert parsed == {
        "srb-probe-jat-0001": Verdict("ok"),
        "srb-probe-jat-0002": Verdict("fix", "vrijemena / vremena"),
        "srb-probe-jat-0003": Verdict("add", "vremenâ"),
        "srb-probe-jat-0004": Verdict("unsure"),
        "srb-probe-jat-0005": Verdict("drop"),
    }


def test_marks_are_case_insensitive_and_a_comment_is_ignored() -> None:
    parsed = parse_verification_sheet(sheet_with("OK   # proverio u Pravopisu"))
    assert parsed["srb-probe-jat-0001"] == Verdict("ok")


def test_an_unknown_mark_is_an_error_that_names_the_item() -> None:
    with pytest.raises(ValueError, match="srb-probe-jat-0001"):
        parse_verification_sheet(sheet_with("mozda"))


def test_a_fix_without_a_value_is_an_error() -> None:
    with pytest.raises(ValueError, match="srb-probe-jat-0001"):
        parse_verification_sheet(sheet_with("x"))


# --- applying verdicts ---------------------------------------------------------


def test_ok_marks_the_item_verified() -> None:
    applied = apply_verdict(cloze(), Verdict("ok"))
    assert applied is not None and applied.verified is True


def test_fix_replaces_cloze_answers_and_verifies() -> None:
    applied = apply_verdict(cloze(), Verdict("fix", "rijeci / rijeki"))
    assert isinstance(applied, ClozeItem)
    assert applied.answers == ["rijeci", "rijeki"] and applied.verified


def test_add_keeps_the_gold_and_appends_a_variant() -> None:
    applied = apply_verdict(cloze(), Verdict("add", "vremenâ"))
    assert isinstance(applied, ClozeItem)
    assert applied.answers == ["vremena", "vremenâ"] and applied.verified


def test_fix_on_mcq_takes_a_letter() -> None:
    applied = apply_verdict(mcq(), Verdict("fix", "b"))
    assert isinstance(applied, EvalItem)
    assert applied.answer_index == 1 and applied.verified


def test_fix_on_mcq_rejects_anything_but_a_letter() -> None:
    with pytest.raises(ValueError, match="srb-grammar-padezi-0007"):
        apply_verdict(mcq(), Verdict("fix", "Idem u bašti."))


def test_add_on_mcq_is_an_error() -> None:
    with pytest.raises(ValueError, match="srb-grammar-padezi-0007"):
        apply_verdict(mcq(), Verdict("add", "x"))


def test_unsure_leaves_the_item_unverified_and_unchanged() -> None:
    item = cloze()
    assert apply_verdict(item, Verdict("unsure")) == item


def test_drop_removes_the_item() -> None:
    assert apply_verdict(cloze(), Verdict("drop")) is None


# --- selection ---------------------------------------------------------------------


def test_selection_takes_all_core_items_then_tops_up_with_unverified_others() -> None:
    core = [cloze(id=f"srb-probe-jat-{i:04d}") for i in range(5)]
    others = [mcq(id=f"srb-grammar-padezi-{i:04d}") for i in range(10)]
    others[0] = others[0].model_copy(update={"verified": True})
    picked = select_for_verification(core, others, n=8, seed=0)
    assert [p.id for p in picked[:5]] == [c.id for c in core]
    assert len(picked) == 8
    assert all(not p.verified for p in picked)
    assert len({p.id for p in picked}) == 8
