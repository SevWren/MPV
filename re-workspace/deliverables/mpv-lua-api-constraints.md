# mpv Lua API Constraints
## Target: mpv-x86_64-20261114-git-649001d4e2 (LuaJIT 2.1, clang, Windows 10)
## Source: re-workspace/canonical/webm.lf.lua (2856 lines)

---

## 1a. APIs Confirmed Available in webm.lf.lua

### mp.utils.subprocess
**Signature used**: `utils.subprocess({ args = <table>, cancellable = <bool> })`
**Line references**: L273 (wrapper `run_subprocess`), L1836–1838 (first-pass twopass), L1865–1867 (non-detached encode)
**Windows-specific behavior**: None in the call itself; the subprocess spawns a second `mpv` process. On Windows the spawned process is a console application and inherits the parent's console window, which causes a brief window flash unless `run_detached` is used instead.
**Version requirement**: Available since mpv 0.9. No version concern for 649001d.

### mp.utils.subprocess_detached
**Signature used**: `utils.subprocess_detached({ args = <table> })`
**Line references**: L1858–1860
**Windows-specific behavior**: On Windows, `subprocess_detached` internally uses `CreateProcess` with the `DETACHED_PROCESS` flag (mpv C source). This is not `cmd.exe /Q /C start ""` — that wrapper is only used for older mpv versions that lacked native detach support. The 649001d build uses the native path. No console window is created.
**Version requirement**: Available since mpv 0.14. Present in 649001d.

