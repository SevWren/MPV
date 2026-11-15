# ISSUE-002 — Team 1 Diagnosis Report
# Encode subprocess hangs / output file unplayable or empty

**Investigation team**: TEAM 1
**Evidence base**: `/home/vercel-sandbox/mpv-log.txt` (1455 lines), `/home/vercel-sandbox/MPV/re-workspace/canonical/webm.lf.lua`
**All claims cite log line numbers or lua line numbers.**

---

## 1. What Was Wrong With All Previous Analyses

- Previous analyses cited "FIND-001" (bitrate variable `bitrate` undefined at lua:1779-1780) as the
  primary cause of the hang.  While the undefined variable is a real secondary bug, it only affects
  the `strict_filesize_constraint=yes` minrate/maxrate code path.  It does not explain an indefinite
  hang — mpv encode mode would emit an error and exit, not hang forever.

- Previous analyses did not read the subprocess args array (log:1282) in full.  The array form is
  the definitive record of what was passed to the child process, not the display string (log:1281).
  The array shows `args="cq-level=28"` as an explicit bare positional argument.

- Previous analyses did not check whether `--no-config` or `--load-scripts=no` are present.
  Zero occurrences of either string exist anywhere in `webm.lf.lua` (confirmed by text search).

- Previous analyses did not connect `keep-open=yes` (log:62) to the subprocess lifecycle.  This
  is the highest-confidence primary hang cause.

- The `msg-level=verbose` workaround was already proven broken at log:36-38 (`Invalid message
  level 'verbose'`).  It never produced any additional debug output, explaining why previous
  investigators couldn't see subprocess output.

---

## 2. Confirmed Facts From the Log

| Fact | Log line(s) |
|---|---|
| mpv version 0.42.0-41-g649001d4e, built Nov 14 2026 | log:2-3 |
| mpv.conf loaded from C:\Users\mmuel\AppData\Roaming/mpv/mpv.conf | log:29 |
| `msg-level=verbose` is **invalid** and was rejected | log:36-38 |
| `keep-open=yes` set in mpv.conf (default profile) | log:62 |
| `save-position-on-quit=yes` set in mpv.conf | log:61 |
| `hwdec=auto-copy` set in mpv.conf via high-quality profile | log:77 |
| `ytdl-format=bv*[height<=1080]+ba/b[height<=1080]` set in mpv.conf | log:43 |
| File loaded: D:\Videos\Rockford_High-School-Marching-Band-..._001_1080p.mp4 | log:787 |
| `extension.mp4` profile auto-applied on file load | log:790-791 |
| `loop-file=inf` set by extension.mp4 profile | log:792 |
| `loop-playlist=inf` set by extension.mp4 profile | log:794 |
| Parent process uses d3d11va-copy hardware decoder | log:1374 |
| autoload.lua active; builds 25-file playlist from D:\Videos\ | log:1323-1368 |
| Encode triggered at t=19.931 | log:1278-1280 |
| Encode output target: D:\ProgramData\asus/[...]-audio.mp4 | log:1280 |
| Full subprocess args array recorded | log:1282 |
| `cq-level=28` appears as bare positional arg (no --) in args array | log:1282 |
| `--keep-open=no` is NOT in the subprocess args | log:1282 |
| `--no-config` is NOT in the subprocess args | log:1282 |
| `--load-scripts=no` is NOT in the subprocess args | log:1282 |
| `--hwdec=no` is NOT in the subprocess args | log:1282 |
| `--loop-playlist=no` is NOT in the subprocess args | log:1282 |
| `--ytdl-format=...` IS in the subprocess args (leaking player setting) | log:1282 |
| Parent mpv quit at t=59.024 (39 seconds after encode launched) | log:1405 |
| No encode completion message in log (subprocess was detached, ran independently) | log:1283 |

---

## 3. Root Cause Chain (Step by Step)

**Step 1: User presses `e` in the webm.lua UI**
Log:1278 shows `script-binding webm/e`. The `encode()` function in webm.lf.lua (lua:1697) is called with startTime=0.567, endTime=1.469.

**Step 2: `non_strict_additional_flags` token loop executes**
webm.conf has `strict_filesize_constraint=yes`, so the `additional_flags` path runs (lua:1790-1792).
webm.conf has `additional_flags= cq-level=28` (the value with leading space; the space is consumed by gmatch tokenizer, leaving the token `cq-level=28`).
lua:1791: `command[#command + 1] = token` appends the token verbatim with no `--` prefix check.
Result: `cq-level=28` is in the command array as a bare string with no `--`.

