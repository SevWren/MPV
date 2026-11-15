# 02 — Architecture

**Purpose**: Describe the system architecture of webm.lua.
**Audience**: Developers, maintainers.
**Source hash**: sha256:3f454dc0ca030b591d659f7405a3ddfdf7585e5b5eb4cd5b3a573b4151b33214
**Generation date**: 2026-11-15

---

## Overview

webm.lua is structured as a single-file Lua module with a 7-layer architecture. All layers share access to the global `options` table as the primary configuration mechanism.

## Layer Diagram

```
Layer 0: Bootstrap          L2838-2855
Layer 1: OSD UI Pages       L1217-2856
Layer 2: Encode Orchestration L1673-1885
Layer 3: Command Builders   L1420-1672
Layer 4: Format Registry    L745-1216
Layer 5: Data Models        L466-744
Layer 6: Utilities          L75-337
Layer 7: Geometry           L338-465
```

## Class Hierarchy

The file defines 10 MoonScript-generated classes:

**UI Pages** (extend Page):
- `Page` (L1217) — base class
- `EncodeWithProgress` (L1329) — progress overlay
- `CropPage` (L1886)
- `EncodeOptionsPage` (L2211)
- `PreviewPage` (L2539)
- `MainPage` (L2639)

**Format Codec Strategies** (extend Format):
- `Format` (L746) — base class
- `WebmVP8`, `WebmVP9`, `MP4`, `MP4NVENC`, `MP3`, `GIF`

**Data Models** (standalone):
- `VideoPoint` (L466), `Region` (L506), `FirstpassStats` (L618), `Option` (L2047)

## Key Design Patterns

1. **Strategy Pattern**: Format subclasses override `postCommandModifier`, `getFlags`, etc. to customize encoding commands without changing encode().
2. **Callback Navigation**: UI pages pass callbacks instead of direct references, enabling loose coupling between MainPage and its child pages.
3. **Global Options**: The `options` table is a module-level global accessed by virtually every function.
4. **Cache Invalidation**: `_video_dimensions` is cached and invalidated by any of 11 observed mpv properties.
5. **MoonScript OOP**: All classes use the MoonScript-generated setmetatable-based OOP pattern.

## Boot Sequence

1. Module loads and executes top-to-bottom.
2. Options table declared (L6-31).
3. `mpopts.read_options(options)` applies script-opts (L33).
4. All functions and classes defined (L34-2856).
5. Bootstrap section (L2838-2855):
   - `monitor_dimensions()` registers 11 property observers.
   - `mainPage = MainPage()` creates the singleton.
   - `mp.add_key_binding` registers the entry key.
   - `mp.register_event("file-loaded", ...)` registers the file-load handler.

## State Shared Across Modules

| Variable | Type | Modified By |
|----------|------|------------|
| `options` | table | mpopts, test_set_options, EncodeOptionsPage.confirmOpts |
| `_video_dimensions` | table | get_video_dimensions() |
| `dimensions_changed` | bool | set_dimensions_changed(), get_video_dimensions() |
| `formats` | table | Format class definitions (read-only after boot) |
| `mainPage` | MainPage | bootstrap |
