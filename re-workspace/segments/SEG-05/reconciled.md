# SEG-05 Reconciled Analysis
**Lines**: L745-931
**Description**: formats registry, Format base class, WebmVP8 format class

## Purpose
Establishes the format registry (`formats` table) and defines the Format class hierarchy. Format provides the interface contract for all output formats. WebmVP8 is the first concrete format, adding VP8-specific 2-pass log patching.

## Line Walkthrough
- **L745**: `local formats = {}` — the global format registry (keyed by string ID).
- **L746-806**: `Format` base class.
  - `getPreFilters()`: returns `{}`.
  - `getPostFilters()`: returns `{}`.
  - `getFlags()`: returns `{}`.
  - `getCodecFlags()`: returns `{--ovc=videoCodec, --oac=audioCodec}` where non-empty.
  - `postCommandModifier(command, region, startTime, endTime)`: returns `command` unchanged (identity).
  - `__init`: sets `displayName`, `supportsTwopass`, `videoCodec`, `audioCodec`, `outputExtension`, `acceptsBitrate`.
- **L807-931**: `WebmVP8` class (extends Format).
  - `__init`: displayName="WebM", supportsTwopass=true, videoCodec="libvpx", audioCodec="libvorbis", outputExtension="webm", acceptsBitrate=true.
  - `getColorspace()`: returns `"bt709"` colorspace filter string.
  - `getPostFilters()`: returns colorspace filter.
  - `postCommandModifier()`: after first pass, calls `vp8_patch_logfile` to fix pass1 log. During second pass, appends pass2 logfile path flag.

## Inputs / Outputs
- **Format interface**: Takes command array, region, times; returns modified command array.
- **WebmVP8.postCommandModifier**: modifies command for VP8 2-pass encoding.

## Side Effects
- `formats["webm-vp8"] = WebmVP8()` registered at module level (after class definition).
- `vp8_patch_logfile` call in postCommandModifier writes to filesystem.

## Invariants
- All Format subclasses must implement getCodecFlags (inherited), getFlags, getPreFilters, getPostFilters, postCommandModifier.
- `supportsTwopass=false` for formats that don't support 2-pass encoding.

## Edge Cases
- Format base `postCommandModifier` returns the command unchanged — subclasses must call super or re-implement.
- WebmVP8 postCommandModifier uses `is_stream` from upvalue — but it's the encode function's local. This would need to be passed in or accessed differently. Actually, reviewing: postCommandModifier receives `command, region, startTime, endTime` only — it does NOT receive `is_stream`. It calls `vp8_patch_logfile` unconditionally. The check `format.supportsTwopass and not is_stream` is in encode() before the call.

## mpv Interactions
None in this segment.
