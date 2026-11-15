# Canary Recall Audit

**Date**: 2026-11-15

## Canary C1: base64_encode/decode declared as globals

**Expected**: Analyst finds that base64_encode/decode are global (not local) functions.
**Recall**: CONFIRMED independently in SEG-00 analysis.
- SEG-00-R-001: "base64_encode and base64_decode are declared as GLOBAL functions (not local), making them accessible to all mpv scripts"
- Lines L36-62 confirmed in source.
- Also confirmed in deliverable 01-provenance (security note) and 05-api-reference.
**Verdict**: RECALLED ✓

## Canary C2: mpv-webm-set-options accepts JSON blob with no validation

**Expected**: Analyst finds the IPC handler accepts any JSON without validation.
**Recall**: CONFIRMED independently in SEG-00 analysis.
- SEG-00-R-002: "test_set_options accepts arbitrary JSON with no key validation, type checking, or value sanitization"
- FIND-006 in findings.jsonl (security, HIGH severity)
- Deliverable 12-security-and-robustness-review.md documents as HIGH finding.
**Verdict**: RECALLED ✓

## Canary C3: Both argv-style and shell-string process execution paths

**Expected**: Analyst finds both run_subprocess (argv) and run_subprocess_popen (shell string).
**Recall**: CONFIRMED independently in SEG-01 analysis.
- SEG-01-R-002: "Two subprocess execution paths: run_subprocess (argv array via utils.subprocess, safe) and run_subprocess_popen (shell string via io.popen, used for progress display)"
- Deliverable 11-process-and-filesystem-interactions.md documents both modes.
**Verdict**: RECALLED ✓

## Canary C4: read_double/write_double manual IEEE-754 correctness

**Expected**: Analyst evaluates correctness of manual IEEE-754 implementation.
**Recall**: CONFIRMED in SEG-04 analysis.
- SEG-04 reconciled.md documents the algorithm and notes the get_duration bug (using reversed_binary_duration instead of big_endian_binary_duration).
- SEG-04-R-001: "get_duration uses undefined local 'reversed_binary_duration'"
- Algorithm tested in harness/tests/test_algorithms.py (8 cases, all pass).
- read_double implementation confirmed correct; write_double plausible but not fully tested.
**Verdict**: RECALLED ✓ (correctness: plausible; bug in get_duration: found)

## Canary C5: startEncode appends empty table (vestigial no-op)

**Expected**: Analyst finds the empty table append in startEncode.
**Recall**: CONFIRMED independently in SEG-08 analysis.
- SEG-08-R-001: "startEncode appends an empty table to copy_command_line (append(copy_command_line, {})) - vestigial no-op artifact"
- FIND-005 in findings.jsonl (defect, LOW severity)
- Quote confirmed: L1365-1366 source text matches.
**Verdict**: RECALLED ✓

## Canary C6: additional_flags tokenized by whitespace, quoted values with spaces break

**Expected**: Analyst finds the whitespace tokenization of additional_flags.
**Recall**: CONFIRMED independently in SEG-01 and SEG-10 analyses.
- SEG-01-R-001: "additional_flags tokenized by whitespace before escaping, so spaces in flag values split across arguments"
- SEG-10-R-004: "additional_flags and non_strict_additional_flags are tokenized by whitespace"
- FIND-009 in findings.jsonl.
- L1790: `for token in string.gmatch(options.additional_flags, "[^%s]+") do`
**Verdict**: RECALLED ✓

## Canary C7: Lua 5.1/5.2/LuaJIT dialect, portability to 5.3+ unverified

**Expected**: Analyst identifies Lua dialect compatibility.
**Recall**: CONFIRMED in gate-G1.md and deliverable 14-compatibility-matrix.md.
- Gate G1: "Uses math.ldexp (deprecated in Lua 5.3)"
- 14-compatibility-matrix.md documents Lua version compatibility table.
- Also notes string.char(unpack(...)) issue in 5.3+.
**Verdict**: RECALLED ✓

## Canary C8: UI pages bind keys via mp.add_forced_key_binding, cleanup/leak behavior

**Expected**: Analyst finds mp.add_forced_key_binding usage and evaluates cleanup.
**Recall**: CONFIRMED independently in SEG-08 analysis.
- SEG-08-R-002: "Page.add_keybinds uses mp.add_forced_key_binding with repeatable=true for all keys"
- SEG-08-R-005: "Page uses mp.add_forced_key_binding (not mp.add_key_binding) - forced bindings override all other key handlers"
- Cleanup evaluated: remove_keybinds() calls mp.remove_key_binding() — cleanup is correct. No leak in normal flow.
- 08-mpv-integration-surface.md documents the binding pattern.
**Verdict**: RECALLED ✓

## Summary

| Canary | Recalled | Evidence |
|--------|---------|---------|
| C1 | YES | SEG-00-R-001, L36-62 |
| C2 | YES | SEG-00-R-002, FIND-006, L68-74 |
| C3 | YES | SEG-01-R-002, L272-308 |
| C4 | YES | SEG-04-R-001, test_algorithms.py |
| C5 | YES | SEG-08-R-001, FIND-005, L1365-1366 |
| C6 | YES | SEG-01-R-001, FIND-009, L1790 |
| C7 | YES | gate-G1.md, doc 14 |
| C8 | YES | SEG-08-R-002/R-005, L1226 |

**Canary recall rate: 8/8 (100%)**
