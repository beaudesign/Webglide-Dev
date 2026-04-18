import pytest

from cuga_arc3.config import Settings


def test_settings_reads_arc_api_key_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ARC_API_KEY", "test-api-key")

    settings = Settings.from_env()

    assert settings.arc_api_key == "test-api-key"
    assert settings.default_stage == "S0"


def test_settings_rejects_missing_arc_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ARC_API_KEY", raising=False)

    with pytest.raises(ValueError, match="ARC_API_KEY is required"):
        Settings.from_env()


def test_from_env_optional_returns_none_when_key_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ARC_API_KEY", raising=False)

    assert Settings.from_env_optional() is None


def test_from_env_optional_returns_settings_when_key_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ARC_API_KEY", "test-api-key")

    settings = Settings.from_env_optional()

    assert settings is not None
    assert settings.arc_api_key == "test-api-key"


def test_settings_reads_max_steps_per_game(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ARC_API_KEY", "k")
    monkeypatch.setenv("ARC_MAX_STEPS_PER_GAME", "77")

    settings = Settings.from_env()

    assert settings.max_steps_per_game == 77
