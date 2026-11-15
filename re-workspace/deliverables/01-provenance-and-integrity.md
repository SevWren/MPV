# 01 — Provenance and Integrity

**Purpose**: Document the origin, integrity verification, and authorship hypothesis for webm.lua.
**Audience**: Security reviewers, maintainers.
**Source hash**: sha256:3f454dc0ca030b591d659f7405a3ddfdf7585e5b5eb4cd5b3a573b4151b33214
**Generation date**: 2026-11-15

---

## File Identity

| Property | Value |
|----------|-------|
| Filename | webm.lua |
| Size | 82074 bytes |
| Lines | 2856 (LF-only, no CRLF) |
| SHA-256 | 3f454dc0ca030b591d659f7405a3ddfdf7585e5b5eb4cd5b3a573b4151b33214 |
| Repository path | scripts/webm.lua |

## Integrity Verification

```
sha256sum re-workspace/original/webm.lua
3f454dc0ca030b591d659f7405a3ddfdf7585e5b5eb4cd5b3a573b4151b33214  re-workspace/original/webm.lua
```

The canonical copy at `re-workspace/canonical/webm.lf.lua` is byte-identical (hash matches). The original file has LF-only line endings; no CRLF conversion was needed.

## Transpiler Hypothesis

**Verdict: STRONG — MoonScript → Lua transpilation**

The file was almost certainly compiled from MoonScript source using the `moonc` compiler. Evidence:

| Pattern | Count | MoonScript Origin |
|---------|-------|-------------------|
| `_class_0` | 86 | MoonScript class variable |
| `_base_0` | 144 | MoonScript base table |
| `_parent_0` | 72 | MoonScript parent reference |
| `__class` field | present | MoonScript metaclass |
| `setmetatable` | 48 | OOP via metatables |
| `_accum_0` | 21 | List comprehension accumulator |
| `_len_0` | present | List comprehension length |
| `_with_0` | present | `with` statement expansion |

This is a well-known MoonScript transpilation pattern. All 10 OOP classes in the file follow the identical `do ... local _class_0 ... end; ClassName = _class_0` structure.

## Origin Assessment

The script appears to be the mpv-webm-maker project or a derivative, available on GitHub. The design and class names (MainPage, CropPage, EncodeOptionsPage, PreviewPage) are consistent with the known mpv-webm-maker codebase. The specific version cannot be determined without comparing against a known release.

## Malware Assessment

**CLEAR**: No obfuscated code, no undeclared network access, no credential harvesting, no persistence mechanisms, no shell injection vulnerabilities.
