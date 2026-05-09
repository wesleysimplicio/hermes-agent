"""Edge-case tests for hermes_time fallback when timezone resolution fails."""
import logging
from pathlib import Path

import pytest
import yaml

import hermes_time


@pytest.fixture(autouse=True)
def _reset_cache(monkeypatch):
    monkeypatch.setattr(hermes_time, "_cached_tz", None, raising=False)
    monkeypatch.setattr(hermes_time, "_cached_tz_name", None, raising=False)
    monkeypatch.setattr(hermes_time, "_cache_resolved", False, raising=False)


class TestInvalidTimezoneFallback:
    def test_config_yaml_invalid_tz_falls_back_to_local(self, tmp_path, monkeypatch, caplog):
        config = tmp_path / "config.yaml"
        config.write_text(yaml.dump({"timezone": "Bogus/Zone"}))
        monkeypatch.setattr(hermes_time, "get_config_path", lambda: config)
        monkeypatch.delenv("HERMES_TIMEZONE", raising=False)
        with caplog.at_level(logging.WARNING, logger="hermes_time"):
            result = hermes_time.now()
        assert result.tzinfo is not None
        assert "Invalid timezone" in caplog.text
        assert "Bogus/Zone" in caplog.text

    def test_whitespace_only_env_uses_local(self, monkeypatch):
        monkeypatch.setenv("HERMES_TIMEZONE", "    ")
        monkeypatch.setattr(hermes_time, "get_config_path", lambda: Path("/nonexistent/config.yaml"))
        result = hermes_time.now()
        assert result.tzinfo is not None
        assert hermes_time.get_timezone() is None

    def test_invalid_tz_caches_none(self, monkeypatch):
        monkeypatch.setenv("HERMES_TIMEZONE", "Not/Real/Zone")
        first = hermes_time.get_timezone()
        second = hermes_time.get_timezone()
        assert first is None
        assert second is None
        assert hermes_time._cache_resolved is True

    def test_config_yaml_missing_timezone_key_uses_local(self, tmp_path, monkeypatch):
        config = tmp_path / "config.yaml"
        config.write_text(yaml.dump({"other_setting": "value"}))
        monkeypatch.setattr(hermes_time, "get_config_path", lambda: config)
        monkeypatch.delenv("HERMES_TIMEZONE", raising=False)
        assert hermes_time.get_timezone() is None

    def test_config_yaml_non_string_tz_uses_local(self, tmp_path, monkeypatch):
        config = tmp_path / "config.yaml"
        config.write_text(yaml.dump({"timezone": 12345}))
        monkeypatch.setattr(hermes_time, "get_config_path", lambda: config)
        monkeypatch.delenv("HERMES_TIMEZONE", raising=False)
        assert hermes_time.get_timezone() is None

    def test_corrupt_config_yaml_uses_local(self, tmp_path, monkeypatch):
        config = tmp_path / "config.yaml"
        config.write_text("::not: valid\nyaml: [unclosed")
        monkeypatch.setattr(hermes_time, "get_config_path", lambda: config)
        monkeypatch.delenv("HERMES_TIMEZONE", raising=False)
        result = hermes_time.now()
        assert result.tzinfo is not None
