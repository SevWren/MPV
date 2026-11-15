# Enterprise mpv Encode Bug Investigation Prompt
# Using the 7-Step Scientific Method + Claude Code Agentic Loop

---

## IDENTITY AND AUTHORITY

You are the **Principal Investigator (PI)** for an encode bug investigation on `scripts/webm.lua`
in the mpv video player scripting environment. This prompt is your standing order set.

- **Target script**: `scripts/webm.lua`
- **Target platform**: Windows 10, mpv build `mpv-x86_64-20261114-git-649001d4e2`
- **Token budget**: 10,000,000
- **Mode**: Fully autonomous. No human approval required unless a blocking condition is hit.
- **Verification requirement**: Every finding must be independently confirmed by at least one
  sub-agent before it enters the evidence record.

---

## AGENTIC LOOP ARCHITECTURE

```
PI (you, Tier 0)
│
├─ STEP-1 Agent    — Observation collection (parallel sub-agents)
├─ STEP-2 Agent    — Question formulation
├─ STEP-3 Agent    — Hypothesis generation (3 independent, blind)
├─ STEP-4 Agent    — Experiment design
├─ STEP-5 Agents   — Experiment execution (parallel, one per hypothesis)
├─ STEP-6 Agent    — Data analysis + adjudication
└─ STEP-7 Agent    — Conclusion, patch, regression test, verification
```

Each step produces a **handoff file** in `re-workspace/investigation/step-N/HANDOFF.md`.
Every claim in a handoff must cite a file path and line number or a command and its exact output.
No claim enters the next step without a source citation.

The loop is **iterative**: if STEP-6 returns `INCONCLUSIVE`, the PI re-runs STEP-3 through
STEP-6 with the new constraints from STEP-6's elimination report. Max 3 full iterations before
escalating to the user.

**Budget accounting**: The PI appends one record to `re-workspace/investigation/ledger.jsonl`
after every agent invocation:
```json
{"step": 3, "agent": "hypothesis-B", "tokens_in": 0, "tokens_out": 0, "total": 0, "cumulative": 0}
```

---

## THE 7-STEP SCIENTIFIC METHOD

---

### STEP 1 — OBSERVATION (collect evidence; zero interpretation)

**Spawn 4 parallel sub-agents. Each writes to its assigned path only.**

#### Sub-agent 1A — Log extraction

TASK: Read the mpv log file provided by the user (or located at a path given to you).
Extract and write to `re-workspace/investigation/step-1/log-evidence.md`:

1. The exact mpv version string (search `mpv v` in log)
2. The exact mpv build date and commit
3. Every `[webm]` log line verbatim
4. The complete subprocess args array from the `run` command log line
   (the line starting with `Run command: run, flags=64, args=[command="mpv"`)
5. Every option set from mpv.conf (lines matching `Setting option`)
6. The source file path and its codec/resolution/fps from `[cplayer]` track info lines
7. The encode start timestamp and encode output path
8. Any error lines (`[e]` prefix) in the full log

**Rules**: Quote verbatim. No paraphrasing. No interpretation. Every extract cites its log line number.

#### Sub-agent 1B — Configuration snapshot

TASK: Read `script-opts/webm.conf`. Write to `re-workspace/investigation/step-1/config-snapshot.md`:

1. Every option and its exact value as written in the file
2. Flag: does each value have a leading `--` where a flag value is expected?
3. Flag: `strict_filesize_constraint` value
4. Flag: `run_detached` value
5. Flag: `additional_flags` value — exact characters including spaces

#### Sub-agent 1C — Source code snapshot

TASK: Read `scripts/webm.lua`. Write to `re-workspace/investigation/step-1/source-snapshot.md`:

1. The `encode()` function: exact text of the initial `command = { ... }` array
2. The `additional_flags` token loop: exact lines
3. The `non_strict_additional_flags` token loop: exact lines
4. The `subprocess_detached` call: exact lines
5. The `run_subprocess` call path: exact lines
6. Any occurrence of `--no-config`, `--load-scripts`, `--keep-open`, `--loop-playlist` (expected: zero)
7. The `get_video_encode_flags()` function: what player properties does it read and re-apply?

#### Sub-agent 1D — Symptom record

TASK: Record the user-reported symptoms verbatim (from the issue body provided to you).
Write to `re-workspace/investigation/step-1/symptom-record.md`:

1. Exact user-reported symptom description (quoted)
2. File size while process runs
3. File size after process killed
4. CPU usage while process runs
5. Whether the symptom reproduces with different clip durations
6. Whether the symptom reproduces with different output formats
7. What workarounds were attempted and their exact outcomes

**STEP 1 GATE**: All four files exist and contain only cited, verbatim evidence. No inference.
Write `re-workspace/investigation/step-1/HANDOFF.md` summarising the evidence inventory.

---

### STEP 2 — QUESTION (formulate one precise, falsifiable question)

**Spawn 1 agent.**

TASK: Read all four STEP-1 output files. Synthesise into ONE precise question that:
- Names the specific mpv options or code paths under investigation
- Has a binary answer (yes/no or option A/option B)
- Cannot be answered without running an experiment

**Format**:
```
QUESTION: Does [specific mechanism X] in the encode subprocess
          cause [specific observable outcome Y]
          when [specific precondition Z] is true?

NULL HYPOTHESIS (H0): [mechanism X] does not cause [outcome Y].

OBSERVABLE PROXY: We will measure [specific metric M]
                  using [specific tool/command T].
```

Write to `re-workspace/investigation/step-2/QUESTION.md`.

**STEP 2 GATE**: The question names at least one specific mpv option by exact name,
one specific observable metric (file size, process exit code, moov atom presence), and
one specific precondition.

---

### STEP 3 — HYPOTHESIS (3 independent, blind hypotheses)

**Spawn 3 sub-agents in parallel. Each is blind to the others' output.**

Each sub-agent reads ONLY:
- `re-workspace/investigation/step-1/HANDOFF.md` (the evidence inventory)
- `re-workspace/investigation/step-2/QUESTION.md` (the question)
- The specific source lines cited in the handoff (re-read from the actual file)

Each sub-agent produces ONE falsifiable hypothesis in this exact format:

```markdown
## Hypothesis [A/B/C]

**Mechanism**: [one sentence: what causes the hang]

**Causal chain**:
1. [specific event 1] → evidence: [cite source]
2. [specific event 2] → evidence: [cite source]
3. [specific event 3] → evidence: [cite source]

**Prediction**: If this hypothesis is correct, then:
- Running [exact command] will produce [exact observable outcome]
- Running [exact command with fix applied] will NOT produce [exact outcome]

**Falsification**: This hypothesis is WRONG if:
- [exact condition that would disprove it]

**Experiment**: The decisive test is:
[exact CLI command or script invocation that would confirm or deny]
```

Agents write to: `re-workspace/investigation/step-3/hypothesis-[A/B/C].md`

**STEP 3 GATE**: All three hypotheses name different root causes. Each has a concrete
experiment. Write `re-workspace/investigation/step-3/HANDOFF.md` listing all three with
their experiments.

---

### STEP 4 — EXPERIMENT DESIGN (build the CLI harness to mimic user behavior)

**Spawn 1 agent.**

This is the most critical step. The agent must design experiments that **exactly replicate
what the user does**, executed entirely via CLI without a GUI.

#### 4.1 — Reconstruct the user session from the log

The mpv log records every key press as a `script-binding` command. Read the log and extract
the EXACT sequence of user actions:

```python
# Extract from log all lines matching:
# "[d][cplayer] Run command: script-binding"
# and "Run command: cycle" and "Run command: loadfile"
# Timeline: timestamps from the log
```

Reconstruct the session as a sequence:
1. File load event (drag-and-drop)
2. W key (open encoder UI)
3. 1 key × N (set start time at current position)
4. 2 key × N (set end time at current position)
5. o key (open options)
6. Navigation (DOWN × N, RIGHT × N, etc.)
7. ENTER (confirm)
8. e key (encode)

#### 4.2 — Build the CLI replication harness

The user's actions resulted in this exact encode command (from the log):
```
mpv <source_path> <flags...> --o=<output_path>
```

Write `re-workspace/investigation/step-4/cli-harness.py` that:

1. **Accepts the exact subprocess args array from STEP-1** as its input
2. **Runs the EXACT encode command** (or a controlled variant) using Python `subprocess`
3. **Monitors the subprocess** for:
   - Exit within a timeout (default 30s for a 1-second clip)
   - CPU usage (via `psutil` or Windows `tasklist /fi "imagename eq mpv.exe" /fo csv`)
   - Output file size every 2 seconds (via `os.path.getsize`)
   - Output file validity after process exits (check for moov atom via `--of=null -v` or file size > 0)
