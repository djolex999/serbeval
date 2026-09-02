"""Build cloze items from hand-written sentence frames plus an inflectional lexicon.

This is the answer to contamination. Mining takes attested sentences, which for any public
corpus are already on the web and plausibly in training data. Synthesis writes the sentence
itself, so it demonstrably never existed before — and the gold form still comes from a
lexicon rather than from a tagger or a model, so nothing is guessed:

    frame:    "Otkazali su izlet zbog ____."   (requires genitive)
    lexicon:  nevreme -> nevremena (Gen Sing)

Three properties fall out of that. Verification cost collapses from one check per item to
one check per *frame*, since a frame that is grammatical for one lemma of its class is
grammatical for all of them. Scale becomes free. And the exam is no longer written by the
kind of system sitting it.

Because the frames are authored, the case is guaranteed by construction rather than inferred
— which is why, unlike `serbeval.mine`, this module can use `u` and `na`. Those govern
locative OR accusative depending on whether the verb expresses motion, so mining had to skip
them; here the frame supplies the verb, making that contrast the deliberate `hard` tier.

Semantic classes keep the sentences sensible: a frame declares the kind of noun its blank
takes, and only lemmas of that class are substituted, so no item reads "otkazali su izlet
zbog abakusa".
"""

import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from serbeval.lexicon import Lexicon
from serbeval.schema import ClozeItem

SOURCE = "synthetic-srlex"
# Forms are taken from srLex, which is CC BY-SA; the share-alike term carries over.
LICENSE = "CC-BY-SA-4.0"

_NUMBERS = ("Sing", "Plur")


@dataclass(frozen=True)
class Frame:
    text: str
    case: str
    lemma_class: str
    explanation: str
    difficulty: str = "medium"


# Nouns grouped by the semantic role a frame needs, so substitution stays plausible.
LEMMA_CLASSES: dict[str, list[str]] = {
    "EVENT": [
        "nevreme", "kiša", "kvar", "štrajk", "kriza", "požar", "gužva", "bolest",
        "sastanak", "koncert", "utakmica", "ispit", "svađa", "poplava", "nesreća",
    ],
    "PLACE": [
        "grad", "selo", "škola", "bolnica", "biblioteka", "tržnica", "fabrika", "luka",
        "planina", "reka", "kuhinja", "dvorište", "bašta", "kancelarija", "šuma",
    ],
    "PERSON": [
        "lekar", "komšija", "profesor", "vozač", "radnik", "student", "sudija",
        "novinar", "trener", "pekar", "brat", "sestra", "prijatelj",
    ],
    "ABSTRACT": [
        "sloboda", "pravda", "istina", "sreća", "ljubav", "strpljenje", "hrabrost",
        "nada", "mir", "znanje", "mladost", "tuga",
    ],
    # OBJECT is split three ways on purpose. A single "things" class produced
    # grammatical nonsense — "Knjiga je ostala na olovci", "Otvorio je vrata
    # stolicama" — because what you rest a book ON and what you open a door WITH are
    # not the same set. The class a frame declares is a semantic role, not a category.
    "OBJECT": [
        "ranac", "telefon", "knjiga", "sat", "torba", "ogledalo", "kaput", "novčanik",
    ],
    "SURFACE": [
        "sanduk", "stolica", "polica", "klupa", "terasa", "daska", "prozor", "tastatura",
    ],
    "TOOL": [
        "ključ", "čekić", "nož", "olovka", "krpa", "makaze", "lopata",
    ],
}


