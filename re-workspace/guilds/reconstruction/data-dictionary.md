# Data Dictionary

## Global Variables

| Name | Type | Defined At | Description |
|------|------|-----------|-------------|
| options | table | L6 | All 24 user-configurable settings |
| base64_chars | string | L34 | Base64 alphabet string |
| base64_encode | function | L36 | Global base64 encoder |
| base64_decode | function | L49 | Global base64 decoder |
| _video_dimensions | table | L339 | Cached OSD-to-video geometry |
| dimensions_changed | bool | L338 | Cache invalidation flag |
| formats | table | L745 | Format registry {id → Format instance} |
| is_windows | bool | L259 | Platform detection flag |
| mainPage | MainPage | L2839 | Singleton main UI page |

## Options Fields

| Field | Type | Default | Range/Values |
|-------|------|---------|-------------|
| keybind | string | "W" | Any mpv key name |
| output_directory | string | "" | Path or empty |
| run_detached | bool | true | true/false |
| output_template | string | "%F-[%s-%e]%M" | Template string |
| scale_height | number | -1 | -1 or pixel height |
| fps | number | -1 | -1 or frame rate |
| target_filesize | number | 10000 | KB, 0 for constant quality |
| strict_filesize_constraint | bool | false | |
| strict_bitrate_multiplier | number | 0.95 | UNUSED |
| strict_audio_bitrate | number | 128 | kbps |
| output_format | string | "mp4 (h264/AAC)" | Format registry key |
| twopass | bool | false | |
| apply_current_filters | bool | false | |
| write_filename_on_metadata | bool | false | |
| libvpx_threads | number | 4 | Thread count |
| additional_flags | string | "" | Space-separated mpv flags |
| crf | number | -1 | -1=disabled, else CRF value |
| non_strict_additional_flags | string | "cq-level=28" | Space-separated flags |
| display_progress | string | "true" | "true"/"false"/"auto" |
| font_size | number | 28 | OSD font size |
| margin | number | 10 | OSD margin pixels |
| message_duration | number | 5 | OSD message seconds |
| gif_dither | number | 0 | 0-6 dither algorithm |
| force_square_pixels | bool | false | |

## Format Class Fields

| Field | Type | Description |
|-------|------|-------------|
| displayName | string | Human-readable name |
| videoCodec | string | ffmpeg video codec name (empty = no video) |
| audioCodec | string | ffmpeg audio codec name (empty = no audio) |
| outputExtension | string | File extension without dot |
| supportsTwopass | bool | Whether 2-pass encoding is supported |
| acceptsBitrate | bool | Whether bitrate calculation should be applied |

## VideoPoint Fields

| Field | Type | Sentinel | Description |
|-------|------|----------|-------------|
| x | int | -1 | Horizontal video pixel coordinate |
| y | int | -1 | Vertical video pixel coordinate |

## Region Fields

| Field | Type | Sentinel | Description |
|-------|------|----------|-------------|
| x | int | -1 | Left edge in video pixels |
| y | int | -1 | Top edge in video pixels |
| w | int | -1 | Width in video pixels |
| h | int | -1 | Height in video pixels |

## _video_dimensions Fields

| Field | Type | Description |
|-------|------|-------------|
| top_left | {x,y} | Top-left corner of video in OSD coordinates |
| bottom_right | {x,y} | Bottom-right corner of video in OSD coordinates |
| ratios | {w,h} | video_pixels / display_pixels ratio |

## FirstpassStats Fields

| Field | Type | Description |
|-------|------|-------------|
| binary_data_before_duration | byte[] | 16×8=128 bytes before duration field |
| binary_duration | byte[] | 8 bytes, little-endian IEEE-754 double |
| binary_data_after_duration | byte[] | 1×8=8 bytes after duration field |

Class constants:
- `duration_multiplier = 1e7` (VP8 timestamps in 100-nanosecond units)
- `fields_before_duration = 16`
- `fields_after_duration = 1`
- Record size = 144 bytes

## Option Widget Fields

| Field | Type | Description |
|-------|------|-------------|
| optType | string | "bool", "int", or "list" |
| displayText | string | Label shown in UI |
| value | any | Current value (bool: bool, int: number, list: 1-based index) |
| opts | table | Type-specific options (see Options Guild) |
| visibleCheckFn | fn or nil | Returns true if option should be shown |
