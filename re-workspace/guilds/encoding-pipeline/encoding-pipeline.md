# Encoding Pipeline Guild Report

## Overview

The encoding pipeline converts a time range + optional crop region into an output media file by constructing and executing an mpv command line with appropriate codec/filter arguments.

## High-Level Flow

```
User: press 'e' in MainPage
  → MainPage.encode(region, startTime, endTime)
    → find_path(startTime, endTime)
    → encode(region, startTime, endTime)
      → build command[]
      → 2-pass or 1-pass dispatch
        → run_subprocess | run_subprocess_popen | subprocess_detached
      → cleanup
```

## Command Construction Order

```
1. ["mpv", path,
    "--start=HH:MM:SS.mmm",
    "--end=HH:MM:SS.mmm",
    "--loop-file=no",
    "--no-pause"]

2. format:getCodecFlags()
   → ["--ovc=VCODEC", "--oac=ACODEC"]

3. Track flags:
   → ["--vid=N"] or ["--audio-file=PATH"] or ["--vid=no"]
   → ["--aid=N"] or ["--lavfi-complex=[aid1][aid2]amix[ao]"]
   → ["--sid=N"] or ["--sid=no"]

4. get_video_encode_flags(format, region):
   → get_playback_options() → ["--sub-ass-override=V", ...]
   → get_video_filters() as ["--vf-add=FILTER", ...]
     → format:getPreFilters()
     → apply_current_filters() (if option enabled)
     → "lavfi-crop=W:H:X:Y" (if region valid)
     → get_scale_filters()   → "lavfi-scale=..."
     → get_fps_filters()     → "fps=N"
     → get_contrast_brightness_saturation_filters()
     → format:getPostFilters()
   → get_speed_flags() → ["--vf-add=setpts=...", "--af-add=atempo=...", "--sub-speed=..."]

5. format:getFlags()
   → VP9: ["--ovcopts-add=threads=N"]
   → others: []

6. get_metadata_flags() (if option enabled)
   → ["--oset-metadata=title=%N%FILENAME"]

7. Bitrate flags (if acceptsBitrate and target_filesize > 0):
   → ["--ovcopts-add=b=Vk", "--oacopts-add=b=Ak"]
   → (strict) ["--ovcopts-add=minrate=Vk", "--ovcopts-add=maxrate=Vk"]  [BUG: uses undefined 'bitrate']

8. Non-strict additional flags (if not strict):
   → options.non_strict_additional_flags (tokenized by whitespace)
   → (if crf >= 0) ["--ovcopts-add=crf=N"]

9. options.additional_flags (tokenized by whitespace)

10. ["--o=OUTPUT_PATH"]
```

## Per-Format Variations

### WebM VP8 (libvpx)
- postCommandModifier (2-pass): patches VP8 firstpass logfile with vp8_patch_logfile
- getPostFilters: colorspace bt709 filter
- supportsTwopass: true

### WebM VP9 (libvpx-vp9)
- getFlags: adds `--ovcopts-add=threads=N`
- supportsTwopass: false

### MP4 H.264 (libx264)
- No overrides beyond base
- supportsTwopass: true

### MP4 NVENC (h264_nvenc)
- No overrides beyond base
- Requires NVIDIA GPU

### MP3 (libmp3lame)
- videoCodec = "" → no --ovc flag
- Video filters skipped (no videoCodec)
- supportsTwopass: false

### GIF
- postCommandModifier completely replaces filter chain
- Output: `--vf-add=lavfi=[palettegen filtergraph]`, `--of=lavfi`, `--ovc=gif`
- acceptsBitrate: false → no bitrate flags
- supportsTwopass: false

## 2-Pass Encoding Flow (WebmVP8, MP4*)

```
Phase 1:
  copy command + ["--ovcopts-add=flags=+pass1"]
  run_subprocess(first_pass_cmd)
  if libvpx: vp8_patch_logfile(out_path + "-video-pass1.log", duration)

Phase 2:
  original command + ["--ovcopts-add=flags=+pass2"]
  format:postCommandModifier(command, ...)
  → run_subprocess | EncodeWithProgress
```

## Output File Naming

Template: `options.output_template` (default: `"%F-[%s-%e]%M"`)

Substitutions (from format_filename):
- `%F` → media filename without extension
- `%s` / `%e` → start/end time in path-safe format (dots not colons)
- `%T` → output file extension
- `%M` → media title (from mpv property, via expand_properties)
- `%wH/%wM/%wS` → wall-clock time components

Output directory: `options.output_directory` (default: same dir as source file, or ~ for streams).

## Execution Modes

| Mode | Trigger | Mechanism |
|------|---------|-----------|
| Detached | run_detached=true | mp.utils.subprocess_detached (non-blocking) |
| Blocking quiet | display_progress=false or Windows | mp.utils.subprocess (blocking argv) |
| Blocking progress | display_progress=true (non-Windows) | io.popen + EncodeWithProgress overlay |

## Bitrate Calculation

```
target_filesize: N KB (kilobytes, NOT kilobits)
total_kilobits = N * 8

if strict AND has_audio:
  audio_kilobits = duration_secs * strict_audio_bitrate
  video_kilobits = total_kilobits - audio_kilobits

video_bitrate_kbps = floor(video_kilobits / duration_secs)
audio_bitrate_kbps = floor(audio_kilobits / duration_secs)
```

Default `target_filesize = 10000` (10 MB), `strict_audio_bitrate = 128` (kbps).

## Known Bugs in Pipeline

1. **L1779**: `bitrate` undefined in strict constraint minrate/maxrate assignment → runtime error.
2. **L1365**: `append(copy_command_line, {})` → no-op, vestigial.
3. **L1698**: `formats[options.output_format]` returns nil on first run with default "mp4 (h264/AAC)" → crash.
4. **L2368**: "raw" in formatIds → `formats["raw"].displayName` crash when EncodeOptionsPage instantiated.
5. **L620**: `get_duration` undefined variable → runtime error if called (not called in normal flow).
