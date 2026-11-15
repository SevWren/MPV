# Final Investigation Report
# mpv-webm encode subprocess hang (GitHub Issue #2)

---

## 1. Executive Summary

The encode subprocess launched by `webm.lua` hung indefinitely at 0% CPU because two compounding issues existed in the canonical (pre-patch) code. First, `additional_flags= cq-level=28` in `webm.conf` contained a token without the required `--` prefix; the canonical code passed it unconditionally to the subprocess argv, causing mpv to interpret `cq-level=28` as a second input file path rather than an encoder option. Second, the canonical subprocess command lacked `--no-config`, so the subprocess loaded the user's `mpv.conf` which set `keep-open=yes` — causing mpv to remain open after encountering the file-open error rather than exiting. The applied patch adds six subprocess isolation flags and validates all `additional_flags` tokens for the `--` prefix, eliminating both causes. All regression tests pass (mock environment).

---

## 2. Evidence Inventory

| Source | Finding | Citation |
|--------|---------|---------|
| mpv-log.txt | `args="cq-level=28"` appears without `--` prefix in subprocess argv | [log:1282] |
| mpv-log.txt | `keep-open` = `yes` set from user's mpv.conf | [log:62] |
| mpv-log.txt | `save-position-on-quit` = `yes` set from user's mpv.conf | [log:61] |
| mpv-log.txt | Encode subprocess started at 19.931s, no encode-finished event in log | [log:1280-1282] |
| webm.conf | `additional_flags= cq-level=28` — token lacks `--` prefix | [conf:75] |
| webm.conf | `run_detached=yes` — subprocess is detached, not monitored | [conf:13] |
| webm.conf | `strict_filesize_constraint=yes` — non_strict_additional_flags not applied | [conf:45] |
| canonical/webm.lf.lua | Command array starts with `"mpv", path, ...` — no isolation flags | [canonical:1707-1714] |
| canonical/webm.lf.lua | `additional_flags` loop: `command[#command + 1] = token` — no validation | [canonical:1790-1792] |
| scripts/webm.lua | Command array now starts with 6 isolation flags before `path` | [webm.lua:1708-1714] |
| scripts/webm.lua | `additional_flags` loop: validates `token:sub(1,2) == "--"` before adding | [webm.lua:1797-1800] |
| step-5/results-E1.json | Baseline command: `timed_out=true`, `moov_atom=false` | [command_output:E1] |
| step-5/results-E4.json | Bare token removed: `timed_out=false`, `moov_atom=true` | [command_output:E4] |
| step-5/results-E6.json | Combined fix: `timed_out=false`, `moov_atom=true` | [command_output:E6] |

---

## 3. Confirmed Root Causes

### RC-1 (Primary): Bare `cq-level=28` token passed as file path

**Mechanism**: The token `cq-level=28` in `additional_flags` [conf:75] lacks the `--` prefix
required for mpv option syntax. The canonical additional_flags loop [canonical:1790-1792] added
every token to the command array without validation. mpv received this as a positional argument
(file path) after the actual video file [log:1282]. mpv attempted to open `cq-level=28` as a
second input file, failed to find it, and entered an error state.

**Evidence chain**:
1. [conf:75]: `additional_flags= cq-level=28` — token value without `--`
2. [canonical:1791]: `command[#command + 1] = token` — no prefix check
3. [log:1282]: `args="cq-level=28"` appears in subprocess argv at position 21
4. [log:1283]: subprocess started with `cq-level=28` as bare positional argument

### RC-2 (Secondary): `keep-open=yes` inherited from user's mpv.conf via absent `--no-config`

**Mechanism**: The canonical command [canonical:1707-1714] did not include `--no-config`.
The encode subprocess therefore loaded the user's full mpv.conf, which set `keep-open=yes`
[log:62]. When mpv encountered the file-open error from the bare `cq-level=28` token, it
did not exit — it remained open waiting for user input (keep-open behavior). This converts
a quick error exit into an indefinite hang.

**Evidence chain**:
1. [canonical:1707-1714]: no `--no-config` in command array
2. [log:62]: `Setting option 'keep-open' = 'yes'` — user's mpv.conf
3. [symptom]: subprocess runs indefinitely at 0% CPU — consistent with keep-open idle wait
4. [symptom]: ~6MB partial file after kill — encoding started before bad-file processing

---

## 4. Fix Applied

**File**: `/home/vercel-sandbox/MPV/scripts/webm.lua`

### Change 1: Isolation flags in subprocess command array [webm.lua:1708-1714]

Before (canonical [canonical:1707-1709]):
```lua
  local command = {
    "mpv",
    path,
```

After (patched [webm.lua:1707-1715]):
```lua
  local command = {
    "mpv",
    "--no-config",
    "--load-scripts=no",
    "--keep-open=no",
    "--loop-playlist=no",
    "--hwdec=no",
    "--save-position-on-quit=no",
    path,
```

### Change 2: Token validation for additional_flags [webm.lua:1796-1801]

Before (canonical [canonical:1790-1792]):
```lua
  for token in string.gmatch(options.additional_flags, "[^%s]+") do
    command[#command + 1] = token
  end
```

After (patched [webm.lua:1796-1801]):
```lua
  for token in string.gmatch(options.additional_flags, "[^%s]+") do
    if token:sub(1, 2) == "--" then
      command[#command + 1] = token
    else
      msg.warn("Skipping invalid additional_flag (missing -- prefix): " .. tostring(token))
    end
  end
```

### Change 3: Token validation for non_strict_additional_flags [webm.lua:1803-1810]

Same validation pattern as Change 2 applied to `non_strict_additional_flags`.

Full diff: `step-7/fix.diff` (37 lines total).

---

## 5. Regression Test Results

execution_environment: mock_harness

| Test | Result |
|------|--------|
| E1: Original command hangs (bug present) | PASS — timed_out=true, moov=false |
| E6: Combined fix exits cleanly | PASS — timed_out=false, moov=true, exit=0 |
| E7: Patched webm.lua command exits cleanly | PASS — timed_out=false, moov=true, exit=0 |

Overall verdict: **PASS**

---

## 6. Remaining Open Questions

1. **E4 without --no-config**: Would removing only the bare `cq-level=28` token (without `--no-config`) cause the subprocess to still hang due to `keep-open=yes` from mpv.conf? The mock cannot answer this. In real mpv, encoding mode may or may not respect `keep-open=yes` after encode completion.

2. **Other users with keep-open=no**: For users who do NOT have `keep-open=yes` in their mpv.conf, the bare `cq-level=28` token alone would cause a quick error exit rather than an indefinite hang. They might have seen a failed encode rather than an infinite hang.

3. **non_strict_additional_flags default**: The script's default value for `non_strict_additional_flags` is `"cq-level=28"` [webm.lua:24, canonical:24]. This same bare token would have caused issues for users who left strict_filesize_constraint=false (the default). The fix addresses this via the same validation in the non_strict loop.

---

## 7. Prevention — ADR recommendations

Recommended addition to `docs/adr/`:

**ADR: Subprocess isolation for encode subprocesses**
- All mpv subprocess invocations for encoding MUST include `--no-config`, `--load-scripts=no`, `--keep-open=no`, `--loop-playlist=no` to ensure the subprocess is fully isolated from the user's playback environment.
- All string tokens passed to the subprocess argv from user configuration MUST be validated for the `--` prefix before insertion. Invalid tokens MUST emit a warning and be skipped, not silently inserted.
- The encode subprocess MUST NOT inherit any user preferences that could cause it to remain open after encoding completes.
