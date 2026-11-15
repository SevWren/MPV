# Bug Diagnosis Summary — webm.lua

**Target**: `scripts/webm.lua` (2856 lines, MoonScript-compiled Lua, mpv user script)
**Developer environment**: Windows 10, mpv-x86_64-20261114-git-649001d4e2 (clang)
**Canonical source**: `re-workspace/canonical/webm.lf.lua`
**Analysis date**: 2026-11-15

---

## Summary Table — All 10 Findings

| ID | Type | Severity | Title | Status | Fix Required |
|---|---|---|---|---|---|
| FIND-001 | Defect | High | Undefined variable `bitrate` in strict filesize path | Confirmed — BUG PRESENT | YES |
| FIND-002 | Defect | High | `formats["raw"]` nil — crash in EncodeOptionsPage | Confirmed (filed) / REVISED | NO (see note) |
| FIND-003 | Defect | Medium | `output_format` default doesn't match formats key | Confirmed — BUG PRESENT | YES |
| FIND-004 | Defect | Low | `get_duration` uses undefined `reversed_binary_duration` | Confirmed — BUG PRESENT | LOW (dead path) |
| FIND-005 | Defect | Low | `startEncode` appends empty table (vestigial no-op) | Confirmed — HARMLESS | LOW |
| FIND-006 | Security | High | IPC handler has no input validation | Confirmed — BUG PRESENT | YES |
| FIND-007 | Defect | Medium | Temp file and logfile leaked when `run_detached=true` | Confirmed — BUG PRESENT | YES |
| FIND-008 | Defect | Low | `strict_bitrate_multiplier` declared but never used | Confirmed — DEAD OPTION | LOW |
| FIND-009 | Defect | Low | `additional_flags` whitespace tokenization breaks values with spaces | Confirmed — BUG PRESENT | YES |
| FIND-010 | Defect | Medium | PreviewPage saves properties at construction, not `show()` time | Confirmed — BUG PRESENT | YES |

---

## Priority Order for Fixing (Windows 10 Developer Target)

1. **FIND-006** (Security/High) — IPC handler has no input validation. Active security issue; any co-loaded script or IPC client can inject `additional_flags`, `output_directory`, `output_template`. On Windows 10, the named pipe IPC socket is accessible to same-user processes.

2. **FIND-003** (Defect/Medium) — Default `output_format = "mp4 (h264/AAC)"` does not match registry key `"mp4"`. This crashes `encode()` on first use for any user who has not explicitly overridden the default. Affects every new user on first run.

3. **FIND-001** (Defect/High) — `bitrate` used instead of `video_bitrate` in strict filesize path. Corrupts the ffmpeg command with `--ovcopts-add=minrate=nilk`; encode fails silently under `run_detached=true` (the default on Windows).

4. **FIND-007** (Defect/Medium) — Temp file and logfile leaked when `run_detached=true`. On Windows 10, this is the default code path (`run_detached=true` is the default). VP8 two-pass logfiles and HLS cache_dump.ts files accumulate in the temp directory across sessions.

5. **FIND-010** (Defect/Medium) — PreviewPage saves mpv properties at construction time. The window constructor runs at script load, not at `show()` time, so the "original" values captured may be stale by the time the UI opens.

6. **FIND-009** (Defect/Low) — `additional_flags` tokenized by whitespace, breaking values containing spaces. Affects flags like `-vf scale=1920:1080` passed as a single string — the value would be split at the colon-preceded space if any were present. Workaround: users must use `--ovcopts-add=` style flags.

7. **FIND-004** (Defect/Low) — `get_duration` uses `reversed_binary_duration` instead of `big_endian_binary_duration`. This function is never called in normal flow; only `set_duration` is used. No user impact unless a future code path calls `get_duration`.

8. **FIND-002** (Filed/High — REVISED to No-Fix-Required) — `formats["raw"]` IS registered at L863. See diagnosis.

9. **FIND-008** (Defect/Low) — `strict_bitrate_multiplier = 0.95` is read by `mpopts.read_options` but never referenced in any calculation. Can be removed as dead code or implemented.

