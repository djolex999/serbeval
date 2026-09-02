"""Item schema shared by datasets, generation, and validation."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

ANSWER_LETTERS = "ABCD"

Script = Literal["cyrillic", "latin"]
# Difficulty of the underlying question, independent of script. Optional: the seed items
# predate it, and a None tier simply drops out of the by-tier breakdowns in `serbeval report`.
Difficulty = Literal["easy", "medium", "hard"]


class EvalItem(BaseModel):
    id: str
    task: str
    category: str
    question: str
    choices: list[str] = Field(min_length=4, max_length=4)
    answer_index: int = Field(ge=0, le=3)
    explanation: str
    script: Script
    difficulty: Difficulty | None = None
    pair_id: str | None = None
    source: str
    verified: bool = False
    license: str = "CC-BY-4.0"

    @field_validator("id", "task", "category", "question", "explanation", "source")
    @classmethod
    def _non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value

    @field_validator("choices")
    @classmethod
    def _unique_choices(cls, choices: list[str]) -> list[str]:
        stripped = [c.strip() for c in choices]
        if any(not c for c in stripped):
            raise ValueError("choices must not be blank")
        if len(set(stripped)) != len(stripped):
            raise ValueError("choices must be unique")
        return choices

    @property
    def answer_letter(self) -> str:
        return ANSWER_LETTERS[self.answer_index]


BLANK = "____"


class ClozeItem(BaseModel):
    """A fill-in-the-blank grammar item, scored by exact match on the produced form.

    Cloze sidesteps the whole distractor-quality problem that MCQ items have: there is
    nothing to eliminate, no 25% chance floor, and no structural giveaway for a model to
    pattern-match. `answers` is a list because Serbian norm has genuinely contested cases
    (ijekavian doublets, tolerated variants) — listing every accepted form keeps such an
    item usable instead of forcing one reading and dropping it.
    """

    id: str
    task: str
    category: str
    question: str
    cue: str
    answers: list[str] = Field(min_length=1)
    explanation: str
    script: Script
    difficulty: Difficulty | None = None
    source: str
    verified: bool = False
    license: str = "CC-BY-4.0"

    @field_validator("id", "task", "category", "cue", "explanation", "source")
    @classmethod
    def _non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value

    @field_validator("question")
    @classmethod
    def _has_blank(cls, value: str) -> str:
        if BLANK not in value:
            raise ValueError(f"question must contain the blank marker {BLANK!r}")
        return value

    @field_validator("answers")
    @classmethod
    def _usable_answers(cls, answers: list[str]) -> list[str]:
        stripped = [a.strip() for a in answers]
        if any(not a for a in stripped):
            raise ValueError("answers must not be blank")
        if len(set(stripped)) != len(stripped):
            raise ValueError("answers must be unique")
        return answers
