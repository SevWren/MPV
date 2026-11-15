# Step 1D — Symptom Record

## 1. Exact user-reported symptom description (from GitHub issue #2)
"mpv.exe encode subprocess runs indefinitely at 0% CPU. Output file is 0 bytes while running.
Output file has ~6MB of data after manually killing — but is corrupt (`moov atom not found`).
Happens even with 0.1-second clips. Not fixed by `strict_filesize_constraint=no`."

## 2. File size while process runs
0 bytes (reported: "0 bytes while running")

## 3. File size after process killed
~6MB (~6,291,456 bytes) — file exists but is corrupt

## 4. CPU usage while process runs
0% CPU (subprocess appears to be waiting/hanging, not encoding)

## 5. Whether the symptom reproduces with different clip durations
Yes — "Happens even with 0.1-second clips" (confirmed: duration is not the variable)

## 6. Whether the symptom reproduces with different output formats
Not explicitly stated. The log shows `output_format=mp4` with `--ovc=libx264 --oac=aac`.
The issue states it happens with this configuration. Other formats not tested per issue.

## 7. Workarounds attempted and their exact outcomes
- `strict_filesize_constraint=no`: **Did NOT fix the bug.**
  (This is relevant because `non_strict_additional_flags=cq-level=28` in the canonical
  default would only be passed when `strict_filesize_constraint=no` — but user set
  `additional_flags= cq-level=28` which is always passed regardless of constraint mode.)

## Corroboration from log
The encode was triggered at [log:1282] timestamp 19.931s.
The mpv session was quit at [log:1405] timestamp 59.024s — approximately 39 seconds later.
No encode completion message appears in the log (no "encode-finished" success/fail event).
The encode subprocess ran detached (`run_detached=yes` [conf:13]) so mpv did not track it.
The encode process was still running (or had run indefinitely) when mpv was quit.
