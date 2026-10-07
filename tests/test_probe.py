from serbeval.lexicon import Lexicon, VerbLexicon
from serbeval.probe import NounFrame, VerbFrame, synthesize_noun_probe, synthesize_verb_probe


def nouns(**paradigms: dict[tuple[str, str], list[tuple[str, int]]]) -> Lexicon:
    lex = Lexicon()
    for lemma, slots in paradigms.items():
        for slot, forms in slots.items():
            for form, frequency in forms:
                lex.paradigms[lemma][slot].append((frequency, form))
    return lex


def verbs(**paradigms: dict[tuple[str, str, str], list[tuple[str, int]]]) -> VerbLexicon:
    lex = VerbLexicon()
    for lemma, slots in paradigms.items():
        for slot, forms in slots.items():
            for form, frequency in forms:
                lex.paradigms[lemma][slot].append((frequency, form))
    return lex


DAT = NounFrame(
    text="Dao je poklon ____.",
    case="Dat",
    number="Sing",
    lemmas=("majka", "mačka"),
    explanation="Dativ jednine; ispred -i velar prelazi u sibilant (sibilarizacija).",
)

AORIST = VerbFrame(
    text="Ja ____ kući pre ponoći.",
    person="1",
    number="Sing",
    lemmas=("doći",),
    explanation="Aorist, 1. lice jednine.",
)


def test_noun_probe_takes_the_attested_form_as_gold() -> None:
    lex = nouns(majka={("Dat", "Sing"): [("majci", 3869)]})
    [item] = synthesize_noun_probe(lex, [DAT], category="sibilarizacija")
    assert item.answers == ["majci"]
    assert item.cue == "majka, jednina"
    assert item.category == "sibilarizacija"
    assert item.question == "Dao je poklon ____."


def test_noun_probe_never_accepts_a_generated_frequency_zero_form() -> None:
    # „mačci“ is srLex's generator applying sibilarization where the norm does not.
    lex = nouns(mačka={("Dat", "Sing"): [("mački", 150), ("mačci", 0)]})
    [item] = synthesize_noun_probe(lex, [DAT], category="sibilarizacija")
    assert item.answers == ["mački"]


def test_noun_probe_skips_a_lemma_with_no_attested_form() -> None:
    lex = nouns(majka={("Dat", "Sing"): [("majci", 0)]})
    assert synthesize_noun_probe(lex, [DAT], category="sibilarizacija") == []


def test_noun_probe_cue_names_plural_for_a_plural_slot() -> None:
    frame = NounFrame("Na trgu su stajali ____.", "Nom", "Plur", ("junak",), "Nom. mn.")
    lex = nouns(junak={("Nom", "Plur"): [("junaci", 4527)]})
    [item] = synthesize_noun_probe(lex, [frame], category="sibilarizacija")
    assert item.cue == "junak, množina"


def test_verb_probe_builds_an_aorist_item_from_the_attested_form() -> None:
    lex = verbs(doći={("aorist", "1", "Sing"): [("dođoh", 540)]})
    [item] = synthesize_verb_probe(lex, [AORIST], category="aorist-imperfekat")
    assert item.answers == ["dođoh"]
    assert item.cue == "doći, aorist"


def test_verb_probe_accepts_every_attested_variant_but_no_generated_one() -> None:
    lex = verbs(
        doći={("aorist", "1", "Sing"): [("dođoh", 540), ("dođeh", 3), ("dođih", 0)]}
    )
    [item] = synthesize_verb_probe(lex, [AORIST], category="aorist-imperfekat")
    assert item.answers == ["dođoh", "dođeh"]


def test_probe_ids_are_unique_and_prefixed_per_category() -> None:
    lex = nouns(
        majka={("Dat", "Sing"): [("majci", 10)]},
        mačka={("Dat", "Sing"): [("mački", 10)]},
    )
    items = synthesize_noun_probe(lex, [DAT], category="sibilarizacija")
    assert [i.id for i in items] == [
        "srb-probe-sibilarizacija-syn-0001",
        "srb-probe-sibilarizacija-syn-0002",
    ]
    assert all(i.difficulty == "hard" and i.source == "synthetic-srlex" for i in items)
