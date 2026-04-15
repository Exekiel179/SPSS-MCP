"""
SPSS execution engine using IBM SPSS Statistics XD API.

Submits syntax to the persistent SpssEngine (spss_engine.py), which keeps a
single SPSS Python3 process alive across all tool calls to avoid repeated
~30-60 s SPSS startup overhead.  OMS commands capture output as readable text.
"""

import asyncio
import re
import uuid
from pathlib import Path
from typing import Optional

from spss_mcp.config import get_results_dir, get_spss_executable, get_spss_python, get_temp_dir, get_timeout
from spss_mcp.output_parser import parse_spss_output


def _build_execution_syntax(
    syntax: str,
    data_file: Optional[str] = None,
) -> str:
    normalized = syntax.lstrip()
    has_data_open = normalized.upper().startswith("GET FILE=")
    data_line = ""
    if data_file and not has_data_open:
        data_file_fwd = data_file.replace("\\", "/")
        data_line = f"GET FILE='{data_file_fwd}'.\n"
    return f"{data_line}{syntax.rstrip()}\n"


def _build_selection_syntax(
    filter_variable: Optional[str] = None,
    select_if: Optional[str] = None,
) -> str:
    if filter_variable and select_if:
        raise ValueError("filter_variable and select_if cannot be used together")

    if not filter_variable and not select_if:
        return ""

    prelude = "USE ALL.\nFILTER OFF.\nWEIGHT OFF.\nSPLIT FILE OFF.\n"
    if filter_variable:
        return prelude + f"FILTER BY {filter_variable}.\n"
    if select_if:
        return prelude + f"TEMPORARY.\nSELECT IF ({select_if}).\n"
    return ""


def _build_full_syntax(
    execution_syntax: str,
    output_file: str,
    viewer_file: str | None = None,
) -> str:
    output_file_fwd = output_file.replace("\\", "/")

    viewer_oms = ""
    viewer_oms_end = ""
    if viewer_file:
        viewer_file_fwd = viewer_file.replace("\\", "/")
        viewer_oms = (
            "OMS /TAG='SPV1' /SELECT ALL\n"
            f"  /DESTINATION FORMAT=SPV OUTFILE='{viewer_file_fwd}'.\n"
        )
        viewer_oms_end = "OMSEND TAG='SPV1'.\n"

    return (
        "OMS /TAG='TXT1' /SELECT ALL\n"
        "  /DESTINATION FORMAT=TEXT\n"
        f"    OUTFILE='{output_file_fwd}'.\n"
        f"{viewer_oms}"
        f"{execution_syntax}"
        "OMSEND TAG='TXT1'.\n"
        f"{viewer_oms_end}"
    )


_SYNTAX_WARNING_PATTERNS = [
    re.compile(r"contains an invalid (?:keyword|subcommand)", re.IGNORECASE),
    re.compile(r"unrecognized (?:keyword|subcommand)", re.IGNORECASE),
    re.compile(r"this command is not valid", re.IGNORECASE),
]


def _extract_syntax_issue_warnings(raw_output: str) -> list[str]:
    warnings: list[str] = []
    for line in raw_output.splitlines():
        text = line.strip()
        if not text:
            continue
        if any(pattern.search(text) for pattern in _SYNTAX_WARNING_PATTERNS):
            warnings.append(text)
    return warnings


