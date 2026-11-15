# Adversarial Code Review — webm.lua patch set

Reviewer: adversarial static-analysis agent
Date: 2026-11-15
Subject file: `/home/vercel-sandbox/MPV/scripts/webm.lua`

---

## Change 1 — FIND-003: `output_format = "mp4"` (was `"mp4 (h264/AAC)"`)

**Exact location**: L17 in the `options` table.

**What changed**: The default value of `output_format` was shortened from the human-readable string `"mp4 (h264/AAC)"` to the registry key `"mp4"`.

**Adversarial challenge**: A user who previously relied on the script-opts default or who had `output_format=mp4 (h264/AAC)` in their `script-opts/webm.conf` will now have a **nil format** at runtime because `formats["mp4 (h264/AAC)"]` does not exist in the registry. The encode function does `local format = formats[options.output_format]` with no nil-guard, so if `options.output_format` is an unrecognised key the script will crash with `attempt to index a nil value`.

**Rebuttal**: The `formats` table (verified in source) registers keys `"raw"`, `"webm-vp8"`, `"webm-vp9"`, `"mp4"`, `"mp4-nvenc"`, `"mp3"`, `"gif"`. The old default `"mp4 (h264/AAC)"` was never a valid registry key — it was a display name mismatch that made the _default_ crash silently. The fix is therefore necessary and correct. Users with `output_format=mp4 (h264/AAC)` in script-opts had a broken config already; they are no better or worse off.

**Verdict**: SAFE

**Edge cases**: Any external script or user config that sets `output_format` to a value not in the registry will produce a nil-dereference in `encode()`. A guard (`if not format then message("Unknown output_format: " ...) return end`) would make the failure user-friendly but is out of scope for this fix.

---

## Change 2 — FIND-012: subprocess isolation flags added before `path`

**Exact location**: L1715–1728 (`local command = { ... }`).

**What changed**: Six isolation flags (`--no-config`, `--load-scripts=no`, `--keep-open=no`, `--loop-playlist=no`, `--hwdec=no`, `--save-position-on-quit=no`) were inserted between `"mpv"` and `path` in the command array.

**Adversarial challenge**: mpv processes command-line arguments in order. Options that appear after a bare filename argument are typically still accepted by mpv (it does not use `--` to terminate the option list), but `--no-config` specifically must appear before mpv loads its config. Because it precedes `path` in the array, it fires before the input file is processed — this is correct.

**Rebuttal**: Verified in source: array order is `"mpv"`, six flags, then `path` (L1716–1723). mpv's `--no-config` before the input path is the correct placement and is documented behaviour. All other flags (`--keep-open=no` etc.) override the user's `mpv.conf` which sets `keep-open=yes`, `save-position-on-quit=yes`, `hwdec=auto-copy` — without these overrides the encode subprocess would inherit those settings and potentially hang or write resume data.

**Verdict**: SAFE

**Edge cases**:
- `--hwdec=no` forces software decode. For users on low-end CPUs encoding very long clips, this could make encode significantly slower. There is no option to override this in `additional_flags` safely (you could pass `--hwdec=auto` via `additional_flags` but the validation loop accepts any `--` prefixed token, so a user could do it deliberately).
- `--no-config` also suppresses any user encode-specific settings in `mpv.conf` that the user might intentionally want applied during encoding (e.g., custom video filters). This is a **regression risk** — see regression section below.

---

## Change 3 — FIND-012 (prior commit): `additional_flags` token validation

**Exact location**: L1804–1818.

**What changed**: Both `additional_flags` and `non_strict_additional_flags` loops now skip tokens that do not start with `--`, logging a `msg.warn`.

**Adversarial challenge**: The validation `token:sub(1, 2) == "--"` is a prefix check only. A token like `"--; rm -rf ~"` would pass validation and be passed directly to mpv as an argument. However, since the command is passed as an array to `subprocess` (not a shell), shell injection is not possible — each token is a separate argv element.

**Rebuttal**: The check is correct for its stated purpose: preventing accidental positional arguments (e.g., a bare filename or a flag without `--`) from being injected. Shell injection is not relevant here because mpv subprocess calls use an argument array, not a shell string.

**Verdict**: SAFE

**Edge cases**: Users who had non-`--` tokens in `additional_flags` (e.g., bare `cq-level=28` without the leading `--`) will now silently skip those tokens. `non_strict_additional_flags` defaults to `"cq-level=28"` — this default itself would be **skipped** because it lacks `--`. Verified in source: the actual default in L24 is `"cq-level=28"` without `--`. This means the default non_strict flag is now always silently dropped. This is a **latent regression** unless the fix is considered intentional (a bare `cq-level=28` was never a valid mpv flag anyway — the correct form is `--ovcopts-add=cq-level=28`). However it represents a silent behaviour change.

---

## Change 4 — FIND-001: `bitrate` → `video_bitrate` (L1793–1794)

**Exact location**: L1793–1794 in the strict filesize constraint block.

