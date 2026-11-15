# 16 — Reconstruction Notes

**Source hash**: sha256:3f454dc0ca030b591d659f7405a3ddfdf7585e5b5eb4cd5b3a573b4151b33214
**Generation date**: 2026-11-15

---

## Overview

The file `scripts/webm.lua` is a MoonScript-compiled Lua script. A clean Lua reconstruction would require re-writing the MoonScript source and recompiling. This document describes what the original MoonScript source likely looked like.

## Inferred MoonScript Class Definitions

### Format class (MoonScript pseudocode)
```moonscript
class Format
  new: (config) =>
    @displayName = config.displayName or "Unknown"
    @videoCodec = config.videoCodec or ""
    @audioCodec = config.audioCodec or ""
    @outputExtension = config.outputExtension or "webm"
    @supportsTwopass = config.supportsTwopass or false
    @acceptsBitrate = config.acceptsBitrate or true

  getPreFilters: => {}
  getPostFilters: => {}
  getFlags: => {}
  getCodecFlags: =>
    codecs = {}
    codecs[] = "--ovc=#{@videoCodec}" if @videoCodec != ""
    codecs[] = "--oac=#{@audioCodec}" if @audioCodec != ""
    codecs
  postCommandModifier: (command, region, startTime, endTime) => command
```

### Page class (MoonScript pseudocode)
```moonscript
class Page
  new: =>
    @keybinds = nil
    @visible = false

  show: =>
    @visible = true
    @add_keybinds!
    @observe_properties!
    @prepare!
    @draw!

  hide: =>
    @visible = false
    @remove_keybinds!
    @unobserve_properties!
    @dispose!
    @clear!
```

## Key Architecture Decisions in Original Source

1. **MoonScript's class system** was used for all OOP — compiles to the verbose `_class_0`/`_base_0` pattern.
2. **Global options table** was likely a module-level `options = { ... }` declaration.
3. **Format registry** was likely built as a simple table literal.
4. **Callback pattern** for navigation suggests MoonScript lambdas `-> self\method!`.

## Reconstruction Limitations

A full syntactic reconstruction to MoonScript is not feasible without the original source. The compiled Lua is unambiguous in semantics but the specific MoonScript syntax (line breaks, table constructors, comprehensions) cannot be uniquely recovered.

## What CAN Be Reconstructed

A clean, manually-written Lua version that is functionally equivalent could be written by:
1. Extracting all function logic from the segments (source of truth: canonical/webm.lf.lua).
2. Replacing MoonScript OOP boilerplate with hand-written Lua OOP (e.g., using metatables directly).
3. Fixing the confirmed bugs (FIND-001, FIND-002, FIND-003, FIND-004).

This is left as a recommendation for the maintenance team.