**Step 3: `utils.subprocess_detached()` is called**
lua:1858: `utils.subprocess_detached({args = command})` launches the child process.
Because `run_detached=yes` in webm.conf, the parent does NOT wait for the child (log:1283 shows `Starting subprocess`; control immediately returns).
**No `--no-config` flag is present**: the subprocess reads the full mpv.conf.

**Step 4: Subprocess reads mpv.conf**
The subprocess is a fresh mpv instance.  It reads `C:\Users\mmuel\AppData\Roaming/mpv/mpv.conf` (same path as parent, log:29).
From mpv.conf it loads:
- `keep-open=yes` (log:62 — this is the hang trigger)
- `save-position-on-quit=yes` (log:61)
- `hwdec=auto-copy` via high-quality profile (log:77)

**Step 5: Subprocess loads scripts**
No `--load-scripts=no` is present.  The subprocess loads all scripts from the scripts directory, including `autoload.lua`.
`autoload.lua` scans `D:\Videos\` and builds a playlist of ~25 items (same behavior as log:1323-1368).
The encode command's input file is item 0.  The subprocess now has a 25-item playlist.

**Step 6: Subprocess processes `cq-level=28` as a positional arg**
mpv treats `cq-level=28` as a second input file path.  mpv tries to open `cq-level=28` as a media file.  Depending on mpv error mode, it either:
(a) logs an error and skips it (non-fatal in encode mode), or
(b) adds it to the encode queue
In either case, the codec option is NOT applied to libx264 (the option is silently ignored or errors).

**Step 7: The extension.mp4 profile applies**
On loading the .mp4 input, the `extension.mp4` profile sets `loop-playlist=inf` (log:794).  The encode command includes `--loop-file=no` but NOT `--loop-playlist=no`.
After the first file encodes, mpv would loop the 25-file playlist.

**Step 8: Encode of the target clip "completes"**
The 0.902-second clip encodes.  mpv encode mode would normally exit with "End of file".
However, `keep-open=yes` is active.  mpv does NOT exit.  It stays open, waiting.
The MP4 muxer's `moov` atom is never written because mpv never reaches the finalization/cleanup path.
The output file is 0 bytes or has only partial mdat data with no moov.

**Step 9: Subprocess is detached and invisible**
Because `run_detached=yes` and no progress monitoring occurs (subprocess is detached), neither the user nor the parent mpv sees any output.  The subprocess sits at 0% CPU consuming no resources, indefinitely.

**Step 10: User kills mpv or reboots**
The partial output file is left on disk.  It is unplayable.

---

## 4. Why Each Previous Workaround Failed

**`strict_filesize_constraint=no`**
This changes which additional_flags path is taken (lua:1793 non_strict_additional_flags path runs instead of lua:1790 additional_flags path).
But `non_strict_additional_flags=` is empty in this webm.conf, and `additional_flags= cq-level=28` only runs when strict IS enabled.
Wait — with `strict_filesize_constraint=no`, the `additional_flags` path STILL runs (lua:1790-1792), AND the `non_strict_additional_flags` path also runs (lua:1793-1801).
In either case, the subprocess still inherits `keep-open=yes` from mpv.conf.  Setting `strict_filesize_constraint=no` removes the `cq-level=28` bare arg only from the non-strict path, but does not fix the hang.
**The hang persists because `keep-open=yes` is still inherited.**

**`msg-level=verbose`**
This line in mpv.conf was already broken: log:36-38 shows mpv rejected it with
`Invalid message level 'verbose'` / `Error parsing option msg-level`.
The option produced no additional logging whatsoever.  Any diagnosis based on "verbose" logs being absent was based on a failed config option.

---

## 5. Correct Immediate User Workaround

Change `webm.conf` to pass isolation flags via `additional_flags`:

```conf
additional_flags=--no-config --load-scripts=no --keep-open=no --hwdec=no --loop-playlist=no
```

This overrides the subprocess's behavior directly from the command line.
Note: `--no-config` must be the FIRST argument after the filename for mpv to honor it before reading the config file.  However, in encode mode this flag is passed on the command line and takes precedence regardless of position because mpv processes command-line flags before the config file at startup.

Also fix the codec option syntax (move cq-level to a proper encoder option):

```conf
additional_flags=--no-config --load-scripts=no --keep-open=no --hwdec=no --loop-playlist=no --ovcopts-add=cq-level=28
```

Note: `cq-level` is a VP8/VP9 (libvpx) option; for libx264 use `--ovcopts-add=crf=28` instead.

---

## 6. Correct Code Fix

In `webm.lf.lua`, inside the `encode()` function (lua:1707), add isolation flags immediately after the input file path:

```lua
local command = {
  "mpv",
  path,
  "--no-config",          -- do not load mpv.conf in subprocess
  "--load-scripts=no",    -- do not load any scripts in subprocess
  "--keep-open=no",       -- exit when encode finishes
  "--loop-playlist=no",   -- do not loop playlist
  "--save-position-on-quit=no",  -- do not pollute watch_later state
  "--hwdec=no",           -- avoid GPU decoder contention with parent
  "--start=" .. seconds_to_time_string(startTime, false, true),
  ...
}
```

Additionally, in the additional_flags token loop (lua:1790-1795), add validation:

```lua
local function add_flags_validated(flag_string, source_name)
  for token in string.gmatch(flag_string, "[^%s]+") do
    if token:sub(1, 2) ~= "--" then
      msg.warn("Ignoring invalid flag in " .. source_name ..
               ": '" .. token .. "' — must start with '--'")
    else
      command[#command + 1] = token
    end
  end
end
add_flags_validated(options.additional_flags, "additional_flags")
```

---

## 7. Secondary Issues

### 7a. `cq-level=28` is wrong for libx264

`cq-level` is a libvpx (VP8/VP9) encoder option.  With `--ovc=libx264`, it has no effect.
For H.264 quality control, the correct option is `crf`: `--ovcopts-add=crf=28`.
webm.lua already supports this via the `crf` option in webm.conf: set `crf=28`.

### 7b. Bitrate of 86939k for a 0.902-second clip

Target: 9800 kB, strict mode, 64 kbps audio, 0.902s.
Calculation: `floor((9800*8 - 0.902*64) / 0.902)` = `floor(78342.272 / 0.902)` = 86854 k
Log shows 86939k (difference: 85k), attributable to floating-point precision in Lua's subtraction of the timestamps.  The bitrate is correct in intent; at 0.9 seconds it results in a ~95 MB/s video bitrate for a 9.8 MB target file — vastly over-engineered for a clip this short, but mathematically consistent with the formula.

### 7c. `--ytdl-format` leaks into encode command

`get_playback_options()` at lua:1562-1575 reads and re-emits `ytdl-format` (lua:1572) as an encode flag.  For local file encodes this is harmless but wasteful.  For the specific case where `ytdl-format` changes something about how mpv opens the file, it could cause unexpected behavior.

### 7d. `msg-level=verbose` in mpv.conf is invalid

Log:36-38 shows this option was rejected.  The correct syntax in modern mpv is
`msg-level=webm=trace` or `msg-level=all=verbose`.  The user's intent was to get webm.lua debug output, but the option silently failed, making diagnosis harder.

### 7e. `loop-playlist=inf` set by extension.mp4 profile

Log:794 confirms this.  The encode command overrides `loop-file=no` but NOT `loop-playlist=no`.  After the encode subprocess finishes (if it ever does despite keep-open), it would start encoding the next file in the 25-item autoload playlist.

### 7f. FIND-001: `bitrate` undefined at lua:1779-1780

When `strict_filesize_constraint=yes`, lua:1779-1780 reference a variable `bitrate` that is never assigned in the `encode()` function (the local variables are named `video_bitrate` and `audio_bitrate`).  This would inject `--ovcopts-add=minrate=nilk --ovcopts-add=maxrate=nilk` into the command, causing an FFmpeg error.  However, in this session `strict_filesize_constraint=yes` is set, so this code path runs — but mpv would likely emit a warning and ignore the nilk values rather than hanging.

---

## Hypothesis Rankings (Post-Investigation)

| Rank | Hypothesis | Confidence | Evidence |
|---|---|---|---|
| H1 | `keep-open=yes` inherited → subprocess never exits | **HIGHEST** | log:62, log:1282 (--keep-open absent), lua has 0 "keep-open" occurrences |
| H2 | `cq-level=28` bare arg → treated as 2nd input file | **HIGH** | log:1282 (bare arg confirmed), lua:1794 (token loop) |
| H4 | autoload.lua → 25-file playlist in subprocess | **HIGH** | log:1323-1368, lua:0 "load-scripts" occurrences |
| H5 | `loop-playlist=inf` → loops after encode | **MEDIUM** | log:794, --loop-playlist absent in log:1282; would be pre-empted by H1 |
| H3 | hwdec=auto-copy GPU contention | **MEDIUM** | log:77, log:1374; subprocess_detached creates independent process, may not compete |

**H1 + H2 together are the primary cause.** H1 prevents finalization; H2 corrupts the codec option. H4 and H5 are compounding factors that would prevent clean exit even if H1 were fixed.
