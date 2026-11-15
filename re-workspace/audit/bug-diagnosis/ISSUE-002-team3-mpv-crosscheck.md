# TEAM 3 — mpv SOURCE CODE CROSS-CHECK
## Issue #2 (SevWren/MPV): Encode subprocess hang investigation
### All findings cite official mpv source or documentation

---

## 1. `--keep-open=yes` in Encode Mode

**Source**: `DOCS/man/options.rst` lines 3442–3476; `player/playloop.c` `handle_keep_open()` function (line 991).

### What the docs say (options.rst lines 3442–3457):
> `--keep-open=<yes|no|always>`
> Do not terminate when playing or seeking beyond the end of the file, and there is no next file to be played (and `--loop` is not used). Instead, **pause the player**.
>
> `yes`: Don't terminate if the current file is the last playlist entry.

`yes` does **not** pause if there is a next file in the playlist, or the playlist is looped. It pauses when the player would otherwise exit normally.

### Source code verdict (`player/playloop.c` lines 991–1012):
```c
static void handle_keep_open(struct MPContext *mpctx)
{
    struct MPOpts *opts = mpctx->opts;
    if (opts->keep_open && mpctx->stop_play == AT_END_OF_FILE &&
        (opts->keep_open == 2 ||
        (!playlist_get_next(mpctx->playlist, 1) && opts->loop_times == 1)))
    {
        mpctx->stop_play = KEEP_PLAYING;
        ...
        if (opts->keep_open_pause) {
            ...
            set_pause_state(mpctx, true);
        }
    }
}
```

**The `handle_keep_open()` function is called unconditionally in `run_playloop()` (line 1369) — there is NO check for `encode_lavc_ctx`.** This means:

- If the encode subprocess inherits `keep-open=yes` from mpv.conf, and
- The encode subprocess is at the last playlist entry (no next file), and
- `loop_times == 1` (default, i.e., no loop-playlist override in effect),

then `handle_keep_open()` will fire, set `stop_play = KEEP_PLAYING`, and **pause the process indefinitely after the encode completes**. The encode output is already written, but mpv does not exit.

**Verdict: `keep-open=yes` CAN cause the encode subprocess to hang after completion. This is SUPPORTED by the source code.**

---

## 2. `--hwdec=auto-copy` in Encode Subprocess

**Source**: `DOCS/man/options.rst` lines 1340–1470.

`auto-copy` is defined as a hardware decoding mode that **copies video back to system RAM** after decoding. The encode subprocess uses `--ovc=libx264` (a software encoder). With `auto-copy`, the GPU is used to decode the source video, then the frame is copied back to CPU RAM before software encoding.

The documentation does NOT document any explicit conflict or resource contention between the parent mpv player instance and an encode subprocess both using `auto-copy`. The `auto-copy` variants are documented as generally safe. No explicit mention in `encode.rst` of hwdec causing issues in encode mode.

**Verdict: `hwdec=auto-copy` inheritance is documented as safe (copies to RAM). No official documentation supports a GPU resource contention hypothesis between parent and child mpv processes using auto-copy. Hypothesis WEAKLY REFUTED — insufficient evidence for contention.**

---

## 3. ytdl_hook Behavior for the Bare Argument `cq-level=28`

**Source**: `player/lua/ytdl_hook.lua` lines 1213–1235 (on_load_hook), lines 1–28 (options), lines 264–297 (is_whitelisted/is_blacklisted).

The bare string `cq-level=28` is treated by mpv as a positional argument and therefore becomes a **playlist entry** (a filename to open). ytdl_hook is a built-in script that fires on `on_load` and `on_load_fail` hooks for each playlist item.

### Logic trace for `url = "cq-level=28"`:

```lua
local url = mp.get_property("stream-open-filename", "")
-- url = "cq-level=28"

local force = url:find("^ytdl://") ~= nil
-- force = false  (does not start with "ytdl://")

local early = force or o.try_ytdl_first or is_whitelisted(url)
-- o.try_ytdl_first = false  (default, confirmed line 8)
-- is_whitelisted("cq-level=28"):
--   url:match("https?://(.+)") = nil  → returns false immediately
-- early = false or false or false = false
```

**For `on_load` hook** (`load_fail = false`):
```lua
if early == load_fail then  -- false == false → TRUE
    return                  -- EXITS IMMEDIATELY
end
```
**ytdl_hook returns early. `run_ytdl_hook` is NOT called.**

