#!/usr/bin/env python3
"""
test_issue_002_feedback_loop.py - Feedback loop for GitHub Issue #2
"MP4 export hangs with zero CPU, leaving 0-byte or corrupted output"

Bugs under test
---------------
FIND-001  L1779-1780: `bitrate` (undefined) used instead of `video_bitrate`.
          With strict_filesize_constraint=yes + target_filesize=9800, the assembled
          mpv command contains --ovcopts-add=minrate=nilk / maxrate=nilk, which mpv
          rejects. With run_detached=yes the failure is completely silent.

FIND-011  L1790-1792: additional_flags tokens are appended WITHOUT a leading `--`.
          The config value `additional_flags= cq-level=28` produces the bare token
          `cq-level=28` as a positional argument. mpv treats it as a filename, not
          a flag. The correct form would be `additional_flags=--cq-level=28`.

RED  = bugs detected in the simulated command
GREEN = bugs absent (patches applied)

Run:
    python3 test_issue_002_feedback_loop.py
"""

import sys
import re
import os

# ---------------------------------------------------------------------------
# Path to canonical source
# ---------------------------------------------------------------------------
LUA_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "../../canonical/webm.lf.lua"
)

# ---------------------------------------------------------------------------
# Confirmed webm.conf for issue #2
# ---------------------------------------------------------------------------
OPTIONS = {
    "output_directory": r"D:\ProgramData\asus",
    "run_detached": True,
    "output_format": "mp4",
    "strict_filesize_constraint": True,
    "target_filesize": 9800,           # KB
    "additional_flags": " cq-level=28",
    "non_strict_additional_flags": "",
    "display_progress": True,
    "twopass": False,
    "strict_bitrate_multiplier": 1,
    "strict_audio_bitrate": 64,        # kbps
    "crf": -1,
    "write_filename_on_metadata": False,
    "libvpx_threads": 0,
}

# ---------------------------------------------------------------------------
# Minimal stub objects / helpers that mirror the real Lua logic
# ---------------------------------------------------------------------------

class MP4Format:
    displayName = "MP4 (h264/AAC)"
    supportsTwopass = True
    videoCodec = "libx264"
    audioCodec = "aac"
    outputExtension = "mp4"
    acceptsBitrate = True

    def getCodecFlags(self):
        return ["--ovc=libx264", "--oac=aac"]

    def getFlags(self):
        return []

    def postCommandModifier(self, command, *_):
        return command


def calculate_bitrate(has_audio, length, options):
    """Python translation of calculate_bitrate() from L1656-1670."""
    video_kilobits = options["target_filesize"] * 8
    audio_kilobits = None
    if options["strict_filesize_constraint"] and has_audio:
        audio_kilobits = length * options["strict_audio_bitrate"]
        video_kilobits -= audio_kilobits
    video_bitrate = int(video_kilobits / length)
    audio_bitrate = int(audio_kilobits / length) if audio_kilobits is not None else None
    return video_bitrate, audio_bitrate


def simulate_encode_command_BUGGY(options, path, start, end_, has_video=True, has_audio=True):
    """
    Simulates encode() command assembly AS-IS (with FIND-001 bug present).
    Mirrors L1707-1816 of webm.lf.lua exactly, including the `bitrate` bug.
    """
    format_ = MP4Format()
    length = end_ - start

    command = [
        "mpv",
        path,
        f"--start={start:.6f}",
        f"--end={end_:.6f}",
        "--loop-file=no",
        "--no-pause",
    ]

    # L1715: format:getCodecFlags()
    command.extend(format_.getCodecFlags())

    # L1758: format:getFlags() — returns [] for MP4
    command.extend(format_.getFlags())

    # L1762-1788: acceptsBitrate block
    if format_.acceptsBitrate:
        if options["target_filesize"] > 0:
            video_bitrate, audio_bitrate = calculate_bitrate(has_audio, length, options)

            if has_video and video_bitrate is not None:
                command.append(f"--ovcopts-add=b={video_bitrate}k")
            if has_audio and audio_bitrate is not None:
                command.append(f"--oacopts-add=b={audio_bitrate}k")

            if options["strict_filesize_constraint"]:
                type_ = "ovc" if format_.videoCodec != "" else "oac"
                # --- FIND-001 BUG: uses undefined `bitrate` (Python: None) ---
                bitrate = None   # deliberately undefined, mirroring the Lua bug
                command.append(f"--{type_}opts-add=minrate={bitrate}k")
                command.append(f"--{type_}opts-add=maxrate={bitrate}k")
        else:
            type_ = "ovc" if format_.videoCodec != "" else "oac"
            command.append(f"--{type_}opts-add=b=0")

    # L1790-1792: additional_flags tokenization
    for token in re.split(r"\s+", options["additional_flags"].strip()):
        if token:
            command.append(token)   # FIND-011: no `--` prefix added by webm.lua

    # L1816
    out_path = options["output_directory"] + "\\output.mp4"
    command.append(f"--o={out_path}")

    return command


