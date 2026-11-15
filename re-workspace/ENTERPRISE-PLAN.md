# ENTERPRISE PLAN: MPV webm.lua — Full Resolution via 30-Team Adversarial Swarm

**Version**: 1.0
**Date**: 2026-11-15
**Scope**: Complete resolution of all remaining FIND-* defects, architecture gaps, documentation gaps, testing gaps, and infrastructure gaps in `/home/vercel-sandbox/MPV/scripts/webm.lua`.
**Classification**: Enterprise Engineering Plan

---

## Executive Summary

This plan describes a 30-team, 20+-agent-per-team swarm that resolves ALL remaining issues in the MPV/webm.lua project. Every design assumption includes the possibility that any agent will lie, hallucinate, or produce plausible-but-wrong output. No claim advances past "unverified" until an independent adversarial team re-derives it from source. Majority vote never decides anything — only evidence does.

The plan is organized into five clusters (A–E), an agentic loop with explicit phase gates, a verification matrix for every FIND-* item, an enterprise standards compliance checklist, and a deliverables checklist. The loop terminates only when all five exit conditions are simultaneously true.

---

## Part 1: Organizational Structure (30 Teams)

### Cluster A — Bug Resolution Teams (Teams 1–10)

**Mission**: Resolve all remaining confirmed defects. Every fix must be traceable to a source line, a test, and a FIND-* ID.

---

#### Team 1 — FIND-005: Vestigial Empty Table Append (20 agents)

**Bug**: In `startEncode`, there is an empty table append (`table.insert(args, {})` or equivalent MoonScript artifact) that is harmless but represents dead code and a code quality violation.

**Agent Roles**:
- 2 x Source Locator agents: independently identify the exact line(s) in webm.lua
- 2 x Root Cause agents: independently determine whether this is a MoonScript transpilation artifact or an intentional no-op
- 2 x Fix Design agents: independently produce minimal removal patches
- 4 x Fix Verification agents: each reads the patched source and confirms the empty append is gone and no adjacent logic was disturbed
- 2 x Regression agents: each runs the Python static analysis suite before and after the patch and confirms no test regressions
- 2 x Claims agents: write entries in `claims.jsonl` with status "unverified"
- 4 x Documentation agents: update inline comments to explain the removal
- 2 x Handoff agents: produce a structured summary for Team 6 (adversarial reviewer)

**Exit criteria**: Fix applied, all 4 Fix Verification agents agree, regression suite passes, claims written.

---

#### Team 2 — FIND-008: Dead Option strict_bitrate_multiplier (20 agents)

**Bug**: `strict_bitrate_multiplier` is declared in the options table (L15) and documented in webm.conf examples, but is never referenced in encode logic. It misleads users who set it expecting an effect.

**Agent Roles**:
- 2 x Source Locator agents: independently confirm all references to `strict_bitrate_multiplier` in webm.lua
- 2 x Impact Assessment agents: independently determine whether removing vs. implementing the option is the correct resolution
- 2 x Design Choice agents: produce options (a) remove and document removal, (b) implement the intended behavior if it can be inferred from context
- 4 x Design Adjudication agents: vote by evidence on which option is safer (must produce evidence, not opinion)
- 2 x Fix Implementation agents: implement the winning option
- 2 x Fix Verification agents: confirm the fix
- 2 x Regression agents: run full test suite
- 2 x Claims agents: write to `claims.jsonl`

**Exit criteria**: Fix applied, design decision documented, test suite passes, claims written.

---

#### Team 3 — FIND-009: additional_flags Space Tokenization Deep Analysis (20 agents)

**Bug**: `additional_flags` is split on whitespace, breaking values that contain spaces (e.g., `--metadata title="My Video"`). Prefix validation was added but the underlying tokenizer is unfixable without full quoting support.

**Agent Roles**:
- 2 x Threat Modeler agents: enumerate all hostile inputs (embedded spaces, embedded quotes, shell metacharacters, Unicode, null bytes)
- 2 x Existing Defense Auditor agents: independently read the current prefix validation code and document exactly what it blocks and what it passes
- 2 x Gap Analysis agents: independently identify inputs that pass prefix validation but would still cause incorrect behavior
- 4 x Design agents: each produces a different hardening approach (a) reject any value containing a space unless quoted, (b) implement a minimal POSIX shell tokenizer, (c) change the interface to accept a JSON array, (d) add a documented limitation notice and strip dangerous metacharacters
- 2 x Design Adjudication agents: select the safest option that does not break backward compatibility for the common case
- 2 x Implementation agents: implement the selected option
- 2 x Test agents: add fuzz cases to `test_all_fixes.py` covering the new behavior
- 2 x Claims agents: write to `claims.jsonl`

**Exit criteria**: Hardening applied or limitation explicitly documented, fuzz tests added, claims written.