async def run_syntax(
    syntax: str,
    data_file: Optional[str] = None,
    save_viewer_output: bool = True,
    save_syntax_file: bool = True,
    filter_variable: Optional[str] = None,
    select_if: Optional[str] = None,
) -> dict:
    """
    Execute SPSS syntax via the persistent engine and return a structured result.

    The engine is started once (on first call or after a crash) and reused for
    all subsequent calls, eliminating the ~30-60 s SPSS startup overhead.

    Returns:
        {
            "success": bool,
            "output_markdown": str,
            "output_raw": str,
            "error": str | None,
            "warnings": list[str],
            ...
        }
    """
    stats_exe = get_spss_executable()
    if not stats_exe:
        return {
            "success": False,
            "timed_out": False,
            "last_error_level": 0,
            "process_returncode": None,
            "parsed_errors": [],
            "parsed_warnings": [],
            "output_markdown": "",
            "output_raw": "",
            "error": (
                "IBM SPSS Statistics is not installed or not found. "
                "Set SPSS_INSTALL_PATH to the SPSS installation directory, "
                "or use spss_check_status to see available capabilities."
            ),
            "warnings": [],
        }

    if not get_spss_python():
        return {
            "success": False,
            "timed_out": False,
            "last_error_level": 0,
            "process_returncode": None,
            "parsed_errors": [],
            "parsed_warnings": [],
            "output_markdown": "",
            "output_raw": "",
            "error": (
                "SPSS Python3 interpreter not found. "
                f"Expected at: {Path(stats_exe).parent / 'Python3' / 'python.exe'}"
            ),
            "warnings": [],
        }

    run_id = uuid.uuid4().hex[:12]
    temp_dir = get_temp_dir()
    results_dir = get_results_dir()
    output_file = temp_dir / f"spss_out_{run_id}.txt"
    syntax_file = results_dir / f"spss_syntax_{run_id}.sps" if save_syntax_file else None
    viewer_file = results_dir / f"spss_viewer_{run_id}.spv" if save_viewer_output else None

    execution_syntax = _build_execution_syntax(syntax=syntax, data_file=data_file)
    selection_syntax = _build_selection_syntax(
        filter_variable=filter_variable, select_if=select_if
    )
    if selection_syntax:
        execution_syntax = execution_syntax.replace("\n", "\n" + selection_syntax, 1)
    full_syntax = _build_full_syntax(
        execution_syntax=execution_syntax,
        output_file=str(output_file),
        viewer_file=str(viewer_file) if viewer_file else None,
    )

    if syntax_file:
        syntax_file.write_text(execution_syntax, encoding="utf-8")

    # ── Submit to persistent engine ───────────────────────────────────────────
    from spss_mcp.spss_engine import get_engine
    engine_result = await get_engine().submit(
        full_syntax=full_syntax,
        output_file=str(output_file),
        viewer_file=str(viewer_file) if viewer_file else None,
    )

    err_level = engine_result.get("err_level", 0)
    fatal_error = engine_result.get("error")
    warn_msg = engine_result.get("warn")
    viewer_ok = engine_result.get("viewer_ok", False)
    output_exists = engine_result.get("output_exists", False)
    timed_out = engine_result.get("timed_out", False)

    # ── Read OMS output file ──────────────────────────────────────────────────
    raw_output = ""
    if output_file.exists():
        raw_output = output_file.read_text(encoding="utf-8-sig", errors="replace")
        try:
            output_file.unlink()
        except OSError:
            pass

    from spss_mcp.output_parser import extract_errors, extract_warnings
    parsed_errors = extract_errors(raw_output) if raw_output else []
    parsed_warnings = extract_warnings(raw_output) if raw_output else []
    syntax_issue_warnings = _extract_syntax_issue_warnings(raw_output) if raw_output else []

    has_fatal_error = err_level >= 3 or bool(fatal_error and not warn_msg)
    has_syntax_issue_warning = bool(syntax_issue_warnings)
    success = (
        output_exists
        and bool(raw_output)
        and not has_fatal_error
        and not timed_out
        and not has_syntax_issue_warning
    )

    markdown = parse_spss_output(raw_output) if raw_output else "_No output produced._"
    warnings: list[str] = list(parsed_warnings)
    for warning in syntax_issue_warnings:
        if warning not in warnings:
            warnings.append(warning)

    if warn_msg and success:
        warnings.append(warn_msg)
        markdown += f"\n\n> **Note:** {warn_msg}"

    viewer_error = None
    if save_viewer_output and viewer_file and not viewer_ok:
        viewer_error = "SPSS did not save viewer output (.spv)."

    error_msg = None
    if not success:
        if timed_out:
            error_msg = f"SPSS job exceeded the {get_timeout()} second timeout. Simplify the analysis or increase SPSS_TIMEOUT."
        elif fatal_error:
            error_msg = fatal_error
        elif err_level >= 3:
            error_msg = "; ".join(parsed_errors) if parsed_errors else f"SPSS reported fatal error level {err_level}"
        elif has_syntax_issue_warning:
            error_msg = "; ".join(syntax_issue_warnings)
        elif not output_exists:
            error_msg = "SPSS ran but produced no output file."
        else:
            error_msg = "SPSS did not confirm successful completion."

    viewer_output_file = str(viewer_file) if viewer_ok and viewer_file and viewer_file.exists() else None
    syntax_output_file = str(syntax_file) if syntax_file and syntax_file.exists() else None

    if viewer_error:
        warnings.append(viewer_error)
        markdown += f"\n\n> **Viewer save note:** {viewer_error}"

    # ── Open .spv in SPSS Statistics Viewer ──────────────────────────────────
    if viewer_output_file and success:
        import os as _os
        import sys as _sys
        try:
            if _sys.platform == "win32":
                _os.startfile(viewer_output_file)
        except Exception:
            pass  # non-fatal: result is still returned even if open fails

    return {
        "success": success,
        "timed_out": timed_out,
        "last_error_level": err_level,
        "process_returncode": 0 if success else 1,
        "parsed_errors": parsed_errors,
        "parsed_warnings": parsed_warnings,
        "output_markdown": markdown,
        "output_raw": raw_output,
        "viewer_output_file": viewer_output_file,
        "syntax_file": syntax_output_file,
        "viewer_error": viewer_error,
        "error": error_msg,
        "warnings": warnings,
    }


