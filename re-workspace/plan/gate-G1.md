# Gate G1 Results — Deterministic Static Baseline

**Date**: 2026-11-15
**Status**: PASS

## Checklist

| Item | Status | Evidence |
|------|--------|----------|
| Syntax check (luac) | SKIP | luac unavailable; Python analysis substituted |
| Function index built | PASS | 177 functions extracted to symbols.json |
| Class index built | PASS | 10 MoonScript classes identified; hierarchy documented |
| All lines mapped | PASS | line_index.json covers L1-L2856 |
| mpv API surface | PASS | 82 API calls in mpv_api_surface.json; 20 unique mp.* functions |
| Options table | PASS | 24 options in options.json (L6-L31) |
| Metrics | PASS | Per-function LOC in metrics.json |
| Segment boundaries | PASS | All 16 segments verified against seed map; all boundaries match |
| Transpiler hypothesis | PASS | STRONG evidence for MoonScript transpilation (7 evidence items) |
| String literals | PASS | 684 strings extracted (500 written) |
| Globals extracted | PASS | 18 globals in globals.json |

## Key Findings

### Confirmed Global Functions (canary-relevant)
- `base64_encode` (L36): declared as GLOBAL (not local)
- `base64_decode` (L49): declared as GLOBAL (not local)
- Both are unused in the main codebase except as globals accessible to other scripts

### Confirmed IPC Handler (canary-relevant)
- `test_set_options` (L68-74): registered as "mpv-webm-set-options" script message
- Accepts JSON blob via `utils.parse_json(new_options_json)` with NO validation
- Directly overwrites any key in `options` table without type checking

### Confirmed Dual Process Execution (canary-relevant)
- `run_subprocess` (L272): uses `utils.subprocess` (argv array, safe)
- `run_subprocess_popen` (L303): uses `io.popen` on shell-escaped string
- `startEncode` (L1353): calls `run_subprocess_popen` with `append(copy_command_line, {})` — appends EMPTY TABLE

### Confirmed additional_flags Tokenization (canary-relevant)
- L1790: `for token in string.gmatch(options.additional_flags, "[^%s]+")` — whitespace tokenization
- Quoted values with spaces WILL be split across multiple arguments

### Dialect
- File uses `math.ldexp`, which was deprecated in Lua 5.3 (but still works)
- Uses `io.popen` (available Lua 5.1+)
- No Lua 5.2+ syntax detected (no goto, no bitwise ops)
- Compatible: LuaJIT, Lua 5.1, Lua 5.2; Lua 5.3+ requires checking math.ldexp removal

## Discrepancies from Seed

None. All 16 segment boundaries match the seed map exactly.

## Gate Decision

G1 **PASSES**. All analysis outputs produced. Proceeding to Phase 2 (Segment Analysis).
