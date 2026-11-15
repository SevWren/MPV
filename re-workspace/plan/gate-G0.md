# Gate G0 Results

**Date**: 2026-11-15
**Status**: PASS

## Checklist

| Item | Status | Evidence |
|------|--------|----------|
| Hash locked | PASS | SHA-256: 3f454dc0ca030b591d659f7405a3ddfdf7585e5b5eb4cd5b3a573b4151b33214 |
| File is read-only | PASS | chmod 444 applied |
| Canonical file created | PASS | canonical/webm.lf.lua (byte-identical, LF-only confirmed) |
| Line count matches | PASS | 2856 lines verified by wc -l |
| File size matches | PASS | 82074 bytes |
| Capability report written | PASS | plan/capability-report.md |
| Validators written | PASS | tools/validate_claims.py, tools/validate_agent_output.py, tools/lint_docs.py |
| Validators self-tested | PASS | 11/11 tests pass (4+3+4) |
| Execution plan written | PASS | plan/execution-plan.md |
| STATE.json initialized | PASS | phase=0, wave=1, hash recorded |
| Ledger initialized | PASS | plan/ledger.jsonl, first entry written |
| Heartbeat written | PASS | plan/heartbeats.md |

## Notes

- No CRLF sequences found; canonical file is byte-for-byte identical to original.
- Only Python 3.9.25, git 2.49.0, jq 1.8.1, sha256sum available. No Lua/mpv/ffmpeg tooling.
- All analysis will be Python-based.

## Gate Decision

G0 **PASSES**. Proceeding to Phase 1 (Static Baseline).
