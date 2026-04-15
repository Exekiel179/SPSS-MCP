"""
Command-line interface for SPSS MCP server.
"""

import argparse
import json
import sys

from spss_mcp.claude_config import (
    build_mcp_server_config,
    configure_claude_settings,
    get_default_settings_path,
    get_entrypoint_config,
)


def main():
    parser = argparse.ArgumentParser(description="SPSS Model Context Protocol server")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # serve
    serve_parser = subparsers.add_parser("serve", help="Run the MCP server")
    serve_parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http", "sse"],
        default="stdio",
        help="Transport to use (default: stdio)",
    )
    serve_parser.add_argument("--host", default="localhost")
    serve_parser.add_argument("--port", type=int, default=8000)

    # status
    subparsers.add_parser("status", help="Show SPSS detection results and exit")

    # version
    subparsers.add_parser("version", help="Print version information")

    # setup-info
    subparsers.add_parser("setup-info", help="Show Claude Code MCP config snippet")

    # configure-claude
    configure_parser = subparsers.add_parser(
        "configure-claude",
        help="Detect SPSS and automatically update Claude Code settings",
    )
    configure_parser.add_argument(
        "--settings-file",
        help="Explicit Claude Code settings file path to update",
    )
    configure_parser.add_argument(
        "--local",
        action="store_true",
        help="Write to settings.local.json instead of settings.json",
    )

    args = parser.parse_args()

    if not args.command:
        args.command = "serve"
        args.transport = "stdio"

    if args.command == "version":
        from spss_mcp._version import __version__
        print(f"SPSS MCP v{__version__}")
        sys.exit(0)

    elif args.command == "status":
        from spss_mcp.config import detect_capabilities
        caps = detect_capabilities()
        print("=== SPSS MCP Capability Status ===")
        print(f"pyreadstat : {'OK v' + caps['pyreadstat_version'] if caps['pyreadstat'] else 'NOT FOUND  (pip install pyreadstat)'}")
        print(f"pandas     : {'OK v' + caps['pandas_version'] if caps['pandas_version'] else 'NOT FOUND'}")
        if caps["spss"]:
            print(f"SPSS batch : OK — {caps['spss_path']}")
        else:
            print("SPSS batch : NOT FOUND")
            print("  Set SPSS_INSTALL_PATH env var to the SPSS installation directory.")
        sys.exit(0)

    elif args.command == "setup-info":
        executable_command, executable_args = get_entrypoint_config()

        from spss_mcp._version import __version__
        snippet = {"mcpServers": {"spss": build_mcp_server_config()}}

        print(f"=== SPSS MCP v{__version__} Setup Info ===")
        print(f"Command: {executable_command}")
        print(f"Args: {json.dumps(executable_args)}")
        print()
        print("Add to your Claude Code MCP settings:")
        print(json.dumps(snippet, indent=2))
        sys.exit(0)

    elif args.command == "configure-claude":
        settings_path = None
        if args.settings_file:
            from pathlib import Path

            settings_path = Path(args.settings_file).expanduser()
        elif args.local:
            settings_path = get_default_settings_path(local=True)

        result = configure_claude_settings(settings_path, local=args.local)
        print("=== Claude Code configuration updated ===")
        print(f"Status: {result['status']}")
        print(f"Settings: {result['settings_path']}")
        if result["backup_path"]:
            print(f"Backup: {result['backup_path']}")
        print()
        print("Configured MCP entry:")
        print(json.dumps({"spss": result["entry"]}, indent=2))
        print()
        print("Restart Claude Code to load the updated MCP server.")
        sys.exit(0)

    elif args.command == "serve":
        from spss_mcp.server import mcp

        transport = getattr(args, "transport", "stdio")
        if transport == "stdio":
            mcp.run(transport="stdio")
        elif transport == "streamable-http":
            mcp.run(transport="streamable-http", host=args.host, port=args.port)
        elif transport == "sse":
            import warnings
            warnings.warn(
                "SSE transport is deprecated. Use streamable-http instead.",
                UserWarning,
            )
            mcp.run(transport="sse", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
