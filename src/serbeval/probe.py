"""Difficulty probe: small sets of candidate-hard phenomena, measured before any is built out.

serbeval is correct but at ceiling (Opus 5.5 230/230 on the Kie triage run), so each
candidate phenomenon gets ~20 cloze items and a model run first; only those where models
fall below ~90% earn a full set and the maintainer's verification time.

Two of the six phenomena are synthesised here, with the gold answer taken from srLex:
aorist and sibilarization/palatalization. Unlike `serbeval.synth`, every slot is filtered
to ATTESTED forms (corpus frequency > 0). srLex fills unattested slots from a generator,
and that generator gets wrong exactly what these items test — it lists „mačci“ beside the
correct „mački“, „tetci“ beside „tetki“ — so a frequency-0 form must never become gold.
The imperfect is not synthesised at all: nearly all its srLex forms are frequency 0, and
some are wrong outright (`videh` filed as the imperfect of videti, which is viđah).

The frames name their lemmas directly instead of using semantic classes: these sets are
tiny, and the lemmas are chosen for the phenomenon (velar stems, the exceptions to them),
not for coverage.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from serbeval.lexicon import Lexicon, VerbLexicon
from serbeval.schema import ClozeItem

TASK = "srb_probe"
SOURCE = "synthetic-srlex"
LICENSE = "CC-BY-SA-4.0"
ATTESTED = 1


@dataclass(frozen=True)
class NounFrame:
    text: str
    case: str
    number: str
    lemmas: tuple[str, ...]
    explanation: str


@dataclass(frozen=True)
class VerbFrame:
    text: str
    person: str
    number: str
    lemmas: tuple[str, ...]
    explanation: str
    tense: str = "aorist"


def _item(
    category: str, index: int, question: str, cue: str, answers: list[str], explanation: str
) -> ClozeItem:
    return ClozeItem(
        id=f"srb-probe-{category}-syn-{index:04d}",
        task=TASK,
        category=category,
        question=question,
        cue=cue,
        answers=answers,
        explanation=explanation,
        script="latin",
        difficulty="hard",
        source=SOURCE,
        license=LICENSE,
    )


def synthesize_noun_probe(
    lexicon: Lexicon, frames: Sequence[NounFrame], *, category: str
) -> list[ClozeItem]:
    items: list[ClozeItem] = []
    for frame in frames:
        number_word = "množina" if frame.number == "Plur" else "jednina"
        for lemma in frame.lemmas:
            answers = lexicon.forms(
                lemma, case=frame.case, number=frame.number, min_frequency=ATTESTED
            )
            if not answers:
                continue
            items.append(
                _item(
                    category,
                    len(items) + 1,
                    frame.text,
                    f"{lemma}, {number_word}",
                    answers,
                    frame.explanation,
                )
            )
    return items


_TENSE_WORD = {"aorist": "aorist", "imperfect": "imperfekat"}


def synthesize_verb_probe(
    lexicon: VerbLexicon, frames: Sequence[VerbFrame], *, category: str
) -> list[ClozeItem]:
    items: list[ClozeItem] = []
    for frame in frames:
        for lemma in frame.lemmas:
            answers = lexicon.forms(
                lemma,
                tense=frame.tense,
                person=frame.person,
                number=frame.number,
                min_frequency=ATTESTED,
            )
            if not answers:
                continue
            items.append(
                _item(
                    category,
                    len(items) + 1,
                    frame.text,
                    f"{lemma}, {_TENSE_WORD[frame.tense]}",
                    answers,
                    frame.explanation,
                )
            )
    return items


_SIB = "ispred -i velar k, g, h prelazi u c, z, s (sibilarizacija)"

SIBILARIZATION_FRAMES: list[NounFrame] = [
    NounFrame(
        "Na trgu su se okupili ____ iz celog kraja.",
        "Nom",
        "Plur",
        ("junak", "đak", "siromah", "momak"),
        f"Nominativ množine na -i: {_SIB}.",
    ),
    NounFrame(
        "Ovogodišnji ____ bili su mnogo teži od prošlogodišnjih.",
        "Nom",
        "Plur",
        ("zadatak",),
        f"Nominativ množine na -i: {_SIB}.",
    ),
    NounFrame(
        "Lekar je rekao da su mu ____ potpuno zdravi.",
        "Nom",
        "Plur",
        ("bubreg",),
        f"Nominativ množine na -i: {_SIB}.",
    ),
    NounFrame(
        "Po staroj kući noću su lutali ____.",
        "Nom",
        "Plur",
        ("duh",),
        "Jednosložne imenice dobijaju umetak -ov-, pa sibilarizacije nema: duhovi.",
    ),
    NounFrame(
        "Za praznik je kupila poklon ____.",
        "Dat",
        "Sing",
        ("majka", "tetka", "baka", "snaha"),
        "Dativ jednine na -i; sibilarizacija izostaje kod hipokoristika i ispred suglasničke "
        "grupe (baki, tetki), a sprovodi se u ostalim slučajevima (majci).",
    ),
    NounFrame(
        "Dugo je pričala o svojoj ____.",
        "Loc",
        "Sing",
        ("mačka", "knjiga", "noga"),
        "Lokativ jednine na -i; sibilarizacija se sprovodi (knjizi, nozi), osim u grupama "
        "kao -čk- (mački).",
    ),
    NounFrame(
        "____, sačuvaj nas od nevolje!",
        "Voc",
        "Sing",
        ("bog",),
        "Vokativ na -e: velar k, g, h prelazi u č, ž, š (palatalizacija): Bože.",
    ),
    NounFrame(
        "Hajde, ____, pomozi mi da podignem ovo!",
        "Voc",
        "Sing",
        ("drug", "junak", "momak", "čovek"),
        "Vokativ na -e: velar k, g, h prelazi u č, ž, š (palatalizacija).",
    ),
    NounFrame(
        "Ne boj se, mali ____, ništa ti neće biti.",
        "Voc",
        "Sing",
        ("vuk",),
        "Vokativ na -e: velar k prelazi u č (palatalizacija): vuče.",
    ),
]

AORIST_FRAMES: list[VerbFrame] = [
    VerbFrame("Ja ____ kući tek pred ponoć.", "1", "Sing", ("doći", "stići"),
              "Aorist, 1. lice jednine."),
    VerbFrame("Gosti ____ bez pozdrava i više se nisu vratili.", "3", "Plur",
              ("otići", "pobeći"), "Aorist, 3. lice množine."),
    VerbFrame("Mi ____ na stanicu u poslednji čas.", "1", "Plur", ("stići",),
              "Aorist, 1. lice množine."),
    VerbFrame("Ja ____ ključ sa stola i izađoh.", "1", "Sing", ("uzeti", "podići"),
              "Aorist, 1. lice jednine."),
    VerbFrame("Kad je pala noć, deca ____ kao zaklana.", "3", "Plur", ("zaspati",),
              "Aorist, 3. lice množine; zbirna imenica „deca“ traži glagol u množini."),
    VerbFrame("On mi tada ____ da više ne dolazim.", "3", "Sing", ("reći",),
              "Aorist, 3. lice jednine."),
    VerbFrame("Starac polako ____ sa klupe i ode.", "3", "Sing", ("ustati",),
              "Aorist, 3. lice jednine."),
    VerbFrame("Na pijaci ja ____ starog prijatelja.", "1", "Sing", ("sresti",),
              "Aorist, 1. lice jednine."),
    VerbFrame("Susedi nam ____ hleb i vino.", "3", "Plur", ("doneti",),
              "Aorist, 3. lice množine."),
]
