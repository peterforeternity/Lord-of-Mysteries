from __future__ import annotations

from datetime import UTC, datetime


class PromptVersionRegistry:
    """Tracks prompt and model versions."""

    def __init__(self) -> None:
        self._prompt_version: str = "0.1.0"
        self._model_version: str = "mock"
        self._updated_at: str = datetime.now(UTC).isoformat()

    def get_versions(self) -> dict[str, str]:
        return {
            "prompt_version": self._prompt_version,
            "model_version": self._model_version,
            "updated_at": self._updated_at,
        }

    def update_prompt_version(self, version: str) -> None:
        self._prompt_version = version
        self._updated_at = datetime.now(UTC).isoformat()

    def update_model_version(self, version: str) -> None:
        self._model_version = version
        self._updated_at = datetime.now(UTC).isoformat()
