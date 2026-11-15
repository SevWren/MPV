# ISSUE-002: Information Requirements Checklist

**Purpose**: Complete diagnostic information needed to fully diagnose the "moov atom not found" export failure
**Reporter environment**: Windows 10, mpv-x86_64-20261114-git-649001d4e2, webm.lua script
**Already provided by reporter**:
- webm.conf: `strict_filesize_constraint=yes`, `run_detached=yes`, `output_format=mp4`, `additional_flags= cq-level=28`
- Console output snippet showing mpv playback and `moov atom not found` error
- mpv build version (implicit from repo context: 649001d4e2)

**Most probable root cause (pre-diagnosis)**: FIND-001 — `strict_filesize_constraint=yes` in webm.conf triggers the undefined `bitrate` variable bug at L1779–1780, producing `--ovcopts-add=minrate=nilk` in the ffmpeg command. ffmpeg rejects this flag and exits with an error. Because `run_detached=yes` is also set, the encode process runs in the background and its failure is silent in the mpv UI. The resulting `.mp4` file is either absent or is a zero-byte/incomplete file (which produces the "moov atom not found" error when any player tries to open it).

---

## Category A: Disambiguation (highest priority)

### A1. Source file vs output file identity
**What it is**: Whether `D:\ProgramData\asus\New folder\Tulsa-...` is the **source** file that was loaded into mpv before pressing W, or the **output** file produced by webm.lua after pressing W.

**Why it's needed**: If the path is the source, the "moov atom not found" error means the source file itself is corrupt — this is a completely different problem unrelated to webm.lua. If it is the output, then the encode process produced a corrupt or truncated mp4, which is the expected symptom of FIND-001.

**How to get**:
1. Check whether the file existed before you pressed W in mpv. If you loaded it into mpv and it played, it is the source.
2. Run in cmd.exe: `dir "D:\ProgramData\asus\New folder\*.mp4" /T:W /O:D`
   This lists mp4 files sorted by write date. A file created at the time you pressed W is the output.
3. The mpv title bar shows the loaded file path — if it matches the path in the error, it is the source.

---

### A2. Output file appearance and size after pressing W
**What it is**: Whether a new `.mp4` file appears in `D:\ProgramData\asus\` after pressing W, and if so, its file size in bytes.

**Why it's needed**:
- **No file created**: suggests the encode process failed before writing anything (command construction error, e.g., `nil` variable crash — consistent with FIND-001).
- **Zero-byte file**: suggests ffmpeg started but immediately exited due to the invalid `--ovcopts-add=minrate=nilk` flag.
- **Non-zero but small file**: suggests ffmpeg wrote headers and then crashed — this produces the "moov atom not found" symptom because the mp4 `moov` atom is written at the end of the encode.
- **Full-size file**: suggests the encode succeeded and the error is coming from the source file or a different player issue.

**How to get**: After pressing W in mpv, run in cmd.exe:
```
dir "D:\ProgramData\asus\*.mp4" /T:W /O:D
```
Report the filename and size of any file created within the last few seconds.

---

### A3. Second mpv.exe process appearance
**What it is**: Whether a second `mpv.exe` process appears in Task Manager after pressing W.

**Why it's needed**: `run_detached=yes` in webm.conf means webm.lua spawns a separate `mpv.exe` process to perform the encode. If no second process ever appears, the script is failing before even calling `subprocess_detached` (e.g., a Lua error in the encode command assembly). If a second process appears and disappears instantly, the encode started but failed immediately (consistent with an invalid ffmpeg flag).

**How to get**:
1. Open Task Manager (Ctrl+Shift+Esc) and go to the Details tab.
2. Press W in mpv.
3. Watch for a new `mpv.exe` row to appear. Note whether it stays open or disappears within 1–2 seconds.

---

## Category B: Configuration Confirmation

### B4. webm.conf is actually being loaded by mpv
**What it is**: Confirmation that mpv is reading the `script-opts/webm.conf` file from the correct location.

**Why it's needed**: If the conf file is in the wrong directory, mpv silently ignores it and uses defaults (which include `strict_filesize_constraint=false`). In that case FIND-001 would not trigger and a different cause must be sought.

**How to get**:
1. The correct location on Windows is `%APPDATA%\mpv\script-opts\webm.conf`. Run:
   `echo %APPDATA%` to find the path, then check `dir "%APPDATA%\mpv\script-opts\"`
2. Alternatively, open the encode options screen in mpv (press W then 'o') and check whether "Strict Filesize Constraint" shows as enabled (On). If it shows Off despite webm.conf having `yes`, the conf is not being loaded.

---

### B5. webm.lua source modifications
**What it is**: Whether the installed `scripts/webm.lua` has been edited from the version in this repository.

**Why it's needed**: The FIND-001 bug exists at L1779–1780 in the canonical file. If the user's copy has a different version or has been patched, the bug may not be present — or additional bugs may be present.