**What changed**: `tostring(bitrate)` → `tostring(video_bitrate)` for both `minrate` and `maxrate` codec options.

**Adversarial challenge**: Was `bitrate` ever defined in this scope? If not, the original code produced a silent `nil` for both minrate and maxrate, meaning the strict constraint was completely non-functional — not a crash, but an undetected logic error. The fix substitutes `video_bitrate` which is computed three lines above at L1779.

**Rebuttal**: Confirmed in source: `local video_bitrate, audio_bitrate = calculate_bitrate(...)` is at L1779. The scope is correct — `video_bitrate` is a local in the same `if options.target_filesize > 0 then` block. The original `bitrate` was an undefined local that resolved to `nil`, making `tostring(nil)` produce `"nil"` and generate an invalid ffmpeg option string. Fix is correct.

**Verdict**: SAFE

**Edge cases**: `video_bitrate` can be `nil` if `calculate_bitrate` returns nil for video (e.g., audio-only encode). The inner `if video_bitrate then` guard at L1780 wraps the main bitrate assignment but the `strict_filesize_constraint` block at L1790 uses `video_bitrate` without an additional nil check. If `video_bitrate` is nil and strict mode is on for an audio-only encode, `tostring(nil)` → `"nil"` produces `--oacopts-add=minrate=nilk` — an invalid option. This is a pre-existing edge case not introduced by the fix.

---

## Change 5 — FIND-004: `reversed_binary_duration` → `big_endian_binary_duration`

**Exact location**: L627 (`get_duration` method of `FirstpassStats`).

**What changed**: The local variable name used in the call to `read_double()` was corrected from `reversed_binary_duration` (undefined) to `big_endian_binary_duration` (defined one line above at L627).

**Adversarial challenge**: Was this variable ever used elsewhere under its old name? Could there be two different variables — one called `reversed_binary_duration` and one called `big_endian_binary_duration` — serving different purposes?

**Rebuttal**: Text search confirms `reversed_binary_duration` appears zero times in the patched file. The variable `big_endian_binary_duration` is set by `reverse(self.binary_duration)` at L627, then passed to `read_double()`. `reverse()` converts little-endian to big-endian order. The semantics are identical — the old name was just wrong. The companion `set_duration` method at L631 correctly names its local `big_endian_binary_duration` — this fix aligns `get_duration` to use the same naming convention.

**Verdict**: SAFE

**Edge cases**: None. The fix is a pure rename of a local variable within a single function body.

---

## Change 6 — FIND-006: IPC handler allowlist validation

**Exact location**: L67–81 (`test_set_options` function).

**What changed**: Added `if options[k] ~= nil then` check before assigning `options[k] = v`, with an `else msg.warn(...)` branch for unknown keys. Also added `type(new_options) ~= "table"` JSON validation.

**Adversarial challenge**: The allowlist check `options[k] ~= nil` relies on the `options` table itself as the allowlist. Any key with a falsy value (`false` or `0`) would have `options[k] ~= nil` return `true`, so those are still correctly accepted. The concern is whether a key that is legitimately `nil` in `options` (there are none — all defaults are non-nil) could be a valid key that gets blocked.

**Rebuttal**: All keys in the `options` table have non-nil defaults. The check correctly rejects keys not present in `options`. The `type(new_options) ~= "table"` guard handles malformed JSON gracefully. `options[k] = v` is still reached for valid keys, confirmed in source at L76.

**Verdict**: SAFE

**Edge cases / Regression risk**: Any external script that previously relied on `test_set_options` to inject **arbitrary** keys into the `options` table (e.g., as a side-channel for custom data) will now be silently rejected. This is a breaking change for such scripts, but those scripts were relying on undefined/unsafe behaviour. See regression section.

---

## Change 7 — FIND-007: cleanup before `subprocess_detached`

**Exact location**: L1878–1886.

**What changed**: `os.remove(get_pass_logfile_path(out_path))` and the `is_temporary` / `os.remove(path)` block were moved to execute BEFORE `utils.subprocess_detached(...)` returns. Previously these cleanups only occurred in the synchronous (non-detached) code path.

**Adversarial challenge**: Is `out_path` in scope at L1879? Could the `get_pass_logfile_path(out_path)` call happen before `out_path` is defined?

**Rebuttal**: `local out_path = utils.join_path(dir, formatted_filename)` is at L1836. The `if options.run_detached then` block starts at L1878. Sequential Lua execution guarantees `out_path` is defined. Test `test_out_path_defined_before_cleanup` confirms this via source position comparison.

**Additional concern**: `os.remove(get_pass_logfile_path(out_path))` in the detached path removes the pass-1 log file BEFORE the detached process runs. If the encode was two-pass, the detached process needs the log from pass-1 to do pass-2. However, inspection of the two-pass logic (L1841–1873) shows that two-pass runs the first pass synchronously (via `run_subprocess`, L1858), then sets `--ovcopts-add=flags=+pass2` on the command. The pass-1 log is written and immediately consumed within the synchronous `encode()` call. The `os.remove` at L1879 therefore only cleans up the residual log file after both passes have completed (or after a one-pass detached encode). This is correct.

