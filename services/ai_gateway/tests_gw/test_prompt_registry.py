"""Tests for PromptVersionRegistry."""

from __future__ import annotations


class TestPromptVersionRegistry:
    def test_default_versions(self, registry):
        versions = registry.get_versions()
        assert versions["prompt_version"] == "0.1.0"
        assert versions["model_version"] == "mock"
        assert "updated_at" in versions

    def test_update_prompt_version(self, registry):
        registry.update_prompt_version("1.0.0")
        versions = registry.get_versions()
        assert versions["prompt_version"] == "1.0.0"
        assert versions["model_version"] == "mock"

    def test_update_model_version(self, registry):
        registry.update_model_version("gpt-4")
        versions = registry.get_versions()
        assert versions["prompt_version"] == "0.1.0"
        assert versions["model_version"] == "gpt-4"

    def test_update_both_versions(self, registry):
        registry.update_prompt_version("2.0.0")
        registry.update_model_version("claude-3")
        versions = registry.get_versions()
        assert versions["prompt_version"] == "2.0.0"
        assert versions["model_version"] == "claude-3"

    def test_updated_at_changes_on_update(self, registry):
        initial = registry.get_versions()["updated_at"]
        registry.update_prompt_version("1.0.0")
        updated = registry.get_versions()["updated_at"]
        assert updated != initial
