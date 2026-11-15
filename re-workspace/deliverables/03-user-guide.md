# 03 — User Guide

**Purpose**: How to use webm.lua to encode video clips.
**Audience**: End users.
**Source hash**: sha256:3f454dc0ca030b591d659f7405a3ddfdf7585e5b5eb4cd5b3a573b4151b33214
**Generation date**: 2026-11-15

---

## Installation

Place `webm.lua` in your mpv scripts directory:
- Linux/macOS: `~/.config/mpv/scripts/webm.lua`
- Windows: `%APPDATA%\mpv\scripts\webm.lua`

## Basic Workflow

1. Open a video in mpv.
2. Press **W** to open the WebM Maker overlay.
3. Use **1** to set the start time (uses current playback position).
4. Use **2** to set the end time (uses current playback position).
5. Press **e** to encode.

The output file is saved in the same directory as the source video by default.

## Key Bindings (Main Menu)

| Key | Action |
|-----|--------|
| W | Open/close the main menu |
| 1 | Set start time to current position |
| 2 | Set end time to current position |
| c | Open crop selection |
| o | Open encoding options |
| p | Preview the selection with crop applied |
| e | Start encoding |
| ESC | Close the main menu |

## Crop Selection

Press **c** to enter crop mode:

| Key | Action |
|-----|--------|
| 1 | Set point A to current mouse position |
| 2 | Set point B to current mouse position |
| r | Reset to full frame |
| ENTER | Confirm crop |
| ESC | Cancel crop |

The crop region is shown as a dark overlay. The selected area remains bright.

## Encoding Options

Press **o** to open the options menu:

| Key | Action |
|-----|--------|
| UP / DOWN | Navigate options |
| LEFT / RIGHT | Change option value |
| ENTER | Apply and close |
| ESC | Cancel (no changes) |

Available options in the UI: Output Format, Two Pass, Apply Current Video Filters, Scale Height, Strict Filesize Constraint, Write Filename on Metadata, Target Filesize, CRF, FPS, GIF Dither Type, Force Square Pixels.

## Output Formats

| Format | Description |
|--------|-------------|
| webm-vp8 | WebM with VP8 video and Vorbis audio |
| webm-vp9 | WebM with VP9 video and Opus audio |
| mp4 | MP4 with H.264 video and AAC audio |
| mp4-nvenc | MP4 with NVIDIA GPU H.264 encoding |
| mp3 | Audio-only MP3 |
| gif | Animated GIF with palette optimization |
| raw | Unknown/broken — do not use |

## Preview

Press **p** to preview the selection with crop applied. mpv will loop the selection. Press **ESC** to exit preview and return to the main menu.

## Configuration via script-opts

Add to `~/.config/mpv/script-opts/webm.conf`:

```ini
keybind=W
output_directory=
target_filesize=10000
output_format=mp4
display_progress=auto
```

See document 04-configuration-reference.md for all options.

## Warnings

- The "raw" format option in the UI will crash the script. Do not select it.
- Enabling strict_filesize_constraint may crash the script due to a bug. Use non-strict mode.
- Output filenames with extensions are always shell-quoted; this is correct behavior.