---

#### Team 4 — Forensic Finding Alpha: Format Registry nil Crash (20 agents)

**Mission**: The format registry seam identified in architecture analysis confirms a structural nil crash is possible if `formats[output_format]` is called with an unrecognized key. This is a NEW finding derived from forensic analysis. Assign FIND-013.

**Agent Roles**:
- 3 x Independent Source Readers: each reads the formats table and all call sites without communicating; each independently produces a list of all paths where nil can be returned
- 3 x Crash Reproducibility agents: each independently attempts to construct a Python test that proves the nil crash is reachable in patched code
- 2 x Fix Design agents: independently design a lookup() guard function
- 2 x Fix Implementation agents: implement the guard
- 4 x Adversarial Challenge agents: each tries to defeat the guard by constructing an input that bypasses it
- 2 x Regression agents: run full test suite
- 2 x Claims agents: write FIND-013 to `findings.jsonl` and `claims.jsonl`
- 2 x Handoff agents: brief Team 10

**Exit criteria**: FIND-013 documented, guard implemented, all 4 adversarial challenges fail to bypass, claims written.

---

#### Team 5 — Forensic Finding Beta: encode() Monolith Internal Defect Hunt (20 agents)

**Mission**: The 212-line `encode()` function contains at least two confirmed defects (FIND-001 and FIND-004 were inside it). This team performs a fresh forensic analysis of encode() to find any remaining latent defects. Assign new FIND-IDs to anything found.

**Agent Roles**:
- 5 x Independent Code Readers: each reads encode() independently and produces a list of all suspected issues with line numbers and reasoning
- 5 x Cross-Reference agents: each takes one reader's list and attempts to confirm or refute each item by reading adjacent code
- 2 x Synthesis agents: aggregate confirmed findings into a ranked list with proposed FIND-IDs
- 2 x Fix agents: apply fixes for any confirmed HIGH or MEDIUM findings
- 2 x Verification agents: confirm fixes applied correctly
- 2 x Regression agents: run full test suite
- 2 x Claims agents: write all new FIND-IDs to `findings.jsonl` and `claims.jsonl`

**Exit criteria**: encode() fully audited, all HIGH/MEDIUM findings fixed, new FIND-IDs documented, claims written.

---

#### Team 6 — Adversarial Review of Team 1 (FIND-005) (20 agents)

**Mission**: Assume Team 1's fix is wrong. Find the error.

**Adversarial Protocol**:
- Each agent independently reads Team 1's patch and the original source without reading Team 1's reasoning.
- Each agent independently re-derives: (a) the exact line(s) of the bug, (b) whether the fix removes the right thing, (c) whether any adjacent logic depends on the removed code.
- Agents do NOT collaborate until each has written their independent assessment.
- After independent assessment: agents compare. Any disagreement triggers a 3-agent Delphi subpanel.
- Delphi panel resolves by citing specific source lines, never by counting votes.

**Verdict options**:
- PASS: Fix is correct. All agents independently agree, with source citations.
- FAIL-WRONG-LINE: Fix touches the wrong line. Specific correct line cited.
- FAIL-INCOMPLETE: Fix removes the bug but leaves a related issue.
- FAIL-REGRESSION: Fix breaks adjacent logic. Specific line cited.

**Output**: Verdict written to `re-workspace/audit/adversarial-code-review.md` with full evidence chain.

---

#### Team 7 — Adversarial Review of Team 2 (FIND-008) (20 agents)

Same adversarial protocol as Team 6, applied to Team 2's fix for `strict_bitrate_multiplier`.

**Additional challenge**: Team 7 must independently determine whether the option has ever been used by any user by searching for any webm.conf documentation that references it and assessing whether removal is a breaking change.

---

#### Team 8 — Adversarial Review of Team 3 (FIND-009) (20 agents)

Same adversarial protocol as Team 6, applied to Team 3's hardening of `additional_flags`.

**Additional challenge**: Team 8 must run the Team 3 fuzz tests and attempt to construct an input that the new tests would miss but that could still cause misbehavior. If found, the case is added to the fuzz suite.

---

#### Team 9 — Adversarial Review of Team 4 (FIND-013: Format Registry) (20 agents)

Same adversarial protocol, applied to Team 4's lookup() guard.

**Additional challenge**: Team 9 must attempt to call lookup() with every string that appears anywhere in webm.lua as a potential output_format key and verify the guard handles all of them correctly.

---

#### Team 10 — Adversarial Review of Team 5 (encode() forensic audit) (20 agents)

Same adversarial protocol, applied to Team 5's forensic findings and fixes.

**Additional challenge**: Team 10 must independently audit encode() from scratch and produce its own findings list. Any discrepancy between Team 5's findings and Team 10's independent audit is treated as a potential lie from one or both teams and triggers full Delphi adjudication.

---