### mp.utils.join_path
**Signature used**: `utils.join_path(dir, filename)` → string
**Line references**: L249 (parse_directory HOMEDRIVE+HOMEPATH fallback), L1682 (cache_dump.ts HLS path), L1814 (output path construction)
**Windows-specific behavior**: On Windows, `join_path` uses `\` as the separator and handles drive-letter paths correctly. This is handled transparently by mpv's implementation; the script does not special-case it.
**Version requirement**: Available since mpv 0.9.

### mp.utils.split_path
**Signature used**: `utils.split_path(path)` → dir, filename
**Line references**: L1808 (extract directory from source file path)
**Windows-specific behavior**: Returns the directory portion using the platform separator. Correctly handles Windows absolute paths like `D:\ProgramData\asus\file.mp4`.
**Version requirement**: Available since mpv 0.9.

### mp.utils.file_info
**Signature used**: `utils.file_info(name)` → info_table or nil, error
**Line references**: L116–120 (`file_exists` helper), L1678 (stream detection in `find_path`)
**Windows-specific behavior**: On Windows, calls `_wstat` internally. Handles UNC paths. Returns nil for non-existent files. Used here only as a boolean existence check (nil = absent).
**Version requirement**: Available since mpv 0.17.

### mp.utils.parse_json
**Signature used**: `utils.parse_json(json_string)` → table
**Line references**: L69 (`test_set_options` IPC handler)
**Windows-specific behavior**: None. Pure JSON parser; platform-independent.
**Version requirement**: Available since mpv 0.14.

### mp.utils.format_json
**Not used in webm.lf.lua.**

### mp.utils.write_file
**Not used in webm.lf.lua.**

### mp.get_property
**Signature used**: `mp.get_property(name)` → string or nil
**Line references**:
- L200: `mp.get_property("filename")`
- L201: `mp.get_property("filename/no-ext")`
- L206: `mp.get_property("media-title")`
- L225: `mp.get_property("stream-open-filename", "")`
- L225: `mp.get_property("filename", "")`
- L802: `mp.get_property("colormatrix")` (RawVideo.getColorspace)
- L1526–1528: `mp.get_property("brightness")`, `"contrast"`, `"saturation"` (filter builder)
- L1542: generic `mp.get_property(property_name)` in `append_property`
- L1526–1591: filename/no-ext for metadata
- L1674: `mp.get_property('path')`
- L1681: `mp.get_property('file-format')`
**Windows-specific behavior**: `filename` and `path` return Windows paths with backslashes on Windows. `stream-open-filename` returns the actual opened URL/path.
**Version requirement**: Core API; always available.

### mp.get_property_native
**Signature used**: `mp.get_property_native(name)` → Lua native type
**Line references**:
- L207: `mp.get_property_native('aid')`, `mp.get_property_native('mute')`
- L208: `mp.get_property_native('height')`
- L345: `mp.get_property_native("video-out-params")`
- L350: `mp.get_property_bool("keepaspect")` (alias)
- L355: `mp.get_property_number("video-rotate")` (alias)
- L366: `mp.get_property_native("video-unscaled")`
- L367: `mp.get_property_number("panscan")`
- L409–415: `mp.get_property_number("video-zoom")`, `"video-align-x/y"`, `"video-pan-x/y"`
- L876: `mp.get_property_native("video-params/colormatrix")` (WebmVP8.getPreFilters)
- L1431: `mp.get_property_native("track-list")`
- L1552: `mp.get_property_native(property_name)` in `append_list_options`
- L1579: `mp.get_property_native("speed")`
- L1598: `mp.get_property_native("vf")`
- L1659 (implicit): `mp.get_property_bool("demuxer-via-network", false)`
- L2545: `mp.get_property_native("vf")` (PreviewPage.prepare)
- L2594–2596: `mp.get_property_native("vf")`, `"time-pos"`, `"pause"` (PreviewPage.__init)
- L2645: `mp.get_property_number("time-pos")` (MainPage.setStartTime/setEndTime)
- L2659–2661: `mp.get_property_native("duration")` (MainPage.setupStartAndEndTimes)
**Windows-specific behavior**: None. Property values are platform-normalised by mpv.
**Version requirement**: Core API.

### mp.get_property_osd
**Signature used**: `mp.get_property_osd(name)` → string
**Line references**:
- L81: `mp.get_property_osd("osd-ass-cc/0")` (message helper — retrieves ASS override escape)
- L132–146: `get_property = mp.get_property_osd` (default in expand_properties, unless raw `=` prefix)
**Windows-specific behavior**: None.
**Version requirement**: Core API.

### mp.set_property
**Signature used**: `mp.set_property(name, value)`
**Line references**:
- L2569: `mp.set_property("ab-loop-a", "no")` (PreviewPage.dispose)
- L2569: `mp.set_property("ab-loop-b", "no")` (PreviewPage.dispose)
**Windows-specific behavior**: None.
**Version requirement**: Core API.

### mp.set_property_native
**Signature used**: `mp.set_property_native(name, value)`
**Line references**:
- L2560: `mp.set_property_native("vf", vf)` (PreviewPage.prepare)
- L2562: `mp.set_property_native("ab-loop-a", startTime)`
- L2563: `mp.set_property_native("ab-loop-b", endTime)`
- L2564: `mp.set_property_native("time-pos", startTime)`
- L2566: `mp.set_property_native("pause", false)`
- L2572: `mp.set_property_native(prop, value)` (restore loop in PreviewPage.dispose)
**Windows-specific behavior**: None.
**Version requirement**: Core API.

### mp.commandv
**Signature used**: `mp.commandv("script-message", ...)` → (implicit return)
**Line references**: L65 (`emit_event` — sends IPC-style events to other scripts)
**Windows-specific behavior**: None.
**Version requirement**: Core API.

### mp.command_native
**Signature used**: `mp.command_native({ 'dump_cache', start_str, end_str, path })`
**Line references**: L1683–1688 (HLS stream cache dump)
**Windows-specific behavior**: The output path is a Windows absolute path. The `dump_cache` command writes the TS file. No special Windows handling in the script; mpv handles the path internally.
**Version requirement**: `dump_cache` command available since mpv 0.33 (requires `--cache=yes`).

### mp.osd_message
**Signature used**: `mp.osd_message(text, duration)`
**Line references**: L83 (`message` helper)
**Windows-specific behavior**: None.
**Version requirement**: Core API.

### mp.add_key_binding
**Signature used**: `mp.add_key_binding(key, name, func, { repeatable = false })`
**Line references**: L2840–2848 (register top-level `W` keybind for `display-webm-encoder`)
**Windows-specific behavior**: None. Key names are platform-independent in mpv's input system.
**Version requirement**: Core API. The 4-argument form with options table available since mpv 0.18.

### mp.add_forced_key_binding
**Signature used**: `mp.add_forced_key_binding(key, name, func, { repeatable = true })`
**Line references**: L1226–1229 (Page.add_keybinds — registers per-page modal keybinds)
**Windows-specific behavior**: None.
**Version requirement**: Available since mpv 0.18.

### mp.remove_key_binding
**Signature used**: `mp.remove_key_binding(name)`
**Line references**: L1236 (Page.remove_keybinds — deregisters keybinds when page hides)
**Windows-specific behavior**: None.
**Version requirement**: Available since mpv 0.18.

### mp.register_event
**Signature used**: `mp.register_event("file-loaded", callback)`
**Line references**: L2849–2855 (triggers `mainPage:setupStartAndEndTimes` on file load)
**Windows-specific behavior**: None.
**Version requirement**: Core API.

### mp.register_script_message
**Signature used**: `mp.register_script_message("mpv-webm-set-options", callback)`
**Line references**: L74 (IPC options injection handler — FIND-006 security issue)
**Windows-specific behavior**: On Windows, the mpv IPC socket is a named pipe (`\\.\pipe\mpvsocket`). Same-user processes on Windows 10 can connect to this pipe without special privileges — slightly broader attack surface than Unix domain sockets.
**Version requirement**: Available since mpv 0.9.

### mp.observe_property
**Signature used**: `mp.observe_property(property_name, "native", callback)`
**Line references**:
- L446 (monitor_dimensions — 11 properties for dimension tracking)
- L1258 (Page.observe_properties — same 11 properties, per-page)
**Windows-specific behavior**: None.
**Version requirement**: Core API.

### mp.unobserve_property
**Signature used**: `mp.unobserve_property(callback_reference)`
**Line references**: L1263 (Page.unobserve_properties)
**Windows-specific behavior**: None.
**Version requirement**: Core API.

### mp.get_osd_size
**Signature used**: `mp.get_osd_size()` → width, height
**Line references**:
- L312 (calculate_scale_factor)
- L364 (get_video_dimensions)
- L1268 (Page.clear)
- L1332 (EncodeWithProgress.draw)
- L1953 (CropPage.draw)
- L2576 (PreviewPage.draw)
- L2672 (MainPage.draw)
**Windows-specific behavior**: Returns the OSD overlay size in pixels, which on Windows corresponds to the window client area size. HiDPI/DPI-awareness is handled by mpv; the script does not need to adjust.
**Version requirement**: Core API.

### mp.set_osd_ass
**Signature used**: `mp.set_osd_ass(width, height, ass_string)`
**Line references**:
- L1269 (Page.clear — called with empty string to clear)
- L1337 (EncodeWithProgress.draw)
- L1965 (CropPage.draw)
- L2581 (PreviewPage.draw)
- L2684 (MainPage.draw)
**Windows-specific behavior**: None. ASS rendering is handled by libass which is platform-independent.
**Version requirement**: Core API.

### mp.get_mouse_pos
**Signature used**: `mp.get_mouse_pos()` → x, y
**Line references**: L1910, L1917 (CropPage.setPointA, setPointB)
**Windows-specific behavior**: Returns screen coordinates within the mpv window. On Windows, coordinates are in physical pixels (not DPI-scaled).
**Version requirement**: Core API.

### mp.msg.* (via `msg = require("mp.msg")`)
**Variants used**:
- `msg.verbose(...)` — L274, L275, L306, L1370, L1599, L1604, L1835, L1849, L1855, L2856
- `msg.info(...)` — L813 (RawVideo colorspace warning), L1854
- `msg.warn(...)` — L251 (home dir not found)
**Line references**: see above.
**Windows-specific behavior**: Output goes to mpv's log system; on Windows this means the mpv log file (if `--log-file` set) and the debug output visible in MSVC debugger or via `DebugView`. Not visible in a standard cmd.exe window when running detached.
**Version requirement**: Core API.

### mp.options.read_options (via `mpopts = require("mp.options")`)
**Signature used**: `mpopts.read_options(options_table)`
**Line references**: L33
**Windows-specific behavior**: Reads from `%APPDATA%\mpv\script-opts\webm.conf` on Windows (or wherever `--config-dir` points). Key-value parsing is platform-independent.
**Version requirement**: Available since mpv 0.9.

### io.open
**Signature used**:
- `io.open(logfile_path, "rb")` — L709 (read VP8 firstpass logfile)
- `io.open(logfile_path, "wb")` — L726 (write patched logfile)
**Line references**: L709, L726
**Windows-specific behavior**: On Windows, binary mode (`"b"`) is required to prevent CRLF translation of binary data. The script correctly uses `"rb"` and `"wb"` for the logfile I/O, which is correct behavior for the binary VP8 stats format.
**Version requirement**: Standard Lua 5.1 / LuaJIT — always available.

### io.popen
**Signature used**: `io.popen(command_line_string)` → file handle
**Line references**: L307 (`run_subprocess_popen` — used only when `display_progress=true` and not Windows, since `should_display_progress` returns false on Windows by default)
**Windows-specific behavior**: On Windows, `io.popen` opens a `cmd.exe` subshell. The `shell_escape` function (L282–301) wraps the entire command in an outer `"..."` to handle the Windows `cmd.exe` quoting rules. The `2>&1` appended at L305 redirects stderr to stdout for mpv progress line parsing. Under Windows, `io.popen` is effectively disabled in this script because `should_display_progress()` returns `false` for `is_windows` when `display_progress = "auto"`.
**Version requirement**: Standard Lua 5.1 / LuaJIT.

### os.time
**Not used in webm.lf.lua.**

### os.date
**Signature used**: `os.date("%" .. format)` where format is a strftime letter
**Line references**: L233 (format_filename — `%t<X>` template expansion)
**Windows-specific behavior**: On Windows, `os.date` uses the MSVCRT `strftime` implementation. All standard POSIX strftime codes work. No known differences for the codes used here.
**Version requirement**: Standard Lua 5.1.

### os.remove
**Signature used**: `os.remove(path)`
**Line references**:
- L1880: `os.remove(get_pass_logfile_path(out_path))` — delete VP8 two-pass logfile
- L1882: `os.remove(path)` — delete HLS cache_dump.ts temp file
**Windows-specific behavior**: On Windows, `os.remove` calls `_wremove`. It will fail silently if the file is locked by another process. Under `run_detached=true` (the default), these lines are **never reached** (the encode branch returns at L1858 before them) — this is FIND-007.
**Version requirement**: Standard Lua 5.1.

### os.tmpname
**Not used in webm.lf.lua.**

### os.getenv
**Signature used**: `os.getenv("HOME")`, `os.getenv("USERPROFILE")`, `os.getenv("HOMEDRIVE")`, `os.getenv("HOMEPATH")`
**Line references**: L241–253 (`parse_directory`)
**Windows-specific behavior**: On Windows, `HOME` is typically not set (it is set by Git for Windows but not by default). The fallback chain `USERPROFILE` → `HOMEDRIVE`+`HOMEPATH` correctly handles the Windows environment. `USERPROFILE` is always set on Windows 10 and is the correct home directory variable.
**Version requirement**: Standard Lua 5.1.

---

## 1b. APIs NOT Used but Needed for Diagnostic Mechanism

### mp.utils.write_file("file://path", data)
**Status**: NOT used in webm.lf.lua. Available in mpv >= 0.37.
**Availability in 649001d**: The build date 20261114 is well after the 0.37 release (November 2022). Confirmed available.
**Usage for diagnostics**: Can write a diagnostic report file without needing `io.open`. Accepts `"file://C:/path/to/file"` URI syntax on Windows.
**Caveat**: The `file://` URI on Windows requires `file:///C:/...` (triple slash for absolute paths). Using `io.open` directly is simpler and equally safe for diagnostic writes.

