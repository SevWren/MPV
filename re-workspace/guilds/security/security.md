# Security Guild Report

## Trust Boundaries

```
[mpv process] ← script-opts config (filesystem)
     |
[webm.lua] ← script-message IPC (local socket/pipe)
     |
     ├── [Media file path] (filesystem: media-derived string)
     ├── [output_directory] (filesystem: user config)
     ├── [output_template] (config: property expansion)
     ├── [additional_flags] (config: appended to command)
     └── [ffmpeg subprocess] (child process)
```

## STRIDE-Lite Threat Analysis

### (a) Script-Message IPC: mpv-webm-set-options

**Threat**: Any script/process with access to mpv's IPC socket can send:
```
mpv-webm-set-options {"additional_flags": "--o=/etc/evil; rm -rf ~"}
```

**Impact**:
- **Spoofing/Tampering**: Can overwrite any options key including `additional_flags`, `output_directory`, `output_template`.
- **No authentication**: Any process on the same machine with IPC access can inject options.
- **No validation**: String values accepted without type or range checks.

**Severity**: HIGH if mpv IPC socket is exposed; MEDIUM for typical local use.

**Evidence**: L68-74 — `for k, v in pairs(new_options) do options[k] = v end`.

### (b) Script-Opts Config File

**Threat**: User edits `~/.config/mpv/script-opts/webm.conf` with malicious values.

**Impact**:
- `additional_flags=--o=/path/to/override` → redirects output file.
- `output_directory=../../etc` → path traversal for output.
- `output_template=%{=run:malicious_command}` → property expansion may execute if mpv supports run: prefix (unclear — depends on mpv version).

**Severity**: LOW — requires attacker to have write access to config files (local attacker only).

### (c) Media-Derived Strings

**Threat**: Malicious media file with crafted metadata (filename, title, etc.).

**Impact**:
- `format_filename` calls `expand_properties` which calls `mp.get_property_osd` on format template.
- `output_template = "%F-[%s-%e]%M"` — `%F` is filename without extension.
- If filename contains shell metacharacters (`;`, `|`, backticks), they flow into:
  - `out_path` passed to `--o=` flag: safe (mpv handles via argv).
  - `run_subprocess_popen`: `shell_escape` is applied, which should quote the args safely.
- BUT: `additional_flags` is NOT escaped before passing to the shell string — it goes through whitespace tokenization only.

**Severity**: LOW for normal use; MEDIUM if user enables additional_flags with attacker-controlled values.

### (d) User-Typed Values in Options UI

**Threat**: Values entered/selected via EncodeOptionsPage.

**Impact**:
- Options are constrained by Option widget (type/range). No free-text input exists in the UI.
- target_filesize is int with min=0, so cannot be set to negative or string.
- **No injection risk through the UI.**

**Severity**: NONE.

### (e) Output Directory and Temp/Log Files

**Threat**: TOCTOU race on output directory; predictable temp file names.

**Impact**:
- `cache_dump.ts` is always written to `~` with a fixed name — symlink attack possible if attacker controls `~`.
- Pass1 logfile: `out_path + "-video-pass1.log"` — fixed name, same directory as output.
- If `run_detached=true`, logfile and temp file are NEVER cleaned up.

**Severity**: LOW — theoretical local race conditions.

## Command Injection Assessment

### run_subprocess (L272-281)
Uses `mp.utils.subprocess(params)` where params is `{args=table}`. The `args` table is passed directly as argv — **NO shell injection risk**.

### run_subprocess_popen (L303-308)
Uses `io.popen(shell_escape(argv) .. " 2>&1")`. Shell escaping is applied via `shell_escape()`. The escaping appears correct for POSIX (single-quote with `'\''` inner quote replacement). However:
- If `additional_flags` contains a value like `--vf-add='; malicious_command; true'`, it would be tokenized to tokens: `["--vf-add='` and `malicious_command;` and `true'"]` — the split creates unquoted fragments.
- After tokenization, shell_escape quotes each fragment individually. `"malicious_command;"` would be quoted as `'malicious_command;'` — the semicolon is INSIDE quotes, so safe.

**Conclusion**: `additional_flags` with shell metacharacters is SAFE from injection because each whitespace-delimited token is individually quoted by shell_escape.

**HOWEVER**: A flag like `--o=/tmp/x` in additional_flags (which contains no shell-special chars) would override the `--o=` output path set by the script without shell injection.

## Security Summary

| Finding | Severity | Evidence |
|---------|----------|---------|
| IPC set-options no validation | HIGH | L68-74 |
| additional_flags can override --o= output path | MEDIUM | L1790-1796 |
| output_directory path traversal | LOW | L1810-1811 |
| cache_dump.ts fixed filename | LOW | L1682 |
| run_detached temp file leak | LOW | L1856-1860 |
| No shell injection in popen path | SAFE | L283-308 |
| UI options have no injection risk | SAFE | SEG-13 |

## No Obfuscated Payloads

No obfuscated code, undeclared network access, credential harvesting, or malware behavior was detected. The base64 functions are utilities for data encoding, not for obfuscation.
