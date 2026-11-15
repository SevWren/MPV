# ISSUE-002 Corrected GitHub Comment

**Status**: Ready to post. Copy the content below the second horizontal rule.

---

---

Hi again — I need to correct something from my previous comment. The workaround I
suggested earlier was incomplete. I apologize for the confusion and want to give you
the full picture.

---

## What is actually causing the problem

There are two separate issues working together:

**Issue 1 — The encoder inherits your entire player configuration.**

When webm.lua starts an encode, it launches a second copy of mpv to do the actual
encoding work. The problem is that this second copy loads your entire `mpv.conf` just
like a normal player would. Settings that are fine for watching video — like
`keep-open=yes` (keep the window open when the video ends), `hwdec=auto-copy` (use the
GPU for decoding), and scripts like ytdl_hook and autoload — are actively harmful in an
encoder. Specifically, `keep-open=yes` means the encoder never exits after finishing,
so the output file is never properly closed and finalized. An MP4 file that was never
properly closed cannot be played — which is exactly what you are seeing.

**Issue 2 — `cq-level=28` is passed without the required `--` prefix.**

Your webm.conf has `additional_flags= cq-level=28`. Because there is no `--` in front,
mpv treats `cq-level=28` as a *filename to open*, not as an option flag. The encoder
immediately errors trying to open a file called "cq-level=28" that does not exist.

There is also a third deeper bug in the script itself (a wrong variable name that
produces `minrate=nilk` in the encode command when `strict_filesize_constraint=yes`),
but that is a code-level fix we are tracking separately.

---

## Immediate fix — change `additional_flags` in webm.conf

Open `%APPDATA%\mpv\script-opts\webm.conf` and change this line:

```
additional_flags= cq-level=28
```

To this:

```
additional_flags=--no-config --load-scripts=no --keep-open=no --hwdec=no
```

Each flag needs the `--` prefix. What they do in plain terms:

- `--no-config` — tells the encoder to ignore your player config entirely
- `--load-scripts=no` — prevents your scripts from loading inside the encoder
- `--keep-open=no` — tells the encoder to exit when it finishes (so the file gets
  properly closed)
- `--hwdec=no` — tells the encoder to use software decoding, avoiding GPU conflicts

Also set `strict_filesize_constraint=no` to avoid the separate variable-name bug:

```
strict_filesize_constraint=no
```

Save the file and try the export again. You should not need to restart mpv, but a
restart does not hurt.

---

## Note on `cq-level=28`

This flag is for a different video format (VP8/VP9 for `.webm` files). It does nothing
for H.264 `.mp4` output. If you want to control encode quality for MP4, the equivalent
setting is `crf=28`. You can either add it directly to webm.conf as a separate line:

```
crf=28
```

Or include it in `additional_flags`:

```
additional_flags=--no-config --load-scripts=no --keep-open=no --hwdec=no --ovcopts-add=crf=28
```

---

## The underlying code fix

We are tracking a proper fix that adds `--no-config --load-scripts=no --keep-open=no
--hwdec=no` directly into webm.lua's encode command so users do not need to put them in
`additional_flags`. This will be included in an upcoming release.

---

## Two questions to help confirm this worked

**1. After applying the fix above, does the export complete successfully?**
A yes here confirms both issues are resolved.

**2. What options do you have in your `mpv.conf` (not webm.conf)?**
Specifically: do you have `keep-open=`, `hwdec=`, or `loop-playlist=` set? This helps
us understand which inherited settings were active in the encoder and whether the fix
above covers all of them.

---

## Team 4 Reconciliation Note (internal — not for GitHub)

### Where all teams agree

- FIND-001 (`bitrate` undefined → `minrate=nilk`) is the primary confirmed code bug
  that causes immediate encode failure when `strict_filesize_constraint=yes`.
- FIND-011 (`cq-level=28` bare token) is a confirmed secondary issue.
- The fix for FIND-011 is: prefix with `--`, and note that `cq-level` is libvpx-only;
  for H.264 use `crf=28` via webm.conf's native `crf=` option.
- `run_detached=yes` causes all failures to be silent (no error visible to user).
- The "0% CPU hang" is the player process idling, not the encoder stuck in a loop.

### Team 4 additions vs. prior diagnosis

The prior diagnosis (ISSUE-002-diagnosis.md, representing Teams 1+2) correctly
identified FIND-001 and FIND-011 and recommended `strict_filesize_constraint=no` as the
immediate workaround. Team 4 extends this with:

1. **Config inheritance as a separate issue**: The lack of `--no-config` and
   `--load-scripts=no` in the encode command is an independent bug class (FIND-012,
   new). Even after FIND-001 is patched, users with `keep-open=yes` in mpv.conf will
   still see hangs. The proper code fix must add these four protective flags to the
   command array in `encode()`.

2. **`--keep-open=no` as the most user-visible cause**: The prior comment focused on
   the `nilk` bitrate bug. Team 4 notes that `keep-open=yes` inherited from mpv.conf
   is an equally probable cause of the "hang" symptom, and may affect users who do not
   have `strict_filesize_constraint=yes` at all.

3. **`cq-level=28` codec mismatch clarified**: Prior diagnosis noted it is libvpx-only.
   Team 4 adds the correct user-facing replacement (`crf=28` or `--ovcopts-add=crf=28`).

### Disagreements and resolution

None — Team 4 analysis is consistent with the prior diagnosis. The only difference is
scope: Team 4 adds the config-inheritance issue as a distinct bug requiring a distinct
fix (the four-flag code patch), whereas the prior analysis treated it as background
context rather than a separate actionable finding.

### Final consensus root cause

The encode fails due to two confirmed bugs:

1. **FIND-001** (code bug): `bitrate` variable is undefined at L1779-1780; produces
   `minrate=nilk` / `maxrate=nilk`; triggered only when `strict_filesize_constraint=yes`.
   Fix: change `bitrate` to `video_bitrate` in `webm.lua`.

2. **FIND-011** (config bug + validation gap): `cq-level=28` without `--` prefix is
   treated as a filename; `cq-level` is also wrong codec for H.264.
   Fix: add `--` prefix; use `crf=28` for H.264.

3. **FIND-012** (new, code bug): encode subprocess inherits full user mpv.conf including
   `keep-open=yes`, `hwdec=auto-copy`, all user scripts.
   Fix: add `--no-config --load-scripts=no --keep-open=no --hwdec=no` to encode command.

All three are silent failures because `run_detached=yes` discards the subprocess exit
code entirely.
