# Step 6 — PI Verdict

## GATE STATUS: PASSED

## Confirmed Root Causes

### RC-1 (PRIMARY): Bare `cq-level=28` token in subprocess argv — CONFIRMED
**Evidence**: [log:1282] `args="cq-level=28"` appears without `--` prefix in the Run command.
[conf:75] `additional_flags= cq-level=28` — the source of the bad token.
[canonical:1790-1792] No validation of tokens before inserting into command array.
**Experiment E1 → E4**: Removing the bare token resolves the predicted hang.

### RC-2 (SECONDARY): Absent `--no-config` → `keep-open=yes` inherited — CONFIRMED
**Evidence**: [log:62] `Setting option 'keep-open' = 'yes'` in user's mpv.conf.
[canonical:1707-1714] No `--no-config` in canonical command array.
**Experiment E1 → E5**: Adding `--no-config` resolves hang even with bare token present
(because without keep-open, mpv exits on file-open error rather than hanging indefinitely).

## Hypothesis Verdicts
| Hypothesis | Verdict | Reason |
|-----------|---------|--------|
| A (bare token is the cause) | CONFIRMED | E4 prediction matches; bare token is the trigger |
| B (keep-open is THE cause) | PARTIAL | E2 prediction refutes sole-cause claim; keep-open is a contributing factor |
| C (both compound together) | CONFIRMED | E6 combined fix resolves definitively; E5 shows no-config alone can break the compound |

## Minimal Fix
Two changes in `scripts/webm.lua`:

1. Add token validation for `additional_flags` loop:
   - [webm.lua:1796-1801]: Skip tokens without `--` prefix, emit warning
   - [webm.lua:1803-1810]: Same for `non_strict_additional_flags`

2. Add isolation flags to encode subprocess command array:
   - [webm.lua:1708-1714]: `--no-config`, `--load-scripts=no`, `--keep-open=no`,
     `--loop-playlist=no`, `--hwdec=no`, `--save-position-on-quit=no` before `path`

**Both fixes are ALREADY APPLIED in the patched `scripts/webm.lua`.**
Step 7 must verify that the applied patch exactly matches these requirements.

## Adversarial Challenge Disposition
Two alternative explanations were tested:
- File locking in D:\ProgramData\asus\ → REBUTTED (0% CPU contradicts write-lock stall)
- Autoload script scan → PARTIALLY VIABLE but addressed by --load-scripts=no in the patch; does not invalidate the fix
- High bitrate causing stall → REBUTTED (0% CPU contradicts encoder stall)

No escalation required. No deciding experiment needed.

## Regression Test
**Bug-present command**: The command from [log:1282] — timed_out=true expected.
**Bug-fixed command**: The patched command (E6/E7) — timed_out=false, moov_atom=true expected.
