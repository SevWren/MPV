# UI/State Guild Report

## Overview

The UI system consists of four Page subclasses managed by a callback-based navigation model. Only one page is active at a time. The base Page class handles key binding lifecycle, OSD rendering, and property observation.

## State Machine

```
[IDLE]
  W key → MainPage:show()

[MAIN]  (MainPage visible)
  Keys: c, 1, 2, o, p, e, ESC
  1 → setStartTime (time-pos → self.startTime)
  2 → setEndTime (time-pos → self.endTime)
  c → MainPage:hide() → CropPage:show()
  o → MainPage:hide() → EncodeOptionsPage:show()
  p → MainPage:hide() → PreviewPage:show()
  e → MainPage:hide() → encode() → back to MAIN
  ESC → MainPage:hide() → [IDLE]

[CROP]  (CropPage visible)
  Keys: 1, 2, r, ESC, ENTER
  1 → pointA = mouse_pos
  2 → pointB = mouse_pos
  r → reset (full screen)
  ESC → callback(nil) → CropPage:hide() → MainPage:show()
  ENTER → callback(region) → CropPage:hide() → MainPage:show()

[OPTIONS]  (EncodeOptionsPage visible)
  Keys: UP, DOWN, LEFT, RIGHT, ENTER, ESC
  UP/DOWN → prevOpt/nextOpt (skips invisible)
  LEFT/RIGHT → current option value change
  ENTER → confirmOpts() → apply to global options → EncodeOptionsPage:hide() → MainPage:show()
  ESC → cancelOpts() → EncodeOptionsPage:hide() → MainPage:show()

[PREVIEW]  (PreviewPage visible)
  Keys: ESC
  ESC → cancel() → PreviewPage:hide() (restores vf/time-pos/pause) → MainPage:show()
  (mpv plays looped preview with crop applied)
```

## Page Lifecycle

```
show():
  1. self.visible = true
  2. add_keybinds()   → mp.add_forced_key_binding × N
  3. observe_properties()  → mp.observe_property(osd-width/height)
  4. prepare()   (subclass override)
  5. draw()

hide():
  1. self.visible = false
  2. remove_keybinds()   → mp.remove_key_binding × N
  3. unobserve_properties()   → mp.unobserve_property(sizeCallback)
  4. dispose()   (subclass override)
  5. clear()   → mp.set_osd_ass(0, 0, "")
```

## Key Binding Notes

- All in-page keys use `mp.add_forced_key_binding` — they override mpv's default key handlers.
- The main entry key uses `mp.add_key_binding` (non-forced, can be overridden by mpv bindings).
- Key names used as both binding name and key — no namespacing. If two pages use the same key name (e.g., "ESC" or "ENTER"), the second show() call would shadow the first. This is safe in practice because only one page is active at a time.
- `repeatable=true` on forced keybinds means holding a key repeats the action.

## OSD Rendering

All pages use `assdraw.ass_new()` and `mp.set_osd_ass(w, h, text)`. Rendering is triggered:
- Explicitly: each key action calls `self:draw()`.
- Automatically: OSD size change triggers `sizeCallback` → `self:draw()`.

## MainPage Display

```
WebM maker

c: crop
1: set start time (current is HH:MM:SS.mmm)
2: set end time (current is HH:MM:SS.mmm)
o: change encode options
p: preview
e: encode

ESC: close
```

## Callback Pattern

Navigation uses callback functions passed from parent to child:
```
MainPage creates CropPage(callback=self.onUpdateCropRegion, region=self.region)
CropPage calls callback(newRegion) on ENTER or callback(nil) on ESC
onUpdateCropRegion(updated, newRegion): updates self.region if updated, then self:show()
```

This pattern avoids circular references and keeps pages independent.

## Edge Cases and Bugs

- If encode() runs synchronously (non-detached), the UI is hidden during the encode (hide called before encode). No timeout or cancellation mechanism.
- If CropPage is shown with nil get_video_dimensions() (no video), reset() crashes.
- PreviewPage saves properties at __init time, not show() time. If vf changes between creation and show, those changes are captured in originalProperties.
