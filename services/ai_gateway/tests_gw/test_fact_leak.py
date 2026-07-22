"""Tests for FactLeakValidator."""

from __future__ import annotations

import json

from ai_gateway.fact_leak import FactLeakValidator


class TestFactLeakValidator:
    def test_check_leak_no_leak(self, fact_leak):
        """Utterance not mentioning secret IDs should have no flags."""
        flags = fact_leak.check_leak("Hello, how are you?", [])
        assert flags == []

    def test_check_leak_with_leak(self, fact_leak):
        """Utterance mentioning a core secret ID should be flagged."""
        flags = fact_leak.check_leak("I know about fact_secret_1", ["claim_npc1_secret"])
        assert "possible_leak:fact_secret_1" in flags

    def test_check_leak_multiple_leaks(self, fact_leak):
        """Multiple secret references should generate multiple flags."""
        flags = fact_leak.check_leak("fact_secret_1 and fact_secret_2 are both here", [])
        # Only fact_secret_1 exists in the fixture data
        assert "possible_leak:fact_secret_1" in flags
        assert len(flags) == 1

    def test_check_leak_referenced_claims_no_leak(self, fact_leak):
        """Referenced claims alone should not trigger leaks."""
        flags = fact_leak.check_leak("I know something", ["claim_npc1_secret"])
        assert flags == []

    def test_get_secret_count(self, fact_leak):
        count = fact_leak.get_secret_count()
        assert count == 1  # Only fact_secret_1 has secrecy="core_secret"

    def test_no_secrets_file(self, temp_dir):
        """Validator without a secrets file should have zero secrets."""
        no_secrets_path = temp_dir / "nonexistent.json"
        validator = FactLeakValidator(no_secrets_path)
        assert validator.get_secret_count() == 0
        flags = validator.check_leak("fact_secret_1", [])
        assert flags == []

    def test_empty_secrets_file(self, temp_dir):
        """Empty secrets file should result in zero secrets."""
        empty_path = temp_dir / "empty.json"
        with open(empty_path, "w") as f:
            json.dump([], f)
        validator = FactLeakValidator(empty_path)
        assert validator.get_secret_count() == 0
        flags = validator.check_leak("anything", [])
        assert flags == []

    def test_check_leak_empty_utterance(self, fact_leak):
        flags = fact_leak.check_leak("", [])
        assert flags == []
