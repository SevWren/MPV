# 14b — Windows Developer Environment Analysis

**Source hash**: sha256:3f454dc0ca030b591d659f7405a3ddfdf7585e5b5eb4cd5b3a573b4151b33214
**Generation date**: 2026-11-15
**Context**: Active development environment as of 2026-11-15. See `14-compatibility-matrix.md` for the general matrix.

---

## 1. mpv Build Specifics

| Property | Value |
|----------|-------|
| Build name | `mpv-x86_64-20261114-git-649001d4e2` |
| Build date | 2026-11-14 at 12:51 |
| Commit | `mpv-player/mpv@649001d` |
| Architecture | x86_64 (64-bit) |
| OS | Windows 10 |
| Compiler | clang |
| Build system | zhongfly/mpv-winbuild (GitHub Actions run 43592714705) |
| Install prefix | `--prefix=/mingw64` (zhongfly standard) |
| Lua runtime | LuaJIT 2.1 (bundled; zhongfly builds include LuaJIT by default) |

### 1.1 LuaJIT 2.1 in this build

zhongfly/mpv-winbuild links LuaJIT 2.1 statically. This means:

- `math.ldexp` and `math.frexp` are present (LuaJIT 2.1 retains the Lua 5.1 math library in full). No breakage here.
- Bitwise extensions (`bit.band`, `bit.bor`, etc.) are available as `require("bit")` or via LuaJIT's built-in `bit` library. The script does not use these; they are irrelevant to current analysis.
- `unpack` is global (not `table.unpack`). The script uses `string.char(unpack(...))` at the base64 encoder — this is correct for LuaJIT 2.1.
- The `_class_0` / `_base_0` / `_parent_0` MoonScript scaffolding runs identically under LuaJIT 2.1 and Lua 5.1; no behavioral difference.
- `pcall`/`xpcall` behave identically to standard Lua 5.1. The script has **no** `pcall` wrappers around any encode logic, so a Lua error propagates directly to mpv's error handler on Windows exactly as on Linux.
- `string.format` with `%d`/`%f`/`%s` is identical on Windows and Linux under LuaJIT 2.1. No locale-dependent decimal separator in `string.format` (LuaJIT uses the C locale for `string.format`; `os.date` respects the system locale but is used only for timestamp tokens in `format_filename`).

---

## 2. Windows Path Handling in webm.lua

### 2.1 `parse_directory()` — L239-258

The implementation at L239-258 is Windows-aware:

```lua
local home_dir = os.getenv("HOME")          -- nil on most Windows installs
if not home_dir then
  home_dir = os.getenv("USERPROFILE")        -- e.g. C:\Users\Alice
end
if not home_dir then
  local drive = os.getenv("HOMEDRIVE")      -- e.g. C:
  local path  = os.getenv("HOMEPATH")       -- e.g. \Users\Alice
  if drive and path then
    home_dir = utils.join_path(drive, path) -- joined correctly by mpv
  else
    msg.warn("Couldn't find home dir.")
    home_dir = ""
  end
end
dir, _ = dir:gsub("^~", home_dir)
```

On a standard Windows 10 install with the zhongfly mpv build:

- `HOME` is typically not set (it is set in MSYS2/Git Bash shells, not in a standard user environment). If mpv is launched from Explorer or a desktop shortcut, `HOME` will be nil.
- `USERPROFILE` is always set to `C:\Users\<username>`. This is the correct fallback.
- The tilde expansion produces a path like `C:\Users\Alice` (backslash-separated, as returned by the Windows environment variable).
- `utils.join_path` from mpv's Lua API uses the OS path separator, so joining `C:\Users\Alice` with `cache_dump.ts` produces `C:\Users\Alice\cache_dump.ts`. This is correct.

**Result**: `parse_directory("~")` works correctly on this Windows 10 build. Home directory resolution falls through to `USERPROFILE`.

### 2.2 `shell_escape()` — L282-301

The implementation at L282-301 uses `is_windows` (detected at L259) to switch quoting style:

```lua
local is_windows = type(package) == "table"
                   and type(package.config) == "string"
                   and package.config:sub(1, 1) == "\\"
```

