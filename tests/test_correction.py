import random

import pytest
from pydantic import ValidationError

from serbeval.correction import (
    CorrectionItem,
    diacritic_error,
    extract_correction,
    fill,
    is_correct,
    spacing_error,
)
from serbeval.schema import ClozeItem


def cloze(**overrides: object) -> ClozeItem:
    raw: dict[str, object] = {
        "id": "srb-pravopis-poluslozenice-0002",
        "task": "srb_pravopis",
        "category": "poluslozenice",
        "question": "Zapišite naš ____ za hitne slučajeve.",
        "cue": "kontakt + telefon",
        "answers": ["kontakt-telefon"],
        "explanation": "Polusloženica: kontakt-telefon.",
        "script": "latin",
        "source": "handwritten-claude",
    }
    raw.update(overrides)
    return ClozeItem.model_validate(raw)


def item(**overrides: object) -> CorrectionItem:
    raw: dict[str, object] = {
        "id": "srb-correction-razmak-crtica-0001",
        "task": "srb_correction",
        "category": "razmak-crtica",
        "text": "Zapišite naš kontakt telefon za hitne slučajeve.",
        "answers": ["Zapišite naš kontakt-telefon za hitne slučajeve."],
        "has_error": True,
        "explanation": "Polusloženica: kontakt-telefon.",
        "script": "latin",
        "source": "derived-srb_pravopis",
    }
    raw.update(overrides)
    return CorrectionItem.model_validate(raw)


# --- schema ----------------------------------------------------------------


def test_an_error_item_must_not_list_its_own_text_as_correct() -> None:
    with pytest.raises(ValidationError):
        item(answers=["Zapišite naš kontakt telefon za hitne slučajeve."])


def test_a_clean_item_must_accept_its_own_text() -> None:
    clean = "Zapišite naš kontakt-telefon za hitne slučajeve."
    assert item(text=clean, answers=[clean], has_error=False).has_error is False
    with pytest.raises(ValidationError):
        item(text=clean, answers=["Nešto drugo."], has_error=False)


# --- building --------------------------------------------------------------


def test_fill_puts_the_form_into_the_blank() -> None:
    assert fill(cloze(), "kontakt-telefon") == "Zapišite naš kontakt-telefon za hitne slučajeve."


def test_a_hyphenated_noun_gold_becomes_the_written_apart_error() -> None:
    assert spacing_error(cloze()) == "kontakt telefon"


def test_a_hyphenated_adjective_gold_becomes_the_written_together_error() -> None:
    adj = cloze(category="slozeni-pridevi", cue="srpski + engleski", answers=["srpsko-engleski"])
    assert spacing_error(adj) == "srpskoengleski"


def test_a_together_adjective_gold_is_split_with_a_hyphen_at_the_part_boundary() -> None:
    # The linking vowel stays with the first part: jugo-istočnom, not jug-oistočnom.
    adj = cloze(category="slozeni-pridevi", cue="jug + istočni", answers=["jugoistočnom"])
    assert spacing_error(adj) == "jugo-istočnom"


def test_a_together_adverb_gold_is_split_apart() -> None:
    adv = cloze(category="sastavljeno-rastavljeno", cue="na + pamet", answers=["napamet"])
    assert spacing_error(adv) == "na pamet"


def test_an_apart_gold_is_joined_together() -> None:
    apart = cloze(category="sastavljeno-rastavljeno", cue="ni + od + ko", answers=["ni od koga"])
    assert spacing_error(apart) == "niodkoga"


def test_no_spacing_error_when_the_cue_does_not_name_parts() -> None:
    assert spacing_error(cloze(cue="pet ili šest, približno", answers=["pet-šest"])) is None


def test_no_spacing_error_when_the_error_is_itself_an_accepted_answer() -> None:
    doublet = cloze(cue="džez + muzika", answers=["džez-muziku", "džez muziku"])
    assert spacing_error(doublet) is None


def test_diacritic_error_swaps_c_and_c_acute_only_into_a_non_word() -> None:
    known = {"kuća", "plaća", "plača"}
    rng = random.Random(0)
    wrong, original, swapped = diacritic_error("Kupili su kuću i plaća je dobra.", known, rng)
    assert (original, swapped) == ("kuću", "kuču")
    assert wrong == "Kupili su kuču i plaća je dobra."


def test_diacritic_error_is_none_when_every_swap_is_a_real_word() -> None:
    assert diacritic_error("Plaća je mala.", {"plaća", "plača"}, random.Random(0)) is None


# --- scoring ---------------------------------------------------------------


