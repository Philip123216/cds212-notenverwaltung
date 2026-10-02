from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    database_url: str | None
    version: str
    log_level: str

    @classmethod
    def from_env(cls) -> Config:
        return cls(
            database_url=os.environ.get("DATABASE_URL") or None,
            version=os.environ.get("APP_VERSION", "0.0.0-dev"),
            log_level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        )
