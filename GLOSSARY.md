# Glossary

Domain-specific terms for the `webm.lua` mpv encoder script. Generic programming terms (function, table, loop, callback) are excluded.

---

## Encoding Concepts

**Encode**: The act of invoking mpv in encode mode (`--o=...`) to produce an output file from a clip. One encode corresponds to one `mp.utils.subprocess` or `io.popen` call.

**Encode Session**: The in-progress state of a single encode job: the constructed command argv, the temp file paths reserved, and the two-pass logfile handle (if applicable). Not a persistent data structure — it is assembled and consumed within a single encode() invocation.

**Clip**: The user-defined time span to be encoded, expressed as a start time and end time in seconds. Set interactively via MainPage. _Avoid_: "segment" (overloaded with source analysis segments), "selection"

**Two-pass encoding** (also: **2-pass**): A VBR encoding strategy that runs the encoder twice — first to gather statistics, then to produce the final file using those statistics for optimal bitrate allocation. Only available for formats where `supportsTwopass = true` (VP8, MP4, MP4-NVENC).

**First pass** / **Second pass**: The two stages of two-pass encoding. The first pass writes a binary statistics log; the second pass reads it and writes the output file.

**FirstpassStats**: The binary data produced by libvpx during the VP8 first pass. Stored in a temp `.log` file. Requires `vp8_patch_logfile` normalization before the second pass can consume it. _Avoid_: "logfile" (too generic)

**Target filesize**: The user-specified maximum output size in kilobytes (default: 10,000 KB ≈ 10 MB). When non-zero, the script calculates a video bitrate from this value. When zero, encoding uses constant-quality mode with no bitrate limit. _Avoid_: "filesize limit"

**Bitrate calculation**: The derivation of a video bitrate (kbps) from target filesize, clip duration, and reserved audio bitrate. Performed by `calculate_bitrate()`. Only applied for formats where `acceptsBitrate = true`.

**CRF** (Constant Rate Factor): A quality-based encoding parameter where lower values produce higher quality at larger file sizes. Applied when `target_filesize = 0` and `crf ≥ 0`. Not available for all formats.

**Strict filesize constraint**: An encoding mode that adds `minrate`/`maxrate` flags to enforce a hard file size ceiling. Enabled by `strict_filesize_constraint = true`. Currently triggers FIND-001 (undefined `bitrate` variable crash).

---

## Spatial / Geometry

**VideoPoint**: A 2D integer coordinate `(x, y)` in video pixel space, referencing a position on the decoded video frame. Used as the two corners of a Region. _Avoid_: "point", "coordinate"

**Region**: A rectangular crop area defined by two VideoPoints (top-left and bottom-right corners) in video pixel coordinates. When set, the script adds a `crop=W:H:X:Y` filter to the ffmpeg filter graph. _Avoid_: "crop rect", "selection box"

**Filter graph**: The ffmpeg `-vf` filter chain assembled by the script. May include crop, scale, fps, palette generation (GIF), and any filters from mpv's current `vf` chain if `apply_current_filters` is enabled. _Avoid_: "filter chain" (use filter graph)

---

## UI / OSD

**Page**: A full-screen OSD overlay that presents one mode of the encoder UI. All pages extend the `Page` base class. Active pages render themselves via ASS draw calls. _Avoid_: "screen", "panel", "view"

**MainPage**: The entry-point OSD page. Displays clip start/end times and launches child pages. Singleton; created once at bootstrap and never destroyed.

**CropPage**: The OSD page for interactively selecting a Region by clicking two VideoPoints on the video frame.

**EncodeOptionsPage**: The OSD page for reviewing and changing the 11 UI-settable options. Options are presented as a scrollable list of Option widgets.

**PreviewPage**: The OSD page that shows a brief looping preview of the encoded clip region before committing. Saves a snapshot of options state at construction time (not at show() time — see FIND-010).

**EncodeWithProgress**: An OSD overlay that displays encoding progress (elapsed/estimated time) during a foreground (non-detached) encode. Not navigable; it is dismissed automatically.

**Option** (UI widget): A configurable setting with an associated display widget in EncodeOptionsPage. Each Option has a name, a current value, and a value cycle or input handler. Options are a subset of the full 24 configuration options. _Avoid_: "setting" (overloaded with the broader `options` table)