def _has_fatal_error(text: str) -> bool:
    import re
    return bool(re.search(r"Error\s*#?\s*\d+", text, re.IGNORECASE))


# ─── High-level analysis syntax builders ──────────────────────────────────────

def build_frequencies_syntax(
    file_path: str,
    variables: list[str],
    statistics: list[str],
) -> str:
    vars_str = " ".join(variables)
    stats_str = " ".join(s.upper() for s in statistics)
    return (
        f"GET FILE='{file_path}'.\n"
        f"FREQUENCIES VARIABLES={vars_str}\n"
        f"  /STATISTICS={stats_str}.\n"
    )


def build_descriptives_syntax(
    file_path: str,
    variables: list[str],
    statistics: list[str],
) -> str:
    vars_str = " ".join(variables)
    stats_str = " ".join(s.upper() for s in statistics)
    return (
        f"GET FILE='{file_path}'.\n"
        f"DESCRIPTIVES VARIABLES={vars_str}\n"
        f"  /STATISTICS={stats_str}.\n"
    )


def build_crosstabs_syntax(
    file_path: str,
    row_variable: str,
    column_variable: str,
    include_chisquare: bool,
    include_row_pct: bool,
    include_col_pct: bool,
) -> str:
    cells = ["COUNT"]
    if include_row_pct:
        cells.append("ROW")
    if include_col_pct:
        cells.append("COLUMN")
    cells_str = " ".join(cells)
    chi_line = "  /STATISTICS=CHISQ\n" if include_chisquare else ""
    return (
        f"GET FILE='{file_path}'.\n"
        f"CROSSTABS\n"
        f"  /TABLES={row_variable} BY {column_variable}\n"
        f"  /CELLS={cells_str}\n"
        f"{chi_line}."
    )


def build_regression_syntax(
    file_path: str,
    dependent: str,
    predictors: list[str],
    method: str,
    include_diagnostics: bool,
) -> str:
    preds_str = " ".join(predictors)
    diag = "COEFF OUTS R ANOVA COLLIN TOL" if include_diagnostics else "COEFF OUTS R ANOVA"
    return (
        f"GET FILE='{file_path}'.\n"
        f"REGRESSION\n"
        f"  /STATISTICS={diag}\n"
        f"  /DEPENDENT {dependent}\n"
        f"  /METHOD={method.upper()} {preds_str}.\n"
    )


