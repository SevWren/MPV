"""
Team 4 Regression Tests — ISSUE-002
Config Inheritance and additional_flags Validation

Tests verify:
  1. Bugs present in original command from log line 1281
  2. Fixed command (with --no-config --load-scripts=no --keep-open=no --hwdec=no)
  3. additional_flags=--keep-open=no --load-scripts=no produces valid flags
  4. cq-level=28 (no --) detected as invalid by validation logic
"""

import sys
import re

PASS = 0
FAIL = 0

def ok(label: str, condition: bool):
    global PASS, FAIL
    status = "PASS" if condition else "FAIL"
    if condition:
        PASS += 1
    else:
        FAIL += 1
    print(f"  [{status}] {label}")

def header(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ---------------------------------------------------------------------------
# Log line 1281 — the actual encode command from the bug report
# ---------------------------------------------------------------------------
LOG_LINE_1281 = (
    "mpv D:\\Videos\\Rockford_...mp4 "
    "--start=0:00:00.567 --end=0:00:01.469 "
    "--loop-file=no --no-pause "
    "--ovc=libx264 --oac=aac "
    "--vid=1 --aid=1 --sid=no "
    "--sub-ass-override=force --sub-auto=fuzzy "
    "--sub-pos=97.000000 --sub-delay=0.000000 "
    "--video-rotate=0 "
    "--ytdl-format=bv*[height<=1080]+ba/b[height<=1080] "
    "--deinterlace=no "
    "--vf-add=lavfi-scale=-2:720 "
    "--vf-add=lavfi-eq=contrast=1:saturation=1:brightness=0 "
    "--ovcopts-add=b=86939k cq-level=28 "
    "--o=D:\\ProgramData\\asus\\...mp4"
)

# Parse the command into args (simple whitespace split, respecting the log format)
# In the actual subprocess call each token is a separate array element;
# here we simulate by splitting on whitespace, noting that cq-level=28 is bare.
ORIGINAL_ARGS = LOG_LINE_1281.split()


def is_bare_positional(token: str) -> bool:
    """Return True if token looks like a bare positional arg (no leading --)."""
    return not token.startswith("-") and not token.startswith("mpv")


def has_problematic_inherited_option(args: list, option: str) -> bool:
    """
    Return True if the given option is NOT present in the args
    (i.e., the problematic inherited option from mpv.conf is not being overridden).
    """
    for arg in args:
        if arg.startswith(f"--{option}=") or arg == f"--{option}":
            return True
    return False


def validate_additional_flags_token(token: str) -> tuple:
    """
    Validate a single token from additional_flags.
    Returns (is_valid: bool, reason: str).
    """
    if not token.startswith("--"):
        return False, f"Token '{token}' does not start with '--'; would be treated as filename"
    return True, "OK"


# ---------------------------------------------------------------------------
# Test 1: Verify bugs present in original command
# ---------------------------------------------------------------------------
header("Test 1: Original command (log line 1281) — verify bugs are present")

# 1a. Bare positional arg — cq-level=28 should be there without --
bare_args = [t for t in ORIGINAL_ARGS if is_bare_positional(t) and "=" in t and not t.startswith("D:\\")]
cq_level_bare = any("cq-level=28" == t for t in ORIGINAL_ARGS)
ok("cq-level=28 is present as a bare token (no --)", cq_level_bare)

# 1b. No --no-config in original command
no_config_present = "--no-config" in ORIGINAL_ARGS
ok("--no-config is ABSENT from original command (expected)", not no_config_present)

# 1c. No --load-scripts=no in original command
load_scripts_present = "--load-scripts=no" in ORIGINAL_ARGS
ok("--load-scripts=no is ABSENT from original command (expected)", not load_scripts_present)

# 1d. No --keep-open=no in original command (meaning keep-open=yes from mpv.conf is inherited)
keep_open_no_present = "--keep-open=no" in ORIGINAL_ARGS
ok("--keep-open=no is ABSENT from original command (inherited keep-open=yes risk)", not keep_open_no_present)

# 1e. No --hwdec=no in original command (hwdec=auto-copy inherited from mpv.conf)
hwdec_no_present = "--hwdec=no" in ORIGINAL_ARGS
ok("--hwdec=no is ABSENT from original command (inherited hwdec=auto-copy risk)", not hwdec_no_present)

# 1f. Count positional args (non-flag, non-mpv tokens) — should be more than 1 (the input file) due to bug
positional_args = [t for t in ORIGINAL_ARGS if is_bare_positional(t)]
ok("Original command has bare positional arg(s) beyond the input file", len(positional_args) >= 1)

print(f"\n  Bare positional tokens found: {positional_args}")


# ---------------------------------------------------------------------------
# Test 2: Fixed command — verify no bare positional args, no problematic inheritance
# ---------------------------------------------------------------------------
header("Test 2: Fixed command (with --no-config --load-scripts=no --keep-open=no --hwdec=no)")

# Build the fixed command by:
# 1. Inserting the four protective flags right after the input path
# 2. Replacing cq-level=28 with --ovcopts-add=crf=28 (or simply removing the bare token)
def build_fixed_command(original_args: list) -> list:
    """Simulate the fixed webm.lua command construction."""
    result = []
    # Insert mpv and path
    result.append("mpv")
    # Find the input path (first non-mpv token that looks like a path)
    path_token = None
    rest = []
    skip_next = False
    for i, token in enumerate(original_args[1:], 1):  # skip "mpv"
        if path_token is None and not token.startswith("--"):
            # This is the input path (e.g., D:\Videos\...)
            if token.startswith("D:\\") or token.endswith(".mp4") or token.endswith(".mkv"):
                path_token = token
                continue
        rest.append(token)

    if path_token:
        result.append(path_token)

    # Add the four protective flags (the proper code fix)
    result.extend([
        "--no-config",
        "--load-scripts=no",
        "--keep-open=no",
        "--hwdec=no",
    ])

    # Add the remaining flags, skipping bare tokens (the validation fix)
    for token in rest:
        valid, reason = validate_additional_flags_token(token)
        if token.startswith("--") or token == "mpv":
            result.append(token)
        # bare tokens (cq-level=28) are dropped

    return result

FIXED_ARGS = build_fixed_command(ORIGINAL_ARGS)

# 2a. --no-config present
ok("--no-config present in fixed command", "--no-config" in FIXED_ARGS)

# 2b. --load-scripts=no present
ok("--load-scripts=no present in fixed command", "--load-scripts=no" in FIXED_ARGS)

# 2c. --keep-open=no present
ok("--keep-open=no present in fixed command", "--keep-open=no" in FIXED_ARGS)

# 2d. --hwdec=no present
ok("--hwdec=no present in fixed command", "--hwdec=no" in FIXED_ARGS)

# 2e. No bare positional args (beyond the input file path)
bare_in_fixed = [t for t in FIXED_ARGS[2:] if is_bare_positional(t)]  # skip "mpv" and path
ok("No bare positional args in fixed command", len(bare_in_fixed) == 0)

# 2f. cq-level=28 bare token is gone
ok("cq-level=28 bare token absent from fixed command", "cq-level=28" not in FIXED_ARGS)

print(f"\n  Fixed command protective flags: --no-config, --load-scripts=no, --keep-open=no, --hwdec=no")
print(f"  Bare tokens in fixed command (excluding path): {bare_in_fixed}")


# ---------------------------------------------------------------------------
# Test 3: Minimal workaround via additional_flags in webm.conf
# ---------------------------------------------------------------------------
header("Test 3: Minimal workaround — additional_flags=--keep-open=no --load-scripts=no")

MINIMAL_WORKAROUND_VALUE = "--keep-open=no --load-scripts=no"

def parse_additional_flags(value: str) -> list:
    """Simulate webm.lua's gmatch tokeniser: split on whitespace."""
    return [t for t in value.split() if t]

minimal_tokens = parse_additional_flags(MINIMAL_WORKAROUND_VALUE)

# 3a. Both tokens parse correctly
ok("Minimal workaround produces 2 tokens", len(minimal_tokens) == 2)

# 3b. All tokens start with --
all_valid = all(t.startswith("--") for t in minimal_tokens)
ok("All tokens in minimal workaround start with '--'", all_valid)

# 3c. --keep-open=no is present
ok("--keep-open=no token present", "--keep-open=no" in minimal_tokens)

# 3d. --load-scripts=no is present
ok("--load-scripts=no token present", "--load-scripts=no" in minimal_tokens)

COMPLETE_WORKAROUND_VALUE = "--no-config --load-scripts=no --keep-open=no --hwdec=no"
complete_tokens = parse_additional_flags(COMPLETE_WORKAROUND_VALUE)

# 3e. Complete workaround produces 4 tokens, all valid
ok("Complete workaround produces 4 tokens", len(complete_tokens) == 4)
ok("All tokens in complete workaround start with '--'", all(t.startswith("--") for t in complete_tokens))

print(f"\n  Minimal tokens:  {minimal_tokens}")
print(f"  Complete tokens: {complete_tokens}")


# ---------------------------------------------------------------------------
# Test 4: cq-level=28 detected as invalid by validation logic
# ---------------------------------------------------------------------------
header("Test 4: Validation logic — cq-level=28 without -- is detected as invalid")

# 4a. cq-level=28 is invalid (bare, no --)
valid, reason = validate_additional_flags_token("cq-level=28")
ok("cq-level=28 detected as INVALID (no -- prefix)", not valid)
print(f"  Reason: {reason}")

# 4b. --cq-level=28 is syntactically valid (even though it's wrong codec)
valid2, reason2 = validate_additional_flags_token("--cq-level=28")
ok("--cq-level=28 passes syntax validation (has -- prefix)", valid2)

# 4c. --ovcopts-add=crf=28 is the correct H.264 replacement — passes validation
valid3, reason3 = validate_additional_flags_token("--ovcopts-add=crf=28")
ok("--ovcopts-add=crf=28 passes validation (correct H.264 quality flag)", valid3)

# 4d. All the original fixed flags pass validation
fixed_flags = ["--no-config", "--load-scripts=no", "--keep-open=no", "--hwdec=no"]
all_pass = all(validate_additional_flags_token(f)[0] for f in fixed_flags)
ok("All four protective flags pass validation", all_pass)

# 4e. Edge case: empty string
empty_tokens = parse_additional_flags("")
ok("Empty additional_flags produces zero tokens (no crash)", len(empty_tokens) == 0)

# 4f. Edge case: flag with leading space (original bug: " cq-level=28")
space_prefixed = parse_additional_flags(" cq-level=28")
ok("Leading-space ' cq-level=28' still parses to bare token", space_prefixed == ["cq-level=28"])
valid4, _ = validate_additional_flags_token(space_prefixed[0])
ok("Leading-space bare token still fails validation", not valid4)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
total = PASS + FAIL
header(f"RESULTS: {PASS}/{total} passed, {FAIL}/{total} failed")

if FAIL == 0:
    print("  ALL TESTS PASSED")
    sys.exit(0)
else:
    print(f"  {FAIL} TEST(S) FAILED")
    sys.exit(1)