### Cluster B — Architecture Deepening Teams (Teams 11–17)

**Mission**: Address the structural format registry seam and the encode() monolith. Produce a deployable, adversarially-reviewed architectural improvement.

---

#### Team 11 — Format Registry Design A: Interface-First Lookup Contract (20 agents)

**Design mandate**: Design a `format_registry` module with a strict `lookup(key) -> FormatSpec | error` contract. The contract must:
- Never return nil — either return a valid FormatSpec or raise a structured error
- Be callable from any context in webm.lua without ambient state
- Support forward declaration (formats can be registered after the registry is created)

**Deliverables**:
- Interface specification (pseudo-code, language-agnostic)
- Mapping of all 12 existing formats to the new structure
- Risk analysis: what breaks if lookup() raises instead of returning nil

---

#### Team 12 — Format Registry Design B: Lazy Validation with Fallback (20 agents)

**Design mandate**: Design a format registry that validates at registration time, not at lookup time. Unknown keys at lookup time return a safe "unknown format" sentinel that causes encode() to abort gracefully with a user-visible error rather than a Lua nil crash.

**Deliverables**:
- Interface specification
- Sentinel value design
- Migration path from existing code

---

#### Team 13 — Format Registry Design C: Compile-Time Enumeration (20 agents)

**Design mandate**: Design a format system where all valid output_format values are enumerated at module load time and stored as a Lua enum-equivalent. Any code path that constructs an output_format string must reference the enum, making it impossible to pass an unregistered value at runtime.

**Deliverables**:
- Interface specification
- Impact analysis on options system (how does `output_format` get set from user config and IPC?)
- Backward compatibility assessment

---

#### Team 14 — Design Adjudicator (20 agents)

**Mission**: Read Designs A, B, and C without knowledge of which team produced each. For each design:
- List its strengths with specific source citations
- List its failure modes with specific scenarios
- Score it on: crash safety, testability, backward compatibility, implementation complexity

**Decision process**: Each of the 20 agents independently scores all three designs. Scores are compared. Any agent whose scoring diverges from the consensus by more than one rank must produce additional evidence. The winning design is the one with the best evidence-backed score, not the highest vote count.

**Output**: Design selection with full evidence chain in `re-workspace/audit/design-adjudication.md`.

---

#### Team 15 — Implementation Team Alpha (20 agents)

**Mission**: Implement the winning format registry design as a complete draft in a branch. The draft must be a full working implementation, not a skeleton.

**Anti-lying protocol**: Each implementation agent writes a subset of the code independently. No agent sees another's output until all subsets are complete. Integration is done by 2 dedicated Integration agents who resolve any conflicts by citing the winning design specification.

---

#### Team 16 — Implementation Team Beta (20 agents)

**Mission**: Implement the same winning design independently of Team 15. Teams 15 and 16 must NOT share code, variable names, or structure before both implementations are complete.

**Purpose**: If Teams 15 and 16 produce identical implementations, there is evidence they are copying rather than independently deriving. Structurally identical implementations with no independent derivation are treated as a potential coordinated lie and trigger re-implementation.

---

#### Team 17 — Adversarial Implementation Reviewer (20 agents)

**Mission**: Read both implementations (Team 15 and Team 16) independently. For each:
- Find any path where the winning design's contract is violated
- Find any path where nil can still escape the registry
- Find any regression relative to the existing format handling code

**Decision**: If Team 15's implementation is strictly better in all evidence-cited dimensions, it is selected. If Team 16 is strictly better, it is selected. If they are equal, merge the best-evidenced portions. If neither is acceptable, return both teams to re-implementation with specific documented failures.

---

### Cluster C — Testing and Verification Teams (Teams 18–24)

**Mission**: Produce a complete, adversarially-verified test suite that runs without a Lua runtime.

---

#### Team 18 — Static Analysis Test Suite (20 agents)

**Mission**: Write Python tests in `re-workspace/harness/tests/test_all_fixes.py` covering every FIND-* item. Tests must:
- Run without mpv, Lua, or any external binary
- Use only Python standard library + pytest
- Be deterministic (same result on every run)
- Each test must include a comment citing the FIND-* ID and source line(s) it verifies

**Coverage targets**:
- FIND-001: minrate/maxrate contain `video_bitrate` (not bare `bitrate`)
- FIND-003: `formats[default_output_format]` is not nil
- FIND-004: `reversed_binary_duration` absent from source
- FIND-006: IPC handler has `options[k] ~= nil` check
- FIND-007: `os.remove` precedes `subprocess_detached` in source order
- FIND-010: `originalProperties` assigned in `prepare()` not `__init`
- FIND-011: `cq-level=28` bare arg validation present
- FIND-012: `--no-config` precedes path in subprocess command array
- FIND-013: lookup() guard present and covers all call sites
- FIND-005: empty table append absent from startEncode
- FIND-008: `strict_bitrate_multiplier` handled per Team 2 decision

