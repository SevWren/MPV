# Error Handling Guild Report

## Overview

The script has inconsistent error handling. Some failures produce user-visible messages; others silently return nil or false; a few have bugs that would cause runtime crashes.

## Silent Failures (No User Notification)

| Location | Condition | Result |
|----------|-----------|--------|
| get_video_dimensions() L346-348 | video-out-params is nil | Returns nil; callers may crash |
| make_fullscreen_region() | No video params | Returns nil |
| file_exists() L115-121 | utils.file_info error | Returns false |
| shell_escape() | Any input | Always returns a string; no error |
| run_subprocess() L276-280 | Subprocess fails | Returns false with msg.verbose |
| EncodeWithProgress.startEncode() | finishedReason != "End of file" | Returns false |
| setValue() for list L2141-2143 | Invalid value | msg.warn only, value unchanged |
| format_filename() | Property expansion fails | Returns fallback or empty string |

## User-Visible Error Messages (via message())

| Condition | Message | Line |
|-----------|---------|------|
| No file being played | "No file is being played" | L1704 |
| First pass failed | "First pass failed! Check the logs for details." | L1841 |
| Encode success | "Encoded successfully! Saved to [path]" | L1874 |
| Encode failed | "Encode failed! Check the logs for details." | L1878 |
| No start time | "No start time, aborting" | L2738 |
| No end time | "No end time, aborting" | L2742 |
| Start >= end | "Start time is ahead of end time, aborting" | L2746 |
| Started encode (detached) | "Started encode, process was detached." | L1857 |
| Started encode (quiet) | "Started encode..." | L1864 |

## Unchecked Return Values

| Function Call | Return | Used? |
|---------------|--------|-------|
| `run_subprocess(first_pass)` | bool | YES — checked at L1840 |
| `run_subprocess(main)` | bool | YES — checked at L1873 |
| `EncodeWithProgress.startEncode()` | bool | YES — checked at L1873 |
| `vp8_patch_logfile()` | (return of write) | NO — not checked |
| `os.remove(logfile)` | bool | NO |
| `os.remove(temp file)` | bool | NO |
| `mp.command_native(dump_cache)` | varies | NO |
| `processFd:close()` | bool | NO |
| `mpopts.read_options()` | void | N/A |

## Runtime Crash Risks

### CRITICAL: undefined 'bitrate' variable (L1779)
```lua
"--" .. type .. "opts-add=minrate=" .. tostring(bitrate) .. "k"
```
`bitrate` is not defined in this scope. The local `video_bitrate` exists. This crashes when `strict_filesize_constraint=true` AND `target_filesize > 0`.

### HIGH: formats[options.output_format] = nil (L1698)
```lua
local format = formats[options.output_format]
-- ... later ...
format:getCodecFlags()  -- nil indexing
```
Crashes if output_format doesn't match a formats key (e.g., default "mp4 (h264/AAC)").

### HIGH: formats["raw"] = nil (L2380)
```lua
_accum_0[_len_0] = { fId, formats[fId].displayName }
```
When fId = "raw", `formats["raw"]` is nil → crash in EncodeOptionsPage.__init().

### MEDIUM: get_duration undefined variable (L620)
```lua
return read_double(reversed_binary_duration)  -- should be big_endian_binary_duration
```
Crashes if get_duration() is called. Not called in normal flow.

### MEDIUM: VideoPoint.set_from_screen with nil dimensions (L470-478)
If `get_video_dimensions()` returns nil (no video loaded), indexing `d.top_left` crashes.

## Error Recovery

The script has no pcall/xpcall error recovery. All errors propagate as uncaught Lua errors to mpv, which logs them to the terminal. The user sees no OSD notification for crashes — the OSD simply remains or disappears.

## Logging

- `msg.verbose()`: Detailed debug info (subprocess output, filter names, command lines).
- `msg.warn()`: Used only for invalid setValue call.
- `msg.info()`: "Encoding to PATH" before encode.
- `msg.error()` / `msg.fatal()`: Not used.

All mpv msg.* calls are always active regardless of log level filtering (at the verbose level, they appear only with --msg-level=webm=verbose).
