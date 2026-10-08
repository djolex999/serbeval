"""Gold verification worksheet: the maintainer checks items WITH the answer shown.

`serbeval baseline` is blind on purpose: it hides the gold so a native speaker's score
says whether the items are sound. That is the right control for a sample, but too slow
to verify a whole set. Verification asks a different question — "is this gold correct,
and is it the only correct answer?" — so the sheet shows the gold and the explanation,
and the maintainer only marks each item on its check line:

    ok                 the gold is right; the item becomes verified
    x <answer>         the gold is wrong: a letter for MCQ, form(s) for cloze („a / b“)
    + <form>           the gold is right, but this form is also correct (cloze only)
    ?                  contested or unsure: stays unverified, kept out of the official set
    -                  the item is bad (unnatural, ambiguous): removed to discarded.jsonl

Anything after `#` on the line is a comment. A blank check line means "not reviewed".
"""

import random
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from serbeval.schema import ANSWER_LETTERS, ClozeItem, EvalItem

Item = EvalItem | ClozeItem
Kind = Literal["ok", "fix", "add", "unsure", "drop"]

_CHECK = "PROVERA:"
_ID_LINE = re.compile(r"^\[\d+\]\s+(\S+)")
_CHECK_LINE = re.compile(rf"^{_CHECK}\s*(.*)$")
_FORM_SEPARATOR = "/"

_HEADER = """# serbeval — provera tačnih odgovora
#
# Ovde VIDIŠ tačan odgovor. Pitanje je: da li je tačan, i da li je jedini tačan?
# Na svaku liniju PROVERA upiši jednu oznaku:
#
#   ok                 tačno je — item postaje proveren
#   x <ispravka>       pogrešno je — za ponuđene odgovore slovo (A-D), za dopunu
#                      ispravan oblik; više tačnih oblika odvoji sa „ / “
#   + <oblik>          tačno je, ali je tačan i ovaj oblik (samo za dopunu)
#   ?                  sporno ili nisi siguran — ostaje neprovereno, ne ulazi u zvanični set
#   -                  loš item (neprirodna ili dvosmislena rečenica) — izbacuje se
#
# Komentar posle # se ignoriše. Prazna PROVERA = nisi stigao do tog itema; možeš da
# radiš u delovima i da primeniš više puta.
#
# Kad završiš:  serbeval verify --apply <ovaj fajl>
"""


@dataclass(frozen=True)
class Verdict:
    kind: Kind
    value: str = ""


def select_for_verification(
    core: Sequence[Item], others: Sequence[Item], *, n: int, seed: int = 0
) -> list[Item]:
    """Every unverified core item, then a seeded spread of unverified others up to `n`."""
    picked = [item for item in core if not item.verified]
    seen = {item.id for item in picked}
    rest = [item for item in others if not item.verified and item.id not in seen]
    rng = random.Random(seed)
    rng.shuffle(rest)
    # Round-robin over tasks so the top-up is not all from the largest set.
    by_task: dict[str, list[Item]] = {}
    for item in rest:
        by_task.setdefault(item.task, []).append(item)
    queues = [by_task[task] for task in sorted(by_task)]
    while len(picked) < n and any(queues):
        for queue in queues:
            if queue and len(picked) < n:
                picked.append(queue.pop(0))
    return picked


def build_verification_sheet(items: Sequence[Item]) -> str:
    lines = [_HEADER]
    for number, item in enumerate(items, start=1):
        lines.append(f"[{number}] {item.id}   ({item.task} · {item.category})")
        if isinstance(item, ClozeItem):
            lines.append(f"{item.question}  ({item.cue})")
            lines.append(f"TAČNO: {f' {_FORM_SEPARATOR} '.join(item.answers)}")
        else:
            lines.append(item.question)
            for letter, choice in zip(ANSWER_LETTERS, item.choices, strict=False):
                lines.append(f"  {letter}) {choice}")
            lines.append(f"TAČNO: {item.answer_letter}) {item.choices[item.answer_index]}")
        lines.append(f"Objašnjenje: {item.explanation}")
        lines.append(_CHECK)
        lines.append("")
    return "\n".join(lines)


def _parse_mark(item_id: str, raw: str) -> Verdict | None:
    mark = raw.split("#", 1)[0].strip()
    if not mark:
        return None
    head, _, rest = mark.partition(" ")
    head, rest = head.lower(), rest.strip()
    if head == "ok" and not rest:
        return Verdict("ok")
    if head == "?" and not rest:
        return Verdict("unsure")
    if head == "-" and not rest:
        return Verdict("drop")
    if head in ("x", "+"):
        if not rest:
            raise ValueError(f"{item_id}: „{head}“ needs a value after it")
        return Verdict("fix" if head == "x" else "add", rest)
    raise ValueError(f"{item_id}: unknown mark {mark!r} (use ok, x …, + …, ?, -)")


def parse_verification_sheet(text: str) -> dict[str, Verdict]:
    """Map item id -> its verdict; unmarked items are left out."""
    verdicts: dict[str, Verdict] = {}
    current: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if match := _ID_LINE.match(stripped):
            current = match.group(1)
            continue
        if (check := _CHECK_LINE.match(stripped)) and current is not None:
            verdict = _parse_mark(current, check.group(1))
            if verdict is not None:
                verdicts[current] = verdict
            current = None
    return verdicts


def _forms(value: str) -> list[str]:
    forms: list[str] = []
    for form in (part.strip() for part in value.split(_FORM_SEPARATOR)):
        if form and form not in forms:
            forms.append(form)
    return forms


def apply_verdict(item: Item, verdict: Verdict) -> Item | None:
    """The item after the maintainer's verdict; None means it is dropped."""
    if verdict.kind == "drop":
        return None
    if verdict.kind == "unsure":
        return item
    if verdict.kind == "ok":
        return item.model_copy(update={"verified": True})

    if isinstance(item, EvalItem):
        if verdict.kind == "add":
            raise ValueError(f"{item.id}: „+“ adds a form and only applies to cloze items")
        letter = verdict.value.strip().upper()
        if len(letter) != 1 or letter not in ANSWER_LETTERS:
            raise ValueError(f"{item.id}: a fix for a multiple-choice item is a letter A-D")
        return item.model_copy(
            update={"answer_index": ANSWER_LETTERS.index(letter), "verified": True}
        )

    forms = _forms(verdict.value)
    answers = forms if verdict.kind == "fix" else [*item.answers, *(f for f in forms
                                                                   if f not in item.answers)]
    # Re-validate: answers must stay non-blank and unique.
    return ClozeItem.model_validate({**item.model_dump(), "answers": answers, "verified": True})


def build_verification_html(items: Sequence[Item], *, title: str) -> str:
    """The same worksheet as a single offline HTML page; its download feeds `--apply`."""
    from serbeval.verify_page import build_verification_html as build

    return build(items, title=title)