10. **FIND-005** (Defect/Low) — Vestigial `append(copy_command_line, {})` no-op. No impact; can be removed in cleanup.

---

## BUG-1 (FIND-001) — Full Phase 1-6 Results

**Phase 1 — Feedback loop**: `re-workspace/harness/tests/test_find_001.py`
Reads L1779-1780 from canonical source; asserts `tostring(bitrate)` absent and `tostring(video_bitrate)` present.

**Phase 2 — Reproduce**: RED confirmed. L1779-1780 contain `tostring(bitrate)` on both lines. `video_bitrate` is defined at L1765 and in scope.

**Phase 3 — Hypotheses**: Most likely a MoonScript refactoring artifact — the variable was split from a single `bitrate` to `video_bitrate`/`audio_bitrate` but the strict constraint block was missed.

**Phase 4 — Instrument**: `bitrate` does not exist as a local or global anywhere in the file. Lua evaluates `tostring(nil)` which produces `"nil"` — the resulting flag `--ovcopts-add=minrate=nilk` is passed to ffmpeg, which rejects it. Under `run_detached=true` (Windows default), this failure is silent.

**Phase 5 — Fix**: Replace `bitrate` with `video_bitrate` on both lines.
Patch: `re-workspace/deliverables/patches/FIND-001-fix-bitrate-variable.patch`
Regression test: `test_find_001.py` — GREEN after patch applied.

**Phase 6 — Cleanup**: After patch, test produces GREEN exit 0. No side effects.

---

## BUG-2 (FIND-002) — Full Phase 1-6 Results

**Phase 1 — Feedback loop**: `re-workspace/harness/tests/test_find_002.py`
Extracts formatIds and formats registration keys; asserts all formatIds are registered.

**Phase 2 — Reproduce**: GREEN — all 7 formatIds are registered. `formats["raw"] = RawVideo()` exists at L863. The finding's claim `"never registered"` is incorrect for `canonical/webm.lf.lua`.

**Phase 3 — Hypotheses**: The finding likely describes a prior revision of the source, or was based on the class definition block being mistaken for the registration (the `do...end` block defines `RawVideo` class but the registration `formats["raw"] = RawVideo()` is the next statement at L863).

**Phase 4 — Instrument**: The 7 registered keys `{raw, webm-vp8, webm-vp9, mp4, mp4-nvenc, mp3, gif}` match exactly the 7 formatIds `{webm-vp8, webm-vp9, mp4, mp4-nvenc, raw, mp3, gif}`.

**Phase 5 — Fix**: No code change required. Patch is documentation only.
Patch: `re-workspace/deliverables/patches/FIND-002-fix-raw-format-id.patch`
Regression test: `test_find_002.py` serves as a guard against future regressions.

**Phase 6 — Cleanup**: Test produces GREEN exit 0. FIND-003 is the adjacent confirmed issue.

---

## BUG-3 (FIND-006) — Full Phase 1-6 Results

**Phase 1 — Feedback loop**: `re-workspace/harness/tests/test_find_006.py`
Extracts handler body; checks for 5 validation indicators (allowlist, type(), logging, range checks, bare merge loop).

**Phase 2 — Reproduce**: RED confirmed. Handler is a 5-line bare merge with zero validation.

**Phase 3 — Hypotheses**: Function name `test_set_options` indicates it was a development debug helper. The `mp.register_script_message` call was never removed, leaving it permanently active.

**Phase 4 — Instrument (STRIDE)**:
- **Spoofing**: No sender identity — any script can send `mpv-webm-set-options`.
- **Tampering**: `additional_flags` injection adds arbitrary ffmpeg flags; `output_directory` enables Windows path traversal; `output_template` enables targeted file overwrite.
- **Repudiation**: No logging of set-options calls.
- **Information disclosure**: Injected unknown keys pollute the options table.
- **Denial of Service**: Inject `run_detached=false` to block mpv UI during encode.
- **Elevation of Privilege**: Not directly applicable (no setuid), but output to Startup folder is a persistence vector.

