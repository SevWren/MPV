# 05 — API Reference: Format Class Hierarchy

**Source hash**: sha256:3f454dc0ca030b591d659f7405a3ddfdf7585e5b5eb4cd5b3a573b4151b33214
**Generation date**: 2026-11-15

---

## Format (Base Class) — L746-806

### Fields

| Field | Type | Description |
|-------|------|-------------|
| displayName | string | Human-readable display name |
| videoCodec | string | ffmpeg video codec (empty = no video) |
| audioCodec | string | ffmpeg audio codec (empty = no audio) |
| outputExtension | string | File extension without dot |
| supportsTwopass | bool | Whether 2-pass encoding is supported |
| acceptsBitrate | bool | Whether bitrate calculation should be applied |

### Methods

#### `getPreFilters(self)` → `{}`
Returns video filters to prepend. Base returns empty list.

#### `getPostFilters(self)` → `{}`
Returns video filters to append. Base returns empty list.

#### `getFlags(self)` → `{}`
Returns format-specific mpv flags. Base returns empty list.

#### `getCodecFlags(self)` → `{string, ...}` — L759-768
Returns `{--ovc=CODEC}` and/or `{--oac=CODEC}` for non-empty codecs.

#### `postCommandModifier(self, command, region, startTime, endTime)` → `command`
Post-processes the full command array. Base returns command unchanged.

---

## WebmVP8 — L807-931

Extends Format.
- `displayName = "WebM"`, `videoCodec = "libvpx"`, `audioCodec = "libvorbis"`
- `supportsTwopass = true`, `outputExtension = "webm"`, `acceptsBitrate = true`

### Additional Methods

#### `getColorspace(self)` → `string`
Returns `"bt709"` colorspace filter string.

#### `getPostFilters(self)` → `{string}`
Returns `{getColorspace()}`.

#### `postCommandModifier(self, command, region, startTime, endTime)` → command
For 2-pass: appends `--ovcopts-add=flags=+passN`, patches VP8 logfile on pass1.

---

## WebmVP9 — L933-981

Extends Format.
- `displayName = "WebM (VP9)"`, `videoCodec = "libvpx-vp9"`, `audioCodec = "libopus"`
- `supportsTwopass = false`, `outputExtension = "webm"`, `acceptsBitrate = true`

#### `getFlags(self)` → `{string}`
Returns `{"--ovcopts-add=threads=N"}` where N = `options.libvpx_threads`.

---

## MP4 — L983-1025

Extends Format. No method overrides.
- `displayName = "MP4 (h264/AAC)"`, `videoCodec = "libx264"`, `audioCodec = "aac"`
- `supportsTwopass = true`, `outputExtension = "mp4"`, `acceptsBitrate = true`

---

## MP4NVENC — L1027-1069

Extends Format. No method overrides.
- `displayName = "MP4 (h264-NVENC/AAC)"`, `videoCodec = "h264_nvenc"`, `audioCodec = "aac"`
- `supportsTwopass = true`, `outputExtension = "mp4"`, `acceptsBitrate = true`
- Requires NVIDIA GPU with NVENC support in ffmpeg.

---

## MP3 — L1071-1113

Extends Format. No method overrides.
- `displayName = "MP3 (libmp3lame)"`, `videoCodec = ""`, `audioCodec = "libmp3lame"`
- `supportsTwopass = false`, `outputExtension = "mp3"`, `acceptsBitrate = true`
- Audio-only: no `--ovc` flag generated.

---

## GIF — L1115-1215

Extends Format. Complex postCommandModifier.
- `displayName = "GIF"`, `videoCodec = "gif"`, `audioCodec = ""`
- `supportsTwopass = false`, `outputExtension = "gif"`, `acceptsBitrate = false`

#### `postCommandModifier(self, command, region, startTime, endTime)` → command
Rebuilds the entire video filter chain as a lavfi filtergraph with palettegen/paletteuse for GIF palette optimization. See 07-algorithms/gif-pipeline.md for details.