### mp.utils.getpid()
**Status**: NOT used in webm.lf.lua.
**Availability in 649001d**: Available since mpv 0.33. Present in this build.
**Usage for diagnostics**: Can generate unique temp filenames (e.g., `webm-diag-<pid>.txt`) to avoid collisions across concurrent mpv instances.

### mp.get_script_directory()
**Status**: NOT used in webm.lf.lua.
**Availability in 649001d**: Available since mpv 0.33. Present in this build.
**Usage for diagnostics**: Returns the directory containing webm.lua itself, allowing relative path construction like `mp.get_script_directory() .. "\\webm-debug.log"` for Windows.

### mp.utils.file_info(path) — post-encode size check
**Status**: USED as `file_exists` boolean helper (L116–120). NOT used for size inspection.
**Post-encode diagnostic use**: `local info = mp.utils.file_info(out_path); if info then msg.info("Output size: " .. info.size) end` — `info.size` gives the byte count of the output file, confirming whether ffmpeg produced output at all.

---

## 1c. Windows-Specific Behaviors

### is_windows Detection
**Location**: L259
```lua
local is_windows = type(package) == "table"
                   and type(package.config) == "string"
                   and package.config:sub(1, 1) == "\\"
```
This detects Windows by checking `package.config`'s first character. On Windows this is `\` (the directory separator). This is the idiomatic LuaJIT/Lua 5.1 Windows detection pattern. It does not use `jit.os` (which would be `"Windows"` on LuaJIT 2.1) but achieves the same result.

