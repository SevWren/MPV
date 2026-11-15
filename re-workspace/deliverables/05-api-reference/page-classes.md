# 05 — API Reference: Page Class Hierarchy

**Source hash**: sha256:3f454dc0ca030b591d659f7405a3ddfdf7585e5b5eb4cd5b3a573b4151b33214
**Generation date**: 2026-11-15

---

## Page (Base Class) — L1217-1328

### Fields
| Field | Type | Description |
|-------|------|-------------|
| keybinds | table or nil | Key→function mapping |
| visible | bool | Whether page is currently shown |

### Methods

#### `show(self)`
Sets visible=true; calls add_keybinds, observe_properties, prepare, draw.

#### `hide(self)`
Sets visible=false; calls remove_keybinds, unobserve_properties, dispose, clear.

#### `draw(self)`
Renders OSD. Must be overridden by subclasses.

#### `clear(self)`
Clears OSD with mp.set_osd_ass(0, 0, "").

#### `prepare(self)`
Pre-show hook. No-op in base; subclasses override.

#### `dispose(self)`
Post-hide hook. No-op in base; subclasses override.

#### `setup_text(self, ass)`
Applies font_size, margin from options to ASS draw context.

---

## EncodeWithProgress (extends Page) — L1329-1419

Displays real-time encoding progress by parsing mpv subprocess stderr.

### Fields
| Field | Type | Description |
|-------|------|-------------|
| startTime | float | Encode start time |
| endTime | float | Encode end time |
| duration | float | endTime - startTime |
| currentTime | float | Current time-pos from stderr |
| finishedReason | string | Last "Exiting..." reason |
| finished | bool | Whether exit was detected |

### Methods

#### `startEncode(self, command_line)` → bool
Copies command_line, calls show(), opens io.popen subprocess, parses each line. Returns true if finishedReason == "End of file".

#### `parseLine(self, line)`
Parses "Encode time-pos: X" and "Exiting... (reason)" from stderr.

---

## CropPage (extends Page) — L1886-2046

Interactive crop region selection.

### Construction
`CropPage(callback, region)` — callback receives Region on ENTER, nil on ESC.

### Key bindings
1=pointA, 2=pointB, r=reset, ESC=cancel, ENTER=finish.

---

## EncodeOptionsPage (extends Page) — L2211-2538

Options configuration UI.

### Construction
`EncodeOptionsPage(callback)` — callback() called on ENTER, callback(false) on ESC.

### Key bindings
UP/DOWN navigate, LEFT/RIGHT change value, ENTER=confirm, ESC=cancel.

---

## PreviewPage (extends Page) — L2539-2638

Live preview with crop applied.

### Construction
`PreviewPage(callback, region, startTime, endTime)` — saves current mpv properties.

### Key bindings
ESC=cancel and restore.

---

## MainPage (extends Page) — L2639-2836

Top-level UI. Singleton (mainPage).

### Key bindings
c=crop, 1=setStart, 2=setEnd, o=options, p=preview, e=encode, ESC=hide.
