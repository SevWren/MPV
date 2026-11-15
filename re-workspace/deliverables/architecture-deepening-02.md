# Architecture Deepening 02 — encode() Pipeline Module

**Candidate:** Deepen the encode() pipeline
**Strength:** Strong
**Dependency category:** In-process (flag assembly) + Ports & Adapters (subprocess execution)
**Lines affected:** L1673–L1885 (the encode() function, 212 lines)
**Date:** 2026-11-15

---

## Context

`encode()` is a 212-line function that is responsible for all of the following, with no internal module boundaries:

1. Format lookup from the global `formats` table
2. HLS path handling via `find_path()` (may dump a cache file to disk)
3. Building the initial mpv command array (codec flags, track selection, disable-track flags)
4. Building video encode flags via `get_video_encode_flags()` (itself delegating to 8 more functions)
5. Bitrate calculation and conditional strict-mode flag injection (contains FIND-001 bug: uses undefined `bitrate` instead of `video_bitrate`)
6. Output path construction via `format_filename()`
7. Two-pass conditional: shallow-copies command, appends pass1 flags, runs subprocess, optionally patches vp8 logfile, appends pass2 flags
8. Calling `format:postCommandModifier()` (GIF uses this to rebuild the entire filter chain)
9. Choosing between three execution paths: detached, run_subprocess, or EncodeWithProgress
10. Cleanup: removing the pass logfile, removing the HLS temp file

Failing the deletion test: if encode() were deleted, all 10 concerns would reappear across the call site (MainPage) and there is nowhere else for them to go. This confirms encode() is earning its keep — but the concerns are not separated from each other, so changing any one of them requires reading all 212 lines.

The function has one defect confirmed in this region (FIND-001: undefined `bitrate` variable in strict-mode path, L1779-1780) and one resource-leak defect (FIND-007: temp files not cleaned up on the detached execution path, L1856-1860).

---

## Design-A — Minimize interface (3 entry points, maximize leverage per entry point)

### Interface

```lua
-- Three entry points; all state flows through explicit parameters.
-- No shared mutable state beyond what mpv API provides.

-- Entry point 1: assemble the full command array.
-- Invariant: returned command is complete and ready to execute (all flags included).
-- Error mode: returns nil + message string if preconditions fail (no file loaded, unknown format).
local command, out_path, err = encode_pipeline.build(region, startTime, endTime)

-- Entry point 2: execute a fully-assembled command.
-- Invariant: handles all three execution modes (detached, blocking, progress-overlay).
-- Error mode: returns false + message string on subprocess failure.
local ok, err = encode_pipeline.execute(command, startTime, endTime)

-- Entry point 3: clean up side-effects of a build/execute cycle.
-- Idempotent: safe to call even if build or execute failed.
encode_pipeline.cleanup(out_path, is_temporary_path)
```

**Entry points:** 3
**Types:**
- `region`: Region or nil
- `startTime`, `endTime`: numbers (seconds)
- `command`: array of strings (mpv invocation)
- `out_path`: string (absolute path to output file)
- `is_temporary_path`: boolean
- `ok`: boolean
- `err`: string or nil

**Invariants:**
- `build` is pure given fixed mpv property values: same inputs → same command array.
- `execute` does not inspect the command contents; it only chooses execution mode.
- `cleanup` is safe to call multiple times (idempotent).
- Callers may call `build` without `execute` (useful for dry-run or logging).

**Ordering constraint:** `cleanup` must be called after `execute` (or after `build` on failure path) — the caller is responsible for this ordering. The interface makes this visible by requiring `out_path` as an explicit argument.

**Error modes:**
- `build` returns `nil, nil, "No file is being played"` if no path.
- `build` returns `nil, nil, "Unknown output format: <key>"` if bad format.
- `execute` returns `false, "First pass failed..."` on subprocess error.
- `cleanup` does not return errors (best-effort).

### Implementation hidden behind seam

- Format lookup and nil guard
- HLS path dump (is_temporary logic)
- Track selection (get_active_tracks, filter_tracks_supported_by_format, append_track, append_audio_tracks)
- All flag builders (get_video_encode_flags, calculate_bitrate, format_filename, get_metadata_flags)
- FIND-001 fix location: bitrate → video_bitrate at L1779
- Two-pass branching (copy of command, pass1 run, vp8_patch_logfile, pass2 append)
- format:postCommandModifier call
- Execution mode selection (run_detached, should_display_progress, EncodeWithProgress)
- emit_event calls
- Logfile path calculation

### Usage example (Design-A)

```lua
-- In MainPage (the only real caller):
local command, out_path, err = encode_pipeline.build(self.region, self.start_time, self.end_time)
if not command then
  message(err)
  return
end
local ok, exec_err = encode_pipeline.execute(command, self.start_time, self.end_time)
if ok then
  message("Encoded successfully! Saved to\\N" .. bold(out_path))
else
  message(exec_err or "Encode failed!")
end
encode_pipeline.cleanup(out_path, false)

-- Dry-run / diagnostic mode (not currently possible):
local command, out_path, err = encode_pipeline.build(nil, 0, 10)
if command then
  msg.info("Would run: " .. table.concat(command, " "))
end
```

---

## Design-B — Optimize for the most common caller (default case trivial)

### Interface

```lua
-- Single entry point for the common case (UI-triggered encode).
-- Handles build + execute + cleanup internally.
-- Error mode: never raises; always shows mpv message; returns boolean.
local ok = encode_pipeline.run(region, startTime, endTime)
```

**Entry points:** 1
**Types:**
- `region`: Region or nil
- `startTime`, `endTime`: numbers
- `ok`: boolean (true = encode succeeded; false = any failure, message already shown)