### shell_escape Windows Branch (L282–301)
On Windows (`is_windows == true`):
1. Each argument that contains non-alphanumeric characters is wrapped in double-quotes: `'"' .. arg .. '"'` with internal double-quotes escaped as `'"\\""'` (L289).
2. After all arguments are individually quoted, the **entire concatenated string** is wrapped in an additional outer double-quote pair: `'"' .. concat .. '"'` (L298).
This double-wrapping is required for passing the string through `cmd.exe` when using `io.popen`. It does NOT apply to `mp.utils.subprocess` / `mp.utils.subprocess_detached`, which accept arg arrays and bypass the shell entirely.

### subprocess_detached Windows Behavior
In the 649001d build, `mp.utils.subprocess_detached` uses mpv's C-level `CreateProcess` with `DETACHED_PROCESS`. It does **not** wrap in `cmd.exe /Q /C start ""`. The `start ""` wrapper pattern was used in older mpv versions before the native detach API was available. The args array is passed directly to the Windows process creation API.

### parse_directory("~") — USERPROFILE on Windows
**Location**: L241–253
On Windows:
- `HOME` is checked first (may be set by Git Bash or WSL)
- Falls back to `USERPROFILE` (e.g., `C:\Users\username`) — **always set on Windows 10**
- Ultimate fallback: `HOMEDRIVE` + `HOMEPATH` via `utils.join_path` (e.g., `C:` + `\Users\username`)

