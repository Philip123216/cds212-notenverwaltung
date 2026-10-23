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


class PostgresGradeRepository:
    """PostgreSQL-Backend für den Container- und Produktionsbetrieb."""

    def __init__(self, dsn: str) -> None:
        import psycopg
        from psycopg_pool import ConnectionPool

        self._psycopg = psycopg
        self._pool = ConnectionPool(dsn, min_size=1, max_size=5, open=True)
        self._create_schema()

    def _create_schema(self) -> None:
        with self._pool.connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS grades (
                    id      SERIAL PRIMARY KEY,
                    course  TEXT NOT NULL,
                    grade   NUMERIC(3, 2) NOT NULL,
                    ects    INTEGER NOT NULL
                )
                """
            )

    def list(self) -> list[Grade]:
        with self._pool.connection() as conn:
            rows = conn.execute("SELECT id, course, grade, ects FROM grades ORDER BY id").fetchall()
        return [Grade(r[0], r[1], float(r[2]), int(r[3])) for r in rows]

    def get(self, grade_id: int) -> Grade | None:
        with self._pool.connection() as conn:
            row = conn.execute(
                "SELECT id, course, grade, ects FROM grades WHERE id = %s", (grade_id,)
            ).fetchone()
        return Grade(row[0], row[1], float(row[2]), int(row[3])) if row else None

    def add(self, course: str, grade: float, ects: int) -> Grade:
        with self._pool.connection() as conn:
            row = conn.execute(
                """
                INSERT INTO grades (course, grade, ects)
                VALUES (%s, %s, %s)
                RETURNING id, course, grade, ects
                """,
                (course, grade, ects),
            ).fetchone()
        return Grade(row[0], row[1], float(row[2]), int(row[3]))

    def delete(self, grade_id: int) -> bool:
        with self._pool.connection() as conn:
            res = conn.execute("DELETE FROM grades WHERE id = %s", (grade_id,))
        return res.rowcount > 0

    def healthy(self) -> bool:
        try:
            with self._pool.connection() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception:
            log.exception("Database health check failed")
            return False


def create_repository(config: Config) -> GradeRepository:
    if config.database_url:
        log.info("Verwende PostgreSQL-Repository: %s", config.database_url)
        return PostgresGradeRepository(config.database_url)
    log.warning("Keine DATABASE_URL gesetzt -> verwende In-Memory-Repository")
    return InMemoryGradeRepository()
