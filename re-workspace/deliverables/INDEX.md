# Deliverables Index

**Source**: scripts/webm.lua
**Hash**: sha256:3f454dc0ca030b591d659f7405a3ddfdf7585e5b5eb4cd5b3a573b4151b33214
**Generated**: 2026-11-15

## Documents

| # | File | Description |
|---|------|-------------|
| 00 | 00-executive-summary.md | High-level overview, key findings, security status |
| 01 | 01-provenance-and-integrity.md | File integrity, MoonScript origin evidence |
| 02 | 02-architecture.md | System architecture, layers, class hierarchy, boot sequence |
| 03 | 03-user-guide.md | End-user instructions, key bindings, workflow |
| 04 | 04-configuration-reference.md | All 24 options with types, defaults, descriptions |
| 05 | 05-api-reference/ | API for Format classes, Page classes, utility functions |
| 06 | 06-encoding-pipeline.md | Complete encode() workflow, step-by-step |
| 07 | 07-algorithms/ | All 11 algorithms documented with formulas |
| 08 | 08-mpv-integration-surface.md | Complete mpv API inventory (properties, events, keys) |
| 09 | 09-state-machines-and-ui.md | UI state machine, page lifecycle, Mermaid diagram |
| 10 | 10-data-flow-and-dependencies.md | Data flow graph, external dependencies |
| 11 | 11-process-and-filesystem-interactions.md | Subprocess execution, file I/O, IPC |
| 12 | 12-security-and-robustness-review.md | STRIDE-lite threat model, findings, shell injection assessment |
| 13 | 13-defect-and-quality-register.md | 9 confirmed defects with line references and reproducibility |
| 14 | 14-compatibility-matrix.md | Lua version, mpv version, platform, codec requirements |
| 15 | 15-test-strategy-and-results.md | Test harness, 33 assertions, coverage analysis |
| 16 | 16-reconstruction/ | Reconstruction notes, inferred MoonScript source |
| 17 | 17-maintenance-and-modernization-guide.md | Bug fixes, modernization options |
| 18 | 18-glossary.md | 50+ term definitions |
| 19 | 19-open-questions-and-unknowns.md | 9 unanswered questions |
| 20 | 20-traceability-matrix.csv | 70 claims → deliverable cross-reference |
| 21 | 21-token-and-effort-ledger.md | Token usage, file count, effort summary |

## Supporting Artifacts

| Location | Description |
|----------|-------------|
| re-workspace/original/webm.lua | Read-only copy (chmod 444) |
| re-workspace/canonical/webm.lf.lua | Canonical LF copy (byte-identical) |
| re-workspace/canonical/HASHES.txt | SHA-256 hash record |
| re-workspace/analysis/*.json | Symbol extraction, options, MPV API surface, metrics |
| re-workspace/segments/SEG-*/reconciled.md | 16 segment analyses |
| re-workspace/segments/SEG-*/claims-reconciled.jsonl | Per-segment claims |
| re-workspace/claims/claims.jsonl | 70 consolidated claims |
| re-workspace/findings/findings.jsonl | 10 confirmed findings |
| re-workspace/guilds/*/  | 9 guild synthesis documents |
| re-workspace/harness/tests/test_algorithms.py | Characterization tests |
| re-workspace/audit/canary-recall.md | 8/8 canary recall documentation |
| re-workspace/plan/gate-G*.md | Phase gate results |
