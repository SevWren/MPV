# SEG-14 Reconciled Analysis
**Lines**: L2539-2638
**Description**: PreviewPage class — live preview with crop applied

## Purpose
PreviewPage temporarily modifies the mpv video filter chain to add the crop region, sets the playback position to startTime, enables looping, and shows a live preview. On exit (ESC), it restores original properties.

## Line Walkthrough
- **L2544-2567**: `prepare(self)` — reads current vf, adds `{name="sub"}` filter and optionally a crop filter with region dimensions. Sets time-pos to startTime, enables looping, unpauses.
- **L2568-2574**: `dispose(self)` — restores `vf`, `time-pos`, and `pause` to saved originalProperties.
- **L2575-2582**: `draw(self)` — renders "Press ESC to exit preview." text overlay.
- **L2583-2590**: `cancel(self)` — calls callback() and hides.
- **L2591-2611**: `__init(self, callback, region, startTime, endTime)` — saves current vf, time-pos, pause. Binds ESC=cancel. Stores region and times.

## Side Effects
- `prepare` modifies mpv's `vf` property (adds filters).
- `prepare` changes `time-pos` and `pause` properties.
- `dispose` restores all three properties.
- If page is not properly hidden (crash/error), mpv properties are left modified.

## Edge Cases
- If `region:is_valid()` is false, only sub filter is added (no crop) — still useful for checking timing.
- If mpv is closed while preview is active, dispose may not run — properties permanently modified for session.
- Saving `originalProperties` at __init time (not at show time) — if vf changes between creation and show, those changes are captured.

## mpv Interactions
- `mp.get_property_native("vf")`, `mp.get_property_native("time-pos")`, `mp.get_property_native("pause")`: __init
- `mp.set_property_native("vf", ...)`, `mp.set_property_native("time-pos", ...)`, `mp.set_property_native("pause", ...)`: prepare, dispose
- `mp.get_osd_size()`, `mp.set_osd_ass()`: draw
