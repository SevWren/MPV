# Diagnostic Export Mechanism — Integration Design

**Target**: `scripts/webm.lua` (mpv user script, LuaJIT 2.1)
**Date**: 2026-11-15
**Status**: Design proposal — no existing code modified

---

## 1. Recommendation

**Yes — webm.lua should include an automatic diagnostic export mechanism.**

The confirmed silent-failure mode (FIND-001) is structural: when `run_detached=yes`
(the default on Windows), `mp.utils.subprocess_detached` returns no value, produces
no visible error, and the user receives only the message "Started encode, process was
detached."  When the encode subsequently fails — for any reason including a malformed
`--ovcopts-add` flag — there is no feedback and no artifact.

mpv's own log (`--log-file`) does capture the command line at `msg.verbose` level
(L1835, L1855), but this requires the user to have pre-configured `--log-file` and
to know to look for it.  Effectively no end user does this.

A diagnostic file written to the output directory at encode time gives any user
immediately actionable data without any configuration.  The risk — unexpected files
in the output directory — is real but manageable: the file is written only on
failure (default), is clearly named `webm-debug-*.json`, and can be suppressed by
removing the integration call.

**What to capture**: the full assembled command (most critical), subprocess result,
input/output paths, options snapshot, and environment metadata.
**When to write**: on encode failure by default; on every encode when `debug_mode=true`.
**Where to write**: same directory as the output file (already a user-controlled
location); fall back to `~/` then `os.tmpname()` parent.
**Opt-in vs always-on**: conditional write (failure-only) is on by default;
unconditional write requires `debug_mode=true` in `webm.conf`.

---

## 2. Module Interface: Design A vs Design B

### Design A — Single capture function

```lua
webm_diag.capture(context) -> path | nil
```

One entry point.  The caller passes a context table with whatever fields are
available at call time; the module resolves everything else internally.

### Design B — Event-based capture

```lua
webm_diag.on_encode_start(command, format, out_path)
webm_diag.on_encode_end(result, out_path)
webm_diag.on_encode_error(err, command)
```

Three entry points, each writing an append entry to a session log.

### Comparison

| Dimension      | Design A                                                    | Design B                                                            |
|----------------|-------------------------------------------------------------|---------------------------------------------------------------------|
| **Depth**      | High. One entry point hides file I/O, path resolution,     | Low. Callers must call 2–3 functions per encode, in sequence.       |
|                | JSON serialization, Windows/POSIX differences, and         | The module's depth is split across three shallow functions.         |
|                | fallback strategies.                                       |                                                                     |
| **Locality**   | All diagnostic logic in one function and its helpers.      | Logic is spread across three functions that must share state        |
|                | Maintainers find everything in one place.                  | (session log path, start context) via upvalues or module state.     |
| **Seam**       | Caller only knows the context table shape.  It does not    | Caller must know the calling order, the session log concept,        |
| **placement**  | know about paths, serialization, or fallbacks.             | and that all three functions must be called correctly.              |
| **Leverage**   | Maximum: one call from `encode()` captures everything.     | Lower: three coordinated calls, each doing less.                    |

**Winner: Design A.**

Design A is a deeper module.  Its interface (one function, one table argument,
one return value) is narrower than Design B's three-function seam, yet it delivers
more behaviour per call.  The caller shoulders no knowledge of file paths, JSON,
platform differences, or fallback strategies — all of that is hidden behind the
single `capture` seam.  Locality is superior: every diagnostic concern lives in
one function tree.  Design B's three-function seam forces the caller to orchestrate
state across the encode lifecycle, defeating the purpose of a module boundary.

---

## 3. Implementation Notes

### What can go wrong

| Failure mode                        | Handling                                                                    |
|-------------------------------------|-----------------------------------------------------------------------------|
| `io.open` fails (permissions, full disk) | Caught by `pcall`; falls through to `mp.utils.write_file` secondary attempt. |
| `mp.utils.write_file` unavailable   | Function is guarded by `pcall`; falls through to `mp.msg.warn` log fallback.|
| `utils.file_info` returns nil       | Treated as "file does not exist"; recorded as `false` in diagnostic.        |
| `utils.split_path` returns empty    | Falls back to `~/` via `mp.command_native({"expand-path", "~/"})`.          |
| `_json_serialize` encounters cycle  | Cycle-visited table tracking returns `"<cycle>"` string; never crashes.     |
| `context` is nil                    | `_collect` guards with `context = context or {}`; all fields degrade to defaults.|
| Entire `capture()` throws           | Outer `pcall` in `capture()` catches it; logs error via `mp.msg.error`, returns nil. |

### Critical guarantee

