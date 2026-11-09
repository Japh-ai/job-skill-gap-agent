from typing import Literal
from pydantic import BaseModel, Field

SKILL_FORMAT = (
    "Use short standard names, one skill per item, e.g. 'Python', 'RAG', 'AWS', 'Prompt engineering'. "
    "Only technical skills: no spoken languages, soft skills or years of experience."
)


class JobPost(BaseModel):
    """A job post, extracted into structured fields."""

    company: str = Field(description="Company name")
    role: str = Field(description="Job title, as written in the post.")
    location: str | None = Field(
        description="City and/or country, or null if not given"
    )
    work_mode: Literal["remote", "hybrid", "onsite", "unknown"] = Field(
        description="Where the work happens, as stated in the post"
    )
    seniority: Literal["intern", "junior", "mid", "senior", "lead", "unknown"] = Field(
        description="Seniority level; 'unknown' if the post doesn't say"
    )
    skills_required: list[str] = Field(
        description="Technical skills the post says are required or must-have. "
        + SKILL_FORMAT
    )
    skills_nice_to_have: list[str] = Field(
        description="Technical skills the post calls a plus, preferred, bonus or nice to have. "
        + SKILL_FORMAT
    )
    salary_min: int | None = Field(
        description="Lowest salary in the range as a plain number, or null"
    )
    salary_max: int | None = Field(
        description="Highest salary in the range as a plain number, or null"
    )
    salary_currency: Literal["USD", "EUR", "MXN", "CZK", "other"] | None = Field(
        description="Currency code, 'other' for any currency not listed, or null if no salary is given"
    )
    salary_period: Literal["year", "month", "week", "day", "hour"] | None = Field(
        description="Salary period, or null if no salary is given"
    )


class SkillRating(BaseModel):
    """How well the user's notes show they know one skill."""
    evidence_note: str | None = Field(description="Title of the note that proves the rating, or null for NOT YET")
    reason: str = Field(description="One short sentence explaining the rating.")
    rating: Literal["HANDS-ON","STUDYING", "NOT YET"] = Field(description="Rating from the rubric")

