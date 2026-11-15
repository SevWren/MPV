#!/usr/bin/env python3
"""
extract_symbols.py - Extract symbols from webm.lua using Python regex parsing.
Produces: analysis/symbols.json, analysis/globals.json, analysis/string_literals.json,
          analysis/line_index.json, analysis/mpv_api_surface.json, analysis/options.json,
          analysis/metrics.json
"""
import json
import re
import sys
import os

SOURCE = "/home/vercel-sandbox/MPV/re-workspace/canonical/webm.lf.lua"
OUT_DIR = "/home/vercel-sandbox/MPV/re-workspace/analysis"

def read_source():
    with open(SOURCE, "r") as f:
        return f.readlines()

def strip_comments_and_strings_for_parsing(lines):
    """
    Returns a parallel list of 'cleaned' lines with string contents replaced by placeholders
    and comments stripped. Used for structural analysis only.
    """
    cleaned = []
    for line in lines:
        # Remove single-line comments (but not inside strings - simplified)
        # Remove --[[ ... ]] block comments handled separately
        c = re.sub(r'--(?!\[\[).*$', '', line)
        # Replace string literals with placeholder
        c = re.sub(r'"(?:[^"\\]|\\.)*"', '""', c)
        c = re.sub(r"'(?:[^'\\]|\\.)*'", "''", c)
        cleaned.append(c)
    return cleaned

def extract_functions(lines, cleaned):
    """Extract function definitions with line numbers."""
    functions = []

    # Patterns for Lua function definitions
    patterns = [
        # function name(args)
        re.compile(r'^(?:local\s+)?function\s+([\w.:]+)\s*\(([^)]*)\)'),
        # name = function(args)
        re.compile(r'^(?:local\s+)?([\w.:\[\]"]+)\s*=\s*function\s*\(([^)]*)\)'),
        # name.method = function(args)
        re.compile(r'([\w]+)\.([\w]+)\s*=\s*function\s*\(([^)]*)\)'),
    ]

    for lineno, (line, cline) in enumerate(zip(lines, cleaned), 1):
        for pat in patterns:
            m = pat.match(cline.strip())
            if m:
                groups = m.groups()
                name = groups[0] if len(groups) >= 1 else "unknown"
                args = groups[1] if len(groups) >= 2 else ""
                # For the third pattern, combine class.method
                if len(groups) == 3:
                    name = f"{groups[0]}.{groups[1]}"
                    args = groups[2]
                functions.append({
                    "name": name.strip(),
                    "args": args.strip(),
                    "line_start": lineno,
                    "line_end": None,  # will be filled in later
                    "raw": line.rstrip()
                })
                break

    # Estimate end lines by looking at next function start
    for i, fn in enumerate(functions):
        if i + 1 < len(functions):
            fn["line_end"] = functions[i+1]["line_start"] - 1
        else:
            fn["line_end"] = len(lines)

    return functions

def extract_classes(lines, cleaned):
    """Extract class-like tables (MoonScript-generated patterns)."""
    classes = []

    # MoonScript generates patterns like:
    # local _class_0 = ...
    # local _base_0 = { ... }
    # ClassName = setmetatable(...)

    class_patterns = [
        re.compile(r'local\s+_class_0\s*='),
        re.compile(r'local\s+_base_0\s*='),
        re.compile(r'(\w+)\s*=\s*setmetatable\('),
        re.compile(r'(\w+)\s*=\s*_class_0'),
        re.compile(r'(\w+)\.__index\s*='),
        re.compile(r'(\w+)\.__class\s*='),
    ]

    # Also look for class name assignments and do blocks
    do_stack = []

    for lineno, (line, cline) in enumerate(zip(lines, cleaned), 1):
        stripped = cline.strip()
        for pat in class_patterns:
            m = pat.search(stripped)
            if m:
                name = m.group(1) if m.lastindex and m.lastindex >= 1 else "_anonymous"
                # Don't double-add
                already = any(c["line"] == lineno for c in classes)
                if not already:
                    classes.append({
                        "name": name,
                        "line": lineno,
                        "pattern": pat.pattern,
                        "raw": line.rstrip()
                    })

    return classes

