# 07 — Algorithms Reference

**Source hash**: sha256:3f454dc0ca030b591d659f7405a3ddfdf7585e5b5eb4cd5b3a573b4151b33214
**Generation date**: 2026-11-15

See `re-workspace/guilds/algorithms/algorithms.md` for the complete algorithms reference. Key algorithms:

1. **Coordinate Transform** (L470-485): Screen ↔ video pixel conversion with clamping.
2. **Panscan/Zoom Geometry** (L341-425): Computes video display rectangle accounting for zoom, alignment, panscan.
3. **Time Formatting** (L93-106): `HH:MM:SS.mmm` or `MM:SS.mmm` format.
4. **Bitrate Calculation** (L1657-1671): `target_filesize × 8 / duration` with optional audio reservation.
5. **Shell Escaping** (L283-301): Single-quote POSIX / double-quote Windows per-token escaping.
6. **Property Template Expansion** (L123-173): `${prop}`, `${?prop:fallback}`, etc.
7. **Output Filename Generation** (L175-239): Two-stage substitution with time and mpv properties.
8. **IEEE-754 Double Encode/Decode** (L563-617): Manual big-endian IEEE-754 for VP8 logfile patching.
9. **GIF Palette Pipeline** (L1120-1210): palettegen+paletteuse lavfi filtergraph.
10. **VP8 Firstpass Log Patching** (L736-749): Normalizes frame durations after first pass.
11. **ASS Crop Box Drawing** (L1933-1950): Four-rectangle letterbox vignette effect.

## Shell Escape Safe Character Set

The safe characters in shell_escape are: `A-Za-z0-9`, `_`, `/`, `:`, `=`, `-`.

**Notable exclusions**: `.` (dot), `~`, `+`, `,`, `@`, space.

This means ALL file paths with extensions (e.g., `/tmp/video.mp4`) are quoted, which is correct behavior.

## Bitrate Calculation Example

```
target_filesize = 10000 KB, duration = 30 seconds, non-strict, has video:
  total_kilobits = 10000 × 8 = 80000 kb
  video_bitrate = floor(80000 / 30) = 2666 kbps

target_filesize = 10000 KB, duration = 30 seconds, strict, has audio:
  audio_kilobits = 30 × 128 = 3840 kb
  video_kilobits = 80000 - 3840 = 76160 kb
  video_bitrate = floor(76160 / 30) = 2538 kbps
  audio_bitrate = 128 kbps
```
