"""Find Serbian language errors in arbitrary generated text.

This is not the benchmark. The benchmark asks "how good is this model at Serbian" using
items with known answers; this asks "what is wrong with THIS text", which has no gold
answer to compare against. Different problem, same lexicon.

Four checks, all pure lookups against an inflectional lexicon — no model, no parser, no
API key, so it runs on real product output today:

* **mixed script** — a Cyrillic letter inside a Latin word (or the reverse). Invisible to
  the reader, broken in the data, and a very common LLM failure for Serbian.
* **missing diacritics** — "basti" where the lexicon has "bašti". Probably the single most
  frequent way generated Serbian goes wrong, and the one readers notice first.
* **unknown forms** — a word form absent from the lexicon: a typo, or an inflection the
  model invented.
* **dialect mixing** — ekavian and ijekavian spellings of the same word in one document
  ("mera" alongside "mjera"), which matters when the output is meant to be consistent.

What it deliberately does NOT do is judge meaning. If the text says the war began in the
wrong year, a lexicon has no opinion; that needs a judge model and is a separate problem.

Two accuracy notes, both deliberate. Capitalised tokens are exempt from the lexicon checks
because proper nouns are the bulk of any lexicon's misses and flagging them would bury
every real finding under names. And a document is only reported as dialect-mixed when both
variants actually occur, never on a single ijekavian word.
"""

import gzip
import re
from dataclasses import dataclass, field
from pathlib import Path

# Latin letters used by Serbian, plus the Cyrillic block.
_LATIN = set("abcdefghijklmnopqrstuvwxyzčćžšđ")
_CYRILLIC_RANGE = range(0x0400, 0x0500)
_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)

_FOLD = str.maketrans({"č": "c", "ć": "c", "ž": "z", "š": "s", "đ": "d"})


@dataclass(frozen=True)
class Token:
    text: str
    line: int
    column: int


@dataclass(frozen=True)
class Finding:
    kind: str
    message: str
    token: str = ""
    line: int = 0
    column: int = 0


def _is_cyrillic(ch: str) -> bool:
    return ord(ch) in _CYRILLIC_RANGE


def _is_latin(ch: str) -> bool:
    return ch.lower() in _LATIN


def fold_diacritics(word: str) -> str:
    """č/ć -> c, ž -> z, š -> s, đ -> d. Used only to *find* a missing diacritic."""
    return word.lower().translate(_FOLD)


# The ijekavian reflex of yat never starts a word, and the shortest real alternations
# ("mjera") are five letters. Without both guards "je" de-jekavizes to the known form
# "e" and the copula gets classified as a dialect marker on every document.
_MIN_JEKAVIAN_LENGTH = 5


def dejekavize(word: str) -> str:
    """Map an ijekavian spelling towards its ekavian counterpart ("mjera" -> "mera")."""
    if len(word) < _MIN_JEKAVIAN_LENGTH:
        return word
    head, tail = word[0], word[1:]
    return head + tail.replace("ije", "e").replace("je", "e")


def tokenize(text: str) -> list[Token]:
    tokens = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for match in _WORD.finditer(line):
            tokens.append(
                Token(text=match.group(), line=line_number, column=match.start() + 1)
            )
    return tokens


@dataclass
class FormIndex:
    """Known word forms, plus the two derived lookups the checks need."""

    forms: set[str] = field(default_factory=set)
    # de-diacriticized spelling -> the real forms it could be
    folded: dict[str, list[str]] = field(default_factory=dict)
    # forms that look ijekavian because de-jekavizing them lands on another known form
    ijekavian: set[str] = field(default_factory=set)
    # the ekavian spellings those map onto — precomputed, because testing membership
    # per token against the whole ijekavian set is quadratic on a real lexicon
    ekavian: set[str] = field(default_factory=set)

    @classmethod
    def build(cls, forms: set[str]) -> "FormIndex":
        lowered = {form.lower() for form in forms}
        folded: dict[str, list[str]] = {}
        for form in lowered:
            stripped = fold_diacritics(form)
            if stripped != form:
                folded.setdefault(stripped, []).append(form)
        ijekavian = {
            form
            for form in lowered
            if dejekavize(form) != form and dejekavize(form) in lowered
        }
        return cls(
            forms=lowered,
            folded={k: sorted(v) for k, v in folded.items()},
            ijekavian=ijekavian,
            ekavian={dejekavize(form) for form in ijekavian},
        )

    def knows(self, word: str) -> bool:
        return word.lower() in self.forms