def build_t_test_syntax(
    file_path: str,
    test_type: str,
    variables: list[str],
    grouping_variable: str | None,
    test_value: float | None,
) -> str:
    vars_str = " ".join(variables)
    if test_type == "one_sample":
        val = test_value if test_value is not None else 0
        return (
            f"GET FILE='{file_path}'.\n"
            f"T-TEST\n"
            f"  /TESTVAL={val}\n"
            f"  /VARIABLES={vars_str}.\n"
        )
    elif test_type == "independent":
        if not grouping_variable:
            raise ValueError("grouping_variable is required for independent samples t-test")
        return (
            f"GET FILE='{file_path}'.\n"
            f"T-TEST GROUPS={grouping_variable}\n"
            f"  /VARIABLES={vars_str}.\n"
        )
    else:  # paired
        if len(variables) < 2:
            raise ValueError("paired t-test requires exactly 2 variables")
        return (
            f"GET FILE='{file_path}'.\n"
            f"T-TEST PAIRS={variables[0]} WITH {variables[1]} (PAIRED).\n"
        )


def build_anova_syntax(
    file_path: str,
    dependent: str,
    factor: str,
    post_hoc: list[str] | None,
) -> str:
    ph_line = ""
    if post_hoc:
        ph_str = " ".join(p.upper() for p in post_hoc)
        ph_line = f"  /POSTHOC={ph_str}\n"
    return (
        f"GET FILE='{file_path}'.\n"
        f"ONEWAY {dependent} BY {factor}\n"
        f"{ph_line}  /STATISTICS DESCRIPTIVES.\n"
    )


def build_correlations_syntax(
    file_path: str,
    variables: list[str],
    method: str,
    two_tailed: bool,
) -> str:
    vars_str = " ".join(variables)
    sig = "TAILS(2)" if two_tailed else "TAILS(1)"
    if method.lower() == "spearman":
        return (
            f"GET FILE='{file_path}'.\n"
            f"NONPAR CORR\n"
            f"  /VARIABLES={vars_str}\n"
            f"  /PRINT=SPEARMAN {sig}.\n"
        )
    return (
        f"GET FILE='{file_path}'.\n"
        f"CORRELATIONS\n"
        f"  /VARIABLES={vars_str}\n"
        f"  /PRINT={sig}.\n"
    )


def build_factor_syntax(
    file_path: str,
    variables: list[str],
    method: str,
    rotation: str,
    n_factors: int | None,
) -> str:
    vars_str = " ".join(variables)
    extract_line = f"  /EXTRACTION={method}\n"
    if n_factors:
        extract_line += f"  /CRITERIA FACTORS({n_factors})\n"
    rotation_line = ""
    if rotation and rotation.upper() != "NONE":
        rotation_line = f"  /ROTATION={rotation.upper()}\n"
    return (
        f"GET FILE='{file_path}'.\n"
        f"FACTOR\n"
        f"  /VARIABLES={vars_str}\n"
        f"{extract_line}"
        f"{rotation_line}"
        f"  /PRINT=INITIAL EXTRACTION ROTATION.\n"
    )


def build_reliability_syntax(
    file_path: str,
    variables: list[str],
    scale_name: str | None,
    model: str,
) -> str:
    vars_str = " ".join(variables)
    scale = scale_name or "Scale"
    return (
        f"GET FILE='{file_path}'.\n"
        f"RELIABILITY\n"
        f"  /VARIABLES={vars_str}\n"
        f"  /SCALE('{scale}') ALL\n"
        f"  /MODEL={model.upper()}\n"
        f"  /STATISTICS=DESCRIPTIVE SCALE CORR.\n"
    )


