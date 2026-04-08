import asyncio
import json
from pathlib import Path

from spss_mcp import server
from spss_mcp.spss_runner import run_syntax


def test_reproduction_manifest_structure():
    manifest_path = Path("F:/MCP/spss-mcp/tests/fixtures/reproduction_manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert len(manifest) == 10
    for case in manifest:
        assert "id" in case
        assert "file_path" in case
        assert "params" in case
        assert "execution_context" in case
        assert "expected_success" in case
        assert "required_output_markers" in case
        assert case.get("tool") or case.get("syntax_kind")


def test_reproduction_manifest_cases_execute_successfully():
    manifest_path = Path("F:/MCP/spss-mcp/tests/fixtures/reproduction_manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    for case in manifest:
        if case.get("syntax_kind") == "raw":
            result = asyncio.run(
                run_syntax(
                    case["params"]["syntax"],
                    data_file=case["file_path"],
                    filter_variable=case["execution_context"].get("filter_variable"),
                    select_if=case["execution_context"].get("select_if"),
                )
            )
            rendered = result.get("output_markdown") or ""
            if result.get("error"):
                rendered = f"Error: {result['error']}\n\n{rendered}"
        else:
            tool = getattr(server, case["tool"])
            rendered = asyncio.run(tool(file_path=case["file_path"], **case["params"]))

        assert rendered.startswith("Error:") is False, case["id"] + " failed with output:\n" + rendered[:4000]
        for marker in case["required_output_markers"]:
            assert marker in rendered, f"{case['id']} missing marker: {marker}\n{rendered[:4000]}"
