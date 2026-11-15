# 08 — mpv Integration Surface

**Source hash**: sha256:3f454dc0ca030b591d659f7405a3ddfdf7585e5b5eb4cd5b3a573b4151b33214
**Generation date**: 2026-11-15

See `re-workspace/guilds/mpv-surface/mpv-surface.md` for the complete API inventory. Summary:

## Key Bindings
- `mp.add_key_binding(W, "display-webm-encoder", ...)` — entry point (non-forced)
- `mp.add_forced_key_binding(key, key, fn, {repeatable=true})` — all in-page keys

## Events
- `mp.register_event("file-loaded", ...)` — auto-sets start/end times

## Script Messages
- `mp.register_script_message("mpv-webm-set-options", test_set_options)` — IPC handler

## Observed Properties (13 total persistent + per-page)
Video geometry (11 via monitor_dimensions) + OSD size (2 via Page.observe_properties).

## Properties Read (34 unique)
Includes: video-out-params, track-list, path, vf, brightness/contrast/saturation, sub-*, speed, time-pos, duration, etc.

## Properties Set (3)
vf, time-pos, pause — all only by PreviewPage (restored on hide).

## Subprocess Functions
- `mp.utils.subprocess` (safe argv mode)
- `mp.utils.subprocess_detached` (async mode)
- `mp.utils.parse_json`, `mp.utils.file_info`, `mp.utils.join_path`, `mp.utils.split_path`
- `io.popen` (shell string mode, for progress display)
