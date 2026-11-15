# SEG-15 Reconciled Analysis
**Lines**: L2639-2856
**Description**: MainPage class and bootstrap

## Purpose
MainPage is the top-level UI page — the entry point triggered by the "W" key. It manages start/end time selection, crop region, and dispatches to CropPage, EncodeOptionsPage, PreviewPage, or the encode() function.

## Line Walkthrough

### MainPage methods (L2643-2750)
- **L2644-2650**: `setStartTime(self)` — sets startTime from time-pos; redraws if visible.
- **L2651-2657**: `setEndTime(self)` — sets endTime from time-pos; redraws if visible.
- **L2658-2669**: `setupStartAndEndTimes(self)` — sets startTime=0 and endTime=duration if duration available; else sets both to -1.
- **L2671-2685**: `draw(self)` — renders main menu: "WebM maker", key hints (c/1/2/o/p/e/ESC).
- **L2686-2689**: `show(self)` — calls parent show(), then `emit_event("show-main-page")`.
- **L2690-2694**: `onUpdateCropRegion(self, updated, newRegion)` — updates `self.region` if updated; shows self.
- **L2696-2705**: `crop(self)` — hides self, creates CropPage with onUpdateCropRegion callback, shows CropPage.
- **L2707-2709**: `onOptionsChanged(self, updated)` — shows self (after options changed).
- **L2710-2719**: `changeOptions(self)` — hides self, creates EncodeOptionsPage with onOptionsChanged callback.
- **L2721-2723**: `onPreviewEnded(self)` — shows self (after preview ended).
- **L2724-2733**: `preview(self)` — hides self, creates PreviewPage, shows it.
- **L2735-2749**: `encode(self)` — validates startTime/endTime, calls `encode(self.region, startTime, endTime)`.

### MainPage __init (L2755-2814)
- Keybinds: c=crop, 1=setStartTime, 2=setEndTime, o=changeOptions, p=preview, e=encode, ESC=hide.
- Initial region is nil; times are nil (setupStartAndEndTimes will set them).

### Bootstrap (L2838-2855)
- **L2838**: `monitor_dimensions()` — registers 11 property observers.
- **L2839**: `mainPage = MainPage()` — creates the single instance.
- **L2840-2848**: `mp.add_key_binding(options.keybind, "display-webm-encoder", mainPage:show, {repeatable=false})` — binds the "W" key (or configured keybind).
- **L2849-2855**: `mp.register_event("file-loaded", mainPage:setupStartAndEndTimes)` — registers file-loaded event handler.

## State Machine
```
idle
  → (W key) → MainPage.show → visible
visible
  → (1) → setStartTime → visible
  → (2) → setEndTime → visible
  → (c) → CropPage.show → crop_active
  → (o) → EncodeOptionsPage.show → options_active
  → (p) → PreviewPage.show → preview_active
  → (e) → encode() → encoding → visible (after encode)
  → (ESC) → MainPage.hide → idle
crop_active
  → (1/2) → update point → crop_active
  → (ENTER) → callback(region) → visible
  → (ESC) → callback(nil) → visible
options_active
  → (UP/DOWN/LEFT/RIGHT) → option change → options_active
  → (ENTER) → confirmOpts → visible
  → (ESC) → cancelOpts → visible
preview_active
  → (ESC) → cancel → visible
```

## Edge Cases
- MainPage.encode: Does NOT validate that region is valid. Calls encode() with nil region. encode() / get_video_filters() handles nil region gracefully (skips crop filter).
- bootstrap: `options.keybind` is read at module load time — if changed via mpv-webm-set-options after load, the key binding is not updated.
- `mp.register_event("file-loaded", ...)` fires on every file load, resetting startTime/endTime.

## mpv Interactions
- `mp.add_key_binding(keybind, "display-webm-encoder", ...)` — primary entry point.
- `mp.register_event("file-loaded", ...)` — auto-sets times on file load.
- `mp.get_property_number("time-pos")` — in setStartTime, setEndTime.
- `mp.get_property_native("duration")` — in setupStartAndEndTimes.
