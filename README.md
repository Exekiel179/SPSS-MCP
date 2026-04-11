# SPSS-MCP

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-lightgrey.svg)]()
[![MCP](https://img.shields.io/badge/protocol-MCP-green.svg)](https://modelcontextprotocol.io)

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that gives AI assistants (Claude Code, Claude Desktop, etc.) direct access to **IBM SPSS Statistics** for statistical analysis.

Describe your analysis in plain language — SPSS-MCP translates it into SPSS syntax, runs it against the real SPSS engine, and returns Markdown-formatted results with persistent output files.

---

## Table of Contents

- [Requirements](#requirements)
- [Deployment](#deployment)
  - [1. Clone & Install](#1-clone--install)
  - [2. Verify Installation](#2-verify-installation)
  - [3. Configure Environment](#3-configure-environment)
  - [4. Connect to Claude Code](#4-connect-to-claude-code)
  - [5. Install Claude Code Skills](#5-install-claude-code-skills)
- [Output Files](#output-files)
- [Available Tools](#available-tools)
- [Troubleshooting](#troubleshooting)
- [Development](#development)

---

## Requirements

| Item | Version / Notes |
|---|---|
| OS | Windows 10 / 11 (SPSS XD API is Windows-only) |
| Python | 3.10 or higher |
| IBM SPSS Statistics | Version 20–31 — required for analysis tools; file-only mode works without it |
| Claude Code | Any version with MCP support |

---

## Deployment

### 1. Clone & Install

```bash
git clone https://github.com/Exekiel179/SPSS-MCP.git
cd SPSS-MCP
pip install -e .
```

> **Virtual environment (recommended)**
> ```bash
> python -m venv .venv
> .venv\Scripts\activate
> pip install -e .
> ```

---

### 2. Verify Installation

```bash
spss-mcp status
```

Expected output when SPSS is installed and detected:

```
pyreadstat : ✓ 1.2.x
pandas     : ✓ 2.x.x
SPSS       : ✓ C:\Program Files\IBM\SPSS Statistics\31\stats.exe
SPSS Python: ✓ C:\Program Files\IBM\SPSS Statistics\31\Python3\python.exe
```

If SPSS shows `✗`, see [Troubleshooting](#troubleshooting).

---

### 3. Configure Environment

Copy the example config and edit as needed:

```bash
copy .env.example .env
```

`.env` options:

```ini
# Explicit SPSS install path — only needed if auto-detection fails
# SPSS_INSTALL_PATH=C:\Program Files\IBM\SPSS Statistics\31

# Temporary work files directory (default: %TEMP%\spss-mcp)
# SPSS_TEMP_DIR=%TEMP%\spss-mcp

# Persistent output directory for .spv and .sps files (default: %TEMP%\spss-mcp\results)
# SPSS_RESULTS_DIR=%TEMP%\spss-mcp\results

# Timeout per analysis job in seconds (default: 120)
# SPSS_TIMEOUT=120

# Force file-only mode even if SPSS is installed (default: 0)
# SPSS_NO_SPSS=0
```

> Most settings have sensible defaults. You only need `.env` if auto-detection fails or you want to change output locations.

---

### 4. Connect to Claude Code

#### Option A — Claude Code (`settings.json`)

Open Claude Code settings (`Ctrl+,`) and add the `mcpServers` block:

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

If using a virtual environment, use the full path to the executable:

```json
{
  "mcpServers": {
    "spss": {
      "command": "C:\\path\\to\\SPSS-MCP\\.venv\\Scripts\\spss-mcp.exe",
      "args": ["serve", "--transport", "stdio"]
    }
  }
}
```

#### Option B — Claude Desktop (`claude_desktop_config.json`)

File location: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "spss": {
      "command": "spss-mcp",
      "args": ["serve", "--transport", "stdio"],
      "env": {
        "SPSS_INSTALL_PATH": "C:\\Program Files\\IBM\\SPSS Statistics\\31",
        "SPSS_TIMEOUT": "120"
      }
    }
  }
}
```

After saving, **restart Claude Code / Claude Desktop**. The `spss` server should appear in the connected MCP servers list.

To get a ready-to-paste snippet for your specific setup:

```bash
spss-mcp setup-info
```

---

### 5. Install Claude Code Skills

This repository includes two Claude Code skills that make SPSS-MCP significantly more reliable. Install them by copying the `skills/` directory into your Claude Code skills folder.

#### What the skills do

| Skill | Activates | Purpose |
|---|---|---|
| `spss-analyst` | Automatically on every SPSS tool call | Writes syntax, executes analyses, archives output |
| `spss-mcp-guard` | Automatically on every SPSS tool call | Catches known failure patterns before they cause silent errors |

**`spss-analyst`** follows an 8-step defensive workflow:

```
1. Check capabilities (spss_check_status)
2. Explore data (spss_file_summary / spss_read_metadata)
3. Smoke test for unfamiliar procedures
4. Write SPSS syntax following conventions
5. Execute with the appropriate MCP tool
6. Parse warnings, not just success flags
7. Interpret results in plain language
8. Archive output → spss_result/ in working directory  ←  automatic
```

After every analysis, the skill automatically saves:

```
spss_result/
├── 01_descriptives.sps     ← annotated syntax (Chinese header + English SPSS commands)
├── 01_descriptives.spv     ← SPSS Viewer output (open in IBM SPSS for full charts)
├── 02_regression.sps
├── 02_regression.spv
└── NN_<type>.*             ← globally-incrementing sequence number
```

**`spss-mcp-guard`** catches failure patterns documented in `skills/spss-mcp-guard/references/failure-patterns.md` — invalid subcommand keywords, timeout vs. syntax ambiguity, stale `.env` state, `success=True` with embedded warnings, and advanced procedure incompatibilities.

#### Installation

**Windows (Command Prompt):**

```cmd
set SKILLS_DIR=%USERPROFILE%\.claude\skills

xcopy /E /I skills\spss-analyst "%SKILLS_DIR%\spss-analyst"
xcopy /E /I skills\spss-mcp-guard "%SKILLS_DIR%\spss-mcp-guard"
```

**Windows (PowerShell):**

```powershell
$skillsDir = "$env:USERPROFILE\.claude\skills"

Copy-Item -Recurse -Force skills\spss-analyst  "$skillsDir\spss-analyst"
Copy-Item -Recurse -Force skills\spss-mcp-guard "$skillsDir\spss-mcp-guard"
```

**Verify:**

```
%USERPROFILE%\.claude\skills\
├── spss-analyst\
│   ├── SKILL.md
│   └── references\
│       ├── spss-syntax.md
│       ├── spss-mcp-tools.md
│       └── failure-patterns.md
└── spss-mcp-guard\
    ├── SKILL.md
    └── references\
        └── failure-patterns.md
```

Restart Claude Code after copying. Both skills activate automatically — no slash command needed.

---

## Output Files

Every analysis produces two persistent files:

| File | Description |
|---|---|
| `.spv` | SPSS Viewer file — open in IBM SPSS Statistics for full formatted tables, charts, and plots |
| `.sps` | SPSS syntax file — the exact syntax that ran, with a header documenting variables, parameters, and date |

**Default location** (without skills installed): `%TEMP%\spss-mcp\results\`

**With `spss-analyst` skill installed**: automatically copied to `spss_result/NN_<type>.*` in your current working directory after every analysis.

---

## Available Tools

36 tools across 8 categories.

### File & Data (9)

| Tool | Description |
|---|---|
| `spss_check_status` | Check server capabilities and SPSS version |
| `spss_list_supported_methods` | List registry-backed methods with support tags |
| `spss_get_method_schema` | Inspect a method's parameter schema |
| `spss_get_method_support` | Inspect coverage assertions for a method |
| `spss_list_files` | List `.sav` / `.zsav` files in a directory |
| `spss_list_variables` | List variables with labels (searchable) |
| `spss_read_metadata` | Read variable types, labels, value labels |
| `spss_read_data` | Preview data rows as a table |
| `spss_file_summary` | Case count, variable count, basic stats |

### Basic Statistics (9)

| Tool | Description |
|---|---|
| `spss_frequencies` | Frequency tables with optional statistics |
| `spss_descriptives` | Mean, SD, min, max, skewness, kurtosis |
| `spss_crosstabs` | Contingency tables with chi-square |
| `spss_t_test` | Independent / paired / one-sample t-tests |
| `spss_anova` | One-way ANOVA with post-hoc (Tukey, Bonferroni, LSD) |
| `spss_correlations` | Pearson / Spearman correlation matrix |
| `spss_regression` | Linear regression (ENTER, stepwise, etc.) |
| `spss_normality_outliers` | Shapiro-Wilk, K-S + outlier detection |
| `spss_nonparametric_tests` | Mann-Whitney U, Wilcoxon, Kruskal-Wallis |

### Advanced Regression & GLM (3)

| Tool | Description |
|---|---|
| `spss_logistic_regression` | Binary / multinomial logistic regression |
| `spss_ordinal_regression` | Ordinal regression (PLUM) |
| `spss_genlin` | Generalized linear models (Poisson, Gamma, etc.) |

### Multilevel & Mixed Models (2)

| Tool | Description |
|---|---|
| `spss_mixed` | Linear mixed-effects models with random effects |
| `spss_genlinmixed` | Generalized linear mixed models (GLMM) |

### Survival Analysis (2)

| Tool | Description |
|---|---|
| `spss_cox_regression` | Cox proportional hazards regression |
| `spss_kaplan_meier` | Kaplan-Meier curves with log-rank test |

### Multivariate Analysis (5)

| Tool | Description |
|---|---|
| `spss_factor` | Exploratory factor analysis (PCA / PAF + rotation) |
| `spss_discriminant` | Discriminant analysis |
| `spss_manova` | Multivariate ANOVA |
| `spss_glm_univariate` | Univariate GLM with factorial designs and estimated marginal means |
| `spss_repeated_measures_anova` | Repeated measures ANOVA with Greenhouse-Geisser correction |

### Clustering (2)

| Tool | Description |
|---|---|
| `spss_cluster_hierarchical` | Hierarchical clustering with dendrogram |
| `spss_twostep_cluster` | Two-step cluster analysis (automatic cluster count) |

### Reliability & Scale (2)

| Tool | Description |
|---|---|
| `spss_reliability_alpha` | Cronbach's α with item-deleted statistics |
| `spss_compute_scale_score` | Scale scores (SUM / MEAN with reverse coding) |

### Utility (3)

| Tool | Description |
|---|---|
| `spss_import_csv` | Import CSV to `.sav` format (no SPSS required) |
| `spss_run_syntax` | Execute arbitrary SPSS syntax |
| `spss_validate_syntax` | Validate syntax without running it |

---

## Troubleshooting

**SPSS not detected — `spss-mcp status` shows ✗**

Set the path explicitly in `.env`:
```ini
SPSS_INSTALL_PATH=C:\Program Files\IBM\SPSS Statistics\31
```
Restart the MCP server after saving.

**Analysis times out**

Increase the timeout in `.env`:
```ini
SPSS_TIMEOUT=300
```

**`success=True` but results look wrong or incomplete**

SPSS sometimes returns success with embedded warning blocks that contain the real error. Check the raw output for `Warning` or `Execution of this command stops` lines. The `spss-mcp-guard` skill catches the most common cases automatically.

**File-only mode — analysis tools not working**

Without IBM SPSS Statistics installed, only the 9 File & Data tools work. Install SPSS and re-run `spss-mcp status` to confirm detection.

**Skills not activating in Claude Code**

Verify the folders exist:
```
%USERPROFILE%\.claude\skills\spss-analyst\SKILL.md
%USERPROFILE%\.claude\skills\spss-mcp-guard\SKILL.md
```
Restart Claude Code after copying the skill folders.

**`spss_result/` not being created**

The output archiving is handled by the `spss-analyst` skill. Confirm the skill is installed (see above) and that Claude Code has been restarted since installation.

---

## Development

```bash
# Compile check
python -m compileall src/spss_mcp

# Run test suite
pytest

# Format
black src/ tests/
isort src/ tests/

# CLI
spss-mcp status       # environment check
spss-mcp setup-info   # print MCP config snippet for Claude Code / Claude Desktop
```

---

## License

MIT — see [LICENSE](LICENSE)
