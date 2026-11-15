#!/usr/bin/env python3
"""
test_find_006.py - Feedback loop for FIND-006
Bug: mpv-webm-set-options IPC handler has no input validation.
Location: canonical/webm.lf.lua L68-74

Phase 1: Build a feedback loop
  RED  — the handler merges all keys without any allowlist, type check, or rejection
  GREEN — the handler validates keys against an allowlist and rejects unknown/wrong-type values

Security context (Windows 10):
  - Any mpv Lua script loaded in the same session can send script-messages.
  - 'additional_flags' injection adds arbitrary ffmpeg CLI flags.
  - 'output_directory' injection enables path traversal on Windows NTFS.
  - 'output_template' injection can overwrite arbitrary files.

Run: python3 test_find_006.py
"""
import sys
import re
import os

LUA_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../canonical/webm.lf.lua"
)

# Expected options keys from the options table (L6-31)
EXPECTED_OPTIONS = {
    "keybind",
    "output_directory",
    "run_detached",
    "output_template",
    "scale_height",
    "fps",
    "target_filesize",
    "strict_filesize_constraint",
    "strict_bitrate_multiplier",
    "strict_audio_bitrate",
    "output_format",
    "twopass",
    "apply_current_filters",
    "write_filename_on_metadata",
    "libvpx_threads",
    "additional_flags",
    "crf",
    "non_strict_additional_flags",
    "display_progress",
    "font_size",
    "margin",
    "message_duration",
    "gif_dither",
    "force_square_pixels",
}

def load_source():
    with open(LUA_PATH, "r", encoding="utf-8") as f:
        return f.read()

def extract_handler_body(content):
    """
    Extract the test_set_options function body (L68-73).
    Returns (body_text, start_line, end_line)
    """
    lines = content.splitlines(keepends=True)
    # Find function start
    start_idx = None
    for i, line in enumerate(lines):
        if re.search(r'test_set_options\s*=\s*function', line):
            start_idx = i
            break

    if start_idx is None:
        return None, -1, -1

    # Collect until closing 'end'
    depth = 0
    end_idx = start_idx
    for i in range(start_idx, len(lines)):
        for ch in lines[i]:
            if ch == '{':
                depth += 1
        # Count function/do as block opens, end as closes
        stripped = lines[i].strip()
        if re.search(r'\bfunction\b', stripped) and not stripped.startswith('--'):
            depth += 1
        if stripped == 'end' or stripped.startswith('end ') or stripped.startswith('end\n'):
            depth -= 1
            if depth <= 0:
                end_idx = i
                break

    body = "".join(lines[start_idx:end_idx + 1])
    return body, start_idx + 1, end_idx + 1

def check_validation_absent(handler_body):
    """
    RED check: the handler has no validation.
    Returns (bug_present: bool, evidence: list[str])
    """
    evidence = []

    # 1. Check for allowlist-style validation (table of allowed keys)
    has_allowlist = bool(re.search(r'allowed|allowlist|whitelist|valid_keys|ALLOWED', handler_body, re.IGNORECASE))
    if not has_allowlist:
        evidence.append("No allowlist of valid option keys found")

    # 2. Check for type checking (type(), tonumber(), tostring() on values)
    has_type_check = bool(re.search(r'\btype\s*\(', handler_body))
    if not has_type_check:
        evidence.append("No type() calls found — no type validation")

    # 3. Check for key rejection / logging of unknown keys
    has_rejection = bool(re.search(r'msg\.(warn|error|info)|unknown|reject|invalid', handler_body, re.IGNORECASE))
    if not has_rejection:
        evidence.append("No rejection logging for unknown/invalid keys")

    # 4. Check for range/value validation
    has_range_check = bool(re.search(r'>=|<=|>|<', handler_body) and re.search(r'number|string|boolean', handler_body))
    if not has_range_check:
        evidence.append("No range or value validation found")

    # 5. The only operation is a bare pairs() loop merging everything
    has_bare_merge = bool(re.search(r'for\s+k\s*,\s*v\s+in\s+pairs\s*\(', handler_body))
    if has_bare_merge:
        evidence.append("Bare pairs() merge loop found — all keys merged unconditionally")

    bug_present = len(evidence) >= 3  # Need at least 3 indicators to call it unvalidated
    return bug_present, evidence

def check_dangerous_options(content):
    """
    Identify high-risk options that can be injected via the handler.
    """
    high_risk = []
    if re.search(r'additional_flags', content):
        high_risk.append("additional_flags — can inject arbitrary ffmpeg CLI flags")
    if re.search(r'output_directory', content):
        high_risk.append("output_directory — path traversal on Windows (e.g. ..\\..\\System32\\)")
    if re.search(r'output_template', content):
        high_risk.append("output_template — file overwrite via crafted template")
    return high_risk

def check_fix_applied(handler_body):
    """
    GREEN check: fix applied — allowlist + type checking present.
    """
    has_allowlist = bool(re.search(r'allowed|whitelist|valid_keys', handler_body, re.IGNORECASE))
    has_type_check = bool(re.search(r'\btype\s*\(', handler_body))
    has_rejection_log = bool(re.search(r'msg\.(warn|error|info)', handler_body))
    return all([has_allowlist, has_type_check, has_rejection_log])

def run():
    print("=" * 60)
    print("FIND-006: IPC handler test_set_options — no input validation")
    print("=" * 60)

    if not os.path.exists(LUA_PATH):
        print(f"ERROR: Source file not found at {LUA_PATH}")
        sys.exit(2)

    content = load_source()
    print(f"Loaded source from canonical/webm.lf.lua\n")

    # Phase 2: Extract handler
    handler_body, start_line, end_line = extract_handler_body(content)
    if handler_body is None:
        print("ERROR: Could not locate test_set_options function")
        sys.exit(2)

    print(f"[Phase 2 - Handler body (L{start_line}-{end_line})]")
    print(f"  {handler_body.strip()}")

    # Phase 3+4: Check for validation absence
    bug_present, evidence = check_validation_absent(handler_body)
    print(f"\n[Phase 4 - Validation analysis]")
    for e in evidence:
        print(f"  - {e}")

    # Dangerous options
    high_risk = check_dangerous_options(content)
    print(f"\n[Phase 4 - High-risk injectable options]")
    for r in high_risk:
        print(f"  RISK: {r}")

    # Windows 10 specific
    print(f"\n[Phase 4 - Windows 10 specific threat surface]")
    print(f"  - additional_flags injection: attacker adds -f rawvideo or -vf commands")
    print(f"  - output_directory: Windows path traversal with ..\\..\\  sequences")
    print(f"  - output_template: overwrite sensitive files via %F/../../../target")
    print(f"  - Any co-loaded mpv Lua script can send script-messages (no auth)")
    print(f"  - mpv IPC socket (--input-ipc-server) allows external process injection")

    # Phase 6: Fix verification
    fix_ok = check_fix_applied(handler_body)
    print(f"\n[Phase 6 - Fix verification]")
    if fix_ok:
        print(f"  GREEN: Allowlist + type-checking + rejection logging detected.")
    else:
        print(f"  RED: Fix NOT applied. Handler remains unvalidated.")

    print()
    if bug_present:
        print("RESULT: RED - Security bug confirmed. No input validation on IPC handler.")
        sys.exit(1)
    else:
        print("RESULT: GREEN - Validation logic detected in handler.")
        sys.exit(0)

if __name__ == "__main__":
    run()
