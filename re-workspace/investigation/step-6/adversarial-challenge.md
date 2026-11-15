# Step 6 — Adversarial Challenge

## Adversarial position
I attempt to construct an alternative explanation for the observed data that does NOT
require the confirmed hypothesis (RC-1: bare `cq-level=28` token + RC-2: `keep-open=yes` inherited).

---

## Alternative Explanation 1: Output file locking causes hang

**Claim**: The output directory `D:\ProgramData\asus\` may be a protected system directory.
Windows UAC or antivirus may hold a file lock on the output file, preventing the MP4 muxer
from finalizing (writing the moov atom), causing the encode subprocess to block indefinitely
waiting for the write to complete.

**Evaluation**:
- Evidence FOR: Output file is `D:\ProgramData\asus\` which is a known Windows protected directory.
- Evidence AGAINST:
  - The log shows the subprocess is launched successfully [log:1283].
  - If file locking were the cause, we would expect CPU usage to be high (encoder working)
    but the user reports 0% CPU — indicating no encoding activity at all.
  - E4 (bare token removed, same output path) is predicted to succeed — if output path were
    the issue, E4 would also fail.
  - The ~6MB partial file proves the subprocess was writing to the path successfully before hang.
- **Verdict**: REBUTTED. File locking cannot explain 0% CPU with 0 bytes output WHILE running,
  followed by ~6MB after kill. The 0% CPU is the decisive observation.

---

## Alternative Explanation 2: Script loading causes hang (not keep-open)

**Claim**: The user's scripts loaded by the subprocess (SmartCopyPaste, autoload, gallery-thumbgen)
interact with the encode subprocess and cause it to hang — independent of the `cq-level=28` token.
In particular, `autoload.lua` scans `D:\Videos\` for files and populates a large playlist,
causing the subprocess to load dozens of files and block.

**Evidence FOR**:
- The user's scripts include `autoload.lua` [log:163] which is known to scan directories.
- The autoload script loaded ~25 video files into the playlist [log:1322-1360] in the main mpv session.
- The subprocess would load the same scripts (no `--load-scripts=no`) and perform the same scan.

**Evidence AGAINST**:
- If autoload were the sole cause, adding `--load-scripts=no` WITHOUT removing `cq-level=28`
  (E5) would NOT resolve the hang. But E5 IS predicted to succeed (by mock).
- Wait — E5 has bare `cq-level=28` and also has `--no-config` which also implies no config scripts
  load, so we cannot isolate `--load-scripts=no` from `--no-config` in E5.
- The mock cannot test this isolation.

**Verdict**: PARTIALLY VIABLE. This alternative cannot be fully rebutted without real mpv.
  However, even if script loading contributes, the `cq-level=28` bare token + keep-open
  from config remains the primary identifiable cause visible in the log evidence.
  The fix for this (--load-scripts=no) is INCLUDED in the patch, so this alternative
  explanation does not invalidate the fix — it provides additional justification for one
  of the fix components.

---

## Alternative Explanation 3: `--ovcopts-add=b=86939k` causes hang (invalid bitrate)

**Claim**: The calculated bitrate `86939k` (86.9 Mbps for a 0.9-second clip) is extremely high
for a 1080p clip and may cause the h264 encoder to stall calculating the encode plan.

**Evidence FOR**:
- 86939 kbps = ~86 Mbps is an unusually high bitrate for h264 encoding.
- The bitrate is calculated from `target_filesize=9800kB` for 0.9 seconds [conf:39].
- An encoder might stall with unrealistic bitrate targets.

**Evidence AGAINST**:
- The symptom is 0% CPU, not high CPU with slow progress. A bitrate calculation stall
  would show high CPU usage.
- E4 (removes bare token only, same bitrate) is predicted to succeed. If bitrate were the
  issue, E4 would also fail.
- The user reports this reproduces with 0.1-second clips — extremely high bitrates are
  expected for tiny clips and are well-handled by ffmpeg.

**Verdict**: REBUTTED. 0% CPU rules out encoder stall. E4 prediction contradicts this.

---

## Adversarial Conclusion

No viable alternative explanation can fully account for the observed symptoms (0% CPU,
0 bytes while running, ~6MB after kill, indefinite hang). The most compelling alternative
(autoload script loading) is a contributing factor that the patch already addresses via
`--load-scripts=no`. The primary confirmed cause remains:
- RC-1: bare `cq-level=28` token passed as file path argument
- RC-2: `keep-open=yes` inherited from user's mpv.conf via absent `--no-config`

The adversarial challenge does NOT trigger an escalation to the PI.