**How to get**: Run the following and share the output:
```
findstr /n "minrate\|maxrate\|bitrate" "%APPDATA%\mpv\scripts\webm.lua"
```
If lines containing `minrate=nilk` or `tostring(bitrate)` appear, FIND-001 is present in the installed script.

---

## Category C: Reproduce Isolation Test

### C6. Test with strict_filesize_constraint=no
**What it is**: The single-variable isolation test — change `strict_filesize_constraint=yes` to `strict_filesize_constraint=no` in webm.conf and attempt the same export.

**Why it's needed**: If the export succeeds with `no` and fails with `yes`, this definitively confirms FIND-001 as the root cause. No other diagnosis is needed.

**How to get**:
1. Edit `%APPDATA%\mpv\script-opts\webm.conf`
2. Change `strict_filesize_constraint=yes` to `strict_filesize_constraint=no`
3. Restart mpv, load the same file, press W, set the same region, press 'e' to encode
4. Report whether a valid mp4 file is produced

---

### C7. Test with additional_flags cleared
**What it is**: Test with `additional_flags=` (empty) in webm.conf.

**Why it's needed**: The current config has `additional_flags= cq-level=28`. Note the leading space before `cq-level` — this is legal but unusual. Additionally, `cq-level=28` is an NVENC-specific flag; if the system does not have an NVIDIA GPU or the `mp4` format does not use NVENC, this flag may be passed to libx264 which does not understand it. This could be a secondary cause of encode failure independent of FIND-001.

**How to get**: Comment out or empty the `additional_flags` line, retry the export.

---

## Category D: Output Path Analysis

### D8. Expected output file path
**What it is**: The exact filesystem path that webm.lua would construct for the output file, given the source filename and template.

**Why it's needed**: Confirms whether the output directory is writable and whether path length could be a problem (Windows MAX_PATH = 260 characters).

**Expected output path** (based on `output_template = "%F-[%s-%e]%M"` and typical usage):
```
D:\ProgramData\asus\New folder\Tulsa-Union-High-Sch001-[00:00:00.000-00:00:10.000].mp4
```
(Colons in time strings are stripped by `format_filename` via `[<>:"/\\|?*]` → `""` replacement, so the actual path uses dots: `Tulsa-Union-High-Sch001-[00.00.00.000-00.00.10.000].mp4`)

**Check**: Is `D:\ProgramData\asus\New folder\` writable by your Windows user account?
Run: `icacls "D:\ProgramData\asus\New folder"` and confirm write permission.

Also check total path length. If the full output path exceeds 260 characters, the write will fail silently. Count: if `Tulsa-Union-High-Sch001-...` is very long, this may apply.

---

## Category E: mpv Verbose Log

### E9. mpv verbose log capturing the encode command line
**What it is**: The mpv log file showing the exact command line that webm.lua assembles and passes to subprocess_detached.

**Why it's needed**: At L1855, the script logs: `msg.verbose("Command line:", table.concat(command, " "))`. This line shows the **exact** ffmpeg invocation including all flags. If FIND-001 is the cause, the log will show `--ovcopts-add=minrate=nilk`. If a different issue is the cause, the actual flags reveal it.

**How to get**:
1. Add to `%APPDATA%\mpv\mpv.conf`:
   ```
   log-file=C:\Users\Public\mpv-log.txt
   msg-level=webm=verbose
   ```
2. Restart mpv, attempt the export
3. Open `C:\Users\Public\mpv-log.txt` and search for `Command line:`
4. Share the line that starts with `[webm] Command line:`

---

## Category F: Before/After Isolation Tests

### F10. Different source file test
**What it is**: Attempt the same export with a different, known-good short video clip (e.g., a 30-second MP4 from a different source).

**Why it's needed**: Rules out source-file-specific issues (e.g., the source `Tulsa-...` file has an unusual codec, container, or metadata that confuses webm.lua's track selection logic).

**How to get**: Download any short MP4 test clip, load it in mpv, perform the same export with the same webm.conf settings.

---

### F11. Different output format test
**What it is**: Change `output_format=webm-vp8` in webm.conf and attempt the same export.

**Why it's needed**:
1. Rules out mp4-specific muxer issues.
2. `webm-vp8` does not use libx264, so the `cq-level=28` flag in `additional_flags` would not apply — this helps isolate whether the `additional_flags` are contributing.
3. `webm-vp8` with `strict_filesize_constraint=yes` would still trigger FIND-001, but the error message from ffmpeg/libvpx may be different and more diagnostic.

**How to get**: Change `output_format=webm-vp8` in webm.conf, retry export.

---

## Priority Order for Requesting Information

For a minimal diagnostic cycle, ask in this order:

1. **C6** — Test with `strict_filesize_constraint=no`. This is the fastest single test; if it succeeds, FIND-001 is confirmed and no further diagnosis is needed.
2. **A2** — Output file size after pressing W. Quick to check; immediately distinguishes "encode never ran" from "encode ran and failed mid-write."
3. **E9** — mpv verbose log with `msg-level=webm=verbose`. Definitive; shows the exact bad flag in the command line.
