from serbeval.baseline import build_worksheet, parse_worksheet, sample_items, score_worksheet
from serbeval.schema import ClozeItem, EvalItem


def mcq(id_: str = "m1", answer_index: int = 1) -> EvalItem:
    return EvalItem.model_validate(
        {
            "id": id_, "task": "srb_grammar", "category": "padezi",
            "question": "Koja je rečenica ispravna?",
            "choices": ["Pišem sa olovkom.", "Pišem olovkom.", "Pišem olovku.", "Pišem o olovkom."],
            "answer_index": answer_index, "explanation": "Instrumental sredstva.",
            "script": "latin", "source": "handwritten-claude",
        }
    )


def cloze(id_: str = "c1", answers: list[str] | None = None) -> ClozeItem:
    return ClozeItem.model_validate(
        {
            "id": id_, "task": "srb_grammar_cloze", "category": "padezi",
            "question": "Otkazali su izlet zbog ____.", "cue": "nevreme, jednina",
            "answers": answers or ["nevremena"], "explanation": "Genitiv.",
            "script": "latin", "source": "handwritten-claude",
        }
    )


def fill(sheet: str, *answers: str) -> str:
    """Write answers onto the blank ODGOVOR lines, in order.

    Matches "ODGOVOR:\n" rather than "ODGOVOR:" so the instruction text in the header,
    which mentions the word, is never mistaken for an answer line.
    """
    for answer in answers:
        sheet = sheet.replace("ODGOVOR:\n", f"ODGOVOR: {answer}\n", 1)
    return sheet


# --- sampling --------------------------------------------------------------


def test_sample_is_deterministic_for_a_seed() -> None:
    pool = [mcq(f"m{i}") for i in range(20)]
    assert [i.id for i in sample_items(pool, n=5, seed=3)] == [
        i.id for i in sample_items(pool, n=5, seed=3)
    ]


def test_sample_spreads_across_tasks() -> None:
    # A flat random draw over a pool that is 90% one task would leave the others
    # unmeasured, and the point of the baseline is to find broken items everywhere.
    pool = [mcq(f"m{i}") for i in range(90)] + [cloze(f"c{i}") for i in range(10)]
    tasks = {i.task for i in sample_items(pool, n=10, seed=0)}
    assert tasks == {"srb_grammar", "srb_grammar_cloze"}


def test_sample_never_returns_more_than_the_pool() -> None:
    assert len(sample_items([mcq()], n=30, seed=0)) == 1


# --- worksheet -------------------------------------------------------------


def test_worksheet_shows_mcq_choices_and_an_answer_line() -> None:
    sheet = build_worksheet([mcq()])
    assert "A) Pišem sa olovkom." in sheet
    assert "D) Pišem o olovkom." in sheet
    assert "ODGOVOR:" in sheet


def test_worksheet_shows_the_cloze_cue() -> None:
    sheet = build_worksheet([cloze()])
    assert "Otkazali su izlet zbog ____." in sheet
    assert "(nevreme, jednina)" in sheet


def test_worksheet_never_leaks_the_answer() -> None:
    # The whole control is worthless if the gold is visible while answering.
    sheet = build_worksheet([mcq(), cloze()])
    assert "Instrumental sredstva" not in sheet
    assert "nevremena" not in sheet


def test_worksheet_carries_item_ids_for_scoring() -> None:
    assert "m1" in build_worksheet([mcq()])


# --- parsing filled worksheets ---------------------------------------------


def test_parses_filled_answers() -> None:
    sheet = fill(build_worksheet([mcq(), cloze()]), "B", "nevremena")
    assert parse_worksheet(sheet) == {"m1": "B", "c1": "nevremena"}


def test_unanswered_items_are_absent_rather_than_empty() -> None:
    assert parse_worksheet(build_worksheet([mcq()])) == {}


# --- scoring ---------------------------------------------------------------


def test_scores_a_correct_mcq_letter() -> None:
    sheet = fill(build_worksheet([mcq()]), "B")
    result = score_worksheet(sheet, [mcq()])
    assert (result.correct, result.answered) == (1, 1)
    assert result.wrong == []


def test_scores_a_wrong_mcq_letter_and_names_the_item() -> None:
    sheet = fill(build_worksheet([mcq()]), "C")
    result = score_worksheet(sheet, [mcq()])
    assert result.correct == 0
    assert result.wrong == ["m1"]


def test_mcq_letter_is_case_insensitive() -> None:
    sheet = fill(build_worksheet([mcq()]), "b")
    assert score_worksheet(sheet, [mcq()]).correct == 1


def test_scores_cloze_with_the_benchmarks_own_rule() -> None:
    # Same normalisation the eval uses, so a human baseline and a model score are
    # measured on identical terms.
    sheet = fill(build_worksheet([cloze()]), " Nevremena. ")
    assert score_worksheet(sheet, [cloze()]).correct == 1


def test_cloze_accepts_any_listed_variant() -> None:
    item = cloze(answers=["stigneš", "budeš stigao"])
    sheet = fill(build_worksheet([item]), "budeš stigao")
    assert score_worksheet(sheet, [item]).correct == 1


def test_unanswered_items_are_not_counted_as_wrong() -> None:
    result = score_worksheet(build_worksheet([mcq()]), [mcq()])
    assert (result.answered, result.correct, result.wrong) == (0, 0, [])
