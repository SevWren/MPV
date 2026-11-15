# 10 — Data Flow and Dependencies

**Source hash**: sha256:3f454dc0ca030b591d659f7405a3ddfdf7585e5b5eb4cd5b3a573b4151b33214
**Generation date**: 2026-11-15

## Data Flow: User Action → Encoded File

```
User presses 'e'
  → MainPage.startTime, endTime (from time-pos property)
  → MainPage.region (from CropPage interaction, may be nil)
  → encode(region, startTime, endTime)
    → options.output_format → formats[key] → Format instance
    → find_path() → path (filesystem), times (adjusted for HLS)
    → get_active_tracks() → track list from mpv
    → command[] built from:
        path + times
        format.getCodecFlags()
        track selection
        get_video_encode_flags() ← region, options, mpv properties
        format.getFlags()
        bitrate calculation ← options.target_filesize, duration
        additional_flags (from options)
        output_path ← options.output_directory, output_template, mpv properties
    → format.postCommandModifier(command)
    → subprocess execution
    → output file on disk
```

## Dependency Graph (simplified)

```
encode()
  ├── formats (global registry)
  ├── find_path() → mp.get_property('path')
  ├── get_active_tracks() → mp.get_property_native('track-list')
  ├── get_video_encode_flags()
  │     ├── get_playback_options() → mp.get_property × 8
  │     ├── get_video_filters()
  │     │     ├── format.getPreFilters()
  │     │     ├── apply_current_filters() → mp.get_property_native('vf')
  │     │     ├── Region.is_valid() → lavfi-crop filter
  │     │     ├── get_scale_filters() → options.scale_height
  │     │     ├── get_fps_filters() → options.fps
  │     │     └── get_contrast_brightness_saturation() → mp.get_property × 3
  │     └── get_speed_flags() → mp.get_property_native('speed')
  ├── calculate_bitrate() → options.target_filesize, options.strict_*
  ├── format_filename() → expand_properties() → mp.get_property_osd × N
  └── format.postCommandModifier() → (GIF: rebuilds filter chain)
```

## External Dependencies

| Dependency | Used For |
|-----------|---------|
| mp (mpv Lua API) | All mpv integration |
| mp.assdraw | OSD rendering |
| mp.msg | Logging |
| mp.utils | Subprocess, JSON, path utils |
| mp.options | Script-opts reading |
| io (Lua stdlib) | File I/O, popen |
| os (Lua stdlib) | File removal |
| math (Lua stdlib) | ldexp, frexp, floor |
| string (Lua stdlib) | Pattern matching, format |
| table (Lua stdlib) | concat |
