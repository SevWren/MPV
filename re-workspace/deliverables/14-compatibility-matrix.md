# 14 — Compatibility Matrix

**Source hash**: sha256:3f454dc0ca030b591d659f7405a3ddfdf7585e5b5eb4cd5b3a573b4151b33214
**Generation date**: 2026-11-15

---

## Lua Version Compatibility

| Feature | Lua 5.1 | Lua 5.2 | Lua 5.3+ | LuaJIT |
|---------|---------|---------|---------|--------|
| math.ldexp | Yes | Yes | Deprecated (still works) | Yes |
| math.frexp | Yes | Yes | Deprecated (still works) | Yes |
| string.char(unpack(...)) | Yes | Yes | No (unpack moved to table.unpack) | Yes |
| io.popen | Yes | Yes | Yes | Yes |
| setmetatable | Yes | Yes | Yes | Yes |
| goto | No | Yes | Yes | Yes (extension) |

**Verdict**: Compatible with Lua 5.1 and LuaJIT. Compatible with 5.2. May fail in Lua 5.3+ due to `math.ldexp` removal and `unpack` rename (though `math.ldexp` is still present as deprecated in 5.3 and 5.4).

**Note**: mpv uses LuaJIT 2.x for Lua scripting, so Lua 5.3+ issues are not relevant in practice.

## mpv Version Requirements

| Feature | Required |
|---------|---------|
| mp.utils.subprocess | Required (all versions) |
| mp.utils.subprocess_detached | Required |
| mp.utils.parse_json | Required for IPC |
| mp.add_forced_key_binding | Required for UI |
| mp.set_osd_ass | Required for OSD |
| mp.assdraw | Required for OSD drawing |
| mp.options.read_options | Required for config |
| mp.command_native | Required for HLS/expand-path |
| assdraw.rect_cw | Required for crop box |

**Minimum mpv version**: Unknown (uses APIs available since mpv 0.9+).

## Platform Compatibility

| Platform | Status | Notes |
|----------|--------|-------|
| Linux | Supported | Full features |
| macOS | Supported | Full features |
| Windows | Partial | Progress display disabled in auto mode; io.popen uses cmd.exe |
| FreeBSD | Likely | Same as Linux |

## Encoder/Codec Dependencies

| Format | Required Codec in ffmpeg |
|--------|------------------------|
| webm-vp8 | libvpx |
| webm-vp9 | libvpx-vp9 |
| mp4 | libx264 |
| mp4-nvenc | h264_nvenc (requires NVIDIA GPU) |
| mp3 | libmp3lame |
| gif | Built-in GIF support, palettegen/paletteuse lavfi filters |

**Note**: mpv uses its own bundled ffmpeg for `--ovc`/`--oac` encoding. The codecs must be compiled into mpv's bundled ffmpeg, not the system ffmpeg.
