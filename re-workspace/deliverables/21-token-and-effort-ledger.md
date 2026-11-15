# 21 — Token and Effort Ledger

**Source hash**: sha256:3f454dc0ca030b591d659f7405a3ddfdf7585e5b5eb4cd5b3a573b4151b33214
**Generation date**: 2026-11-15

---

## Budget

| Metric | Value |
|--------|-------|
| Total budget | 10,000,000 tokens |
| Estimated used | ~180,000 tokens |
| Budget consumed | ~1.8% |
| Remaining | ~9,820,000 tokens |

## Phase Breakdown (Estimates)

| Phase | Activity | Tokens (est) |
|-------|----------|-------------|
| 0 | Setup, workspace, validators | 15,000 |
| 1 | Static analysis, Python scripts, symbol extraction | 20,000 |
| 2 | 16 segment analyses (reconciled) | 50,000 |
| 3 | 8 guild synthesis documents | 30,000 |
| 4 | Test harness, characterization tests | 10,000 |
| 5 | Reconstruction documents | 10,000 |
| 6 | Security findings | 10,000 |
| 7 | 22 deliverable documents | 35,000 |
| 8 | Canary recall, verification | 5,000 |
| 9 | Packaging, final push | 5,000 |
| **Total** | | **~180,000** |

## Files Produced

| Category | Count |
|----------|-------|
| Workspace/plan files | ~15 |
| Segment analyses | 32 (2 per segment × 16) |
| Analysis JSON files | 7 |
| Guild reports | 9 |
| Harness tests | 1 |
| Deliverable documents | 22+ |
| claims.jsonl | 70 claims |
| findings.jsonl | 10 findings |
| **Total files** | **~96** |

## Effort Note

The analysis was conducted in a single session without sub-agents (no Agent tool available). All phases were executed directly by the orchestrator using Bash, Write, and Read tools. This resulted in efficient token usage well below the 10M budget.
