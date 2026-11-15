# FIND-001 Bug Diagnosis: Undefined Variable `bitrate` in Strict Filesize Path

**ID**: FIND-001
**Severity**: High
**Type**: Defect (Runtime nil error)
**Location**: `scripts/webm.lua` L1779-1780
**Status**: Confirmed — bug present in `canonical/webm.lf.lua`

---

## Phase 1: Feedback Loop

**Script**: `re-workspace/harness/tests/test_find_001.py`

The loop reads L1779-1780 from the canonical source and applies three assertions:

1. `test_bug_present` — RED if `tostring(bitrate)` appears (bare variable, not `video_bitrate`)
2. `test_video_bitrate_in_scope` — confirms `video_bitrate` is defined in-scope at L1765
3. `test_fix_correctness` — GREEN only when `video_bitrate` replaces `bitrate` on those lines

**Baseline run result**: RED (exit 1) — `tostring(bitrate)` confirmed on both L1779 and L1780.

---

## Phase 2: Reproduce and Minimise

**Minimal reproduction path** (Lua pseudocode):
```lua
-- Trigger condition:
options.strict_filesize_constraint = true
options.target_filesize = 10000  -- any value > 0
-- encode() called with a video+audio track
```

The execution path through `encode()`:
1. L1763: `options.target_filesize > 0` → enters bitrate block
2. L1765: `local video_bitrate, audio_bitrate = calculate_bitrate(...)` — `video_bitrate` assigned
3. L1776: `options.strict_filesize_constraint` → enters strict block
4. L1779: `tostring(bitrate)` → `bitrate` is `nil` (not defined in this scope)
5. Lua string concatenation with `nil` raises: `attempt to concatenate a nil value (global 'bitrate')`

**Minimal form**: the two lines that fail are:
```lua
"--" .. tostring(type) .. "opts-add=minrate=" .. tostring(bitrate) .. "k",
"--" .. tostring(type) .. "opts-add=maxrate=" .. tostring(bitrate) .. "k"
```
The correct variable `video_bitrate` is defined at L1765 and in scope at L1779.

---

## Phase 3: Hypotheses

Ranked by likelihood:

1. **Typo during authoring** (probability: 0.90) — The MoonScript source likely had `bitrate` as a shorthand but the compiled Lua lost context. The developer intended `video_bitrate`, which is the only bitrate variable in scope at this point.

2. **Refactoring artifact** (probability: 0.07) — An earlier version may have had a single `bitrate` variable; a refactor split it into `video_bitrate` / `audio_bitrate` but missed these two lines.

3. **Intentional global reference** (probability: 0.02) — Extremely unlikely; there is no global `bitrate` defined anywhere in the file.

4. **Dead code path** (probability: 0.01) — `strict_filesize_constraint` defaults to `false`, so this path is only reached when explicitly enabled. The bug would go unnoticed in default usage.

---

## Phase 4: Instrument

Targeted analysis of scope at L1779:

```
L1762: if format.acceptsBitrate then
L1763:   if options.target_filesize > 0 then
L1765:     local video_bitrate, audio_bitrate = calculate_bitrate(...)
L1766:     if video_bitrate then
L1767-1770:   append -- uses video_bitrate correctly
L1771:     if audio_bitrate then
L1772-1774:   append -- uses audio_bitrate correctly
L1776:     if options.strict_filesize_constraint then
L1777:       local type = ...
L1778-1781:   append -- BUG: uses bare 'bitrate' instead of 'video_bitrate'
```

The variable `video_bitrate` is in scope throughout this block. No `bitrate` variable exists
anywhere in `encode()` or at module level. Lua treats it as a global lookup which returns `nil`.

The `tostring(nil)` call returns the string `"nil"`, so the flag would actually be:
`--ovcopts-add=minrate=nilk` — an invalid ffmpeg option, causing an ffmpeg error rather
than a Lua crash. However, Lua's `..` operator concatenation requires a string or number,
and `tostring(bitrate)` does handle the nil without crashing — it produces `"nil"` as the
string value. The actual consequence is a corrupt ffmpeg invocation rather than a Lua exception.

---

## Phase 5: Fix and Regression Test

**Regression test** (in `test_find_001.py`):
```python
def test_fix_correctness(lines):
    target_lines = lines[1778:1780]
    combined = "".join(target_lines)
    bare = re.search(r'\bbitrate\b(?!_)', combined)
    video = re.search(r'video_bitrate', combined)
    return not bare and video, ...
```

**Patch**: `re-workspace/deliverables/patches/FIND-001-fix-bitrate-variable.patch`

```diff
-          "--" .. tostring(type) .. "opts-add=minrate=" .. tostring(bitrate) .. "k",
-          "--" .. tostring(type) .. "opts-add=maxrate=" .. tostring(bitrate) .. "k"
+          "--" .. tostring(type) .. "opts-add=minrate=" .. tostring(video_bitrate) .. "k",
+          "--" .. tostring(type) .. "opts-add=maxrate=" .. tostring(video_bitrate) .. "k"
```

**Note on semantics**: The strict filesize block sets both `minrate` and `maxrate` equal to
`video_bitrate`, which is correct — this forces a constant bitrate (CBR) mode for the codec,
which is what strict filesize constraint requires to guarantee the output size stays within
the target filesize budget.

---

## Phase 6: Cleanup and Verification

After applying the patch, re-run:
```
python3 re-workspace/harness/tests/test_find_001.py
```
Expected: GREEN (exit 0) — `video_bitrate` found on L1779-1780, no bare `bitrate`.

**Windows 10 specific note**: On the developer's target platform (mpv-x86_64-20261114,
clang build), `strict_filesize_constraint` is a user-facing option. If a user enables it
via the config file (`script-opts/webm-strict_filesize_constraint=yes`) and sets
`target_filesize`, this code path executes on every encode. The resulting ffmpeg command
would contain `--ovcopts-add=minrate=nilk` which ffmpeg would reject with an error, causing
the encode to fail silently (mpv detaches the process when `run_detached=true`).
