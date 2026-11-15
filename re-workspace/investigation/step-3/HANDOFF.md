# Step 3 HANDOFF — Hypotheses

## Status: GATE PASSED — Three hypotheses with different root causes and concrete experiments.

| Hypothesis | Root Cause | Decisive Experiment |
|-----------|-----------|-------------------|
| A | Bare `cq-level=28` token → mpv treats it as file path → demux error → keep-open holds subprocess open | E4: remove bare token; expect no timeout |
| B | Missing `--no-config` → `keep-open=yes` inherited → subprocess stays open after encoding | E2: add `--keep-open=no`; expect no timeout |
| C | BOTH A and B are necessary: bare token + keep-open compound → indefinite hang; scripts loaded add further blocking | E6: combined fix removes both issues simultaneously |

## Key distinction between hypotheses
- **A** says `cq-level=28` bare token is THE cause; `keep-open` is secondary
- **B** says `keep-open=yes` inherited is THE cause; `cq-level=28` is secondary
- **C** says BOTH are required; neither alone is sufficient

## Note on testability
Real mpv is not available in this sandbox. All experiments will be run through the mock
harness with `execution_environment: mock`. Results will be static analysis of the
command arrays rather than actual execution outcomes.

## Cross-reference to Step 2 question
The question asks whether `cq-level=28` bare token COMBINED WITH `keep-open=yes` inherited
is the cause. Hypothesis C most directly addresses this. Hypotheses A and B test each
factor independently. If E4 and E2 both resolve the hang independently, then either
single fix is sufficient and C is partially refuted.
