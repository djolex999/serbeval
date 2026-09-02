from serbeval.check import FormIndex, check_text, tokenize

# A tiny stand-in for srLex: real forms, with and without diacritics, plus an
# ekavian/ijekavian pair.
FORMS = {
    "bašti", "bašta", "baštu", "kuća", "kuće", "ključem", "ključ",
    "mera", "mere", "mjera", "mjere", "dete", "djete", "olovkom", "olovka",
    "je", "su", "na", "u", "i", "ostala", "otvorio", "vrata", "knjiga",
}


def index() -> FormIndex:
    return FormIndex.build(FORMS)


def kinds(text: str) -> list[str]:
    return [f.kind for f in check_text(text, index())]


# --- tokenizing ------------------------------------------------------------


def test_tokenizes_serbian_latin_and_cyrillic() -> None:
    assert [t.text for t in tokenize("Knjiga je na stolu.")] == [
        "Knjiga", "je", "na", "stolu"
    ]


def test_records_line_and_column() -> None:
    token = tokenize("prvi red\ndrugi red")[2]
    assert (token.text, token.line, token.column) == ("drugi", 2, 1)


def test_skips_numbers_and_punctuation() -> None:
    assert [t.text for t in tokenize("Ima 25 knjiga, zar ne?")] == [
        "Ima", "knjiga", "zar", "ne"
    ]


# --- mixed script ----------------------------------------------------------


def test_flags_a_token_mixing_cyrillic_and_latin() -> None:
    # "кuća" starts with a Cyrillic к — invisible to the eye, broken in the data.
    assert "mixed-script-word" in kinds("Ovo je кuća.")


def test_clean_latin_text_has_no_script_finding() -> None:
    assert "mixed-script-word" not in kinds("Ovo je kuća.")


def test_reports_a_document_that_mixes_both_scripts() -> None:
    assert "mixed-script-document" in kinds("Ovo je kuća. Ово је кућа.")


def test_single_script_document_is_not_flagged() -> None:
    assert "mixed-script-document" not in kinds("Ovo je kuća i bašta.")


# --- diacritics ------------------------------------------------------------


def test_flags_a_form_that_lost_its_diacritics() -> None:
    found = check_text("Sedeli smo u basti.", index())
    findings = [f for f in found if f.kind == "missing-diacritics"]
    assert [f.token for f in findings] == ["basti"]
    assert "bašti" in findings[0].message


def test_correctly_spelled_form_is_not_flagged() -> None:
    assert "missing-diacritics" not in kinds("Sedeli smo u bašti.")


def test_a_word_with_no_diacritic_counterpart_is_not_a_diacritics_finding() -> None:
    assert "missing-diacritics" not in kinds("Ovo je mera.")


# --- unknown forms ---------------------------------------------------------


def test_flags_a_form_the_lexicon_does_not_have() -> None:
    found = check_text("Otvorio je vrata kljucevima.", index())
    findings = [f for f in found if f.kind == "unknown-form"]
    assert [f.token for f in findings] == ["kljucevima"]


def test_known_form_is_not_flagged() -> None:
    assert "unknown-form" not in kinds("Otvorio je vrata ključem.")


def test_capitalised_words_are_not_reported_as_unknown() -> None:
    # Proper nouns are the bulk of any lexicon's misses; flagging them would bury
    # every real finding under names.
    assert "unknown-form" not in kinds("Milan i Jovana su otvorio vrata.")


# --- dialect consistency ---------------------------------------------------


def test_flags_a_document_mixing_ekavian_and_ijekavian() -> None:
    assert "dialect-mixing" in kinds("Ovo je mera. Ono je mjera.")


def test_consistent_ekavian_is_not_flagged() -> None:
    assert "dialect-mixing" not in kinds("Ovo je mera i ovo su mere.")


def test_consistent_ijekavian_is_not_flagged() -> None:
    assert "dialect-mixing" not in kinds("Ovo je mjera i ovo su mjere.")


# --- shape of the output ---------------------------------------------------


def test_findings_carry_a_position() -> None:
    finding = next(f for f in check_text("Sedeli smo u basti.", index()) if f.token == "basti")
    assert finding.line == 1
    assert finding.column == 14


def test_clean_serbian_text_produces_nothing() -> None:
    assert check_text("Knjiga je ostala na bašti.", index()) == []


# --- index build / load ----------------------------------------------------


def test_index_round_trips_through_a_file(tmp_path: object) -> None:
    from pathlib import Path

    from serbeval.check import load_form_index, write_form_index

    path = Path(str(tmp_path)) / "forms.txt.gz"
    write_form_index(FORMS, path)
    loaded = load_form_index(path)
    assert loaded.knows("bašti")
    assert not loaded.knows("kljucevima")
    assert loaded.folded[fold("basti")] == ["bašti"]


def fold(word: str) -> str:
    from serbeval.check import fold_diacritics

    return fold_diacritics(word)


def test_index_is_built_from_every_form_in_a_lexicon_file(tmp_path: object) -> None:
    from pathlib import Path

    from serbeval.check import forms_from_lexicon

    lexicon = Path(str(tmp_path)) / "lex.tsv"
    lexicon.write_text(
        "bašti\tbašta\tNcfsl\t_\tNOUN\tCase=Loc|Number=Sing\t10\t0.1\n"
        "ključem\tključ\tNcmsi\t_\tNOUN\tCase=Ins|Number=Sing\t10\t0.1\n"
        "brzo\tbrz\tRgp\t_\tADV\tDegree=Pos\t10\t0.1\n",
        encoding="utf-8",
    )
    # Every part of speech, unlike serbeval.lexicon which indexes one at a time:
    # a checker must recognise adverbs and verbs too, not only nouns.
    assert forms_from_lexicon(lexicon) == {"bašti", "ključem", "brzo"}


def test_index_excludes_proper_nouns(tmp_path: object) -> None:
    # srLex carries the acronym "CE" as a PROPN. Lowercased into the form set it made
    # "ce" a known word, which silently masked the very common error of writing "ce"
    # for "će". Capitalised tokens are skipped when checking anyway, so proper nouns
    # earn nothing and cost real findings.
    from pathlib import Path

    from serbeval.check import forms_from_lexicon

    lexicon = Path(str(tmp_path)) / "lex.tsv"
    lexicon.write_text(
        "CE\tCE\tNpmsan\t_\tPROPN\tCase=Acc\t163\t0.2\n"
        "će\thteti\tVaf3s\t_\tAUX\tTense=Fut\t900\t1.2\n"
        "bašti\tbašta\tNcfsl\t_\tNOUN\tCase=Loc\t10\t0.1\n",
        encoding="utf-8",
    )
    assert forms_from_lexicon(lexicon) == {"će", "bašti"}


def test_ce_is_reported_as_a_missing_diacritic() -> None:
    index = FormIndex.build({"će", "objasniti", "gradivo"})
    findings = check_text("Nastavnik ce objasniti gradivo.", index)
    assert [(f.kind, f.token) for f in findings] == [("missing-diacritics", "ce")]


def test_short_and_word_initial_je_is_not_treated_as_ijekavian() -> None:
    # "je" de-jekavizes to "e", which is a known form, so the naive rule classified the
    # copula as ijekavian and fired dialect-mixing on essentially every document.
    index = FormIndex.build({"je", "e", "mjera", "mera", "jesen", "esen"})
    assert "je" not in index.ijekavian
    assert "jesen" not in index.ijekavian
    assert "mjera" in index.ijekavian