---

#### Team 19 — Mock Harness Expansion (20 agents)

**Mission**: Expand the existing mock harness to cover all encode() paths, including:
- Normal single-pass encode
- Two-pass encode (both pass 1 and pass 2)
- Detached subprocess encode
- HLS encode
- Strict filesize constraint path
- Error paths (file not found, subprocess fails, IPC timeout)

Each path must have a mock test that verifies the correct subprocess flags are present and in the correct order.

---

#### Team 20 — Fuzz Test Team (20 agents)

**Mission**: Write hostile input tests for:
- Filenames: null bytes, Unicode, path traversal (`../../../etc/passwd`), spaces, quotes, shell metacharacters
- JSON IPC payloads: oversized keys, unknown keys, type mismatches, nested objects where strings expected
- `additional_flags`: embedded spaces, embedded quotes, `--config` injection, `--load-scripts` injection, empty string, 10,000-character value

Each fuzz case must be a runnable pytest test that asserts the system rejects, sanitizes, or handles the input gracefully (no crash, no silent data corruption).

---

#### Team 21 — Regression Test Team (20 agents)

**Mission**: For each FIND-* item that has been fixed, write a test that:
1. Proves the bug EXISTS in the ORIGINAL (unpatched) source — the test must FAIL on the original
2. Proves the bug is ABSENT in the PATCHED source — the test must PASS on the patched version

This is the gold standard of regression testing: a test that cannot distinguish patched from unpatched code is worthless.

**Deliverables**: `re-workspace/harness/tests/test_regressions.py` with one test pair per FIND-* item.

---

#### Team 22 — Independent Test Verifier Alpha (20 agents)

**Mission**: Run the full test suite (`python3 -m pytest re-workspace/harness/tests/ -v`) in a clean environment. Record every test name, result (PASS/FAIL/ERROR), and any output. Write results to `re-workspace/audit/test-run-alpha.json`.

**Anti-lying protocol**: Each agent runs the suite independently and records results before seeing any other agent's results. All 20 results must agree. Any discrepancy is treated as an environment inconsistency or a flaky test, not a valid result, and triggers re-investigation.

---

#### Team 23 — Independent Test Verifier Beta (20 agents)

Same as Team 22, writing to `re-workspace/audit/test-run-beta.json`. Team 23 must not see Team 22's results before writing its own.

---

#### Team 24 — Independent Test Verifier Gamma (20 agents)

Same as Teams 22 and 23, writing to `re-workspace/audit/test-run-gamma.json`.

**Cross-team comparison**: After all three verifier teams complete, a 3-agent Comparison Panel reads all three result files and produces a discrepancy report. Any test that produces different results across teams is flagged as `DISPUTED` and triggers immediate re-investigation by a dedicated 5-agent Delphi panel. Only tests that pass in ALL THREE independent runs are marked `confirmed_pass`.

---

### Cluster D — Documentation Teams (Teams 25–28)

**Mission**: Bring all documentation to full parity with the patched and architecturally-improved codebase.

---

#### Team 25 — GLOSSARY.md Update (20 agents)

**Mission**: Read the current GLOSSARY.md and add entries for all new terms introduced by this session's fixes and design work, including:
- `format_registry` / `lookup()` (new architecture term)
- `subprocess isolation flags` (from FIND-012 / ADR-0007)
- `IPC trust boundary` (from FIND-006 / ADR-0008)
- `claims.jsonl` / `findings.jsonl` (verification infrastructure)
- `adversarial review` (methodology term)
- `Delphi panel` (methodology term)
- Any new FIND-IDs added by Teams 4 and 5

**Anti-lying protocol**: Two agents independently produce draft glossary entries. A third agent reads both drafts and the source code and confirms accuracy of each definition. Any definition that cannot be confirmed from source is marked `DISPUTED` and not included.

---

#### Team 26 — ADR Authoring (20 agents)

**Mission**: Write two new Architecture Decision Records:

**ADR-0007**: `docs/adr/ADR-0007-subprocess-isolation.md`
- Decision: subprocess isolation flags protocol
- Context: mpv subprocess inherits all of `~/.config/mpv/mpv.conf`
- Consequences: clean exit, moov atom written; trade-off vs. encoding-profiles.conf

**ADR-0008**: `docs/adr/ADR-0008-ipc-trust-boundary.md`
- Decision: IPC handler validates keys against known options table
- Context: original handler was permissive
- Consequences: unknown keys discarded; prevents option injection

Each ADR must be independently reviewed by 2 agents who have not read the original draft. The reviewers confirm accuracy against source code before the ADR is finalized.

---

#### Team 27 — API Reference Update (20 agents)

