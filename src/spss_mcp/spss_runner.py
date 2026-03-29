"""
SPSS execution engine using IBM SPSS Statistics XD API.

Runs SPSS syntax headlessly via SPSS's own Python3 (XD API) as a subprocess,
injecting OMS commands to capture output as readable text instead of .spv binary.
"""

import asyncio
import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Optional

from spss_mcp.config import get_results_dir, get_spss_executable, get_temp_dir, get_timeout
from spss_mcp.output_parser import parse_spss_output


def get_spss_python() -> str | None:
    """Return path to the SPSS Python3 executable bundled with SPSS."""
    stats_exe = get_spss_executable()
    if not stats_exe:
        return None
    spss_home = str(Path(stats_exe).parent)
    python_exe = Path(spss_home) / "Python3" / "python.exe"
    if python_exe.exists():
        return str(python_exe)
    return None


def _build_execution_syntax(
    syntax: str,
    data_file: Optional[str] = None,
) -> str:
    data_line = ""
    if data_file:
        data_file_fwd = data_file.replace("\\", "/")
        data_line = f"GET FILE='{data_file_fwd}'.\n"
    return f"{data_line}{syntax.rstrip()}\n"


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


def _make_runner_script(
    spss_home: str,
    full_syntax: str,
    output_file: str,
    viewer_file: str | None = None,
) -> str:
    """
    Generate the Python script that runs inside SPSS Python3 via XD API.
    The script starts the SPSS backend, submits OMS-wrapped syntax, writes output, then exits.
    """

    # Write the syntax and paths to a separate data file to avoid quoting hell
    # The runner script reads them back at runtime using paths injected as raw strings
    spss_home_r = repr(spss_home)
    output_file_r = repr(output_file)
    viewer_file_r = repr(viewer_file)
    syntax_r = repr(full_syntax)

    lines = [
        "import sys, os",
        f"SPSS_HOME = {spss_home_r}",
        'os.environ["PATH"] = SPSS_HOME + os.pathsep + os.environ.get("PATH", "")',
        'sys.path.insert(0, os.path.join(SPSS_HOME, "Python3", "Lib", "site-packages"))',
        "import spss",
        f"syntax = {syntax_r}",
        f"output_file = {output_file_r}",
        f"viewer_file = {viewer_file_r}",
        "try:",
        "    spss.StartSPSS()",
        "except Exception as e:",
        '    print(f"__spss_error__={e}", file=sys.stderr)',
        "    sys.exit(1)",
        "try:",
        "    spss.Submit(syntax)",
        "except spss.SpssError as e:",
        '    print(f"__spss_warn__={e}", file=sys.stderr)',
        "except Exception as e:",
        '    print(f"__spss_error__={e}", file=sys.stderr)',
        "    sys.exit(2)",
        "if viewer_file:",
        "    if os.path.exists(viewer_file):",
        '        print("__spss_viewer_ok__")',
        "    else:",
        '        print("__spss_viewer_missing__", file=sys.stderr)',
        "last_err = spss.GetLastErrorLevel()",
        'print(f"__spss_err_level__={last_err}")',
        "if os.path.exists(output_file):",
        '    print("__spss_ok__")',
        "else:",
        '    print("__spss_no_output__", file=sys.stderr)',
    ]
    return "\n".join(lines) + "\n"


