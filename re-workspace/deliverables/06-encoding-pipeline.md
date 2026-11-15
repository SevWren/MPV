# 06 — Encoding Pipeline

**Purpose**: End-to-end description of the encoding workflow.
**Audience**: Developers, integrators.
**Source hash**: sha256:3f454dc0ca030b591d659f7405a3ddfdf7585e5b5eb4cd5b3a573b4151b33214
**Generation date**: 2026-11-15

---

## Overview

The encoding pipeline converts a time range (startTime, endTime) and optional crop region into an output media file by constructing and executing an mpv sub-process command.

## Entry Point

`encode(region, startTime, endTime)` at L1697. Called from `MainPage:encode()` (L2735).

## Step-by-Step

### 1. Format Lookup (L1698)
```lua
local format = formats[options.output_format]
```
**BUG**: Returns nil if `options.output_format` doesn't match a registry key (e.g., default "mp4 (h264/AAC)").

### 2. Path Resolution (L1702)
`find_path(startTime, endTime)`:
- Gets `mp.get_property('path')`.
- If path doesn't exist on disk: `is_stream = true`.
- For HLS: dumps cache to `~/cache_dump.ts`, resets times to relative.

### 3. Base Command (L1707-1714)
```
["mpv", path, "--start=HH:MM:SS.mmm", "--end=HH:MM:SS.mmm", "--loop-file=no", "--no-pause"]
```

### 4. Codec Flags (L1715)
From `format:getCodecFlags()`: `["--ovc=CODEC", "--oac=CODEC"]`.

### 5. Track Selection (L1716-1754)
- Video: `--vid=N` or `--vid=no`
- Audio: `--aid=N` or `--lavfi-complex=[aid1][aid2]amix[ao]` for multi-track
- Sub: `--sid=N` or `--sid=no`
- External: `--audio-file=PATH` or `--sub-file=PATH`

### 6. Video Encode Flags (L1755-1757)
`get_video_encode_flags(format, region)`:
- Playback options (sub-ass-override, deinterlace, etc.)
- Video filters as `--vf-add=FILTER`:
  - `format:getPreFilters()`
  - Current mpv vf chain (if `apply_current_filters=true`)
  - Crop: `lavfi-crop=W:H:X:Y` (if region valid)
  - Scale: `lavfi-scale=-2:HEIGHT` (if `scale_height > 0`)
  - FPS: `fps=N` (if `fps > 0`)
  - EQ: `lavfi-eq=contrast=X:saturation=Y:brightness=Z`
  - `format:getPostFilters()`
- Speed filters (if speed ≠ 1)

### 7. Format Flags (L1758)
`format:getFlags()` — e.g., VP9 threads.

### 8. Metadata (L1759-1761)
If `write_filename_on_metadata=true`: `--oset-metadata=title=%N%FILENAME`.

### 9. Bitrate (L1762-1801)
If `acceptsBitrate=true` and `target_filesize > 0`:
```
video_bitrate_kbps = floor(target_filesize * 8 / duration)
audio_bitrate_kbps = (strict mode) floor(strict_audio_bitrate)
```
Adds `--ovcopts-add=b=Vk`, `--oacopts-add=b=Ak`.

For non-strict: also adds `non_strict_additional_flags` and CRF if set.
**BUG**: strict mode references undefined `bitrate` variable (L1779).

### 10. Additional Flags (L1790-1796)
Both `additional_flags` and (non-strict) `non_strict_additional_flags` tokenized by whitespace and appended.

### 11. Output Path (L1803-1817)
- Directory: source dir, or `~` for streams, or `options.output_directory`.
- Filename: `format_filename(originalStartTime, originalEndTime, format)`.
- Combined: `utils.join_path(dir, formatted_filename)`.
- Appended as `--o=OUTPUT_PATH`.

### 12. Encode Started Event (L1818)
`emit_event("encode-started")`.

### 13. 2-Pass (L1819-1851)
If `twopass=true AND format.supportsTwopass=true AND NOT is_stream`:
1. Copy command + `--ovcopts-add=flags=+pass1`.
2. `run_subprocess(first_pass_cmd)`.
3. For libvpx: `vp8_patch_logfile()`.
4. Add `--ovcopts-add=flags=+pass2` to main command.

### 14. postCommandModifier (L1853)
`format:postCommandModifier(command, region, startTime, endTime)` — format-specific final processing (GIF completely rewrites filter chain).

### 15. Dispatch (L1856-1872)
- `run_detached=true`: `mp.utils.subprocess_detached(args=command)` → non-blocking.
- `display_progress=false`: `run_subprocess(args=command)` → blocking.
- `display_progress=true`: `EncodeWithProgress:startEncode(command)` → blocking with OSD.

### 16. Result and Cleanup (L1873-1884)
- Success: `message("Encoded successfully!")`, `emit_event("encode-finished", "success")`.
- Failure: `message("Encode failed!")`, `emit_event("encode-finished", "fail")`.
- Cleanup: `os.remove(logfile)` (unchecked), `os.remove(temp_file)` if is_temporary.
- **BUG**: cleanup not reached when `run_detached=true`.