**Mission**: Update `docs/api-reference.md` (or create if absent) with entries for every function whose signature or behavior changed during this session:
- `encode()` — document all subprocess isolation flags now required
- `ipc_handler()` / `mpv-webm-set-options` handler — document validation behavior
- `lookup()` — document the new format registry contract
- `prepare()` — document `originalProperties` capture timing

Each entry must include: function signature, parameter descriptions, return value, error conditions, and source line reference.

---

#### Team 28 — User Guide Update (20 agents)

**Mission**: Update `README.md` or `docs/user-guide.md` with corrected webm.conf examples:
- Remove any example that uses `strict_bitrate_multiplier` (if Team 2 decides to remove it)
- Remove the broken `msg-level=webm=verbose` debug line from mpv.conf examples
- Update `additional_flags` examples to show the documented limitation for values with spaces
- Add a note about `encoding-profiles.conf` being bypassed due to subprocess isolation

---

### Cluster E — Audit and Closure Teams (Teams 29–30)

---

#### Team 29 — Independent Final Audit (20 agents)

**Mission**: Fresh context. No agent on Team 29 has read any output from Teams 1–28 before beginning.

**Protocol**:
1. Each agent independently reads `scripts/webm.lua` from scratch
2. Each agent independently re-derives 30 facts about the codebase (source lines, variable names, logic flow)
3. Each agent independently verifies each FIND-* item's fix status by reading the patched source
4. Each agent independently runs the test suite and records results
5. All 20 agents compare their independently-derived facts. Any fact where fewer than 18/20 agents agree is flagged for Delphi adjudication.

**Verdict**: PASS requires all of the following:
- 20/20 agents agree all FIND-* items are fixed in the patched source
- 20/20 agents agree the test suite passes 100%
- 0 disputed claims remaining in `claims.jsonl`
- All ADRs confirmed accurate against source

**Output**: `re-workspace/audit/final-audit-report.md` with full evidence chain.

---

#### Team 30 — GitHub Issue Management (20 agents)

**Mission**: After Team 29 produces a PASS verdict:

1. Read all open GitHub issues in the mpv-webm repository
2. For each issue that references a FIND-* item confirmed fixed: close the issue with a comment citing the fix commit hash and test name
3. For each remaining FIND-* item with status NOT `confirmed_fixed`: file a new issue with full reproduction steps and source line references
4. Update GitHub issue #2 with the final resolution summary from Team 29's audit report
5. Write a summary of all issue actions to `re-workspace/audit/github-issue-actions.md`

**Anti-lying protocol**: Two agents independently read the same GitHub issue and independently determine whether the referenced bug is fixed. Only if both agree is the issue closed. Any disagreement triggers a 3-agent Delphi panel.

---

## Part 2: Agentic Loop Design

The loop runs until ALL FIVE of these exit conditions are simultaneously true:

1. Every FIND-* item has status `confirmed_fixed` in `findings.jsonl`
2. Test suite passes 100% with no skips across all three independent verifier runs (Teams 22–24)
3. No `disputed` claims remain in `claims.jsonl`
4. The final audit team (Team 29) produced a PASS verdict
5. All GitHub issues referencing confirmed bugs are closed (Team 30 confirmed)

### Loop Iteration Structure

```
LOOP:

  Phase 1: Bug Resolution (Teams 1-5 in parallel)
    - Each team writes claims to claims.jsonl with status: "unverified"
    - Each team writes fix diffs to re-workspace/drafts/
    - Exit: all 5 teams report COMPLETE

  Phase 2: Adversarial Review (Teams 6-10 in parallel, review Phase 1 output)
    - Each adversarial team reads the fix independently
    - Each adversarial team writes a verdict to re-workspace/audit/adversarial-code-review.md
    - Exit: all 5 adversarial teams report verdict

  Phase 3: Verdict Adjudication
    IF any adversarial team returns FAIL:
      - Identify the specific failure reason (FAIL-WRONG-LINE, FAIL-INCOMPLETE, FAIL-REGRESSION)
      - Return the failing bug team to Phase 1 with the specific challenge appended to their brief
      - Only the failing team re-runs; teams with PASS verdicts do not re-run
    IF all adversarial teams return PASS:
      - Promote all fixes from claims.jsonl status "unverified" to "verified"
      - Apply fixes to scripts/webm.lua
      - Proceed to Phase 4

  Phase 4: Architecture Deepening (Teams 11-17 in sequence)
    - Team 11, 12, 13 run in parallel (design phase)
    - Team 14 runs after 11/12/13 complete (adjudication)
    - Teams 15 and 16 run in parallel after Team 14 completes (implementation)
    - Team 17 runs after Teams 15 and 16 complete (adversarial review)
    - Exit: Team 17 selects a winning implementation or returns both teams to re-implement

  Phase 5: Run Full Test Suite (Teams 18-21 build; Teams 22-24 verify)
    - Teams 18-21 run in parallel to build/expand test suite
    - Teams 22-24 run in parallel to independently execute the suite
    IF any test team (22-24) disagrees with another:
      - Comparison Panel identifies specific disagreeing test(s)
      - 5-agent Delphi panel investigates
      - Flaky tests are fixed; genuine disagreements trigger source re-investigation
    IF all three verifier teams agree:
      - Promote all test results to confirmed_pass in audit logs
      - Proceed to Phase 6

  Phase 6: Documentation (Teams 25-28 in parallel)
    - Exit: all 4 documentation teams report COMPLETE
    - 2-agent cross-review: each doc team's output reviewed by one agent from a different doc team

  Phase 7: Final Audit (Teams 29-30)
    - Team 29 runs first (audit)
    - Team 30 runs after Team 29 produces PASS verdict
    IF Team 29 verdict is FAIL:
      - Identify the specific gap (which FIND-* item, which claim, which test)
      - Return to Phase 1 with the gap appended to the scope
      - Increment loop counter
    IF Team 29 verdict is PASS AND Team 30 completes issue management:
      - Commit all changes to git with message referencing all resolved FIND-* IDs
      - Push to remote
      - EXIT LOOP

END LOOP
```

