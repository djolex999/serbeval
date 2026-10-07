import pytest
from pydantic import ValidationError

from serbeval.cloze import extract_answer, is_correct, normalize
from serbeval.schema import ClozeItem


def make_raw(**overrides: object) -> dict[str, object]:
    raw: dict[str, object] = {
        "id": "srb-cloze-padezi-0001",
        "task": "srb_grammar_cloze",
        "category": "padezi",
        "question": "Celo popodne sedeli smo u ____ i razgovarali.",
        "cue": "bašta",
        "answers": ["bašti"],
        "explanation": "Mirovanje posle predloga „u“ traži lokativ.",
        "script": "latin",
        "source": "handwritten-claude",
    }
    raw.update(overrides)
    return raw


# --- schema ----------------------------------------------------------------


def test_valid_cloze_item_parses() -> None:
    item = ClozeItem.model_validate(make_raw())
    assert item.answers == ["bašti"]
    assert item.verified is False


def test_cloze_item_requires_at_least_one_answer() -> None:
    with pytest.raises(ValidationError, match="answers"):
        ClozeItem.model_validate(make_raw(answers=[]))


def test_cloze_item_rejects_a_blank_answer() -> None:
    with pytest.raises(ValidationError, match="answers"):
        ClozeItem.model_validate(make_raw(answers=["bašti", "   "]))


def test_cloze_item_requires_a_blank_in_the_question() -> None:
    with pytest.raises(ValidationError, match="____"):
        ClozeItem.model_validate(make_raw(question="Nema praznine u ovoj rečenici."))


# --- normalization ---------------------------------------------------------


def test_normalize_lowercases_and_strips_punctuation() -> None:
    assert normalize("  Bašti.  ") == "bašti"


def test_normalize_keeps_serbian_diacritics_significant() -> None:
    # č/ć/ž/š/đ carry the orthography we are testing — folding them would score
    # a misspelling as correct.
    assert normalize("baŠti") != normalize("basti")
    assert normalize("kuća") != normalize("kuca")


# --- answer extraction from a model response -------------------------------


def test_extract_takes_a_bare_word() -> None:
    assert extract_answer("bašti") == "bašti"


def test_extract_strips_a_serbian_answer_prefix() -> None:
    assert extract_answer("Odgovor: bašti") == "bašti"


def test_extract_takes_only_the_first_line() -> None:
    assert extract_answer("bašti\n\nObjašnjenje: lokativ posle predloga u.") == "bašti"


def test_extract_keeps_a_multi_word_answer() -> None:
    assert extract_answer("lošem vremenu") == "lošem vremenu"


def test_extract_unwraps_quotes_and_trailing_punctuation() -> None:
    assert extract_answer('"bašti".') == "bašti"


def test_extract_of_empty_response_is_empty() -> None:
    assert extract_answer("") == ""


# --- scoring ---------------------------------------------------------------


def test_exact_answer_is_correct() -> None:
    assert is_correct("bašti", make_item()) is True


def test_wrong_case_form_is_incorrect() -> None:
    assert is_correct("baštu", make_item()) is False


def test_any_accepted_variant_counts() -> None:
    # Contested norms (ijekavian doublets, tolerated variants) list every accepted
    # form rather than forcing one and dropping the item.
    item = make_item(answers=["ćeš doći", "ćeš da dođeš"])
    assert is_correct("ćeš da dođeš", item) is True


def test_scoring_ignores_case_and_surrounding_punctuation() -> None:
    assert is_correct("  Bašti. ", make_item()) is True


def test_a_verbose_response_still_scores() -> None:
    assert is_correct("Odgovor: bašti", make_item()) is True


def test_empty_response_is_incorrect() -> None:
    assert is_correct("", make_item()) is False


def make_item(**overrides: object) -> ClozeItem:
    return ClozeItem.model_validate(make_raw(**overrides))


# --- dataset IO ------------------------------------------------------------