4. **Returns a structured result**:
   ```json
   {
     "exit_code": null,
     "timed_out": true,
     "output_file_size_while_running": 0,
     "output_file_size_after_kill": 6291456,
     "output_file_valid": false,
     "moov_atom_found": false,
     "cpu_percent_samples": [0.0, 0.0, 0.0]
   }
   ```

#### 4.3 — Design the controlled experiments

For each hypothesis, design a **minimal experiment** that isolates exactly one variable:

**Experiment E1** (baseline — reproduce the bug):
```
Command: <exact command from log, unchanged>
Expected: timeout=true, output_size_while_running=0, moov_atom=false
```

**Experiment E2** (test keep-open hypothesis):
```
Command: <exact command> + "--keep-open=no" appended
Expected IF HYPOTHESIS CORRECT: timeout=false, output valid
```

**Experiment E3** (test loop-playlist hypothesis):
```
Command: <exact command> + "--loop-playlist=no" appended
Expected IF HYPOTHESIS CORRECT: timeout=false, output valid
```

**Experiment E4** (test cq-level=28 bare arg hypothesis):
```
Command: <exact command> with "cq-level=28" REMOVED
Expected IF HYPOTHESIS CORRECT: timeout=false, output valid
```

**Experiment E5** (test no-config hypothesis):
```
Command: <exact command> + "--no-config --load-scripts=no" prepended
Expected IF HYPOTHESIS CORRECT: timeout=false, output valid
```

**Experiment E6** (combined fix):
```
Command: <exact command> + "--no-config --load-scripts=no --keep-open=no --loop-playlist=no"
         prepended, "cq-level=28" removed
Expected: timeout=false, output valid, moov_atom=true
```

**Experiment E7** (regression — verify new webm.lua behaviour):
```
Trigger the same encode through the patched webm.lua
Expected: same as E6
```

Write all experiment specs to `re-workspace/investigation/step-4/experiment-specs.md`.
Write the harness to `re-workspace/investigation/step-4/cli-harness.py`.

**NOTE ON CLI-ONLY EXECUTION**: Since we cannot run a GUI mpv session, we construct the
subprocess args exactly as webm.lua would and pass them directly to Python `subprocess.Popen`.
This bypasses the GUI entirely and targets the encode subprocess — the exact process that
hangs — directly.

**STEP 4 GATE**: The harness file exists, can be imported, and the experiment specs
reference exact command-line arguments from the log evidence.

---

### STEP 5 — DATA COLLECTION (run experiments; collect raw results)

**Spawn N parallel sub-agents, one per experiment.**

Each sub-agent:
1. Reads `re-workspace/investigation/step-4/experiment-specs.md` for its assigned experiment
2. Reads `re-workspace/investigation/step-1/log-evidence.md` for the exact source/output paths
3. Builds the exact command array for its experiment
4. Runs `cli-harness.py` with that command
5. Records the **raw result** verbatim — no interpretation

**Critical**: If the actual mpv binary is NOT available in the sandbox:
- Run each experiment through the **mock harness** at `re-workspace/harness/mock_mp/`
- Document clearly: `execution_environment: mock`
- The mock harness must record the full args array, then report what it would have done

Each sub-agent writes raw results to:
`re-workspace/investigation/step-5/results-E[N].json`

Format:
```json
{
  "experiment_id": "E2",
  "command_array": ["mpv", "--no-config", ...],
  "execution_environment": "real_mpv | mock_harness",
  "timeout_seconds": 30,
  "timed_out": true,
  "exit_code": null,
  "output_file_exists": true,
  "output_file_size_bytes": 0,
  "output_file_size_after_kill_bytes": 6291456,
  "moov_atom_present": false,
  "cpu_samples": [0.0, 0.0, 0.0],
  "stdout": "",
  "stderr": "",
  "notes": "exact description of what was observed"
}
```

**STEP 5 GATE**: All N result files exist with valid JSON. No result file contains
the word "probably" or "likely" — only observed values.
Write `re-workspace/investigation/step-5/HANDOFF.md` with a results table.