`webm_diag.capture()` **never raises**.  The encode path in `webm.lua` calls it
and discards the return value; a nil return is the only signal of diagnostic
failure.  The encode itself is unaffected.

### JSON serializer

`mp.utils.format_json` is available but has historically failed on tables with
mixed integer/string keys and nested structures.  The module includes a standalone
recursive serializer with explicit cycle detection, deterministic key ordering,
and integer/float disambiguation.  It produces indented, human-readable output.

---

## 4. Opt-in vs Always-on

**Proposal**: add `debug_mode=no` to `script-opts/webm.conf`.

```ini
# Write a webm-debug-*.json diagnostic file to the output directory.
# on = write on every encode (verbose; use when debugging)
# off = write only on encode failure (default; minimal footprint)
debug_mode=no
```

Calling convention inside `encode()`:

```lua
if options.debug_mode then
    webm_diag.capture(diag_ctx)          -- always-on: write every encode
else
    webm_diag.capture_on_failure(diag_ctx, res)  -- failure-only: default
end
```

`capture_on_failure` is a thin adapter on `capture`: it inspects the
subprocess result and delegates to `capture` only when status is non-zero,
nil, or the subprocess was detached (where failure cannot be ruled out).

---

## 5. Windows-Specific Notes

### run_detached=yes and missing subprocess result

When `options.run_detached` is true (the Windows default), the script calls:

```lua
utils.subprocess_detached({args = command})
```

This returns nothing.  The diagnostic module records `{detached = true}` in
`subprocess_result`.  The diagnostic file captures only pre-encode state: the
full command, options, input path, and environment.  This is the most valuable
field anyway — FIND-001 was a malformed flag in `command`, visible immediately
in the pre-encode capture without needing a subprocess result.

### Recommended: switch to run_detached=no when debug_mode=true

When `debug_mode=true`, the integration code in `encode()` should force
`run_subprocess` (blocking) instead of `subprocess_detached`, so that
`subprocess_result.status` is available and the post-encode file size check
is meaningful.  This is a one-line conditional in `encode()` and does not
affect the default user experience.

### Output path example (Windows)

Given `options.output_directory = "D:\\ProgramData\\asus"`:

```
D:\ProgramData\asus\webm-debug-20261115-120000.json
```

`utils.join_path` handles the separator correctly on Windows.  `io.open`
with a Windows absolute path works in LuaJIT 2.1.

### Platform detection

```lua
local platform_str = mp.get_property("platform")  -- "windows" on Win10
local is_windows   = (platform_str == "windows")
```

The diagnostic records both the raw string and the boolean flag.

---

## 6. User Workflow

**Standard workflow when an encode produces no output file:**

1. Check the output directory (same folder as the source video, or the
   directory set by `output_directory` in `webm.conf`) for a file named
   `webm-debug-*.json`.
2. Open the JSON file in any text editor.
3. Find the `"command"` array — it contains the exact mpv command that was
   (or would have been) run.
4. Paste the command array contents into a bug report.

The file is self-contained: no log configuration, no terminal, no mpv
restart required.

**To enable always-on diagnostic capture** (recommended while investigating
a recurring issue):

```ini
# script-opts/webm.conf
debug_mode=yes
```

This writes a diagnostic file for every encode, including successful ones,
so the user can compare a working run against a failing run.

---

## 7. What Would Have Caught FIND-001

FIND-001: `--ovcopts-add=minrate=nilk` injected into the command when
`options.strict_filesize_constraint` is true but `bitrate` is nil
(a variable-capture bug at L1779 — `bitrate` should be `video_bitrate`).

The diagnostic file's `"command"` field would have shown:

```json
"command": [
  "mpv",
  "D:\\Videos\\source.mkv",
  "--start=00:01:00.000",
  "--end=00:01:30.000",
  ...
  "--ovcopts-add=minrate=nilk",
  "--ovcopts-add=maxrate=nilk",
  ...
]
```

The literal string `"nilk"` (Lua's `tostring(nil)` appended to `"k"`) is
immediately visible without any log configuration, without reproducing the
issue in a terminal, and without knowing which mpv flag is malformed.  A
user filing a bug report with this JSON would have provided the root cause
in the first message.

The existing `msg.verbose` call at L1855 logs the same command line, but
only appears in mpv's log at verbose level — invisible unless `--log-file`
and `-v` are both configured, which no default user does.

---

## Appendix: Module File Location

```
scripts/webm.lua                              (target — not modified)
re-workspace/deliverables/webm-diagnostic-module.lua   (prototype)
```

To integrate, copy or inline `webm-diagnostic-module.lua` content into
`webm.lua` before the `encode` function definition, then add the two
integration call sites described in the prototype's header comments.
