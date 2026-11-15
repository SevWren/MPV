# ISSUE-002 Bug Diagnosis: MP4 Export Hangs — 0-byte / "moov atom not found"

**Repository**: SevWren/MPV
**Script**: `scripts/webm.lua` (MoonScript-compiled Lua, 2856 lines)
**mpv build**: `mpv-x86_64-20261114-git-649001d4e2` (LuaJIT 2.1, clang)
**Platform**: Windows 10
**Date**: 2026-11-15

---

## 1. Issue Disambiguation

The user's console output begins:

```
[cplayer] Auto-loading profile 'extension.mp4'
[cplayer] Playing: D:\ProgramData\asus\New folder\Tulsa-Union-High-Sch001-...
[ffmpeg/demuxer] moov atom not found
[ffmpeg/demuxer] 3gp, 3g2,mj2: moov atom not found
[cplayer] Failed to recognize file format.
```

**This is NOT the encode subprocess output.** The `[cplayer]` prefix identifies the main mpv player process — the one the user is operating interactively. The player is trying to *play* a file. The critical clue is the path:

- **Source file** (what the user is watching): lives inside `D:\ProgramData\asus\New folder\`
- **Export destination** (`output_directory=D:\ProgramData\asus`): the parent directory, one level up

The most probable chain of events:

1. User presses `W` to export. webm.lua calls `encode()`.
2. `encode()` builds a malformed mpv command (see Section 3) and launches it detached (`run_detached=yes`).
3. The detached `mpv.exe` process receives invalid options, exits immediately with code 1 — **silently**, because `run_detached=yes` returns without checking the exit code (L1858).
4. No output file is written, OR a 0-byte file is written (MP4 container is not finalised because mpv never wrote the `moov` atom).
5. The user, expecting the encode to be running, sees 0% CPU and suspects a hang.
6. The user then opens `D:\ProgramData\asus\` and tries to play the 0-byte export. mpv's demuxer reports `moov atom not found` because the file is empty/truncated — there is no moov atom in a 0-byte file.

The source file `Tulsa-Union-High-Sch001-...` in the `New folder` subdirectory may also be corrupt (the same `moov atom not found` error would appear), but that is a **separate possibility**. The confirmed root cause below explains the 0-byte export regardless of whether the source file is intact.

---

## 2. Root Cause: FIND-001 (Confirmed)

**File**: `re-workspace/canonical/webm.lf.lua`
**Lines**: 1779–1780

```lua
-- L1776-1781 (strict_filesize_constraint branch)
if options.strict_filesize_constraint then
  local type = format.videoCodec ~= "" and "ovc" or "oac"
  append(command, {
    "--" .. tostring(type) .. "opts-add=minrate=" .. tostring(bitrate) .. "k",   -- L1779
    "--" .. tostring(type) .. "opts-add=maxrate=" .. tostring(bitrate) .. "k"    -- L1780
  })
end
```

The variable `bitrate` is **never defined** in `encode()`. The correct variable is `video_bitrate`, which was computed at L1765:

```lua
local video_bitrate, audio_bitrate = calculate_bitrate(supported_active_tracks, format, length)
```

In Lua, referencing an undefined local returns `nil`. `tostring(nil)` = `"nil"`. The resulting options become:

```
--ovcopts-add=minrate=nilk
--ovcopts-add=maxrate=nilk
```

mpv does not recognise `nilk` as a valid bitrate value. It rejects the command and exits non-zero immediately. Because `run_detached=yes` is set, the script calls `utils.subprocess_detached()` (L1858) and never observes the failure.

**webm.conf triggers this path because**:
- `strict_filesize_constraint=yes` — enters the strict branch
- `target_filesize=9800` — `> 0`, so the bitrate block is active
- `run_detached=yes` — failure is completely silent

---

## 3. Command Reconstruction

For the reported configuration and a hypothetical 10-second clip:

| Step | Line(s) | Command fragment appended |
|------|---------|--------------------------|
| Base args | 1708–1714 | `mpv <path> --start=0.000000 --end=10.000000 --loop-file=no --no-pause` |
| Codec flags | 1715 | `--ovc=libx264 --oac=aac` |
| Format flags | 1758 | _(empty for MP4)_ |
| Bitrate (video) | 1767–1769 | `--ovcopts-add=b=7776k` _(9800×8 − 64×10 = 77760 kb; 77760/10 = 7776 kbps)_ |
| Bitrate (audio) | 1771–1774 | `--oacopts-add=b=64k` |
| **FIND-001 BUG** | **1779–1780** | **`--ovcopts-add=minrate=nilk --ovcopts-add=maxrate=nilk`** |
| additional_flags | 1790–1792 | `cq-level=28` _(bare, no `--` — FIND-011)_ |
| Output | 1815–1817 | `--o=D:\ProgramData\asus\<filename>.mp4` |

**Full reconstructed malformed command**:
```
mpv
  "D:\ProgramData\asus\New folder\Tulsa-..._001.mp4"
  --start=0.000000
  --end=10.000000
  --loop-file=no
  --no-pause
  --ovc=libx264
  --oac=aac
  --ovcopts-add=b=7776k
  --oacopts-add=b=64k
  --ovcopts-add=minrate=nilk        <-- FIND-001: causes immediate failure
  --ovcopts-add=maxrate=nilk        <-- FIND-001: causes immediate failure
  cq-level=28                        <-- FIND-011: treated as filename by mpv
  "--o=D:\ProgramData\asus\<out>.mp4"
