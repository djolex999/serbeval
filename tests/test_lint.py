from serbeval.lint import lint_item, lint_items
from serbeval.schema import EvalItem


def make_item(**overrides: object) -> EvalItem:
    raw: dict[str, object] = {
        "id": "srb-grammar-padezi-0001",
        "task": "srb_grammar",
        "category": "padezi",
        "question": "Koja je rečenica ispravna?",
        "choices": [
            "Pišem pismo olovkom koju si mi poklonio.",
            "Pišem pismo sa olovkom koju si mi poklonio.",
            "Pišem pismo o olovkom koju si mi poklonio.",
            "Pišem pismo za olovkom koju si mi poklonio.",
        ],
        "answer_index": 0,
        "explanation": "Sredstvo ide golim instrumentalom.",
        "script": "latin",
        "source": "handwritten-claude",
    }
    raw.update(overrides)
    return EvalItem.model_validate(raw)


def make_idiom(**overrides: object) -> EvalItem:
    raw: dict[str, object] = {
        "id": "srb-idiomi-a-0001",
        "task": "srb_idioms",
        "category": "idiomi-a",
        "question": "Šta znači izraz „pasti s konja na magarca“?",
        "choices": [
            "Pogoršati svoj položaj, proći još gore nego pre",
            "Naglo se obogatiti zahvaljujući sreći",
            "Naučiti nešto na sopstvenoj grešci",
            "Pasti s velike visine i povrediti se",
        ],
        "answer_index": 0,
        "explanation": "Zameniti loše stanje još gorim.",
        "script": "latin",
        "source": "handwritten-claude",
    }
    raw.update(overrides)
    return EvalItem.model_validate(raw)


# --- shape detection -------------------------------------------------------


def test_sentence_variant_choices_detected_as_variant_shape() -> None:
    assert lint_item(make_item()).shape == "variant"


def test_independent_meaning_choices_detected_as_semantic_shape() -> None:
    assert lint_item(make_idiom()).shape == "semantic"


# --- distractor classification (variant items) -----------------------------


def test_single_token_change_from_gold_is_a_minimal_pair() -> None:
    report = lint_item(make_item())
    by_index = {v.index: v for v in report.verdicts}
    assert by_index[1].verdict == "minimal-pair"


def test_two_stacked_changes_from_gold_is_weak() -> None:
    # Inserts "sa" AND swaps olovkom -> olovku: two independent errors.
    item = make_item(
        choices=[
            "Pišem pismo olovkom koju si mi poklonio.",
            "Pišem pismo sa olovkom koju si mi poklonio.",
            "Pišem pismo sa olovku koju si mi poklonio.",
            "Pišem pismo za olovkom koju si mi poklonio.",
        ]
    )
    by_index = {v.index: v for v in lint_item(item).verdicts}
    assert by_index[2].verdict == "weak"


def test_three_stacked_changes_from_gold_is_dead() -> None:
    # Inserts "sa", swaps olovkom -> olovku, and poklonio -> poklonila. Past two stacked
    # errors a sentence stops being a plausible thing anyone would write.
    item = make_item(
        choices=[
            "Pišem pismo olovkom koju si mi poklonio.",
            "Pišem pismo sa olovkom koju si mi poklonio.",
            "Pišem pismo sa olovku koju si mi poklonila.",
            "Pišem pismo za olovkom koju si mi poklonio.",
        ]
    )
    by_index = {v.index: v for v in lint_item(item).verdicts}
    assert by_index[2].verdict == "dead"


def test_unrelated_choice_is_dead() -> None:
    item = make_item(
        choices=[
            "Pišem pismo olovkom koju si mi poklonio.",
            "Pišem pismo sa olovkom koju si mi poklonio.",
            "Juče je padala kiša ceo dan bez prestanka.",
            "Pišem pismo za olovkom koju si mi poklonio.",
        ]
    )
    by_index = {v.index: v for v in lint_item(item).verdicts}
    assert by_index[2].verdict == "dead"


