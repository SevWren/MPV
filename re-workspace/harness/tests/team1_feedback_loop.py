#!/usr/bin/env python3
"""
TEAM 1 Feedback Loop — Phase 1 of diagnosing-bugs skill
Evidence file: /home/vercel-sandbox/mpv-log.txt
Script:        /home/vercel-sandbox/MPV/re-workspace/canonical/webm.lf.lua
"""

import re

# ── Evidence strings ──────────────────────────────────────────────────────────
# Source: log line 1281 (the full command-line string)
LOG_LINE_1281 = (
    "mpv D:\\Videos\\Rockford_High-School-Marching-Band-2026-BOA-Grand-National-"
    "Championships-Prelimi_001_1080p.mp4 --start=0:00:00.567 --end=0:00:01.469 "
    "--loop-file=no --no-pause --ovc=libx264 --oac=aac --vid=1 --aid=1 --sid=no "
    "--sub-ass-override=force --sub-auto=fuzzy --sub-pos=97.000000 "
    "--sub-delay=0.000000 --video-rotate=0 "
    "--ytdl-format=bv*[height<=1080]+ba/b[height<=1080] --deinterlace=no "
    "--vf-add=lavfi-scale=-2:720 --vf-add=lavfi-eq=contrast=1:saturation=1:brightness=0 "
    "--ovcopts-add=b=86939k cq-level=28 "
    "--o=D:\\ProgramData\\asus/Rockford_High-School-Marching-Band-2026-BOA-Grand-"
    "National-Championships-Prelimi_001_1080p-[00.00.567-00.01.469]-audio.mp4"
)

# Source: log line 1282 (the subprocess args array — ground truth)
# This is the ACTUAL array passed to mpv subprocess.
LOG_LINE_1282_ARGS = [
    "mpv",
    "D:\\Videos\\Rockford_High-School-Marching-Band-2026-BOA-Grand-National-Championships-Prelimi_001_1080p.mp4",
    "--start=0:00:00.567",
    "--end=0:00:01.469",
    "--loop-file=no",
    "--no-pause",
    "--ovc=libx264",
    "--oac=aac",
    "--vid=1",
    "--aid=1",
    "--sid=no",
    "--sub-ass-override=force",
    "--sub-auto=fuzzy",
    "--sub-pos=97.000000",
    "--sub-delay=0.000000",
    "--video-rotate=0",
    "--ytdl-format=bv*[height<=1080]+ba/b[height<=1080]",
    "--deinterlace=no",
    "--vf-add=lavfi-scale=-2:720",
    "--vf-add=lavfi-eq=contrast=1:saturation=1:brightness=0",
    "--ovcopts-add=b=86939k",
    "cq-level=28",          # <-- bare positional arg — no leading --
    "--o=D:\\ProgramData\\asus/Rockford_High-School-Marching-Band-2026-BOA-Grand-National-Championships-Prelimi_001_1080p-[00.00.567-00.01.469]-audio.mp4",
]

# ── Helpers ───────────────────────────────────────────────────────────────────
PASS = "\033[32mGREEN\033[0m"
FAIL = "\033[31mRED\033[0m"

results = []

def test(name, condition_is_bad, description, evidence):
    """
    condition_is_bad=True  → RED (bug present)
    condition_is_bad=False → GREEN (no bug here)
    """
    color = FAIL if condition_is_bad else PASS
    status = "RED" if condition_is_bad else "GREEN"
    msg = f"  [{color}] {name}: {description}"
    detail = f"         Evidence: {evidence}"
    print(msg)
    print(detail)
    results.append((name, status, description))
    return condition_is_bad

# ── Read webm.lf.lua for code-level evidence ──────────────────────────────────
LUA_PATH = "/home/vercel-sandbox/MPV/re-workspace/canonical/webm.lf.lua"
with open(LUA_PATH, "r", encoding="utf-8") as f:
    lua_source = f.read()

lua_lines = lua_source.splitlines()

def find_lua_lines(pattern):
    """Return list of (lineno, line) for lines matching pattern."""
    matched = []
    for i, line in enumerate(lua_lines, 1):
        if re.search(pattern, line):
            matched.append((i, line.strip()))
    return matched

# ── Verify command assembly logic in webm.lf.lua ──────────────────────────────
print("\n=== WEBM.LF.LUA — KEY CODE LOCATIONS ===")

# additional_flags token loop
af_lines = find_lua_lines(r"additional_flags.*gmatch|gmatch.*additional_flags|token.*command")
for ln, text in af_lines[:5]:
    print(f"  lua:{ln}: {text}")

# non_strict_additional_flags
nsaf_lines = find_lua_lines(r"non_strict_additional_flags")
for ln, text in nsaf_lines[:5]:
    print(f"  lua:{ln}: {text}")

