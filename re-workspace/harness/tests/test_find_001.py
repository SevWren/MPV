#!/usr/bin/env python3
"""
test_find_001.py - Feedback loop for FIND-001
Bug: Undefined variable 'bitrate' used instead of 'video_bitrate' in strict filesize path.
Location: canonical/webm.lf.lua L1779-1780

Phase 1: Build a feedback loop
  RED  — the word 'bitrate' (not 'video_bitrate') appears on L1779-1780 in the tostring() call
  GREEN — after patch, L1779-1780 reference 'video_bitrate' consistently

Run: python3 test_find_001.py
"""
import sys
import re
import os

LUA_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../canonical/webm.lf.lua"
)

def load_lines():
    with open(LUA_PATH, "r", encoding="utf-8") as f:
        return f.readlines()

def test_bug_present(lines):
    """
    RED test: confirms the bug exists.
    L1779-1780 (1-indexed) should contain 'tostring(bitrate)' (bare 'bitrate' not 'video_bitrate').
    Returns (found_bug: bool, detail: str)
    """
    target_lines = lines[1778:1780]  # 0-indexed → L1779-1780
    combined = "".join(target_lines)

    # The bug: bare 'bitrate' token (not prefixed with 'video_') appears in tostring()
    # We look for tostring(bitrate) — not tostring(video_bitrate) or tostring(audio_bitrate)
    bare_bitrate = re.search(r'tostring\(bitrate\)', combined)
    video_bitrate = re.search(r'tostring\(video_bitrate\)', combined)

    if bare_bitrate and not video_bitrate:
        return True, f"BUG PRESENT: found 'tostring(bitrate)' at L1779-1780:\n  {combined.strip()}"
    elif video_bitrate and not bare_bitrate:
        return False, f"BUG FIXED: found 'tostring(video_bitrate)' at L1779-1780:\n  {combined.strip()}"
    elif bare_bitrate and video_bitrate:
        return True, f"MIXED: both 'bitrate' and 'video_bitrate' present — still buggy:\n  {combined.strip()}"
    else:
        return None, f"INCONCLUSIVE: neither pattern found at L1779-1780:\n  {combined.strip()}"

def test_video_bitrate_in_scope(lines):
    """
    Verify that 'video_bitrate' is defined earlier in the same if-block (L1765).
    This confirms 'video_bitrate' is the correct variable to use.
    """
    # Search for the assignment of video_bitrate within the encode() function
    scope_lines = lines[1760:1785]  # L1761-1785 roughly
    combined = "".join(scope_lines)
    match = re.search(r'local\s+video_bitrate\s*,\s*audio_bitrate\s*=', combined)
    if match:
        return True, "CONFIRMED: 'video_bitrate' is defined in scope via calculate_bitrate()"
    return False, "WARNING: 'video_bitrate' assignment not found in expected scope"

def test_fix_correctness(lines):
    """
    GREEN test: after fix, L1779-1780 must use 'video_bitrate', not bare 'bitrate'.
    Also checks that the strict_filesize_constraint block uses a consistent variable.
    """
    target_lines = lines[1778:1780]
    combined = "".join(target_lines)
    bare = re.search(r'\bbitrate\b(?!_)', combined)  # bare 'bitrate' not part of video_bitrate/audio_bitrate
    video = re.search(r'video_bitrate', combined)
    if not bare and video:
        return True, "FIX VERIFIED: 'video_bitrate' used correctly, no bare 'bitrate'"
    return False, f"FIX NOT APPLIED or incomplete: {combined.strip()}"

def run():
    print("=" * 60)
    print("FIND-001: Undefined variable 'bitrate' in strict filesize path")
    print("=" * 60)

    if not os.path.exists(LUA_PATH):
        print(f"ERROR: Source file not found at {LUA_PATH}")
        sys.exit(2)

    lines = load_lines()
    total_lines = len(lines)
    print(f"Loaded {total_lines} lines from canonical/webm.lf.lua\n")

    # Phase 2: Reproduce the bug
    bug_present, detail = test_bug_present(lines)
    print(f"[Phase 2 - Reproduce]")
    print(f"  {detail}")

    # Phase 4: Verify video_bitrate is in scope
    scope_ok, scope_detail = test_video_bitrate_in_scope(lines)
    print(f"\n[Phase 4 - Instrument - variable scope]")
    print(f"  {scope_detail}")

    # Phase 6: Check fix
    fix_ok, fix_detail = test_fix_correctness(lines)
    print(f"\n[Phase 6 - Fix verification]")
    print(f"  {fix_detail}")

    print()
    if bug_present is True:
        print("RESULT: RED - Bug confirmed present. Patch required.")
        sys.exit(1)
    elif bug_present is False:
        print("RESULT: GREEN - Bug not present (patch already applied or not in this revision).")
        # Still report on fix quality
        if fix_ok:
            print("         Fix is correct (video_bitrate used).")
            sys.exit(0)
        else:
            print("WARNING: Unexpected variable usage at L1779-1780.")
            sys.exit(0)
    else:
        print("RESULT: INCONCLUSIVE - Manual review required.")
        sys.exit(2)

if __name__ == "__main__":
    run()