def test_gold_is_not_given_a_verdict() -> None:
    report = lint_item(make_item())
    assert 0 not in {v.index for v in report.verdicts}
    assert len(report.verdicts) == 3


# --- item-level flags ------------------------------------------------------


def test_only_one_near_miss_flags_two_way_mcq() -> None:
    item = make_item(
        choices=[
            "Pišem pismo olovkom koju si mi poklonio.",
            "Pišem pismo sa olovkom koju si mi poklonio.",
            "Juče je padala kiša ceo dan bez prestanka.",
            "Sutra putujemo na more ako bude lepo vreme.",
        ]
    )
    assert "two-way-mcq" in lint_item(item).flags


def test_three_near_misses_does_not_flag_two_way_mcq() -> None:
    assert "two-way-mcq" not in lint_item(make_item()).flags


def test_gold_shorter_by_one_function_word_is_not_a_length_outlier() -> None:
    # Gold here is the only choice without a preposition, so it is one token shorter than
    # all three distractors. That is a real giveaway, but it is a *structural* one (a
    # missing function word), not a length one — a single token out of eight is well
    # inside normal variation. The length flag deliberately stays quiet; catching this
    # would need a separate shared-function-word check, which is not implemented.
    assert "gold-length-outlier" not in lint_item(make_item()).flags


def test_gold_of_typical_length_does_not_flag_structural_leak() -> None:
    item = make_item(
        choices=[
            "Pišem pismo sa olovkom koju si mi poklonio.",
            "Pišem pismo olovkom koju si mi poklonio.",
            "Pišem pismo za olovkom koju si mi poklonio.",
            "Pišem pismo o olovkom koju si mi poklonio.",
        ],
        answer_index=0,
    )
    assert "gold-length-outlier" not in lint_item(item).flags


def test_semantic_item_is_not_flagged_two_way_mcq() -> None:
    # Minimal-pair logic does not apply when choices are independent statements;
    # flagging idioms as 2-way would be a false positive.
    assert "two-way-mcq" not in lint_item(make_idiom()).flags


def test_semantic_item_verdicts_are_not_applicable() -> None:
    assert {v.verdict for v in lint_item(make_idiom()).verdicts} == {"n/a"}


# --- scoring and ranking ---------------------------------------------------


def test_all_minimal_pairs_scores_higher_than_mostly_dead() -> None:
    good = make_item(
        choices=[
            "Pišem pismo sa olovkom koju si mi poklonio.",
            "Pišem pismo olovkom koju si mi poklonio.",
            "Pišem pismo za olovkom koju si mi poklonio.",
            "Pišem pismo o olovkom koju si mi poklonio.",
        ],
        answer_index=0,
    )
    bad = make_item(
        choices=[
            "Pišem pismo olovkom koju si mi poklonio.",
            "Juče je padala kiša ceo dan bez prestanka.",
            "Sutra putujemo na more ako bude lepo vreme.",
            "Voz za Novi Sad kasni petnaest minuta.",
        ]
    )
    assert lint_item(good).score > lint_item(bad).score


def test_lint_items_ranks_worst_first() -> None:
    good = make_item(
        id="good",
        choices=[
            "Pišem pismo sa olovkom koju si mi poklonio.",
            "Pišem pismo olovkom koju si mi poklonio.",
            "Pišem pismo za olovkom koju si mi poklonio.",
            "Pišem pismo o olovkom koju si mi poklonio.",
        ],
        answer_index=0,
    )
    bad = make_item(
        id="bad",
        choices=[
            "Pišem pismo olovkom koju si mi poklonio.",
            "Juče je padala kiša ceo dan bez prestanka.",
            "Sutra putujemo na more ako bude lepo vreme.",
            "Voz za Novi Sad kasni petnaest minuta.",
        ],
    )
    assert [r.item_id for r in lint_items([good, bad])] == ["bad", "good"]


