---
name: spss-analyst
description: >
  Write and execute IBM SPSS Statistics syntax following SPSS conventions and run SPSS MCP analyses defensively. Use when the user asks to run statistical analysis (frequencies, descriptives, regression, t-test, ANOVA, correlations, factor analysis, crosstabs, MDS/PROXSCAL, clustering, survival, mixed models, etc.), write or review SPSS syntax/code, explore or summarize .sav data files, compute/recode/transform variables, clean or restructure data in SPSS, diagnose SPSS MCP timeouts or syntax incompatibilities, or use SPSS MCP tools safely with smoke tests first. Triggered by keywords like SPSS, .sav, 分析, 频率, 回归, 方差分析, 相关, 描述统计, t检验, 因子分析, 交叉表, 编码, 临近映射, MDS, PROXSCAL, or any request involving statistical analysis with SPSS data files.
---

# SPSS Analyst

## Workflow

1. **Check capabilities** — Call `spss_check_status` first to confirm SPSS batch is available.
2. **Explore the data** — For any `.sav` file, call `spss_file_summary` or `spss_read_metadata` to know variable names, types, and labels before writing syntax.
3. **Run a smoke test before heavy or uncommon analysis** — If the target procedure is cold-path, high-cost, or unfamiliar, first run a minimal baseline such as `DESCRIPTIVES`, `FREQUENCIES`, or `DISPLAY DICTIONARY`.
4. **Write syntax** — Follow conventions below. See [references/spss-syntax.md](references/spss-syntax.md) for full command reference.
5. **Execute defensively** — Use the appropriate MCP tool when one exists; otherwise use `spss_run_syntax` and add optional subcommands only after the minimal command works.
6. **Read warnings, not just success flags** — A run may return output and still contain critical warning text. Treat SPSS warning blocks as syntax guidance.
7. **Interpret** — Explain key results in plain language after output arrives.
8. **Archive output** — After every analysis tool call that produces a `Viewer file:`, immediately archive results to `spss_result/`. See [Output Archiving](#output-archiving) below.

## Reliability Rules

- Never guess variable names or data shape.
- Never jump directly to a complex procedure on the first try.
- For uncommon methods, start with the smallest valid syntax and then add print/save options.
- If SPSS says a keyword is unrecognized, rewrite the syntax to match the reported valid keywords.
- If timeout behavior looks stale, verify that repo-local `.env` is actually being loaded and restart the MCP session if needed.

## Core Syntax Rules

| Rule | Correct | Wrong |
|---|---|---|
| Keywords uppercase | `FREQUENCIES` | `frequencies` |
| Period ends every command | `DESCRIPTIVES VARIABLES=age.` | `DESCRIPTIVES VARIABLES=age` |
| Subcommands start with `/` | `/STATISTICS=MEAN` | `STATISTICS=MEAN` |
| Strings in single quotes | `'myfile.sav'` | `"myfile.sav"` |
| Comments with `*` | `* My comment.` | `# My comment` |
| Missing value code | `MISSING VALUES age (99).` | — |

## Standard File Header

Always begin a syntax block with:

```spss
* ============================================================
* 分析目的: [简述目的]
* 数据文件: [文件路径]
* 日期: [YYYY-MM-DD]
* ============================================================

GET FILE='C:/Data/myfile.sav'.
```

## Common Procedure Patterns

```spss
* 频率表 + 描述统计
FREQUENCIES VARIABLES=var1 var2
  /STATISTICS=MEAN MEDIAN MODE STDDEV
  /ORDER=ANALYSIS.

* 描述统计（仅连续变量）
DESCRIPTIVES VARIABLES=score age income
  /STATISTICS=MEAN STDDEV MIN MAX VARIANCE.

* 独立样本 t 检验
T-TEST GROUPS=gender(1 2)
  /VARIABLES=score.

* 单因素方差分析
ONEWAY score BY group
  /STATISTICS DESCRIPTIVES
  /POSTHOC=TUKEY ALPHA(.05).

* 线性回归
REGRESSION
  /DEPENDENT score
  /METHOD=ENTER age edu income.

* 交叉表 + 卡方
CROSSTABS
  /TABLES=gender BY jobcat
  /STATISTICS=CHISQ
  /CELLS=COUNT ROW COLUMN.

* 计算新变量
COMPUTE bmi = weight / (height * height).
VARIABLE LABELS bmi '体质指数'.
EXECUTE.

* 变量重新编码
RECODE age (18 THRU 35=1)(36 THRU 55=2)(56 THRU HI=3) INTO age_group.
VALUE LABELS age_group 1'青年' 2'中年' 3'老年'.
EXECUTE.
```

## Advanced Procedure Guardrails

- For PROXSCAL / MDS, do not assume keywords like `SYMMETRIC`, `EUCLID`, or `CONFIGURATION` are valid in the installed syntax variant without testing.
- Start with a smoke test, then a minimal valid target procedure, then add richer output requests.
- For timeout vs syntax ambiguity, prove the environment with a baseline command first.

## Output Archiving

After every `mcp__spss__*` tool call that produces output (i.e., result contains `Viewer file:`), immediately:

**1. Ensure directory exists**
```bash
mkdir -p <cwd>/spss_result
```

**2. Determine next sequence number** — Glob `spss_result/[0-9][0-9]_*`, take max prefix + 1 (start at `01`).

**3. Map tool → type label**

| Tool / main command | Label |
|---|---|
| `spss_descriptives` / `DESCRIPTIVES` | `descriptives` |
| `spss_frequencies` / `FREQUENCIES` | `frequencies` |
| `spss_twostep_cluster` / `QUICK CLUSTER` | `kmeans_cluster` |
| `spss_cluster_hierarchical` / `CLUSTER` | `hierarchical_cluster` |
| `spss_anova` / `ONEWAY` | `oneway_anova` |
| `spss_t_test` / `T-TEST` | `ttest` |
| `spss_regression` / `REGRESSION` | `regression` |
| `spss_correlations` / `CORRELATIONS` or `NONPAR CORR` | `correlation` |
| `spss_factor` / `FACTOR` | `factor_analysis` |
| `spss_reliability_alpha` / `RELIABILITY` | `reliability` |
| `spss_logistic_regression` / `LOGISTIC REGRESSION` | `logistic_regression` |
| `spss_glm_univariate` / `GLM` | `glm_univariate` |
| `spss_manova` / `MANOVA` | `manova` |
| `spss_mixed` / `MIXED` | `mixed_model` |
| `spss_crosstabs` / `CROSSTABS` | `crosstabs` |
| `spss_nonparametric_tests` / `NPAR TESTS` | `nonparametric` |
| `spss_normality_outliers` / `EXAMINE` | `normality` |
| `spss_run_syntax` (mixed) | infer from dominant command |

**4. Copy .spv** — Extract path after `Viewer file:` from tool result, copy to `spss_result/NN_<label>.spv`. Skip if path missing.

**5. Write .sps** — Create `spss_result/NN_<label>.sps` with header block + full syntax:

```
************************************************************
* 文件名：NN_<label>.sps
* 分析类型：<中文全称>
* 数据文件：<.sav 路径>
* 因变量 / 预测变量 / 分组变量：<变量名>（若适用）
* 关键参数：<聚类数、事后检验、CI水平等>
* 缺失值处理：<LISTWISE / PAIRWISE>
* 执行日期：<YYYY-MM-DD>
************************************************************
<完整 SPSS 语法>
```

**Constraints:** sequence number is global (not per-type); parallel tool calls each get their own number; read-only tools (`spss_list_files`, `spss_file_summary`, `spss_import_csv`, `spss_check_status`, etc.) do **not** trigger archiving.

## Reference Files

- **[references/spss-syntax.md](references/spss-syntax.md)** — Full command reference: all procedures, data management, variable operations, SELECT IF, SORT, MERGE, OMS. Load when writing unfamiliar or complex commands.
- **[references/spss-mcp-tools.md](references/spss-mcp-tools.md)** — All MCP tools with parameters and when to use each. Load when choosing which tool to call.
- **[references/failure-patterns.md](references/failure-patterns.md)** — Read when diagnosing timeouts, invalid keywords, stale `.env` behavior, `success=True` with warnings, or advanced procedure incompatibilities.
