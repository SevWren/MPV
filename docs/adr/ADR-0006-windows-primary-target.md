# Windows 10 with mpv build 649001d4e2 is the primary development target

The active development and debugging environment is Windows 10 running mpv build `mpv-x86_64-20261114-git-649001d4e2` (compiled with clang, git commit `649001d`). This is the only build against which bugs are reproduced and fixes are verified.

The script contains explicit Windows detection (`is_windows = package.config:sub(1,1) == "\\"`) and branches on it in multiple places: shell wrapping uses `cmd.exe /Q /C "..."`, the null device is `NUL` instead of `/dev/null`, and `display_progress = "auto"` defaults to disabled on Windows.

## Consequences

- All confirmed findings (FIND-001 through FIND-010) were observed or reproduced on this Windows build. POSIX behavior has not been independently verified against the same build date.
- The `cmd.exe` quoting rules applied by `shell_escape` are the primary correctness concern; POSIX shell quoting is secondary.
- Path separator handling (backslash vs forward slash) in `output_directory` and temp file paths must be validated against Windows path semantics first.
- When testing a fix, the reference environment is Windows 10 + this exact mpv binary. Fixes that pass on Linux but have not been tested on Windows are not considered verified.
- Future mpv builds may change Lua API surface, subprocess behavior, or IPC semantics. Pin the build identifier when reporting a regression.
