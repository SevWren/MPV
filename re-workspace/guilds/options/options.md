# Options Guild Report

## Complete Options Reference

All options are defined in the `options` table (L6-31), overridable via mpv script-opts.

| Option | Default | Type | Description |
|--------|---------|------|-------------|
| keybind | "W" | string | Key to open the WebM encoder UI |
| output_directory | "" (empty) | string | Output directory; empty = same as source |
| run_detached | true | boolean | Run ffmpeg as detached subprocess |
| output_template | "%F-[%s-%e]%M" | string | Output filename template |
| scale_height | -1 | number | Output height in pixels (-1 = source height) |
| fps | -1 | number | Output frame rate (-1 = source FPS) |
| target_filesize | 10000 | number | Target file size in kilobytes |
| strict_filesize_constraint | false | boolean | Enforce strict bitrate limits |
| strict_bitrate_multiplier | 0.95 | number | Multiplier for strict bitrate (unused in code?) |
| strict_audio_bitrate | 128 | number | Audio bitrate reserved in strict mode (kbps) |
| output_format | "mp4 (h264/AAC)" | string | Default output format ID |
| twopass | false | boolean | Enable 2-pass encoding |
| apply_current_filters | false | boolean | Apply current mpv video filters to output |
| write_filename_on_metadata | false | boolean | Write source filename to output metadata |
| libvpx_threads | 4 | number | Thread count for VP9 encoding |
| additional_flags | "" | string | Extra mpv flags (whitespace-separated) |
| crf | -1 | number | CRF value (-1 = disabled) |
| non_strict_additional_flags | "cq-level=28" | string | Flags added in non-strict mode |
| display_progress | "true" | string | Progress display: "true", "false", "auto" |
| font_size | 28 | number | OSD font size |
| margin | 10 | number | OSD margin in pixels |
| message_duration | 5 | number | OSD message display duration in seconds |
| gif_dither | 0 | number | GIF dither algorithm (0-6) |
| force_square_pixels | false | boolean | Force 1:1 pixel aspect ratio |

## Notes on Individual Options

### output_format
Default `"mp4 (h264/AAC)"` does NOT match any formats table key. The correct keys are: `webm-vp8`, `webm-vp9`, `mp4`, `mp4-nvenc`, `mp3`, `gif`. On first use without UI interaction, `formats[options.output_format]` returns nil and encode() crashes. This is resolved once the user opens EncodeOptionsPage and confirms.

### display_progress
Stored as a string, not a boolean. Valid values: `"true"`, `"false"`, `"auto"`. `"auto"` disables progress on Windows. `should_display_progress()` function handles the conversion. Setting to `true` (boolean) via script-opts would be coerced to string "true" by mpv.

### strict_bitrate_multiplier
Declared in options table (L15) but never referenced in the code. Appears to be vestigial.

### additional_flags
Tokenized by whitespace (`gmatch("[^%s]+")`). Values with embedded spaces cannot be passed as single tokens. This affects any ffmpeg option whose value contains a space.

### output_directory
Empty string `[[]]` (Lua long string syntax) is falsy in the sense that the check `if options.output_directory ~= "" then` at L1810 uses it as an override trigger. Empty = use source directory.

### non_strict_additional_flags
Default `"cq-level=28"` applies a VP8/VP9 quality constraint in non-strict mode. This is a VP8-specific option; for other codecs, it may be silently ignored or cause an error.

## IPC Override (mpv-webm-set-options)

Any option can be overridden via script-message:
```
mpv --script-opts=... --script-message-to=webm mpv-webm-set-options '{"option_name": value}'
```
OR at runtime:
```lua
mp.commandv("script-message-to", "webm", "mpv-webm-set-options", json_string)
```
No validation, type checking, or key whitelisting. Setting non-option keys inserts them into the global options table.

## UI-Settable Options

EncodeOptionsPage exposes 11 options:
output_format, twopass, apply_current_filters, scale_height, strict_filesize_constraint, write_filename_on_metadata, target_filesize, crf, fps, gif_dither, force_square_pixels.

Options NOT accessible via UI: keybind, output_directory, run_detached, output_template, strict_bitrate_multiplier, strict_audio_bitrate, libvpx_threads, additional_flags, non_strict_additional_flags, display_progress, font_size, margin, message_duration.
