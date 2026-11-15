#!/usr/bin/env python3
"""
lint_docs.py - Lint documentation files.
Checks: dead links (relative), unresolved placeholders, line-ref validity, code-fence syntax.
Usage: python3 lint_docs.py <doc.md> [--source-max-lines 2856]
"""
import sys
import re
import os
import argparse

SOURCE_MAX_LINES = 2856

def lint_file(path, source_max_lines=SOURCE_MAX_LINES, check_links=True):
    errors = []
    warnings = []

    with open(path, "r") as f:
        lines = f.readlines()
    text = "".join(lines)

    # 1. Unresolved placeholders
    placeholders = re.findall(r'\[TODO[^\]]*\]|\[FIXME[^\]]*\]|\[TBD[^\]]*\]|\[PLACEHOLDER[^\]]*\]|\[UNKNOWN[^\]]*\]', text)
    for ph in placeholders:
        warnings.append(f"Unresolved placeholder: {ph}")

    # 2. Line references out of range
    # Match patterns like L123, L123-456, lines 123-456, line 123
    line_ref_patterns = [
        re.compile(r'\bL(\d+)-(\d+)\b'),   # L123-456
        re.compile(r'\bL(\d+)\b'),           # L123
        re.compile(r'\blines?\s+(\d+)\s*[-–]\s*(\d+)\b', re.IGNORECASE),
        re.compile(r'\bline\s+(\d+)\b', re.IGNORECASE),
    ]
    for docline_no, docline in enumerate(lines, 1):
        for pat in line_ref_patterns:
            for m in pat.finditer(docline):
                g = m.groups()
                lo = int(g[0])
                hi = int(g[1]) if len(g) > 1 and g[1] else lo
                if lo < 1 or hi < lo or hi > source_max_lines:
                    errors.append(f"Doc line {docline_no}: line reference {m.group(0)} out of range (source has {source_max_lines} lines)")

    # 3. Code fence syntax check (balanced fences)
    fence_open = None
    fence_line = None
    for docline_no, docline in enumerate(lines, 1):
        stripped = docline.strip()
        if stripped.startswith("```"):
            if fence_open is None:
                fence_open = stripped[3:].strip()  # language tag
                fence_line = docline_no
            else:
                fence_open = None
                fence_line = None
    if fence_open is not None:
        errors.append(f"Unclosed code fence opened at doc line {fence_line} (language: '{fence_open}')")

    # 4. Dead relative links
    if check_links:
        link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        doc_dir = os.path.dirname(os.path.abspath(path))
        for m in link_pattern.finditer(text):
            link_target = m.group(2)
            # Only check relative links (not http/https/mailto/anchors)
            if link_target.startswith(("http://", "https://", "mailto:", "#", "ftp://")):
                continue
            # Strip anchor
            target_path = link_target.split("#")[0]
            if not target_path:
                continue
            full_path = os.path.join(doc_dir, target_path)
            if not os.path.exists(full_path):
                warnings.append(f"Dead relative link: [{m.group(1)}]({link_target})")

    # 5. Check for obviously broken markdown tables (mismatched pipes)
    in_table = False
    for docline_no, docline in enumerate(lines, 1):
        stripped = docline.strip()
        if stripped.startswith("|"):
            pipe_count = stripped.count("|")
            if in_table and pipe_count < 2:
                warnings.append(f"Doc line {docline_no}: possible malformed table row")
            in_table = True
        else:
            in_table = False

    return errors, warnings

def run_self_test():
    import tempfile, os as os_mod
    print("Running self-test...")

    # Good doc
    good_doc = """# Test Document

## Overview
This is a test document referencing L1-74 and L2856.

```lua
local x = 1
```

See [other file](../canonical/HASHES.txt) for hashes.
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, dir='/tmp') as f:
        f.write(good_doc)
        good_path = f.name
    errors, warnings = lint_file(good_path, check_links=False)
    assert errors == [], f"Expected no errors for good doc, got: {errors}"
    print("  PASS: good doc accepted")
    os_mod.unlink(good_path)

    # Bad: out-of-range line ref
    bad_ref = good_doc + "\nSee L9999-10000 for details.\n"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, dir='/tmp') as f:
        f.write(bad_ref)
        bad_path = f.name
    errors, warnings = lint_file(bad_path, check_links=False)
    assert any("out of range" in e for e in errors), f"Expected range error, got: {errors}"
    print("  PASS: out-of-range line ref detected")
    os_mod.unlink(bad_path)

    # Bad: unclosed code fence
    bad_fence = good_doc + "\n```python\nunclosed fence\n"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, dir='/tmp') as f:
        f.write(bad_fence)
        fence_path = f.name
    errors, warnings = lint_file(fence_path, check_links=False)
    assert any("Unclosed code fence" in e for e in errors), f"Expected fence error, got: {errors}"
    print("  PASS: unclosed code fence detected")
    os_mod.unlink(fence_path)

    # Bad: placeholder
    ph_doc = good_doc + "\n[TODO: write this section]\n"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, dir='/tmp') as f:
        f.write(ph_doc)
        ph_path = f.name
    errors, warnings = lint_file(ph_path, check_links=False)
    assert any("placeholder" in w.lower() for w in warnings), f"Expected placeholder warning, got: {warnings}"
    print("  PASS: placeholder detected")
    os_mod.unlink(ph_path)

    print("Self-test PASSED (4/4)")

def main():
    parser = argparse.ArgumentParser(description="Lint documentation markdown files")
    parser.add_argument("file", nargs='?', help="Path to markdown file")
    parser.add_argument("--source-max-lines", type=int, default=SOURCE_MAX_LINES)
    parser.add_argument("--no-links", action="store_true", help="Skip dead link checks")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        run_self_test()
        return

    if not args.file:
        parser.print_help()
        sys.exit(1)

    errors, warnings = lint_file(args.file, args.source_max_lines, check_links=not args.no_links)

    print(f"Linting {args.file}")
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
