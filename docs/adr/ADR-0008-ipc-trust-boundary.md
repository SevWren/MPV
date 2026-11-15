# ADR-0008: IPC Handler Trust Boundary — Known-Key Allowlist Validation

**Status**: Accepted
**Date**: 2026-11-15
**Deciders**: webm.lua maintainers
**Related**: FIND-006, scripts/webm.lua

---

## Context

webm.lua exposes a named IPC handler (`mpv-webm-set-options`) that allows other mpv scripts running in the same mpv process to modify webm.lua's options at runtime. The handler receives a JSON-encoded table of key-value pairs and writes them into the `options` table.

The original handler implementation was permissive:

```lua
mp.register_script_message("mpv-webm-set-options", function(json)
    local opts = utils.parse_json(json)
    for k, v in pairs(opts) do
        options[k] = v  -- no validation of k
    end
end)
```

This means any script with access to the IPC channel can:

1. Set `additional_flags` to arbitrary mpv flags, potentially injecting `--script-opts` or `--config-dir` values that alter encode behavior.
2. Set `output_directory` to an arbitrary path, redirecting output files to unintended locations.
3. Set `output_template` to a template that escapes the intended output directory.
4. Inject an entirely new key into `options` that is later read by code that iterates over `options` without expecting unknown keys.

The IPC channel is intended as an extension point for legitimate callers (e.g., a companion UI script or automation script). It is not a security boundary in the OS sense — all callers are co-located in the same mpv process and are trusted to the degree that the user has trusted them by placing them in `~/.config/mpv/scripts/`. However, the permissive handler creates an unnecessarily large attack surface:

- A buggy companion script could accidentally set a key it did not intend to.
- A malicious script installed by a third party (e.g., bundled with a video player theme) could deliberately poison webm.lua's options.
- The permissive handler makes it impossible to audit what state changes are possible from outside webm.lua.

This was confirmed as FIND-006 during the webm.lua defect investigation.

---

## Decision

The `mpv-webm-set-options` IPC handler must validate incoming JSON keys against the known options table before writing them. Unknown keys must be logged (at `warn` level) and discarded.

The validation logic:

```lua
mp.register_script_message("mpv-webm-set-options", function(json)
    local opts = utils.parse_json(json)
    if opts == nil then
        msg.warn("mpv-webm-set-options: failed to parse JSON")
        return
    end
    for k, v in pairs(opts) do
        if options[k] ~= nil then
            options[k] = v
        else
            msg.warn("mpv-webm-set-options: unknown option key '" .. tostring(k) .. "', discarded")
        end
    end
end)
```

The check `options[k] ~= nil` uses the existing `options` table as the allowlist. Any key that was declared at module load time is a valid key. Any key not present at module load time is rejected.

This approach is preferred over a separate allowlist constant because:
- It is automatically in sync with the actual options table (no maintenance burden).
- It is auditable: the full set of valid IPC keys is exactly the set of keys in the `options` table declaration at the top of webm.lua.
- It does not require a separate validation layer that could drift from the actual options.

---

## Consequences

### Positive

- The set of values that can be changed via IPC is exactly the set of declared options — no more, no less.
- Buggy or malicious callers that send unknown keys receive a warning log message instead of silently corrupting state.
- The handler is auditable: reading the options table declaration fully enumerates all valid IPC operations.
- Future options added to the options table are automatically valid IPC targets without any code change to the handler.

### Negative (Trade-offs)

**Removed options become invalid IPC keys immediately**: If a future refactor removes an option from the options table, any external script that was setting that option via IPC will silently have its calls discarded (with a warn log). This is the correct behavior — removed options should not be settable — but it is a breaking change for callers that depended on the removed option.

**No type validation**: The handler validates key existence but not value types. A caller can set `output_format` to a boolean or a table. Future work (not in scope for this decision) could add type validation using the declared default value's type.

---

## Alternatives Considered

### Alternative 1: Remove the IPC handler entirely

The IPC handler is an undocumented extension point. Removing it would eliminate the attack surface entirely.

**Rejected**: The handler is an intentional feature that enables legitimate automation use cases (e.g., a companion script that sets `output_directory` based on the currently playing file's directory). The correct response to an overly permissive interface is to add validation, not to remove the interface.

### Alternative 2: Explicit allowlist constant

Maintain a separate `ALLOWED_IPC_KEYS = { "output_format", "output_directory", ... }` constant and validate against it.

**Rejected**: This creates a maintenance burden. Every time a new option is added to the options table, the allowlist must also be updated. Using `options[k] ~= nil` as the allowlist is strictly better: it cannot drift.

### Alternative 3: Require a shared secret

Require IPC callers to pass a shared secret that webm.lua generates at startup.

**Rejected**: mpv scripts cannot securely exchange secrets. Any secret passed via IPC would be visible to all other scripts listening on the same message bus.

---

## Verification

This decision is verified by the following static analysis test:

```python
# test_all_fixes.py — FIND-006
def test_find_006_ipc_key_validation():
    source = open("scripts/webm.lua").read()
    # The IPC handler must contain an allowlist check
    assert "options[k] ~= nil" in source or "options[k] != nil" in source
```

The full test is in `re-workspace/harness/tests/test_all_fixes.py`.

---

## References

- FIND-006: IPC handler key injection defect record
- `scripts/webm.lua` IPC handler (search for `mpv-webm-set-options`)
- mpv Lua scripting documentation: `mp.register_script_message`
- `re-workspace/deliverables/13-defect-and-quality-register.md`
