import gzip
from pathlib import Path

from serbeval.lexicon import Lexicon, load_lexicon

ROWS = [
    # form, lemma, msd, verbose, upos, ud feats, freq, freq/M
    ("bašta", "bašta", "Ncfsn", "_", "NOUN", "Case=Nom|Gender=Fem|Number=Sing", "2570"),
    ("bašti", "bašta", "Ncfsl", "_", "NOUN", "Case=Loc|Gender=Fem|Number=Sing", "4157"),
    ("baštu", "bašta", "Ncfsa", "_", "NOUN", "Case=Acc|Gender=Fem|Number=Sing", "2418"),
    ("bašte", "bašta", "Ncfsg", "_", "NOUN", "Case=Gen|Gender=Fem|Number=Sing", "4096"),
    ("bašta", "bašta", "Ncfpg", "_", "NOUN", "Case=Gen|Gender=Fem|Number=Plur", "375"),
    ("baštâ", "bašta", "Ncfpg", "_", "NOUN", "Case=Gen|Gender=Fem|Number=Plur", "1"),
    ("baštama", "bašta", "Ncfpl", "_", "NOUN", "Case=Loc|Gender=Fem|Number=Plur", "612"),
    ("grad", "grad", "Ncmsn", "_", "NOUN", "Case=Nom|Gender=Masc|Number=Sing", "90000"),
    ("grada", "grad", "Ncmsg", "_", "NOUN", "Case=Gen|Gender=Masc|Number=Sing", "5000"),
    ("lep", "lep", "Agpmsn", "_", "ADJ", "Case=Nom|Gender=Masc|Number=Sing", "800"),
]


def write_lexicon(path: Path, *, gz: bool = False) -> Path:
    body = "".join("\t".join(r) + "\t0.0\n" for r in ROWS)
    if gz:
        path.write_bytes(gzip.compress(body.encode("utf-8")))
    else:
        path.write_text(body, encoding="utf-8")
    return path


def test_loads_a_plain_tsv(tmp_path: Path) -> None:
    lex = load_lexicon(write_lexicon(tmp_path / "l.tsv"))
    assert isinstance(lex, Lexicon)
    assert "bašta" in lex.lemmas()


def test_loads_a_gzipped_file(tmp_path: Path) -> None:
    lex = load_lexicon(write_lexicon(tmp_path / "l.tsv.gz", gz=True))
    assert "bašta" in lex.lemmas()


def test_returns_the_form_for_a_slot(tmp_path: Path) -> None:
    lex = load_lexicon(write_lexicon(tmp_path / "l.tsv"))
    assert lex.forms("bašta", case="Loc", number="Sing") == ["bašti"]


def test_returns_every_variant_for_one_slot_most_frequent_first(tmp_path: Path) -> None:
    # Genitive plural of "bašta" has two attested forms; both are correct answers,
    # and `answers` being a list is exactly what keeps such an item usable.
    lex = load_lexicon(write_lexicon(tmp_path / "l.tsv"))
    assert lex.forms("bašta", case="Gen", number="Plur") == ["bašta", "baštâ"]


def test_unknown_slot_is_empty(tmp_path: Path) -> None:
    lex = load_lexicon(write_lexicon(tmp_path / "l.tsv"))
    assert lex.forms("bašta", case="Voc", number="Plur") == []
    assert lex.forms("nepostojeca", case="Gen", number="Sing") == []


def test_only_the_requested_part_of_speech_is_indexed(tmp_path: Path) -> None:
    lex = load_lexicon(write_lexicon(tmp_path / "l.tsv"), upos="NOUN")
    assert "lep" not in lex.lemmas()


def test_a_lemma_filter_keeps_the_index_small(tmp_path: Path) -> None:
    # srLex is ~7M rows; a caller only ever needs the handful of lemmas it will use.
    lex = load_lexicon(write_lexicon(tmp_path / "l.tsv"), lemmas={"grad"})
    assert lex.lemmas() == {"grad"}


def test_reports_the_frequency_of_a_lemma(tmp_path: Path) -> None:
    lex = load_lexicon(write_lexicon(tmp_path / "l.tsv"))
    assert lex.frequency("grad") > lex.frequency("bašta")


# --- attestation and verbs -------------------------------------------------

