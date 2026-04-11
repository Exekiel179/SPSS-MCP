---
name: spss-mcp-guard
description: >
  Make IBM SPSS Statistics MCP execution more reliable by preventing common MCP/SPSS failures before they happen and diagnosing them when they do. Use when the user wants to avoid SPSS MCP timeouts, syntax incompatibilities, PROXSCAL/MDS errors, invalid subcommands, stale environment configuration, or flaky batch execution; when a statistical analysis should be executed defensively with smoke tests first; or when Claude should probe with minimal syntax before attempting a heavier SPSS run.
---

# SPSS MCP Guard

Use this skill to make SPSS MCP execution robust, especially for uncommon procedures, long-running analyses, and syntax that may vary by SPSS version.

## Workflow

1. **Check capability first**
   - Call `spss_check_status`.
   - If SPSS batch is unavailable, stop and explain that only file-mode tools are safe.

2. **Read the data before writing syntax**
   - Use `spss_file_summary` or `spss_read_metadata` first.
   - Never guess variable names or data shape.

3. **Prefer the safest execution path**
   - Use a dedicated MCP tool when one exists and is known-good.
   - Use `spss_run_syntax` for uncommon methods, but only after a smoke test.

4. **Smoke test before heavy analysis**
   - First run a minimal procedure such as:
     - `DESCRIPTIVES`
     - `FREQUENCIES`
     - `DISPLAY DICTIONARY`
   - Only attempt heavier methods after the smoke test succeeds.

5. **Escalate analysis gradually**
   - Start with the smallest sample or simplest valid syntax.
   - Add options one subcommand at a time.
   - For MDS/PROXSCAL-style work, first validate the command family and legal keywords by interpreting SPSS warnings.

6. **Treat SPSS warnings as syntax guidance**
   - If SPSS says a keyword is unrecognized, rewrite syntax to match the reported valid keywords.
   - Do not keep retrying the same syntax.

7. **Distinguish timeout from syntax failure**
   - A long wait is not always a true performance issue.
   - If possible, probe the same command through a minimal direct execution path before concluding it is only a timeout issue.

## Guardrails

- Do not jump directly to complex procedures on first attempt.
- Do not assume old SPSS syntax examples match the installed version.
- Do not assume `.env` settings are loaded; verify behavior if timeout values look stale.
- Do not treat `success=True` as “analysis valid” without reading warning blocks.
- For uncommon procedures, keep the first successful run minimal, then add output options later.

## Decision Tree

1. **Execution fails immediately?**
   - Check `spss_check_status`.
   - Verify data path and variables with file tools.

2. **Execution times out?**
   - Re-run a minimal baseline procedure on the same file.
   - If baseline succeeds, suspect syntax/procedure complexity rather than global SPSS failure.
   - Inspect timeout configuration behavior before increasing complexity.

3. **SPSS returns warnings/errors but output exists?**
   - Read the warning text carefully.
   - Use it to rewrite subcommands.
   - Especially common for `PRINT`, `MODEL`, and `SHAPE` subcommands in advanced procedures.

4. **Procedure is unfamiliar or cold-path?**
   - Use `spss_run_syntax`.
   - Start with minimal valid syntax.
   - Add optional subcommands only after the base command works.

## Known reliable patterns

- For a baseline smoke test:

```spss
DESCRIPTIVES VARIABLES=x1 x2 x3
  /STATISTICS=MEAN STDDEV MIN MAX.
```

- For defensive PROXSCAL probing, prefer minimal legal syntax first. Do not assume keywords like `SYMMETRIC`, `EUCLID`, or `CONFIGURATION` are valid in the installed SPSS syntax variant without testing.

## References

- Read `references/failure-patterns.md` when diagnosing timeouts, invalid keywords, stale `.env` behavior, or advanced procedure incompatibilities.
- Reuse `spss-analyst` for general SPSS workflow and syntax conventions; this skill is specifically for failure prevention and recovery.
