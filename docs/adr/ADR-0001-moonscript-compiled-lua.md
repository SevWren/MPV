# Maintain compiled Lua, not MoonScript source

The original MoonScript source files (`.moon`) are absent from this repository. The file `scripts/webm.lua` is compiler output from MoonScript, identifiable by the `_class_0`/`_base_0`/`_parent_0`/`_accum_0`/`_with_0` scaffolding that the `moonc` transpiler emits for every class definition and list comprehension. Because the source is unavailable, all modifications must be made directly in the compiled Lua form.

## Consequences

- The MoonScript OOP scaffolding (nested `_base_0`/`_class_0` assignments, `setmetatable` chains, `__index` wiring) is generated boilerplate, not idiomatic hand-written Lua. It must be preserved exactly as-is; partial edits to these blocks break the inheritance chain in non-obvious ways.
- There is no round-trip path: editing the Lua and then recompiling from MoonScript is not possible without first reconstructing the `.moon` sources.
- Reviewers must not mistake transpiler variables for intentional state; `_with_0` is always a temporary assignment target, `_accum_0` is always a list accumulator.
- If the MoonScript sources are ever recovered, any Lua-level patches must be back-ported manually before switching back to a MoonScript-first workflow.
