# DECISIONS.md

## Decision Log

### D-001: Python-only static analysis
**Date**: 2026-11-15
**Context**: No Lua, luac, luacheck, mpv, or ffmpeg tools available in sandbox.
**Decision**: All static analysis performed via Python scripts using regex and state-machine parsing.
**Rationale**: Python 3.9.25 is available; Lua syntax is regular enough for regex-based extraction.
**Risk**: May miss subtle syntactic constructs. Mitigated by manual verification in analyst phases.

### D-002: Canonical file is identical to original
**Date**: 2026-11-15
**Context**: Original file is already LF-only (0 CRLF sequences).
**Decision**: canonical/webm.lf.lua is a byte-identical copy of original/webm.lua.
**Rationale**: No CRLF stripping needed; sha256 matches.

### D-003: Diagrams as Mermaid source only
**Date**: 2026-11-15
**Context**: No dot, mmdc, or pandoc available for rendering.
**Decision**: All diagrams delivered as Mermaid markdown source.
**Rationale**: Mermaid is renderable by GitHub and standard Markdown viewers.

### D-004: No runtime execution
**Date**: 2026-11-15
**Context**: mpv and ffmpeg absent; Lua interpreter absent.
**Decision**: Dynamic analysis limited to Python mock harness only.
**Rationale**: Cannot execute actual Lua code or mpv commands.
