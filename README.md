# SPSS-MCP

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-lightgrey.svg)]()
[![MCP](https://img.shields.io/badge/protocol-MCP-green.svg)](https://modelcontextprotocol.io)

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that gives AI assistants (Claude Code, Claude Desktop, etc.) direct access to **IBM SPSS Statistics** for statistical analysis.

Ask your AI assistant in plain language — SPSS-MCP translates the request into SPSS syntax, runs it against the real SPSS engine, and returns Markdown-formatted results.

---

## Features

- **33 statistical analysis tools** covering the full range of psychology and social science research methods
- **Uses the real SPSS engine** — results are identical to what you'd get clicking through SPSS menus
- **File-only mode** — read `.sav` metadata and preview data even without SPSS installed (via `pyreadstat`)
- **Persistent artifacts** — every run saves a `.spv` viewer file and a `.sps` syntax file for auditing and reproducibility
- **Auto-detects SPSS** via Windows registry; no manual path configuration needed in most cases

---

## Requirements

| Requirement | Notes |
|---|---|
| Windows 10/11 | SPSS XD API is Windows-only |
| Python 3.10+ | |
| IBM SPSS Statistics 20–31 | For analysis tools; file-only mode works without it |

---

## Installation

### 1. Clone and install

```bash
git clone https://github.com/Exekiel179/SPSS-MCP.git
cd SPSS-MCP
pip install -e .
```

### 2. Verify

```bash
spss-mcp status
```

Expected output (with SPSS installed):

```
pyreadstat : ✓ 1.2.x
pandas     : ✓ 2.x.x
SPSS       : ✓ C:\Program Files\IBM\SPSS Statistics\31\stats.exe
SPSS Python: ✓ ...Python3\python.exe
```

### 3. (Optional) Configure

Copy `.env.example` to `.env` and adjust if auto-detection doesn't find your SPSS:

```bash
copy .env.example .env
```

Relevant settings:

```ini
# Explicit SPSS install path (skip if auto-detect works)
SPSS_INSTALL_PATH=C:\Program Files\IBM\SPSS Statistics\31

# Timeout for long-running analyses (seconds)
SPSS_TIMEOUT=120

# Force file-only mode (no SPSS execution)
# SPSS_NO_SPSS=1
```

---

## Connect to Claude Code

### Automatic (recommended)

```bash
spss-mcp setup-info
```

This prints a ready-to-paste JSON snippet for your Claude Code `settings.json`.

### Manual

Add to `%APPDATA%\Claude\claude_desktop_config.json` (Claude Desktop) or your Claude Code `settings.json`:

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

Restart Claude Code / Claude Desktop. You should see **spss** in the connected MCP servers list.

---

## Usage Examples

Once connected, just describe what you want in plain language:

> "Run a reliability analysis on items q1 through q20 in `survey.sav`"

> "Check if the age variable is normally distributed, then run an independent-samples t-test comparing scores by group"

> "Fit a mixed-effects model with random intercepts for participant ID, predicting anxiety from time and condition"

SPSS-MCP will call the right tools, execute the SPSS syntax, and return the results as formatted tables.

---

## Available Tools (33 total)

### File & Data (6)
| Tool | Description |
|---|---|
| `spss_check_status` | Check server capabilities and SPSS version |
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
| `spss_normality_outliers` | Shapiro-Wilk, K-S tests + outlier detection |
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
| `spss_glm_univariate` | Univariate GLM with factorial designs and EMMs |
| `spss_repeated_measures_anova` | Repeated measures ANOVA + Greenhouse-Geisser |

### Clustering (2)
| Tool | Description |
|---|---|
| `spss_cluster_hierarchical` | Hierarchical clustering with dendrogram |
| `spss_twostep_cluster` | Two-step cluster analysis (auto cluster count) |

### Reliability & Scale (2)
| Tool | Description |
|---|---|
| `spss_reliability_alpha` | Cronbach's α + item-deleted statistics |
| `spss_compute_scale_score` | Scale scores (SUM / MEAN + reverse coding) |

### Utility (2)
| Tool | Description |
|---|---|
| `spss_run_syntax` | Execute arbitrary SPSS syntax |
| `spss_validate_syntax` | Validate syntax without running it |

---

## Output Files

Each analysis saves two files to `SPSS_RESULTS_DIR` (default: `%TEMP%\spss-mcp\results\`):

| File | Description |
|---|---|
| `*.spv` | SPSS Viewer file — open in IBM SPSS Statistics for full formatted output |
| `*.sps` | SPSS syntax file — the exact syntax that was run (for reproducibility) |

---

## Troubleshooting

**SPSS not detected**

Run `spss-mcp status` to see what paths were searched. Set `SPSS_INSTALL_PATH` explicitly in `.env` if needed.

**Timeout errors on large datasets**

Increase `SPSS_TIMEOUT` in `.env` (e.g., `SPSS_TIMEOUT=300`).

**File-only mode only**

Without IBM SPSS Statistics installed, only the 6 file & data tools work. Analysis tools return an error message explaining this.

---

## Development

```bash
# Compile check
python -m compileall src/spss_mcp

# Run CLI
spss-mcp status
spss-mcp setup-info
```

---

## License

MIT — see [LICENSE](LICENSE)