### Loop Termination Safeguard

If the loop counter exceeds 5 iterations without reaching EXIT:
- Escalate to a Human Review Panel
- Produce a report identifying which specific claim or fix is preventing convergence
- Do NOT continue looping indefinitely

### Anti-Lying Protocol (Applied at Every Step)

**Step 1**: Each team writes all claims in `claims.jsonl` using this structure:
```json
{
  "claim_id": "C-001",
  "find_id": "FIND-005",
  "team_id": "TEAM-1",
  "claim_text": "The empty table append at L1365 has been removed",
  "source_evidence": {"file": "scripts/webm.lua", "line": 1365, "text": "<actual line text>"},
  "status": "unverified",
  "timestamp": "2026-11-15T00:00:00Z"
}
```

**Step 2**: The adversarial team (Teams 6–10) reads the same source file independently and writes a counter-claim:
```json
{
  "claim_id": "C-001-VERIFY",
  "original_claim_id": "C-001",
  "adversarial_team_id": "TEAM-6",
  "agrees": true,
  "source_evidence": {"file": "scripts/webm.lua", "line": 1365, "text": "<independently read line text>"},
  "status": "verified"
}
```

**Step 3**: If `agrees: false`, a 3-agent Delphi panel is convened:
- Each Delphi agent reads the source independently
- Each Delphi agent writes their own finding
- The finding with the most source citations wins (never the finding with the most votes)
- If all three Delphi agents disagree, the claim is marked `IRRESOLVABLE` and escalated to human review

**Step 4**: Only claims where BOTH the original team AND the adversarial team write `agrees: true` with matching source evidence are promoted to `status: "confirmed"`.

---

## Part 3: Verification Methods

For each FIND-* item, the external verification method is a runnable Python test. All tests live in `re-workspace/harness/tests/`. The single external verification command is:

```bash
python3 -m pytest re-workspace/harness/tests/ -v
```

| FIND | Title | Verification Method | External Evidence Required |
|------|-------|--------------------|-----------------------------|
| FIND-001 | Undefined 'bitrate' in strict mode | Python regex: minrate/maxrate lines must contain `video_bitrate`, not bare `bitrate` | Static analysis of patched scripts/webm.lua |
| FIND-003 | output_format default mismatch | Python test: `formats[default_output_format]` resolves to a non-nil value | Static analysis: default value at L17 matches a key in the formats table |
| FIND-004 | get_duration undefined variable | Python string search: `reversed_binary_duration` must be ABSENT from scripts/webm.lua | String search confirms absence |
| FIND-005 | startEncode empty table append | Python test: `table.insert(args, {})` or equivalent MoonScript artifact absent from startEncode function body | String/AST search within startEncode scope |
| FIND-006 | IPC handler key injection | Python test: IPC handler contains `options[k] ~= nil` or equivalent allowlist check | Static analysis of handler function |
| FIND-007 | Temp file leak on detached | Python test: `os.remove` call precedes `subprocess_detached` call in source order within the same execution path | Line-order check in patched source |
| FIND-008 | strict_bitrate_multiplier dead option | Python test: either (a) `strict_bitrate_multiplier` is absent from the options table, or (b) it is referenced in encode logic (not just declared) | Static analysis confirms one of the two states |
| FIND-009 | additional_flags space tokenization | Python fuzz tests: inputs containing spaces, quotes, and metacharacters are either rejected or handled per documented behavior | Fuzz test suite in test_all_fixes.py |
| FIND-010 | PreviewPage property capture timing | Python test: `originalProperties` assignment appears within `prepare()` function body, not in `__init` | Static analysis of prepare() scope |
| FIND-011 | cq-level=28 bare arg validation | Python test: validation code that checks for `--` prefix before `cq-level` is present | Static analysis of validation logic |
| FIND-012 | Subprocess config isolation | Python test: `--no-config` appears before the input file path in the subprocess command array construction | Line-order check and array position check |
| FIND-013 | Format registry nil crash | Python test: a lookup() guard function exists and is called at all format access sites | Static analysis of all `formats[` call sites |

