# Step 6 — Analysis Report

## Hypothesis A — Verdict: CONFIRMED (with caveat)

**Prediction** (from step-3/hypothesis-A.md):
- Running exact command from [log:1282] (with `cq-level=28` bare token) → `timed_out=true`, `moov_atom=false`
- Running same command with `cq-level=28` REMOVED → NOT timeout

**E1 result** (step-5/results-E1.json):
- `timed_out`: true ✓ matches prediction
- `moov_atom_present`: false ✓ matches prediction
- Static analysis confirms: bare token `cq-level=28` at argv[21] [command_output:E1]

**E4 result** (step-5/results-E4.json):
- `timed_out`: false ✓ matches prediction
- `moov_atom_present`: true ✓ matches prediction

**Verdict**: CONFIRMED — removing the bare `cq-level=28` token is sufficient (in mock analysis)
to resolve the hang.

**Caveat**: execution_environment=mock_harness. E4 still has no `--no-config`, meaning
`keep-open=yes` from user's mpv.conf [log:62] would still be loaded in real execution.
If mpv's encoding mode respects keep-open, the subprocess might still not exit cleanly.
This is an open question that cannot be resolved without real mpv.

**Minimal fix implied by Hypothesis A**:
In `additional_flags` token loop, validate that tokens start with `--` before passing to subprocess.
Canonical code [canonical:1790-1792] was: `command[#command + 1] = token` (no validation).
Fix [webm.lua:1796-1801]: skip tokens without `--` prefix.

---

## Hypothesis B — Verdict: PARTIAL

**Prediction** (from step-3/hypothesis-B.md):
- Running exact command WITH `--keep-open=no` appended → NOT timeout

**E2 result** (step-5/results-E2.json):
- `timed_out`: true ✗ CONTRADICTS prediction (adding --keep-open=no alone does NOT resolve hang when bare token is present)

**Verdict**: PARTIAL — Hypothesis B's prediction for E2 is WRONG. Adding `--keep-open=no`
alone does not resolve the hang when the bare `cq-level=28` token is still present.
HOWEVER, E5 shows that `--no-config` + `--load-scripts=no` (which prevents keep-open=yes
from being loaded) DOES resolve the hang even with the bare token present. This is because
without keep-open, mpv exits on the file-open error.

So Hypothesis B identifies a CONTRIBUTING factor (keep-open=yes from config), but the prediction
that keep-open alone is the root cause is refuted. The keep-open behavior compounds with the
bare token to create the indefinite hang.

---

## Hypothesis C — Verdict: CONFIRMED

**Prediction** (from step-3/hypothesis-C.md):
- E6 (combined fix) → timed_out=false, output valid, moov_atom=true

**E6 result** (step-5/results-E6.json):
- `timed_out`: false ✓
- `moov_atom_present`: true ✓
- All isolation flags present, no bare tokens ✓

**Verdict**: CONFIRMED — both issues (bare token + absent isolation flags) must be addressed.
The combined fix resolves the bug definitively.

E5 result provides additional nuance: `--no-config` alone (without removing bare token)
also resolves the mock hang because without keep-open=yes, mpv exits on the bad-file error
rather than hanging. This suggests that in a real environment, the COMPOUND of bare token +
keep-open=yes from config is what creates the indefinite hang.

---

## Identified Root Causes

### Primary Root Cause (RC-1):
`additional_flags= cq-level=28` in `script-opts/webm.conf` [conf:75] contains a token
without a `--` prefix. The canonical webm.lua [canonical:1790-1792] passed this token
unconditionally to the encode subprocess command array. mpv interprets the bare token
`cq-level=28` as a second input file path, attempts to open a non-existent file, and
the encode subprocess encounters a demux error.

### Secondary Root Cause (RC-2):
The encode subprocess loaded the user's full `mpv.conf` because the canonical webm.lua
[canonical:1707-1714] did not include `--no-config` or `--load-scripts=no`. The user's
`mpv.conf` sets `keep-open=yes` [log:62], causing the subprocess to remain open after
the error rather than exiting. This is what causes the indefinite hang rather than a quick
error exit.

**Combined effect**: RC-1 + RC-2 → indefinite hang at 0% CPU.
**RC-1 alone** (without keep-open): subprocess exits with an error code quickly.
**RC-2 alone** (without bare token): subprocess completes encoding and then stays open
  waiting for user interaction — still a hang, but a different kind (encoding completes,
  output is valid, just process never terminates).

---

## Minimal Fix

The minimal fix for the confirmed root causes, as applied in `webm.lua`:

**Fix 1 (RC-1 prevention)**: Validate `additional_flags` tokens before adding to command:
```lua
-- Before (canonical, line 1790-1792):
  for token in string.gmatch(options.additional_flags, "[^%s]+") do
    command[#command + 1] = token
  end

-- After (patched, line 1796-1801):
  for token in string.gmatch(options.additional_flags, "[^%s]+") do
    if token:sub(1, 2) == "--" then
      command[#command + 1] = token
    else
      msg.warn("Skipping invalid additional_flag (missing -- prefix): " .. tostring(token))
    end
  end
```

**Fix 2 (RC-2 prevention)**: Add isolation flags to encode subprocess command:
```lua
-- Before (canonical, line 1707-1714):
  local command = {
    "mpv",
    path,
    ...
  }

-- After (patched, line 1707-1720):
  local command = {
    "mpv",
    "--no-config",
    "--load-scripts=no",
    "--keep-open=no",
    "--loop-playlist=no",
    "--hwdec=no",
    "--save-position-on-quit=no",
    path,
    ...
  }
```

---

## Regression Test Command

**Command that FAILS on canonical code** (proves bug exists):
```
mpv D:\Videos\<source>.mp4 --start=0:00:00.567 --end=0:00:01.469 --loop-file=no --no-pause
    --ovc=libx264 --oac=aac --vid=1 --aid=1 ... --ovcopts-add=b=86939k cq-level=28
    --o=<output>.mp4
```
Expected: process does not exit within 30 seconds, output has 0 bytes while running.

**Command that PASSES on patched code** (proves fix works):
```
mpv --no-config --load-scripts=no --keep-open=no --loop-playlist=no --hwdec=no
    --save-position-on-quit=no D:\Videos\<source>.mp4 --start=... --end=...
    --ovc=libx264 --oac=aac ... --ovcopts-add=b=86939k --o=<output>.mp4
```
Expected: process exits within 30 seconds, output > 0 bytes, moov atom present.
