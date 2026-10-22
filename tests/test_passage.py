import pytest

from serbeval.passage import extract_passage, parse_markup, score_passage

MARKUP = "Ja to {ne bih|nebih} uradio. Javi se {ni s kim/ni sa kim|niskim}. Kuća je velika."


def test_markup_gives_source_gold_and_sites() -> None:
    p = parse_markup(MARKUP)
    assert p.source == "Ja to nebih uradio. Javi se niskim. Kuća je velika."
    assert p.gold == "Ja to ne bih uradio. Javi se ni s kim. Kuća je velika."
    assert [s.alternatives for s in p.sites] == [("ne bih",), ("ni s kim", "ni sa kim")]
    assert [s.wrong for s in p.sites] == ["nebih", "niskim"]


def test_a_clean_passage_has_no_sites() -> None:
    p = parse_markup("Kuća je velika.")
    assert p.source == p.gold == "Kuća je velika."
    assert p.sites == ()


def test_markup_rejects_a_site_without_a_correct_form() -> None:
    with pytest.raises(ValueError):
        parse_markup("Ja {|nebih} to.")


def test_every_fix_and_nothing_else_is_exact() -> None:
    out = "Ja to ne bih uradio. Javi se ni sa kim. Kuća je velika."
    s = score_passage(out, parse_markup(MARKUP))
    assert (s.exact, s.true_pos, s.false_pos, s.false_neg) == (True, 2, 0, 0)


def test_case_punctuation_and_script_are_folded() -> None:
    s = score_passage("ја то не бих урадио javi se ni s kim kuća je velika", parse_markup(MARKUP))
    assert s.exact


def test_a_missed_error_is_a_false_negative() -> None:
    s = score_passage("Ja to ne bih uradio. Javi se niskim. Kuća je velika.", parse_markup(MARKUP))
    assert (s.exact, s.true_pos, s.false_pos, s.false_neg) == (False, 1, 0, 1)


def test_a_wrong_fix_is_a_miss_not_also_a_false_alarm() -> None:
    out = "Ja to ne bih uradio. Javi se ni-s-kim. Kuća je velika."
    s = score_passage(out, parse_markup(MARKUP))
    assert (s.true_pos, s.false_pos, s.false_neg) == (1, 0, 1)


def test_changing_correct_text_is_a_false_positive() -> None:
    # Over-correction: v1 showed it is the live failure mode at high reasoning effort.
    out = "Ja to ne bih uradio. Javi se ni s kim. Kuca je velika."
    s = score_passage(out, parse_markup(MARKUP))
    assert (s.exact, s.true_pos, s.false_pos, s.false_neg) == (False, 2, 1, 0)


def test_clean_passage_left_alone_scores_exact() -> None:
    s = score_passage("Kuća je velika.", parse_markup("Kuća je velika."))
    assert s.exact and s.false_pos == 0


@pytest.mark.parametrize("output", [
    "Ja baš ne bih ovo uradio danas i sutra.",
    "Ja ne bih baš ovo uradio danas i sutra.",
])
def test_inserting_at_a_site_boundary_is_an_overcorrection(output: str) -> None:
    passage = parse_markup("Ja {ne bih|nebih} ovo uradio danas i sutra.")
    score = score_passage(output, passage)
    assert (score.exact, score.true_pos, score.false_pos, score.false_neg) == (False, 1, 1, 0)


def test_a_replacement_spanning_a_site_and_correct_text_counts_both_errors() -> None:
    passage = parse_markup(
        "Ovo je naš {kontakt telefon|kontakt-telefon} za sve dodatne informacije danas."
    )
    score = score_passage(
        "Ovo je njihov broj telefona za sve dodatne informacije danas.", passage
    )
    assert (score.true_pos, score.false_pos, score.false_neg) == (0, 1, 1)


def test_an_insertion_inside_a_site_is_a_wrong_fix() -> None:
    passage = parse_markup("Ja {ne bih|nebih} ovo uradio danas i sutra.")
    score = score_passage("Ja ne baš bih ovo uradio danas i sutra.", passage)
    assert (score.true_pos, score.false_pos, score.false_neg) == (0, 0, 1)


@pytest.mark.parametrize("output, expected_hits", [
    ("Služba intervenisaće će danas, a ja nebih izlazio.", 0),
    ("Služba intervenisaće danas, a ja nebih izlazio.", 1),
    ("Služba intervenisaće će danas, a ja ne bih izlazio.", 1),
    ("Služba intervenisaće danas, a ja ne bih izlazio.", 2),
])
def test_a_retained_source_auxiliary_is_a_missed_site_not_an_overcorrection(
    output: str, expected_hits: int
) -> None:
    passage = parse_markup(
        "Služba {intervenisaće|intervenisaće će} danas, a ja {ne bih|nebih} izlazio."
    )
    score = score_passage(output, passage)
    assert (score.true_pos, score.false_pos, score.false_neg) == (
        expected_hits, 0, 2 - expected_hits
    )
    assert not score.unparsed


def test_a_rewrite_is_unparsed() -> None:
    s = score_passage("Nikad to ne bih uradio; nisam se javio nikome.", parse_markup(MARKUP))
    assert s.unparsed


def test_extract_takes_everything_after_the_marker() -> None:
    raw = "Evo:\nIspravljeno: Ja to ne bih uradio.\nJavi se ni s kim."
    assert extract_passage(raw) == "Ja to ne bih uradio. Javi se ni s kim."


def test_missing_marker_is_unparsed() -> None:
    s = score_passage("", parse_markup(MARKUP))
    assert s.unparsed and not s.exact


def test_a_dense_error_passage_corrected_is_not_a_rewrite() -> None:
    # Joins and splits move many tokens: the gold itself keeps < 80% of the source tokens.
    p = parse_markup(
        "{S obzirom na|Sobzirom na} krizu, {sutradan|sutra dan} je "
        "{ne bih|nebih} {ni u čemu|niučemu}."
    )
    s = score_passage(p.gold, p)
    assert s.exact and not s.unparsed


def test_a_free_site_accepts_either_form_and_is_not_an_error() -> None:
    # Where the norm itself is split (Pravopis 2010 writes both crno-beli and crnobeli film),
    # the site is listed with the source form among the accepted ones: no credit, no penalty.
    p = parse_markup("Gledali smo {crno-beli/crnobeli|crnobeli} film. Ja {ne bih|nebih} išao.")
    assert [s.free for s in p.sites] == [True, False]
    for out in ("Gledali smo crnobeli film. Ja ne bih išao.",
                "Gledali smo crno-beli film. Ja ne bih išao."):
        s = score_passage(out, p)
        assert (s.exact, s.true_pos, s.false_pos, s.false_neg) == (True, 1, 0, 0)