def test_extract_takes_the_text_after_the_marker() -> None:
    raw = "Greška je u crtici.\nIspravljeno: Zapišite naš kontakt-telefon za hitne slučajeve."
    assert extract_correction(raw) == "Zapišite naš kontakt-telefon za hitne slučajeve."


def test_extract_without_a_marker_falls_back_to_the_first_line() -> None:
    assert extract_correction("Rečenica je ispravna.\n\nObjašnjenje") == "Rečenica je ispravna."


def test_a_corrected_sentence_scores_ignoring_case_and_final_punctuation() -> None:
    raw = "Ispravljeno: zapišite naš kontakt-telefon za hitne slučajeve"
    assert is_correct(raw, item())


def test_leaving_the_error_in_place_scores_wrong() -> None:
    assert not is_correct("Ispravljeno: Zapišite naš kontakt telefon za hitne slučajeve.", item())


def test_over_correcting_a_clean_sentence_scores_wrong() -> None:
    clean = "Zapišite naš kontakt-telefon za hitne slučajeve."
    ok = item(text=clean, answers=[clean], has_error=False)
    assert is_correct(f"Ispravljeno: {clean}", ok)
    assert not is_correct("Ispravljeno: Zapišite vaš kontakt-telefon za hitne slučajeve.", ok)


# --- set building ----------------------------------------------------------

from serbeval.correction import Sentence, build_correction_set  # noqa: E402


def _pravopis(n: int) -> list[ClozeItem]:
    return [
        cloze(id=f"p{i}", question=f"Rečenica broj {i} ima ____ u sredini.",
              cue="kontakt + osoba", answers=["kontakt-osobu"])
        for i in range(n)
    ]


def _pool(n: int) -> list[Sentence]:
    # Each sentence carries a DIFFERENT č/ć word: one word is used for at most one item.
    words = ["Kuća", "Noć", "Vožnja", "Ključ", "Večera", "Ćup", "Čaša", "Ćebe", "Čamac", "Ćilim"]
    return [Sentence(f"{words[i]} broj {i} stoji pored reke.", f"o{i}", "CC-BY-4.0")
            for i in range(n)]


def test_build_makes_three_disjoint_categories() -> None:
    items = build_correction_set(
        _pravopis(10), _pool(10), known={"kuća"}, per_category=4, seed=0
    )
    by_cat: dict[str, list[CorrectionItem]] = {}
    for it in items:
        by_cat.setdefault(it.category, []).append(it)
    assert {k: len(v) for k, v in by_cat.items()} == {
        "razmak-crtica": 4, "c-ć": 4, "ispravno": 4,
    }
    assert all(it.has_error for it in by_cat["razmak-crtica"] + by_cat["c-ć"])
    assert not any(it.has_error for it in by_cat["ispravno"])
    # No source sentence appears twice: a clean copy would give away its erroneous twin.
    bases = [it.answers[0] for it in items]
    assert len(bases) == len(set(bases))


def test_build_is_deterministic_and_ids_are_unique() -> None:
    a = build_correction_set(_pravopis(10), _pool(10), known=set(), per_category=4, seed=1)
    b = build_correction_set(_pravopis(10), _pool(10), known=set(), per_category=4, seed=1)
    assert [i.model_dump() for i in a] == [i.model_dump() for i in b]
    assert len({i.id for i in a}) == len(a)


def test_clean_set_mixes_tricky_pravopis_sentences_with_plain_ones() -> None:
    # Clean pravopis sentences („kontakt-osobu“ spelt right) are what measures
    # over-correction of exactly the spellings the error items test.
    items = build_correction_set(_pravopis(10), _pool(10), known=set(), per_category=4, seed=0)
    clean = [it for it in items if it.category == "ispravno"]
    assert any("kontakt-osobu" in it.text for it in clean)
    assert any("Kuća" in it.text for it in clean)


def test_the_first_cue_part_is_skipped_when_finding_the_boundary() -> None:
    # „pol“ occurs inside „spoljni“ itself; the split must come after the first part.
    adj = cloze(category="slozeni-pridevi", cue="spoljni + politički", answers=["spoljnopolitičko"])
    assert spacing_error(adj) == "spoljno-političko"


def test_fill_capitalises_a_blank_at_the_start_of_the_sentence() -> None:
    start = cloze(question="____ da dođe, neće ga pustiti.", cue="ma + ko", answers=["ma ko"])
    assert fill(start, "ma ko") == "Ma ko da dođe, neće ga pustiti."


def test_each_c_word_is_used_for_at_most_one_item() -> None:
    pool = [Sentence(f"Radi tu već {i} godina.", f"s{i}", "CC-BY-4.0") for i in range(6)]
    with pytest.raises(ValueError, match="c-ć"):
        build_correction_set(_pravopis(10), pool, known=set(), per_category=2, seed=0)
