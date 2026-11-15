# Hypothesis A

## Mechanism
The bare token `cq-level=28` (missing `--` prefix) is passed as a positional file-path
argument to the encode subprocess, causing mpv to treat it as an input file. mpv then
attempts to demux a non-existent file, fails to load it, and — because the subprocess
inherited `keep-open=yes` from the user's mpv.conf (no `--no-config` in canonical command)
— the subprocess remains open indefinitely waiting for user interaction, burning 0% CPU.

## Causal chain
1. `additional_flags= cq-level=28` in webm.conf [conf:75] → `options.additional_flags` = `"cq-level=28"` (after trim)
2. Canonical additional_flags loop [canonical:1790-1792] adds `cq-level=28` token unconditionally to command array → token appears at [log:1282] as `args="cq-level=28"`
3. mpv subprocess receives `cq-level=28` as a positional argument → interprets it as a second input file path after the actual video file [log:1283]
4. mpv cannot open file named `cq-level=28` → demux error → with `keep-open=yes` inherited from user mpv.conf [log:62] (because canonical command had no `--no-config` [canonical:1708-1709]), subprocess stays open at the error state
5. Output file grows to ~6MB from partial encoding of the actual video before the bad token is processed, then write is never finalized → `moov atom not found` (MP4 muxer never received EOF signal to write the moov atom)

## Prediction
If this hypothesis is correct, then:
- Running the exact command from [log:1282] (with `cq-level=28` bare token, without `--no-config`) will produce: `timed_out=true`, `output_file_size_while_running=0`, `moov_atom_present=false`
- Running the same command WITH `cq-level=28` REMOVED will NOT produce a timeout

## Falsification
This hypothesis is WRONG if:
- The subprocess exits normally even with `cq-level=28` as a bare positional argument
- The subprocess hangs even when `cq-level=28` is properly prefixed as `--ovcopts-add=cq-level=28`

## Experiment
The decisive test:
```
E1 (reproduce): mpv <source> --start=... --end=... --loop-file=no --no-pause --ovc=libx264 --oac=aac --vid=1 --aid=1 --sid=no <playback flags> --ovcopts-add=b=86939k cq-level=28 --o=<output>
  Expected: timed_out=true within 30s

E4 (remove bare token): same command with "cq-level=28" token removed
  Expected IF HYPOTHESIS CORRECT: timed_out=false, output valid
```
