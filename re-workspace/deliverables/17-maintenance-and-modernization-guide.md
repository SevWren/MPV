# 17 — Maintenance and Modernization Guide

**Source hash**: sha256:3f454dc0ca030b591d659f7405a3ddfdf7585e5b5eb4cd5b3a573b4151b33214
**Generation date**: 2026-11-15

---

## Immediate Bug Fixes Required

### Fix 1: formats['raw'] crash (FIND-002, HIGH)
Remove `"raw"` from `formatIds` in EncodeOptionsPage.__init at L2368:
```lua
-- Before (L2363-2371):
local formatIds = { "webm-vp8", "webm-vp9", "mp4", "mp4-nvenc", "raw", "mp3", "gif" }
-- After:
local formatIds = { "webm-vp8", "webm-vp9", "mp4", "mp4-nvenc", "mp3", "gif" }
```

### Fix 2: options.output_format default (FIND-003, MEDIUM)
Change default at L17:
```lua
-- Before:
output_format = "mp4 (h264/AAC)",
-- After:
output_format = "mp4",
```

### Fix 3: undefined 'bitrate' in strict mode (FIND-001, HIGH)
At L1779-1780, change `bitrate` to `video_bitrate`:
```lua
-- Before:
"--" .. type .. "opts-add=minrate=" .. tostring(bitrate) .. "k",
"--" .. type .. "opts-add=maxrate=" .. tostring(bitrate) .. "k"
-- After:
"--" .. type .. "opts-add=minrate=" .. tostring(video_bitrate) .. "k",
"--" .. type .. "opts-add=maxrate=" .. tostring(video_bitrate) .. "k"
```

### Fix 4: get_duration variable name (FIND-004, LOW)
At L620:
```lua
-- Before:
return read_double(reversed_binary_duration) / duration_multiplier
-- After:
return read_double(big_endian_binary_duration) / duration_multiplier
```

## Recommended Improvements

### Add IPC validation
In `test_set_options`, add a whitelist of valid option keys:
```lua
local valid_keys = { keybind=true, output_directory=true, ... }
for k, v in pairs(new_options) do
  if valid_keys[k] then options[k] = v end
end
```

### Remove unused option
Remove `strict_bitrate_multiplier` from options table (L15) or implement it in calculate_bitrate.

### Clean up global base64 functions
Change `function base64_encode(data)` to `local base64_encode` at L36 and L49.

### Add temp file cleanup for detached mode
Before returning from subprocess_detached path (L1860), schedule cleanup via mp.add_timeout or similar.

## Modernization Options

1. **Rewrite in MoonScript**: Recover the original structure from the compiled Lua, applying bug fixes.
2. **Rewrite in plain Lua**: Replace MoonScript OOP boilerplate with clean hand-written Lua OOP.
3. **Port to mpv C API**: For performance-critical encoding paths (not recommended for a UI script).
4. **Add Lua 5.3+ compatibility**: Replace `math.ldexp`/`math.frexp` with compatible implementations.

## Testing Recommendations

1. Add test for 'o' key → EncodeOptionsPage instantiation (confirms FIND-002 fix).
2. Add test for encode() with strict_filesize_constraint=true (confirms FIND-001 fix).
3. Add test for encode() with default output_format (confirms FIND-003 fix).
4. Test with actual mpv: open a video, press W, set times, press e.
