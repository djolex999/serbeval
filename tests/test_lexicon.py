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
