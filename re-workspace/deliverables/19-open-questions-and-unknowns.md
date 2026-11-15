# 19 — Open Questions and Unknowns

**Source hash**: sha256:3f454dc0ca030b591d659f7405a3ddfdf7585e5b5eb4cd5b3a573b4151b33214
**Generation date**: 2026-11-15

---

## Questions with Unknown Answers

### Q1: What is the "raw" format intended to do?
`"raw"` appears in `formatIds` (L2368) but no corresponding `formats["raw"]` registration exists. Was it removed? Was it never implemented? Is it a placeholder? **Status: Unknown**.

### Q2: Was strict_filesize_constraint (FIND-001) ever functional?
The `bitrate` variable bug at L1779 suggests either: (a) the strict code path was never tested, or (b) a refactoring introduced the regression. No git history is available to determine which. **Status: Unknown**.

### Q3: What is the original MoonScript source location?
The compiled Lua file does not reference a source map. The original MoonScript source is not present in the analyzed repository. The script is consistent with the mpv-webm-maker project on GitHub but the exact origin version is unknown. **Status: Unknown**.

### Q4: What mpv minimum version is required?
The script uses `mp.add_forced_key_binding`, `mp.assdraw`, `mp.utils.subprocess_detached`, and `mp.command_native` with the dump_cache command. The minimum mpv version supporting all these APIs is not known without testing. **Status: Unknown — estimate mpv 0.14+**.

### Q5: Does `formats["raw"]` crash prevent EncodeOptionsPage from ever working?
Based on analysis, yes — but the crash happens during `EncodeOptionsPage.__init()` at the list comprehension that builds `formatOpts.possibleValues`. If this bug exists in the deployed version, the 'o' key effectively does nothing (crashes silently). **Status: Likely confirmed by analysis, unverified by runtime testing**.

### Q6: Is `non_strict_additional_flags = "cq-level=28"` correct for all formats?
`cq-level` is a VP8-specific parameter. For H.264 or other codecs, this flag may be ignored or cause an error. **Status: Likely incorrect for non-VP8 formats in non-strict mode; unverified**.

### Q7: What event listeners consume webm-encode-started/finished events?
The script emits these events via emit_event but no listeners are registered within webm.lua itself. External scripts may listen. **Status: Unknown — no other scripts analyzed**.

### Q8: Does `apply_current_filters` correctly propagate all mpv filter types?
apply_current_filters (L1597-1623) uses a `name:k=%len%v` format for filter parameters. This format is specific to mpv's lavfi filter syntax. Unknown if all filter types (lavfi, vf, etc.) are handled correctly. **Status: Unknown**.

### Q9: Does PreviewPage's loop implementation require mpv loop-file support?
PreviewPage.prepare appears to set loop mode but the exact property name and value were not fully read. **Status: Requires verification**.

## Areas Where Evidence Was Partial

- Windows behavior with io.popen and cmd.exe quoting (no Windows environment to test)
- HLS stream encode behavior (no HLS stream available)
- NVENC format availability (no NVIDIA GPU in sandbox)
- Actual render output of ASS draw commands (no visual output available)
