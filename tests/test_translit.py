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


def test_cyrillic_to_latin_simple() -> None:
    from serbeval.translit import cyrillic_to_latin

    assert cyrillic_to_latin("рата") == "rata"


def test_cyrillic_to_latin_expands_single_letters_to_digraphs() -> None:
    from serbeval.translit import cyrillic_to_latin

    assert cyrillic_to_latin("љубав њива џеп") == "ljubav njiva džep"


def test_cyrillic_to_latin_keeps_diacritics() -> None:
    from serbeval.translit import cyrillic_to_latin

    assert cyrillic_to_latin("ђак ћерка шума жаба чаша") == "đak ćerka šuma žaba čaša"


def test_cyrillic_to_latin_leaves_latin_and_punctuation_alone() -> None:
    from serbeval.translit import cyrillic_to_latin

    assert cyrillic_to_latin("bašti, рата.") == "bašti, rata."


def test_round_trip_on_controlled_vocabulary() -> None:
    from serbeval.translit import cyrillic_to_latin, latin_to_cyrillic

    for word in ("nevremena", "ključem", "ljubav", "džep", "bašti", "Šuma"):
        assert cyrillic_to_latin(latin_to_cyrillic(word)) == word
