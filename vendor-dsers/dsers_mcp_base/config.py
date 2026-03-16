"""DSers MCP configuration — supports test / production via env vars."""

from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass

_PROD_URL = "https://bff-api-gw.dsers.com"
_TEST_URL = "https://bff-api-gw-test.dsers.com"


@dataclass(frozen=True)
class DSersConfig:
    base_url: str
    email: str
    password: str
    session_file: Path

    @classmethod
    def from_env(cls) -> DSersConfig:
        env = os.getenv("DSERS_ENV", "production").lower()
        base_url = os.getenv("DSERS_BASE_URL") or (_TEST_URL if env == "test" else _PROD_URL)
        email = os.getenv("DSERS_EMAIL", "")
        password = os.getenv("DSERS_PASSWORD", "")

        default_session = Path(os.getenv("DSERS_SESSION_FILE", ""))
        if not default_session.name:
            default_session = Path(__file__).resolve().parent.parent / ".session.json"

        return cls(base_url=base_url, email=email, password=password, session_file=default_session)

    @property
    def enabled_modules(self) -> set[str]:
        raw = os.getenv("DSERS_MODULES", "")
        if not raw:
            return {"account", "product", "order", "logistics", "settings"}
        return {m.strip().lower() for m in raw.split(",") if m.strip()}