### Verification Independence Requirement

Each verification test must be written by a team that did NOT write the fix being verified. The test author must derive the expected behavior from the FIND-* description, not from reading the fix diff.

---

## Part 4: Enterprise Standards Checklist

### Code Quality

| Standard | Target | Verification |
|----------|--------|--------------|
| Zero bare `bitrate` references in subprocess flag construction | 0 occurrences of `bitrate` where `video_bitrate` is required | `grep -n '\bbitrate\b' scripts/webm.lua` returns no lines in encode() |
| Zero missing `--` prefixes in subprocess isolation | `--no-config`, `--load-scripts=no`, `--keep-open=no`, `--loop-playlist=no`, `--hwdec=no`, `--save-position-on-quit=no` all present | Python test confirms all 6 flags present before path |
| No dead options in options table | Every declared option is referenced in logic | Python test: every key in options table appears in at least one non-declaration reference |
| No vestigial no-ops | No MoonScript transpilation artifacts (empty table appends, etc.) | Python test: no `table.insert(args, {})` with empty table argument |

### Security

| Standard | Target | Verification |
|----------|--------|--------------|
| IPC handler validates against allowlist | Unknown keys logged and discarded | Python test: allowlist check present in handler |
| No arbitrary key injection via IPC | No path from IPC payload to `options[arbitrary_key] = arbitrary_value` | Static analysis confirms no bypass path |
| additional_flags sanitized | Dangerous metacharacters rejected or documented as unsupported | Fuzz test suite covers all metacharacter classes |

### Reliability

| Standard | Target | Verification |
|----------|--------|--------------|
| subprocess always receives isolation flags | All subprocess call sites include isolation flags | Python test: all subprocess construction paths include `--no-config` |
| Cleanup always runs before detach | `os.remove` precedes `subprocess_detached` on all code paths | Python line-order test |
| Format lookup never returns nil | lookup() guard wraps all format accesses | Static analysis confirms all `formats[` sites use the guard |

### Testability

| Standard | Target | Verification |
|----------|--------|--------------|
| All utility functions testable via Python mock harness | All pure functions can be called from Python test without mpv | Coverage report from mock harness |
| All subprocess construction paths covered by tests | Mock harness covers normal, two-pass, detached, HLS paths | Test coverage report |
| All fuzz cases covered | Hostile inputs for filenames, JSON, additional_flags | Fuzz test suite pass rate |

### Documentation

| Standard | Target | Verification |
|----------|--------|--------------|
| Every public function has line reference in API doc | No undocumented public function | API doc cross-reference check |
| Every architecture decision in an ADR | ADR-0001 through ADR-0008 all present | `ls docs/adr/` confirms 8 files |
| GLOSSARY.md current | All terms from fixes and architecture work defined | Manual review against FIND-* list |

### Traceability

| Standard | Target | Verification |
|----------|--------|--------------|
| Every fix traces to a FIND-* ID | No fix without a FIND-* reference | `findings.jsonl` contains entry for every fix |
| Every FIND-* traces to source lines | No finding without source line citations | All `findings.jsonl` entries have `source_line` field |
| Every FIND-* traces to a test | No finding without a test that proves the fix | `test_all_fixes.py` has at least one test per FIND-* ID |
| Every test traces to a FIND-* | No orphaned tests | All tests have `# FIND-NNN` comment |

---

## Part 5: Deliverables Checklist

For the plan to be COMPLETE, every item in this checklist must exist and pass its verification step.

### Code Deliverables

- [ ] `scripts/webm.lua` — all FIND-* fixes applied, adversarially reviewed by Teams 6–10, format registry guard from Team 17 applied
- [ ] `mpv.conf` — broken `msg-level=webm=verbose` debug lines removed

### Test Deliverables

- [ ] `re-workspace/harness/tests/test_all_fixes.py` — comprehensive static analysis tests, one test per FIND-* item, all tests pass
- [ ] `re-workspace/harness/tests/test_regressions.py` — regression tests proving each bug exists in unpatched code and is absent in patched code
- [ ] `re-workspace/harness/tests/run_all.sh` — single command to run all tests (`python3 -m pytest re-workspace/harness/tests/ -v`)

### Architecture Deliverables

- [ ] Format registry design specification in `re-workspace/investigation/format-registry-design.md` (winning design from Team 14)
- [ ] Format registry implementation in `scripts/webm.lua` (from Team 17 selection)

