# Execution Plan

Generated: 2026-11-15

## Overview

Swarm-based reverse engineering of `scripts/webm.lua` (82074 bytes, 2856 lines).
Target: produce comprehensive documentation suite (deliverables 00-21).

## Constraints

- Token budget: 10,000,000 total
- No Lua/mpv/ffmpeg tooling available; Python-only static analysis
- All outputs under `re-workspace/`
- Final push to `SevWren/MPV` repo

## Wave Schedule

### Wave 1 — Phase 0: Mobilization (Orchestrator only)
- Create workspace dirs
- Copy and hash-lock original
- Capability probe
- Write validators, self-test
- Write execution plan, STATE.json
- **Gate G0**

### Wave 2 — Phase 1: Deterministic Static Baseline (Orchestrator + Python scripts)
- Python-based Lua parser: symbols, globals, strings, line index
- mpv API surface extraction
- Options table extraction
- Metrics per function
- Segment boundary verification
- Transpiler hypothesis assessment
- **Gate G1**

### Wave 3 — Phase 2: Segment Analysis (16 segments x 3 analysts = 48 analyst agents + 16 reconcilers)
- SEG-00 through SEG-07: batch A (8 segments, 3 analysts each in parallel)
- SEG-08 through SEG-15: batch B (8 segments, 3 analysts each in parallel)
- Reconcilers run after each batch
- **Gate G2**

### Wave 4 — Phase 3: Guild Synthesis (8 guilds in parallel)
- Architecture, mpv-Surface, Encoding Pipeline, UI/State, Options, Algorithms, Cross-platform, Error Handling
- **Gate G3**

### Wave 5 — Phase 4: Dynamic Harness (Orchestrator builds harness)
- Mock mpv in Python
- Characterization tests
- **Gate G4**

### Wave 6 — Phase 5: Reconstruction (1 agent)
- Class diagram, call graph, state machines, sequence diagrams, data dictionary
- **Gate G5**

### Wave 7 — Phase 6: Security Review (1 agent)
- STRIDE-lite threat model
- **Gate G6**

### Wave 8 — Phase 7: Documentation Authoring (parallel doc agents)
- 22 deliverable documents
- **Gate G7**

### Wave 9 — Phase 8: Verification (1 agent)
- Canary recall, claim verification, cold-start sufficiency
- **Gate G8**

### Wave 10 — Phase 9: Packaging and Push (Orchestrator)
- INDEX.md, HANDOFF.md, MANIFEST.sha256
- git commit + push
- **Gate G9**

## Budget Allocation

| Phase | Estimated Tokens | Cumulative |
|-------|-----------------|------------|
| 0 | 10,000 | 10,000 |
| 1 | 50,000 | 60,000 |
| 2 | 2,000,000 | 2,060,000 |
| 3 | 1,500,000 | 3,560,000 |
| 4 | 300,000 | 3,860,000 |
| 5 | 300,000 | 4,160,000 |
| 6 | 200,000 | 4,360,000 |
| 7 | 1,500,000 | 5,860,000 |
| 8 | 500,000 | 6,360,000 |
| 9 | 50,000 | 6,410,000 |

Estimated total: ~6.4M tokens (64% of budget), leaving 36% headroom.

## Circuit Breaker Actions

- 60% (6M): Write plan/budget-health.md
- 85% (8.5M): Freeze new analysis
- 95% (9.5M): Emergency finalize
