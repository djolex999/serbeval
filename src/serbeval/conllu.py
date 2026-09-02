"""Minimal CoNLL-U reader — enough of the format to mine cloze items from a treebank.

Deliberately not a general UD library: it reads the ten columns, the `Case=...|Number=...`
feature bundles, and `SpaceAfter=No`, which is everything the miner needs. Multiword-token
ranges (`1-2`) and empty nodes (`1.1`) are skipped, because they are not real tokens and
would corrupt id-based head lookups if kept.

The format is one token per tab-separated line, blank line between sentences, `#` comments
carrying `sent_id` and the original `text`.
"""

from dataclasses import dataclass, field
from pathlib import Path

_BLANK = "____"


@dataclass(frozen=True)
class Token:
    id: int
    form: str
    lemma: str
    upos: str
    feats: dict[str, str] = field(default_factory=dict)
    head: int = 0
    deprel: str = "_"
    space_after: bool = True


@dataclass(frozen=True)
class Sentence:
    sent_id: str
    text: str
    tokens: list[Token]

    def by_id(self, token_id: int) -> Token | None:
        for token in self.tokens:
            if token.id == token_id:
                return token
        return None

    def children(self, token_id: int) -> list[Token]:
        return [t for t in self.tokens if t.head == token_id]

    def render_with_blank(self, token_id: int) -> str:
        """The sentence with one token replaced by the blank marker.

        Rebuilt from tokens rather than sliced out of the `# text` line, so that
        `SpaceAfter=No` keeps punctuation attached: "analizira ____." not "analizira ____ ."
        """
        parts: list[str] = []
        for token in self.tokens:
            parts.append(_BLANK if token.id == token_id else token.form)
            if token.space_after:
                parts.append(" ")
        return "".join(parts).strip()


def _parse_feats(raw: str) -> dict[str, str]:
    if raw == "_":
        return {}
    feats = {}
    for chunk in raw.split("|"):
        if "=" in chunk:
            key, value = chunk.split("=", 1)
            feats[key] = value
    return feats


def _parse_token(line: str) -> Token | None:
    columns = line.split("\t")
    if len(columns) < 10:
        return None
    raw_id = columns[0]
    # "1-2" is a multiword range, "1.1" an empty node — neither is a real token.
    if "-" in raw_id or "." in raw_id:
        return None
    try:
        head = int(columns[6])
    except ValueError:
        head = 0
    return Token(
        id=int(raw_id),
        form=columns[1],
        lemma=columns[2],
        upos=columns[3],
        feats=_parse_feats(columns[5]),
        head=head,
        deprel=columns[7],
        space_after="SpaceAfter=No" not in columns[9],
    )


def parse_conllu(text: str) -> list[Sentence]:
    sentences: list[Sentence] = []
    sent_id = ""
    sent_text = ""
    tokens: list[Token] = []

    def flush() -> None:
        nonlocal sent_id, sent_text, tokens
        if tokens:
            sentences.append(Sentence(sent_id=sent_id, text=sent_text, tokens=tokens))
        sent_id, sent_text, tokens = "", "", []

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        if stripped.startswith("#"):
            if "=" in stripped:
                key, _, value = stripped.lstrip("#").strip().partition("=")
                key, value = key.strip(), value.strip()
                if key == "sent_id":
                    sent_id = value
                elif key == "text":
                    sent_text = value
            continue
        token = _parse_token(line)
        if token is not None:
            tokens.append(token)
    flush()
    return sentences


def load_conllu(path: Path | str) -> list[Sentence]:
    return parse_conllu(Path(path).read_text(encoding="utf-8"))
