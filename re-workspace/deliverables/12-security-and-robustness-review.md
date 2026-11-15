# 12 — Security and Robustness Review

**Source hash**: sha256:3f454dc0ca030b591d659f7405a3ddfdf7585e5b5eb4cd5b3a573b4151b33214
**Generation date**: 2026-11-15

**ALERT STATUS**: CLEAR — no malware or malicious behavior detected.

---

## Security Findings

### HIGH: IPC Handler No Validation (FIND-006)

**Location**: L68-74
**Description**: `test_set_options(new_options_json)` accepts any JSON blob via the `mpv-webm-set-options` script message and merges all keys into the global `options` table without type checking, range validation, or key whitelisting.

**Impact**: Any mpv script or external process with IPC access can:
- Override `additional_flags` to redirect output or add harmful flags.
- Override `output_directory` to write files to arbitrary locations.
- Override `run_detached` to change execution mode.
- Inject arbitrary keys into the options table.

**Mitigation**: This is an IPC authentication/validation issue. For typical standalone use where only trusted scripts have IPC access, severity is LOW. In environments with multiple untrusted scripts, severity is HIGH.

**Evidence**: `for k, v in pairs(new_options) do options[k] = v end` — no validation.

---

### MEDIUM: Output Path Override via additional_flags (FIND-004)

**Location**: L1790-1796
**Description**: `additional_flags` values are tokenized by whitespace and appended to the mpv command. A flag like `--o=/tmp/evil` in `additional_flags` overrides the computed output path.

**Impact**: User-controlled additional_flags can redirect output to arbitrary paths. Combined with IPC override (FIND-006), an attacker can direct encoded output to any writable location.

---

### LOW: Output Directory Path Traversal

**Location**: L1810-1811
**Description**: `options.output_directory` is not sanitized for path traversal sequences (`../`).
**Impact**: Output files could theoretically be written outside the intended directory. Limited by filesystem permissions.

---

### LOW: Predictable Temp File Name

**Location**: L1682
**Description**: HLS cache dump always uses `~/cache_dump.ts` — a predictable, fixed filename.
**Impact**: Symlink attacks possible on multi-user systems. Race condition on repeated encodes.

---

## Defect-Related Robustness Issues

| ID | Severity | Description |
|----|----------|-------------|
| FIND-001 | HIGH | Undefined 'bitrate' var crashes strict mode |
| FIND-002 | HIGH | formats['raw'] nil crashes EncodeOptionsPage |
| FIND-003 | MEDIUM | output_format default crashes encode() |
| FIND-007 | MEDIUM | Temp file/logfile leaked when run_detached=true |
| FIND-010 | MEDIUM | PreviewPage property capture timing issue |

## Shell Injection Assessment

**Conclusion: SAFE.** `run_subprocess_popen` uses `shell_escape()` which single-quote-wraps each individual token. Shell metacharacters within tokens are contained. The only bypass would require injecting a token with a space (which is the tokenization delimiter), which would split the injection across two safely-quoted tokens.

## No Obfuscation

All code is readable transpiled Lua. No base64-encoded payloads, no eval() equivalents, no dynamic code loading.
