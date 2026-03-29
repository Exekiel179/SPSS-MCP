# spss-mcp

A Model Context Protocol (MCP) server for IBM SPSS Statistics.

It provides:
- SPSS file tools (`.sav` / `.zsav`) via `pyreadstat`
- SPSS syntax execution via IBM SPSS batch/XD API
- Markdown output for LLM workflows
- Persistent SPSS artifacts (`.spv` viewer and executed `.sps` syntax files)
- **33 statistical analysis tools** covering basic to advanced methods

## Requirements

- Windows (SPSS execution mode)
- Python 3.10+
- IBM SPSS Statistics installed (for analysis tools)

> File-only tools (metadata/data reading) work without SPSS if `pyreadstat` is available.

## Install

```bash
pip install -e .
```

## Configuration

Copy `.env.example` to `.env` and set values as needed:

- `SPSS_INSTALL_PATH`: SPSS install directory (optional if auto-detect works)
- `SPSS_TEMP_DIR`: temp directory for intermediate runner/OMS files
- `SPSS_RESULTS_DIR`: output directory for persistent `.spv` and `.sps` artifacts
- `SPSS_TIMEOUT`: batch timeout in seconds
- `SPSS_NO_SPSS=1`: force file-only mode

## Run

### MCP server (stdio)

```bash
spss-mcp serve --transport stdio
```

### Status check

```bash
spss-mcp status
```

### Show Claude Code setup snippet

```bash
spss-mcp setup-info
```

## Claude Code MCP config example

Use `spss-mcp setup-info` to generate a snippet tailored to your machine.

Typical structure:

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

## Available Tools (33 total)

### File & Data Tools (6)
- `spss_check_status` - Check server capabilities
- `spss_list_files` - List .sav files in directory
- `spss_list_variables` - List variables with labels
- `spss_read_metadata` - Read variable metadata
- `spss_read_data` - Preview data rows
- `spss_file_summary` - Quick file overview

### Basic Statistics (9)
- `spss_frequencies` - Frequency tables
- `spss_descriptives` - Descriptive statistics
- `spss_crosstabs` - Crosstabulation with chi-square
- `spss_t_test` - Independent/paired/one-sample t-tests
- `spss_anova` - One-way ANOVA with post-hoc
- `spss_correlations` - Pearson/Spearman correlations
- `spss_regression` - Linear regression
- `spss_normality_outliers` - Normality tests and outlier detection
- `spss_nonparametric_tests` - Mann-Whitney/Wilcoxon/Kruskal-Wallis

### Advanced Regression & GLM (3)
- `spss_logistic_regression` - Binary/multinomial logistic regression
- `spss_ordinal_regression` - Ordinal regression (PLUM)
- `spss_genlin` - Generalized linear models

### Multilevel & Mixed Models (2)
- `spss_mixed` - Linear mixed-effects models
- `spss_genlinmixed` - Generalized linear mixed models

### Survival Analysis (2)
- `spss_cox_regression` - Cox proportional hazards regression
- `spss_kaplan_meier` - Kaplan-Meier survival curves

### Multivariate Analysis (5)
- `spss_factor` - Exploratory factor analysis
- `spss_discriminant` - Discriminant analysis
- `spss_manova` - Multivariate ANOVA
- `spss_glm_univariate` - Univariate general linear model
- `spss_repeated_measures_anova` - Repeated measures ANOVA

### Clustering (2)
- `spss_cluster_hierarchical` - Hierarchical cluster analysis
- `spss_twostep_cluster` - Two-step cluster analysis

### Reliability & Scale (2)
- `spss_reliability_alpha` - Cronbach's alpha
- `spss_compute_scale_score` - Compute scale scores

### Utility (2)
- `spss_run_syntax` - Execute arbitrary SPSS syntax
- `spss_validate_syntax` - Validate syntax without execution

## Notes

- `.spv` generation is implemented with OMS `FORMAT=SPV`.
- `spss_validate_syntax` intentionally does not persist `.spv/.sps` outputs.
- Paths in SPSS syntax are normalized to forward slashes for compatibility.
- All analysis tools default to saving `.spv` viewer files and `.sps` syntax files.

## Development

```bash
python -m compileall src/spss_mcp
pytest
```

## License

MIT