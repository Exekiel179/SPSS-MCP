import asyncio

from spss_mcp import server


def test_list_supported_methods_contains_registry_tools():
    output = asyncio.run(server.spss_list_supported_methods())
    assert "spss_logistic_regression" in output
    assert "registry-backed" in output


def test_get_method_support_reports_metadata():
    output = asyncio.run(server.spss_get_method_support("spss_mixed"))
    assert "MIXED" in output
    assert "registry-backed" in output


def test_format_run_result_keeps_error_with_output():
    rendered = server._format_run_result({"error": "boom", "output_markdown": "details"})
    assert rendered.startswith("Error: boom")
    assert "details" in rendered


def test_registered_method_tool_uses_runner_without_duplicate_get_file(monkeypatch):
    async def fake_run_syntax(syntax, data_file=None, save_viewer_output=True, save_syntax_file=True, filter_variable=None, select_if=None):
        return {
            "error": None,
            "output_markdown": syntax,
            "viewer_output_file": None,
            "syntax_file": None,
            "viewer_error": None,
        }

    monkeypatch.setattr(server, "_require_spss", lambda ctx: None)
    import spss_mcp.spss_runner as runner
    monkeypatch.setattr(runner, "run_syntax", fake_run_syntax)

    output = asyncio.run(
        server.spss_logistic_regression(
            file_path="F:/data/example.sav",
            dependent="outcome",
            predictors=["x1", "x2"],
        )
    )
    assert "LOGISTIC REGRESSION VARIABLES outcome" in output
    assert "/METHOD=ENTER x1 x2" in output
    assert output.count("GET FILE='F:/data/example.sav'.") == 1


def test_run_syntax_tool_passes_case_selection(monkeypatch):
    captured = {}

    async def fake_run_syntax(syntax, data_file=None, save_viewer_output=True, save_syntax_file=True, filter_variable=None, select_if=None):
        captured["filter_variable"] = filter_variable
        captured["select_if"] = select_if
        return {
            "error": None,
            "output_markdown": syntax,
            "viewer_output_file": None,
            "syntax_file": None,
            "viewer_error": None,
        }

    monkeypatch.setattr(server, "_require_spss", lambda ctx: None)
    import spss_mcp.spss_runner as runner
    monkeypatch.setattr(runner, "run_syntax", fake_run_syntax)

    asyncio.run(
        server.spss_run_syntax(
            syntax="DESCRIPTIVES VARIABLES=x.",
            data_file="F:/data/example.sav",
            filter_variable="keep_flag",
        )
    )
    assert captured["filter_variable"] == "keep_flag"
    assert captured["select_if"] is None
