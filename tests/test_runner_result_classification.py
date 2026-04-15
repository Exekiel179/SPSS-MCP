from spss_mcp.spss_runner import (
    _build_execution_syntax,
    _build_selection_syntax,
    _extract_syntax_issue_warnings,
)


def test_build_execution_syntax_does_not_duplicate_get_file():
    syntax = "GET FILE='F:/data/example.sav'.\nDESCRIPTIVES VARIABLES=x."
    rendered = _build_execution_syntax(syntax, data_file="F:/data/example.sav")
    assert rendered.count("GET FILE='F:/data/example.sav'.") == 1


def test_build_execution_syntax_injects_get_file_when_missing():
    rendered = _build_execution_syntax("DESCRIPTIVES VARIABLES=x.", data_file="F:/data/example.sav")
    assert rendered.startswith("GET FILE='F:/data/example.sav'.")


def test_selection_syntax_is_empty_without_case_selection():
    assert _build_selection_syntax() == ""


def test_selection_syntax_is_inserted_after_get_file():
    execution = _build_execution_syntax("DESCRIPTIVES VARIABLES=x.", data_file="F:/data/example.sav")
    selection = _build_selection_syntax(select_if="x > 1")
    combined = execution.replace("\n", "\n" + selection, 1)
    assert combined.startswith("GET FILE='F:/data/example.sav'.\nUSE ALL.")
    assert "SELECT IF (x > 1)." in combined


def test_extract_syntax_issue_warnings_detects_invalid_keyword_messages():
    raw_output = """
Warnings

 The SHOW command contains an invalid keyword: TIME.
"""
    assert _extract_syntax_issue_warnings(raw_output) == [
        "The SHOW command contains an invalid keyword: TIME."
    ]
