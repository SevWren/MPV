# FIND-002 Bug Diagnosis: `formats["raw"]` Nil — Crash in EncodeOptionsPage

**ID**: FIND-002
**Severity**: High (as filed) / FINDING REVISED — see Phase 2
**Type**: Defect (nil indexing)
**Location**: `scripts/webm.lua` L2363-2385
**Status**: Confirmed in findings.jsonl — but REVISED by this analysis

---

## Phase 1: Feedback Loop

**Script**: `re-workspace/harness/tests/test_find_002.py`

The loop:
1. Extracts all `formatIds` from the EncodeOptionsPage constructor (L2363-2371)
2. Extracts all `formats["key"] = ...` registration lines from the full source
3. Asserts every formatId has a corresponding registration (RED if any missing, GREEN if all present)

**Baseline run result**: GREEN (exit 0) — all 7 formatIds are registered.

---

## Phase 2: Reproduce and Minimise — FINDING REVISED

The original finding claims: `"formats['raw'] is never registered"`.

**This is factually incorrect for `canonical/webm.lf.lua`.**

At L863: `formats["raw"] = RawVideo()` — registration is present.

The registered keys are: `raw`, `webm-vp8`, `webm-vp9`, `mp4`, `mp4-nvenc`, `mp3`, `gif`
The formatIds are:        `webm-vp8`, `webm-vp9`, `mp4`, `mp4-nvenc`, `raw`, `mp3`, `gif`

These sets are identical (order differs, which is irrelevant for a table lookup).

**Revised diagnosis**: The finding's claim `"formats['raw'] is never registered"` does not
hold for the canonical compiled file. It may have been based on:

- A different revision of the source (perhaps the original `webm.lua` that ships with mpv-webm)
- A misreading of the class definition (the `RawVideo` class is defined in a `do...end` block
  that only introduces the local class — the actual registration `formats["raw"] = RawVideo()`
  follows immediately at L863)
- Confusion with FIND-003 (the `options.output_format` default `"mp4 (h264/AAC)"` which does
  NOT match any formats key — the registry key is `"mp4"`)

**The claim SEG-13-R-001 that this finding is based on should be revisited.**

---

## Phase 3: Hypotheses (for the original claim)

If a future revision removed the `formats["raw"] = RawVideo()` line:

1. **Missing registration line accidentally deleted** — most likely scenario if bug ever existed
2. **formatIds containing a stale reference** — `"raw"` added to formatIds but RawVideo class not yet ported
3. **Namespace collision** — `raw` used as a Lua keyword somewhere (not applicable; it is not a reserved word)

---

## Phase 4: Instrument

Analysis of the actual access pattern:
```lua
-- L2376-2381
for _index_0 = 1, #formatIds do
    local fId = formatIds[_index_0]
    _accum_0[_len_0] = {
        fId,
        formats[fId].displayName  -- nil-index crash if formats[fId] == nil
    }
```

If `formats["raw"]` were nil, the error would be:
`attempt to index a nil value (table element)` at EncodeOptionsPage construction time,
crashing immediately when the user presses the 'o' keybind.

The bug would be highly visible and would have been caught in any basic usage test.
Its absence from the canonical file is consistent with correct implementation.

---

## Phase 5: Fix and Regression Test

**No code change required** for `canonical/webm.lf.lua`.

The regression test (`test_find_002.py`) serves as a **guard** against future regressions:
if someone removes `formats["raw"] = RawVideo()` without removing `"raw"` from `formatIds`,
the test goes RED.

**Patch**: `re-workspace/deliverables/patches/FIND-002-fix-raw-format-id.patch`
The patch is documentation-only, explaining the analysis outcome and noting the related
FIND-003 issue (mismatched `output_format` default).

If the bug were real and the choice were:
- (a) Remove `"raw"` from formatIds — loses raw AVI export capability
- (b) Add `formats["raw"] = RawVideo()` — restores capability

Option (b) is correct. Raw AVI output is a valid and useful feature (lossless intermediate).
The `RawVideo` class is fully implemented with colorspace handling.

---

## Phase 6: Cleanup and Verification

After running the feedback loop:
```
python3 re-workspace/harness/tests/test_find_002.py
```
Result: GREEN — all formatIds registered. Canonical file is correct.

**Related finding**: FIND-003 (medium severity) is a genuine mismatch: `options.output_format`
defaults to `"mp4 (h264/AAC)"` at L17, but the registry key is `"mp4"`. This would cause
`formats[options.output_format]` to return nil on first encode if the user has not changed
the default via config. FIND-003 is a more impactful issue than FIND-002 as filed.
