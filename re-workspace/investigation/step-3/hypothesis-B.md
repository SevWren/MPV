# Hypothesis B

## Mechanism
The encode subprocess inherits `keep-open=yes` from the user's `mpv.conf` because the
canonical webm.lua did not pass `--no-config` to prevent config loading. After encoding
finishes normally, the subprocess stays open indefinitely (keep-open behavior), causing
the apparent hang. The `cq-level=28` bare token is a secondary issue but not the primary
cause of the hang.

## Causal chain
1. Canonical command array [canonical:1707-1714] starts with `"mpv", path, ...` — no `--no-config` present
2. encode subprocess is launched → mpv loads user's `C:\Users\mmuel\AppData\Roaming/mpv/mpv.conf`
3. mpv.conf sets `keep-open=yes` [log:62] → subprocess will not exit after playback/encoding ends
4. Subprocess completes encoding → writes partial data → reaches end-of-file → but `keep-open=yes` prevents exit
5. Process stays alive at 0% CPU, waiting for user to press `q` or send quit signal
6. Output file has ~6MB because encoding started but MP4 container moov atom is never written (muxer not finalized)

## Prediction
If this hypothesis is correct, then:
- Running the exact command from [log:1282] WITHOUT `--no-config` and WITHOUT `--keep-open=no` will produce: `timed_out=true`
- Running the same command WITH `--keep-open=no` appended will NOT produce a timeout (subprocess will exit after encoding)

## Falsification
This hypothesis is WRONG if:
- The subprocess times out even when `--keep-open=no` is explicitly passed
- The subprocess exits normally without `--keep-open=no` (meaning keep-open is not the cause)

## Experiment
The decisive test:
```
E2 (test keep-open): mpv ... --keep-open=no ... cq-level=28 --o=<output>
  Expected IF HYPOTHESIS CORRECT: timed_out=false, output valid

E5 (test no-config): mpv --no-config ... cq-level=28 --o=<output>
  Expected IF HYPOTHESIS CORRECT: timed_out=false (because no-config prevents keep-open=yes from being loaded)
```