### Documentation Deliverables

- [ ] `docs/adr/ADR-0007-subprocess-isolation.md` — ADR for the --no-config subprocess isolation fix
- [ ] `docs/adr/ADR-0008-ipc-trust-boundary.md` — ADR for IPC key validation
- [ ] `GLOSSARY.md` — updated with all new terms from this session
- [ ] `re-workspace/audit/adversarial-code-review.md` — adversarial review report from Teams 6–10
- [ ] `re-workspace/audit/final-audit-report.md` — Team 29 final audit report with PASS verdict
- [ ] API reference updated with all changed functions

### Investigation Artifacts

- [ ] `re-workspace/investigation/` — full 7-step investigation artifacts including Teams 4 and 5 forensic findings
- [ ] `re-workspace/claims/claims.jsonl` — all claims with final `confirmed` or `disputed` status (zero `disputed` at exit)
- [ ] `re-workspace/findings/findings.jsonl` — all FIND-* items with `confirmed_fixed` status at exit

### Defect Register

- [ ] `re-workspace/deliverables/13-defect-and-quality-register.md` — updated with fix status, commit hash, and test name for all fixed items

### GitHub

- [ ] All GitHub issues referencing confirmed-fixed bugs are closed with fix commit hash and test citation
- [ ] GitHub issue #2 updated with final resolution summary
- [ ] New issues filed for any remaining unfixed items
- [ ] `re-workspace/audit/github-issue-actions.md` — log of all issue actions

---

## Appendix A: Team Summary Table

| Team | Cluster | Mission | Size |
|------|---------|---------|------|
| 1 | A | FIND-005 fix | 20 |
| 2 | A | FIND-008 fix | 20 |
| 3 | A | FIND-009 deep analysis and hardening | 20 |
| 4 | A | FIND-013 format registry nil crash (forensic) | 20 |
| 5 | A | encode() monolith forensic audit | 20 |
| 6 | A | Adversarial review of Team 1 | 20 |
| 7 | A | Adversarial review of Team 2 | 20 |
| 8 | A | Adversarial review of Team 3 | 20 |
| 9 | A | Adversarial review of Team 4 | 20 |
| 10 | A | Adversarial review of Team 5 | 20 |
| 11 | B | Format registry Design A | 20 |
| 12 | B | Format registry Design B | 20 |
| 13 | B | Format registry Design C | 20 |
| 14 | B | Design adjudicator | 20 |
| 15 | B | Implementation Alpha | 20 |
| 16 | B | Implementation Beta | 20 |
| 17 | B | Adversarial implementation reviewer | 20 |
| 18 | C | Static analysis test suite | 20 |
| 19 | C | Mock harness expansion | 20 |
| 20 | C | Fuzz test team | 20 |
| 21 | C | Regression test team | 20 |
| 22 | C | Independent test verifier Alpha | 20 |
| 23 | C | Independent test verifier Beta | 20 |
| 24 | C | Independent test verifier Gamma | 20 |
| 25 | D | GLOSSARY.md update | 20 |
| 26 | D | ADR authoring (ADR-0007, ADR-0008) | 20 |
| 27 | D | API reference update | 20 |
| 28 | D | User guide update | 20 |
| 29 | E | Independent final audit | 20 |
| 30 | E | GitHub issue management | 20 |

**Total teams**: 30
**Total agents**: 600 (20 per team)

---

## Appendix B: Anti-Lying Design Principles

This section documents WHY the plan is designed the way it is, so that any agent reading the plan can understand the adversarial assumptions baked into every design decision.

### Principle 1: Independent Re-Derivation Over Trust

No team ever trusts another team's output. Every claim is re-derived from the original source file by an independent team. The adversarial teams (6–10, 17, 22–24, 29) exist specifically because prior teams may lie.

### Principle 2: Evidence Over Votes

Delphi panels decide by citing source lines, never by counting agents who agree. A single agent with a correct source citation defeats twenty agents without citations.

### Principle 3: Structural Independence

Teams 15 and 16 must produce structurally different implementations. If they are identical, it is treated as evidence of coordination rather than independent derivation, and both are rejected.

### Principle 4: Loop Exit by Evidence

The loop exits only when five independently-verifiable conditions are simultaneously true. No single team can declare victory. No majority vote can close a FIND-* item.

### Principle 5: Escalation Path Exists

If the loop runs more than 5 iterations without converging, the problem is escalated to human review with a specific, documented gap identified. The plan never hangs indefinitely.

### Principle 6: Claims Infrastructure

`claims.jsonl` and `findings.jsonl` are the authoritative sources of truth. No verbal or in-context agreement counts. Only file-system evidence counts. This prevents any agent from "remembering" a consensus that was never actually reached.
