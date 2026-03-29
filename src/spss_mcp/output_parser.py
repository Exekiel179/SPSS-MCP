"""
Parse SPSS text output into GitHub-flavored Markdown.

SPSS text output (produced via OMS FORMAT=TEXT) uses fixed-width tables with
pipe/dash borders and has a characteristic structure that this parser converts
to Markdown tables using tabulate.
"""

import re
from typing import Optional


# ─── Error / warning extraction ───────────────────────────────────────────────

_ERROR_RE = re.compile(
    r"^>?\s*Error\s*#?\s*(\d+)[^\n]*\n((?:.*\n)*?)(?=\n|>|\Z)",
    re.MULTILINE | re.IGNORECASE,
)
_WARNING_RE = re.compile(
    r"^>?\s*Warning\s*#?\s*(\d+)[^\n]*\n((?:.*\n)*?)(?=\n|>|\Z)",
    re.MULTILINE | re.IGNORECASE,
)


def extract_errors(text: str) -> list[str]:
    errors = []
    for m in _ERROR_RE.finditer(text):
        errors.append(f"Error #{m.group(1)}: {m.group(2).strip()}")
    return errors


def extract_warnings(text: str) -> list[str]:
    warnings = []
    for m in _WARNING_RE.finditer(text):
        warnings.append(f"Warning #{m.group(1)}: {m.group(2).strip()}")
    return warnings


# ─── Fixed-width table detection ──────────────────────────────────────────────

def _is_separator_line(line: str) -> bool:
    """A line consisting mostly of dashes (SPSS table border)."""
    stripped = line.strip()
    if not stripped:
        return False
    non_dash = re.sub(r"[-\s|+]", "", stripped)
    return len(non_dash) == 0 and len(stripped) >= 3


def _split_fixed_row(line: str) -> list[str]:
    """Split a fixed-width SPSS row by whitespace (2+ spaces) or pipe chars."""
    # Split on two or more consecutive spaces, or on pipe chars
    parts = re.split(r"\s{2,}|\|", line)
    return [p.strip() for p in parts if p.strip()]


def _parse_spss_table_block(lines: list[str]) -> Optional[str]:
    """
    Attempt to parse a block of lines as an SPSS fixed-width table.
    Returns a Markdown table string, or None if the block doesn't look like a table.
    """
    # Filter out blank lines and pure separator lines to find data rows
    data_lines = []
    sep_count = 0
    for line in lines:
        if _is_separator_line(line):
            sep_count += 1
        elif line.strip():
            data_lines.append(line)

    # Need at least 2 data rows and at least 1 separator to be a table
    if sep_count < 1 or len(data_lines) < 2:
        return None

    rows = [_split_fixed_row(line) for line in data_lines]
    # Filter out empty rows
    rows = [r for r in rows if r]
    if len(rows) < 2:
        return None

    # First row is header
    header = rows[0]
    body = rows[1:]

    # Pad rows to same width
    max_cols = max(len(r) for r in [header] + body)
    header = header + [""] * (max_cols - len(header))
    body = [r + [""] * (max_cols - len(r)) for r in body]

    try:
        from tabulate import tabulate
        return tabulate(body, headers=header, tablefmt="github")
    except Exception:
        return None


# ─── Main parser ──────────────────────────────────────────────────────────────

def parse_spss_output(raw_text: str) -> str:
    """
    Convert raw SPSS text output to GitHub-flavored Markdown.

    Strategy:
    1. Extract and report errors / warnings
    2. Split output into blocks separated by blank lines
    3. For each block, try to parse as a table; fall back to preformatted text
    """
    if not raw_text or not raw_text.strip():
        return "_No output produced._"

    errors = extract_errors(raw_text)
    warnings = extract_warnings(raw_text)

    output_parts = []

    if errors:
        output_parts.append("### Errors\n")
        for e in errors:
            output_parts.append(f"- {e}")
        output_parts.append("")

    if warnings:
        output_parts.append("### Warnings\n")
        for w in warnings:
            output_parts.append(f"- {w}")
        output_parts.append("")

    # Split into blocks
    blocks = re.split(r"\n{2,}", raw_text)

    for block in blocks:
        lines = block.splitlines()
        if not lines or not block.strip():
            continue

        # Skip blocks that are purely errors/warnings (already captured)
        if all(
            re.match(r"^>?\s*(Error|Warning)", l, re.IGNORECASE) or not l.strip()
            for l in lines
        ):
            continue

        # Skip SPSS header boilerplate lines
        if any(
            kw in block
            for kw in [
                "IBM SPSS Statistics",
                "Licensed Materials",
                "SPSS for Windows",
                "Copyright IBM",
            ]
        ):
            continue

        parsed_table = _parse_spss_table_block(lines)
        if parsed_table:
            output_parts.append(parsed_table)
            output_parts.append("")
        else:
            # Preserve as preformatted text if it has meaningful content
            clean = block.strip()
            if clean and not _is_separator_line(clean):
                output_parts.append(clean)
                output_parts.append("")

    result = "\n".join(output_parts).strip()
    return result if result else "_Output contained no readable tables or text._"
