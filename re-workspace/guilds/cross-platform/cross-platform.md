# Cross-Platform Guild Report

## Platform Detection

`is_windows` is defined at **L259** (in SEG-01, parse_directory area):

```lua
local is_windows = type(package) == "table" and type(package.config) == "string"
                   and package.config:sub(1, 1) == "\\"
```

This detects Windows by checking if `package.config` starts with `\` (the Windows path separator). This is the standard Lua idiom for Windows detection.

**Note**: This was missed by the initial symbol extractor because `is_windows` is a local variable assignment without a function call pattern. It was found at L259 by grep.

## Windows vs POSIX Differences

| Feature | POSIX | Windows |
|---------|-------|---------|
| Shell escaping | `'value'` single-quote wrap | `"value"` double-quote wrap |
| Command wrap | No extra wrapping | Entire command wrapped in `""` |
| Null device | `/dev/null` | `NUL` |
| Auto progress | Enabled | Disabled |

**Lines using is_windows**:
- L288: Double-quote escaping in shell_escape
- L297: Wrap entire command string in Windows
- L318: `should_display_progress()` — auto → not is_windows

## Null Path

`get_null_path()` (L265-271):
- Windows: returns `"NUL"`
- POSIX: returns `"/dev/null"`

Used for suppressing output in pass1 (potential, not yet confirmed in encode path).

## Path Handling

`utils.join_path()` and `utils.split_path()` are used for path manipulation — these mpv functions handle platform-specific separators internally.

`parse_directory(dir)` uses `mp.command_native({"expand-path", dir})` for `~` expansion — works cross-platform via mpv.

## Subprocess Execution

- `mp.utils.subprocess` and `mp.utils.subprocess_detached` are mpv-native — work cross-platform.
- `io.popen(command_line)` — on Windows uses `cmd.exe`. The Windows shell quoting from `shell_escape` (extra outer double-quotes) is specifically designed for this.
- Progress display disabled by default on Windows (`display_progress="auto"` → `not is_windows`).

## Summary

Cross-platform support is intentional and reasonably complete. The `is_windows` detection uses a reliable standard Lua idiom. The main Windows-specific concern is `io.popen` with the shell-escaped command string — complex paths or arguments may still fail on Windows cmd.exe due to its non-POSIX quoting rules.
