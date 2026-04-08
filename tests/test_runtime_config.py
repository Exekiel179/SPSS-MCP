import importlib

from spss_mcp import config


def test_get_timeout_rejects_invalid_values(monkeypatch):
    monkeypatch.setenv("SPSS_TIMEOUT", "abc")
    assert config.get_timeout() == 120

    monkeypatch.setenv("SPSS_TIMEOUT", "0")
    assert config.get_timeout() == 120

    monkeypatch.setenv("SPSS_TIMEOUT", "600")
    assert config.get_timeout() == 600


def test_get_runtime_config_includes_effective_timeout(monkeypatch):
    monkeypatch.setenv("SPSS_TIMEOUT", "321")
    runtime = config.get_runtime_config()
    assert runtime["timeout"] == 321
    assert "temp_dir" in runtime
    assert "results_dir" in runtime