def extract_globals(lines, cleaned):
    """Extract global variable assignments."""
    globals_list = []

    # Global: assignment not preceded by 'local'
    global_assign = re.compile(r'^([A-Z][A-Za-z0-9_]*)\s*=\s*(.{0,60})')
    local_pattern = re.compile(r'^\s*local\s+')

    for lineno, (line, cline) in enumerate(zip(lines, cleaned), 1):
        stripped = cline.strip()
        if local_pattern.match(stripped):
            continue
        m = global_assign.match(stripped)
        if m:
            globals_list.append({
                "name": m.group(1),
                "value_preview": m.group(2).strip(),
                "line": lineno,
                "raw": line.rstrip()
            })

    return globals_list

def extract_string_literals(lines):
    """Extract all string literals with line numbers."""
    strings = []

    string_pat = re.compile(r'"((?:[^"\\]|\\.)*)"')
    string_pat2 = re.compile(r"'((?:[^'\\]|\\.)*)'")
    # Long strings [[ ... ]]
    long_string_pat = re.compile(r'\[\[(.*?)\]\]', re.DOTALL)

    full_text = "".join(lines)

    for lineno, line in enumerate(lines, 1):
        for m in string_pat.finditer(line):
            val = m.group(1)
            if val:  # skip empty strings from cleanup
                strings.append({"value": val[:200], "line": lineno, "type": "double"})
        for m in string_pat2.finditer(line):
            val = m.group(1)
            if val:
                strings.append({"value": val[:200], "line": lineno, "type": "single"})

    return strings

def extract_mpv_api(lines, cleaned):
    """Extract all mp.*, msg.*, utils.*, assdraw.* usages."""
    api_calls = []

    patterns = [
        ("mp", re.compile(r'\bmp\.(\w+)\s*\(')),
        ("mp_property", re.compile(r'\bmp\.get_property\w*\s*\(\s*["\']([^"\']+)["\']')),
        ("mp_property_set", re.compile(r'\bmp\.set_property\w*\s*\(\s*["\']([^"\']+)["\']')),
        ("mp_msg", re.compile(r'\bmp\.msg\.(\w+)\s*\(')),
        ("mp_utils", re.compile(r'\bmp\.utils\.(\w+)\s*\(')),
        ("mp_assdraw", re.compile(r'\bmp\.assdraw\.(\w+)\s*\(')),
        ("mp_options", re.compile(r'\bmp\.options\.(\w+)\s*\(')),
        ("mp_event", re.compile(r'\bmp\.register_event\s*\(\s*["\']([^"\']+)["\']')),
        ("mp_keybind", re.compile(r'\bmp\.add_(?:forced_)?key_binding\s*\(')),
    ]

    for lineno, (line, cline) in enumerate(zip(lines, cleaned), 1):
        for api_type, pat in patterns:
            for m in pat.finditer(cline):
                api_calls.append({
                    "type": api_type,
                    "call": m.group(0).strip()[:100],
                    "name": m.group(1) if m.lastindex else "",
                    "line": lineno,
                    "raw": line.rstrip()[:120]
                })

    return api_calls

