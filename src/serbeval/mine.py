"""Mine cloze items from a morphologically annotated corpus.

The point is to stop having a model author the exam it will sit. Every item here comes out
of human-annotated text: the sentence is attested, and the gold form is the form a linguist
tagged, not one a model proposed. That removes the bootstrap problem and the need to verify
each gold answer by hand — a human spot-checks a sample instead.

The phenomenon mined is **prepositional case government**: a preposition whose annotation
fixes the case of its noun, with the noun blanked and its lemma given as the cue.

    Otkazali su put zbog ____.  (nevreme)   ->  nevremena

Which prepositions qualify is computed from the corpus, never hardcoded: a preposition is
usable only if it governs one case in at least `min_purity` of its attestations. That matters
because `u` and `na` govern locative OR accusative depending on whether the verb expresses
motion — the preposition alone does not determine the answer, so they are excluded rather
than silently producing unanswerable items. It also means these thresholds keep working when
the corpus is swapped for a different (say, uncontaminated and freshly tagged) one.

What this does NOT fix: contamination. A published treebank's sentences are on the public
web and likely in training data. Point the same miner at recent text to get around that.
"""

from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence

from serbeval.conllu import Sentence, Token
from serbeval.schema import ClozeItem

SOURCE = "ud-serbian-set"
# CC BY-SA is share-alike: items derived from the treebank cannot claim plain CC-BY.
LICENSE = "CC-BY-SA-4.0"

_CASE_NAMES = {
    "Nom": "nominativ",
    "Gen": "genitiv",
    "Dat": "dativ",
    "Acc": "akuzativ",
    "Voc": "vokativ",
    "Loc": "lokativ",
    "Ins": "instrumental",
}
# Agreeing modifiers spell out case/number/gender, which would hand over the answer.
_AGREEING = {"ADJ", "DET", "NUM"}

_MIN_TOKENS = 6
_MAX_TOKENS = 30


def preposition_cases(sentences: Iterable[Sentence]) -> dict[str, Counter[str]]:
    """Per-preposition distribution of the case it governs, measured on this corpus."""
    dist: dict[str, Counter[str]] = defaultdict(Counter)
    for sentence in sentences:
        for token in sentence.tokens:
            if token.upos != "ADP" or token.deprel != "case":
                continue
            head = sentence.by_id(token.head)
            if head is not None and head.upos == "NOUN" and "Case" in head.feats:
                dist[token.lemma.lower()][head.feats["Case"]] += 1
    return dict(dist)


def _reliable_prepositions(
    dist: dict[str, Counter[str]], min_purity: float, min_count: int
) -> dict[str, str]:
    """Prepositions that pin down one case, mapped to that case."""
    reliable = {}
    for prep, cases in dist.items():
        total = sum(cases.values())
        if total < min_count:
            continue
        case, count = cases.most_common(1)[0]
        if count / total >= min_purity:
            reliable[prep] = case
    return reliable


def _is_usable(sentence: Sentence, noun: Token) -> bool:
    """Filters that keep an item answerable and non-trivial."""
    if not (_MIN_TOKENS <= len(sentence.tokens) <= _MAX_TOKENS):
        return False
    if noun.upos != "NOUN":
        return False
    # A form identical to its lemma makes the cue the answer.
    if noun.form.lower() == noun.lemma.lower():
        return False
    others = [t for t in sentence.tokens if t.id != noun.id]
    # The answer must not be readable off the rest of the sentence.
    if any(t.form.lower() == noun.form.lower() for t in others):
        return False
    if any(t.lemma.lower() == noun.lemma.lower() for t in others):
        return False
    # An agreeing modifier spells out case, number and gender, so the item would stop
    # testing whether the preposition's government is known.
    return not any(c.upos in _AGREEING for c in sentence.children(noun.id))


def mine_cloze_items(
    sentences: Sequence[Sentence],
    *,
    min_purity: float = 0.95,
    min_count: int = 20,
    limit: int | None = None,
    task: str = "srb_grammar_cloze",
) -> list[ClozeItem]:
    """Build cloze items from every usable preposition-plus-noun pair in `sentences`."""
    reliable = _reliable_prepositions(
        preposition_cases(sentences), min_purity=min_purity, min_count=min_count
    )

    items: list[ClozeItem] = []
    seen: set[tuple[str, str]] = set()
    seen_questions: set[tuple[str, str]] = set()
    for sentence in sentences:
        for token in sentence.tokens:
            if token.upos != "ADP" or token.deprel != "case":
                continue
            prep = token.lemma.lower()
            required = reliable.get(prep)
            if required is None:
                continue
            noun = sentence.by_id(token.head)
            if noun is None or noun.feats.get("Case") != required:
                continue
            if not _is_usable(sentence, noun):
                continue

            key = (noun.lemma.lower(), required)
            if key in seen:
                continue

            question = sentence.render_with_blank(noun.id)
            plural = noun.feats.get("Number") == "Plur"
            cue = f"{noun.lemma}, {'množina' if plural else 'jednina'}"
            # (question, cue) is the prompt a model actually sees. Two sentences that
            # render alike but blank different words differ by cue and are both usable;
            # a repeated pair would put contradictory gold answers behind one prompt.
            if (question, cue) in seen_questions:
                continue
            seen.add(key)
            seen_questions.add((question, cue))

            plural = noun.feats.get("Number") == "Plur"
            # Number is stated on EVERY item, singular included. Genitive singular "želje"
            # and genitive plural "želja" are both grammatical after "zbog", so a bare
            # lemma would leave two defensible answers and mark one of them wrong.
            cue = f"{noun.lemma}, {'množina' if plural else 'jednina'}"
            case_name = _CASE_NAMES.get(required, required)

            items.append(
                ClozeItem(
                    id=f"srb-cloze-ud-{len(items) + 1:04d}",
                    task=task,
                    category="padezi",
                    question=question,
                    cue=cue,
                    answers=[noun.form],
                    explanation=(
                        f"Predlog „{prep}“ traži {case_name}"
                        f"{' množine' if plural else ''}."
                    ),
                    script="latin",
                    difficulty="medium",
                    source=SOURCE,
                    license=LICENSE,
                )
            )
            if limit is not None and len(items) >= limit:
                return items
    return items
