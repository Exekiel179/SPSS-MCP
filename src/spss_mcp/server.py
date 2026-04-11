"""
SPSS MCP server — all tool definitions.
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal, Optional

from fastmcp import Context, FastMCP

from spss_mcp.config import detect_capabilities, get_runtime_config
from spss_mcp.method_registry import (
    build_registered_syntax,
    get_method_definition,
    get_method_schema,
    list_registered_methods,
)


# ─── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def server_lifespan(server: FastMCP):
    sys.stderr.write("Starting SPSS MCP server...\n")
    caps = detect_capabilities()
    sys.stderr.write(
        f"  pyreadstat : {'available v' + caps['pyreadstat_version'] if caps['pyreadstat'] else 'NOT FOUND'}\n"
    )

    engine_status = "not started"
    if caps.get("spss"):
        sys.stderr.write(f"  SPSS found : {caps['spss_path']}\n")
        sys.stderr.write("  Launching persistent SPSS engine...\n")
        from spss_mcp.spss_engine import get_engine
        ok, msg = await get_engine().ensure_started()
        engine_status = "ready" if ok else f"failed — {msg}"
        sys.stderr.write(f"  SPSS engine: {engine_status}\n")
    else:
        sys.stderr.write("  SPSS batch : NOT FOUND (file-only mode)\n")

    yield {"capabilities": caps, "engine_status": engine_status}

    if caps.get("spss"):
        sys.stderr.write("  Stopping SPSS engine...\n")
        from spss_mcp.spss_engine import get_engine
        await get_engine().stop()
        sys.stderr.write("  SPSS engine stopped.\n")

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
    caps = detect_capabilities()
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
    output = result.get("output_markdown") or "_No output produced._"

    if result.get("error"):
        output = f"Error: {result['error']}\n\n{output}"

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


def _registered_method_summary(method) -> list[str]:
    return [
        method.tool_name,
        method.command_family,
        method.support_level,
        ", ".join(method.doc_tags),
    ]


async def _run_registered_method(tool_name: str, file_path: str, ctx: Context, **params) -> str:
    err = _require_spss(ctx)
    if err:
        return f"Error: {err}"

    from spss_mcp.spss_runner import run_syntax

    syntax = build_registered_syntax(tool_name, file_path, **params)
    result = await run_syntax(syntax)
    return _format_run_result(result)


# ─── Group 1: Status & File Tools (no SPSS needed) ───────────────────────────

@mcp.tool(
    name="spss_list_supported_methods",
    description=(
        "List registry-backed SPSS methods available for structured execution. "
        "Use this to discover cold methods that have schemas, templates, and coverage assertions."
    ),
)
async def spss_list_supported_methods(ctx: Context = None) -> str:
    try:
        from tabulate import tabulate

        rows = [_registered_method_summary(method) for method in list_registered_methods()]
        return tabulate(
            rows,
            headers=["Tool", "Command", "Support", "Tags"],
            tablefmt="github",
        )
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_list_supported_methods error: {e}")
        return f"Error: {e}"


@mcp.tool(
    name="spss_get_method_schema",
    description=(
        "Get the JSON schema for a registry-backed SPSS method. "
        "Useful for structured orchestration and parameter inspection before execution."
    ),
)
async def spss_get_method_schema(tool_name: str, ctx: Context = None) -> str:
    try:
        import json

        method = get_method_definition(tool_name)
        payload = {
            "tool_name": method.tool_name,
            "command_family": method.command_family,
            "support_level": method.support_level,
            "doc_tags": list(method.doc_tags),
            "assertions": list(method.assertions),
            "schema": get_method_schema(tool_name),
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)
    except KeyError:
        return f"Error: Unknown registry-backed method: {tool_name}"
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_get_method_schema error: {e}")
        return f"Error: {e}"


@mcp.tool(
    name="spss_get_method_support",
    description=(
        "Get support metadata for a registry-backed SPSS method, including command family, "
        "support tier, coverage assertions, and documentation tags."
    ),
)
async def spss_get_method_support(tool_name: str, ctx: Context = None) -> str:
    try:
        method = get_method_definition(tool_name)
        lines = [
            f"# {method.tool_name}",
            "",
            f"- Command family: `{method.command_family}`",
            f"- Support level: `{method.support_level}`",
            f"- Doc tags: {', '.join(method.doc_tags)}",
            f"- Coverage assertions: {', '.join(method.assertions)}",
        ]
        return "\n".join(lines)
    except KeyError:
        return f"Error: Unknown registry-backed method: {tool_name}"
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_get_method_support error: {e}")
        return f"Error: {e}"


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
        runtime = get_runtime_config()

        # Engine live status
        engine_alive = False
        if caps.get("spss"):
            from spss_mcp.spss_engine import get_engine
            engine_alive = get_engine().is_alive()

        engine_cell = (
            "✅ Running" if engine_alive
            else ("⚠️ Stopped (will auto-restart on next call)" if caps.get("spss") else "❌ N/A")
        )

        lines = [
            f"# SPSS MCP Server Status (v{__version__})\n",
            "## Capabilities\n",
            "| Capability | Status |",
            "|---|---|",
            f"| pyreadstat (.sav file I/O) | {'✅ v' + caps['pyreadstat_version'] if caps['pyreadstat'] else '❌ Not installed'} |",
            f"| pandas | {'✅ v' + caps['pandas_version'] if caps['pandas_version'] else '❌ Not installed'} |",
            f"| IBM SPSS Statistics | {'✅ Found' if caps['spss'] else '❌ Not found'} |",
            f"| Persistent SPSS engine | {engine_cell} |",
            "",
        ]
        lines.append(f"**Effective timeout:** `{runtime['timeout']}` seconds")
        lines.append(f"**Temp dir:** `{runtime['temp_dir']}`")
        lines.append(f"**Results dir:** `{runtime['results_dir']}`\n")
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


@mcp.tool(
    name="spss_import_csv",
    description=(
        "Convert a CSV file to SPSS .sav format directly using pandas + pyreadstat — "
        "no IBM SPSS Statistics installation required. "
        "Much faster than going through SPSS syntax because it bypasses the SPSS engine entirely. "
        "Saves the .sav file next to the CSV by default, or to a custom output_path."
    ),
)
async def spss_import_csv(
    csv_path: str,
    output_path: Optional[str] = None,
    encoding: str = "utf-8",
    delimiter: str = ",",
    column_labels: Optional[dict] = None,
    ctx: Context = None,
) -> str:
    """
    Parameters
    ----------
    csv_path : str
        Full path to the source CSV file.
    output_path : str, optional
        Destination .sav file path. Defaults to the same directory as the CSV with .sav extension.
    encoding : str, optional
        CSV file encoding (default: utf-8).
    delimiter : str, optional
        Column delimiter (default: comma).
    column_labels : dict, optional
        Mapping of column names to SPSS variable labels, e.g. {"age": "Age of respondent"}.
    """
    try:
        err = _require_pyreadstat(ctx)
        if err:
            return f"Error: {err}"

        from spss_mcp.sav_reader import import_csv_to_sav
        result = await import_csv_to_sav(
            csv_path=csv_path,
            output_path=output_path,
            encoding=encoding,
            delimiter=delimiter,
            column_labels=column_labels,
        )
        lines = [
            f"CSV imported successfully to `{result['output_path']}`",
            f"- Rows: {result['n_rows']}",
            f"- Variables: {result['n_cols']}",
            f"- Columns: {', '.join(result['column_names'])}",
        ]
        return "\n".join(lines)
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_import_csv error: {e}")
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
    filter_variable: Optional[str] = None,
    select_if: Optional[str] = None,
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
            filter_variable=filter_variable,
            select_if=select_if,
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
    try:
        return await _run_registered_method(
            "spss_logistic_regression",
            file_path,
            ctx,
            dependent=dependent,
            predictors=predictors,
            method=method,
            categorical=categorical,
            contrast=contrast,
            save_predicted=save_predicted,
            print_options=print_options,
        )
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
    try:
        return await _run_registered_method(
            "spss_ordinal_regression",
            file_path,
            ctx,
            dependent=dependent,
            predictors=predictors,
            link=link,
            categorical=categorical,
            save_predicted=save_predicted,
            test_parallel=test_parallel,
        )
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
    try:
        return await _run_registered_method(
            "spss_genlin",
            file_path,
            ctx,
            dependent=dependent,
            predictors=predictors,
            distribution=distribution,
            link=link,
            scale=scale,
            categorical=categorical,
            save_predicted=save_predicted,
        )
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
    try:
        return await _run_registered_method(
            "spss_mixed",
            file_path,
            ctx,
            dependent=dependent,
            fixed_effects=fixed_effects,
            random_effects=random_effects,
            subject=subject,
            repeated=repeated,
            repeated_type=repeated_type,
            method=method,
            covtype_random=covtype_random,
        )
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
    try:
        return await _run_registered_method(
            "spss_genlinmixed",
            file_path,
            ctx,
            dependent=dependent,
            fixed_effects=fixed_effects,
            random_effects=random_effects,
            subject=subject,
            distribution=distribution,
            link=link,
        )
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
    try:
        return await _run_registered_method(
            "spss_cox_regression",
            file_path,
            ctx,
            time_variable=time_variable,
            status_variable=status_variable,
            status_event_value=status_event_value,
            predictors=predictors,
            method=method,
            categorical=categorical,
            strata=strata,
            save_survival=save_survival,
        )
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
    try:
        return await _run_registered_method(
            "spss_kaplan_meier",
            file_path,
            ctx,
            time_variable=time_variable,
            status_variable=status_variable,
            status_event_value=status_event_value,
            strata=strata,
            compare_method=compare_method,
            percentiles=percentiles,
        )
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
    try:
        return await _run_registered_method(
            "spss_discriminant",
            file_path,
            ctx,
            groups=groups,
            predictors=predictors,
            method=method,
            priors=priors,
            save_scores=save_scores,
            save_class=save_class,
        )
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
    try:
        return await _run_registered_method(
            "spss_cluster_hierarchical",
            file_path,
            ctx,
            variables=variables,
            method=method,
            measure=measure,
            id_variable=id_variable,
            dendrogram=dendrogram,
        )
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
    try:
        return await _run_registered_method(
            "spss_twostep_cluster",
            file_path,
            ctx,
            continuous=continuous,
            categorical=categorical,
            distance=distance,
            num_clusters=num_clusters,
            max_clusters=max_clusters,
            outlier_handling=outlier_handling,
        )
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
    try:
        return await _run_registered_method(
            "spss_manova",
            file_path,
            ctx,
            dependents=dependents,
            factors=factors,
            covariates=covariates,
            method=method,
            print_multivariate=print_multivariate,
            print_univariate=print_univariate,
        )
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
    try:
        return await _run_registered_method(
            "spss_glm_univariate",
            file_path,
            ctx,
            dependent=dependent,
            factors=factors,
            covariates=covariates,
            emmeans=emmeans,
            posthoc=posthoc,
            posthoc_method=posthoc_method,
            save_predicted=save_predicted,
        )
    except Exception as e:
        if ctx:
            await ctx.error(f"spss_glm_univariate error: {e}")
        return f"Error: {e}"
