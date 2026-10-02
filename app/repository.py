from __future__ import annotations

import logging
import threading
from typing import Protocol

from app.config import Config
from app.models import Grade

log = logging.getLogger(__name__)


class GradeRepository(Protocol):
    def list(self) -> list[Grade]: ...
    def get(self, grade_id: int) -> Grade | None: ...
    def add(self, course: str, grade: float, ects: int) -> Grade: ...
    def delete(self, grade_id: int) -> bool: ...
    def healthy(self) -> bool: ...


class InMemoryGradeRepository:
    def __init__(self) -> None:
        self._grades: dict[int, Grade] = {}
        self._next_id = 1
        self._lock = threading.Lock()

    def list(self) -> list[Grade]:
        with self._lock:
            return sorted(self._grades.values(), key=lambda g: g.id)

    def get(self, grade_id: int) -> Grade | None:
        with self._lock:
            return self._grades.get(grade_id)

    def add(self, course: str, grade: float, ects: int) -> Grade:
        with self._lock:
            entry = Grade(id=self._next_id, course=course, grade=grade, ects=ects)
            self._grades[entry.id] = entry
            self._next_id += 1
            return entry

    def delete(self, grade_id: int) -> bool:
        with self._lock:
            return self._grades.pop(grade_id, None) is not None

    def healthy(self) -> bool:
        return True


def create_repository(config: Config) -> GradeRepository:
    if config.database_url:
        log.info("using database: %s", config.database_url)
    log.warning("no DATABASE_URL set, using in-memory grade repository")
    return InMemoryGradeRepository()
