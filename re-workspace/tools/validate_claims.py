#!/usr/bin/env python3
"""
validate_claims.py - JSON schema validation for claims.jsonl files.
Validates: ID uniqueness, line-range validity, quote-match check.
Usage: python3 validate_claims.py <claims.jsonl> [--source <webm.lua>]
"""
import json
import sys
import re
import argparse

REQUIRED_FIELDS = {"id", "segment", "type", "summary", "lines"}
VALID_TYPES = {"functional", "control-flow", "data-flow", "defect", "security",
               "invariant", "edge-case", "mpv-api", "option", "algorithm", "unknown"}

def load_source_lines(path):
    with open(path, "r") as f:
        return f.readlines()

def validate_claims_file(claims_path, source_lines=None):
    errors = []
    warnings = []
    seen_ids = {}
    claims = []

    with open(claims_path, "r") as f:
        for lineno, raw in enumerate(f, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                claim = json.loads(raw)
            except json.JSONDecodeError as e:
                errors.append(f"Line {lineno}: JSON parse error: {e}")
                continue
            claims.append((lineno, claim))

    for lineno, claim in claims:
        cid = claim.get("id", "")

        # Required fields
        missing = REQUIRED_FIELDS - set(claim.keys())
        if missing:
            errors.append(f"Claim {cid} (jsonl line {lineno}): missing fields: {missing}")

        # ID uniqueness
        if cid in seen_ids:
            errors.append(f"Duplicate ID '{cid}' at jsonl lines {seen_ids[cid]} and {lineno}")
        else:
            seen_ids[cid] = lineno

        # ID format
        if cid and not re.match(r'^[A-Z]{2,5}-\d{2,4}-[A-Z]-\d{3,4}$', cid):
            warnings.append(f"Claim {cid}: ID format unexpected (expected SEG-NN-L-NNN style)")

        # Line range validity
        lines = claim.get("lines")
        if lines is not None:
            if isinstance(lines, list) and len(lines) == 2:
                lo, hi = lines
                if not (isinstance(lo, int) and isinstance(hi, int)):
                    errors.append(f"Claim {cid}: lines must be [int, int]")
                elif lo < 1 or hi < lo:
                    errors.append(f"Claim {cid}: invalid line range [{lo}, {hi}]")
                elif source_lines and hi > len(source_lines):
                    errors.append(f"Claim {cid}: line range [{lo}, {hi}] exceeds source length {len(source_lines)}")
            else:
                errors.append(f"Claim {cid}: 'lines' must be a 2-element array [start, end]")

        # Quote match check (if quote field present)
        quote = claim.get("quote")
        if quote and source_lines and lines and isinstance(lines, list) and len(lines) == 2:
            lo, hi = lines
            if 1 <= lo <= hi <= len(source_lines):
                segment_text = "".join(source_lines[lo-1:hi])
                if quote not in segment_text:
                    errors.append(f"Claim {cid}: quote not found in lines {lo}-{hi}")

        # Type validation
        ctype = claim.get("type", "")
        if ctype and ctype not in VALID_TYPES:
            warnings.append(f"Claim {cid}: unknown type '{ctype}' (valid: {VALID_TYPES})")

        # Confidence
        conf = claim.get("confidence")
        if conf is not None and not isinstance(conf, (int, float)):
            errors.append(f"Claim {cid}: confidence must be numeric")
        elif conf is not None and not (0.0 <= conf <= 1.0):
            errors.append(f"Claim {cid}: confidence {conf} out of [0,1]")

    return errors, warnings, len(claims)

def main():
    parser = argparse.ArgumentParser(description="Validate claims.jsonl files")
    parser.add_argument("claims_file", help="Path to claims.jsonl")
    parser.add_argument("--source", help="Path to source lua file for quote/range checks",
                        default="/home/vercel-sandbox/MPV/re-workspace/canonical/webm.lf.lua")
    parser.add_argument("--self-test", action="store_true", help="Run built-in self-test")
    args = parser.parse_args()

    if args.self_test:
        run_self_test()
        return

    source_lines = None
    if args.source:
        try:
            source_lines = load_source_lines(args.source)
        except FileNotFoundError:
            print(f"WARNING: source file not found: {args.source}", file=sys.stderr)

    errors, warnings, count = validate_claims_file(args.claims_file, source_lines)

    print(f"Validated {count} claims from {args.claims_file}")
    for w in warnings:
        print(f"  WARN: {w}")
    for e in errors:
        print(f"  ERROR: {e}")

    if errors:
        print(f"\nFAILED: {len(errors)} error(s), {len(warnings)} warning(s)")
        sys.exit(1)
    else:
        print(f"\nPASSED: 0 errors, {len(warnings)} warning(s)")

def run_self_test():
    import tempfile, os

    print("Running self-test...")

    # Good claim
    good = {"id": "SEG-00-A-001", "segment": "SEG-00", "type": "functional",
            "summary": "test claim", "lines": [1, 5], "confidence": 0.9}

    # Bad: missing field
    bad_missing = {"id": "SEG-00-A-002", "segment": "SEG-00", "summary": "no type or lines"}

    # Bad: duplicate ID
    dup = {"id": "SEG-00-A-001", "segment": "SEG-00", "type": "functional",
           "summary": "duplicate", "lines": [1, 2]}

    # Bad: invalid line range
    bad_range = {"id": "SEG-00-A-003", "segment": "SEG-00", "type": "functional",
                 "summary": "bad range", "lines": [10, 5]}

    # Test good
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write(json.dumps(good) + "\n")
        good_path = f.name
    errors, warnings, count = validate_claims_file(good_path)
    assert errors == [], f"Expected no errors for good claim, got: {errors}"
    print("  PASS: good claim accepted")
    os.unlink(good_path)

    # Test bad missing fields
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write(json.dumps(bad_missing) + "\n")
        bad_path = f.name
    errors, warnings, count = validate_claims_file(bad_path)
    assert any("missing fields" in e for e in errors), f"Expected missing fields error, got: {errors}"
    print("  PASS: missing fields detected")
    os.unlink(bad_path)

    # Test duplicate IDs
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write(json.dumps(good) + "\n")
        f.write(json.dumps(dup) + "\n")
        dup_path = f.name
    errors, warnings, count = validate_claims_file(dup_path)
    assert any("Duplicate ID" in e for e in errors), f"Expected duplicate ID error, got: {errors}"
    print("  PASS: duplicate ID detected")
    os.unlink(dup_path)

    # Test bad line range
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write(json.dumps(bad_range) + "\n")
        range_path = f.name
    errors, warnings, count = validate_claims_file(range_path)
    assert any("invalid line range" in e for e in errors), f"Expected range error, got: {errors}"
    print("  PASS: invalid line range detected")
    os.unlink(range_path)

    print("Self-test PASSED (4/4)")

if __name__ == "__main__":
    main()