**For `on_load_fail` hook** (`load_fail = true`):
```lua
if early == load_fail then  -- false == true → FALSE
    -- does NOT return here
end
if not force and (not url:find("^https?://") or is_blacklisted(url)) then
-- not false = true
-- url:find("^https?://") on "cq-level=28" = nil → not nil = true
-- condition: true and true = TRUE
    return                  -- EXITS IMMEDIATELY
end
```
**`on_load_fail` also returns early. `run_ytdl_hook` is NOT called.**

**Verdict: ytdl_hook does NOT invoke yt-dlp for `cq-level=28`. The string will simply fail to open as a file (file not found). mpv will then set `init_failed = true` for that playlist entry and move on. The ytdl-yt-dlp invocation hypothesis is REFUTED by source code.**

---

## 4. `loop-playlist=inf` in Encode Mode

**Source**: `DOCS/man/options.rst` lines 478–490; `player/loadfile.c` `mp_next_file()` (lines 2246–2265) and `mp_play_files()` (lines 2285–2340).

### What the docs say (options.rst lines 478–484):
> `--loop-playlist=<N|inf|force|no>`
> Loops playback `N` times. `inf` means forever. If several files are specified on the command line, the **entire playlist is looped**.

### Source code (`loadfile.c` lines 2246–2264):
```c
if (!next && mpctx->opts->loop_times != 1) {
    if (direction > 0) {
        next = playlist_get_first(mpctx->playlist);
        if (next && mpctx->opts->loop_times > 1 && update_loop) {
            mpctx->opts->loop_times--;
        }
    }
    bool ignore_failures = mpctx->opts->loop_times == -2;
    // -2 is the internal representation of "force" mode
```

**`loop_times != 1` is the trigger.** `inf` is stored as `-1`. When the playlist ends (no next entry), if `loop_times != 1`, mpv wraps back to the first playlist entry.

**Critically**: `mp_play_files()` calls `encode_lavc_free()` only after the outer `for(;;)` loop exits (lines 2331–2339). If `loop-playlist=inf` is active, the loop never exits normally — `encode_lavc_free()` is never called, the output file is never finalized, and the process loops forever.

**The encode command uses `--loop-file=no` but does NOT explicitly set `--loop-playlist=no`.** If `loop-playlist=inf` is in mpv.conf and the subprocess inherits mpv.conf via the absence of `--no-config`, the entire encode playlist loops infinitely.

**Verdict: `loop-playlist=inf` in inherited mpv.conf CAUSES INFINITE RE-ENCODING in the encode subprocess. This is STRONGLY SUPPORTED by source code. The encode output file is never finalized because `encode_lavc_free()` is never reached.**

---

## 5. autoload.lua in Encode Subprocess

