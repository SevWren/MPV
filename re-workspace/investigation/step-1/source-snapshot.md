# Step 1C — Source Code Snapshot

## Patched webm.lua: `/home/vercel-sandbox/MPV/scripts/webm.lua`
## Canonical pre-patch: `/home/vercel-sandbox/MPV/re-workspace/canonical/webm.lf.lua`

---

## 1. encode() — initial command array

### Canonical (pre-patch) [canonical:1707-1714]:
```lua
  local command = {
    "mpv",
    path,
    "--start=" .. seconds_to_time_string(startTime, false, true),
    "--end=" .. seconds_to_time_string(endTime, false, true),
    "--loop-file=no",
    "--no-pause"
  }
```

### Patched [webm.lua:1707-1720]:
```lua
  local command = {
    "mpv",
    "--no-config",
    "--load-scripts=no",
    "--keep-open=no",
    "--loop-playlist=no",
    "--hwdec=no",
    "--save-position-on-quit=no",
    path,
    "--start=" .. seconds_to_time_string(startTime, false, true),
    "--end=" .. seconds_to_time_string(endTime, false, true),
    "--loop-file=no",
    "--no-pause"
  }
```

**Difference**: Patched version inserts 6 isolation flags before `path`:
`--no-config`, `--load-scripts=no`, `--keep-open=no`, `--loop-playlist=no`, `--hwdec=no`, `--save-position-on-quit=no`

---

## 2. additional_flags token loop

### Canonical (pre-patch) [canonical:1790-1792]:
```lua
  for token in string.gmatch(options.additional_flags, "[^%s]+") do
    command[#command + 1] = token
  end
```
**NO validation** — every token is added unconditionally.

### Patched [webm.lua:1796-1801]:
```lua
  for token in string.gmatch(options.additional_flags, "[^%s]+") do
    if token:sub(1, 2) == "--" then
      command[#command + 1] = token
    else
      msg.warn("Skipping invalid additional_flag (missing -- prefix): " .. tostring(token))
    end
  end
```
**WITH validation** — tokens without `--` prefix are skipped with a warning.

---

## 3. non_strict_additional_flags token loop

### Canonical (pre-patch) [canonical:1793-1796]:
```lua
  if not options.strict_filesize_constraint then
    for token in string.gmatch(options.non_strict_additional_flags, "[^%s]+") do
      command[#command + 1] = token
    end
```
**NO validation** — every token is added unconditionally.

### Patched [webm.lua:1803-1810]:
```lua
  if not options.strict_filesize_constraint then
    for token in string.gmatch(options.non_strict_additional_flags, "[^%s]+") do
      if token:sub(1, 2) == "--" then
        command[#command + 1] = token
      else
        msg.warn("Skipping invalid non_strict_additional_flag (missing -- prefix): " .. tostring(token))
      end
    end
```
**WITH validation** — tokens without `--` prefix are skipped with a warning.

---

## 4. subprocess_detached call [webm.lua:1870-1874]:
```lua
  if options.run_detached then
    message("Started encode, process was detached.")
    return utils.subprocess_detached({
      args = command
    })
```

---

## 5. run_subprocess call path [webm.lua:1879-1882]:
```lua
      res = run_subprocess({
        args = command,
        cancellable = false
      })
```
`run_subprocess` calls `utils.subprocess(params)` [webm.lua:273].

---

## 6. Occurrences of isolation flags in canonical
Searching canonical for `--no-config`, `--load-scripts`, `--keep-open`, `--loop-playlist`:
Result: **ZERO occurrences** in canonical/webm.lf.lua encode() command array.
These flags are ABSENT in the pre-patch version.

---

## 7. get_video_encode_flags() — player properties re-applied

[webm.lua:1642-1645]:
```lua
local get_video_encode_flags
get_video_encode_flags = function(format, region)
  local flags = { }
  append(flags, get_playback_options())
```

`get_playback_options()` reads and re-applies:
- `sub-ass-override`
- `sub-auto`
- `sub-pos`
- `sub-delay`
- `video-rotate`
- `ytdl-format`
- `deinterlace`
- Video filters via `get_video_filters()` including scale, crop, eq, fps

These are the user's current playback settings, forwarded to the encode subprocess.
The user's `keep-open=yes` and `save-position-on-quit=yes` from mpv.conf are NOT
forwarded here — they come from the user's mpv.conf being loaded by the subprocess.
In the canonical version, `--no-config` was absent, so the encode subprocess loaded
the user's full mpv.conf including `keep-open=yes`. [log:62]
