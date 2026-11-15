# 05 — API Reference: Utility Functions

**Source hash**: sha256:3f454dc0ca030b591d659f7405a3ddfdf7585e5b5eb4cd5b3a573b4151b33214
**Generation date**: 2026-11-15

---

## Encoding Utilities

### `encode(region, startTime, endTime)` — L1697
Main encoding function. See 06-encoding-pipeline.md for full details.

### `find_path(startTime, endTime)` — L1673
Returns `(path, is_stream, is_temporary, startTime, endTime)`. Handles HLS streams.

### `calculate_bitrate(active_tracks, format, length)` — L1657
Returns `(video_bitrate_kbps, audio_bitrate_kbps)`.

### `get_active_tracks()` — L1420
Returns `{video:[], audio:[], sub:[]}` of currently active/visible mpv tracks.

### `get_video_encode_flags(format, region)` — L1643
Returns array of `--vf-add=`, `--sub-ass-override=`, etc. flags.

---

## String/Time Utilities

### `seconds_to_time_string(seconds, no_ms, full)` — L93
Formats seconds as `HH:MM:SS.mmm`. Returns "unknown" for negative input.

### `seconds_to_path_element(seconds, no_ms, full)` — L108
Same as above with `:` replaced by `.` for safe filenames.

### `expand_properties(text, magic)` — L123
Expands `${prop}` / `${?prop:fallback}` templates using mpv properties.

### `format_filename(startTime, endTime, videoFormat)` — L175
Expands output filename template with time and media property substitutions.

### `bold(text)` — L76
Wraps text in ASS bold tags `{\b1}..{\b0}`.

### `trim(s)` — L261
Returns string with leading/trailing whitespace removed.

---

## Subprocess Utilities

### `run_subprocess(params)` — L272
Wraps `mp.utils.subprocess`. Returns bool success.

### `run_subprocess_popen(command_line)` — L303
Shells `shell_escape(command_line) + " 2>&1"` via `io.popen`. Returns file handle.

### `shell_escape(args)` — L283
Quotes argv array for POSIX or Windows shell. Returns concatenated string.

---

## Filesystem Utilities

### `file_exists(name)` — L115
Returns bool. Uses `mp.utils.file_info`.

### `parse_directory(dir)` — L240
Expands `~` and resolves to absolute path via mpv `expand-path` command.

### `get_null_path()` — L265
Returns `"NUL"` on Windows, `"/dev/null"` on POSIX.

### `get_pass_logfile_path(encode_out_path)` — L335
Returns `encode_out_path .. "-video-pass1.log"`.

---

## Base64 Utilities (Global)

### `base64_encode(data)` — L36
Encodes binary string to base64. GLOBAL (not local).

### `base64_decode(data)` — L49
Decodes base64 string to binary. GLOBAL (not local).

---

## Geometry Utilities

### `get_video_dimensions()` — L341
Returns `{top_left, bottom_right, ratios}` or nil.

### `clamp(min, val, max)` — L450
Numeric clamp.

### `clamp_point(top_left, point, bottom_right)` — L460
Clamps {x,y} point to rectangle.

### `make_fullscreen_region()` — L542
Returns Region covering full video frame, or nil.

---

## IPC/Events

### `emit_event(event_name, ...)` — L64
Sends `mp.commandv("script-message", "webm-" .. event_name, ...)`.

### `test_set_options(new_options_json)` — L68
IPC handler. Parses JSON and merges into options (no validation).