**Invariants:**
- Always calls cleanup internally, including on error paths.
- Always calls emit_event("encode-started") and emit_event("encode-finished", status).
- If ok is false, an mpv message has already been shown to the user.
- The caller need not handle any error — it is safe to ignore the return value.

**Extended interface (for testing and diagnostics only):**
```lua
-- Not part of the public seam; available for introspection.
encode_pipeline._build_command(region, startTime, endTime) -- returns command, out_path, err
```

**Ordering constraints:** None visible to caller.

**Error modes:** All errors handled internally. The boolean return is a convenience signal.

### Implementation hidden behind seam

Same as Design-A, plus:
- The build/execute/cleanup orchestration itself is hidden
- Callers never see the intermediate command array
- Two-pass coordination is entirely opaque

### Usage example (Design-B)

```lua
-- In MainPage: one line replaces 15 lines of encode() call + error handling.
encode_pipeline.run(self.region, self.start_time, self.end_time)
-- Done. Message already shown. Event already emitted.

-- Slightly richer (if caller wants to branch on result):
local ok = encode_pipeline.run(self.region, self.start_time, self.end_time)
if ok then self:hide() end
```

---

## What implementation hides behind the seam (both designs)

Both designs hide the same implementation mass:

1. **Format resolution** — `formats[options.output_format]` with nil check
2. **HLS cache dump** — `find_path()` side-effect, is_temporary flag
3. **Track selection** — `get_active_tracks()`, `filter_tracks_supported_by_format()`, two separate track-append loops
4. **Flag assembly** — entire `get_video_encode_flags()` subtree (8 functions, ~172 lines)
5. **Bitrate calculation** — `calculate_bitrate()` with strict-mode conditional (FIND-001 fix goes here)
6. **Additional flags tokenization** — `options.additional_flags` space-split (FIND-009 fix goes here)
7. **Output path construction** — `format_filename()`, `parse_directory()`, `utils.join_path()`
8. **Two-pass orchestration** — command shallow-copy, first pass subprocess, `vp8_patch_logfile()`, second pass append
9. **postCommandModifier** — format-specific final transformation
10. **Execution dispatch** — `run_detached` / `should_display_progress` / `EncodeWithProgress` branching
11. **Event emission** — `emit_event("encode-started")` / `emit_event("encode-finished", status)`
12. **Cleanup** — logfile removal, temp file removal (FIND-007 fix for detached path goes here)

---

## Dependency strategy

**Category (flag assembly):** In-process. All flag-building functions are pure computations given fixed mpv property values. No process boundary is crossed during command construction.

**Category (subprocess execution):** Ports & Adapters. The module crosses the process boundary when it calls `utils.subprocess`, `utils.subprocess_detached`, or `EncodeWithProgress.startEncode`. Three real adapters already exist (Design Review Candidate 3), satisfying the two-adapter rule. If Candidate 3 is implemented first, `encode_pipeline.execute` delegates to `process.run(command, mode)` rather than calling the three paths directly.

**Adapters needed:**
- None for Design-A/B in isolation (uses existing subprocess calls).
- If subprocess module (Candidate 3) is implemented first, `execute` becomes a thin wrapper over `process.run` — one real adapter per execution mode.

**Migration path:**
1. Extract `build_command` as a local function inside encode() first (rename + return command, out_path).
2. Extract `execute_command` as a local function (takes command + times, handles all three paths).
3. Extract `cleanup_encode` as a local function.
4. Expose the three as the module interface (Design-A) or wrap in `run` (Design-B).
5. The global `encode` function becomes a 3-line wrapper or is removed.

---

## Trade-offs comparison

| Dimension | Design-A (3 entry points) | Design-B (1 entry point) |
|-----------|--------------------------|--------------------------|
| Interface size | 3 functions | 1 function |
| Caller complexity | Must orchestrate build/execute/cleanup | Zero orchestration |
| Testability | High — can test build without subprocess | Lower — must mock subprocess to test |
| Dry-run capability | Yes (call build, don't execute) | No (hidden inside run) |
| Debuggability | Can log command before execution | Command not accessible |
| Cleanup ownership | Caller responsible | Module responsible |
| FIND-007 fix location | cleanup() — explicit | run() — implicit |
| Error handling | Caller sees granular errors | All errors hidden, bool only |
| Lines at call site | ~8 lines (with error checks) | 1 line |
| Adding pre-execute hook | Easy (between build and execute) | Requires extending interface |

---

## Recommendation

**Design-A is stronger.**

The key argument against Design-B: hiding the command array eliminates the most useful debugging lever in the codebase. The encode() function already logs the command line (`msg.verbose("Command line:", table.concat(command, " "))`) — Design-A preserves and elevates this. With Design-B, a user reporting an encoding problem cannot get a dry-run command to paste into a terminal.

The key argument for Design-B — a one-line call site — is real but overweighted. The current call site is a single function call (`encode(region, start, end)`) that already hides 212 lines. The caller's complexity is not the problem; the lack of internal seams inside encode() is the problem. Design-A creates those seams without hiding them from the caller unnecessarily.

Design-A also cleanly localizes FIND-007 (temp file leak on detached path): cleanup() is an explicit obligation that the detached path must call, making the leak visible in the interface rather than buried in a 212-line function. With Design-B, the same fix is correct but invisible — a future maintainer modifying run() might re-introduce the leak because nothing in the interface signals that cleanup is an obligation.

The extra two lines at the call site (nil check on build, cleanup call) are worth the gain in debuggability and clean error ownership.