async def run_syntax(
    syntax: str,
    data_file: Optional[str] = None,
    save_viewer_output: bool = True,
    save_syntax_file: bool = True,
) -> dict:
    """
    Execute SPSS syntax via the XD API (SPSS Python3 subprocess) and return structured result.

    Returns:
        {
            "success": bool,
            "output_markdown": str,
            "output_raw": str,
            "error": str | None,
            "warnings": list[str],
        }
    """
    stats_exe = get_spss_executable()
    if not stats_exe:
        return {
            "success": False,
            "output_markdown": "",
            "output_raw": "",
            "error": (
                "IBM SPSS Statistics is not installed or not found. "
                "Set SPSS_INSTALL_PATH to the SPSS installation directory, "
                "or use spss_check_status to see available capabilities."
            ),
            "warnings": [],
        }

    spss_python = get_spss_python()
    if not spss_python:
        return {
            "success": False,
            "output_markdown": "",
            "output_raw": "",
            "error": (
                "SPSS Python3 interpreter not found. "
                f"Expected at: {Path(stats_exe).parent / 'Python3' / 'python.exe'}"
            ),
            "warnings": [],
        }

    spss_home = str(Path(stats_exe).parent)
    run_id = uuid.uuid4().hex[:12]
    temp_dir = get_temp_dir()
    results_dir = get_results_dir()
    runner_script = temp_dir / f"spss_run_{run_id}.py"
    output_file = temp_dir / f"spss_out_{run_id}.txt"
    syntax_file = results_dir / f"spss_syntax_{run_id}.sps" if save_syntax_file else None
    viewer_file = results_dir / f"spss_viewer_{run_id}.spv" if save_viewer_output else None

    execution_syntax = _build_execution_syntax(
        syntax=syntax,
        data_file=data_file,
    )
    full_syntax = _build_full_syntax(
        execution_syntax=execution_syntax,
        output_file=str(output_file),
        viewer_file=str(viewer_file) if viewer_file else None,
    )

    script_content = _make_runner_script(
        spss_home=spss_home,
        full_syntax=full_syntax,
        output_file=str(output_file),
        viewer_file=str(viewer_file) if viewer_file else None,
    )

    try:
        if syntax_file:
            syntax_file.write_text(execution_syntax, encoding="utf-8")
        runner_script.write_text(script_content, encoding="utf-8")

        def _run_subprocess():
            env = os.environ.copy()
            env["PATH"] = spss_home + os.pathsep + env.get("PATH", "")
            return subprocess.run(
                [spss_python, str(runner_script)],
                capture_output=True,
                text=True,
                timeout=get_timeout(),
                env=env,
            )

        try:
            proc = await asyncio.to_thread(_run_subprocess)
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output_markdown": "",
                "output_raw": "",
                "error": (
                    f"SPSS job exceeded the {get_timeout()} second timeout. "
                    "Simplify the analysis or increase SPSS_TIMEOUT."
                ),
                "warnings": [],
            }
        except FileNotFoundError as e:
            return {
                "success": False,
                "output_markdown": "",
                "output_raw": "",
                "error": f"SPSS Python3 not found: {e}",
                "warnings": [],
            }

        # Read OMS output file
        raw_output = ""
        if output_file.exists():
            raw_output = output_file.read_text(encoding="utf-8-sig", errors="replace")

        stderr_text = (proc.stderr or "").strip()

        # Detect success
        stdout_text = proc.stdout or ""
        ok_signal = "__spss_ok__" in stdout_text
        viewer_ok_signal = "__spss_viewer_ok__" in stdout_text

        err_signal = "__spss_error__" in stderr_text
        warn_signal = "__spss_warn__" in stderr_text
        no_output = "__spss_no_output__" in stderr_text
        viewer_missing_signal = "__spss_viewer_missing__" in stderr_text
        viewer_err_signal = "__spss_viewer_error__" in stderr_text

        # Success = output file was produced (even if SPSS emitted a SpssError warning)
        success = ok_signal and bool(raw_output) and proc.returncode == 0

        if not raw_output and stderr_text:
            raw_output = stderr_text

        markdown = parse_spss_output(raw_output) if raw_output else "_No output produced._"

        warnings: list[str] = []

        # Append any SPSS-level warnings to the markdown output
        if warn_signal and success:
            warn_text = "\n".join(
                line.replace("__spss_warn__=", "").strip()
                for line in stderr_text.splitlines()
                if "__spss_warn__" in line
            )
            if warn_text:
                warnings.append(warn_text)
                markdown += f"\n\n> **Note:** {warn_text}"

        viewer_error = None
        if save_viewer_output:
            if viewer_err_signal:
                viewer_error = "\n".join(
                    line.replace("__spss_viewer_error__=", "").strip()
                    for line in stderr_text.splitlines()
                    if "__spss_viewer_error__" in line
                ) or "SPSS failed to save viewer output (.spv)."
            elif viewer_missing_signal:
                viewer_error = "SPSS reported viewer save but .spv file was not found."

        error_msg = None
        if not success:
            if err_signal:
                error_msg = stderr_text.replace("__spss_error__=", "SPSS error: ")
            elif no_output:
                error_msg = "SPSS ran but produced no output file."
            elif proc.returncode != 0:
                error_msg = stderr_text or f"SPSS process exited with code {proc.returncode}"
            elif not ok_signal:
                error_msg = "SPSS did not confirm successful completion."

        viewer_output_file = None
        if save_viewer_output and viewer_file and viewer_file.exists() and viewer_ok_signal:
            viewer_output_file = str(viewer_file)

        syntax_output_file = str(syntax_file) if syntax_file and syntax_file.exists() else None

        if viewer_error:
            warnings.append(viewer_error)
            markdown += f"\n\n> **Viewer save note:** {viewer_error}"

        return {
            "success": success,
            "output_markdown": markdown,
            "output_raw": raw_output,
            "viewer_output_file": viewer_output_file,
            "syntax_file": syntax_output_file,
            "viewer_error": viewer_error,
            "error": error_msg,
            "warnings": warnings,
        }

    finally:
        for f in (runner_script, output_file):
            try:
                if f.exists():
                    f.unlink()
            except OSError:
                pass


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
    diag = "  /STATISTICS=COEFF OUTS R ANOVA COLLIN TOL\n" if include_diagnostics else "  /STATISTICS=COEFF OUTS R ANOVA\n"
    return (
        f"GET FILE='{file_path}'.\n"
        f"REGRESSION\n"
        f"  /DEPENDENT {dependent}\n"
        f"  /METHOD={method.upper()} {preds_str}\n"
        f"{diag}."
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
        ph_line = f"  /POSTHOC={factor} ({ph_str})\n"
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