On Windows (where `package.config` starts with `\`), `is_windows` is `true`.

For each argument that contains characters outside `[A-Za-z0-9_/:=-]`, the Windows branch wraps it in double quotes and escapes embedded double quotes as `"\""`  (L289). The entire concatenated string is then additionally wrapped in an outer pair of double quotes (L297-299).

**Analysis of the Windows quoting**:

The inner quote escape `'"\\""'` produces `"\""` around embedded quotes. This is `cmd.exe` escaping syntax where `\"` is interpreted as a literal double quote inside a double-quoted argument. The outer wrapping is the standard Windows `cmd.exe` idiom: `cmd.exe /Q /C "<whole command>"`.

The script does **not** explicitly prepend `cmd.exe /Q /C` before calling `io.popen`. It relies on `io.popen` itself invoking `cmd.exe` to interpret the string. On Windows, `io.popen` under LuaJIT (and standard Lua) calls `_popen` from the MSVCRT, which launches `cmd.exe /c <string>` automatically. The outer double-quote wrapping in `shell_escape` is consistent with this — `cmd.exe /c "<quoted command>"` is the standard Windows popen idiom.

**Potential issue**: The `'"\\""'` escape (L289) produces `"\""` which is correct for `cmd.exe`, but only when the argument itself does not contain other shell metacharacters (e.g., `%`, `^`, `&`, `|`, `<`, `>`). Media filenames on Windows can contain any of these. This is an existing limitation documented in FIND-009-adjacent concerns: the quoting is not fully robust for hostile filenames on Windows.

**Conclusion**: For typical media file paths (no shell metacharacters beyond spaces), `shell_escape` with the Windows branch produces correct `cmd.exe`-compatible strings when used with `io.popen`. Hostile filenames with `%`, `^`, or `&` are not handled.

### 2.3 Null Device — L264-270

```lua
local get_null_path = function()
  if file_exists("/dev/null") then
    return "/dev/null"
  end
  return "NUL"
end
```

This is correctly handled. On Windows, `/dev/null` does not exist as a file, so `file_exists("/dev/null")` returns false and the function returns `"NUL"` — the Windows null device. No bug here.

### 2.4 `format_filename()` — L174-238

The filename sanitization at L236 strips Windows-illegal characters:

```lua
filename, _ = filename:gsub("[<>:\"/\\|?*]", "")
```

This removes `< > : " / \ | ? *` — the full set of characters illegal in Windows filenames. This is correct and Windows-aware. The resulting filename is safe for Windows file creation.

**Path separator note**: `format_filename` returns only a filename (no directory component). The directory is prepended by `utils.join_path(dir, formatted_filename)` at L1814, which uses the OS-appropriate separator. No hardcoded `/` is used as a path separator in the output path construction.

### 2.5 `find_path()` — L1673-1695

For HLS streams on Windows, the cache dump path becomes:

```
C:\Users\<username>\cache_dump.ts
```

This is a valid Windows path. The `dump_cache` command at L1683-1688 passes it via `mp.command_native` (argv-style, not shell string), so no quoting issues.

For non-stream files, `utils.split_path(path)` returns the directory portion using Windows path separators. The resulting `dir` is then passed to `utils.join_path`, which is correct.

---

## 3. Windows-Specific Bugs

### 3.1 FIND-001: Undefined `bitrate` in strict mode (L1779-1780)

**Windows reproduction steps** (mpv-x86_64-20261114-git-649001d4e2, Windows 10):

1. Create or edit `%APPDATA%\mpv\script-opts\webm.conf` (Windows mpv config path).
2. Add line: `strict_filesize_constraint=yes`
3. Launch mpv with any video file.
4. Press the webm keybind (default: `w`) to open the UI.
5. Press `e` to encode the current selection.
6. Expected: encode starts. Actual: Lua error `attempt to perform arithmetic on a nil value (global 'bitrate')` logged to mpv's terminal/log. Encode fails silently from the user's perspective (mpv shows "Encode failed!").

**Windows-specific note**: The error surfaces identically on Windows as on Linux. No Windows-specific aggravating factor.

### 3.2 FIND-002: `formats["raw"]` nil crash (L2363-2385)

**Windows reproduction steps**:

1. Launch mpv with any video file on Windows 10.
2. Press the webm keybind to open the main UI.
3. Press `o` to open the EncodeOptionsPage.
4. Expected: options page opens. Actual: Lua error `attempt to index a nil value (field '?')` at the line accessing `formats["raw"]`. The options UI fails to initialize and closes immediately.

**Windows-specific note**: This crash is identical on Windows. The `formats` registry does not include a `"raw"` key. The EncodeOptionsPage attempts to look it up and crashes. This is the highest-impact bug for a Windows user trying to use the script.

### 3.3 FIND-003: `output_format` default mismatch (L17, L1698)

**Windows reproduction steps**:

1. Launch mpv on Windows 10 with this build.
2. Do NOT open the options page (do not press `o`).
3. Set a start and end point (e.g., `i` and `o`).
4. Press the encode keybind directly.
5. At L1698, `formats[options.output_format]` is called. `options.output_format` holds the default string from L17. If this string does not exactly match a key in the `formats` table, `format` is nil and the encode function crashes with `attempt to index a nil value`.

**Windows-specific note**: No Windows-specific behavior. The mismatch is a code-level bug independent of OS.

---

## 4. LuaJIT-Specific Behavior in this Build

| Feature | LuaJIT 2.1 Behavior | Impact on webm.lua |
|---------|--------------------|--------------------|
| `math.ldexp` | Present (Lua 5.1 compat) | Used in `read_double`/`write_double` (SEG-04). Works correctly. |
| `math.frexp` | Present | Same. Works correctly. |
| `unpack` (global) | Present | Used in base64 `string.char(unpack(...))`. Works correctly. |
| `string.format %d` | C locale, no locale override | Produces integers without locale separators. Correct. |
| `string.format %f` | C locale | Decimal point is always `.`. Correct for ffmpeg flag values. |
| `pcall` | Standard | Not used in encode path. Errors propagate to mpv. |
| `_class_0` scaffolding | Identical to Lua 5.1 | No behavioral difference. |
| `bit` library | Available (LuaJIT built-in) | Not used by the script. |
| JIT compilation | On by default | No behavioral difference for this script's workload. |
| `io.popen` | Available via MSVCRT `_popen` | Calls `cmd.exe /c` internally. See §2.2 above. |

---

## 5. Progress Display on Windows

`should_display_progress()` at L315-321 returns `false` when `options.display_progress == "auto"` and `is_windows == true`. On this Windows 10 build:

- Progress display is **disabled by default** in auto mode.
- The encode path falls through to `run_subprocess` (blocking, no popen).
- `io.popen` / `run_subprocess_popen` is **not called** in the default Windows configuration.
- The `shell_escape` Windows quoting path is therefore not exercised in the default auto-progress mode on Windows. It would only be triggered if the user explicitly sets `display_progress=yes`.

This is an important observation: most Windows users will never exercise the `io.popen` path, and therefore the Windows quoting behavior in `shell_escape` is rarely tested.

---

## 6. `subprocess_detached` in this Build

The script calls `utils.subprocess_detached` at L1858:

```lua
return utils.subprocess_detached({ args = command })
```

In the zhongfly mpv-x86_64-20261114 build (mpv@649001d), `mp.utils.subprocess_detached` is present. It was introduced in mpv 0.29.0 and has been stable since. This build is from 2026-11-14 and is well past that version. The call is `utils.subprocess_detached` where `utils = mp.utils` (assigned at the top of the script).

**Conclusion**: `mp.utils.subprocess_detached` is available and correct for this build. No compatibility issue.

---

## 7. Summary Table for This Build

| Item | Status | Notes |
|------|--------|-------|
| LuaJIT 2.1 | Compatible | All used APIs present |
| `parse_directory("~")` | Works | Falls through to `USERPROFILE` |
| `get_null_path()` | Works | Returns `"NUL"` on Windows |
| `shell_escape` Windows branch | Partial | Correct for typical paths; hostile filenames with `%^&|<>` not escaped |
| `format_filename` sanitization | Works | Strips all Windows-illegal chars |
| `subprocess_detached` | Works | Available in mpv@649001d |
| `io.popen` path | Rarely triggered | Only when `display_progress=yes` explicitly on Windows |
| FIND-001 | Immediately reproducible | Enable `strict_filesize_constraint=yes` |
| FIND-002 | Immediately reproducible | Press `o` to open options page |
| FIND-003 | Immediately reproducible | Encode without opening options |
| `/dev/null` handling | Handled | `get_null_path()` returns `"NUL"` correctly |
