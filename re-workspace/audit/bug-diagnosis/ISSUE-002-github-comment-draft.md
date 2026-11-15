# ISSUE-002: GitHub Comment Draft

**Ready to post. Copy the content below the horizontal rule.**

---

---

Thanks for the detailed report and for sharing your `webm.conf`. I can see the issue from the config alone and want to give you an immediate workaround, an explanation of the error, and a couple of follow-up questions to confirm the root cause.

---

## Most Likely Root Cause

Your `webm.conf` has:

```
strict_filesize_constraint=yes
```

There is a confirmed bug in `webm.lua` (tracked internally as FIND-001) that is triggered **only** when this option is enabled. When `strict_filesize_constraint=yes`, the script tries to add `minrate` and `maxrate` flags to the ffmpeg command, but it references an undefined variable (`bitrate`) instead of the correct one (`video_bitrate`). This causes the encode command to include:

```
--ovcopts-add=minrate=nilk
--ovcopts-add=maxrate=nilk
```

`nilk` is not a valid bitrate value. ffmpeg rejects these flags, encounters an error, and exits before it can finish writing the mp4 file.

---

## What "moov atom not found" Means

An mp4 file has a special metadata block called the `moov atom` that is written at the **end** of the encoding process. It contains the index of all the video and audio frames.

If ffmpeg crashes or is killed before finishing, the `moov atom` is never written. The file exists on disk (and may even have video data in it) but it is structurally incomplete — no player can open it. This is why you see "moov atom not found": the file was started but never finished.

---

## Immediate Workaround

Edit `%APPDATA%\mpv\script-opts\webm.conf` and change:

```
strict_filesize_constraint=yes
```
to:
```
strict_filesize_constraint=no
```

Save the file, restart mpv, and try the export again. With `no`, the script skips the broken code path and the encode should complete successfully. The output file size will not be strictly capped to your `target_filesize`, but the encode will work.

---

## A Fix Is Available

A patch that corrects the two affected lines (changing `bitrate` to `video_bitrate`) is tracked in this repository at:

```
re-workspace/deliverables/patches/FIND-001-fix-bitrate-variable.patch
```

The patch is two lines. We will include it in the next release.

---

## Three Follow-Up Questions

To confirm this is definitely FIND-001 and rule out anything else:

**1. Does the export succeed after changing `strict_filesize_constraint=no`?**
This is the fastest confirmation. If yes, FIND-001 is the sole cause and no further diagnosis is needed.

**2. After pressing W with the original config (before the workaround), did a new `.mp4` file appear on disk?**
You can check with: `dir "D:\ProgramData\asus\*.mp4" /T:W /O:D` in cmd.exe. If the file appears but is 0 bytes or very small, that confirms ffmpeg exited immediately after the bad flag. If no file appears, that suggests the error happened even earlier.

**3. Can you share the mpv log around the time you pressed W?**
Add these two lines to `%APPDATA%\mpv\mpv.conf`:
```
log-file=C:\Users\Public\mpv-log.txt
msg-level=webm=verbose
```
Restart mpv, attempt the export, then open `C:\Users\Public\mpv-log.txt` and search for `Command line:`. The line starting with `[webm] Command line:` will show the exact command sent to ffmpeg. If you see `minrate=nilk` in that line, FIND-001 is confirmed. This log is also useful for diagnosing any secondary issues.

---

One additional note: your config also has `additional_flags= cq-level=28` (note the leading space). This is a valid NVENC flag but it is not recognised by the default libx264 encoder used with `output_format=mp4`. Once the `strict_filesize_constraint` workaround is applied, if the encode still fails, try clearing this line to `additional_flags=` and test again.
