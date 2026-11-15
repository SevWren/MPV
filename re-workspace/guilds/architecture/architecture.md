# Architecture Guild Report

## Overview

`webm.lua` is a MoonScript-compiled mpv Lua script that provides an interactive video clip encoder with real-time OSD UI. It enables users to select time ranges and crop regions within mpv and encode clips to multiple output formats via mpv's subprocess mechanism.

## Layers

```
Layer 0: Bootstrap (L2838-2855)
  monitor_dimensions(), MainPage(), key binding, event registration

Layer 1: OSD UI (Pages)
  MainPage → CropPage | EncodeOptionsPage | PreviewPage
  Base: Page class (key bindings, OSD lifecycle)

Layer 2: Encode Orchestration
  encode() [L1697-1885] → find_path, command builders, format dispatch

Layer 3: Command Builders
  get_active_tracks, filter_tracks, append_track, get_video_encode_flags
  get_video_filters, get_playback_options, calculate_bitrate

Layer 4: Format Registry
  Format base + 7 concrete formats (webm-vp8, webm-vp9, mp4, mp4-nvenc, mp3, gif, raw)

Layer 5: Data Models
  VideoPoint, Region, FirstpassStats, Option widget

Layer 6: Utilities
  time formatting, shell_escape, run_subprocess*, file_exists
  expand_properties, format_filename, base64, emit_event

Layer 7: Geometry
  get_video_dimensions, VideoPoint↔screen transforms, clamp
```

## Class Hierarchy

```
Page (L1217)
  ├── CropPage (L1886)
  ├── EncodeOptionsPage (L2211)
  ├── PreviewPage (L2539)
  └── MainPage (L2639)

Format (L746)
  ├── WebmVP8 (L807)
  ├── WebmVP9 (L933)
  ├── MP4 (L983)
  ├── MP4NVENC (L1027)
  ├── MP3 (L1071)
  └── GIF (L1115)

Standalone:
  VideoPoint (L466)
  Region (L506)
  FirstpassStats (L618)
  Option (L2047)
  EncodeWithProgress (L1329)
```

## Boot Sequence

1. Module loads: requires (L1-5)
2. options table declared (L6-31)
3. mpopts.read_options(options) (L33) — script-opts override
4. base64_chars, base64_encode, base64_decode (L34-62)
5. emit_event, test_set_options registered (L63-74)
6. Utility functions defined (L75-337)
7. Geometry functions defined (L338-465)
8. Data classes defined (L466-744)
9. Format registry populated (L745-1216)
10. UI classes defined (L1217-2856)
11. Bootstrap executed (L2838-2855):
    - monitor_dimensions() — 11 property observers
    - mainPage = MainPage()
    - mp.add_key_binding for 'W' key
    - mp.register_event "file-loaded"

## Coupling Analysis

- **High coupling**: encode() references all command builders + all format classes + EncodeWithProgress.
- **Moderate coupling**: MainPage creates CropPage, EncodeOptionsPage, PreviewPage; passes callbacks.
- **Low coupling**: Format classes have no direct dependency on UI.
- **Global state**: `options` table accessed from virtually every module function.
- **Shared mutable state**: `_video_dimensions`, `dimensions_changed` module-level vars.

## Module/Class Map (by function)

| Function/Class | Segment | Layer |
|---------------|---------|-------|
| options | SEG-00 | 0 |
| base64_encode/decode | SEG-00 | 6 |
| emit_event | SEG-00 | 6 |
| test_set_options | SEG-00 | 0 (IPC) |
| bold, message, append | SEG-01 | 6 |
| seconds_to_time_string | SEG-01 | 6 |
| expand_properties, format_filename | SEG-01 | 6 |
| run_subprocess, run_subprocess_popen | SEG-01 | 6 |
| shell_escape | SEG-01 | 6 |
| get_video_dimensions | SEG-02 | 7 |
| monitor_dimensions | SEG-02 | 0 |
| VideoPoint, Region | SEG-03 | 5 |
| make_fullscreen_region | SEG-03 | 5 |
| read_double, write_double | SEG-04 | 6 |
| FirstpassStats, vp8_patch_logfile | SEG-04 | 5/6 |
| Format, WebmVP8 | SEG-05 | 4 |
| WebmVP9..MP3 | SEG-06 | 4 |
| GIF | SEG-07 | 4 |
| Page, EncodeWithProgress | SEG-08 | 1/2 |
| get_active_tracks..calculate_bitrate | SEG-09 | 3 |
| find_path, encode | SEG-10 | 2 |
| CropPage | SEG-11 | 1 |
| Option | SEG-12 | 1 |
| EncodeOptionsPage | SEG-13 | 1 |
| PreviewPage | SEG-14 | 1 |
| MainPage, bootstrap | SEG-15 | 0/1 |