def build_compute_scale_syntax(
    file_path: str,
    new_variable: str,
    items: list[str],
    method: str,
    min_valid: int | None,
    reverse_items: list[str] | None,
    reverse_min: float | None,
    reverse_max: float | None,
) -> str:
    items_str = " ".join(items)
    func = "MEAN" if method.lower() == "mean" else "SUM"

    reverse_lines = ""
    if reverse_items:
        if reverse_min is None or reverse_max is None:
            raise ValueError("reverse_min and reverse_max are required when reverse_items is provided")
        for var in reverse_items:
            reverse_lines += (
                f"IF (NOT MISSING({var})) {var} = ({reverse_max} + {reverse_min}) - {var}.\n"
            )

    if min_valid is not None:
        compute_line = (
            f"IF (NVALID({items_str}) >= {min_valid}) {new_variable} = {func}({items_str}).\n"
            f"IF (NVALID({items_str}) < {min_valid}) {new_variable} = $SYSMIS.\n"
        )
    else:
        compute_line = f"COMPUTE {new_variable} = {func}({items_str}).\n"

    return (
        f"GET FILE='{file_path}'.\n"
        f"{reverse_lines}"
        f"{compute_line}"
        f"EXECUTE.\n"
        f"DESCRIPTIVES VARIABLES={new_variable}\n"
        f"  /STATISTICS=MEAN STDDEV MIN MAX.\n"
    )


def build_nonparametric_syntax(
    file_path: str,
    test_type: str,
    variables: list[str],
    grouping_variable: str | None,
    group_values: list[float] | None,
) -> str:
    test = test_type.lower()

    if test == "mann_whitney":
        if len(variables) != 1:
            raise ValueError("mann_whitney requires exactly one variable")
        if not grouping_variable:
            raise ValueError("grouping_variable is required for mann_whitney")
        if not group_values or len(group_values) != 2:
            raise ValueError("group_values must contain exactly 2 values for mann_whitney")
        return (
            f"GET FILE='{file_path}'.\n"
            f"NPAR TESTS\n"
            f"  /MANN-WHITNEY={variables[0]} BY {grouping_variable}({group_values[0]} {group_values[1]}).\n"
        )

    if test == "wilcoxon":
        if len(variables) != 2:
            raise ValueError("wilcoxon requires exactly 2 variables")
        return (
            f"GET FILE='{file_path}'.\n"
            f"NPAR TESTS\n"
            f"  /WILCOXON={variables[0]} WITH {variables[1]} (PAIRED).\n"
        )

    if test == "kruskal_wallis":
        if len(variables) != 1:
            raise ValueError("kruskal_wallis requires exactly one variable")
        if not grouping_variable:
            raise ValueError("grouping_variable is required for kruskal_wallis")
        return (
            f"GET FILE='{file_path}'.\n"
            f"NPAR TESTS\n"
            f"  /K-W={variables[0]} BY {grouping_variable}.\n"
        )

    raise ValueError("Unsupported test_type. Use: mann_whitney, wilcoxon, kruskal_wallis")


def build_normality_outliers_syntax(
    file_path: str,
    variables: list[str],
    plots: bool,
) -> str:
    vars_str = " ".join(variables)
    plot_part = "  /PLOT BOXPLOT STEMLEAF NPPLOT\n" if plots else ""
    return (
        f"GET FILE='{file_path}'.\n"
        f"EXAMINE VARIABLES={vars_str}\n"
        f"{plot_part}"
        f"  /STATISTICS DESCRIPTIVES EXTREME\n"
        f"  /CINTERVAL 95\n"
        f"  /MISSING LISTWISE\n"
        f"  /NOTOTAL.\n"
    )


def build_repeated_measures_anova_syntax(
    file_path: str,
    within_factor_name: str,
    levels: int,
    variables: list[str],
    include_pairwise: bool,
) -> str:
    if levels < 2:
        raise ValueError("levels must be >= 2")
    if len(variables) != levels:
        raise ValueError("variables count must equal levels")

    vars_str = " ".join(variables)
    emmeans = (
        f"  /EMMEANS=TABLES({within_factor_name}) COMPARE ADJ(BONFERRONI)\n"
        if include_pairwise
        else ""
    )

    return (
        f"GET FILE='{file_path}'.\n"
        f"GLM {vars_str}\n"
        f"  /WSFACTOR={within_factor_name} {levels} POLYNOMIAL\n"
        f"  /METHOD=SSTYPE(3)\n"
        f"{emmeans}"
        f"  /PRINT=DESCRIPTIVE ETASQ\n"
        f"  /CRITERIA=ALPHA(.05)\n"
        f"  /WSDESIGN={within_factor_name}.\n"
    )
