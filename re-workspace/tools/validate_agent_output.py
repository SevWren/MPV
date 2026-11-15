#!/usr/bin/env python3
"""
validate_agent_output.py - Validate analyst and reconciler output files.
Checks: required sections present, digest <=300 words, citations valid.
Usage: python3 validate_agent_output.py <analyst.md> [--type analyst|reconciler]
"""
import sys
import re
import argparse

ANALYST_REQUIRED_SECTIONS = [
    "purpose",
    "line walkthrough",
    "inputs",
    "outputs",
    "side effects",
    "invariants",
    "edge cases",
    "mpv interactions",
]

RECONCILER_REQUIRED_SECTIONS = [
    "reconciled",
    "disputes",
    "consensus",
]

LINE_REF_PATTERN = re.compile(r'[Ll](?:ines?\s*)?(\d+)(?:\s*[-–]\s*(\d+))?')
CITATION_PATTERN = re.compile(r'L(\d+)(?:-(\d+))?')

def count_words(text):
    return len(text.split())

def find_digest_section(text):
    """Find a 'digest' or 'summary' section and return its word count."""
    patterns = [
        r'(?:^|\n)#{1,3}\s*(?:digest|summary)\s*\n(.*?)(?=\n#{1,3}|\Z)',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
        if m:
            return count_words(m.group(1).strip())
    return None

def validate_citations(text, source_max_lines=2856):
    """Check all L123 or L123-456 citations are within source bounds."""
    errors = []
    for m in CITATION_PATTERN.finditer(text):
        lo = int(m.group(1))
        hi = int(m.group(2)) if m.group(2) else lo
        if lo < 1 or hi < lo or hi > source_max_lines:
            errors.append(f"Citation L{m.group(0)} out of range (1-{source_max_lines})")
    return errors

def validate_required_sections(text, required):
    """Check that required section headers appear (case-insensitive)."""
    missing = []
    for section in required:
        pattern = re.compile(r'(?:^|\n)#{1,4}\s*' + re.escape(section), re.IGNORECASE)
        if not pattern.search(text):
            # Also check for bold headers or plain mentions
            plain = re.compile(r'\b' + re.escape(section) + r'\b', re.IGNORECASE)
            if not plain.search(text):
                missing.append(section)
    return missing

def validate_file(path, doc_type="analyst"):
    errors = []
    warnings = []

    with open(path, "r") as f:
        text = f.read()

    # Required sections
    required = ANALYST_REQUIRED_SECTIONS if doc_type == "analyst" else RECONCILER_REQUIRED_SECTIONS
    missing = validate_required_sections(text, required)
    if missing:
        warnings.append(f"Missing sections: {missing}")

    # Digest word count
    digest_words = find_digest_section(text)
    if digest_words is not None and digest_words > 300:
        errors.append(f"Digest section exceeds 300 words ({digest_words} words)")

    # Citation validity
    citation_errors = validate_citations(text)
    errors.extend(citation_errors)

    # Check for unresolved placeholders
    placeholders = re.findall(r'\[TODO[^\]]*\]|\[FIXME[^\]]*\]|\[TBD[^\]]*\]|\[PLACEHOLDER[^\]]*\]', text)
    if placeholders:
        warnings.append(f"Unresolved placeholders: {placeholders[:5]}")

    return errors, warnings

def run_self_test():
    import tempfile, os
    print("Running self-test...")

    good_analyst = """# Analyst Report

## Purpose
This segment implements the base64 encoding utility.

## Line Walkthrough
L1-10: module header and requires

## Inputs
- Raw binary data as string

## Outputs
- Base64-encoded string

## Side Effects
None.

## Invariants
Output length is always a multiple of 4.

## Edge Cases
Empty string input returns empty string.

## MPV Interactions
None in this segment.
"""

    # Test good analyst doc
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(good_analyst)
        good_path = f.name
    errors, warnings, = validate_file(good_path, "analyst")
    assert errors == [], f"Expected no errors for good analyst, got: {errors}"
    print("  PASS: good analyst accepted")
    os.unlink(good_path)

    # Test bad citation
    bad_cite = good_analyst + "\nSee L9999 for details.\n"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(bad_cite)
        bad_path = f.name
    errors, warnings = validate_file(bad_path, "analyst")
    assert any("out of range" in e for e in errors), f"Expected citation error, got: {errors}"
    print("  PASS: out-of-range citation detected")
    os.unlink(bad_path)

    # Test placeholder detection
    placeholder_doc = good_analyst + "\n[TODO: fill this in]\n"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(placeholder_doc)
        ph_path = f.name
    errors, warnings = validate_file(ph_path, "analyst")
    assert any("placeholder" in w.lower() for w in warnings), f"Expected placeholder warning, got: {warnings}"
    print("  PASS: placeholder detected")
    os.unlink(ph_path)

    print("Self-test PASSED (3/3)")

def main():
    parser = argparse.ArgumentParser(description="Validate analyst/reconciler output files")
    parser.add_argument("file", help="Path to markdown file")
    parser.add_argument("--type", choices=["analyst", "reconciler"], default="analyst")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        run_self_test()
        return

    errors, warnings = validate_file(args.file, args.type)

    print(f"Validating {args.file} (type={args.type})")
    for w in warnings:
        print(f"  WARN: {w}")
    for e in errors:
        print(f"  ERROR: {e}")

    if errors:
        print(f"\nFAILED: {len(errors)} error(s), {len(warnings)} warning(s)")
        sys.exit(1)
    else:
        print(f"\nPASSED: 0 errors, {len(warnings)} warning(s)")

if __name__ == "__main__":
    main()
