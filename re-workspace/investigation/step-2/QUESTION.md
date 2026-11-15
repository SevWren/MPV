# Step 2 — Research Question

## QUESTION:
Does passing `cq-level=28` (without `--` prefix) as a bare positional argument in the
mpv encode subprocess command array — combined with the user's `keep-open=yes` inherited
from their mpv.conf (because `--no-config` was absent in the canonical webm.lua) — cause
the encode subprocess to run indefinitely at 0% CPU with a 0-byte output file (while running)
and a corrupt ~6MB output file (after kill), when `additional_flags= cq-level=28` is set
in `script-opts/webm.conf`?

## NULL HYPOTHESIS (H0):
The token `cq-level=28` (without `--`) and the absence of `--no-config`/`--keep-open=no`
do NOT cause the encode subprocess to hang indefinitely; some other factor is responsible.

## OBSERVABLE PROXY:
We will measure:
- **Metric M1**: Whether the encode subprocess exits within 30 seconds for a 0.9-second clip
- **Metric M2**: Output file size in bytes while subprocess is running
- **Metric M3**: Output file validity (moov atom present) after subprocess exits or is killed

Using:
- **Tool T**: Python `subprocess` harness (`cli-harness.py`) running the exact argv from
  [log:1282], with and without the bare `cq-level=28` token and with and without
  `--no-config`/`--keep-open=no` prepended.

## GATE CHECK:
- Names specific mpv option: `--keep-open=yes` [log:62], `cq-level=28` bare token [log:1282]
- Names specific observable metric: subprocess exit within 30s, output file size (bytes), moov atom presence
- Names specific precondition: `additional_flags= cq-level=28` in webm.conf [conf:75] AND
  `keep-open=yes` in user's mpv.conf [log:62] AND `--no-config` absent from canonical command [canonical:1708]
