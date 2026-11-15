# Two separate process execution paths: subprocess vs io.popen

The encoder uses two distinct mechanisms to launch ffmpeg/mpv encode processes:

1. **`mp.utils.subprocess`** (argv array): used when `run_detached = false`. The process runs in the foreground; mpv blocks until it exits and can capture stdout/stderr.
2. **`io.popen(shell_escape(...))`**: used when `run_detached = true`. The command string is built by joining shell-escaped argv tokens and passed to the OS shell (`cmd.exe /Q /C "..."` on Windows, `sh -c` on POSIX).

The split is intentional. `mp.utils.subprocess_detached` was not available in older mpv builds, and `io.popen` is the standard Lua mechanism for fire-and-forget process launch. Using `io.popen` with a shell-escaped string is the only portable background-process path available to a Lua script embedded in mpv.

## Consequences

- The argv-style path is injection-safe by construction: individual tokens are never interpreted by a shell.
- The `io.popen` path is injection-safe only if `shell_escape` is correct for every token on every platform. A bug in `shell_escape` on Windows (`cmd.exe` quoting rules differ from POSIX) or on POSIX (tokens with `$`, backticks, etc.) can produce a command injection.
- The `run_detached = true` path does not wait for the subprocess to exit, so temp files written before the call (e.g., firstpass `.log`) are not cleaned up after encoding completes. This is FIND-007.
- When `display_progress = "auto"`, progress display is suppressed on Windows because the foreground path is unreliable there; the detached path is the Windows default.
- Any addition of a new flag that contains shell metacharacters must be validated against `shell_escape` before it is passed through the `io.popen` path.
