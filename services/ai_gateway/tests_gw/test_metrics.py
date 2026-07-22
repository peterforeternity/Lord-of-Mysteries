"""Tests for RequestMetrics."""

from __future__ import annotations


class TestRequestMetrics:
    def test_initial_state(self, metrics):
        summary = metrics.get_summary()
        assert summary["total"] == 0
        assert summary["success"] == 0
        assert summary["failed"] == 0
        assert summary["fallback"] == 0
        assert summary["avg_latency_ms"] == 0.0

    def test_record_success(self, metrics):
        metrics.record_request(100.0, True)
        summary = metrics.get_summary()
        assert summary["total"] == 1
        assert summary["success"] == 1
        assert summary["failed"] == 0
        assert summary["fallback"] == 0

    def test_record_failure(self, metrics):
        metrics.record_request(50.0, False)
        summary = metrics.get_summary()
        assert summary["total"] == 1
        assert summary["success"] == 0
        assert summary["failed"] == 1

    def test_record_fallback(self, metrics):
        metrics.record_request(200.0, False, used_fallback=True)
        summary = metrics.get_summary()
        assert summary["total"] == 1
        assert summary["success"] == 0
        assert summary["failed"] == 1
        assert summary["fallback"] == 1

    def test_avg_latency_calculation(self, metrics):
        metrics.record_request(100.0, True)
        metrics.record_request(200.0, True)
        summary = metrics.get_summary()
        assert summary["avg_latency_ms"] == 150.0

    def test_avg_latency_no_requests(self, metrics):
        """No requests should give 0 avg latency."""
        summary = metrics.get_summary()
        assert summary["avg_latency_ms"] == 0.0

    def test_reset(self, metrics):
        metrics.record_request(100.0, True)
        metrics.record_request(50.0, False, used_fallback=True)
        metrics.reset()
        summary = metrics.get_summary()
        assert summary["total"] == 0
        assert summary["success"] == 0
        assert summary["failed"] == 0
        assert summary["fallback"] == 0
        assert summary["avg_latency_ms"] == 0.0

    def test_multiple_requests_summary(self, metrics):
        """Multiple requests of different types produce correct summary."""
        metrics.record_request(100.0, True)  # success
        metrics.record_request(50.0, True)  # success
        metrics.record_request(200.0, False)  # failed, no fallback
        metrics.record_request(150.0, False, used_fallback=True)  # failed, fallback
        summary = metrics.get_summary()
        assert summary["total"] == 4
        assert summary["success"] == 2
        assert summary["failed"] == 2
        assert summary["fallback"] == 1
        # Avg = (100 + 50 + 200 + 150) / 4 = 500 / 4 = 125
        assert summary["avg_latency_ms"] == 125.0

    def test_latency_rounding(self, metrics):
        """Latency should be rounded to 2 decimal places."""
        metrics.record_request(100.33333, True)
        summary = metrics.get_summary()
        assert summary["avg_latency_ms"] == 100.33
