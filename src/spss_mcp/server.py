"""
SPSS MCP server — all tool definitions.
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal, Optional

from fastmcp import Context, FastMCP

from spss_mcp.config import detect_capabilities


# ─── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def server_lifespan(server: FastMCP):
    sys.stderr.write("Starting SPSS MCP server...\n")
    caps = detect_capabilities()
    sys.stderr.write(
        f"  pyreadstat : {'available v' + caps['pyreadstat_version'] if caps['pyreadstat'] else 'NOT FOUND'}\n"
    )
    sys.stderr.write(
        f"  SPSS batch : {'available — ' + caps['spss_path'] if caps['spss'] else 'NOT FOUND (file-only mode)'}\n"
    )
    yield {"capabilities": caps}
    sys.stderr.write("Shutting down SPSS MCP server.\n")


mcp = FastMCP("SPSS", lifespan=server_lifespan)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_caps(ctx: Context) -> dict:
    try:
        return ctx.request_context.lifespan_context["capabilities"]
    except Exception:
        return detect_capabilities()


def _require_spss(ctx: Context) -> str | None:
    """Return error message if SPSS is not available, else None."""
    caps = _get_caps(ctx)
    if not caps.get("spss"):
        return (
            "This tool requires IBM SPSS Statistics to be installed and detected. "
            "Call `spss_check_status` to see what's available, "
            "or set SPSS_INSTALL_PATH to the SPSS installation directory."
        )
    return None


def _require_pyreadstat(ctx: Context) -> str | None:
    caps = _get_caps(ctx)
    if not caps.get("pyreadstat"):
        return "pyreadstat is not installed. Run: pip install pyreadstat"
    return None


def _format_run_result(result: dict) -> str:
    if result.get("error") and not result.get("output_markdown"):
        return f"Error: {result['error']}"

    output = result.get("output_markdown") or "_No output produced._"

    viewer_file = result.get("viewer_output_file")
    if viewer_file:
        output += f"\n\n> Viewer file: `{viewer_file}`"

    syntax_file = result.get("syntax_file")
    if syntax_file:
        output += f"\n\n> Syntax file: `{syntax_file}`"

    viewer_error = result.get("viewer_error")
    if viewer_error and not viewer_file:
        output += f"\n\n> Viewer save note: {viewer_error}"

    return output


# ─── Group 1: Status & File Tools (no SPSS needed) ───────────────────────────

@mcp.tool(
    name="spss_check_status",
    description=(
        "Check the SPSS MCP server status: which capabilities are available "
        "(SPSS installed vs file-only mode), SPSS path, library versions, and configuration. "
        "Call this first to understand what tools are available."
    ),
)
async def spss_check_status(ctx: Context) -> str:
    try:
        from spss_mcp._version import __version__
        caps = detect_capabilities()
        lines = [
            f"# SPSS MCP Server Status (v{__version__})\n",
            "## Capabilities\n",
            f"| Capability | Status |",
            f"|---|---|",
            f"| pyreadstat (.sav file I/O) | {'✅ v' + caps['pyreadstat_version'] if caps['pyreadstat'] else '❌ Not installed'} |",
            f"| pandas | {'✅ v' + caps['pandas_version'] if caps['pandas_version'] else '❌ Not installed'} |",
            f"| IBM SPSS Statistics (batch) | {'✅ Found' if caps['spss'] else '❌ Not found'} |",
            "",
        ]
        if caps["spss"]:
            lines.append(f"**SPSS path:** `{caps['spss_path']}`\n")
        else:
            lines.append(
                "**Mode:** File-only (read/write .sav files without SPSS). "
                "Set `SPSS_INSTALL_PATH` env var to enable full SPSS analysis.\n"
            )
        return "\n".join(lines)
    except Exception as e:
        await ctx.error(f"spss_check_status error: {e}")
        return f"Error: {e}"


@mcp.tool(
    name="spss_list_files",
    description=(
        "List SPSS .sav files in a directory. "
        "Useful for discovering available datasets when the user hasn't specified a file path."
    ),
)
async def spss_list_files(
    directory: str,
    recursive: bool = False,
    ctx: Context = None,
) -> str:
    try:
        p = Path(directory)
        if not p.exists():
            return f"Error: Directory not found: {directory}"
        if not p.is_dir():
            return f"Error: Not a directory: {directory}"

        pattern = "**/*.sav" if recursive else "*.sav"
        files = sorted(p.glob(pattern))
        zsav = sorted(p.glob("**/*.zsav" if recursive else "*.zsav"))
        all_files = files + zsav

        if not all_files:
            return f"No .sav or .zsav files found in `{directory}`."

        from tabulate import tabulate
        rows = [[f.name, str(f.parent), f"{f.stat().st_size / 1024:.1f} KB"] for f in all_files]
        return tabulate(rows, headers=["File", "Directory", "Size"], tablefmt="github")
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_list_files error: {e}")
        return f"Error: {e}"


@mcp.tool(
    name="spss_list_variables",
    description=(
        "List all variable names and their labels from an SPSS .sav file. "
        "Optionally filter by a search term. Does not require SPSS to be installed."
    ),
)
async def spss_list_variables(
    file_path: str,
    search: Optional[str] = None,
    ctx: Context = None,
) -> str:
    try:
        err = _require_pyreadstat(ctx)
        if err:
            return f"Error: {err}"

        from spss_mcp.sav_reader import read_metadata
        from tabulate import tabulate

        meta = await read_metadata(file_path)
        names = meta["column_names"]
        labels = meta["column_names_to_labels"]

        rows = [[n, labels.get(n, "")] for n in names]
        if search:
            s = search.lower()
            rows = [r for r in rows if s in r[0].lower() or s in r[1].lower()]

        if not rows:
            return f"No variables found matching '{search}'." if search else "No variables found."

        header = f"**{len(rows)} variables** in `{Path(file_path).name}`\n\n"
        return header + tabulate(rows, headers=["Name", "Label"], tablefmt="github")
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_list_variables error: {e}")
        return f"Error: {e}"


@mcp.tool(
    name="spss_read_metadata",
    description=(
        "Read variable names, types, labels, and value labels from an SPSS .sav file. "
        "Returns a detailed Markdown report of the file's structure. "
        "Does not require SPSS to be installed."
    ),
)
async def spss_read_metadata(
    file_path: str,
    ctx: Context = None,
) -> str:
    try:
        err = _require_pyreadstat(ctx)
        if err:
            return f"Error: {err}"

        from spss_mcp.sav_reader import read_metadata, format_metadata_as_markdown
        meta = await read_metadata(file_path)
        return format_metadata_as_markdown(meta)
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_read_metadata error: {e}")
        return f"Error: {e}"


@mcp.tool(
    name="spss_read_data",
    description=(
        "Read rows of data from an SPSS .sav file as a Markdown table. "
        "Optionally filter to specific variables and limit row count. "
        "Does not require SPSS to be installed."
    ),
)
async def spss_read_data(
    file_path: str,
    variables: Optional[list] = None,
    max_rows: int = 50,
    apply_value_labels: bool = True,
    ctx: Context = None,
) -> str:
    try:
        err = _require_pyreadstat(ctx)
        if err:
            return f"Error: {err}"

        from spss_mcp.sav_reader import read_data, format_dataframe_as_markdown
        result = await read_data(
            file_path,
            variables=variables,
            max_rows=max_rows,
            apply_value_labels=apply_value_labels,
        )
        df = result["dataframe"]
        n_total = result["meta"].number_rows
        header = f"**Showing {len(df)} of {n_total} cases** from `{Path(file_path).name}`\n\n"
        return header + format_dataframe_as_markdown(df)
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_read_data error: {e}")
        return f"Error: {e}"


@mcp.tool(
    name="spss_file_summary",
    description=(
        "Get a summary of an SPSS .sav file: case count, variable count, variable list, "
        "and basic descriptive statistics computed locally (no SPSS needed). "
        "Does not require SPSS to be installed."
    ),
)
async def spss_file_summary(
    file_path: str,
    ctx: Context = None,
) -> str:
    try:
        err = _require_pyreadstat(ctx)
        if err:
            return f"Error: {err}"

        from spss_mcp.sav_reader import get_file_summary, format_summary_as_markdown
        summary = await get_file_summary(file_path)
        header = f"# Summary: `{Path(file_path).name}`\n\n"
        return header + format_summary_as_markdown(summary)
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_file_summary error: {e}")
        return f"Error: {e}"


# ─── Group 2: SPSS Analysis Tools (require SPSS installation) ─────────────────

@mcp.tool(
    name="spss_run_syntax",
    description=(
        "Execute arbitrary SPSS syntax commands and return the output as Markdown. "
        "Optionally specify a data_file to automatically prepend GET FILE. "
        "By default, this also persists .spv (SPSS viewer) and .sps (executed syntax) files. "
        "Requires IBM SPSS Statistics to be installed."
    ),
)
async def spss_run_syntax(
    syntax: str,
    data_file: Optional[str] = None,
    save_viewer_output: bool = True,
    save_syntax_file: bool = True,
    ctx: Context = None,
) -> str:
    try:
        err = _require_spss(ctx)
        if err:
            return f"Error: {err}"

        from spss_mcp.spss_runner import run_syntax
        result = await run_syntax(
            syntax,
            data_file=data_file,
            save_viewer_output=save_viewer_output,
            save_syntax_file=save_syntax_file,
        )
        return _format_run_result(result)
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_run_syntax error: {e}")
        return f"Error: {e}"


@mcp.tool(
    name="spss_frequencies",
    description=(
        "Run SPSS FREQUENCIES on one or more variables. "
        "Returns frequency tables with counts, percentages, and optional statistics. "
        "Requires IBM SPSS Statistics to be installed."
    ),
)
async def spss_frequencies(
    file_path: str,
    variables: list,
    statistics: list = None,
    ctx: Context = None,
) -> str:
    try:
        err = _require_spss(ctx)
        if err:
            return f"Error: {err}"

        if statistics is None:
            statistics = ["mean", "median", "mode", "stddev"]

        from spss_mcp.spss_runner import run_syntax, build_frequencies_syntax
        syntax = build_frequencies_syntax(file_path, variables, statistics)
        result = await run_syntax(syntax)
        return _format_run_result(result)
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_frequencies error: {e}")
        return f"Error: {e}"


@mcp.tool(
    name="spss_descriptives",
    description=(
        "Run SPSS DESCRIPTIVES for numeric variables. "
        "Returns N, mean, std deviation, min, max, and optional statistics. "
        "Requires IBM SPSS Statistics to be installed."
    ),
)
async def spss_descriptives(
    file_path: str,
    variables: list,
    statistics: list = None,
    ctx: Context = None,
) -> str:
    try:
        err = _require_spss(ctx)
        if err:
            return f"Error: {err}"

        if statistics is None:
            statistics = ["mean", "stddev", "min", "max", "variance"]

        from spss_mcp.spss_runner import run_syntax, build_descriptives_syntax
        syntax = build_descriptives_syntax(file_path, variables, statistics)
        result = await run_syntax(syntax)
        return _format_run_result(result)
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_descriptives error: {e}")
        return f"Error: {e}"


@mcp.tool(
    name="spss_crosstabs",
    description=(
        "Run SPSS CROSSTABS to create a contingency table between two categorical variables. "
        "Optionally includes chi-square test and row/column percentages. "
        "Requires IBM SPSS Statistics to be installed."
    ),
)
async def spss_crosstabs(
    file_path: str,
    row_variable: str,
    column_variable: str,
    include_chisquare: bool = True,
    include_row_pct: bool = True,
    include_col_pct: bool = True,
    ctx: Context = None,
) -> str:
    try:
        err = _require_spss(ctx)
        if err:
            return f"Error: {err}"

        from spss_mcp.spss_runner import run_syntax, build_crosstabs_syntax
        syntax = build_crosstabs_syntax(
            file_path, row_variable, column_variable,
            include_chisquare, include_row_pct, include_col_pct
        )
        result = await run_syntax(syntax)
        return _format_run_result(result)
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_crosstabs error: {e}")
        return f"Error: {e}"


@mcp.tool(
    name="spss_regression",
    description=(
        "Run SPSS linear regression. Specify a dependent variable and one or more predictors. "
        "Returns coefficients, R-squared, ANOVA table, and significance tests. "
        "Requires IBM SPSS Statistics to be installed."
    ),
)
async def spss_regression(
    file_path: str,
    dependent: str,
    predictors: list,
    method: str = "ENTER",
    include_diagnostics: bool = False,
    ctx: Context = None,
) -> str:
    try:
        err = _require_spss(ctx)
        if err:
            return f"Error: {err}"

        from spss_mcp.spss_runner import run_syntax, build_regression_syntax
        syntax = build_regression_syntax(
            file_path, dependent, predictors, method, include_diagnostics
        )
        result = await run_syntax(syntax)
        return _format_run_result(result)
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_regression error: {e}")
        return f"Error: {e}"


@mcp.tool(
    name="spss_t_test",
    description=(
        "Run SPSS t-test. Supports one_sample, independent, and paired test types. "
        "Requires IBM SPSS Statistics to be installed."
    ),
)
async def spss_t_test(
    file_path: str,
    test_type: Literal["one_sample", "independent", "paired"],
    variables: list,
    grouping_variable: Optional[str] = None,
    test_value: Optional[float] = None,
    ctx: Context = None,
) -> str:
    try:
        err = _require_spss(ctx)
        if err:
            return f"Error: {err}"

        from spss_mcp.spss_runner import run_syntax, build_t_test_syntax
        syntax = build_t_test_syntax(
            file_path, test_type, variables, grouping_variable, test_value
        )
        result = await run_syntax(syntax)
        return _format_run_result(result)
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_t_test error: {e}")
        return f"Error: {e}"


@mcp.tool(
    name="spss_anova",
    description=(
        "Run SPSS one-way ANOVA (ONEWAY). Optionally includes post-hoc tests "
        "(e.g., TUKEY, BONFERRONI, LSD). "
        "Requires IBM SPSS Statistics to be installed."
    ),
)
async def spss_anova(
    file_path: str,
    dependent: str,
    factor: str,
    post_hoc: Optional[list] = None,
    ctx: Context = None,
) -> str:
    try:
        err = _require_spss(ctx)
        if err:
            return f"Error: {err}"

        from spss_mcp.spss_runner import run_syntax, build_anova_syntax
        syntax = build_anova_syntax(file_path, dependent, factor, post_hoc)
        result = await run_syntax(syntax)
        return _format_run_result(result)
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_anova error: {e}")
        return f"Error: {e}"


@mcp.tool(
    name="spss_correlations",
    description=(
        "Run SPSS CORRELATIONS to compute Pearson or Spearman correlation matrix. "
        "Requires IBM SPSS Statistics to be installed."
    ),
)
async def spss_correlations(
    file_path: str,
    variables: list,
    method: Literal["pearson", "spearman"] = "pearson",
    two_tailed: bool = True,
    ctx: Context = None,
) -> str:
    try:
        err = _require_spss(ctx)
        if err:
            return f"Error: {err}"

        from spss_mcp.spss_runner import run_syntax, build_correlations_syntax
        syntax = build_correlations_syntax(file_path, variables, method, two_tailed)
        result = await run_syntax(syntax)
        return _format_run_result(result)
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_correlations error: {e}")
        return f"Error: {e}"


@mcp.tool(
    name="spss_factor",
    description=(
        "Run SPSS FACTOR analysis (principal components or principal axis factoring). "
        "Includes eigenvalues, variance explained, and rotated factor matrix. "
        "Requires IBM SPSS Statistics to be installed."
    ),
)
async def spss_factor(
    file_path: str,
    variables: list,
    method: Literal["PC", "PA"] = "PC",
    rotation: Literal["VARIMAX", "OBLIMIN", "NONE"] = "VARIMAX",
    n_factors: Optional[int] = None,
    ctx: Context = None,
) -> str:
    try:
        err = _require_spss(ctx)
        if err:
            return f"Error: {err}"

        from spss_mcp.spss_runner import run_syntax, build_factor_syntax
        syntax = build_factor_syntax(file_path, variables, method, rotation, n_factors)
        result = await run_syntax(syntax)
        return _format_run_result(result)
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_factor error: {e}")
        return f"Error: {e}"


@mcp.tool(
    name="spss_reliability_alpha",
    description=(
        "Run SPSS RELIABILITY analysis (Cronbach's alpha). "
        "Returns scale reliability and item statistics for psychometric workflows. "
        "Requires IBM SPSS Statistics to be installed."
    ),
)
async def spss_reliability_alpha(
    file_path: str,
    variables: list,
    scale_name: Optional[str] = None,
    model: Literal["ALPHA", "OMEGA"] = "ALPHA",
    ctx: Context = None,
) -> str:
    try:
        err = _require_spss(ctx)
        if err:
            return f"Error: {err}"

        from spss_mcp.spss_runner import run_syntax, build_reliability_syntax
        syntax = build_reliability_syntax(file_path, variables, scale_name, model)
        result = await run_syntax(syntax)
        return _format_run_result(result)
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_reliability_alpha error: {e}")
        return f"Error: {e}"


@mcp.tool(
    name="spss_compute_scale_score",
    description=(
        "Compute a scale score (SUM or MEAN) from multiple item variables, "
        "with optional reverse coding and minimum valid item count. "
        "Requires IBM SPSS Statistics to be installed."
    ),
)
async def spss_compute_scale_score(
    file_path: str,
    new_variable: str,
    items: list,
    method: Literal["sum", "mean"] = "mean",
    min_valid: Optional[int] = None,
    reverse_items: Optional[list] = None,
    reverse_min: Optional[float] = None,
    reverse_max: Optional[float] = None,
    ctx: Context = None,
) -> str:
    try:
        err = _require_spss(ctx)
        if err:
            return f"Error: {err}"

        from spss_mcp.spss_runner import run_syntax, build_compute_scale_syntax
        syntax = build_compute_scale_syntax(
            file_path=file_path,
            new_variable=new_variable,
            items=items,
            method=method,
            min_valid=min_valid,
            reverse_items=reverse_items,
            reverse_min=reverse_min,
            reverse_max=reverse_max,
        )
        result = await run_syntax(syntax)
        return _format_run_result(result)
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_compute_scale_score error: {e}")
        return f"Error: {e}"


@mcp.tool(
    name="spss_nonparametric_tests",
    description=(
        "Run common nonparametric tests in SPSS: Mann-Whitney U, Wilcoxon signed-rank, "
        "or Kruskal-Wallis. Requires IBM SPSS Statistics to be installed."
    ),
)
async def spss_nonparametric_tests(
    file_path: str,
    test_type: Literal["mann_whitney", "wilcoxon", "kruskal_wallis"],
    variables: list,
    grouping_variable: Optional[str] = None,
    group_values: Optional[list] = None,
    ctx: Context = None,
) -> str:
    try:
        err = _require_spss(ctx)
        if err:
            return f"Error: {err}"

        from spss_mcp.spss_runner import run_syntax, build_nonparametric_syntax
        syntax = build_nonparametric_syntax(
            file_path=file_path,
            test_type=test_type,
            variables=variables,
            grouping_variable=grouping_variable,
            group_values=group_values,
        )
        result = await run_syntax(syntax)
        return _format_run_result(result)
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_nonparametric_tests error: {e}")
        return f"Error: {e}"


@mcp.tool(
    name="spss_normality_outliers",
    description=(
        "Run SPSS EXAMINE to check normality and outliers for numeric variables, "
        "with optional diagnostic plots. Requires IBM SPSS Statistics to be installed."
    ),
)
async def spss_normality_outliers(
    file_path: str,
    variables: list,
    plots: bool = True,
    ctx: Context = None,
) -> str:
    try:
        err = _require_spss(ctx)
        if err:
            return f"Error: {err}"

        from spss_mcp.spss_runner import run_syntax, build_normality_outliers_syntax
        syntax = build_normality_outliers_syntax(file_path, variables, plots)
        result = await run_syntax(syntax)
        return _format_run_result(result)
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_normality_outliers error: {e}")
        return f"Error: {e}"


@mcp.tool(
    name="spss_repeated_measures_anova",
    description=(
        "Run SPSS repeated-measures ANOVA (within-subject GLM). "
        "Provide within-factor name, number of levels, and one variable per level. "
        "Requires IBM SPSS Statistics to be installed."
    ),
)
async def spss_repeated_measures_anova(
    file_path: str,
    within_factor_name: str,
    levels: int,
    variables: list,
    include_pairwise: bool = True,
    ctx: Context = None,
) -> str:
    try:
        err = _require_spss(ctx)
        if err:
            return f"Error: {err}"

        from spss_mcp.spss_runner import run_syntax, build_repeated_measures_anova_syntax
        syntax = build_repeated_measures_anova_syntax(
            file_path=file_path,
            within_factor_name=within_factor_name,
            levels=levels,
            variables=variables,
            include_pairwise=include_pairwise,
        )
        result = await run_syntax(syntax)
        return _format_run_result(result)
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_repeated_measures_anova error: {e}")
        return f"Error: {e}"


@mcp.tool(
    name="spss_validate_syntax",
    description=(
        "Validate SPSS syntax without executing it. "
        "Checks for basic syntax errors. "
        "Requires IBM SPSS Statistics to be installed."
    ),
)
async def spss_validate_syntax(
    syntax: str,
    ctx: Context = None,
) -> str:
    try:
        err = _require_spss(ctx)
        if err:
            return f"Error: {err}"

        # Wrap syntax with a FINISH to stop early
        validate_syntax = syntax.rstrip() + "\nFINISH.\n"
        from spss_mcp.spss_runner import run_syntax
        result = await run_syntax(
            validate_syntax,
            save_viewer_output=False,
            save_syntax_file=False,
        )
        if result["success"]:
            return "Syntax appears valid — no errors detected."
        return f"Syntax errors found:\n\n{result['output_markdown']}"
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_validate_syntax error: {e}")
        return f"Error: {e}"


# ─── Advanced Regression & GLM ────────────────────────────────────────────────

@mcp.tool(
    name="spss_logistic_regression",
    description=(
        "Run binary or multinomial logistic regression. "
        "Supports stepwise selection, categorical predictors, and model diagnostics. "
        "Requires IBM SPSS Statistics to be installed."
    ),
)
async def spss_logistic_regression(
    file_path: str,
    dependent: str,
    predictors: list[str],
    method: Literal["ENTER", "FSTEP", "BSTEP"] = "ENTER",
    categorical: Optional[list[str]] = None,
    contrast: Optional[str] = None,
    save_predicted: bool = False,
    print_options: Optional[list[str]] = None,
    ctx: Context = None,
) -> str:
    """
    Binary/multinomial logistic regression.

    Args:
        file_path: Path to .sav file
        dependent: Dependent variable (binary or categorical)
        predictors: List of predictor variables
        method: Variable selection method (ENTER/FSTEP/BSTEP)
        categorical: List of categorical predictors
        contrast: Contrast coding for categorical (INDICATOR/SIMPLE/DEVIATION/etc)
        save_predicted: Save predicted probabilities and group membership
        print_options: Additional print options (CI/CORR/ITER/etc)
    """
    try:
        err = _require_spss(ctx)
        if err:
            return f"Error: {err}"

        from spss_mcp.spss_runner import run_syntax

        syntax = f"GET FILE='{file_path.replace(chr(92), '/')}'.\n"
        syntax += f"LOGISTIC REGRESSION VARIABLES {dependent}\n"
        syntax += f"  /METHOD={method} {' '.join(predictors)}\n"

        if categorical:
            cat_spec = ' '.join(categorical)
            if contrast:
                syntax += f"  /CATEGORICAL={cat_spec}({contrast})\n"
            else:
                syntax += f"  /CATEGORICAL={cat_spec}\n"

        if save_predicted:
            syntax += "  /SAVE=PRED PGROUP\n"

        if print_options:
            syntax += f"  /PRINT={' '.join(print_options)}\n"
        else:
            syntax += "  /PRINT=GOODFIT CI(95)\n"

        syntax += "  /CRITERIA=PIN(0.05) POUT(0.10) ITERATE(20) CUT(0.5).\n"

        result = await run_syntax(syntax, data_file=file_path)
        return _format_run_result(result)
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_logistic_regression error: {e}")
        return f"Error: {e}"


@mcp.tool(
    name="spss_ordinal_regression",
    description=(
        "Run ordinal regression (PLUM) for ordered categorical outcomes. "
        "Supports multiple link functions and parallel lines test. "
        "Requires IBM SPSS Statistics to be installed."
    ),
)
async def spss_ordinal_regression(
    file_path: str,
    dependent: str,
    predictors: list[str],
    link: Literal["LOGIT", "PROBIT", "CLOGLOG", "NLOGLOG", "CAUCHIT"] = "LOGIT",
    categorical: Optional[list[str]] = None,
    save_predicted: bool = False,
    test_parallel: bool = True,
    ctx: Context = None,
) -> str:
    """
    Ordinal regression for ordered categorical dependent variable.

    Args:
        file_path: Path to .sav file
        dependent: Ordered categorical dependent variable
        predictors: List of predictor variables
        link: Link function (LOGIT/PROBIT/CLOGLOG/NLOGLOG/CAUCHIT)
        categorical: List of categorical predictors
        save_predicted: Save predicted category and probabilities
        test_parallel: Test parallel lines assumption
    """
    try:
        err = _require_spss(ctx)
        if err:
            return f"Error: {err}"

        from spss_mcp.spss_runner import run_syntax

        syntax = f"GET FILE='{file_path.replace(chr(92), '/')}'.\n"
        syntax += f"PLUM {dependent} WITH {' '.join(predictors)}\n"
        syntax += f"  /LINK={link}\n"

        if categorical:
            syntax += f"  /CATEGORICAL={' '.join(categorical)}\n"

        if save_predicted:
            syntax += "  /SAVE=PCPROB ACPROB\n"

        syntax += "  /PRINT=FIT PARAMETER SUMMARY\n"

        if test_parallel:
            syntax += "  /TEST=PARALLEL\n"

        syntax += "  /CRITERIA=CIN(95) DELTA(0) LCONVERGE(0) MXITER(100) MXSTEP(5) PCONVERGE(1.0E-6) SINGULAR(1.0E-8).\n"

        result = await run_syntax(syntax, data_file=file_path)
        return _format_run_result(result)
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_ordinal_regression error: {e}")
        return f"Error: {e}"


@mcp.tool(
    name="spss_genlin",
    description=(
        "Run generalized linear model (GENLIN) with flexible distribution and link functions. "
        "Supports Poisson, binomial, gamma, negative binomial, and other distributions. "
        "Requires IBM SPSS Statistics to be installed."
    ),
)
async def spss_genlin(
    file_path: str,
    dependent: str,
    predictors: list[str],
    distribution: Literal["NORMAL", "BINOMIAL", "POISSON", "GAMMA", "IGAUSS", "NEGBIN", "MULTINOMIAL"] = "NORMAL",
    link: Optional[str] = None,
    scale: Optional[str] = None,
    categorical: Optional[list[str]] = None,
    save_predicted: bool = False,
    ctx: Context = None,
) -> str:
    """
    Generalized linear model with flexible distribution families.

    Args:
        file_path: Path to .sav file
        dependent: Dependent variable
        predictors: List of predictor variables
        distribution: Distribution family (NORMAL/BINOMIAL/POISSON/GAMMA/IGAUSS/NEGBIN/MULTINOMIAL)
        link: Link function (auto-selected if None based on distribution)
        scale: Scale parameter method (MLE/DEVIANCE/PEARSON)
        categorical: List of categorical predictors
        save_predicted: Save predicted values and residuals
    """
    try:
        err = _require_spss(ctx)
        if err:
            return f"Error: {err}"

        from spss_mcp.spss_runner import run_syntax

        syntax = f"GET FILE='{file_path.replace(chr(92), '/')}'.\n"
        syntax += f"GENLIN {dependent}"

        if predictors:
            syntax += f" WITH {' '.join(predictors)}\n"
        else:
            syntax += "\n"

        if categorical:
            syntax += f"  /CATEGORICAL={' '.join(categorical)}\n"

        syntax += f"  /MODEL {' '.join(predictors)} DISTRIBUTION={distribution}"

        if link:
            syntax += f" LINK={link}\n"
        else:
            syntax += "\n"

        if scale:
            syntax += f"  /SCALE={scale}\n"

        if save_predicted:
            syntax += "  /SAVE=PRED RESID\n"

        syntax += "  /PRINT=SOLUTION SUMMARY\n"
        syntax += "  /CRITERIA=SCALE=1 COVB=MODEL PCONVERGE=1E-6 SINGULAR=1E-12 ANALYSISTYPE=3(WALD) CILEVEL=95 CITYPE=WALD LIKELIHOOD=FULL.\n"

        result = await run_syntax(syntax, data_file=file_path)
        return _format_run_result(result)
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_genlin error: {e}")
        return f"Error: {e}"


# ─── Multilevel & Mixed Models ───────────────────────────────────────────────

@mcp.tool(
    name="spss_mixed",
    description=(
        "Run linear mixed-effects model (multilevel model) with random effects. "
        "Supports nested and crossed random effects, repeated measures structures. "
        "Requires IBM SPSS Statistics to be installed."
    ),
)
async def spss_mixed(
    file_path: str,
    dependent: str,
    fixed_effects: list[str],
    random_effects: Optional[list[str]] = None,
    subject: Optional[str] = None,
    repeated: Optional[str] = None,
    repeated_type: Optional[str] = None,
    method: Literal["REML", "ML"] = "REML",
    covtype_random: Optional[str] = None,
    ctx: Context = None,
) -> str:
    """
    Linear mixed-effects model for hierarchical/nested data.

    Args:
        file_path: Path to .sav file
        dependent: Dependent variable
        fixed_effects: List of fixed effect predictors
        random_effects: List of random effect variables
        subject: Subject/grouping variable for random effects
        repeated: Repeated measures variable
        repeated_type: Covariance structure for repeated (AR1/CS/UN/etc)
        method: Estimation method (REML/ML)
        covtype_random: Covariance type for random effects (VC/UN/CS/etc)
    """
    try:
        err = _require_spss(ctx)
        if err:
            return f"Error: {err}"

        from spss_mcp.spss_runner import run_syntax

        syntax = f"GET FILE='{file_path.replace(chr(92), '/')}'.\n"
        syntax += f"MIXED {dependent}"

        if fixed_effects:
            syntax += f" WITH {' '.join(fixed_effects)}\n"
        else:
            syntax += "\n"

        # Fixed effects
        if fixed_effects:
            syntax += f"  /FIXED={' '.join(fixed_effects)}\n"
        else:
            syntax += "  /FIXED=INTERCEPT\n"

        # Random effects
        if random_effects and subject:
            random_spec = ' '.join(random_effects) if random_effects else "INTERCEPT"
            syntax += f"  /RANDOM={random_spec} | SUBJECT({subject})"
            if covtype_random:
                syntax += f" COVTYPE({covtype_random})\n"
            else:
                syntax += "\n"

        # Repeated measures
        if repeated and subject:
            syntax += f"  /REPEATED={repeated} | SUBJECT({subject})"
            if repeated_type:
                syntax += f" COVTYPE({repeated_type})\n"
            else:
                syntax += " COVTYPE(AR1)\n"

        syntax += f"  /METHOD={method}\n"
        syntax += "  /PRINT=SOLUTION TESTCOV\n"
        syntax += "  /CRITERIA=CIN(95) MXITER(100) MXSTEP(10) SCORING(1) SINGULAR(0.000000000001) HCONVERGE(0, ABSOLUTE) LCONVERGE(0, ABSOLUTE) PCONVERGE(0.000001, ABSOLUTE).\n"

        result = await run_syntax(syntax, data_file=file_path)
        return _format_run_result(result)
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_mixed error: {e}")
        return f"Error: {e}"


@mcp.tool(
    name="spss_genlinmixed",
    description=(
        "Run generalized linear mixed model combining GLM with random effects. "
        "Supports non-normal outcomes with hierarchical structure. "
        "Requires IBM SPSS Statistics to be installed."
    ),
)
async def spss_genlinmixed(
    file_path: str,
    dependent: str,
    fixed_effects: list[str],
    random_effects: Optional[list[str]] = None,
    subject: Optional[str] = None,
    distribution: Literal["NORMAL", "BINOMIAL", "POISSON", "GAMMA", "NEGBIN"] = "NORMAL",
    link: Optional[str] = None,
    ctx: Context = None,
) -> str:
    """
    Generalized linear mixed model for non-normal hierarchical data.

    Args:
        file_path: Path to .sav file
        dependent: Dependent variable
        fixed_effects: List of fixed effect predictors
        random_effects: List of random effect variables
        subject: Subject/grouping variable
        distribution: Distribution family (NORMAL/BINOMIAL/POISSON/GAMMA/NEGBIN)
        link: Link function (auto if None)
    """
    try:
        err = _require_spss(ctx)
        if err:
            return f"Error: {err}"

        from spss_mcp.spss_runner import run_syntax

        syntax = f"GET FILE='{file_path.replace(chr(92), '/')}'.\n"
        syntax += f"GENLINMIXED\n"
        syntax += f"  /DATA_STRUCTURE SUBJECTS={subject}\n" if subject else ""
        syntax += f"  /FIELDS TARGET={dependent} TRIALS=NONE OFFSET=NONE\n"

        if fixed_effects:
            syntax += f"  /FIXED EFFECTS={' '.join(fixed_effects)} USE_INTERCEPT=TRUE\n"
        else:
            syntax += "  /FIXED USE_INTERCEPT=TRUE\n"

        if random_effects and subject:
            random_spec = ' '.join(random_effects)
            syntax += f"  /RANDOM EFFECTS={random_spec} USE_INTERCEPT=TRUE SUBJECTS={subject}\n"

        syntax += f"  /BUILD_OPTIONS TARGET_CATEGORY_ORDER=ASCENDING INPUTS_CATEGORY_ORDER=ASCENDING MAX_ITERATIONS=100 CONFIDENCE_LEVEL=95 DF_METHOD=RESIDUAL COVB=ROBUST\n"
        syntax += f"  /TARGET_OPTIONS DISTRIBUTION={distribution}"

        if link:
            syntax += f" LINK={link}\n"
        else:
            syntax += "\n"

        syntax += "  /PRINT SOLUTION.\n"

        result = await run_syntax(syntax, data_file=file_path)
        return _format_run_result(result)
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_genlinmixed error: {e}")
        return f"Error: {e}"


# ─── Survival Analysis ────────────────────────────────────────────────────────

@mcp.tool(
    name="spss_cox_regression",
    description=(
        "Run Cox proportional hazards regression for survival analysis. "
        "Supports time-dependent covariates, stratification, and model diagnostics. "
        "Requires IBM SPSS Statistics to be installed."
    ),
)
async def spss_cox_regression(
    file_path: str,
    time_variable: str,
    status_variable: str,
    status_event_value: int | str,
    predictors: list[str],
    method: Literal["ENTER", "FSTEP", "BSTEP"] = "ENTER",
    categorical: Optional[list[str]] = None,
    strata: Optional[list[str]] = None,
    save_survival: bool = False,
    ctx: Context = None,
) -> str:
    """
    Cox proportional hazards regression for survival data.

    Args:
        file_path: Path to .sav file
        time_variable: Time to event variable
        status_variable: Status variable (censored/event)
        status_event_value: Value indicating event occurred (e.g., 1)
        predictors: List of predictor variables
        method: Variable selection method (ENTER/FSTEP/BSTEP)
        categorical: List of categorical predictors
        strata: Stratification variables
        save_survival: Save survival function and hazard
    """
    try:
        err = _require_spss(ctx)
        if err:
            return f"Error: {err}"

        from spss_mcp.spss_runner import run_syntax

        syntax = f"GET FILE='{file_path.replace(chr(92), '/')}'.\n"
        syntax += f"COXREG {time_variable}\n"
        syntax += f"  /STATUS={status_variable}({status_event_value})\n"
        syntax += f"  /METHOD={method} {' '.join(predictors)}\n"

        if categorical:
            syntax += f"  /CATEGORICAL={' '.join(categorical)}\n"

        if strata:
            syntax += f"  /STRATA={' '.join(strata)}\n"

        if save_survival:
            syntax += "  /SAVE=SURVIVAL HAZARD\n"

        syntax += "  /PRINT=CI(95)\n"
        syntax += "  /CRITERIA=PIN(.05) POUT(.10) ITERATE(20).\n"

        result = await run_syntax(syntax, data_file=file_path)
        return _format_run_result(result)
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_cox_regression error: {e}")
        return f"Error: {e}"


@mcp.tool(
    name="spss_kaplan_meier",
    description=(
        "Run Kaplan-Meier survival analysis with log-rank test. "
        "Produces survival curves and compares groups. "
        "Requires IBM SPSS Statistics to be installed."
    ),
)
async def spss_kaplan_meier(
    file_path: str,
    time_variable: str,
    status_variable: str,
    status_event_value: int | str,
    strata: Optional[str] = None,
    compare_method: Literal["LOGRANK", "BRESLOW", "TARONE"] = "LOGRANK",
    percentiles: Optional[list[int]] = None,
    ctx: Context = None,
) -> str:
    """
    Kaplan-Meier survival analysis and group comparison.

    Args:
        file_path: Path to .sav file
        time_variable: Time to event variable
        status_variable: Status variable (censored/event)
        status_event_value: Value indicating event occurred
        strata: Grouping variable for comparison
        compare_method: Group comparison method (LOGRANK/BRESLOW/TARONE)
        percentiles: Survival percentiles to estimate (e.g., [25, 50, 75])
    """
    try:
        err = _require_spss(ctx)
        if err:
            return f"Error: {err}"

        from spss_mcp.spss_runner import run_syntax

        syntax = f"GET FILE='{file_path.replace(chr(92), '/')}'.\n"
        syntax += f"KM {time_variable}"

        if strata:
            syntax += f" BY {strata}\n"
        else:
            syntax += "\n"

        syntax += f"  /STATUS={status_variable}({status_event_value})\n"

        if strata:
            syntax += f"  /COMPARE={compare_method}\n"

        syntax += "  /PRINT=TABLE MEAN\n"

        if percentiles:
            pct_str = ' '.join(map(str, percentiles))
            syntax += f"  /PERCENTILES={pct_str}\n"

        syntax += "  /PLOT=SURVIVAL.\n"

        result = await run_syntax(syntax, data_file=file_path)
        return _format_run_result(result)
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_kaplan_meier error: {e}")
        return f"Error: {e}"


# ─── Discriminant Analysis & Clustering ───────────────────────────────────────

@mcp.tool(
    name="spss_discriminant",
    description=(
        "Run discriminant analysis to classify cases into groups. "
        "Supports stepwise selection and cross-validation. "
        "Requires IBM SPSS Statistics to be installed."
    ),
)
async def spss_discriminant(
    file_path: str,
    groups: str,
    predictors: list[str],
    method: Literal["DIRECT", "WILKS", "MAHAL"] = "DIRECT",
    priors: Literal["EQUAL", "SIZE"] = "EQUAL",
    save_scores: bool = False,
    save_class: bool = False,
    ctx: Context = None,
) -> str:
    """
    Discriminant analysis for group classification.

    Args:
        file_path: Path to .sav file
        groups: Grouping variable
        predictors: List of discriminating variables
        method: Variable selection (DIRECT/WILKS/MAHAL)
        priors: Prior probabilities (EQUAL/SIZE)
        save_scores: Save discriminant scores
        save_class: Save predicted group membership
    """
    try:
        err = _require_spss(ctx)
        if err:
            return f"Error: {err}"

        from spss_mcp.spss_runner import run_syntax

        syntax = f"GET FILE='{file_path.replace(chr(92), '/')}'.\n"
        syntax += f"DISCRIMINANT\n"
        syntax += f"  /GROUPS={groups}\n"
        syntax += f"  /VARIABLES={' '.join(predictors)}\n"
        syntax += f"  /ANALYSIS ALL\n"
        syntax += f"  /METHOD={method}\n"
        syntax += f"  /PRIORS={priors}\n"

        if save_scores or save_class:
            save_opts = []
            if save_scores:
                save_opts.append("SCORES")
            if save_class:
                save_opts.append("CLASS")
            syntax += f"  /SAVE={' '.join(save_opts)}\n"

        syntax += "  /STATISTICS=MEAN STDDEV UNIVF BOXM COEF RAW CORR COV GCOV TABLE\n"
        syntax += "  /CLASSIFY=NONMISSING POOLED.\n"

        result = await run_syntax(syntax, data_file=file_path)
        return _format_run_result(result)
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_discriminant error: {e}")
        return f"Error: {e}"


@mcp.tool(
    name="spss_cluster_hierarchical",
    description=(
        "Run hierarchical cluster analysis with dendrogram. "
        "Supports multiple linkage methods and distance measures. "
        "Requires IBM SPSS Statistics to be installed."
    ),
)
async def spss_cluster_hierarchical(
    file_path: str,
    variables: list[str],
    method: Literal["BAVERAGE", "WAVERAGE", "SINGLE", "COMPLETE", "CENTROID", "MEDIAN", "WARD"] = "WARD",
    measure: Literal["SEUCLID", "EUCLID", "COSINE", "PEARSON", "CHEBYCHEV", "BLOCK", "MINKOWSKI", "CUSTOMIZED"] = "SEUCLID",
    id_variable: Optional[str] = None,
    dendrogram: bool = True,
    ctx: Context = None,
) -> str:
    """
    Hierarchical cluster analysis.

    Args:
        file_path: Path to .sav file
        variables: List of clustering variables
        method: Linkage method (BAVERAGE/WAVERAGE/SINGLE/COMPLETE/CENTROID/MEDIAN/WARD)
        measure: Distance measure (SEUCLID/EUCLID/COSINE/PEARSON/etc)
        id_variable: Case identifier variable for labeling
        dendrogram: Generate dendrogram plot
    """
    try:
        err = _require_spss(ctx)
        if err:
            return f"Error: {err}"

        from spss_mcp.spss_runner import run_syntax

        syntax = f"GET FILE='{file_path.replace(chr(92), '/')}'.\n"
        syntax += f"CLUSTER {' '.join(variables)}\n"

        if id_variable:
            syntax += f"  /ID={id_variable}\n"

        syntax += f"  /METHOD={method}\n"
        syntax += f"  /MEASURE={measure}\n"
        syntax += "  /PRINT=SCHEDULE CLUSTER(2,4)\n"

        if dendrogram:
            syntax += "  /PLOT=DENDROGRAM VICICLE.\n"

        result = await run_syntax(syntax, data_file=file_path)
        return _format_run_result(result)
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_cluster_hierarchical error: {e}")
        return f"Error: {e}"


@mcp.tool(
    name="spss_twostep_cluster",
    description=(
        "Run two-step cluster analysis with automatic cluster number determination. "
        "Handles large datasets and mixed variable types. "
        "Requires IBM SPSS Statistics to be installed."
    ),
)
async def spss_twostep_cluster(
    file_path: str,
    continuous: Optional[list[str]] = None,
    categorical: Optional[list[str]] = None,
    distance: Literal["EUCLID", "CHISQ"] = "EUCLID",
    num_clusters: Optional[int] = None,
    max_clusters: int = 15,
    outlier_handling: bool = True,
    ctx: Context = None,
) -> str:
    """
    Two-step cluster analysis for automatic clustering.

    Args:
        file_path: Path to .sav file
        continuous: List of continuous variables
        categorical: List of categorical variables
        distance: Distance measure (EUCLID for continuous, CHISQ for categorical)
        num_clusters: Fixed number of clusters (None for auto)
        max_clusters: Maximum clusters to consider if auto
        outlier_handling: Enable outlier treatment
    """
    try:
        err = _require_spss(ctx)
        if err:
            return f"Error: {err}"

        from spss_mcp.spss_runner import run_syntax

        if not continuous and not categorical:
            return "Error: Must specify at least one continuous or categorical variable"

        syntax = f"GET FILE='{file_path.replace(chr(92), '/')}'.\n"
        syntax += "TWOSTEP CLUSTER\n"

        if continuous:
            syntax += f"  /CONTINUOUS {' '.join(continuous)}\n"

        if categorical:
            syntax += f"  /CATEGORICAL {' '.join(categorical)}\n"

        syntax += f"  /DISTANCE={distance}\n"

        if num_clusters:
            syntax += f"  /NUMCLUSTERS=FIXED({num_clusters})\n"
        else:
            syntax += f"  /NUMCLUSTERS=AUTO({max_clusters})\n"

        if outlier_handling:
            syntax += "  /OUTLIERS=YES\n"

        syntax += "  /PRINT=MODELINFO CLUSTERINFO\n"
        syntax += "  /PLOT=SILHOUETTE.\n"

        result = await run_syntax(syntax, data_file=file_path)
        return _format_run_result(result)
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_twostep_cluster error: {e}")
        return f"Error: {e}"


# ─── Multivariate ANOVA ───────────────────────────────────────────────────────

@mcp.tool(
    name="spss_manova",
    description=(
        "Run multivariate analysis of variance (MANOVA) for multiple dependent variables. "
        "Tests multivariate effects and provides univariate follow-ups. "
        "Requires IBM SPSS Statistics to be installed."
    ),
)
async def spss_manova(
    file_path: str,
    dependents: list[str],
    factors: list[str],
    covariates: Optional[list[str]] = None,
    method: Literal["SSTYPE1", "SSTYPE2", "SSTYPE3", "SSTYPE4"] = "SSTYPE3",
    print_multivariate: bool = True,
    print_univariate: bool = True,
    ctx: Context = None,
) -> str:
    """
    Multivariate analysis of variance.

    Args:
        file_path: Path to .sav file
        dependents: List of dependent variables
        factors: List of factor variables
        covariates: List of covariate variables
        method: Sum of squares type (SSTYPE1/2/3/4)
        print_multivariate: Print multivariate tests
        print_univariate: Print univariate tests
    """
    try:
        err = _require_spss(ctx)
        if err:
            return f"Error: {err}"

        from spss_mcp.spss_runner import run_syntax

        syntax = f"GET FILE='{file_path.replace(chr(92), '/')}'.\n"
        syntax += f"MANOVA {' '.join(dependents)} BY {' '.join(factors)}"

        if covariates:
            syntax += f" WITH {' '.join(covariates)}\n"
        else:
            syntax += "\n"

        syntax += f"  /METHOD={method}\n"

        print_opts = []
        if print_multivariate:
            print_opts.append("SIGNIF(MULTIV)")
        if print_univariate:
            print_opts.append("SIGNIF(UNIV)")

        if print_opts:
            syntax += f"  /PRINT={' '.join(print_opts)}\n"

        syntax += "  /DESIGN.\n"

        result = await run_syntax(syntax, data_file=file_path)
        return _format_run_result(result)
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_manova error: {e}")
        return f"Error: {e}"


@mcp.tool(
    name="spss_glm_univariate",
    description=(
        "Run univariate general linear model (GLM) with factorial designs. "
        "Supports estimated marginal means, contrasts, and post-hoc tests. "
        "Requires IBM SPSS Statistics to be installed."
    ),
)
async def spss_glm_univariate(
    file_path: str,
    dependent: str,
    factors: list[str],
    covariates: Optional[list[str]] = None,
    emmeans: Optional[list[str]] = None,
    posthoc: Optional[list[str]] = None,
    posthoc_method: Optional[str] = None,
    save_predicted: bool = False,
    ctx: Context = None,
) -> str:
    """
    Univariate general linear model for factorial designs.

    Args:
        file_path: Path to .sav file
        dependent: Dependent variable
        factors: List of factor variables
        covariates: List of covariate variables
        emmeans: Variables for estimated marginal means
        posthoc: Variables for post-hoc comparisons
        posthoc_method: Post-hoc method (TUKEY/BONFERRONI/SCHEFFE/etc)
        save_predicted: Save predicted values and residuals
    """
    try:
        err = _require_spss(ctx)
        if err:
            return f"Error: {err}"

        from spss_mcp.spss_runner import run_syntax

        syntax = f"GET FILE='{file_path.replace(chr(92), '/')}'.\n"
        syntax += f"UNIANOVA {dependent} BY {' '.join(factors)}"

        if covariates:
            syntax += f" WITH {' '.join(covariates)}\n"
        else:
            syntax += "\n"

        if emmeans:
            for var in emmeans:
                syntax += f"  /EMMEANS=TABLES({var})\n"

        if posthoc and posthoc_method:
            posthoc_vars = ' '.join(posthoc)
            syntax += f"  /POSTHOC={posthoc_vars}({posthoc_method})\n"

        if save_predicted:
            syntax += "  /SAVE=PRED RESID\n"

        syntax += "  /PRINT=DESCRIPTIVE ETASQ HOMOGENEITY\n"
        syntax += "  /CRITERIA=ALPHA(.05)\n"
        syntax += "  /DESIGN.\n"

        result = await run_syntax(syntax, data_file=file_path)
        return _format_run_result(result)
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_glm_univariate error: {e}")
        return f"Error: {e}"