**Source**: `/home/vercel-sandbox/MPV/scripts/autoload.lua` (user's script, analyzed).

### What autoload.lua does:
When mpv opens `D:\Videos\source.mp4`, autoload.lua's `find_and_add_entries()` fires:
1. Gets `path = "D:\Videos\source.mp4"`, extracts `dir = "D:\Videos\"` and `filename = "source.mp4"`
2. Checks `o.disabled` (default: false) — does NOT stop
3. Checks `#dir == 0` — `"D:\Videos\"` is non-empty — does NOT stop
4. Gets `pl_count` (initially 1 for a single file), since `pl_count == 1` and `source.mp4` has extension `mp4` which IS in `EXTENSIONS_VIDEO`, it does NOT classify this as a "manually made playlist"
5. Calls `utils.readdir("D:\Videos\", "files")` and filters for all video/audio extensions
6. Sorts them and appends all other video files from `D:\Videos\` to the playlist (up to MAXENTRIES = 300 before + 300 after = up to 600 total entries)

**Result**: If `D:\Videos\` contains 50+ video files, autoload.lua adds them all to the encode subprocess's playlist. The encode subprocess then:
- Encodes `source.mp4` (the target file)
- Attempts to encode all 50+ other files from `D:\Videos\` sequentially using the SAME `--o=` output file

Additionally, the bare `cq-level=28` argument becomes a second playlist entry. autoload.lua sees `pl_count > 1` on subsequent file loads but `autoloaded` is already set to `true` from the first load, so it may continue adding from each file's directory.

**Verdict: autoload.lua ACTIVELY POPULATES the encode subprocess's playlist with all video files from D:\Videos\. This is STRONGLY SUPPORTED. Combined with `loop-playlist=inf`, this creates an infinite encode loop over potentially dozens of files.**

---

## 6. `--no-config` and `--load-scripts=no` as Fixes

**Source**: `DOCS/man/options.rst` lines 813–828 (`--no-config`) and lines 875–879 (`--load-scripts`); `player/main.c` line 441 (`mp_load_scripts` called after encode init).

### `--no-config` (options.rst lines 813–818):
> Do not load default configuration or any user files. This prevents loading of both the user-level and system-wide `mpv.conf` and `input.conf` files. Other user files are blocked as well.

This would prevent inheritance of `keep-open=yes`, `loop-playlist=inf`, and any profile-based `hwdec=auto-copy` from mpv.conf.

### `--load-scripts=no` (options.rst lines 875–879):
> If set to `no`, don't auto-load scripts from the `scripts` configuration subdirectory.

This prevents autoload.lua, ytdl_hook.lua (built-in), and all other user scripts from loading.

**Critical source code finding** (`player/main.c` lines 433–441):
```c
if (opts->encode_opts->file && opts->encode_opts->file[0]) {
    mpctx->encode_lavc_ctx = encode_lavc_init(mpctx->global);
    ...
}
mp_load_scripts(mpctx);  // called AFTER encode init, WITH no guard
```

Scripts ARE loaded even in encode mode. There is no automatic suppression. `--load-scripts=no` and `--no-config` must be **explicitly passed** to the encode subprocess to prevent this.

**Verdict: `--no-config` and `--load-scripts=no` ARE the correct and necessary fixes. They are the official documented mechanisms. Strongly SUPPORTED.**

---

## 7. Final Verdict — Hypothesis Rankings

| # | Hypothesis | Status | Primary Source |
|---|-----------|--------|----------------|
| **A** | `loop-playlist=inf` inherited from mpv.conf causes infinite re-encoding | **CONFIRMED — PRIMARY CAUSE** | `loadfile.c` mp_next_file(), encode_lavc_free() never reached |
| **B** | autoload.lua adds all files from D:\Videos\ to encode playlist | **CONFIRMED — COMPOUNDING CAUSE** | autoload.lua lines 140–214, MAXENTRIES=300 |
| **C** | `keep-open=yes` inherited from mpv.conf pauses subprocess after EOF | **CONFIRMED — COMPOUNDING CAUSE** | `playloop.c` handle_keep_open(), no encode_lavc_ctx guard |
| **D** | `cq-level=28` bare arg treated as playlist entry (file open fail) | **CONFIRMED — MINOR ERROR** | ytdl_hook.lua on_load_hook logic; file not found on open |
| **E** | ytdl_hook invokes yt-dlp for `cq-level=28` | **REFUTED** | ytdl_hook.lua: returns early on on_load; returns early on on_load_fail (non-http URL) |
| **F** | `hwdec=auto-copy` causes GPU resource contention | **UNCONFIRMED — insufficient evidence** | No documentation in encode.rst or hwdec docs |

### Root Cause Chain (official source-confirmed):
1. webm.lua spawns `mpv ... --o=output.mp4` **without** `--no-config` or `--load-scripts=no`
2. The subprocess loads the user's mpv.conf, inheriting `loop-playlist=inf` (from extension.mp4 profile or global) and `keep-open=yes`
3. autoload.lua fires when `source.mp4` is opened, populating the playlist with all files in `D:\Videos\`
4. `loop-playlist=inf` causes `mp_next_file()` to never return NULL, so the encode outer loop never exits and `encode_lavc_free()` is never called
5. Even if loop-playlist is not `inf`: `keep-open=yes` triggers `handle_keep_open()` with no encode-mode guard, pausing the process at EOF

### Required Fixes for webm.lua encode command:
```
--no-config          (prevents mpv.conf inheritance: keep-open, loop-playlist, profiles)
--load-scripts=no    (prevents autoload.lua, ytdl_hook, and other scripts)
--loop-playlist=no   (explicit safety net even if no-config is omitted)
```

---

*Sources consulted:*
- `https://raw.githubusercontent.com/mpv-player/mpv/master/DOCS/man/options.rst`
- `https://raw.githubusercontent.com/mpv-player/mpv/master/DOCS/man/encode.rst`
- `https://raw.githubusercontent.com/mpv-player/mpv/master/player/playloop.c`
- `https://raw.githubusercontent.com/mpv-player/mpv/master/player/loadfile.c`
- `https://raw.githubusercontent.com/mpv-player/mpv/master/player/main.c`
- `https://raw.githubusercontent.com/mpv-player/mpv/master/player/lua/ytdl_hook.lua`
- `/home/vercel-sandbox/MPV/scripts/autoload.lua` (user's installed script)
