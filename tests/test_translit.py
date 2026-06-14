from serbeval.translit import latin_to_cyrillic


def test_basic_letters() -> None:
    assert latin_to_cyrillic("Beograd") == "Београд"
    assert latin_to_cyrillic("zelena") == "зелена"


def test_digraphs() -> None:
    assert latin_to_cyrillic("ljubav") == "љубав"
    assert latin_to_cyrillic("konj") == "коњ"
    assert latin_to_cyrillic("džak") == "џак"


def test_uppercase_digraph_before_lowercase_vowel() -> None:
    # "Nj" at start of a capitalized word maps to a single Cyrillic capital
    assert latin_to_cyrillic("Njegoš") == "Његош"


def test_special_latin_letters() -> None:
    assert latin_to_cyrillic("čaša") == "чаша"
    assert latin_to_cyrillic("ćup") == "ћуп"
    assert latin_to_cyrillic("đak") == "ђак"
    assert latin_to_cyrillic("šuma") == "шума"
    assert latin_to_cyrillic("žaba") == "жаба"


def test_digits_and_punctuation_pass_through() -> None:
    assert latin_to_cyrillic("Koliko je 7 puta 8?") == "Колико је 7 пута 8?"


def test_full_sentence() -> None:
    assert (
        latin_to_cyrillic("Koji je glavni grad Srbije?") == "Који је главни град Србије?"
    )