FRAMES: list[Frame] = [
    # --- genitive ---------------------------------------------------------
    Frame("Otkazali su izlet zbog ____.", "Gen", "EVENT", "Predlog „zbog“ traži genitiv."),
    Frame("Vratili su se kući posle ____.", "Gen", "EVENT", "Predlog „posle“ traži genitiv."),
    Frame("Paket je stigao iz ____.", "Gen", "PLACE", "Predlog „iz“ traži genitiv."),
    Frame("Nije mogao da počne bez ____.", "Gen", "OBJECT", "Predlog „bez“ traži genitiv."),
    Frame("Dugo su razgovarali tokom ____.", "Gen", "EVENT", "Predlog „tokom“ traži genitiv."),
    Frame("Stigli smo do ____ pre mraka.", "Gen", "PLACE", "Predlog „do“ traži genitiv."),
    Frame("Seo je pored ____.", "Gen", "PERSON", "Predlog „pored“ traži genitiv."),
    Frame("Okupili su se oko ____.", "Gen", "SURFACE", "Predlog „oko“ traži genitiv."),
    Frame("Glasali su protiv ____.", "Gen", "EVENT", "Predlog „protiv“ traži genitiv."),
    # --- accusative -------------------------------------------------------
    Frame("Kupili su poklon za ____.", "Acc", "PERSON", "Predlog „za“ traži akuzativ."),
    Frame("Prošli smo kroz ____.", "Acc", "PLACE", "Predlog „kroz“ traži akuzativ."),
    Frame("Popeli su se uz ____.", "Acc", "PLACE", "Predlog „uz“ traži akuzativ."),
    # --- locative ---------------------------------------------------------
    Frame("Dugo su razgovarali o ____.", "Loc", "ABSTRACT", "Predlog „o“ traži lokativ."),
    Frame("Novine su pisale o ____.", "Loc", "EVENT", "Predlog „o“ traži lokativ."),
    # --- dative -----------------------------------------------------------
    Frame("Krenuli su ka ____.", "Dat", "PLACE", "Predlog „ka“ traži dativ."),
    # --- instrumental -----------------------------------------------------
    Frame("Došao je na proslavu sa ____.", "Ins", "PERSON", "Predlog „sa“ traži instrumental."),
    Frame(
        "Otvorio je vrata ____.",
        "Ins",
        "TOOL",
        "Sredstvo se iskazuje golim instrumentalom, bez predloga „sa“.",
    ),
    # --- motion vs rest: the distinction models actually get wrong ---------
    Frame(
        "Ostali smo u ____ do večeri.",
        "Loc",
        "PLACE",
        "Glagol označava mirovanje, pa „u“ traži lokativ.",
        difficulty="hard",
    ),
    Frame(
        "Ušli smo u ____ i seli.",
        "Acc",
        "PLACE",
        "Glagol označava kretanje ka cilju, pa „u“ traži akuzativ.",
        difficulty="hard",
    ),
    Frame(
        "Radi u ____ već deset godina.",
        "Loc",
        "PLACE",
        "Glagol označava mirovanje, pa „u“ traži lokativ.",
        difficulty="hard",
    ),
    Frame(
        "Preselili su se u ____ prošle godine.",
        "Acc",
        "PLACE",
        "Glagol označava kretanje ka cilju, pa „u“ traži akuzativ.",
        difficulty="hard",
    ),
    Frame(
        "Knjiga je ostala na ____.",
        "Loc",
        "SURFACE",
        "Mirovanje: „na“ + lokativ.",
        difficulty="hard",
    ),
    Frame(
        "Stavio je knjigu na ____.",
        "Acc",
        "SURFACE",
        "Kretanje ka cilju: „na“ + akuzativ.",
        difficulty="hard",
    ),
]


def _candidates(
    lexicon: Lexicon, frames: Sequence[Frame], lemma_classes: Mapping[str, Sequence[str]]
) -> list[list[tuple[Frame, str, str, list[str]]]]:
    """Usable (frame, lemma, number, forms) tuples, grouped per frame."""
    grouped = []
    for frame in frames:
        frame_words = {
            word.strip(".,;:!?„“\"'()").lower() for word in frame.text.split()
        }
        rows = []
        for lemma in lemma_classes.get(frame.lemma_class, []):
            for number in _NUMBERS:
                forms = lexicon.forms(lemma, case=frame.case, number=number)
                if not forms:
                    continue
                # A slot containing the lemma itself is answerable by echoing the cue.
                if any(form.lower() == lemma.lower() for form in forms):
                    continue
                # ...and a frame that already mentions this noun hands over the answer:
                # "Stavio je knjigu na ____." (knjiga) has "knjigu" sitting in the prompt.
                if any(form.lower() in frame_words for form in forms):
                    continue
                rows.append((frame, lemma, number, forms))
        grouped.append(rows)
    return grouped


def synthesize_items(
    lexicon: Lexicon,
    *,
    frames: Sequence[Frame] = tuple(FRAMES),
    lemma_classes: Mapping[str, Sequence[str]] = LEMMA_CLASSES,
    limit: int | None = None,
    seed: int = 0,
    task: str = "srb_grammar_cloze",
) -> list[ClozeItem]:
    """Generate one item per (frame, lemma, number) the lexicon can fill.

    `limit` is applied round-robin across frames, not by truncation: taking the first N
    in order would emit every lemma of the first frame and none of the last, leaving the
    set unbalanced by construction.
    """
    grouped = _candidates(lexicon, frames, lemma_classes)
    rng = random.Random(seed)
    for rows in grouped:
        rng.shuffle(rows)

    ordered: list[tuple[Frame, str, str, list[str]]] = []
    for depth in range(max((len(rows) for rows in grouped), default=0)):
        for rows in grouped:
            if depth < len(rows):
                ordered.append(rows[depth])
        if limit is not None and len(ordered) >= limit:
            break

    items: list[ClozeItem] = []
    for frame, lemma, number, forms in ordered[:limit]:
        plural = number == "Plur"
        items.append(
            ClozeItem(
                id=f"srb-cloze-syn-{len(items) + 1:04d}",
                task=task,
                category="padezi",
                question=frame.text,
                cue=f"{lemma}, {'množina' if plural else 'jednina'}",
                answers=forms,
                explanation=frame.explanation,
                script="latin",
                difficulty=frame.difficulty,  # type: ignore[arg-type]
                source=SOURCE,
                license=LICENSE,
            )
        )
    return items
