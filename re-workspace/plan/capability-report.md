# Capability Report

Generated: 2026-11-15

## Available Tools

| Tool | Status | Path | Version |
|------|--------|------|---------|
| lua | MISSING | - | - |
| luajit | MISSING | - | - |
| luac | MISSING | - | - |
| luacheck | MISSING | - | - |
| mpv | MISSING | - | - |
| ffmpeg | MISSING | - | - |
| ffprobe | MISSING | - | - |
| moonc | MISSING | - | - |
| dot (graphviz) | MISSING | - | - |
| mmdc (mermaid-cli) | MISSING | - | - |
| pandoc | MISSING | - | - |
| git | FOUND | /opt/git/bin/git | 2.49.0 |
| python3 | FOUND | /usr/bin/python3 | 3.9.25 |
| jq | FOUND | /usr/bin/jq | jq-1.8.1 |
| sha256sum | FOUND | /usr/bin/sha256sum | GNU coreutils 8.32 |

## Impact Assessment

- **Lua tooling absent**: No luac syntax check possible. No luacheck linting. All static analysis must be done via Python text/AST parsing.
- **mpv absent**: No runtime execution. Dynamic analysis must use mock harness only.
- **ffmpeg/ffprobe absent**: No command-line validation. Command templates analyzed statically.
- **moonc absent**: Cannot transpile back to MoonScript; transpiler hypothesis must be evaluated from code patterns alone.
- **Diagram tools absent**: Mermaid diagrams written as text; graphviz dot graphs written as source; rendering not possible in sandbox.
- **pandoc absent**: Documentation output in Markdown only.
- **Python 3.9.25**: Available for all analysis scripts.
- **git 2.49.0**: Available for final commit/push.
- **jq 1.8.1**: Available for JSON processing.
- **sha256sum**: Available for integrity verification.

## Mitigations

1. Python-based Lua parser (regex + state machine) will substitute for luac/luacheck.
2. Mock mpv harness in Python will substitute for runtime testing.
3. All diagrams delivered as Mermaid source (renderable by any Mermaid-compatible viewer).
