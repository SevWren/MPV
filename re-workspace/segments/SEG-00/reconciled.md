# SEG-00 Reconciled Analysis
**Lines**: L1-74
**Description**: Module requires, options table, base64 encode/decode, emit_event, test_set_options IPC handler

## Purpose
SEG-00 is the bootstrap segment. It loads all required mpv Lua libraries, declares the global `options` table with 24 user-configurable defaults, reads those options from mpv's script-opts system, implements two global base64 utility functions, registers an IPC handler for external option injection, and declares the internal `emit_event` helper.

## Line Walkthrough
- **L1-5**: `require` calls for `mp`, `mp.assdraw`, `mp.msg`, `mp.utils`, `mp.options` — all standard mpv Lua bindings.
- **L6-31**: `options` table literal with 24 fields. All accessed globally throughout the script.
- **L33**: `mpopts.read_options(options)` — reads script-opts overrides into the `options` table from mpv config.
- **L34**: `base64_chars` local constant — the base64 alphabet.
- **L36-47**: `base64_encode(data)` — GLOBAL function. Pure string manipulation, no side effects.
- **L49-62**: `base64_decode(data)` — GLOBAL function. Inverse of encode.
- **L63-66**: `emit_event(event_name, ...)` — sends a script-message prefixed with "webm-".
- **L67-73**: `test_set_options(new_options_json)` — parses JSON blob and merges into `options` table, NO validation.
- **L74**: `mp.register_script_message("mpv-webm-set-options", test_set_options)` — registers the IPC handler.

## Inputs / Outputs
- **Inputs**: mpv script-opts configuration; script-messages on "mpv-webm-set-options" channel.
- **Outputs**: Populated `options` global; registered IPC handler; `emit_event` function available.

## Side Effects
- Global `options` table is mutable and accessible from all segments.
- `mp.register_script_message` registers a persistent IPC listener.
- `mpopts.read_options` reads from mpv's configuration system at load time.

## Invariants
- `options` table always has all 24 keys after L31 (before read_options may overwrite).
- `base64_chars` has exactly 65 characters (64 + '/').

## Edge Cases
- `test_set_options` accepts ANY JSON keys without validation — can set arbitrary keys including non-option names.
- `base64_encode` on empty string returns `""` (the `{}[1]` padding lookup).
- `base64_decode` strips non-base64 chars before decoding (L50).
- `options.display_progress` is stored as a string "true" (not boolean), which is intentional — it can also be "auto".

## mpv Interactions
- `mpopts.read_options(options)`: Reads script-opts at startup.
- `mp.commandv("script-message", ...)`: Used by emit_event.
- `mp.register_script_message(...)`: IPC listener.

## Security Notes
- **CRITICAL**: `test_set_options` performs no type checking, no key whitelisting, no sanitization. Any script with access to the mpv IPC channel can set arbitrary options values including `additional_flags`, `output_directory`, etc.
- `base64_encode` and `base64_decode` are GLOBAL — visible to all scripts in the same mpv instance.

## Consensus
All three lenses agree on purpose and implementation. Security concern about test_set_options is confirmed.
