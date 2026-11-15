# 11 — Process and Filesystem Interactions

**Source hash**: sha256:3f454dc0ca030b591d659f7405a3ddfdf7585e5b5eb4cd5b3a573b4151b33214
**Generation date**: 2026-11-15

## Process Execution

### Mode 1: Detached subprocess (default)
- **API**: `mp.utils.subprocess_detached({args=command})`
- **Behavior**: Non-blocking. mpv does not wait for completion.
- **Triggered when**: `options.run_detached = true`
- **Output**: None returned to script.
- **Cleanup bug**: Temp files not cleaned up after return.

### Mode 2: Blocking subprocess
- **API**: `mp.utils.subprocess({args=command, cancellable=false})`
- **Behavior**: Blocking. mpv freezes UI until complete.
- **Triggered when**: `run_detached=false AND display_progress=false` (or Windows auto)
- **Return**: Success bool.

### Mode 3: Progress subprocess (popen)
- **API**: `io.popen(shell_escape(command) .. " 2>&1")`
- **Behavior**: Blocking with line-by-line stderr parsing.
- **Triggered when**: `run_detached=false AND display_progress=true AND non-Windows`
- **Return**: File handle → lines → closed after encode.

## Filesystem Reads

| Path | Function | When |
|------|---------|------|
| media file (path) | Implicit | Every encode |
| VP8 pass1 logfile | read_logfile_into_stats_array | 2-pass WebmVP8 after pass1 |
| Any path | file_exists | Detecting stream vs file |
| `~/.config/mpv/script-opts/webm.conf` | mpopts.read_options | Startup |

## Filesystem Writes

| Path | Function | When |
|------|---------|------|
| `{output_dir}/{filename}.{ext}` | encode output | Every successful encode |
| `{out_path}-video-pass1.log` | First pass log | 2-pass encoding |
| `~/cache_dump.ts` | HLS cache dump | HLS stream encode |

## File Cleanup

| File | Cleaned When |
|------|-------------|
| pass1 logfile | `os.remove` after successful or failed encode (if `run_detached=false`) |
| cache_dump.ts | `os.remove` after encode if `is_temporary=true AND run_detached=false` |

**Note**: Neither file is cleaned when `run_detached=true`.

## mpv IPC

| Message | Direction | Handler | Line |
|---------|-----------|---------|------|
| mpv-webm-set-options | Inbound | test_set_options | L74 |
| webm-encode-started | Outbound | (listeners) | L1818 |
| webm-encode-finished | Outbound | (listeners) | L1875, L1879 |
| webm-show-main-page | Outbound | (listeners) | L2688 |
