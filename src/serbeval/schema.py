"""Item schema shared by datasets, generation, and validation."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

ANSWER_LETTERS = "ABCD"

Script = Literal["cyrillic", "latin"]


class EvalItem(BaseModel):
    id: str
    task: str
    category: str
    question: str
    choices: list[str] = Field(min_length=4, max_length=4)
    answer_index: int = Field(ge=0, le=3)
    explanation: str
    script: Script
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