def simulate_encode_command_FIXED(options, path, start, end_, has_video=True, has_audio=True):
    """
    Simulates encode() command assembly AFTER both patches are applied.
    FIND-001: uses video_bitrate instead of bitrate.
    FIND-011: user must prefix flags with `--` in config; here we demonstrate
              that additional_flags=--cq-level=28 passes correctly.
    """
    format_ = MP4Format()
    length = end_ - start

    command = [
        "mpv",
        path,
        f"--start={start:.6f}",
        f"--end={end_:.6f}",
        "--loop-file=no",
        "--no-pause",
    ]

    command.extend(format_.getCodecFlags())
    command.extend(format_.getFlags())

    if format_.acceptsBitrate:
        if options["target_filesize"] > 0:
            video_bitrate, audio_bitrate = calculate_bitrate(has_audio, length, options)

            if has_video and video_bitrate is not None:
                command.append(f"--ovcopts-add=b={video_bitrate}k")
            if has_audio and audio_bitrate is not None:
                command.append(f"--oacopts-add=b={audio_bitrate}k")

            if options["strict_filesize_constraint"]:
                type_ = "ovc" if format_.videoCodec != "" else "oac"
                # FIND-001 FIXED: use video_bitrate
                command.append(f"--{type_}opts-add=minrate={video_bitrate}k")
                command.append(f"--{type_}opts-add=maxrate={video_bitrate}k")
        else:
            type_ = "ovc" if format_.videoCodec != "" else "oac"
            command.append(f"--{type_}opts-add=b=0")

    # FIND-011: after fix, user config uses --cq-level=28 (with leading --)
    fixed_additional_flags = options.get("additional_flags_fixed", "")
    for token in re.split(r"\s+", fixed_additional_flags.strip()):
        if token:
            command.append(token)

    out_path = options["output_directory"] + "\\output.mp4"
    command.append(f"--o={out_path}")

    return command


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

RED   = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"
BOLD  = "\033[1m"


def coloured(text, colour):
    return f"{colour}{text}{RESET}"


def check_find_001_in_command(command):
    """Returns (bug_present: bool, evidence: str)"""
    nilk_args = [a for a in command if "nilk" in a]
    if nilk_args:
        return True, f"nilk args found: {nilk_args}"
    none_k_args = [a for a in command if "Nonek" in a or "=Nonek" in a or "=None" in a]
    if none_k_args:
        return True, f"None-based args found: {none_k_args}"
    return False, "No nilk/None values in command"


def check_find_011_in_command(command):
    """
    Returns (bug_present: bool, evidence: str)
    Bug: a token matching the pattern of a flag (contains '=') but lacking
    a leading '--' appears in the command after position 0 (which is 'mpv').
    """
    bare_flag_re = re.compile(r'^[a-z][a-z0-9\-]+=')
    suspicious = [a for a in command[1:] if bare_flag_re.match(a)]
    if suspicious:
        return True, f"Bare flag-like tokens (no '--' prefix): {suspicious}"
    return False, "No bare flag tokens detected"


def check_lua_source():
    """
    Direct static check: read the Lua source and verify the bug at L1779-1780.
    Returns (find001_present, find011_present, details)
    """
    if not os.path.exists(LUA_PATH):
        return None, None, f"Source not found: {LUA_PATH}"

    with open(LUA_PATH, encoding="utf-8") as f:
        lines = f.readlines()

    # FIND-001: L1779-1780 (0-indexed: 1778-1779)
    block = "".join(lines[1778:1780])
    find001 = bool(re.search(r'tostring\(bitrate\)', block))

    # FIND-011: L1790-1792 — additional_flags tokens appended bare
    # The pattern: command[#command + 1] = token  with no '--' prefix logic
    additional_block = "".join(lines[1789:1792])
    # Bug is structural: tokens from additional_flags are appended as-is.
    # We confirm the absence of any '--' injection logic in those lines.
    has_prefix_injection = bool(re.search(r"'--'", additional_block))
    find011_structural = not has_prefix_injection  # bug if no prefix is injected

    details = {
        "L1779-1780": block.strip(),
        "L1790-1792": additional_block.strip(),
        "find001_bare_bitrate": find001,
        "find011_no_prefix_logic": find011_structural,
    }
    return find001, find011_structural, details


# ---------------------------------------------------------------------------
# Main test runner
# ---------------------------------------------------------------------------

