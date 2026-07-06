from __future__ import annotations

import pytest

from devtrack_ai_ai.gemini_service import GeminiConfig


pytestmark = pytest.mark.integration


def test_gemini_config_reads_environment_without_exposing_key(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test-model")

    config = GeminiConfig.from_env()

    assert config.api_key == "test-gemini-key"
    assert config.model == "gemini-test-model"
    assert "test-gemini-key" not in repr(config)
