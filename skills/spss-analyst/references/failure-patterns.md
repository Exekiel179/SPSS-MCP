# SPSS MCP Failure Patterns

## 1. Timeout that is really syntax failure

Symptom:
- MCP reports timeout or the run appears to hang.

Check:
- Run a tiny baseline procedure on the same `.sav` file.
- If `DESCRIPTIVES` succeeds quickly, the environment is probably healthy.
- Then inspect the failing syntax for invalid subcommands.

## 2. Stale timeout configuration

Symptom:
- `.env` was changed but behavior still reflects an older timeout.

Check:
- Verify the code actually loads the repo-local `.env`.
- If the process inherited old shell variables, ensure repo-local `.env` overrides them.
- Restart the MCP server/session after changing timeout-related configuration.

## 3. PROXSCAL / MDS syntax incompatibility

Observed pattern from real debugging:
- `MODEL=EUCLID DIMENSIONS=2` may be invalid in the installed syntax variant.
- `PRINT=CONFIGURATION` may be invalid.
- `SHAPE=SYMMETRIC` may be invalid.

A minimal working pattern found in practice:

```spss
PROXSCAL
  /VARIABLES=v1 v2 v3 v4
  /SHAPE=BOTH
  /MODEL=IDENTITY
  /CRITERIA=DIMENSIONS(2)
  /PRINT=STRESS.
```

Important:
- Use SPSS warning text to refine the syntax.
- Prefer the exact legal keywords SPSS reports.

## 4. `success=True` with warnings

Meaning:
- The runner may still return output if an OMS text file was produced.
- The command may still be partially invalid.

Action:
- Always read warning blocks before calling the run valid.
- Especially important for advanced procedures and uncommon subcommands.

## 5. Baseline smoke-test sequence

Use this exact progression:

1. `spss_check_status`
2. `spss_read_metadata` or `spss_file_summary`
3. `DESCRIPTIVES` baseline
4. minimal target procedure
5. richer target procedure with optional print/save clauses

This sequence reduces wasted retries and separates environment problems from syntax problems.