def run():
    sep = "=" * 68
    print(sep)
    print("ISSUE-002 Feedback Loop: MP4 export hangs, 0-byte output")
    print(sep)

    path = (r"D:\ProgramData\asus\New folder"
            r"\Tulsa-Union-High-Sch001-Semi-fina1-performance-at-BOA-"
            r"Grand-Nationals_001.mp4")
    start, end_ = 0.0, 10.0

    # ------------------------------------------------------------------
    # Phase 1A: Static source analysis
    # ------------------------------------------------------------------
    print("\n[Phase 1A] Static analysis of webm.lf.lua source")
    find001_src, find011_src, src_details = check_lua_source()

    if find001_src is None:
        print(f"  WARNING: {src_details}")
    else:
        status = coloured("BUG PRESENT", RED) if find001_src else coloured("FIXED", GREEN)
        print(f"  FIND-001 L1779-1780 bare `bitrate` in source: {status}")
        print(f"    -> {src_details['L1779-1780']}")

        status2 = coloured("BUG PRESENT", RED) if find011_src else coloured("FIXED", GREEN)
        print(f"  FIND-011 L1790-1792 no `--` prefix injection:  {status2}")
        print(f"    -> {src_details['L1790-1792']}")

    # ------------------------------------------------------------------
    # Phase 1B: Simulated command — BUGGY path
    # ------------------------------------------------------------------
    print("\n[Phase 1B] Simulated encode() command — BUGGY (as-is)")
    buggy_cmd = simulate_encode_command_BUGGY(OPTIONS, path, start, end_)

    f001_cmd, f001_evidence = check_find_001_in_command(buggy_cmd)
    f011_cmd, f011_evidence = check_find_011_in_command(buggy_cmd)

    print(f"  FIND-001 nilk in command: "
          f"{coloured('TRIGGERED', RED) if f001_cmd else coloured('not triggered', GREEN)}")
    print(f"    -> {f001_evidence}")
    print(f"  FIND-011 bare flag token: "
          f"{coloured('TRIGGERED', RED) if f011_cmd else coloured('not triggered', GREEN)}")
    print(f"    -> {f011_evidence}")

    print("\n  Full buggy command:")
    for i, arg in enumerate(buggy_cmd):
        marker = ""
        if "nilk" in arg or "Nonek" in arg or "=None" in arg:
            marker = f"  {coloured('<-- FIND-001: nilk corrupts option', RED)}"
        elif i > 0 and re.match(r'^[a-z][a-z0-9\-]+=', arg):
            marker = f"  {coloured('<-- FIND-011: bare token, no -- prefix', RED)}"
        print(f"    [{i:02d}] {arg}{marker}")

    # ------------------------------------------------------------------
    # Phase 1C: Simulated command — FIXED path
    # ------------------------------------------------------------------
    print("\n[Phase 1C] Simulated encode() command — FIXED (patches applied)")
    fixed_opts = dict(OPTIONS)
    fixed_opts["additional_flags_fixed"] = "--no-audio"  # benign valid flag for demonstration
    fixed_cmd = simulate_encode_command_FIXED(fixed_opts, path, start, end_)

    f001_fixed, _ = check_find_001_in_command(fixed_cmd)
    f011_fixed, _ = check_find_011_in_command(fixed_cmd)

    print(f"  FIND-001 nilk absent: "
          f"{coloured('PASS', GREEN) if not f001_fixed else coloured('FAIL', RED)}")
    print(f"  FIND-011 no bare tokens: "
          f"{coloured('PASS', GREEN) if not f011_fixed else coloured('FAIL', RED)}")

    # Verify H.264 / MP4 flags present
    has_ovc_libx264 = "--ovc=libx264" in fixed_cmd
    has_oac_aac = "--oac=aac" in fixed_cmd
    minrate_ok = any("minrate=" in a and "Nonek" not in a and "nilk" not in a and "None" not in a
                     for a in fixed_cmd)
    maxrate_ok = any("maxrate=" in a and "Nonek" not in a and "nilk" not in a and "None" not in a
                     for a in fixed_cmd)

    print(f"  --ovc=libx264 present:  "
          f"{coloured('PASS', GREEN) if has_ovc_libx264 else coloured('FAIL', RED)}")
    print(f"  --oac=aac present:      "
          f"{coloured('PASS', GREEN) if has_oac_aac else coloured('FAIL', RED)}")
    print(f"  minrate has real value: "
          f"{coloured('PASS', GREEN) if minrate_ok else coloured('FAIL', RED)}")
    print(f"  maxrate has real value: "
          f"{coloured('PASS', GREEN) if maxrate_ok else coloured('FAIL', RED)}")

    print("\n  Full fixed command:")
    for i, arg in enumerate(fixed_cmd):
        print(f"    [{i:02d}] {arg}")

    # ------------------------------------------------------------------
    # Overall verdict
    # ------------------------------------------------------------------
    print()
    print(sep)
    bugs_in_source = (find001_src is True) or (find011_src is True)
    bugs_in_simulation = f001_cmd or f011_cmd
    fixes_pass = (not f001_fixed) and (not f011_fixed) and has_ovc_libx264 and has_oac_aac and minrate_ok and maxrate_ok

    if bugs_in_source or bugs_in_simulation:
        label = coloured("RED - BUGS CONFIRMED PRESENT", RED + BOLD)
        print(f"RESULT: {label}")
        if find001_src is True:
            print("  - FIND-001: L1779-1780 uses bare `bitrate` (nil) => nilk in mpv command")
        if find011_src is True:
            print("  - FIND-011: L1790-1792 appends additional_flags tokens without `--` prefix")
        sys.exit(1)
    elif fixes_pass:
        label = coloured("GREEN - ALL CHECKS PASS (patches applied)", GREEN + BOLD)
        print(f"RESULT: {label}")
        sys.exit(0)
    else:
        label = coloured("YELLOW - INCONCLUSIVE", "\033[93m" + BOLD)
        print(f"RESULT: {label}")
        sys.exit(2)


if __name__ == "__main__":
    run()
