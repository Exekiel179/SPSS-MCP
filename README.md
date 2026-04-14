# SPSS-MCP

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-lightgrey.svg)]()
[![MCP](https://img.shields.io/badge/protocol-MCP-green.svg)](https://modelcontextprotocol.io)

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that gives AI assistants direct access to **IBM SPSS Statistics** for statistical analysis.

Describe your analysis in plain language — SPSS-MCP translates it into SPSS syntax, runs it against the real SPSS engine, and returns Markdown-formatted results.

> **🚀 快速开始：** 查看 [QUICK_START.md](QUICK_START.md) 或直接运行 `install.bat` 一键安装

---

## Requirements

- Windows 10/11
- Python 3.10+
- IBM SPSS Statistics (version 20-31)
- Claude Code with MCP support

---

## Quick Install

### One-Click (Recommended)

```bash
git clone https://github.com/Exekiel179/SPSS-MCP.git
cd SPSS-MCP
install.bat
```

Then restart Claude Code. Done!

### Manual Install

```bash
# 1. Install
pip install -e .

# 2. Get config
spss-mcp setup-info

# 3. Add config to Claude Code (Ctrl+,)
# 4. Restart Claude Code
```

---

## Configuration

### Basic Setup

Add to Claude Code settings (`Ctrl+,` → search `mcpServers`):

```json
{
  "mcpServers": {
    "spss": {
      "command": "spss-mcp",
      "args": ["serve", "--transport", "stdio"]
    }
  }
}
```

### SPSS Path (if not auto-detected)

Create `.env` file:

```ini
SPSS_INSTALL_PATH=C:\Program Files\IBM\SPSS Statistics\31
```

### Optional: Install Skills

Skills make analysis more reliable and auto-save results:

```cmd
set SKILLS_DIR=%USERPROFILE%\.claude\skills
xcopy /E /I skills\spss-analyst "%SKILLS_DIR%\spss-analyst"
xcopy /E /I skills\spss-mcp-guard "%SKILLS_DIR%\spss-mcp-guard"
```

Restart Claude Code after installation.

---

## Usage

Just describe your analysis in natural language:

```
请对 data.sav 进行描述性统计
```

```
分析 age 和 income 的相关性
```

```
用 t 检验比较男女收入差异
```

Claude will:
1. Read your data file
2. Generate SPSS syntax
3. Execute the analysis
4. Return formatted results
5. Save `.spv` and `.sps` files

---

## Output Files

Every analysis produces:

| File | Description |
|------|-------------|
| `.spv` | SPSS Viewer file (open in SPSS for full charts) |
| `.sps` | SPSS syntax file (the exact commands that ran) |

**Default location:** `%TEMP%\spss-mcp\results\`

**With skills installed:** `spss_result/` in your working directory

---

## Available Tools

### File & Data (9 tools)
- `spss_check_status` - Check server capabilities
- `spss_list_files` - List .sav files
- `spss_list_variables` - List variables with labels
- `spss_read_metadata` - Read variable types and labels
- `spss_read_data` - Preview data rows
- `spss_file_summary` - Get file statistics
- `spss_import_csv` - Convert CSV to .sav

### Basic Statistics (9 tools)
- `spss_frequencies` - Frequency tables
- `spss_descriptives` - Mean, SD, min, max
- `spss_crosstabs` - Contingency tables with chi-square
- `spss_t_test` - Independent/paired/one-sample t-tests
- `spss_anova` - One-way ANOVA with post-hoc
- `spss_correlations` - Pearson/Spearman correlations
- `spss_regression` - Linear regression
- `spss_normality_outliers` - Normality tests
- `spss_nonparametric_tests` - Mann-Whitney, Wilcoxon, Kruskal-Wallis

### Advanced Analysis (18 tools)
- Logistic regression (binary/multinomial/ordinal)
- Generalized linear models (GLM, GENLIN, GENLINMIXED)
- Mixed models (MIXED)
- Survival analysis (Cox regression, Kaplan-Meier)
- Multivariate analysis (Factor, MANOVA, Discriminant)
- Clustering (Hierarchical, Two-step)
- Reliability (Cronbach's α)
- And more...

**Total: 36 tools** across 8 categories

---

## Troubleshooting

### SPSS not detected

Run `spss-mcp status`. If SPSS shows `✗`:

1. Create `.env` file with SPSS path
2. Restart Claude Code

### Analysis timeout

Increase timeout in `.env`:

```ini
SPSS_TIMEOUT=300
```

### Skills not working

1. Verify files exist:
   ```
   %USERPROFILE%\.claude\skills\spss-analyst\SKILL.md
   %USERPROFILE%\.claude\skills\spss-mcp-guard\SKILL.md
   ```
2. Restart Claude Code

### MCP server not connecting

1. Check JSON syntax in settings
2. Verify `spss-mcp` command works in terminal
3. Restart Claude Code

---

## Platform Support

| Platform | File Tools | Analysis Tools |
|----------|------------|----------------|
| Windows 10/11 | ✓ | ✓ (requires SPSS) |
| macOS | ✓ | ✗ |
| Linux | ✓ | ✗ |

Analysis tools require SPSS XD API (Windows-only).

---

## Development

```bash
# Compile check
python -m compileall src/spss_mcp

# Run tests
pytest

# Format code
black src/ tests/
isort src/ tests/

# CLI commands
spss-mcp status       # Check environment
spss-mcp setup-info   # Generate config
```

---

## License

MIT — see [LICENSE](LICENSE)

---

## Links

- **Quick Start**: [QUICK_START.md](QUICK_START.md)
- **Issues**: https://github.com/Exekiel179/SPSS-MCP/issues
- **MCP Protocol**: https://modelcontextprotocol.io