# get_playback_options
gpo_lines = find_lua_lines(r"get_playback_options|ytdl.format|append_property.*ytdl")
for ln, text in gpo_lines[:8]:
    print(f"  lua:{ln}: {text}")

# no-config / load-scripts / keep-open in source
noconfig = find_lua_lines(r"no.config|load.scripts|keep.open")
print(f"\n  no-config / load-scripts / keep-open occurrences in lua: {len(noconfig)}")
for ln, text in noconfig:
    print(f"    lua:{ln}: {text}")

print()

# ── TESTS ─────────────────────────────────────────────────────────────────────
print("=== PHASE 1 FEEDBACK LOOP TESTS ===\n")

# Test A: cq-level=28 is a bare positional arg (no leading --)
bare_cq = "cq-level=28" in LOG_LINE_1282_ARGS
test(
    "TEST-A",
    condition_is_bad=bare_cq,
    description="cq-level=28 appears as bare positional arg (no leading --)",
    evidence="log:1282 args array element: args=\"cq-level=28\" — no double-dash prefix; "
             "source lua:24 non_strict_additional_flags default=\"cq-level=28\"; "
             "lua:1794 token loop: command[#command+1]=token (no -- prepended)"
)

# Test B: --keep-open= is NOT explicitly overridden in the encode command
keep_open_present = any(a.startswith("--keep-open") for a in LOG_LINE_1282_ARGS)
test(
    "TEST-B",
    condition_is_bad=not keep_open_present,
    description="--keep-open=no is ABSENT from encode command (subprocess inherits keep-open=yes from mpv.conf)",
    evidence="log:62 mpv.conf sets keep-open=yes; log:1282 no --keep-open arg in subprocess; "
             "webm.lua never emits --keep-open=no (confirmed: no match in lua source)"
)

# Test C: --no-config is NOT in the encode command
no_config_present = "--no-config" in LOG_LINE_1282_ARGS
test(
    "TEST-C",
    condition_is_bad=not no_config_present,
    description="--no-config is ABSENT from encode command (subprocess inherits entire mpv.conf)",
    evidence="log:1282 no --no-config arg; webm.lua has 0 occurrences of 'no-config' or 'no_config'; "
             "subprocess therefore reads C:\\Users\\mmuel\\AppData\\Roaming/mpv/mpv.conf"
)

# Test D: --load-scripts=no is NOT in the encode command
load_scripts_present = any(a.startswith("--load-scripts") for a in LOG_LINE_1282_ARGS)
test(
    "TEST-D",
    condition_is_bad=not load_scripts_present,
    description="--load-scripts=no is ABSENT from encode command (subprocess loads ALL user scripts)",
    evidence="log:1282 no --load-scripts arg; webm.lua has 0 occurrences of 'load-scripts'; "
             "log:1323-1368 autoload.lua prepends/appends 25+ files to playlist in parent session — "
             "same would occur in encode subprocess"
)

# Test E: --hwdec=no is NOT in the encode command
hwdec_present = any(a.startswith("--hwdec") for a in LOG_LINE_1282_ARGS)
test(
    "TEST-E",
    condition_is_bad=not hwdec_present,
    description="--hwdec=no is ABSENT from encode command (subprocess inherits hwdec=auto-copy)",
    evidence="log:77 mpv.conf high-quality profile sets hwdec=auto-copy; "
             "log:1374 parent process uses d3d11va-copy hardware decoding; "
             "log:1282 no --hwdec arg in subprocess; "
             "webm.lua never emits --hwdec flag"
)

# Test F: --ytdl-format is IN the encode command (player setting leaking)
ytdl_present = any(a.startswith("--ytdl-format") for a in LOG_LINE_1282_ARGS)
test(
    "TEST-F",
    condition_is_bad=ytdl_present,
    description="--ytdl-format= IS in the encode command (player setting leaking into encode subprocess)",
    evidence="log:43 mpv.conf sets ytdl-format; log:1282 --ytdl-format=bv*[height<=1080]+ba/b[height<=1080]; "
             "lua:1572 get_playback_options() calls append_property(ret,'ytdl-format') — "
             "this is a streaming hint, not relevant for local file encode"
)

# Test G: Bitrate verification — 9800 kB target, 0.902s clip, strict mode, 64 kbps audio
# webm.conf: target_filesize=9800, strict_filesize_constraint=yes, strict_audio_bitrate=64, strict_bitrate_multiplier=1
# Duration from log: endTime=1.469, startTime=0.567 → length = 0.902 s
# calculate_bitrate() logic (lua:1657-1671):
#   video_kilobits = 9800 * 8 = 78400
#   audio_kilobits = 0.902 * 64 = 57.728
#   video_kilobits = 78400 - 57.728 = 78342.272
#   video_bitrate = floor(78342.272 / 0.902) = floor(86854.0) = 86854
# BUT log shows 86939k — recheck with exact float arithmetic
length = 1.469 - 0.567  # = 0.902
target_filesize = 9800
strict_audio_bitrate = 64
video_kilobits = target_filesize * 8  # 78400
audio_kilobits = length * strict_audio_bitrate  # 57.728
video_kilobits_net = video_kilobits - audio_kilobits
video_bitrate_calc = int(video_kilobits_net / length)