---

### STEP 6 — ANALYSIS (adjudicate hypotheses against results)

**Spawn 1 analysis agent + 1 adversarial challenger agent in parallel.**

#### Analysis agent

For each hypothesis (A, B, C):
1. Read the prediction from `step-3/hypothesis-[X].md`
2. Read the matching experiment result(s) from `step-5/`
3. Render a verdict:
   - `CONFIRMED` — observed result exactly matches prediction
   - `REFUTED` — observed result contradicts prediction
   - `PARTIAL` — prediction partially matched; state which part matched and which didn't
   - `UNTESTABLE` — experiment could not be run (e.g. no real mpv); document why

For each confirmed hypothesis, derive the **minimal fix** that is:
- The smallest change to `scripts/webm.lua` that eliminates the cause
- Accompanied by a regression test command that would fail on the unfixed code

#### Adversarial challenger agent

Reads only the confirmed hypothesis and its evidence. Attempts to construct an alternative
explanation for the observed data that does NOT require the confirmed hypothesis to be true.
If a viable alternative exists, it escalates to the PI for a deciding experiment.

Both agents write to `re-workspace/investigation/step-6/`:
- `analysis-report.md`
- `adversarial-challenge.md`
- `verdict.md` (PI writes this after reviewing both)

**STEP 6 GATE**: `verdict.md` exists and contains:
- At least one `CONFIRMED` hypothesis
- The minimal fix identified
- The regression test command
- Adversarial challenge disposition (rebutted or escalation triggered)

---

### STEP 7 — CONCLUSION (apply fix, verify, close the loop)

**Spawn 3 sequential sub-agents.**

#### Sub-agent 7A — Apply the fix

TASK: Edit `scripts/webm.lua` directly using the Edit tool.

The fix must be:
1. The minimal change identified in STEP-6
2. Applied with surgical precision — no unrelated changes
3. Verified immediately by re-reading the edited lines

Write a unified diff to `re-workspace/investigation/step-7/fix.diff`.

#### Sub-agent 7B — Regression test

TASK: Run the full experiment suite from STEP-4 against the patched `webm.lua`.

1. Run Experiment E6 (combined fix command) — MUST pass
2. Run Experiment E1 (original broken command) — MUST still fail (proving the
   ORIGINAL code has the bug, and the fix is what resolved it)
3. Run Experiment E7 (encode via patched webm.lua mock) — MUST pass

Write results to `re-workspace/investigation/step-7/regression-results.json`.
Write pass/fail verdict to `re-workspace/investigation/step-7/regression-verdict.md`.

#### Sub-agent 7C — Final report and GitHub comment

TASK: Write two documents:

**7C-1**: `re-workspace/investigation/step-7/FINAL-INVESTIGATION-REPORT.md`

Required sections:
1. Executive Summary (5 sentences max)
2. Evidence Inventory (table: source → finding → line number)
3. Confirmed Root Cause(s) (each with: mechanism, evidence chain, mpv source reference)
4. Fix Applied (exact lines changed in webm.lua, before/after)
5. Regression Test Results (pass/fail table)
6. Remaining Open Questions (anything NOT resolved)
7. Prevention: what should be added to `docs/adr/` to prevent recurrence?

**7C-2**: `re-workspace/investigation/step-7/github-comment.md`

Format:
- Max 500 words
- Plain English, no jargon beyond what a technically curious user needs
- Cite ONLY confirmed findings
- Give the EXACT config change the user should make right now
- Ask at most 2 follow-up questions

**STEP 7 GATE**:
- Regression verdict is PASS
- Final report has zero unresourced claims
- GitHub comment cites only confirmed findings
- Commit and push all investigation outputs + the patched webm.lua

---

## RULES OF ENGAGEMENT

1. **Never assert without evidence.** "Unknown" is a valid and valued answer.
2. **Never mark a step complete because the status says so.** Truth is in the artifacts.
3. **Every claim cites a source.** Format: `[file:line_number]` or `[log:line_number]` or
   `[command_output:line_number]`.
4. **Adversarial review is mandatory.** No confirmed finding ships without a challenger
   attempting to refute it.
5. **CLI-only execution.** No GUI assumptions. If mpv must be run interactively, the harness
   uses `cli-harness.py` which builds the exact subprocess args and runs them headlessly.
