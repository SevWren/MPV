# SEG-09 Reconciled Analysis
**Lines**: L1420-1672
**Description**: Track selection, command builders, bitrate calculation

## Purpose
Provides the functions that build the ffmpeg/mpv command-line arguments for encoding: track selection, video filter chain construction, playback option propagation, speed adjustment, metadata writing, and bitrate calculation.

## Line Walkthrough
- **L1420-1438**: `get_active_tracks()` — returns `{video:[], audio:[], sub:[]}` of currently active/visible tracks.
- **L1440-1449**: `filter_tracks_supported_by_format(active_tracks, format)` — returns only tracks supported by format (audio/sub excluded if format has no audio/video codec).
- **L1451-1470**: `append_track(out, track)` — appends `--audio-file=PATH` or `--sub-file=PATH` for external tracks; `--vid/aid/sid=ID` for internal. External filename limited to 2048 chars.
- **L1472-1499**: `append_audio_tracks(out, tracks)` — handles multiple audio tracks. If >1 internal audio tracks, builds `--lavfi-complex=[aid1][aid2]...amix[ao]` for audio mixing.
- **L1501-1514**: `get_scale_filters()` — returns `lavfi-scale=iw*sar:ih` if `force_square_pixels`; `lavfi-scale=-2:HEIGHT` if `scale_height > 0`.
- **L1516-1523**: `get_fps_filters()` — returns `fps=N` if `options.fps > 0`.
- **L1525-1538**: `get_contrast_brightness_and_saturation_filters()` — reads mpv brightness/contrast/saturation; maps to ffmpeg `lavfi-eq` filter values.
- **L1540-1548**: `append_property(out, property_name, option_name)` — reads mpv property and appends as `--option_name=value`.
- **L1550-1561**: `append_list_options(out, property_name, option_prefix)` — reads list property and appends each element as `--option_prefix-append=value`.
- **L1563-1575**: `get_playback_options()` — collects sub-ass-override, sub-ass-vsfilter-aspect-compat, sub-auto, sub-pos, sub-delay, video-rotate, ytdl-format, deinterlace. NOTE: sub-ass-force-style is commented out (L1566).
- **L1577-1588**: `get_speed_flags()` — if speed ≠ 1, adds setpts, atempo, sub-speed filters.
- **L1590-1595**: `get_metadata_flags()` — builds `--oset-metadata=title=%N%FILENAME` with length-prefixed value.
- **L1597-1623**: `apply_current_filters(filters)` — reads current mpv vf chain, skips disabled filters, serializes enabled ones as `name:k=%len%v` format.
- **L1625-1641**: `get_video_filters(format, region)` — assembles: preFilters, current_filters (optional), crop (if valid region), scale, fps, eq, postFilters.
- **L1643-1655**: `get_video_encode_flags(format, region)` — combines playback_options, video_filters (as --vf-add), speed_flags.
- **L1657-1671**: `calculate_bitrate(active_tracks, format, length)` — computes video/audio bitrates from `target_filesize * 8 / length`. For strict constraint: reserves `strict_audio_bitrate * length` kilobits for audio.

## Key Algorithm — Bitrate Calculation
```
total_kilobits = target_filesize * 8  (kB * 8 = kb)
if strict AND has_audio:
  audio_kilobits = length * strict_audio_bitrate
  video_kilobits = total_kilobits - audio_kilobits
video_bitrate = floor(video_kilobits / length)   [kbps]
audio_bitrate = floor(audio_kilobits / length)   [kbps]
```

For audio-only (videoCodec == ""):
```
audio_bitrate = target_filesize * 8 / length
```

## Edge Cases
- `additional_flags` tokenized at L1790 by `gmatch("[^%s]+"`) — values with embedded spaces are split.
- `append_track` external filename limit 2048 chars — silently falls through to internal track if exceeded.
- `get_contrast_brightness_and_saturation_filters` reads mpv properties as strings but compares to 0 numerically (L1529) — Lua string-to-number coercion; will work for "0" but may fail for unexpected values.
- Multiple audio tracks: `amix` without `inputs=N` parameter may default to 2 inputs in some ffmpeg versions.
- If `target_filesize = 0` (default is 10000 so this is non-default), returns 0kbps bitrate.

## Security Notes
- `get_metadata_flags` embeds the filename in the command line using length-prefixed format `%N%value`. The length prefixing prevents option injection via special characters in the filename.
- `apply_current_filters` uses `%len%value` format for filter params — same length-prefix protection.
