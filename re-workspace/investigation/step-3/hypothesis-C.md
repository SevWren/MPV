# Hypothesis C

## Mechanism
Both the bare `cq-level=28` token AND the absent `--no-config` flag are necessary for the
hang. The bare token causes mpv to treat `cq-level=28` as an input file path, which mpv
cannot open. Without `keep-open=yes` this would cause mpv to exit with an error. But with
`keep-open=yes` inherited from the user's mpv.conf (because `--no-config` was absent), mpv
stays open after the error, waiting for user interaction. The two bugs compound: either one
alone would cause a less severe failure, but together they produce the indefinite hang.

## Causal chain
1. Bare token `cq-level=28` → mpv interprets it as input file path [log:1282, log:1283]
2. No `--no-config` flag in canonical command [canonical:1708] → user's mpv.conf loaded by subprocess
3. mpv.conf includes `keep-open=yes` [log:62] AND user scripts (autoload, SmartCopyPaste, gallery-thumbgen etc.) loaded by subprocess [log:112-179] because `--load-scripts=no` absent
4. Loaded scripts may interact with the encode subprocess (autoload could try to populate playlist from D:\Videos\ directory) → further blocking behavior
5. mpv subprocess: (a) loads scripts, (b) attempts to open `cq-level=28` as file, (c) fails, (d) keep-open prevents exit, (e) scripts may block exit further
6. Net effect: subprocess idles at 0% CPU indefinitely, output file never finalized

## Prediction
If this hypothesis is correct, then:
- Only the COMBINED fix of `--no-config` + `--load-scripts=no` + `--keep-open=no` (or just removing `cq-level=28`) resolves the hang
- Fixing EITHER issue alone may not fully resolve the hang under all conditions
- Running E6 (combined fix) will produce: `timed_out=false`, `output valid`, `moov_atom=true`

## Falsification
This hypothesis is WRONG if:
- Removing only `cq-level=28` (without adding `--no-config`) produces a successful encode
- Adding only `--keep-open=no` (without fixing `cq-level=28`) produces a successful encode

## Experiment
The decisive test:
```
E6 (combined fix): mpv --no-config --load-scripts=no --keep-open=no --loop-playlist=no <source> ... (without cq-level=28 bare token) --o=<output>
  Expected IF HYPOTHESIS CORRECT: timed_out=false, output_file_size > 0, moov_atom=true

E4 (bare token removed only): same command without --no-config but with cq-level=28 removed
  Expected IF HYPOTHESIS C CORRECT: MAY still timeout due to keep-open=yes from mpv.conf

E2 (keep-open=no only): add --keep-open=no but keep cq-level=28 bare token
  Expected IF HYPOTHESIS C CORRECT: MAY still timeout because mpv tries to open bad file path
```