**Verdict**: SAFE

**Edge cases**: If twopass is true AND run_detached is true, the first-pass runs synchronously before the `run_detached` branch. The cleanup removes the now-stale log before the second-pass subprocess is detached. This is correct — the second-pass log is embedded in the command via `--ovcopts-add=flags=+pass2`, not via the log file at that point.

---

## Change 8 — FIND-010: `originalProperties` capture moved to `prepare()`

**Exact location**: L2570–2575 (new `prepare()` body) and L2624 (`__init` sentinel).

**What changed**: In `PreviewPage.__init`, `self.originalProperties = {}` (empty sentinel). In `prepare()`, it is overwritten with actual live mpv property values (`vf`, `time-pos`, `pause`).

**Adversarial challenge**: Is there any code path where `dispose()` is called WITHOUT `prepare()` having been called first? If so, `dispose()` would iterate an empty `originalProperties` table and NOT restore `vf`, `time-pos`, or `pause`, leaving the player in a modified state.

**Rebuttal**: The `Page` base class (L1286–1305) guarantees: `show()` calls `prepare()` before returning; `hide()` checks `if not self.visible then return end`. Since `hide()` only proceeds when `visible == true`, and `visible` is only set to `true` inside `show()` (which always calls `prepare()` first), `dispose()` can only be reached after `prepare()` has run. The `self.originalProperties = {}` sentinel in `__init` is a safe default that simply means "nothing to restore" if the impossible path were reached.

**Verdict**: SAFE

**Edge cases**: If `prepare()` is called multiple times (e.g., via multiple `show()` calls without an intervening `hide()`), `show()` has an early-return guard `if self.visible then return end`, so double-prepare cannot occur. The fix is robust.

---

## Regression Analysis

### Regression 1: `output_format = "mp4"` default change

**Risk**: Users who had `output_format=mp4 (h264/AAC)` in their `script-opts/webm.conf` will get a nil-dereference crash in `encode()` because `formats["mp4 (h264/AAC)"]` does not exist. However, those users were already broken since `"mp4 (h264/AAC)"` was never a valid registry key — the old default was itself buggy. Net regression risk: **LOW** (pre-existing broken configs remain broken; previously working configs are now fixed).

### Regression 2: IPC allowlist blocks external scripts

**Risk**: External scripts that call `script-message mpv-webm-set-options` with custom/unknown keys to pass data into the webm script will now have those keys silently dropped with a warning. Any script that relied on the previous "accept any key" behaviour as a data-injection mechanism is broken. **Mitigation**: The warning via `msg.warn` makes the failure visible. **Risk level**: MEDIUM for unusual integrations.

### Regression 3: `--no-config` suppresses user encode settings

**Risk**: If a user added encode-specific settings to their `mpv.conf` (e.g., a custom `vf=` chain or `lavfi-complex` filter for encoding), those settings are now completely ignored because `--no-config` is passed to the encode subprocess. The user has no supported way to inject config-file settings into the encode process. **Mitigation**: The user can still use `additional_flags` to pass individual options. **Risk level**: MEDIUM for power users who customised encode behaviour via mpv.conf profiles.

### Regression 4: `non_strict_additional_flags` default value silently dropped

**Risk**: The default value of `non_strict_additional_flags` is `"cq-level=28"` (L24). After the `--` prefix validation change, this token is skipped because it lacks a `--` prefix. Users who relied on the default CQ level being applied to non-strict encodes will silently lose that setting. This is a silent quality regression for all VP8/VP9 encodes using default settings. **Risk level**: HIGH — this silently changes encode quality for all users who have not overridden `non_strict_additional_flags`. The correct fix would be to either update the default to `"--ovcopts-add=cq-level=28"` or to treat the default value as a special case. This should be flagged for rework.

---

## Summary Table

| Change | Verdict | Key concern |
|--------|---------|-------------|
| FIND-003: output_format default | SAFE | Pre-existing breakage for invalid configs |
| FIND-012: subprocess isolation flags | SAFE | --no-config suppresses user mpv.conf encode settings (regression) |
| FIND-012: additional_flags validation | NEEDS_REWORK | Default `non_strict_additional_flags="cq-level=28"` is now silently dropped |
| FIND-001: bitrate -> video_bitrate | SAFE | Pre-existing nil edge case for audio-only strict encodes |
| FIND-004: big_endian_binary_duration | SAFE | None |
| FIND-006: IPC allowlist | SAFE | Breaks external scripts injecting unknown keys |
| FIND-007: cleanup before detached | SAFE | Interaction with twopass+detached verified correct |
| FIND-010: originalProperties in prepare | SAFE | Empty sentinel safe; show/hide lifecycle enforces correct order |
