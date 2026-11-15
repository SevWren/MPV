# 04 — Configuration Reference

**Purpose**: Complete reference for all 24 configuration options.
**Audience**: Users, integrators.
**Source hash**: sha256:3f454dc0ca030b591d659f7405a3ddfdf7585e5b5eb4cd5b3a573b4151b33214
**Generation date**: 2026-11-15

---

## Configuration Methods

1. **Script-opts file**: `~/.config/mpv/script-opts/webm.conf`
2. **Command-line**: `mpv --script-opts=webm-keybind=X`
3. **IPC message**: `mpv-webm-set-options` script message (WARNING: no validation)
4. **UI**: EncodeOptionsPage (11 options only)

## Complete Options Table

### keybind
- **Default**: `"W"`
- **Type**: string
- **Description**: mpv key name to toggle the main UI.
- **UI settable**: No
- **Notes**: Bound at startup; changing via IPC after load has no effect.

### output_directory
- **Default**: `""` (empty)
- **Type**: string (path)
- **Description**: Directory for output files. Empty = same directory as source file. For streams, defaults to home directory.
- **UI settable**: No

### run_detached
- **Default**: `true`
- **Type**: boolean
- **Description**: If true, the encoding process is detached (non-blocking). If false, mpv waits for completion with an optional progress overlay.
- **UI settable**: No
- **Notes**: When true, temp files are not cleaned up after encode.

### output_template
- **Default**: `"%F-[%s-%e]%M"`
- **Type**: string (template)
- **Description**: Output filename template. Supports substitution tokens.
  - `%F` — source filename without extension
  - `%s` / `%e` — start/end time in path-safe format
  - `%T` — output file extension
  - `%M` — media title (from mpv property)
  - `%wH/%wM/%wS` — start time components
  - `%mH/%mM/%mS` — end time components
- **UI settable**: No

### scale_height
- **Default**: `-1`
- **Type**: number (integer)
- **Description**: Output video height in pixels. -1 = use source height. Scale preserves aspect ratio (`-2:HEIGHT`).
- **UI settable**: Yes (list: -1, 144, 240, 360, 480, 540, 720, 1080, 1440, 2160)

### fps
- **Default**: `-1`
- **Type**: number
- **Description**: Output frame rate. -1 = use source frame rate.
- **UI settable**: Yes (list: source, 15, 24, 30, 48, 50, 60, 120, 240)

### target_filesize
- **Default**: `10000`
- **Type**: number (kilobytes)
- **Description**: Target output file size in kilobytes. 0 = constant quality mode (no bitrate limit).
- **UI settable**: Yes (int, min=0, step=250)

### strict_filesize_constraint
- **Default**: `false`
- **Type**: boolean
- **Description**: If true, adds minrate/maxrate constraints for strict file size. **WARNING: Triggers a crash bug (FIND-001)**. Use with caution.
- **UI settable**: Yes

### strict_bitrate_multiplier
- **Default**: `0.95`
- **Type**: number
- **Description**: **UNUSED**. Declared but never referenced in any calculation. No effect.
- **UI settable**: No

### strict_audio_bitrate
- **Default**: `128`
- **Type**: number (kbps)
- **Description**: Audio bitrate reserved in strict filesize mode.
- **UI settable**: No

### output_format
- **Default**: `"mp4 (h264/AAC)"` (**NOTE**: this default is broken — use "mp4" instead)
- **Type**: string (format registry key)
- **Description**: Output format identifier. Must match a key in the formats registry.
  Valid values: `webm-vp8`, `webm-vp9`, `mp4`, `mp4-nvenc`, `mp3`, `gif`.
  **Do not use** `raw` (crashes).
- **UI settable**: Yes

### twopass
- **Default**: `false`
- **Type**: boolean
- **Description**: Enable 2-pass encoding. Only effective for formats with `supportsTwopass=true` (webm-vp8, mp4, mp4-nvenc) and non-stream sources.
- **UI settable**: Yes

### apply_current_filters
- **Default**: `false`
- **Type**: boolean
- **Description**: Apply mpv's current video filter chain (vf) to the encoded output.
- **UI settable**: Yes

### write_filename_on_metadata
- **Default**: `false`
- **Type**: boolean
- **Description**: Write the source filename to the output file's metadata title field.
- **UI settable**: Yes

### libvpx_threads
- **Default**: `4`
- **Type**: number (integer)
- **Description**: Thread count for VP9 (libvpx-vp9) encoding.
- **UI settable**: No

### additional_flags
- **Default**: `""`
- **Type**: string (space-separated mpv flags)
- **Description**: Extra mpv flags appended to the encode command. Tokenized by whitespace. Values with embedded spaces cannot be used.
- **UI settable**: No
- **Security note**: Values are individually shell-quoted; metacharacters are safe. However, `--o=PATH` in this field overrides the computed output path.

### crf
- **Default**: `-1`
- **Type**: number (integer)
- **Description**: CRF (Constant Rate Factor) value. -1 = disabled. Applied in non-strict mode only.
- **UI settable**: Yes (int, min=-1, step=1; -1 displays as "disabled")

### non_strict_additional_flags
- **Default**: `"cq-level=28"`
- **Type**: string (space-separated mpv flags)
- **Description**: Extra flags added in non-strict filesize mode. Default applies VP8/VP9 quality constraint.
- **UI settable**: No

### display_progress
- **Default**: `"true"`
- **Type**: string ("true", "false", "auto")
- **Description**: Whether to show progress overlay during encoding. "auto" = enabled on non-Windows. Only effective when `run_detached=false`.
- **UI settable**: No

### font_size
- **Default**: `28`
- **Type**: number
- **Description**: OSD overlay font size.
- **UI settable**: No

### margin
- **Default**: `10`
- **Type**: number (pixels)
- **Description**: OSD overlay margin in pixels.
- **UI settable**: No

### message_duration
- **Default**: `5`
- **Type**: number (seconds)
- **Description**: Duration for OSD status messages.
- **UI settable**: No

### gif_dither
- **Default**: `0`
- **Type**: number (integer 0-6)
- **Description**: GIF dither algorithm for palette generation.
  0-5: bayer_scale 0-5; 6: sierra2_4a.
- **UI settable**: Yes (visible only when format = gif)

### force_square_pixels
- **Default**: `false`
- **Type**: boolean
- **Description**: Force 1:1 pixel aspect ratio by scaling `iw*sar:ih`.
- **UI settable**: Yes