def _script_findings(tokens: list[Token]) -> list[Finding]:
    findings = []
    cyrillic_words = latin_words = 0
    for token in tokens:
        has_cyrillic = any(_is_cyrillic(ch) for ch in token.text)
        has_latin = any(_is_latin(ch) for ch in token.text)
        if has_cyrillic and has_latin:
            findings.append(
                Finding(
                    kind="mixed-script-word",
                    message=f"„{token.text}“ meša ćirilicu i latinicu unutar iste reči",
                    token=token.text,
                    line=token.line,
                    column=token.column,
                )
            )
        elif has_cyrillic:
            cyrillic_words += 1
        elif has_latin:
            latin_words += 1

    if cyrillic_words and latin_words:
        findings.append(
            Finding(
                kind="mixed-script-document",
                message=(
                    f"tekst meša pisma: {latin_words} latiničnih i "
                    f"{cyrillic_words} ćiriličnih reči"
                ),
            )
        )
    return findings


def _lexicon_findings(tokens: list[Token], index: FormIndex) -> list[Finding]:
    findings = []
    for token in tokens:
        word = token.text
        # Proper nouns dominate any lexicon's misses; checking them buries real findings.
        if word[:1].isupper():
            continue
        lowered = word.lower()
        if index.knows(lowered):
            continue
        candidates = index.folded.get(fold_diacritics(lowered), [])
        if candidates:
            findings.append(
                Finding(
                    kind="missing-diacritics",
                    message=f"„{word}“ nije oblik u rečniku; verovatno „{candidates[0]}“",
                    token=word,
                    line=token.line,
                    column=token.column,
                )
            )
        else:
            findings.append(
                Finding(
                    kind="unknown-form",
                    message=f"„{word}“ nije poznat oblik — tipfeler ili izmišljena fleksija",
                    token=word,
                    line=token.line,
                    column=token.column,
                )
            )
    return findings


def _dialect_findings(tokens: list[Token], index: FormIndex) -> list[Finding]:
    """Report only when BOTH variants occur — one ijekavian word is a choice, not a bug."""
    ijekavian = {t.text.lower() for t in tokens if t.text.lower() in index.ijekavian}
    ekavian = {
        t.text.lower()
        for t in tokens
        if t.text.lower() in index.ekavian and t.text.lower() not in index.ijekavian
    }
    if ijekavian and ekavian:
        return [
            Finding(
                kind="dialect-mixing",
                message=(
                    "tekst meša ekavicu i ijekavicu: "
                    f"{', '.join(sorted(ekavian))} vs {', '.join(sorted(ijekavian))}"
                ),
            )
        ]
    return []


def check_text(text: str, index: FormIndex) -> list[Finding]:
    """Every finding in `text`, in reading order with document-level findings last."""
    tokens = tokenize(text)
    findings = _script_findings(tokens)
    findings += _lexicon_findings(tokens, index)
    findings += _dialect_findings(tokens, index)
    return sorted(findings, key=lambda f: (f.line == 0, f.line, f.column))


def forms_from_lexicon(path: Path | str) -> set[str]:
    """Every surface form in an srLex-format file, across ALL parts of speech.

    `serbeval.lexicon` indexes one part of speech into paradigms because the generators
    need noun declensions. A checker needs the opposite: a flat set covering verbs,
    adverbs and everything else, or it reports ordinary words as unknown.
    """
    forms: set[str] = set()
    opener = gzip.open if Path(path).suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            columns = line.rstrip("\n").split("\t")
            if len(columns) < 5:
                continue
            # Proper nouns are excluded on purpose. srLex carries acronyms like "CE",
            # which lowercase into ordinary-looking words and mask real errors — "ce"
            # for "će" being the costly one. Capitalised tokens are skipped when
            # checking anyway, so proper nouns add nothing and hide findings.
            if columns[4] == "PROPN":
                continue
            forms.add(columns[0].lower())
    return forms


def write_form_index(forms: set[str], path: Path | str) -> None:
    """Store the forms as one sorted word per line, gzipped.

    Deliberately not the raw lexicon: srLex is ~54 MB of eight columns, of which the
    checker uses exactly one. Sorted so the file diffs and compresses well.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(sorted(forms)) + "\n"
    if target.suffix == ".gz":
        target.write_bytes(gzip.compress(body.encode("utf-8")))
    else:
        target.write_text(body, encoding="utf-8")


def load_form_index(path: Path | str) -> FormIndex:
    source = Path(path)
    if source.suffix == ".gz":
        text = gzip.decompress(source.read_bytes()).decode("utf-8")
    else:
        text = source.read_text(encoding="utf-8")
    return FormIndex.build({line for line in text.splitlines() if line})
