# SEG-03 Reconciled Analysis
**Lines**: L466-562
**Description**: VideoPoint class, Region class, make_fullscreen_region

## Purpose
Provides the two geometric data types used by the crop UI: VideoPoint (a 2D coordinate in video pixel space with screen↔video conversions) and Region (a crop rectangle). make_fullscreen_region creates a full-frame Region.

## Line Walkthrough
- **L466-505**: `VideoPoint` class (MoonScript-generated).
  - `__init`: sets `self.x = -1, self.y = -1` (sentinel for "unset").
  - `set_from_screen(sx, sy)`: clamps screen point to video bounds, converts to video pixels using ratios.
  - `to_screen()`: inverse mapping — video pixels to screen coordinates.
- **L506-541**: `Region` class.
  - `__init`: sets `x,y,w,h = -1,-1,-1,-1` (all invalid).
  - `is_valid()`: returns true iff all four fields > -1.
  - `set_from_points(p1, p2)`: computes AABB from two VideoPoints. Handles arbitrary point order.
- **L542-562**: `make_fullscreen_region()` — creates a Region covering the full video frame.
  - Gets `video-out-params` for `w` and `h`.
  - Returns Region with `x=0, y=0, w=w, h=h`.
  - Returns nil if no video params.

## Inputs / Outputs
- **VideoPoint.set_from_screen**: screen (x,y) → video pixel (x,y), clamped.
- **VideoPoint.to_screen**: video pixel (x,y) → screen (x,y).
- **Region.set_from_points**: two VideoPoints → crop rectangle.
- **make_fullscreen_region**: () → Region or nil.

## Side Effects
- VideoPoint/Region mutate their own fields.
- make_fullscreen_region reads mpv property.

## Invariants
- VideoPoint initialized with (-1,-1); only valid after set_from_screen.
- Region is_valid requires all fields > -1; a 0×0 region at (0,0) is valid but would crop nothing useful.
- set_from_points ensures x ≤ min(p1.x, p2.x), so x/y are always the top-left corner.

## Edge Cases
- If `get_video_dimensions()` returns nil, `set_from_screen` will error (nil indexing on `d`). Callers must ensure video is loaded.
- Zero-width or zero-height region (p1.x == p2.x): `is_valid()` returns true (w=0 > -1), but crop with w=0 would fail in ffmpeg.
- `make_fullscreen_region` returns nil if no video — callers must check.

## mpv Interactions
- `get_video_dimensions()` called by both VideoPoint methods.
- `mp.get_property_native("video-out-params")` called by make_fullscreen_region (via inner call).
