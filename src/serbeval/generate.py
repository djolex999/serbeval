"""Candidate item generation via the Claude API.

Generated items land in data/<task>/candidates.jsonl with verified=False; they are
merged into items.jsonl only after the selfcheck filter and a human review pass.
"""

from collections.abc import Iterable, Set

import anthropic
from pydantic import BaseModel, Field

from serbeval.schema import EvalItem

DEFAULT_MODEL = "claude-opus-4-8"

COMMON_RULES = """\
PRAVILA (poštuj svako):
- Savremeni standardni srpski jezik, EKAVSKA varijanta, LATINICA.
- Tačno 4 ponuđena odgovora; TAČNO JEDAN ispravan po normi (Pravopis srpskoga jezika MS,
  normativna gramatika). Distraktori su greške koje izvorni govornici zaista prave.
- Nikad ne nudi ispravan ijekavski oblik kao "pogrešan" odgovor; izbegavaj sporne norme.
- Pitanja samostalna i raznovrsna po formi; raznovrsna težina.
- explanation: 1-2 rečenice na srpskom zašto je tačan odgovor tačan."""

CATEGORY_BRIEFS: dict[tuple[str, str], str] = {
    ("srb_grammar", "padezi"): (
        "Rekcija glagola i predloga i upotreba padeža: instrumental sredstva bez 'sa', "
        "akuzativ vs lokativ posle u/na, genitiv uz brojeve, zbog/radi, vokativ."
    ),
    ("srb_grammar", "glagolski-vid"): (
        "Izbor svršenog/nesvršenog glagola u kontekstu; fazni glagoli traže nesvršeni vid; "
        "iterativni konteksti."
    ),
    ("srb_grammar", "kongruencija"): (
        "Paukal uz 2/3/4, brojevi 5+, zbirne imenice, većina/manjina, slaganje prideva."
    ),
    ("srb_grammar", "enklitike"): (
        "Red i položaj enklitika: drugo mesto, redosled li > glagolske > dativske > "
        "akuzativske > se, sažimanje 'se je'."
    ),
    ("srb_grammar", "komparacija"): "Nepravilni komparativi i superlativi prideva i priloga.",
    ("srb_grammar", "pravopis"): (
        "Sastavljeno/rastavljeno pisanje, futur I, rečca li, č/ć i dž/đ, veliko slovo."
    ),
    ("srb_grammar", "standard"): (
        "Bezlično 'treba da', 's obzirom na to da', 'u vezi s tim', zahvaliti (se), oba/obe."
    ),
}


class CandidateItem(BaseModel):
    question: str
    choices: list[str] = Field(min_length=4, max_length=4)
    answer_index: int = Field(ge=0, le=3)
    explanation: str


class CandidateBatch(BaseModel):
    items: list[CandidateItem]


def _slug(task: str) -> str:
    return task.replace("_", "-")


def next_id(task: str, category: str, existing_ids: Set[str]) -> str:
    prefix = f"{_slug(task)}-{category}-"
    max_seq = 0
    for existing in existing_ids:
        tail = existing.removeprefix(prefix)
        if tail != existing and tail.isdigit():
            max_seq = max(max_seq, int(tail))
    return f"{prefix}{max_seq + 1:04d}"


def build_prompt(task: str, category: str, n: int, existing_questions: Iterable[str]) -> str:
    brief = CATEGORY_BRIEFS.get(
        (task, category), f"Stavke za zadatak '{task}', kategorija '{category}'."
    )
    existing = "\n".join(f"- {q}" for q in existing_questions)
    avoid = (
        f"\nVEĆ POSTOJE (ne ponavljaj ih niti pravi bliske varijante):\n{existing}"
        if existing
        else ""
    )
    return f"""Ti si lingvista za srpski jezik i autor stavki za benčmark "{task}".
Napiši tačno {n} stavki višestrukog izbora za kategoriju "{category}".
SPEC KATEGORIJE: {brief}
{COMMON_RULES}{avoid}"""


def generate_candidates(
    client: anthropic.Anthropic,
    *,
    task: str,
    category: str,
    n: int,
    model: str,
    existing_ids: Set[str],
    existing_questions: Set[str],
) -> list[EvalItem]:
    prompt = build_prompt(task, category, n, sorted(existing_questions))
    response = client.messages.parse(
        model=model,
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}],
        output_format=CandidateBatch,
    )
    batch = response.parsed_output
    if batch is None:
        raise RuntimeError("model returned no parseable candidate batch")

    ids = set(existing_ids)
    seen_questions = {q.strip() for q in existing_questions}
    items: list[EvalItem] = []
    for candidate in batch.items:
        question = candidate.question.strip()
        if question in seen_questions:
            continue
        seen_questions.add(question)
        item_id = next_id(task, category, ids)
        ids.add(item_id)
        items.append(
            EvalItem(
                id=item_id,
                task=task,
                category=category,
                question=candidate.question,
                choices=candidate.choices,
                answer_index=candidate.answer_index,
                explanation=candidate.explanation,
                script="latin",
                source=f"generated-claude-{model}",
                verified=False,
            )
        )
    return items
