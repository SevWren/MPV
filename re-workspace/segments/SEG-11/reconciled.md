# SEG-11 Reconciled Analysis
**Lines**: L1886-2046
**Description**: CropPage class — interactive crop region selection UI

## Purpose
CropPage extends Page to provide an interactive crop selection overlay. The user moves a crosshair/box to define two points (A and B) that define the crop rectangle. The crop box is rendered as four dark rectangles around the selected region.

## Line Walkthrough
- **L1891-1908**: `reset(self)` — sets pointA to top-left of video, pointB to bottom-right (full screen crop).
- **L1909-1915**: `setPointA(self)` — gets current mouse position, sets pointA from screen coords.
- **L1916-1922**: `setPointB(self)` — same for pointB.
- **L1923-1926**: `cancel(self)` — calls `self.callback(nil)` and hides.
- **L1927-1932**: `finish(self)` — creates Region from pointA/B, calls `self.callback(region)`, hides.
- **L1933-1950**: `draw_box(self, ass)` — draws four dark overlay rectangles:
  - Top-left: (topleft.x, topleft.y) → (region.x, region.y+h)
  - Top-right: (region.x, topleft.y) → (bottomright.x, region.y)
  - Bottom-left: (topleft.x, region.y+h) → (region.x+w, bottomright.y)
  - Bottom-right: (region.x+w, region.y) → (bottomright.x, bottomright.y)
  This creates a "letterbox" effect around the crop region.
- **L1951-1966**: `draw(self)` — renders crop box + text overlay with key hints.
- **L1971-2018**: `__init(self, callback, region)`:
  - Creates pointA, pointB as VideoPoints.
  - Binds keys: "1"=setPointA, "2"=setPointB, "r"=reset, "ESC"=cancel, "ENTER"=finish.
  - Calls `self:reset()`.
  - If existing region provided, restores points from it.

## Inputs / Outputs
- **Input**: callback function, optional existing Region.
- **Output**: callback called with Region (or nil on cancel).

## Side Effects
- Renders OSD overlay.
- Binds/unbinds keys via Page base class.

## Invariants
- pointA and pointB initialized to full-screen region on construction (via reset).
- callback must be provided; cancel calls callback(nil), finish calls callback(region).

## Edge Cases
- `get_video_dimensions()` called in reset/setPointA/B — if nil (no video), indexing crashes.
- `mp.get_mouse_pos()` returns screen coordinates — accurate only if OSD matches display.
- Region from finish may have w=0 or h=0 if pointA == pointB — `is_valid()` returns true but encode would produce zero-dimension output.
- draw_box ASS rectangles use screen coordinates from `to_screen()` — accurate for current dimensions only.

## mpv Interactions
- `mp.get_osd_size()`: draw
- `mp.get_mouse_pos()`: setPointA, setPointB
- `assdraw.ass_new()`: draw
- `mp.set_osd_ass()`: draw