def extract_options(lines):
    """Extract the options table with defaults and types."""
    options = []

    # Look for the options table definition
    in_options = False
    options_start = None

    # Pattern: options = { ... } or local options = {
    options_table_start = re.compile(r'^(?:local\s+)?options\s*=\s*\{')

    # Option entry patterns
    # name = value, -- comment
    option_entry = re.compile(r'^\s+(\w+)\s*=\s*([^,\n]+?)(?:\s*,)?\s*(?:--(.*))?$')

    brace_depth = 0

    for lineno, line in enumerate(lines, 1):
        stripped = line.strip()

        if not in_options:
            if options_table_start.match(stripped):
                in_options = True
                options_start = lineno
                brace_depth = stripped.count('{') - stripped.count('}')
                continue
        else:
            brace_depth += stripped.count('{') - stripped.count('}')
            if brace_depth <= 0:
                in_options = False
                continue

            m = option_entry.match(line)
            if m:
                name = m.group(1)
                value = m.group(2).strip().rstrip(',').strip()
                comment = m.group(3).strip() if m.group(3) else ""

                # Infer type
                if value in ('true', 'false'):
                    opt_type = "boolean"
                elif re.match(r'^-?\d+\.?\d*$', value):
                    opt_type = "number"
                elif value.startswith('"') or value.startswith("'"):
                    opt_type = "string"
                else:
                    opt_type = "unknown"

                options.append({
                    "name": name,
                    "default": value,
                    "type": opt_type,
                    "comment": comment,
                    "line": lineno
                })

    return options, options_start

def build_line_index(lines, functions, classes):
    """Build a mapping from line number to its containing function/class."""
    line_index = {}

    for lineno in range(1, len(lines) + 1):
        # Find which function contains this line
        containing_fn = None
        for fn in functions:
            if fn["line_start"] <= lineno <= (fn["line_end"] or len(lines)):
                if containing_fn is None or fn["line_start"] > containing_fn["line_start"]:
                    containing_fn = fn

        line_index[str(lineno)] = {
            "function": containing_fn["name"] if containing_fn else None,
            "function_start": containing_fn["line_start"] if containing_fn else None,
        }

    return line_index

def compute_metrics(lines, functions):
    """Compute per-function LOC and nesting depth estimates."""
    metrics = []

    for fn in functions:
        start = fn["line_start"]
        end = fn["line_end"] or len(lines)
        fn_lines = lines[start-1:end]

        loc = len([l for l in fn_lines if l.strip() and not l.strip().startswith('--')])

        # Estimate nesting depth
        max_depth = 0
        depth = 0
        for line in fn_lines:
            stripped = line.strip()
            # Increase depth
            for kw in ['if ', 'for ', 'while ', 'do', 'function ', 'then']:
                if re.search(r'\b' + kw.strip() + r'\b', stripped):
                    depth += stripped.count(kw) if kw in stripped else 0
                    break
            # Decrease depth
            if re.match(r'^end\b', stripped):
                depth = max(0, depth - 1)
            max_depth = max(max_depth, depth)

        metrics.append({
            "name": fn["name"],
            "line_start": start,
            "line_end": end,
            "loc": loc,
            "total_lines": end - start + 1,
            "estimated_max_depth": min(max_depth, 20)  # cap at 20 to avoid outliers
        })

    return metrics

def assess_transpiler_hypothesis(lines):
    """Assess whether file was generated by MoonScript transpiler."""
    evidence = []

    full_text = "".join(lines)

    # MoonScript class patterns
    if '_class_0' in full_text:
        count = full_text.count('_class_0')
        evidence.append(f"_class_0 appears {count} times (MoonScript class pattern)")

    if '_base_0' in full_text:
        count = full_text.count('_base_0')
        evidence.append(f"_base_0 appears {count} times (MoonScript base table pattern)")

    if '_parent_0' in full_text:
        count = full_text.count('_parent_0')
        evidence.append(f"_parent_0 appears {count} times (MoonScript parent pattern)")

    if '__class' in full_text:
        evidence.append("__class field present (MoonScript metaclass)")

    if 'setmetatable' in full_text:
        count = full_text.count('setmetatable')
        evidence.append(f"setmetatable called {count} times (OOP via metatables)")

    # do ... end blocks for class definitions
    do_class = re.findall(r'\bdo\b.*?_class_0', full_text[:5000], re.DOTALL)
    if do_class:
        evidence.append("do-block enclosing _class_0 (MoonScript class scoping)")

    # _with_0 pattern (MoonScript with statement)
    if '_with_0' in full_text:
        count = full_text.count('_with_0')
        evidence.append(f"_with_0 appears {count} times (MoonScript 'with' statement)")

    # Check for typical MoonScript list comprehension artifacts
    if '_accum_0' in full_text:
        count = full_text.count('_accum_0')
        evidence.append(f"_accum_0 appears {count} times (MoonScript list comprehension)")

    if '_len_0' in full_text:
        evidence.append("_len_0 present (MoonScript list comprehension length)")

    # Check for moonscript header comment
    for line in lines[:10]:
        if 'moonscript' in line.lower() or 'moon' in line.lower():
            evidence.append(f"Header mentions moonscript: {line.strip()}")

    verdict = "STRONG" if len(evidence) >= 4 else "MODERATE" if len(evidence) >= 2 else "WEAK"

    return {
        "verdict": verdict,
        "evidence": evidence,
        "transpiler": "MoonScript" if verdict in ("STRONG", "MODERATE") else "Unknown"
    }

