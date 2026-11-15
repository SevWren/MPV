# SEG-06 Reconciled Analysis
**Lines**: L932-1113
**Description**: WebmVP9, MP4 (h264/AAC), MP4NVENC (h264-NVENC/AAC), MP3 format classes

## Purpose
Defines four additional Format subclasses: WebmVP9 (VP9 codec), MP4 (H.264/AAC via libx264), MP4NVENC (NVIDIA GPU-accelerated H.264 via h264_nvenc), and MP3 (audio-only). Each overrides __init to set codec/format metadata, with minimal behavioral overrides.

## Line Walkthrough
- **L932**: `formats["webm-vp8"] = WebmVP8()` — WebmVP8 instance registered.
- **L933-981**: `WebmVP9` — videoCodec="libvpx-vp9", audioCodec="libopus", supportsTwopass=false. Overrides `getFlags` to add `--ovcopts-add=threads=N`.
- **L982**: `formats["webm-vp9"] = WebmVP9()` registered.
- **L983-1025**: `MP4` — videoCodec="libx264", audioCodec="aac", supportsTwopass=true. No method overrides.
- **L1026**: `formats["mp4"] = MP4()` registered.
- **L1027-1069**: `MP4NVENC` — videoCodec="h264_nvenc", audioCodec="aac", supportsTwopass=true. No method overrides.
- **L1070**: `formats["mp4-nvenc"] = MP4NVENC()` registered.
- **L1071-1113**: `MP3` — videoCodec="", audioCodec="libmp3lame", supportsTwopass=false, outputExtension="mp3". Audio-only: empty videoCodec means getCodecFlags omits --ovc.
- **L1114**: `formats["mp3"] = MP3()` registered.

## Registered Formats Summary

| ID | Display Name | Video | Audio | Ext | 2-pass | Bitrate |
|----|-------------|-------|-------|-----|--------|---------|
| webm-vp8 | WebM | libvpx | libvorbis | webm | yes | yes |
| webm-vp9 | WebM (VP9) | libvpx-vp9 | libopus | webm | no | yes |
| mp4 | MP4 (h264/AAC) | libx264 | aac | mp4 | yes | yes |
| mp4-nvenc | MP4 (h264-NVENC/AAC) | h264_nvenc | aac | mp4 | yes | yes |
| mp3 | MP3 (libmp3lame) | (none) | libmp3lame | mp3 | no | yes |
| gif | GIF | (see SEG-07) | (none) | gif | no | no |

## Edge Cases
- WebmVP9 `supportsTwopass=false` — VP9 2-pass via libvpx-vp9 not implemented.
- MP3 with `videoCodec=""` — `getCodecFlags` returns only `--oac=libmp3lame`.
- MP4NVENC requires NVIDIA GPU; ffmpeg will fail at runtime if unavailable.
- `options.output_format` default is `"mp4 (h264/AAC)"` — but the registry key is `"mp4"`. The UI must map display names to keys.

## Note on options.output_format
The default value "mp4 (h264/AAC)" does NOT match any registry key ("mp4", "webm-vp8", etc.). The EncodeOptionsPage uses a `list` type Option where values are the registry keys. The default "mp4 (h264/AAC)" appears to be a stale display name that may cause `formats[options.output_format]` to return nil on first run if not properly initialized through the UI.