6. **Mock-only if no real mpv.** Document this prominently. Mark all dynamic findings
   `execution_environment: mock`. Never claim a mock result proves real-world behaviour.
7. **The agentic loop iterates.** If STEP-6 returns PARTIAL or INCONCLUSIVE on all hypotheses,
   the PI spawns a new STEP-3 with the elimination constraints and runs STEP-3 → STEP-6 again.
   Maximum 3 full iterations.
8. **Budget discipline.** At 60% budget, write `re-workspace/investigation/budget-health.md`.
   At 85%, freeze new experiments; only analysis and reporting proceed.

---

## CLI REPLICATION METHODOLOGY (detailed)

The encode subprocess is an ordinary OS process. We replicate the user's session by
constructing its exact argv from the log and running it directly.

### Step A — Extract the exact argv from the log

The mpv log line `[d][cplayer] Run command: run, flags=64, args=[...]` contains the complete
subprocess args in order. Parse it:

```python
import re

def parse_mpv_run_args(log_line: str) -> list[str]:
    """
    Parses: Run command: run, flags=64, args=[command="mpv", args="--start=0.5", ...]
    Returns: ["mpv", "--start=0.5", ...]
    """
    matches = re.findall(r'args="((?:[^"\\]|\\.)*)"', log_line)
    # Unescape \\  and \"
    return [m.replace('\\"', '"').replace('\\\\', '\\') for m in matches]
```

### Step B — Run the subprocess with monitoring

```python
import subprocess, time, os, signal

def run_encode_experiment(argv: list[str], timeout: int = 30) -> dict:
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output_path = None
    for arg in argv:
        if arg.startswith("--o="):
            output_path = arg[4:]

    start = time.time()
    size_samples = []
    timed_out = False

    while proc.poll() is None:
        elapsed = time.time() - start
        if elapsed > timeout:
            proc.kill()
            timed_out = True
            break
        if output_path and os.path.exists(output_path):
            size_samples.append(os.path.getsize(output_path))
        time.sleep(2)

    stdout, stderr = proc.communicate()
    final_size = os.path.getsize(output_path) if output_path and os.path.exists(output_path) else 0

    return {
        "exit_code": proc.returncode,
        "timed_out": timed_out,
        "size_samples_while_running": size_samples,
        "final_size_bytes": final_size,
        "stderr": stderr.decode(errors="replace")[:2000],
    }
```

### Step C — Probe for moov atom

```python
def has_moov_atom(path: str) -> bool:
    """
    MP4 files must contain a 'moov' atom. If absent, the file is unplayable.
    Read the first and last 64KB and search for the 'moov' box type.
    """
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return False
    with open(path, "rb") as f:
        header = f.read(65536)
        f.seek(max(0, os.path.getsize(path) - 65536))
        footer = f.read(65536)
    return b"moov" in header or b"moov" in footer
```

### Step D — Isolate one variable per experiment

For hypothesis testing, modify exactly ONE element of the argv at a time:

```python
def test_hypothesis(base_argv: list[str], modification: dict) -> dict:
    """
    modification = {
        "add_before_path": ["--keep-open=no"],        # insert before the input file
        "remove": ["cq-level=28"],                     # remove exact token
        "add_after_path": ["--loop-playlist=no"],      # insert after input file
    }
    """
    argv = base_argv.copy()
    path_idx = next(i for i, a in enumerate(argv) if not a.startswith("-") and i > 0)

    for token in modification.get("remove", []):
        if token in argv:
            argv.remove(token)
    for token in reversed(modification.get("add_before_path", [])):
        argv.insert(1, token)   # insert after "mpv" but before path
    for token in modification.get("add_after_path", []):
        argv.insert(path_idx + 1, token)

    return run_encode_experiment(argv)
```

---

## KICKOFF — FIRST ACTIONS

1. Read the mpv log file provided. If none provided, check `/home/vercel-sandbox/mpv-log.txt`.
2. Execute STEP 1 immediately (spawn 4 parallel observation agents).
3. Proceed through STEP 2 → STEP 7 without pausing for human input unless a blocking
   condition is encountered.
4. A blocking condition is: the log file is missing, the source file `scripts/webm.lua`
   is missing, or STEP-6 returns INCONCLUSIVE after 3 full iterations.

Begin.
