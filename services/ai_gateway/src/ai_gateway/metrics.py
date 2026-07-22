from __future__ import annotations

from typing import Any


class RequestMetrics:
    """Collects request metrics."""

    def __init__(self) -> None:
        self.total_requests: int = 0
        self.successful_requests: int = 0
        self.failed_requests: int = 0
        self.fallback_requests: int = 0
        self.total_latency_ms: float = 0.0

    def record_request(self, latency_ms: float, success: bool, used_fallback: bool = False) -> None:
        self.total_requests += 1
        self.total_latency_ms += latency_ms
        if used_fallback:
            self.fallback_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

    def get_summary(self) -> dict[str, Any]:
        avg_latency = self.total_latency_ms / max(1, self.total_requests)
        return {
            "total": self.total_requests,
            "success": self.successful_requests,
            "failed": self.failed_requests,
            "fallback": self.fallback_requests,
            "avg_latency_ms": round(avg_latency, 2),
        }

    def reset(self) -> None:
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.fallback_requests = 0
        self.total_latency_ms = 0.0
