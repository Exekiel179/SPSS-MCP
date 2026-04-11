"""
pyreadstat-based async wrappers for reading SPSS .sav files.
No IBM SPSS Statistics installation required.
"""

import asyncio
from pathlib import Path
from typing import Optional

import pandas as pd
import pyreadstat
from tabulate import tabulate


def _check_file(file_path: str) -> Path:
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if p.suffix.lower() not in (".sav", ".por", ".zsav"):
        raise ValueError(f"Unsupported file type: {p.suffix}. Expected .sav, .zsav, or .por")
    return p


async def read_metadata(file_path: str) -> dict:
    """Read variable metadata from a .sav file without loading all data."""
    def _read():
        _check_file(file_path)
        _, meta = pyreadstat.read_sav(file_path, metadataonly=True)
        return meta

    meta = await asyncio.to_thread(_read)
    return {
        "column_names": meta.column_names,
        "column_labels": meta.column_labels,
        "column_names_to_labels": meta.column_names_to_labels,
        "value_labels": meta.variable_value_labels,
        "variable_types": meta.original_variable_types,
        "number_rows": meta.number_rows,
        "number_columns": meta.number_columns,
        "file_label": getattr(meta, "file_label", ""),
        "notes": getattr(meta, "notes", []),
    }


async def read_data(
    file_path: str,
    variables: Optional[list] = None,
    max_rows: int = 50,
    apply_value_labels: bool = True,
) -> dict:
    """Read data rows from a .sav file."""
    def _read():
        _check_file(file_path)
        kwargs = {
            "apply_value_formats": apply_value_labels,
            "row_limit": max_rows,
        }
        if variables:
            kwargs["usecols"] = variables
        df, meta = pyreadstat.read_sav(file_path, **kwargs)
        return df, meta

    df, meta = await asyncio.to_thread(_read)
    return {"dataframe": df, "meta": meta}


async def import_csv_to_sav(
    csv_path: str,
    output_path: Optional[str] = None,
    encoding: str = "utf-8",
    delimiter: str = ",",
    column_labels: Optional[dict] = None,
) -> dict:
    """
    Convert a CSV file to SPSS .sav format using pandas + pyreadstat.
    Does not require IBM SPSS Statistics to be installed.

    Returns a dict with keys: output_path, n_rows, n_cols, column_names.
    """
    import pandas as pd

    csv_p = Path(csv_path)
    if not csv_p.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    if output_path is None:
        output_path = str(csv_p.with_suffix(".sav"))

    def _convert():
        df = pd.read_csv(csv_p, encoding=encoding, sep=delimiter)
        write_kwargs: dict = {}
        if column_labels:
            write_kwargs["column_labels"] = column_labels
        pyreadstat.write_sav(df, output_path, **write_kwargs)
        return df.shape[0], df.shape[1], list(df.columns)

    n_rows, n_cols, col_names = await asyncio.to_thread(_convert)
    return {
        "output_path": output_path,
        "n_rows": n_rows,
        "n_cols": n_cols,
        "column_names": col_names,
    }


async def get_file_summary(file_path: str) -> dict:
    """Compute a quick summary: case count, variable count, descriptive stats."""
    def _read():
        _check_file(file_path)
        df, meta = pyreadstat.read_sav(file_path)
        return df, meta

    df, meta = await asyncio.to_thread(_read)
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    desc = df[numeric_cols].describe().round(4) if numeric_cols else pd.DataFrame()
    return {
        "n_cases": meta.number_rows,
        "n_variables": meta.number_columns,
        "variable_names": meta.column_names,
        "variable_labels": meta.column_names_to_labels,
        "descriptives_df": desc,
        "file_label": getattr(meta, "file_label", ""),
    }


# ─── Markdown formatters ───────────────────────────────────────────────────────

def format_metadata_as_markdown(meta_dict: dict) -> str:
    """Format variable metadata as Markdown tables."""
    lines = []
    n_rows = meta_dict.get("number_rows", "?")
    n_cols = meta_dict.get("number_columns", "?")
    file_label = meta_dict.get("file_label", "")
    if file_label:
        lines.append(f"**File label:** {file_label}\n")
    lines.append(f"**Cases:** {n_rows} | **Variables:** {n_cols}\n")

    # Variable list table
    names = meta_dict.get("column_names", [])
    labels_map = meta_dict.get("column_names_to_labels", {})
    types_map = meta_dict.get("variable_types", {})
    val_labels = meta_dict.get("value_labels", {})

    rows = []
    for name in names:
        label = labels_map.get(name, "")
        vtype = types_map.get(name, "")
        has_val_labels = "Yes" if name in val_labels else ""
        rows.append([name, label, vtype, has_val_labels])

    lines.append("## Variables\n")
    lines.append(
        tabulate(rows, headers=["Name", "Label", "Type", "Value Labels"], tablefmt="github")
    )

    # Value labels section
    if val_labels:
        lines.append("\n\n## Value Labels\n")
        for var, mapping in val_labels.items():
            lines.append(f"\n**{var}** ({labels_map.get(var, '')}):\n")
            vl_rows = [[k, v] for k, v in mapping.items()]
            lines.append(tabulate(vl_rows, headers=["Code", "Label"], tablefmt="github"))

    return "\n".join(lines)


def format_dataframe_as_markdown(df: pd.DataFrame, meta=None) -> str:
    """Format a pandas DataFrame as a GitHub-flavored Markdown table."""
    if df.empty:
        return "_No data rows returned._"
    return tabulate(df, headers="keys", tablefmt="github", showindex=False)


def format_summary_as_markdown(summary: dict) -> str:
    """Format file summary as Markdown."""
    lines = []
    file_label = summary.get("file_label", "")
    if file_label:
        lines.append(f"**File label:** {file_label}\n")
    lines.append(f"**Cases:** {summary['n_cases']} | **Variables:** {summary['n_variables']}\n")

    # Variable list
    names = summary["variable_names"]
    labels = summary["variable_labels"]
    var_rows = [[n, labels.get(n, "")] for n in names]
    lines.append("## Variables\n")
    lines.append(tabulate(var_rows, headers=["Name", "Label"], tablefmt="github"))

    # Descriptive statistics
    desc: pd.DataFrame = summary.get("descriptives_df", pd.DataFrame())
    if not desc.empty:
        lines.append("\n\n## Descriptive Statistics (numeric variables)\n")
        lines.append(tabulate(desc, headers="keys", tablefmt="github"))

    return "\n".join(lines)