def test_score_is_bounded_between_zero_and_one() -> None:
    for item in (make_item(), make_idiom()):
        assert 0.0 <= lint_item(item).score <= 1.0


def test_unknown_task_falls_back_to_overlap_detection() -> None:
    variant = make_item(task="srb_future_task")
    semantic = make_idiom(task="srb_future_task")
    assert lint_item(variant).shape == "variant"
    assert lint_item(semantic).shape == "semantic"


def test_all_dead_distractors_are_not_excused_as_semantic() -> None:
    # Regression: an item whose distractors are all garbage has the same low mutual
    # overlap as an idiom item, and must not escape variant analysis because of it.
    item = make_item(
        choices=[
            "Pišem pismo olovkom koju si mi poklonio.",
            "Juče je padala kiša ceo dan bez prestanka.",
            "Sutra putujemo na more ako bude lepo vreme.",
            "Voz za Novi Sad kasni petnaest minuta.",
        ]
    )
    report = lint_item(item)
    assert report.shape == "variant"
    assert {v.verdict for v in report.verdicts} == {"dead"}
    assert report.score == 0.0


def test_gold_longer_by_a_single_token_is_not_a_length_outlier() -> None:
    # Being uniquely longest-or-shortest of 4 choices happens ~50% of the time by chance,
    # so rank alone is not evidence of a leak. Only a wide margin is.
    item = make_idiom(
        choices=[
            "jedan dva tri četiri pet šest",
            "jedan dva tri četiri pet",
            "alfa beta gama delta epsilon",
            "crveno plavo zeleno žuto belo",
        ],
        answer_index=0,
    )
    assert "gold-length-outlier" not in lint_item(item).flags


def test_gold_far_longer_than_every_distractor_is_a_length_outlier() -> None:
    item = make_idiom(
        choices=[
            "jedan dva tri četiri pet šest sedam osam devet deset",
            "jedan dva tri",
            "alfa beta gama",
            "crveno plavo zeleno",
        ],
        answer_index=0,
    )
    assert "gold-length-outlier" in lint_item(item).flags


def test_reordered_same_words_is_a_minimal_pair_not_a_stacked_error() -> None:
    # Clitic-placement items vary word ORDER, not word choice. A moved token shows up in a
    # sequence diff as delete+insert (two regions), but it is one error dimension and a very
    # real trap — exactly what srb_grammar's `enklitike` category is built to test.
    item = make_item(
        category="enklitike",
        choices=[
            "Da li ćeš mi pomoći oko selidbe?",
            "Da li mi ćeš pomoći oko selidbe?",
            "Da ćeš li mi pomoći oko selidbe?",
            "Da li ćeš pomoći mi oko selidbe?",
        ],
    )
    report = lint_item(item)
    assert {v.verdict for v in report.verdicts} == {"minimal-pair"}
    assert "two-way-mcq" not in report.flags


def test_reordering_reason_names_word_order() -> None:
    item = make_item(
        category="enklitike",
        choices=[
            "Da li ćeš mi pomoći oko selidbe?",
            "Da li mi ćeš pomoći oko selidbe?",
            "Da ćeš li mi pomoći oko selidbe?",
            "Da li ćeš pomoći mi oko selidbe?",
        ],
    )
    assert all("order" in v.reason for v in lint_item(item).verdicts)


def test_reordering_plus_a_changed_word_is_still_weak() -> None:
    item = make_item(
        category="enklitike",
        choices=[
            "Da li ćeš mi pomoći oko selidbe?",
            "Da li mi ćeš pomoći oko preseljenja?",
            "Da li ćeš mi pomoći oko selidbe danas?",
            "Da ćeš li mi pomoći oko selidbe?",
        ],
    )
    by_index = {v.index: v for v in lint_item(item).verdicts}
    assert by_index[1].verdict == "weak"
