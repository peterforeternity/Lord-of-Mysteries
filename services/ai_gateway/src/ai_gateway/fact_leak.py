from __future__ import annotations

import json
from pathlib import Path


class FactLeakValidator:
    """Validates that AI responses don't leak secret facts."""

    def __init__(self, secrets_path: Path | None = None) -> None:
        self._core_secret_ids: list[str] = []
        if secrets_path and secrets_path.exists():
            with open(secrets_path) as f:
                facts = json.load(f)
                self._core_secret_ids = [
                    f["fact_id"] for f in facts if f.get("secrecy") == "core_secret"
                ]

    def check_leak(self, utterance: str, referenced_claim_ids: list[str]) -> list[str]:
        flags: list[str] = []
        # Check if utterance mentions any core secret fact IDs
        for secret_id in self._core_secret_ids:
            if secret_id in utterance:
                flags.append(f"possible_leak:{secret_id}")
        return flags

    def get_secret_count(self) -> int:
        return len(self._core_secret_ids)
