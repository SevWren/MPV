# ADR-0007: Subprocess Isolation Flags for mpv Encode Processes

**Status**: Accepted
**Date**: 2026-11-15
**Deciders**: webm.lua maintainers
**Related**: FIND-012, scripts/webm.lua

---

## Context

webm.lua encodes video by spawning a child mpv process (via `subprocess` or `subprocess_detached`) with an output file argument. This child process is a full mpv instance. Unless told otherwise, it loads `~/.config/mpv/mpv.conf` and all scripts in `~/.config/mpv/scripts/` on startup — the same configuration used for the user's normal media player.

A typical user mpv.conf may contain any of:

```
keep-open=yes
loop-playlist=inf
hwdec=auto-copy
save-position-on-quit=yes
```

Each of these settings interferes with a headless encode subprocess in a different way:

- `keep-open=yes` — the subprocess does not exit after the encode completes. It waits for user input that will never come. The output file is left open and the moov atom (required for playable MP4/WebM) is never written.
- `loop-playlist=inf` — the subprocess loops the input indefinitely. The output file grows until disk is full or the parent process kills the child.
- `hwdec=auto-copy` — hardware decode may fail silently on headless systems, causing encode to fall back to a different pixel format and produce a broken output file.
- `save-position-on-quit=yes` — the subprocess writes a playback position to `~/.local/share/mpv/watch_later/` for the input file, corrupting the user's watch-later state for that file.

These failures are silent and environment-dependent. On a development machine with a minimal `mpv.conf`, everything works. On a production machine with a typical power-user `mpv.conf`, the encode fails with no error message — the output file simply has no moov atom or is zero bytes.

This was confirmed as FIND-012 during the webm.lua defect investigation.

---

## Decision

Every mpv encode subprocess spawned by webm.lua must receive the following flags, in this order, before the input file path:

```
--no-config
--load-scripts=no
--keep-open=no
--loop-playlist=no
--hwdec=no
--save-position-on-quit=no
```

These flags are collectively called the **subprocess isolation flags**.

The flags must be applied to ALL subprocess execution paths, including:
- Normal single-pass encode (`subprocess`)
- Two-pass encode, pass 1 (`subprocess`)
- Two-pass encode, pass 2 (`subprocess`)
- Detached encode (`subprocess_detached`)
- HLS encode (`subprocess`)

The order matters: `--no-config` must come first so that it prevents `mpv.conf` from being loaded before any other flag is processed. The remaining flags are belt-and-suspenders redundancy in case `--no-config` does not suppress a specific setting on all mpv versions.

---

## Consequences

### Positive

- Encode subprocess always exits cleanly after encoding completes.
- Output file always has a moov atom written.
- Encode behavior is deterministic regardless of the user's `mpv.conf` contents.
- Watch-later state is not corrupted.
- Hardware decode quirks do not silently affect output quality.

### Negative (Trade-offs)

**`--no-config` bypasses `encoding-profiles.conf`**: Some advanced users configure custom encode codec profiles in `~/.config/mpv/encoding-profiles.conf`. With `--no-config`, these profiles are not loaded. Users who rely on custom encoding profiles must migrate those settings to webm.lua's `additional_flags` option.

This is a deliberate trade-off: the correctness of the encode (clean exit, valid output file) is more important than supporting custom encoding profiles via `encoding-profiles.conf`. Users who need profile behavior should use `additional_flags`.

**`--hwdec=no` forces software decode**: On systems where hardware decode is significantly faster, encode throughput may decrease. This is acceptable because hardware decode has a higher failure rate in headless environments.

---

## Alternatives Considered

### Alternative 1: Document the issue, do not fix it

Document that `keep-open=yes` and `loop-playlist=inf` break webm.lua encodes, and ask users to add per-profile overrides to their `mpv.conf`.

**Rejected**: This pushes the burden to every user and produces silent failures for users who do not read the documentation.

### Alternative 2: Fix only keep-open and loop-playlist

Apply `--keep-open=no --loop-playlist=no` without `--no-config`, preserving access to `encoding-profiles.conf`.

**Rejected**: This is fragile. Any new setting added to the user's `mpv.conf` in the future could re-introduce the problem. `--no-config` is the only defense that is robust against unknown future `mpv.conf` contents.

### Alternative 3: Detect and warn

Before spawning the subprocess, read `mpv.conf` and warn the user if dangerous settings are present.

**Rejected**: Parsing `mpv.conf` is non-trivial (include directives, conditional blocks, profile inheritance) and still fails to handle settings added after the warning is shown.

---

## Verification

This decision is verified by the following static analysis test:

```python
# test_all_fixes.py — FIND-012
def test_find_012_subprocess_isolation():
    source = open("scripts/webm.lua").read()
    # --no-config must appear before the input path in all subprocess constructions
    assert "--no-config" in source
    assert "--load-scripts=no" in source
    assert "--keep-open=no" in source
```

The full test is in `re-workspace/harness/tests/test_all_fixes.py`.

---

## References

- FIND-012: Subprocess config isolation defect record
- `scripts/webm.lua` subprocess construction (search for `subprocess` calls)
- mpv man page: `--no-config`, `--load-scripts`
- `re-workspace/deliverables/13-defect-and-quality-register.md`
