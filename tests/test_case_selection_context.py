from spss_mcp.method_validation import CaseSelectionParams
from spss_mcp.spss_runner import _build_selection_syntax
import pytest


def test_case_selection_params_reject_conflicting_options():
    with pytest.raises(ValueError):
        CaseSelectionParams(filter_variable="keep", select_if="x > 1")


def test_case_selection_params_require_one_option():
    with pytest.raises(ValueError):
        CaseSelectionParams()


def test_build_selection_syntax_for_filter_variable():
    syntax = _build_selection_syntax(filter_variable="keep_flag")
    assert "FILTER BY keep_flag." in syntax
    assert "USE ALL." in syntax


def test_build_selection_syntax_for_select_if():
    syntax = _build_selection_syntax(select_if="score > 80")
    assert "TEMPORARY." in syntax
    assert "SELECT IF (score > 80)." in syntax
