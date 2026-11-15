# 13 — Defect and Quality Register

**Source hash**: sha256:3f454dc0ca030b591d659f7405a3ddfdf7585e5b5eb4cd5b3a573b4151b33214
**Generation date**: 2026-11-15

---

## Confirmed Defects

| ID | Severity | Lines | Title | Reproducible |
|----|----------|-------|-------|-------------|
| FIND-001 | HIGH | L1779-1780 | Undefined 'bitrate' in strict mode | Yes (strict_filesize_constraint=true) |
| FIND-002 | HIGH | L2363-2385 | formats['raw'] nil crash | Yes (press 'o' to open options) |
| FIND-003 | MEDIUM | L17, L1698 | output_format default mismatch | Yes (first encode without opening options) |
| FIND-004 | LOW | L620 | get_duration undefined variable | No (not called in normal flow) |
| FIND-005 | LOW | L1365-1366 | startEncode empty table append | No (no-op, harmless) |
| FIND-007 | MEDIUM | L1856-1860 | Temp file/logfile leak on detached | Yes (run_detached=true, HLS or 2-pass) |
| FIND-008 | LOW | L15 | strict_bitrate_multiplier unused | No (silent dead code) |
| FIND-009 | LOW | L1790-1792 | additional_flags space tokenization | Yes (flags with space in value) |
| FIND-010 | MEDIUM | L2591-2611 | PreviewPage property capture timing | Yes (edge case timing) |

## Critical Path Analysis

**FIND-002** is triggered by the primary user workflow ('o' key → EncodeOptionsPage → instantiation crash). This is a HIGH-impact bug that prevents the options UI from working entirely.

**FIND-003** may be masked by FIND-002: if the options UI crashes, the user never confirms a valid output_format, and the default "mp4 (h264/AAC)" is used for encode(), causing a second crash.

**FIND-001** requires explicitly enabling strict_filesize_constraint, which is non-default.

## Code Quality Observations

1. **Dead option**: `strict_bitrate_multiplier` is documented and configurable but never used (L15).
2. **Commented-out code**: `--append_property(ret, "sub-ass-force-style")` at L1566 — may be intentional or oversight.
3. **MoonScript artifacts**: Several patterns (empty table append, vestigial no-ops) appear to be MoonScript transpilation artifacts.
4. **Global function leak**: `base64_encode` and `base64_decode` are global, potentially conflicting with other scripts.
5. **No error recovery**: No pcall/xpcall wrappers; any Lua error propagates to mpv.
6. **Inconsistent return values**: Some functions return bool success, some return nil on error, some crash.

## Potential Issues Not Confirmed (Unknown)

- Whether `formats["raw"]` crash was recently introduced or has always been present (Unknown — no git history analyzed).
- Whether the `bitrate` variable bug in strict mode has ever worked (Unknown — may be a regression).
- Whether `get_duration` was ever functional (Unknown — the bug may have been introduced during refactoring).
