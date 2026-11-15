# HANDOFF.md

## Reverse Engineering Package: scripts/webm.lua

**Completed**: 2026-11-15
**Source hash**: sha256:3f454dc0ca030b591d659f7405a3ddfdf7585e5b5eb4cd5b3a573b4151b33214

## What Was Analyzed

`scripts/webm.lua` — An mpv Lua script providing an interactive video clip encoder. The script was compiled from MoonScript source (original source not present in repo).

## Critical Findings for Immediate Action

### 1. EncodeOptionsPage crashes on instantiation (HIGH)
**File**: scripts/webm.lua, L2368
**Issue**: `"raw"` in formatIds but `formats["raw"]` is nil → crash when user presses 'o'.
**Fix**: Remove `"raw"` from formatIds array.

### 2. encode() crashes in strict filesize mode (HIGH)
**File**: scripts/webm.lua, L1779-1780
**Issue**: `bitrate` variable undefined; should be `video_bitrate`.
**Fix**: Replace `bitrate` with `video_bitrate` at L1779-1780.

### 3. Default output_format crashes encode() on first use (MEDIUM)
**File**: scripts/webm.lua, L17
**Issue**: Default `"mp4 (h264/AAC)"` doesn't match any formats key.
**Fix**: Change default to `"mp4"`.

### 4. IPC handler has no validation (SECURITY/HIGH)
**File**: scripts/webm.lua, L68-74
**Issue**: `mpv-webm-set-options` message merges any JSON keys into options without validation.
**Risk**: Moderate for standalone use; high in multi-script environments.
**Fix**: Add key whitelist validation.

## What Works

- Core encoding workflow (non-strict, non-detached, with valid format)
- All UI pages (except EncodeOptionsPage, which crashes — FIND-002)
- Crop selection, preview, start/end time selection
- WebM VP8/VP9, MP4 H.264/NVENC, MP3, GIF formats (after FIND-003 fix)
- Cross-platform Windows/POSIX support
- HLS stream support

## What Doesn't Work

- EncodeOptionsPage (crashes on 'o' key — FIND-002)
- Strict filesize constraint (crashes — FIND-001)
- "raw" format (doesn't exist — FIND-002/FIND-003)

## Package Contents

See INDEX.md for full listing of 24 deliverable documents and supporting artifacts.
