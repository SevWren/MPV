#!/usr/bin/env python3
"""
test_find_002.py - Feedback loop for FIND-002
Bug: formats['raw'] is nil — crash in EncodeOptionsPage instantiation.
Claim: formatIds at L2368 includes 'raw' but formats['raw'] is never registered.
Location: canonical/webm.lf.lua L2363-2385

Phase 1: Build a feedback loop
  RED  — any id in formatIds is not a key in the registered formats table
  GREEN — all ids in formatIds have a corresponding formats registration

NOTE: Analysis of canonical/webm.lf.lua shows formats["raw"] IS registered at L863.
The finding may describe a previous source revision. This test documents both the
claimed bug condition and the actual state of the canonical file.

Run: python3 test_find_002.py
"""
import sys
import re
import os

LUA_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../canonical/webm.lf.lua"
)

def load_source():
    with open(LUA_PATH, "r", encoding="utf-8") as f:
        return f.read(), f.readlines() if False else None

def load_source_full():
    with open(LUA_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    with open(LUA_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return content, lines

def extract_format_ids(content):
    """
    Extract the formatIds list from EncodeOptionsPage constructor.
    Matches the literal table: local formatIds = { ... }
    """
    # Find the formatIds table in EncodeOptionsPage
    pattern = re.compile(
        r'local\s+formatIds\s*=\s*\{([^}]+)\}',
        re.DOTALL
    )
    match = pattern.search(content)
    if not match:
        return None, "Could not locate 'local formatIds = { ... }'"

    body = match.group(1)
    ids = re.findall(r'"([^"]+)"', body)
    return ids, f"Found formatIds at char offset {match.start()}: {ids}"

def extract_registered_format_keys(content):
    """
    Extract all keys used in formats["key"] = ... assignments.
    These are the registered format identifiers.
    """
    pattern = re.compile(r'^formats\["([^"]+)"\]\s*=', re.MULTILINE)
    keys = pattern.findall(content)
    return keys, f"Found {len(keys)} registered format keys: {keys}"

def check_all_ids_registered(format_ids, registered_keys):
    """
    Returns (all_ok: bool, missing: list)
    all_ok = True means GREEN (bug not present or fixed)
    """
    registered_set = set(registered_keys)
    missing = [fid for fid in format_ids if fid not in registered_set]
    return len(missing) == 0, missing

def run():
    print("=" * 60)
    print("FIND-002: formats['raw'] nil — crash in EncodeOptionsPage")
    print("=" * 60)

    if not os.path.exists(LUA_PATH):
        print(f"ERROR: Source file not found at {LUA_PATH}")
        sys.exit(2)

    content, _ = load_source_full()
    print(f"Loaded source from canonical/webm.lf.lua\n")

    # Phase 2: Extract formatIds
    format_ids, id_detail = extract_format_ids(content)
    print(f"[Phase 2 - Extract formatIds]")
    print(f"  {id_detail}")

    if format_ids is None:
        print("RESULT: INCONCLUSIVE — could not parse formatIds")
        sys.exit(2)

    # Phase 4: Extract registered format keys
    registered_keys, reg_detail = extract_registered_format_keys(content)
    print(f"\n[Phase 4 - Instrument - registered formats]")
    print(f"  {reg_detail}")

    # Phase 2+: Check for missing keys (the bug condition)
    all_ok, missing = check_all_ids_registered(format_ids, registered_keys)

    print(f"\n[Phase 2 - Bug presence check]")
    if not all_ok:
        print(f"  BUG PRESENT: formatIds contains unregistered keys: {missing}")
        print(f"  Accessing formats['{missing[0]}'].displayName would nil-index crash.")
    else:
        print(f"  All formatIds have registered formats entries: {format_ids}")
        print(f"  Note: 'raw' is registered at L863 (formats['raw'] = RawVideo())")
        print(f"  The canonical file does NOT exhibit the FIND-002 crash condition.")
        print(f"  FIND-002 may describe a prior revision or the finding's claim about")
        print(f"  'never registered' was inaccurate for this compiled output.")

    # Phase 6: Fix verification — alignment check passes
    print(f"\n[Phase 6 - Fix verification]")
    if all_ok:
        print(f"  GREEN: No mismatched format IDs. All {len(format_ids)} ids covered.")
    else:
        print(f"  RED: {len(missing)} format ID(s) lack registration: {missing}")

    print()
    if not all_ok:
        print("RESULT: RED - Bug confirmed. Missing format registrations found.")
        sys.exit(1)
    else:
        print("RESULT: GREEN - All formatIds registered. Canonical file is correct.")
        print("        FIND-002 as reported (formats['raw'] nil) does NOT apply to")
        print("        canonical/webm.lf.lua — formats['raw']=RawVideo() at L863.")
        sys.exit(0)

if __name__ == "__main__":
    run()