def main():
    print("Loading source...")
    lines = read_source()
    print(f"  {len(lines)} lines")

    cleaned = strip_comments_and_strings_for_parsing(lines)

    print("Extracting functions...")
    functions = extract_functions(lines, cleaned)
    print(f"  {len(functions)} functions found")

    print("Extracting classes...")
    classes = extract_classes(lines, cleaned)
    print(f"  {len(classes)} class-like patterns found")

    print("Extracting globals...")
    globals_list = extract_globals(lines, cleaned)
    print(f"  {len(globals_list)} globals found")

    print("Extracting string literals...")
    strings = extract_string_literals(lines)
    print(f"  {len(strings)} string literals found")

    print("Extracting mpv API surface...")
    api_calls = extract_mpv_api(lines, cleaned)
    print(f"  {len(api_calls)} mpv API calls found")

    print("Extracting options...")
    options, options_start = extract_options(lines)
    print(f"  {len(options)} options found (table starts at L{options_start})")

    print("Building line index...")
    line_index = build_line_index(lines, functions, classes)

    print("Computing metrics...")
    metrics = compute_metrics(lines, functions)

    print("Assessing transpiler hypothesis...")
    transpiler = assess_transpiler_hypothesis(lines)
    print(f"  Verdict: {transpiler['verdict']} - {transpiler['transpiler']}")
    for e in transpiler['evidence']:
        print(f"    - {e}")

    # Write outputs
    os.makedirs(OUT_DIR, exist_ok=True)

    symbols = {
        "functions": functions,
        "classes": classes,
        "transpiler_hypothesis": transpiler
    }

    with open(f"{OUT_DIR}/symbols.json", "w") as f:
        json.dump(symbols, f, indent=2)
    print(f"\nWrote {OUT_DIR}/symbols.json")

    with open(f"{OUT_DIR}/globals.json", "w") as f:
        json.dump(globals_list, f, indent=2)
    print(f"Wrote {OUT_DIR}/globals.json")

    with open(f"{OUT_DIR}/string_literals.json", "w") as f:
        json.dump(strings[:500], f, indent=2)  # limit to 500 for size
    print(f"Wrote {OUT_DIR}/string_literals.json (first 500)")

    with open(f"{OUT_DIR}/line_index.json", "w") as f:
        json.dump(line_index, f, indent=2)
    print(f"Wrote {OUT_DIR}/line_index.json")

    with open(f"{OUT_DIR}/mpv_api_surface.json", "w") as f:
        json.dump(api_calls, f, indent=2)
    print(f"Wrote {OUT_DIR}/mpv_api_surface.json")

    with open(f"{OUT_DIR}/options.json", "w") as f:
        json.dump({"options_table_line": options_start, "options": options}, f, indent=2)
    print(f"Wrote {OUT_DIR}/options.json")

    with open(f"{OUT_DIR}/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"Wrote {OUT_DIR}/metrics.json")

    print("\nDone.")

if __name__ == "__main__":
    main()