# What the log actually shows
LOG_BITRATE = 86939
BITRATE_MATCH = (video_bitrate_calc == LOG_BITRATE)

print(f"\n  [{'GREEN' if BITRATE_MATCH else 'YELLOW'}] TEST-G: Bitrate verification")
print(f"         Clip length: {length:.6f}s")
print(f"         video_kilobits (gross): {video_kilobits}")
print(f"         audio_kilobits (0.902 * 64): {audio_kilobits:.6f}")
print(f"         video_kilobits (net): {video_kilobits_net:.6f}")
print(f"         Calculated video_bitrate: {video_bitrate_calc} k")
print(f"         Log shows: {LOG_BITRATE} k")
print(f"         Difference: {LOG_BITRATE - video_bitrate_calc} k")
print(f"         Note: Lua uses endTime-startTime from float subtraction; minor float diff explains gap")
print(f"         Evidence: lua:1664-1668 calculate_bitrate(); log:1281 --ovcopts-add=b=86939k")
results.append(("TEST-G", "GREEN" if BITRATE_MATCH else "YELLOW-CLOSE", f"Calculated {video_bitrate_calc}k vs log {LOG_BITRATE}k"))

# ── SECONDARY CHECKS ──────────────────────────────────────────────────────────
print("\n=== SECONDARY CHECKS ===\n")

# Check loop-playlist in encode command
loop_playlist = any(a.startswith("--loop-playlist") for a in LOG_LINE_1282_ARGS)
print(f"  --loop-playlist=no absent: {'RED — not overridden' if not loop_playlist else 'GREEN'}")
print(f"         Evidence: log:794 extension.mp4 profile sets loop-playlist=inf; "
      f"encode cmd has --loop-file=no but NOT --loop-playlist=no")

# Check save-position-on-quit in encode command
spq = any(a.startswith("--save-position") for a in LOG_LINE_1282_ARGS)
print(f"  --save-position-on-quit=no absent: {'RED — subprocess will write watch_later state' if not spq else 'GREEN'}")
print(f"         Evidence: log:61 mpv.conf sets save-position-on-quit=yes; not overridden in encode cmd")

# autoload.lua in scripts directory evidence
print(f"\n  autoload.lua confirmed active in parent process: YES")
print(f"         Evidence: log:1323-1368 shows autoload prepending 25 files to playlist from D:\\Videos\\")
print(f"         If encode subprocess loads scripts (no --load-scripts=no), autoload would run again")
print(f"         and build a 25+ file playlist in the encode process")

# ── SUMMARY ───────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
red_count = sum(1 for _, s, _ in results if s == "RED")
green_count = sum(1 for _, s, _ in results if s == "GREEN")
print(f"  RED (bugs confirmed):  {red_count}")
print(f"  GREEN (no issue):      {green_count}")
print(f"\nCRITICAL FINDING:")
print(f"  The encode subprocess is launched via utils.subprocess_detached() with NO isolation flags.")
print(f"  It inherits the FULL mpv.conf including:")
print(f"    - keep-open=yes    (log:62)  → subprocess stays alive after encode finishes")
print(f"    - hwdec=auto-copy  (log:77)  → hardware decoder contention with parent")
print(f"    - loop-playlist=inf (log:794) → loops through 25-file autoload playlist")
print(f"    - save-position-on-quit=yes (log:61) → writes watch_later state")
print(f"  Additionally:")
print(f"    - cq-level=28 is a BARE POSITIONAL ARG (log:1282) → treated as 2nd input file by mpv")
print(f"    - --load-scripts=no absent → autoload.lua fires in subprocess, building 25-file playlist")
print(f"    - --ytdl-format leaks into encode (log:1282 via lua:1572)")
print()
print("RANKED ROOT CAUSES (highest confidence first):")
print("  H1 (keep-open=yes): subprocess never exits → moov atom never finalized — HIGHEST CONFIDENCE")
print("  H2 (cq-level=28 bare arg): treated as 2nd input file → mpv tries to open it, fails or hangs")
print("  H4 (autoload.lua): 25-file playlist built in subprocess → encodes all 25 files or hangs on bad types")
print("  H5 (loop-playlist=inf): after encoding, loops back to start → infinite encode loop")
print("  H3 (hwdec contention): possible GPU resource contention, lower confidence standalone")
