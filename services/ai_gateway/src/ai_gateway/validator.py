from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from .models import DialogueResponse


class StructuredOutputValidator:
    """Validates structured LLM output."""

    def validate(self, raw_output: str) -> DialogueResponse | None:
        try:
            data = json.loads(raw_output)
            return DialogueResponse(**data)
        except (json.JSONDecodeError, ValidationError, TypeError):
            return None

    def validate_dict(self, data: dict[str, Any]) -> DialogueResponse | None:
        try:
            return DialogueResponse(**data)
        except ValidationError:
            return None