from serbeval.lexicon import load_verb_lexicon  # noqa: E402

GENERATED_ROWS = [
    # srLex fills unattested slots from a generator that misses exceptions: „mačci“ (0)
    # sits beside the attested, correct „mački“.
    ("mački", "mačka", "Ncfsd", "_", "NOUN", "Case=Dat|Gender=Fem|Number=Sing", "150"),
    ("mačci", "mačka", "Ncfsd", "_", "NOUN", "Case=Dat|Gender=Fem|Number=Sing", "0"),
]

VERB_ROWS = [
    ("rekoh", "reći", "Vma1s", "Type=main|VForm=aorist|Person=first|Number=singular",
     "VERB", "Mood=Ind|Number=Sing|Person=1|Tense=Past|VerbForm=Fin", "8143"),
    ("reče", "reći", "Vma3s", "Type=main|VForm=aorist|Person=third|Number=singular",
     "VERB", "Mood=Ind|Number=Sing|Person=3|Tense=Past|VerbForm=Fin", "999"),
    ("rekosmo", "reći", "Vma1p", "Type=main|VForm=aorist|Person=first|Number=plural",
     "VERB", "Mood=Ind|Number=Plur|Person=1|Tense=Past|VerbForm=Fin", "4"),
    ("rekao", "reći", "Vmp-sm", "Type=main|VForm=participle|Number=singular|Gender=masculine",
     "VERB", "Gender=Masc|Number=Sing|Tense=Past|VerbForm=Part|Voice=Act", "340120"),
    ("pisah", "pisati", "Vme1s", "Type=main|VForm=imperfect|Person=first|Number=singular",
     "VERB", "Mood=Ind|Number=Sing|Person=1|Tense=Imp|VerbForm=Fin", "17"),
    ("pisaše", "pisati", "Vme3s", "Type=main|VForm=imperfect|Person=third|Number=singular",
     "VERB", "Mood=Ind|Number=Sing|Person=3|Tense=Imp|VerbForm=Fin", "0"),
]


def write_rows(path: Path, rows: list[tuple[str, ...]]) -> Path:
    path.write_text("".join("\t".join(r) + "\t0.0\n" for r in rows), encoding="utf-8")
    return path


def test_min_frequency_drops_unattested_generated_forms(tmp_path: Path) -> None:
    lex = load_lexicon(write_rows(tmp_path / "l.tsv", GENERATED_ROWS))
    assert lex.forms("mačka", case="Dat", number="Sing") == ["mački", "mačci"]
    assert lex.forms("mačka", case="Dat", number="Sing", min_frequency=1) == ["mački"]


def test_verb_lexicon_indexes_aorist_by_person_and_number(tmp_path: Path) -> None:
    lex = load_verb_lexicon(write_rows(tmp_path / "v.tsv", VERB_ROWS))
    assert lex.forms("reći", tense="aorist", person="1", number="Sing") == ["rekoh"]
    assert lex.forms("reći", tense="aorist", person="3", number="Sing") == ["reče"]
    assert lex.forms("reći", tense="aorist", person="1", number="Plur") == ["rekosmo"]


def test_verb_lexicon_ignores_non_finite_forms(tmp_path: Path) -> None:
    lex = load_verb_lexicon(write_rows(tmp_path / "v.tsv", VERB_ROWS))
    assert lex.forms("reći", tense="participle", person="3", number="Sing") == []


def test_verb_lexicon_keeps_imperfect_separate_and_filters_by_frequency(
    tmp_path: Path,
) -> None:
    lex = load_verb_lexicon(write_rows(tmp_path / "v.tsv", VERB_ROWS))
    assert lex.forms("pisati", tense="imperfect", person="1", number="Sing") == ["pisah"]
    assert lex.forms("pisati", tense="aorist", person="1", number="Sing") == []
    assert lex.forms("pisati", tense="imperfect", person="3", number="Sing") == ["pisaše"]
    assert (
        lex.forms("pisati", tense="imperfect", person="3", number="Sing", min_frequency=1)
        == []
    )


def test_verb_lexicon_restricts_to_requested_lemmas(tmp_path: Path) -> None:
    lex = load_verb_lexicon(write_rows(tmp_path / "v.tsv", VERB_ROWS), lemmas={"reći"})
    assert lex.lemmas() == {"reći"}
