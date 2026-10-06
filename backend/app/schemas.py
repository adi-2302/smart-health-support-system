import re
import datetime as dt
from pydantic import BaseModel, Field, field_validator

from .questionnaire import QUESTION_KEYS, ALLOWED_VALUES

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str
    password: str = Field(min_length=8, max_length=128)
    age: int | None = Field(default=None, ge=15, le=60)
    gender: str | None = None
    course: str | None = None
    year: str | None = None
    living_conditions: str | None = None
    mental_health_history: bool = False
    exam_date: dt.date
    exam_label: str | None = None

    @field_validator("email")
    @classmethod
    def valid_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not _EMAIL.match(v):
            raise ValueError("Invalid email address")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


class ExamUpdate(BaseModel):
    exam_date: dt.date
    exam_label: str | None = None


class CheckinRequest(BaseModel):
    answers: dict[str, int]
    date: dt.date | None = None  # only honoured when ALLOW_BACKDATED_CHECKINS is enabled

    @field_validator("answers")
    @classmethod
    def validate_answers(cls, v: dict[str, int]) -> dict[str, int]:
        missing = [k for k in QUESTION_KEYS if k not in v]
        extra = [k for k in v if k not in QUESTION_KEYS]
        if missing or extra:
            raise ValueError(f"answers must contain exactly the {len(QUESTION_KEYS)} questionnaire keys "
                             f"(missing={missing}, unexpected={extra})")
        bad = {k: val for k, val in v.items() if val not in ALLOWED_VALUES[k]}
        if bad:
            raise ValueError(f"invalid option values: {bad}")
        return v
