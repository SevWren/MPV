# SEG-08 Reconciled Analysis
**Lines**: L1217-1419
**Description**: Page base class (OSD UI), EncodeWithProgress class

## Purpose
Page is the OSD UI base class providing the key-binding lifecycle, property observation, ASS OSD rendering, and show/hide/clear state management. EncodeWithProgress extends Page to show a live progress overlay during encode, parsing mpv's stderr output for time position and exit status.

## Line Walkthrough

### Page class (L1217-1328)
- `add_keybinds(self)`: Iterates `self.keybinds` table; calls `mp.add_forced_key_binding(key, key, func, {repeatable=true})` for each.
- `remove_keybinds(self)`: Calls `mp.remove_key_binding(key)` for each keybind.
- `observe_properties(self)`: Sets up a `sizeCallback` that calls `self:draw()` on OSD size changes. Observes `osd-width` and `osd-height`.
- `unobserve_properties(self)`: Calls `mp.unobserve_property(self.sizeCallback)`.
- `clear(self)`: Calls `mp.set_osd_ass(0, 0, "")` to clear OSD.
- `prepare(self)`: no-op in base.
- `dispose(self)`: no-op in base.
- `show(self)`: Sets `self.visible=true`, calls add_keybinds, observe_properties, prepare, draw.
- `hide(self)`: Sets `self.visible=false`, calls remove_keybinds, unobserve_properties, dispose, clear.
- `setup_text(self, ass)`: Configures ASS text style using font_size and margin from options.
- `__init`: Sets `self.keybinds = nil`.

### EncodeWithProgress class (L1329-1419)
- Extends Page.
- `__init(startTime, endTime)`: stores times, computes `duration = endTime - startTime`, sets `currentTime = startTime`.
- `draw()`: Renders progress percentage as ASS overlay.
- `parseLine(line)`: Parses ffmpeg stderr for "Encode time-pos: X" and "Exiting... (reason)".
- `startEncode(command_line)`:
  1. Copies command_line array.
  2. `append(copy_command_line, {})` — appends EMPTY TABLE (vestigial no-op, bug/artifact).
  3. Calls `self:show()`.
  4. Opens `run_subprocess_popen(copy_command_line)`.
  5. Loops over lines: parseLine + draw.
  6. Closes fd, hides.
  7. Returns `true` iff `finishedReason == "End of file"`.

## Edge Cases
- **Empty table append at L1365-1366**: `append(copy_command_line, {})` is a no-op. The empty table adds nothing. This is a vestigial artifact, possibly from MoonScript code that once appended additional flags here.
- `parseLine` only matches "Encode time-pos" and "Exiting..." patterns. Other stderr lines are silently ignored (no error handling).
- If the subprocess exits abnormally (killed, crash), `finishedReason` may never be set to "End of file" → returns false → caller treats as failure.
- `mp.add_forced_key_binding` with `repeatable=true` means holding a key repeats the action.
- Key names in `self.keybinds` are used as both the binding name and the key — potential collision if two pages use the same key name.
- `unobserve_property(self.sizeCallback)` — passes the function reference itself, requiring mpv to unobserve by function identity.

## mpv Interactions
- `mp.add_forced_key_binding(key, key, func, {repeatable=true})`
- `mp.remove_key_binding(key)`
- `mp.observe_property("osd-width", "native", sizeCallback)` and osd-height
- `mp.unobserve_property(sizeCallback)`
- `mp.set_osd_ass(w, h, text)`
- `mp.get_osd_size()`
- `assdraw.ass_new()` for rendering
