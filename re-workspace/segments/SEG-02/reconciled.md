# SEG-02 Reconciled Analysis
**Lines**: L339-465
**Description**: Video geometry — OSD-to-video coordinate mapping, aspect ratio handling, pan/zoom, dimension observers

## Purpose
Computes the mapping between OSD screen coordinates and video pixel coordinates, accounting for aspect ratio, panscan, zoom, and alignment. The result is cached in `_video_dimensions` and invalidated on any relevant property change.

## Line Walkthrough
- **L338-339**: `dimensions_changed = true`, `_video_dimensions = {}` — cache init.
- **L341-425**: `get_video_dimensions()` — returns `{top_left={x,y}, bottom_right={x,y}, ratios={w,h}}`. Returns nil if no video-out-params. Caches result until invalidated.
  - Reads `video-out-params` (native): `w`, `h`, `dw`, `dh` (display width/height).
  - Handles 90-degree rotation by swapping w/h and dw/dh.
  - `keep_aspect=true` path: Computes fitted video rectangle considering panscan area and split_scaling.
  - `keep_aspect=false` path: Video covers entire OSD window.
  - Computes `ratios.w = w / (right.x - left.x)` and `ratios.h = h / (right.y - left.y)`.
- **L395-408**: `split_scaling(dst_size, scaled_src_size, zoom, align, pan)` — LOCAL function inside get_video_dimensions. Computes start/end pixel positions with zoom and alignment. Clamps to prevent zero-size output.
- **L427-430**: `set_dimensions_changed()` — sets `dimensions_changed = true`.
- **L431-448**: `monitor_dimensions()` — calls `mp.observe_property` on 11 properties.
- **L450-458**: `clamp(min, val, max)` — numeric clamp.
- **L460-465**: `clamp_point(top_left, point, bottom_right)` — applies clamp to x and y.

## Inputs / Outputs
- **Inputs**: mpv properties: video-out-params, keepaspect, video-unscaled, panscan, video-zoom, video-align-x/y, video-pan-x/y, osd-width, osd-height, video-rotate.
- **Outputs**: `_video_dimensions` cache: `{top_left, bottom_right, ratios}`.

## Side Effects
- `monitor_dimensions()` registers 11 property observers; these persist for the script lifetime.
- `get_video_dimensions()` modifies `_video_dimensions` and `dimensions_changed` module-level vars.

## Invariants
- `ratios.w > 0` and `ratios.h > 0` (provided video dimensions are non-zero).
- `top_left.x <= bottom_right.x` and `top_left.y <= bottom_right.y`.
- `split_scaling` ensures `dst_start < dst_end` (clamps to 0,1 if degenerate).

## Edge Cases
- If `video-out-params` is nil (no video loaded), returns nil — callers must handle.
- 90-degree rotation: w and h swap, dw and dh swap — correct mapping for rotated video.
- If `fheight == window_h` and `fwidth == window_w` (perfect fit), `vo_panscan_area = 0` — panscan has no effect.
- `unscaled == "downscale-big"`: treated as truthy (non-nil), forces fwidth/fheight = dw/dh only if dw<=window_w and dh<=window_h.
- `split_scaling` zoom at 0 means no zoom (2^0 = 1).

## mpv Interactions
- `mp.get_property_native("video-out-params")`, `mp.get_property_bool("keepaspect")`, `mp.get_property_number("video-rotate")`, `mp.get_osd_size()`, various `mp.get_property_number` calls.
- `mp.observe_property(p, "native", set_dimensions_changed)` × 11 in monitor_dimensions.
