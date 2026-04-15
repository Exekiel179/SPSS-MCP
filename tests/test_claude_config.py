import json
from pathlib import Path

from spss_mcp import claude_config


def test_configure_claude_settings_creates_new_settings_file(monkeypatch, tmp_path):
    monkeypatch.setattr(
        claude_config,
        "build_mcp_server_config",
        lambda: {
            "type": "stdio",
            "command": "spss-mcp",
            "args": ["serve", "--transport", "stdio"],
            "env": {
                "SPSS_INSTALL_PATH": r"E:\spss",
                "SPSS_TIMEOUT": "300",
            },
        },
    )

    settings_path = tmp_path / "settings.json"
    result = claude_config.configure_claude_settings(settings_path)

    saved = json.loads(settings_path.read_text(encoding="utf-8"))
    assert result["status"] == "created"
    assert result["backup_path"] is None
    assert saved["mcpServers"]["spss"]["type"] == "stdio"
    assert saved["mcpServers"]["spss"]["command"] == "spss-mcp"
    assert saved["mcpServers"]["spss"]["env"]["SPSS_INSTALL_PATH"] == r"E:\spss"


def test_configure_claude_settings_merges_existing_settings(monkeypatch, tmp_path):
    monkeypatch.setattr(
        claude_config,
        "build_mcp_server_config",
        lambda: {
            "type": "stdio",
            "command": "spss-mcp",
            "args": ["serve", "--transport", "stdio"],
            "env": {
                "SPSS_INSTALL_PATH": r"E:\spss",
                "SPSS_TIMEOUT": "300",
            },
        },
    )

    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "model": "claude-opus-4-6-thinking",
                "mcpServers": {
                    "drawio": {"command": "node", "args": ["drawio.js"]},
                    "spss": {"command": "old-command"},
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    result = claude_config.configure_claude_settings(settings_path)
    saved = json.loads(settings_path.read_text(encoding="utf-8"))

    assert result["status"] == "updated"
    assert result["backup_path"] is not None
    assert Path(result["backup_path"]).exists()
    assert saved["model"] == "claude-opus-4-6-thinking"
    assert saved["mcpServers"]["drawio"]["command"] == "node"
    assert saved["mcpServers"]["spss"]["command"] == "spss-mcp"


def test_configure_claude_settings_rejects_non_object_mcp_servers(tmp_path):
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps({"mcpServers": []}),
        encoding="utf-8",
    )

    try:
        claude_config.configure_claude_settings(settings_path)
    except ValueError as exc:
        assert "mcpServers" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid mcpServers")
