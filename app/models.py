from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class Grade:
    id: int
    course: str
    grade: float
    ects: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ValidationError(ValueError):
    """Wird geworfen, wenn die Noten- oder ECTS-Eingabe ungültig ist."""


MAX_COURSE_LENGTH = 100
MIN_GRADE = 1.0
MAX_GRADE = 6.0


def validate_course(raw: Any) -> str:
    if not isinstance(raw, str):
        raise ValidationError("course must be a string")
    course = raw.strip()
    if not course:
        raise ValidationError("course must not be empty")
    if len(course) > MAX_COURSE_LENGTH:
        raise ValidationError(f"course must be at most {MAX_COURSE_LENGTH} characters")
    return course


def validate_grade_value(raw: Any) -> float:
    if not isinstance(raw, (int, float)) or isinstance(raw, bool):
        raise ValidationError("grade must be a number")
    val = float(raw)
    if val < MIN_GRADE or val > MAX_GRADE:
        raise ValidationError(f"grade must be between {MIN_GRADE} and {MAX_GRADE}")
    return round(val, 2)


def validate_ects(raw: Any) -> int:
    if not isinstance(raw, int) or isinstance(raw, bool):
        raise ValidationError("ects must be an integer")
    if raw <= 0:
        raise ValidationError("ects must be greater than 0")
    return raw
