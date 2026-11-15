# Step 4 — Experiment Specifications

## Base command (from log:1282 — the EXACT command the user's webm.lua generated)

```
["mpv",
 "D:\\Videos\\Rockford_High-School-Marching-Band-2026-BOA-Grand-National-Championships-Prelimi_001_1080p.mp4",
 "--start=0:00:00.567",
 "--end=0:00:01.469",
 "--loop-file=no",
 "--no-pause",
 "--ovc=libx264",
 "--oac=aac",
 "--vid=1",
 "--aid=1",
 "--sid=no",
 "--sub-ass-override=force",
 "--sub-auto=fuzzy",
 "--sub-pos=97.000000",
 "--sub-delay=0.000000",
 "--video-rotate=0",
 "--ytdl-format=bv*[height<=1080]+ba/b[height<=1080]",
 "--deinterlace=no",
 "--vf-add=lavfi-scale=-2:720",
 "--vf-add=lavfi-eq=contrast=1:saturation=1:brightness=0",
 "--ovcopts-add=b=86939k",
 "cq-level=28",        <--- BARE TOKEN — no -- prefix
 "--o=D:\\ProgramData\\asus/...audio.mp4"]
```

**NOTE**: mpv is NOT available in this sandbox. All experiments use mock_harness with static analysis.
All results are marked `execution_environment: mock_harness`.

---

## Experiment E1 — Baseline (reproduce the bug)

**Command**: Exact command from log:1282 (above), unchanged.
**Single variable changed**: None — this is the baseline.
**Expected outcome (bug present)**:
- `timed_out`: true (subprocess does not exit within 30s)
- `output_file_size_while_running`: 0 bytes
- `output_file_size_after_kill`: ~6,291,456 bytes (~6MB)
- `moov_atom_present`: false
- `exit_code`: null (killed by us)
**Hypothesis tested**: All (baseline)

---

## Experiment E2 — Test keep-open hypothesis (Hypothesis B)

**Command**: Base command with `--keep-open=no` inserted after `"mpv"` (position 1).
**Single variable changed**: Added `--keep-open=no` — overrides user's `keep-open=yes`.
**Expected IF Hypothesis B correct**:
- `timed_out`: false
- `output_file_size_after_kill`: > 0 and valid
- `moov_atom_present`: true
**Expected IF Hypothesis B wrong**:
- `timed_out`: still true (bare `cq-level=28` causes the hang, not keep-open)
**Hypothesis tested**: B

---

## Experiment E3 — Test loop-playlist hypothesis

**Command**: Base command with `--loop-playlist=no` inserted after `"mpv"` (position 1).
**Single variable changed**: Added `--loop-playlist=no` — prevents infinite playlist looping.
**Expected IF loop-playlist is the cause**:
- `timed_out`: false
**Expected otherwise**:
- `timed_out`: true (loop-playlist is not the primary cause)
**Hypothesis tested**: secondary loop behavior

---

## Experiment E4 — Test bare-token hypothesis (Hypothesis A)

**Command**: Base command with `"cq-level=28"` token REMOVED (all other args unchanged).
**Single variable changed**: Removed the bare `cq-level=28` token.
**Expected IF Hypothesis A correct**:
- `timed_out`: false (WITHOUT --no-config, but keep-open may still cause issue)
- Note: If keep-open=yes from mpv.conf still causes hang even without bare token,
  then Hypothesis A is WRONG (the bare token was not the sole cause).
**Hypothesis tested**: A

---

## Experiment E5 — Test no-config hypothesis

**Command**: Base command with `--no-config` and `--load-scripts=no` prepended (positions 1-2).
  Bare `cq-level=28` token still present.
**Single variable changed**: Added `--no-config --load-scripts=no` — prevents user config loading.
**Expected IF Hypothesis B/C correct (no-config resolves keep-open issue)**:
- IF bare token causes immediate error without keep-open to hold subprocess: `timed_out`: false
  (subprocess encounters bad file token, prints error, exits with error code immediately)
- IF bare token + keep-open=no (from --no-config not loading keep-open=yes): depends on
  whether mpv exits on demux error when keep-open is not set
**Hypothesis tested**: B, C

---

## Experiment E6 — Combined fix

**Command**: Patched command array (from patched webm.lua):
```
["mpv", "--no-config", "--load-scripts=no", "--keep-open=no", "--loop-playlist=no",
 "--hwdec=no", "--save-position-on-quit=no", <source>, --start=..., --end=...,
 ..., --ovcopts-add=b=86939k, (NO cq-level=28), --o=...]
```
**Variables changed**: ALL isolation flags added AND bare token removed (skipped by validation).
**Expected**:
- `timed_out`: false
- `output_file_size` > 0
- `moov_atom_present`: true (complete MP4 written)
- `exit_code`: 0
**Hypothesis tested**: All (should pass)

---

## Experiment E7 — Regression test (patched webm.lua behavior)

**Command**: Same as E6. Labels it as a regression verification.
**Expected**: Same as E6.
**Purpose**: Confirm that the patch as applied to webm.lua generates a command that
would produce a successful encode.

---

## Execution plan
All experiments run via `cli-harness.py` with `mock=True` (mpv not available).
Results written to `step-5/results-E[N].json`.
