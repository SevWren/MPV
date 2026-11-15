# 18 — Glossary

**Source hash**: sha256:3f454dc0ca030b591d659f7405a3ddfdf7585e5b5eb4cd5b3a573b4151b33214
**Generation date**: 2026-11-15

---

| Term | Definition |
|------|-----------|
| acceptsBitrate | Format field; if true, calculate_bitrate() is applied to the encode command |
| additional_flags | User-configurable extra mpv flags appended to encode command |
| ASS | Advanced SubStation Alpha — subtitle/overlay format used by mpv for OSD |
| assdraw | mpv Lua module for drawing ASS shapes and text |
| CRF | Constant Rate Factor — quality-based encoding parameter (lower = better quality, larger file) |
| firstpass stats | Binary log file written during VP8 2-pass encoding, containing per-frame statistics |
| Format | Base class for output format strategies |
| formats | Global table mapping format ID strings to Format instances |
| GIF | Animated GIF output format; uses palettegen/paletteuse for color optimization |
| HLS | HTTP Live Streaming — adaptive streaming format handled via cache dump |
| IPC | Inter-Process Communication — mpv's script-message mechanism |
| is_windows | Boolean detecting Windows platform via package.config |
| keybind | Configurable key name to open the main UI (default: W) |
| lavfi | libavfilter — ffmpeg's video/audio filter framework |
| LuaJIT | Just-In-Time compiled Lua, used by mpv for scripting |
| MainPage | Top-level UI page; singleton created at bootstrap |
| MoonScript | Lua dialect compiled to Lua; webm.lua was generated from MoonScript |
| moonc | MoonScript compiler |
| mp | mpv Lua core API module |
| mp.assdraw | mpv OSD drawing module |
| mp.msg | mpv message/logging module |
| mp.options | mpv script-opts reading module |
| mp.utils | mpv utility functions (subprocess, JSON, path, etc.) |
| mpv | Media player for video/audio |
| OSD | On-Screen Display — mpv's overlay system |
| output_template | Filename template with substitution tokens (%F, %s, %e, etc.) |
| Page | Base class for all OSD UI pages |
| panscan | mpv property controlling video panning |
| postCommandModifier | Format method that transforms the final encode command |
| Region | Data class representing a crop rectangle in video pixel coordinates |
| run_detached | Option; if true, encoding subprocess is non-blocking |
| script-opts | mpv configuration system for Lua script options |
| setmetatable | Lua function to set a table's metatable (used for OOP) |
| shell_escape | Function that quotes argv tokens for shell execution |
| strict_filesize_constraint | Option; if true, adds minrate/maxrate bitrate limits |
| supportsTwopass | Format field; if true, 2-pass encoding is available |
| target_filesize | Desired output file size in kilobytes (default: 10000 KB = ~10 MB) |
| test_set_options | IPC handler for mpv-webm-set-options script message |
| twopass | Option; enables 2-pass encoding for supported formats |
| VideoPoint | Data class representing a point in video pixel coordinates |
| VP8 | Video codec (libvpx); first VP8 format; supports 2-pass |
| VP9 | Video codec (libvpx-vp9); no 2-pass support |
| vp8_patch_logfile | Function that normalizes VP8 firstpass logfile frame durations |
| _accum_0 | MoonScript list comprehension accumulator variable (transpiler artifact) |
| _base_0 | MoonScript class base table variable (transpiler artifact) |
| _class_0 | MoonScript class variable (transpiler artifact) |
| _parent_0 | MoonScript parent class reference (transpiler artifact) |