### Null Device
**Location**: L265–270
```lua
local get_null_path = function()
  if file_exists("/dev/null") then return "/dev/null" end
  return "NUL"
end
```
On Windows, `/dev/null` does not exist as a filesystem path, so the function returns `"NUL"` (Windows null device). Note: `get_null_path` is defined but **not called anywhere** in the current script — it is dead code at present.

### Path Separator Handling
The script uses `utils.join_path` and `utils.split_path` for all path construction, delegating separator handling to mpv's C layer. No hardcoded `/` or `\` separators appear in path construction code. The exception is `parse_directory("~")` which uses regex substitution on the leading `~` character — this is separator-agnostic.

### display_progress Windows Override
**Location**: L316–320
```lua
local should_display_progress = function()
  if options.display_progress == "auto" then
    return not is_windows
  end
  return options.display_progress
end
```
When `display_progress = "auto"` (not the default — default is `"true"`), progress display is disabled on Windows. This avoids the `io.popen` path, which on Windows requires `cmd.exe` and produces unreliable output.

---

## 1d. Diagnostic-Safe APIs

### Read-Only (safe to call at any time, no side effects)
| API | Safety Note |
|-----|-------------|
| `mp.get_property(name)` | Pure read; no state change |
| `mp.get_property_native(name)` | Pure read |
| `mp.get_property_osd(name)` | Pure read |
| `mp.get_property_number(name)` | Pure read |
| `mp.get_property_bool(name)` | Pure read |
| `mp.utils.file_info(path)` | Filesystem stat only; no write |
| `os.time()` | Returns current epoch time; no state change |
| `os.date(fmt)` | Formats time; no state change |
| `os.getenv(name)` | Reads environment; no state change |

### Write (safe — creates files only, no mpv state change)
| API | Safety Note |
|-----|-------------|
| `mp.msg.verbose(...)` | Writes to log; no mpv state change |
| `mp.msg.info(...)` | Writes to log; no mpv state change |
| `mp.msg.warn(...)` | Writes to log; no mpv state change |
| `io.open(path, "w")` | Creates/overwrites a file; safe as long as path is chosen carefully |
| `mp.utils.write_file(uri, data)` | Same as io.open write; safe |

### Risky (avoid in diagnostic routine)
| API | Risk |
|-----|------|
| `mp.utils.subprocess(...)` | Spawns external process; could conflict with ongoing encode, blocks mpv event loop |
| `mp.utils.subprocess_detached(...)` | Same risk; additionally loses error reporting |
| `io.popen(...)` | Spawns shell process; on Windows requires `cmd.exe` with brittle quoting |
| `mp.set_property_native(...)` | Mutates mpv playback state; could disrupt active playback |
| `mp.commandv(...)` | Sends mpv command; side effects depend on command used |
| `os.remove(...)` | Destructive filesystem operation |
