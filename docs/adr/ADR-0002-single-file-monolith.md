# Single monolithic Lua file — no internal modules

`webm.lua` is implemented as one file (2856 lines) with no `require` calls beyond mpv's built-in modules (`mp`, `mp.utils`, `mp.options`, `mp.assdraw`, `mp.msg`). All 10 classes, 24 options, 7 format strategies, the UI layer, the encode orchestrator, and the geometry utilities coexist in a single file scope.

The constraint is structural: mpv's Lua sandbox does not provide a portable way to `require` user-supplied files from within a user script. The `package.path` is not reliably writable, and cross-platform path resolution for sibling script files is not documented or guaranteed. Splitting the file would require either a build step that concatenates sources before deployment or a platform-specific `package.path` hack that breaks on some installations.

## Consequences

- All state is effectively global to the file. Any function can read or write `options`, `formats`, `mainPage`, and `_video_dimensions` without import or parameter passing.
- There are no unit-testable seams without a mock harness that stubs the entire `mp.*` API surface before loading the file.
- Merge conflicts in the single file affect unrelated subsystems simultaneously.
- The layered architecture (Layers 0–7 as described in `02-architecture.md`) exists only as a logical convention enforced by line ordering, not by module boundaries.
- Any refactor that introduces `require`-based splitting must also introduce a build/concatenation step and update deployment instructions.
