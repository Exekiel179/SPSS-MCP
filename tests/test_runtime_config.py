import importlib

from spss_mcp import config


def test_get_timeout_rejects_invalid_values(monkeypatch):
    monkeypatch.setenv("SPSS_TIMEOUT", "abc")
    assert config.get_timeout() == 120

    monkeypatch.setenv("SPSS_TIMEOUT", "0")
    assert config.get_timeout() == 120

    monkeypatch.setenv("SPSS_TIMEOUT", "600")
    assert config.get_timeout() == 600


def test_get_startup_timeout_rejects_invalid_values(monkeypatch):
    monkeypatch.setenv("SPSS_STARTUP_TIMEOUT", "abc")
    assert config.get_startup_timeout() == 300

    monkeypatch.setenv("SPSS_STARTUP_TIMEOUT", "0")
    assert config.get_startup_timeout() == 300

    monkeypatch.setenv("SPSS_STARTUP_TIMEOUT", "900")
    assert config.get_startup_timeout() == 900


def test_get_runtime_config_includes_effective_timeout(monkeypatch):
    monkeypatch.setenv("SPSS_TIMEOUT", "321")
    monkeypatch.setenv("SPSS_STARTUP_TIMEOUT", "654")
    runtime = config.get_runtime_config()
    assert runtime["timeout"] == 321
    assert runtime["startup_timeout"] == 654
    assert "temp_dir" in runtime
    assert "results_dir" in runtime
