from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict


class FileJobStore:
    def __init__(self, root: Path) -> None:
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)

    def create(self, payload: Dict[str, Any]) -> str:
        job_id = str(uuid.uuid4())
        self.save(job_id, payload)
        return job_id

    def save(self, job_id: str, payload: Dict[str, Any]) -> None:
        self._job_path(job_id).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self, job_id: str) -> Dict[str, Any]:
        path = self._job_path(job_id)
        if not path.exists():
            raise KeyError(f"Unknown job_id: {job_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _job_path(self, job_id: str) -> Path:
        return self._root / f"{job_id}.json"
