from serbeval.lexicon import Lexicon
from serbeval.schema import ClozeItem
from serbeval.synth import Frame, synthesize_items


def lexicon(**paradigms: dict[tuple[str, str], list[str]]) -> Lexicon:
    lex = Lexicon()
    for lemma, slots in paradigms.items():
        for (case, number), forms in slots.items():
            for rank, form in enumerate(forms):
                lex.paradigms[lemma][(case, number)].append((100 - rank, form))
            lex.frequencies[lemma] = 1000
    return lex


FRAME = Frame(
    text="Otkazali su izlet zbog ____.",
    case="Gen",
    lemma_class="EVENT",
    explanation="Predlog „zbog“ traži genitiv.",
)


def test_builds_an_item_using_the_lexicon_form() -> None:
    lex = lexicon(nevreme={("Gen", "Sing"): ["nevremena"]})
    items = synthesize_items(lex, frames=[FRAME], lemma_classes={"EVENT": ["nevreme"]})
    assert len(items) == 1
    assert items[0].question == "Otkazali su izlet zbog ____."
    assert items[0].answers == ["nevremena"]
    assert items[0].cue == "nevreme, jednina"


def test_accepts_every_attested_variant_for_the_slot() -> None:
    # A slot with two attested forms must accept both, or a correct answer is
    # marked wrong.
    lex = lexicon(bašta={("Gen", "Plur"): ["bašti", "baštâ"]})
    items = synthesize_items(lex, frames=[FRAME], lemma_classes={"EVENT": ["bašta"]})
    assert items[0].answers == ["bašti", "baštâ"]


def test_skips_a_slot_whose_form_is_the_cue_itself() -> None:
    # Genitive plural of "bašta" is "bašta" — identical to the lemma shown as the cue,
    # so the item would be answerable by echoing the prompt.
    lex = lexicon(bašta={("Gen", "Plur"): ["bašta"], ("Gen", "Sing"): ["bašte"]})
    items = synthesize_items(lex, frames=[FRAME], lemma_classes={"EVENT": ["bašta"]})
    assert [i.answers for i in items] == [["bašte"]]


def test_skips_a_lemma_the_lexicon_does_not_cover() -> None:
    items = synthesize_items(
        lexicon(), frames=[FRAME], lemma_classes={"EVENT": ["nepostojeca"]}
    )
    assert items == []


def test_marks_motion_versus_rest_frames_as_hard() -> None:
    # "u" takes locative or accusative depending on the verb; that distinction is the
    # thing models actually get wrong, so those frames are tiered separately.
    rest = Frame(
        text="Ostali smo u ____ do večeri.",
        case="Loc",
        lemma_class="PLACE",
        explanation="Mirovanje: „u“ + lokativ.",
        difficulty="hard",
    )
    lex = lexicon(grad={("Loc", "Sing"): ["gradu"]})
    items = synthesize_items(lex, frames=[rest], lemma_classes={"PLACE": ["grad"]})
    assert items[0].difficulty == "hard"


def test_is_deterministic_for_a_given_seed() -> None:
    lex = lexicon(
        nevreme={("Gen", "Sing"): ["nevremena"]},
        kvar={("Gen", "Sing"): ["kvara"]},
        kriza={("Gen", "Sing"): ["krize"]},
    )
    classes = {"EVENT": ["nevreme", "kvar", "kriza"]}
    first = synthesize_items(lex, frames=[FRAME], lemma_classes=classes, seed=7)
    second = synthesize_items(lex, frames=[FRAME], lemma_classes=classes, seed=7)
    assert [i.id for i in first] == [i.id for i in second]
    assert [i.answers for i in first] == [i.answers for i in second]


def test_items_are_unverified_and_share_alike_licensed() -> None:
    lex = lexicon(nevreme={("Gen", "Sing"): ["nevremena"]})
    item = synthesize_items(lex, frames=[FRAME], lemma_classes={"EVENT": ["nevreme"]})[0]
    assert item.verified is False
    assert item.license == "CC-BY-SA-4.0"
    assert item.source == "synthetic-srlex"
    assert isinstance(item, ClozeItem)


def test_generated_items_pass_dataset_validation() -> None:
    from serbeval.data import validate_cloze_dataset

    lex = lexicon(
        nevreme={("Gen", "Sing"): ["nevremena"]},
        kvar={("Gen", "Sing"): ["kvara"]},
    )
    items = synthesize_items(
        lex, frames=[FRAME], lemma_classes={"EVENT": ["nevreme", "kvar"]}
    )
    assert validate_cloze_dataset(items) == []


def test_limit_spreads_across_frames_rather_than_filling_one() -> None:
    # Taking the first N in order would emit every lemma of frame 1 and nothing of
    # frame 2, leaving the set unbalanced by construction.
    other = Frame(
        text="Vratili su se posle ____.",
        case="Gen",
        lemma_class="EVENT",
        explanation="Predlog „posle“ traži genitiv.",
    )
    lex = lexicon(
        nevreme={("Gen", "Sing"): ["nevremena"]},
        kvar={("Gen", "Sing"): ["kvara"]},
        kriza={("Gen", "Sing"): ["krize"]},
        pozar={("Gen", "Sing"): ["pozara"]},
    )
    classes = {"EVENT": ["nevreme", "kvar", "kriza", "pozar"]}
    items = synthesize_items(lex, frames=[FRAME, other], lemma_classes=classes, limit=4)
    assert len({i.question.split("____")[0] for i in items}) == 2


def test_skips_a_lemma_whose_form_already_appears_in_the_frame() -> None:
    # "Stavio je knjigu na ____." with the lemma "knjiga" has its own answer sitting in
    # the prompt: accusative singular is "knjigu", which the frame already contains.
    frame = Frame(
        text="Stavio je knjigu na ____.",
        case="Acc",
        lemma_class="OBJECT",
        explanation="Kretanje ka cilju: „na“ + akuzativ.",
    )
    lex = lexicon(
        knjiga={("Acc", "Sing"): ["knjigu"]},
        sanduk={("Acc", "Sing"): ["sanduk"], ("Acc", "Plur"): ["sanduke"]},
    )
    items = synthesize_items(
        lex, frames=[frame], lemma_classes={"OBJECT": ["knjiga", "sanduk"]}
    )
    assert all("knjiga" not in i.cue for i in items)
    assert [i.answers for i in items] == [["sanduke"]]


def test_every_shipped_frame_avoids_leaking_its_own_answer() -> None:
    # Guards the frame list itself: a new frame mentioning a noun from its own class
    # would silently produce items answerable by reading the prompt.
    from serbeval.data import validate_cloze_dataset
    from serbeval.synth import FRAMES, LEMMA_CLASSES

    lex = lexicon(
        **{
            lemma: {(case, "Sing"): [lemma + "om"]}
            for lemmas in LEMMA_CLASSES.values()
            for lemma in lemmas
            for case in ("Gen", "Acc", "Loc", "Dat", "Ins")
        }
    )
    assert validate_cloze_dataset(synthesize_items(lex, frames=FRAMES)) == []