def test_load_cloze_items_round_trips(tmp_path: object) -> None:
    from pathlib import Path

    from serbeval.data import load_cloze_items, save_cloze_items

    path = Path(str(tmp_path)) / "items.jsonl"
    items = [make_item(), make_item(id="srb-cloze-padezi-0002")]
    save_cloze_items(items, path)
    assert load_cloze_items(path) == items


def test_validate_cloze_flags_duplicate_ids() -> None:
    from serbeval.data import validate_cloze_dataset

    problems = validate_cloze_dataset([make_item(), make_item()])
    assert any("duplicate id" in p for p in problems)


def test_validate_cloze_flags_an_answer_left_in_the_question() -> None:
    # A question that already contains its own answer is unanswerable-by-inspection
    # in the wrong direction: the model can read the form straight off the prompt.
    from serbeval.data import validate_cloze_dataset

    item = make_item(question="Sedeli smo u bašti, a ____ je bila lepa.")
    assert any("contains its own answer" in p for p in validate_cloze_dataset([item]))


def test_validate_cloze_accepts_a_clean_dataset() -> None:
    from serbeval.data import validate_cloze_dataset

    items = [
        make_item(),
        make_item(id="b", question="Bavi se ____ godinama.", answers=["fudbalom"]),
    ]
    assert validate_cloze_dataset(items) == []


def test_validate_cloze_allows_one_question_across_many_cues() -> None:
    # Template-generated items share a frame by design; the cue is what distinguishes
    # them, so a repeated question alone is not a problem.
    from serbeval.data import validate_cloze_dataset

    items = [
        make_item(id="a", cue="nevreme", answers=["nevremena"]),
        make_item(id="b", cue="kvar", answers=["kvara"]),
    ]
    assert validate_cloze_dataset(items) == []


def test_validate_cloze_flags_a_repeated_question_and_cue() -> None:
    # Same prompt, different gold answer, is a genuine contradiction.
    from serbeval.data import validate_cloze_dataset

    items = [
        make_item(id="a", cue="nevreme", answers=["nevremena"]),
        make_item(id="b", cue="nevreme", answers=["nevremenu"]),
    ]
    assert any("duplicate question and cue" in p for p in validate_cloze_dataset(items))


def test_a_correct_form_written_in_cyrillic_scores_correct() -> None:
    # Opus answered a Latin cloze item with „рата“ — the right genitive, in the other
    # script. This task measures case morphology; script consistency is measured by
    # srb_cyrillic_agreement. Penalising it here would mark correct grammar wrong.
    item = make_item(cue="rat, jednina", answers=["rata"])
    assert is_correct("рата", item) is True


def test_a_wrong_form_in_cyrillic_is_still_wrong() -> None:
    item = make_item(cue="rat, jednina", answers=["rata"])
    assert is_correct("рату", item) is False


def test_cyrillic_tolerance_does_not_fold_diacritics() -> None:
    # „башти“ transliterates to „bašti“, never to „basti“.
    assert is_correct("башти", make_item()) is True
    assert is_correct("basti", make_item()) is False


def test_extract_skips_a_leading_explanation_line() -> None:
    # Opus via Kie twice answered "<reasoning line>\n\n<form>": the form was right but
    # the first line was scored, so a correct answer counted as a miss.
    assert extract_answer('"kroz" + accusative plural: sela.\n\nsela') == "sela"


def test_extract_still_ignores_a_trailing_explanation() -> None:
    assert extract_answer("bašti\n\nObjašnjenje: lokativ posle predloga u.") == "bašti"


def test_extract_keeps_a_two_word_answer_after_an_explanation() -> None:
    raw = 'Uprkos takes the dative case in Serbian, so "loše vreme" becomes:\n\nlošem vremenu'
    assert extract_answer(raw) == "lošem vremenu"


def test_extract_falls_back_to_the_first_line_when_nothing_is_short() -> None:
    raw = "ovo je dugačak odgovor bez kratke linije\ni još jedna duga linija ovde"
    assert extract_answer(raw) == "ovo je dugačak odgovor bez kratke linije"
