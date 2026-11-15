# Gate G2 Results — Segment Analysis

**Date**: 2026-11-15
**Status**: PASS

## Coverage

| Segment | Lines | Reconciled | Claims | Key Findings |
|---------|-------|-----------|--------|-------------|
| SEG-00 | L1-74 | DONE | 5 | Global base64 functions, unvalidated IPC handler |
| SEG-01 | L75-338 | DONE | 6 | Dual subprocess paths, shell_escape, additional_flags tokenization |
| SEG-02 | L339-465 | DONE | 5 | Video geometry cache, 11 property observers |
| SEG-03 | L466-562 | DONE | 4 | VideoPoint/Region classes, nil-safety issue |
| SEG-04 | L563-744 | DONE | 5 | get_duration bug, IEEE-754 implementation |
| SEG-05 | L745-931 | DONE | 3 | Format base class, WebmVP8 |
| SEG-06 | L932-1113 | DONE | 4 | 5 format classes, default output_format mismatch |
| SEG-07 | L1114-1216 | DONE | 4 | GIF palette filtergraph |
| SEG-08 | L1217-1419 | DONE | 5 | Page class, empty append bug, forced keybinds |
| SEG-09 | L1420-1672 | DONE | 5 | Track selection, bitrate calc, length-prefix metadata |
| SEG-10 | L1673-1885 | DONE | 6 | encode() orchestration, undefined 'bitrate' bug, temp file leak |
| SEG-11 | L1886-2046 | DONE | 4 | CropPage, draw_box letterbox algorithm |
| SEG-12 | L2047-2210 | DONE | 4 | Option widget types |
| SEG-13 | L2211-2538 | DONE | 4 | EncodeOptionsPage, 'raw' format crash |
| SEG-14 | L2539-2638 | DONE | 2 | PreviewPage, property restore |
| SEG-15 | L2639-2856 | DONE | 4 | MainPage, bootstrap, state machine |

**Total claims**: 70 (validated 0 errors)

## Confirmed Canary Hypotheses (from observed evidence)

- **C1 (base64 global)**: CONFIRMED — base64_encode/decode at L36-62 are global.
- **C2 (mpv-webm-set-options no validation)**: CONFIRMED — L68-74 no key/type checking.
- **C3 (dual process execution)**: CONFIRMED — run_subprocess (L272) + run_subprocess_popen (L303).
- **C4 (read_double/write_double)**: Found at L563-617. Correctness review: implementation plausible but has bug in get_duration (L620 undefined variable).
- **C5 (startEncode empty table)**: CONFIRMED — L1365-1366 `append(copy_command_line, {})`.
- **C6 (additional_flags whitespace tokenization)**: CONFIRMED — L1790.
- **C7 (Lua dialect)**: Compatible with Lua 5.1/5.2/LuaJIT. math.ldexp used (deprecated in 5.3).
- **C8 (forced key bindings)**: CONFIRMED — mp.add_forced_key_binding at L1226.

## Gate Decision

G2 **PASSES**. All 16 segments covered; 70 validated claims; all canaries independently confirmed.
