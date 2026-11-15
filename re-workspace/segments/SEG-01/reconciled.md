# SEG-01 Reconciled Analysis
**Lines**: L75-338
**Description**: Utility layer — text formatting, time conversion, file/path utilities, subprocess wrappers, shell escaping, geometry helpers

## Purpose
SEG-01 provides the cross-cutting utility functions used by all other segments. Key subsystems: ASS text formatting, time-to-string conversions, property template expansion, filename generation, path/directory resolution, two subprocess execution wrappers (safe and popen), shell argument escaping, scale factor calculation, progress display decision, and list reversal.

## Line Walkthrough
- **L75-79**: `bold(text)` — wraps text in ASS bold tags `{\b1}..{\b0}`.
- **L80-85**: `message(text, duration)` — displays an OSD message via `mp.osd_message`.
- **L86-91**: `append(a, b)` — appends all elements of table `b` into table `a` in-place.
- **L93-106**: `seconds_to_time_string(seconds, no_ms, full)` — converts seconds to HH:MM:SS.mmm format. Returns "unknown" for negative input. Conditionally includes hours (always if >3600 or `full=true`).
- **L108-113**: `seconds_to_path_element` — same but replaces `:` with `.` for safe filenames.
- **L115-121**: `file_exists(name)` — uses `utils.file_info`; returns bool.
- **L123-173**: `expand_properties(text, magic)` — expands `${prop}` / `${?prop:fallback}` / `${!prop:fallback}` / `${=prop}` / `${?prop==val:text}` templates using mpv properties. Recursive for nested values. Magic character defaults to `$`.
- **L175-239**: `format_filename(startTime, endTime, videoFormat)` — expands a template string using time/format substitutions. Supports `%F`, `%s`, `%e`, `%M`, `%T`, `%wH`/`%mH` etc. macro system.
- **L240-260**: `parse_directory(dir)` — expands `~` to home dir via `mp.command_native({expand-path})`. Returns absolute path.
- **L261-264**: `trim(s)` — removes leading/trailing whitespace.
- **L265-271**: `get_null_path()` — returns `/dev/null` or `NUL` on Windows.
- **L272-281**: `run_subprocess(params)` — wraps `utils.subprocess`; returns bool success.
- **L283-301**: `shell_escape(args)` — builds shell-quoted string from argv array. Single-quote style on POSIX, double-quote with `\"` on Windows. Wraps entire result in extra quotes on Windows.
- **L303-308**: `run_subprocess_popen(command_line)` — calls `shell_escape` then `io.popen` with `2>&1` appended. Returns file handle.
- **L310-314**: `calculate_scale_factor()` — returns `osd_height / 720` for UI scaling.
- **L316-321**: `should_display_progress()` — returns false on Windows if "auto"; else returns options value.
- **L323-333**: `reverse(list)` — returns a new reversed list (MoonScript list comprehension).
- **L335-337**: `get_pass_logfile_path(encode_out_path)` — appends `-video-pass1.log`.

## Inputs / Outputs
- **Inputs**: Various — seconds numbers, strings, tables, mpv properties.
- **Outputs**: Formatted strings, booleans, file handles, modified tables.

## Side Effects
- `message`: calls `mp.osd_message` — modifies OSD display.
- `run_subprocess`: calls `utils.subprocess` — may launch external process.
- `run_subprocess_popen`: calls `io.popen` — launches external process, returns open file descriptor.
- `parse_directory`: calls `mp.command_native` — queries mpv.

## Invariants
- `append` always returns the modified `a` table.
- `seconds_to_time_string` returns "unknown" for seconds < 0.
- `shell_escape` always produces a valid shell-quoted string for the target OS.

## Edge Cases
- **`shell_escape` / `run_subprocess_popen`**: `additional_flags` values containing spaces will be tokenized at whitespace (by the caller at L1790), not by shell_escape. Shell_escape only handles individual tokens.
- **`expand_properties`**: Recursive gsub can be called multiple times on the same template. Malformed templates with unclosed `}` may silently produce no substitution.
- **`format_filename`**: The `%M` macro uses `expand_properties` which calls mpv property system — could fail if no media loaded.
- **`seconds_to_time_string` with `full=true`**: Always includes hours, even for sub-hour clips (used in --start/--end arguments to mpv).
- **`run_subprocess_popen`**: The file descriptor must be closed by the caller or it leaks. `startEncode` does close it.

## mpv Interactions
- `mp.osd_message`: message()
- `mp.get_osd_size`: calculate_scale_factor()
- `mp.command_native({"expand-path", ...})`: parse_directory()
- `mp.get_property_osd`, `mp.get_property`: expand_properties()

## Security Notes
- `run_subprocess_popen` builds a shell string from user-controlled `additional_flags` values. If `additional_flags` contains shell metacharacters (`;`, `|`, `&`, backticks), they may execute arbitrary commands. `shell_escape` mitigates this for argv items but `additional_flags` is split by whitespace BEFORE shell_escape.
- `format_filename` calls `expand_properties` which calls `mp.get_property_osd` on user-defined template strings — potential property name injection.
