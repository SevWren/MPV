# SEG-10 Reconciled Analysis
**Lines**: L1673-1885
**Description**: find_path (HLS cache handling) and encode() — the main encoding orchestration function

## Purpose
`encode()` is the central function of the script. It orchestrates the complete encoding workflow: determining output path, building the mpv command-line, handling 2-pass encoding, dispatching to run_subprocess or EncodeWithProgress, cleaning up temp files, and emitting events.

## Line Walkthrough

### find_path (L1673-1695)
- Gets `mp.get_property('path')`.
- If file doesn't exist on disk: it's a stream.
- For HLS streams: dumps cache to `~/cache_dump.ts`, adjusts startTime/endTime to relative.
- Returns `path, is_stream, is_temporary, startTime, endTime`.

### encode() (L1697-1885)
1. **L1698**: Gets format from `formats[options.output_format]`. If nil → crash.
2. **L1702**: Calls `find_path` for path resolution.
3. **L1707-1714**: Builds base command: `["mpv", path, --start, --end, --loop-file=no, --no-pause]`.
4. **L1715**: Appends codec flags.
5. **L1716-1754**: Appends track selections; appends `--vid/aid/sid=no` for missing track types.
6. **L1755-1757**: Appends video encode flags (filters, playback opts).
7. **L1758**: Appends format-specific flags.
8. **L1759-1761**: Appends metadata flags if write_filename_on_metadata.
9. **L1762-1801**: Bitrate handling: computes bitrate if target_filesize > 0 and format.acceptsBitrate.
   - Strict: also adds minrate/maxrate.
   - Non-strict: appends non_strict_additional_flags (tokenized) and crf.
10. **L1790-1796**: Tokenizes `additional_flags` and `non_strict_additional_flags` by whitespace.
11. **L1803-1817**: Resolves output directory (stream→~, else media dir; override with output_directory). Formats filename. Builds out_path.
12. **L1818**: `emit_event("encode-started")`.
13. **L1819-1851**: 2-pass handling: if twopass+supportsTwopass+not is_stream: copies command, adds +pass1 flag, runs first pass, checks result, adds +pass2 flag, patches VP8 logfile if libvpx.
14. **L1853**: `format:postCommandModifier(command, region, startTime, endTime)`.
15. **L1856-1884**: Dispatch:
    - `run_detached=true`: uses `utils.subprocess_detached`.
    - else if `should_display_progress()=false`: `run_subprocess` (blocking, argv).
    - else: `EncodeWithProgress:startEncode` (blocking, popen, with progress overlay).
16. **L1873-1884**: On success: message + emit_event("encode-finished", "success"). On failure: emit_event("fail"). Cleanup logfile + temp file.

## Edge Cases
- **L1698**: `formats[options.output_format]` — nil if output_format doesn't match any key → `format:getCodecFlags()` crashes.
- **L1779**: References `bitrate` (undefined local in this scope) — should be `video_bitrate`. Bug: strict minrate/maxrate would use an undefined variable.
- **L1856**: When `run_detached=true`, there is NO cleanup of logfile or temp file (early return). The temp `cache_dump.ts` and pass1 logfile are leaked.
- 2-pass not available for streams (`not is_stream` check at L1819).
- `options.additional_flags` with shell metacharacters in `run_subprocess_popen` path — potential command injection via shell escaping.

## Security Notes
- **Medium**: `out_path` comes from user-controlled `output_directory` + `output_template`. If `output_template` expands to `../../../etc/passwd`, the output file could be written to arbitrary locations.
- **Medium**: When `additional_flags` contains flags like `--o=DIFFERENT_PATH`, it could override the output path set at L1816.