**OSD** (On-Screen Display): mpv's overlay rendering layer. The script draws all UI via ASS text/shapes rendered onto the OSD. Not a GUI window — it is composited over the video.

**ASS**: Advanced SubStation Alpha. The subtitle/overlay markup format used to draw text and shapes on mpv's OSD. The script uses `mp.assdraw` to construct ASS draw calls.

**Keybind**: The single mpv key name (default: `W`) that opens MainPage. Configured via the `keybind` option. Registered once at bootstrap via `mp.add_key_binding`; IPC changes after boot have no effect.

---

## Format / Codec

**Format**: A named output container + codec combination registered in the global `formats` table. Each Format is a strategy object with fields like `acceptsBitrate`, `supportsTwopass`, and override methods `postCommandModifier` / `getFlags`. _Avoid_: "codec profile", "preset"

**WebmVP8**: Format identifier `webm-vp8`. Container: WebM, codec: libvpx (VP8). Supports two-pass and bitrate calculation. Requires firstpass stats normalization.

**WebmVP9**: Format identifier `webm-vp9`. Container: WebM, codec: libvpx-vp9 (VP9). No two-pass support. Uses `libvpx_threads` thread count.

**MP4**: Format identifier `mp4`. Container: MP4, codec: H.264 (libx264) + AAC. Supports two-pass.

**MP4NVENC**: Format identifier `mp4-nvenc`. Container: MP4, codec: H.264 via NVIDIA NVENC hardware encoder. Supports two-pass.

**GIF**: Format identifier `gif`. Container: GIF. Uses a two-step lavfi pipeline: `palettegen` on a first ffmpeg pass, `paletteuse` on a second. Dither algorithm controlled by `gif_dither`. Does not use the standard two-pass / bitrate path.

**MP3**: Format identifier `mp3`. Audio-only output.

**postCommandModifier**: A Format method that transforms the final encode command argv before execution. Used by GIF to splice the palette filter pipeline and by other formats to inject codec-specific flags.

**supportsTwopass**: A boolean field on a Format instance. If true, two-pass encoding is available for that format. _Avoid_: "two-pass capable"

**acceptsBitrate**: A boolean field on a Format instance. If true, `calculate_bitrate()` is called and the result is injected into the encode command. _Avoid_: "bitrate-aware"

---

## Configuration / IPC

**Script message** (`mpv-webm-set-options`): The IPC mechanism by which external Lua scripts or processes can overwrite the `options` table at runtime. Accepts a JSON blob via mpv's `script-message` event. No input validation (FIND-006).

**script-opts**: mpv's native configuration system for Lua scripts. Options are read from `script-opts/webm.conf` or `--script-opts=webm-KEY=VALUE` flags at startup. Only flat string/number values are supported.

**output_template**: A filename template string with substitution tokens (`%F`, `%s`, `%e`, `%T`, `%M`, etc.) used to generate the output filename. Evaluated at encode time.

**additional_flags**: A space-separated string of extra mpv flags appended to the encode command. Tokenized by whitespace, so values containing spaces cannot be represented (FIND-009).

**run_detached**: Boolean option. When true, the encoding subprocess is launched via `io.popen` (non-blocking background process). When false, it runs via `mp.utils.subprocess` with an optional progress overlay. Detached mode does not clean up temp files (FIND-007).

---

## Runtime / Internal

**shell_escape**: The function that quotes individual argv tokens for safe shell insertion. On Windows it wraps the full command in `cmd.exe /Q /C "..."`. Critical correctness requirement for the `io.popen` code path.

**_video_dimensions**: A module-level cache of the current video's display dimensions. Invalidated by any of 11 mpv property observers registered at bootstrap. Rebuilt on demand by `get_video_dimensions()`.

**MoonScript transpiler artifacts**: The `_class_0`, `_base_0`, `_parent_0`, `_accum_0`, `_with_0` local variables that appear throughout the file. These are generated by the MoonScript compiler's OOP and comprehension patterns. They are not hand-written idiom and should not be modified as if they were. _Avoid_: calling these "classes" or "helpers" without noting their generated origin.
