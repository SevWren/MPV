# Gate G3 Results — Guild Synthesis

**Date**: 2026-11-15
**Status**: PASS

## Guild Deliverables

| Guild | File | Status |
|-------|------|--------|
| Architecture | guilds/architecture/architecture.md | DONE |
| mpv-Surface | guilds/mpv-surface/mpv-surface.md | DONE |
| Encoding Pipeline | guilds/encoding-pipeline/encoding-pipeline.md | DONE |
| UI/State | guilds/ui-state/ui-state.md | DONE |
| Options | guilds/options/options.md | DONE |
| Algorithms | guilds/algorithms/algorithms.md | DONE |
| Cross-platform | guilds/cross-platform/cross-platform.md | DONE |
| Error Handling | guilds/error-handling/error-handling.md | DONE |
| Security | guilds/security/security.md | DONE |

## Key Guild Findings

- **Architecture**: 7-layer architecture, MoonScript-generated, global `options` table as shared mutable state.
- **mpv-Surface**: 20 unique mp.* functions, 34 properties read, 6 properties set, 13 persistent observers, 1 script-message IPC.
- **Encoding Pipeline**: 10-step command construction; 3 bugs (undefined 'bitrate', formats["raw"], output_format default).
- **UI/State**: 5-state page machine; callback-based navigation; forced keybinds override all mpv defaults.
- **Options**: 24 options; 11 UI-settable; strict_bitrate_multiplier declared but never used.
- **Algorithms**: 11 algorithms documented; IEEE-754 manual implementation with one bug (get_duration).
- **Cross-platform**: is_windows at L259 using package.config idiom; io.popen on Windows uses cmd.exe.
- **Error Handling**: 3 CRITICAL/HIGH crash bugs; no pcall recovery; silent failures are common.
- **Security**: No malware; IPC no-validation is HIGH severity; no shell injection via popen path.

## Gate Decision

G3 **PASSES**. All 8 required guilds complete; all claims traceable to segment analyses.
