# ISSUE-002 Immediate User Workaround
# No code changes required — webm.conf edits only

## Background

The encode subprocess launched by webm.lua inherits the user's full `mpv.conf` because
no `--no-config` or `--load-scripts=no` flag is passed to the child mpv process.
This means settings like `keep-open=yes`, `hwdec=auto-copy`, `loop-playlist=inf`,
and all auto-loaded scripts (ytdl_hook.lua, autoload.lua, webm.lua itself) are active
in the encoder subprocess.

Additionally, the confirmed FIND-001 bug (`bitrate` undefined at L1779-1780) produces
`--ovcopts-add=minrate=nilk` which immediately kills the encode subprocess when
`strict_filesize_constraint=yes` is set.

The `additional_flags` token `cq-level=28` (missing `--` prefix) is also appended as
a bare positional argument, which mpv treats as a second input filename.

---

## Workaround 1 — Minimal Fix

Addresses the config-inheritance issue most likely to cause a hang or silent failure.

Edit `%APPDATA%\mpv\script-opts\webm.conf`:

```conf
# Change this line:
additional_flags= cq-level=28

# To this:
additional_flags=--keep-open=no --load-scripts=no
```

**What this fixes:**
- `--keep-open=no`: Overrides `keep-open=yes` from the user's mpv.conf in the encode
  subprocess. Without this override the encoder may not finalize the output file because
  mpv waits for the user to close the player rather than exiting when done.
- `--load-scripts=no`: Prevents webm.lua, ytdl_hook.lua, autoload.lua and any other
  user scripts from loading inside the encode subprocess. This eliminates the risk of
  scripts interfering with the encode.
- Removes the bare `cq-level=28` token that was being passed as a filename.

**What this does NOT fix:**
- FIND-001 (`--ovcopts-add=minrate=nilk`): If `strict_filesize_constraint=yes` is still
  set, the broken nilk flags will still be injected. Combine with the FIND-001 workaround:
  set `strict_filesize_constraint=no`.
- GPU hardware decode inherited from mpv.conf: `hwdec=auto-copy` is not explicitly
  overridden. Add `--hwdec=no` if you experience GPU resource errors during encode.

---

## Workaround 2 — Complete Fix

Addresses all config-inheritance issues comprehensively.

Edit `%APPDATA%\mpv\script-opts\webm.conf`:

```conf
# Change this line:
additional_flags= cq-level=28

# To this:
additional_flags=--no-config --load-scripts=no --keep-open=no --hwdec=no
```

**What each flag does:**

| Flag | Effect |
|------|--------|
| `--no-config` | Prevents the encode subprocess from loading mpv.conf entirely. The encode subprocess starts with clean defaults. |
| `--load-scripts=no` | Prevents all auto-loaded scripts (ytdl_hook.lua, autoload.lua, webm.lua, etc.) from running inside the encoder. |
| `--keep-open=no` | Ensures the encoder exits when done, rather than waiting indefinitely for user interaction. |
| `--hwdec=no` | Disables GPU hardware decoding in the encoder subprocess. Avoids GPU resource conflicts when both player and encoder try to use the same hardware decoder simultaneously. |

**Combined with FIND-001 workaround** (set `strict_filesize_constraint=no`), the full
recommended webm.conf fix is:

```conf
output_directory=D:\ProgramData\asus
run_detached=yes
output_format=mp4
strict_filesize_constraint=no
target_filesize=9800
additional_flags=--no-config --load-scripts=no --keep-open=no --hwdec=no
non_strict_additional_flags=
display_progress=yes
twopass=no
strict_bitrate_multiplier=1
strict_audio_bitrate=64
```

---

## Note on `cq-level=28`

`cq-level` is a **libvpx** codec option, used for VP8/VP9 (`.webm` output). It has no
meaning for `libx264` (H.264 / `.mp4` output). Using it with `--ovc=libx264` is a no-op
at best and an error at worst depending on the ffmpeg version.

For H.264 quality control, the correct option is `crf` (Constant Rate Factor). webm.lua
already has a built-in option for this:

```conf
# In webm.conf, set the CRF value directly:
crf=28
```

If you want to pass it via `additional_flags` instead:

```conf
# Correct H.264 quality flag via additional_flags:
additional_flags=--no-config --load-scripts=no --keep-open=no --hwdec=no --ovcopts-add=crf=28
```

**Summary**: Remove `cq-level=28` from `additional_flags`. Use `crf=28` in webm.conf,
or `--ovcopts-add=crf=28` in `additional_flags` if you need it there.