**Phase 5 — Fix**: Add `_valid_options` allowlist (24 entries), type checking per option, coercion for strings to bool/number, rejection logging via `msg.warn`.
Patch: `re-workspace/deliverables/patches/FIND-006-fix-ipc-validation.patch`
Regression test: `test_find_006.py` — GREEN after patch applied.

**Phase 6 — Cleanup**: After patch, test produces GREEN exit 0. Recommend also evaluating removal of the handler entirely for production builds.

---

## FIND-004 Brief Diagnosis

**L620**: `FirstpassStats.get_duration()` returns `read_double(reversed_binary_duration)` where `reversed_binary_duration` is undefined. The correct local is `big_endian_binary_duration` (defined at L619). This is a copy-paste typo.

**Severity assessment**: Low — `get_duration` is never called in the normal encoding flow (only `set_duration` is used for VP8 two-pass stats patching). The bug would surface only if future code adds a `get_duration` call.

**Recommended fix**: Change `reversed_binary_duration` to `big_endian_binary_duration` on L620.

---

## FIND-005 Brief Diagnosis

**L1365-1366**: `append(copy_command_line, {})` appends an empty table, which does nothing (the `append` function iterates over the second argument; empty table = zero iterations).

**Severity assessment**: Low — completely harmless dead code. No runtime effect.

**Recommended fix**: Remove the line. It is a vestigial artifact from a previous `append` call that had actual content.

---

## FIND-007 Brief Diagnosis — Windows-Specific Note

**L1856**: When `run_detached=true`, `encode()` returns immediately after `subprocess_detached()` without running cleanup code. This leaks:
- VP8 two-pass logfile (`get_pass_logfile_path(out_path)`) — a `.log` file in the output directory
- HLS cache temp file (`cache_dump.ts`) — a temp file written for stream sources

**Windows 10 specific**: `run_detached=true` is the **default** (`options.run_detached = true` at L9). On Windows 10, `utils.subprocess_detached` uses `cmd.exe /Q /C start ""` to background the mpv encode process. The cleanup code at L1875+ (which deletes the logfile and cache_dump.ts) is only reached when `run_detached=false`. Since the default is `run_detached=true`, the temp file leak is the **default behavior on Windows**.

**Recommended fix**: Move cleanup into a separate function; call it from both the detached and non-detached paths. Alternatively, use a unique temp path that includes the PID/timestamp so leaked files are identifiable.

---

## FIND-008 Brief Diagnosis

**L15**: `strict_bitrate_multiplier = 0.95` is loaded from config via `mpopts.read_options` but never used in `calculate_bitrate()` or anywhere else. The function calculates bitrates without any safety multiplier, potentially producing outputs that slightly exceed the target filesize.

**Severity assessment**: Low (dead option). No crash; just a missing feature.

**Recommended fix**: Either implement the multiplier in `calculate_bitrate()` by multiplying `video_kilobits` by `options.strict_bitrate_multiplier`, or remove the option entirely.

---

## FIND-009 Brief Diagnosis

**L1790**: `additional_flags` is split by `gmatch('[^%s]+')` — any whitespace splits into separate tokens. A flag like `--vf "scale=1920 1080"` (with a space in the value) would be split into `--vf`, `"scale=1920`, `1080"` — corrupting the argument.

**Severity assessment**: Low in normal use (users typically pass simple flags). Can become a security issue when combined with FIND-006 injection.

**Recommended fix**: Change the flag input to accept a Lua table of pre-split tokens, or implement proper shell-style quoting (respect single/double quotes in the split). For Windows compatibility, use the existing `shell_escape` function.

---

## FIND-010 Brief Diagnosis

**L2591-2597**: `PreviewPage.__init` saves `vf`, `time-pos`, and `pause` at construction time (when the script module loads), not at `show()` time. If the user opens a file, creates a region, then opens the PreviewPage, the `time-pos` saved during construction may be from a different position.

**Severity assessment**: Medium — causes incorrect restoration of mpv state after the preview page closes. User may notice their playback position or video filter state is wrong after previewing.

**Recommended fix**: Move the property save (`self.old_vf`, `self.old_time_pos`, `self.old_pause`) from `__init` into the `show()` method, capturing the values at the moment the page is actually displayed.
