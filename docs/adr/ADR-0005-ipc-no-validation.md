# IPC handler overwrites options with no validation — intentional trust boundary

The `mpv-webm-set-options` script message handler (`test_set_options`, L68–74) accepts an arbitrary JSON blob and merges every key-value pair directly into the `options` table with no type checking, range validation, or allowlist. Any key present in the JSON — including `output_directory`, `additional_flags`, and `output_format` — is overwritten unconditionally.

This is a deliberate design choice, not an oversight. The handler is intended for programmatic control by other Lua scripts or external tools running within the same mpv process. The trust model is: anything that can send a `script-message` to this script is already running inside mpv with the same privileges as the user. There is no untrusted input channel — script messages are not exposed over a network or to unprivileged processes.

## Consequences

- Any co-loaded Lua script (or any process with access to mpv's IPC socket) can override all options at any time, including security-relevant ones like `output_directory` (path traversal) and `additional_flags` (flag injection into the encode command) — documented as FIND-006.
- Do not add input validation without first understanding whether existing integrations depend on the ability to set arbitrary keys, including keys not in the declared `options` table.
- If the attack surface ever expands (e.g., the mpv IPC socket is exposed to network peers), validation becomes mandatory. Document that change as a separate ADR.
- The handler name `test_set_options` is a misnomer inherited from the MoonScript source; it is the production IPC entry point, not a test fixture.