```

mpv rejects `nilk`, logs an error to its own stderr (which the user never sees because the process is detached), and exits. Output file is not created or is 0 bytes.

---

## 4. Secondary Issue: FIND-011 — `additional_flags` Configuration Gap

**File**: `re-workspace/canonical/webm.lf.lua`
**Lines**: 1790–1792

```lua
for token in string.gmatch(options.additional_flags, "[^%s]+") do
  command[#command + 1] = token
end
```

The user's config contains:
```
additional_flags= cq-level=28
```

The gmatch tokeniser splits on whitespace and appends each token literally. The leading space means the first (and only) token is `cq-level=28` — no `--` prefix. mpv receives this as a positional argument and interprets it as a **filename to play**, not a flag. This would produce a secondary error even if FIND-001 were fixed.

**Classification**: Both a user-configuration error AND a documentation/validation gap in webm.lua:

- **User error**: The flag should be written `--cq-level=28` with a leading `--`.
- **Additional error**: `cq-level` is a libvpx-only option (VP8/VP9). It has no meaning for H.264 (`libx264`). The user is likely copying config from a webm/VP8 workflow and applying it to an MP4 export.
- **Documentation gap**: The configuration reference does not explicitly warn that `additional_flags` values must include the `--` prefix.
- **Validation gap**: webm.lua does not warn or error when a token in `additional_flags` lacks a `--` prefix.

This is logged as **FIND-011** (new defect, medium severity) in `findings/findings.jsonl`.

---

## 5. Phase 3: Hypotheses (Ranked)

| Rank | ID | Hypothesis | Prediction | Probability |
|------|----|------------|------------|-------------|
| 1 | H1 | `bitrate` undefined at L1779 → `nilk` in minrate/maxrate → mpv encode rejects → silent failure (`run_detached`) | Removing `strict_filesize_constraint=yes` or applying FIND-001 patch stops the `nilk` injection and encode succeeds | **HIGH** — directly confirmed by static analysis of L1779-1780 and webm.conf values |
| 2 | H2 | `additional_flags= cq-level=28` without `--` prefix → mpv treats as filename → command error | Removing `additional_flags` or changing to `--cq-level=28` eliminates the bare-token argument; encode command becomes valid (modulo H1) | **HIGH** — confirmed by static analysis; independently produces a malformed command |
| 3 | H4 | Console output shows mpv *playing* a corrupt source file, unrelated to webm.lua | If source file `Tulsa-...` is independently corrupt, the `moov atom not found` error appears on *play*, not on export | **MEDIUM** — plausible co-occurrence; does not explain 0-byte export output |
| 4 | H3 | `output_directory=D:\ProgramData\asus` path has no trailing separator → path join issue | `utils.join_path()` should handle the missing separator; on Windows mpv paths should still resolve | **LOW** — Lua's `utils.join_path` handles this correctly; not the primary cause |
| 5 | H5 | `run_detached=yes` + `display_progress=yes` conflict → unexpected behavior | On Windows, detached mode skips the progress-display path entirely (L1856 returns before reaching the `EncodeWithProgress` branch); no functional conflict | **LOW** — confirmed no code-path conflict; display_progress is ignored when run_detached is true |

---

## 6. Phase 5: Fix Summary

### Fix 1 — FIND-001 (patch file: `deliverables/patches/FIND-001-v2-strict-bitrate-fix.patch`)

Replace `bitrate` with `video_bitrate` at L1779–1780:

```diff
-          "--" .. tostring(type) .. "opts-add=minrate=" .. tostring(bitrate) .. "k",
-          "--" .. tostring(type) .. "opts-add=maxrate=" .. tostring(bitrate) .. "k"
+          "--" .. tostring(type) .. "opts-add=minrate=" .. tostring(video_bitrate) .. "k",
+          "--" .. tostring(type) .. "opts-add=maxrate=" .. tostring(video_bitrate) .. "k"
```

After this fix, `--ovcopts-add=minrate=7776k --ovcopts-add=maxrate=7776k` are generated (for the reported config and a 10-second clip).

### Fix 2 — FIND-011 (configuration fix for user; documentation fix for webm.lua)

**User-side**: Change `webm.conf`:
```
# Before (broken):
additional_flags= cq-level=28

# After — correct prefix AND valid codec option for H.264:
additional_flags=--preset=fast
# OR: remove entirely if no additional flags needed:
additional_flags=
```

`cq-level` is libvpx-specific; for `libx264` the equivalent constant-quality option is `crf`, which webm.lua handles natively via `options.crf`.

**Code-side**: webm.lua should emit a warning when a token in `additional_flags` does not start with `--`. This is a validation gap (FIND-011).

---

## 7. Information Still Needed from Reporter

1. **What files appear in `D:\ProgramData\asus\` after pressing `W`?** (name + size in bytes) — if a file exists but is 0 bytes this confirms FIND-001; if no file appears at all this may indicate a path error.

2. **Is `D:\ProgramData\asus\New folder\Tulsa-...` the source file you are trying to export from, or is it a previous export?** — this disambiguates whether the `moov atom not found` error is from playing a corrupt source or a 0-byte export.

3. **Does removing `strict_filesize_constraint=yes` (or setting it to `no`) from `webm.conf` make the export succeed?** — this is the fastest verification of FIND-001.

4. **Does changing `additional_flags=` to empty make any difference?** — isolates FIND-011.

---

## 8. Recommended Immediate Fix

Change `webm.conf` to:

```conf
output_directory=D:\ProgramData\asus
run_detached=yes
output_format=mp4
strict_filesize_constraint=no
target_filesize=9800
additional_flags=
non_strict_additional_flags=
display_progress=yes
twopass=no
strict_bitrate_multiplier=1
strict_audio_bitrate=64
```

This disables the strict-bitrate path entirely, side-stepping FIND-001 until the patch can be applied to `webm.lua`. It also removes the invalid `cq-level=28` flag.

For a code fix, apply `deliverables/patches/FIND-001-v2-strict-bitrate-fix.patch` to `scripts/webm.lua`.

---

## 9. Windows-Specific Notes

With `run_detached=yes` on Windows, `utils.subprocess_detached()` creates a second `mpv.exe` process via the Windows `CreateProcess` API (no console window). If that process receives `--ovcopts-add=minrate=nilk`, it logs the error to its own stderr and exits immediately. The **player** `mpv.exe` process (the one showing `[cplayer]`) continues running normally — it is not the encode process. This creates the appearance of a "hang at 0% CPU": the user expects encode activity but the encode process never ran. The player sits idle, consuming ~0% CPU, while the user waits.

The "0% CPU hang" is therefore the **player process idling**, not an encode process stuck in a loop. There is no actual hang; the encode process already exited.

---

## 10. Feedback Loop Test

**File**: `harness/tests/test_issue_002_feedback_loop.py`

Run:
```
python3 re-workspace/harness/tests/test_issue_002_feedback_loop.py
```

- **RED**: Both bugs confirmed present in canonical source (exit code 1)
- **GREEN**: After FIND-001 patch applied and additional_flags corrected (exit code 0)

The test confirmed **RED** on the unpatched canonical source, with the full malformed command printed including `--ovcopts-add=minrate=Nonek` / `maxrate=Nonek` and bare `cq-level=28` token.
