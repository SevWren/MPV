# Use mpv native script-opts for configuration — no JSON config file

All 24 configuration options are declared as a flat Lua table and read via `mp.options.read_options(options)` at startup (L33). This populates values from `script-opts/webm.conf` or `--script-opts=webm-KEY=VALUE` command-line flags. There is no JSON config file, no INI parser, and no custom file format.

The decision follows mpv's documented and supported pattern for user scripts. Using the native options system means mpv itself handles config file location, command-line override precedence, and type coercion for strings and numbers. Introducing a custom config file format would require shipping a parser, handling platform-specific config paths, and duplicating precedence logic that mpv already provides.

## Consequences

- Options can only be flat strings or numbers. Arrays, nested objects, and typed lists are not representable. The `additional_flags` and `non_strict_additional_flags` options work around this by encoding lists as space-separated strings, which introduces the whitespace tokenization bug (FIND-009).
- The `output_format` default (`"mp4 (h264/AAC)"`) does not match any key in the formats registry (valid key is `"mp4"`). This is a silent misconfiguration that falls through to whatever format happens to be the first entry — FIND-003.
- Changing an option via `mp.options.read_options` after boot (e.g., the `keybind` option via IPC) has no effect on bindings already registered by `mp.add_key_binding`.
- The `strict_bitrate_multiplier` option is declared in the table and read by `read_options`, but is never referenced anywhere in the code — FIND-008. It wastes a slot in the script-opts namespace with no remedy.
