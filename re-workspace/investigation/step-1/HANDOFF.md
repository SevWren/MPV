# Step 1 HANDOFF — Evidence Inventory

## Status: GATE PASSED — All four evidence files exist with cited, verbatim evidence.

## Evidence Files
1. `log-evidence.md` — mpv log extracts with line citations
2. `config-snapshot.md` — webm.conf option snapshot
3. `source-snapshot.md` — webm.lua encode() function diff canonical vs patched
4. `symptom-record.md` — user-reported symptoms

## Critical Evidence Summary

### Finding 1: Bare token `cq-level=28` in subprocess args
[log:1282] The encode subprocess was launched with `args="cq-level=28"` as a positional
argument — no `--` prefix. This is NOT a valid mpv option; it is interpreted as a file path.
Source: `additional_flags= cq-level=28` in [conf:75].

### Finding 2: User mpv.conf sets `keep-open=yes`
[log:62] `Setting option 'keep-open' = 'yes'` from user's mpv.conf.
In the canonical (pre-patch) webm.lua, the encode subprocess had NO `--no-config` flag,
meaning it loaded the user's full mpv.conf including `keep-open=yes`.

### Finding 3: User mpv.conf sets `save-position-on-quit=yes`
[log:61] `Setting option 'save-position-on-quit' = 'yes'` from user's mpv.conf.
Same issue — this would cause the encode subprocess to save playback state on quit,
potentially waiting for I/O.

### Finding 4: The canonical command array lacked isolation flags
[canonical:1707-1714] The pre-patch command array started with `"mpv", path, ...` —
no `--no-config`, no `--load-scripts=no`, no `--keep-open=no`, no `--loop-playlist=no`.

### Finding 5: The patched command array adds isolation flags
[webm.lua:1707-1720] The patched command inserts `--no-config`, `--load-scripts=no`,
`--keep-open=no`, `--loop-playlist=no`, `--hwdec=no`, `--save-position-on-quit=no`
before `path`.

### Finding 6: The patched version validates additional_flags tokens
[webm.lua:1796-1801] Tokens without `--` prefix are skipped. The canonical version
[canonical:1790-1792] passed them unconditionally.

### Finding 7: run_detached=yes
[conf:13] The subprocess is launched detached — mpv does not monitor it. This means
a hung subprocess is invisible to the parent.

## Root cause candidates identified
- **Candidate A**: `keep-open=yes` inherited from mpv.conf causes the encode subprocess
  to remain open after encoding finishes (waiting for user input or next file), never exiting.
- **Candidate B**: `cq-level=28` bare token causes mpv to try to open a file named
  `cq-level=28`, fail, and hang or loop on error/keep-open behavior.
- **Candidate C**: `save-position-on-quit=yes` + user scripts loaded by subprocess
  cause the subprocess to perform extra I/O or hang on quit.
- **Candidate D**: Both A and B compound: subprocess tries to open `cq-level=28` as a
  file (fails), then stays open due to `keep-open=yes`, and is idle at 0% CPU.

## Confidence
Both findings 1 and 2 are CONFIRMED by verbatim log citations.
Finding 1 is the more immediately visible issue. Finding 2 explains why the subprocess
does not exit even after the bad token causes mpv to stall.
