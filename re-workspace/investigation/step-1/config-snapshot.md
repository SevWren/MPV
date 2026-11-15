# Step 1B — Configuration Snapshot

Source: `/home/vercel-sandbox/MPV/script-opts/webm.conf`

## Every option and its exact value

| Option | Value | Has `--` prefix where flag value expected? |
|--------|-------|---------------------------------------------|
| keybind | W | N/A (string) |
| output_directory | D:\ProgramData\asus | N/A (path) |
| run_detached | yes | No `--` prefix — this is a bare value `yes`, not `--yes`. Correct format for conf file. |
| output_template | %F-[%s-%e]%M | N/A (template) |
| scale_height | -1 | N/A (integer) |
| fps | -1 | N/A (integer) |
| target_filesize | 9800 | N/A (integer) |
| strict_filesize_constraint | yes | N/A (boolean) |
| strict_bitrate_multiplier | 1 | N/A (float) |
| strict_audio_bitrate | 64 | N/A (integer) |
| output_format | mp4 | N/A (string) |
| twopass | no | N/A (boolean) |
| apply_current_filters | no | N/A (boolean) |
| write_filename_on_metadata | no | N/A (boolean) |
| libvpx_threads | 3 | N/A (integer) |
| additional_flags | ` cq-level=28` | **CRITICAL: value is `cq-level=28` (with leading space) — MISSING `--` prefix** |
| crf | -1 | N/A (integer) |
| non_strict_additional_flags | (empty) | N/A |
| display_progress | yes | N/A |
| font_size | 20 | N/A |
| margin | 5 | N/A |
| message_duration | 5 | N/A |
| gif_dither | 2 | N/A |
| force_square_pixels | no | N/A |

## Flag: strict_filesize_constraint
[conf:45] `strict_filesize_constraint=yes`
Value: `yes` (boolean true)

## Flag: run_detached
[conf:13] `run_detached=yes`
Value: `yes` (boolean true) — subprocess is detached, mpv does not wait for it

## Flag: additional_flags — EXACT characters including spaces
[conf:75] `additional_flags= cq-level=28`
Exact value: ` cq-level=28` (one leading space, then `cq-level=28`)
**This token does NOT start with `--`. It is not a valid mpv option.**

## Flag: non_strict_additional_flags
[conf:83] `non_strict_additional_flags=`
Value: empty string `""`

## Critical finding
The `additional_flags` conf value is `cq-level=28` without a `--` prefix.
When parsed by `string.gmatch(options.additional_flags, "[^%s]+")`, the token `cq-level=28` is extracted.
In the **canonical** (pre-patch) webm.lua, this token was passed directly to the command array WITHOUT validation [canonical:1791]: `command[#command + 1] = token`
This bare token appears in the subprocess args at [log:1282] as `args="cq-level=28"`.
