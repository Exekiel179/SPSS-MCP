# SPSS-MCP Release Notes

## v0.2.0 (2026-03-29)

### What's Included

- **33 statistical analysis tools** across 9 categories
- **File-only mode** (pyreadstat) — metadata and data reading without SPSS
- **Full SPSS execution mode** — statistical analysis via IBM SPSS XD API
- **Persistent artifacts** — `.spv` viewer files and `.sps` syntax files saved per run
- **FastMCP async architecture** — non-blocking I/O for all operations
- **Auto-detection** of IBM SPSS Statistics via Windows registry and common paths

### Tool Categories

| Category | Count |
|---|---|
| File & Data | 6 |
| Basic Statistics | 9 |
| Advanced Regression & GLM | 3 |
| Multilevel & Mixed Models | 2 |
| Survival Analysis | 2 |
| Multivariate Analysis | 5 |
| Clustering | 2 |
| Reliability & Scale | 2 |
| Utility | 2 |

### Known Limitations

- **Windows only** for SPSS execution (SPSS XD API constraint)
- Requires IBM SPSS Statistics to be installed for analysis tools
- File-only mode limited to metadata and data reading (no statistical computation)

### Verified On

- Windows 11
- IBM SPSS Statistics 31
- Python 3.10 / 3.11 / 3.12
- FastMCP 2.14+
