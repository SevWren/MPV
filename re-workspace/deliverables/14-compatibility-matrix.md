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

---

## § Developer Environment (Active 2026-11-15)

This section documents the specific environment in which the script is under active development and debugging as of 2026-11-15. See `14b-windows-developer-environment.md` for full analysis.

| Property | Value |
|----------|-------|
| mpv build | `mpv-x86_64-20261114-git-649001d4e2` |
| Build date | 2026-11-14 at 12:51 |
| Compiler | clang (zhongfly/mpv-winbuild via GitHub Actions run 43592714705) |
| Git commit | `mpv-player/mpv@649001d` |
| OS | Windows 10 |
| Lua runtime | LuaJIT 2.1 (bundled; zhongfly builds include LuaJIT by default) |
| Install prefix | `--prefix=/mingw64` |

### Expected script behavior on this build

All three highest-severity confirmed defects are immediately reproducible on this build without any special configuration:

| Finding | Trigger | Windows Behavior |
|---------|---------|-----------------|
| FIND-002 (HIGH) | Press `o` to open EncodeOptionsPage | Lua error: `formats["raw"]` is nil; options UI crashes immediately |
| FIND-001 (HIGH) | Set `strict_filesize_constraint=yes` and encode | Lua error: `bitrate` is nil (undefined variable) |
| FIND-003 (MEDIUM) | Encode without opening options page first | `formats[options.output_format]` may be nil; crash on encode |

### subprocess_detached

The script calls `mp.utils.subprocess_detached` at L1858 (not `mp.utils.subprocess` with `detach=true`). The `subprocess_detached` API has been available since mpv 0.29.0 and is present in this build (mpv@649001d, 2026-11-14). No compatibility issue.

### Shell execution on Windows

`io.popen` calls go through `cmd.exe /c` on Windows (via MSVCRT `_popen`). The `shell_escape` function at L282-301 applies Windows-specific quoting (double-quote wrapping per argument and outer double-quote wrap of the whole command string) when `is_windows == true`. This is correct for typical media file paths. Filenames containing Windows shell metacharacters (`%`, `^`, `&`, `|`, `<`, `>`) are not fully escaped.

Progress display defaults to disabled on Windows (`should_display_progress()` returns false when `display_progress="auto"` and `is_windows=true`), so the `io.popen`/`shell_escape` path is **not exercised** in the default Windows configuration. It is only triggered if the user explicitly sets `display_progress=yes`.

### `/dev/null` handling

Handled correctly. `get_null_path()` at L264-270 checks `file_exists("/dev/null")` first; on Windows this returns false, so the function returns `"NUL"`. No bug.

### Home directory resolution

`parse_directory("~")` at L239-258 resolves `HOME` → `USERPROFILE` → `HOMEDRIVE`+`HOMEPATH` in order. On standard Windows 10 without a POSIX environment, `HOME` is typically unset and the function correctly falls through to `USERPROFILE` (e.g., `C:\Users\<username>`).

### LuaJIT 2.1 compatibility

LuaJIT 2.1 as bundled in this build retains full Lua 5.1 API compatibility. All features used by webm.lua (`math.ldexp`, `math.frexp`, global `unpack`, `string.format`, `io.popen`, `setmetatable`, `pcall`) are present and behave identically to standard Lua 5.1. The `_class_0`/`_base_0`/`_parent_0` MoonScript scaffolding runs without modification.
