# SEG-13 Reconciled Analysis
**Lines**: L2211-2538
**Description**: EncodeOptionsPage class — the encoding options configuration UI

## Purpose
EncodeOptionsPage is the main options configuration page. It presents 11 Option widgets in a scrollable list (navigation with UP/DOWN arrows, value change with LEFT/RIGHT). Confirming applies values to the `options` global and calls the callback.

## Line Walkthrough
- **L2216-2218**: `getCurrentOption()` — returns `self.options[self.currentOption][2]` (the Option widget).
- **L2219-2226**: `leftKey()`/`rightKey()` — delegates to current option's leftKey/rightKey; redraws.
- **L2227-2244**: `prevOpt()`/`nextOpt()` — moves currentOption up/down, skipping invisible options.
- **L2245-2253**: `confirmOpts()` — iterates `self.options`, applies `options[key] = widget:getValue()` to global `options`; calls `callback()`.
- **L2254-2257**: `cancelOpts()` — calls `callback(false)`.
- **L2258-2278**: `draw()` — renders all visible options as ASS text; highlights currentOption in bold.
- **L2279-2511**: `__init(self, callback)` — builds 11 Option widgets:

| # | Key | Type | Values |
|---|-----|------|--------|
| 1 | output_format | list | webm-vp8, webm-vp9, mp4, mp4-nvenc, raw, mp3, gif |
| 2 | twopass | bool | true/false |
| 3 | apply_current_filters | bool | |
| 4 | scale_height | list | -1(no), 144, 240, 360, 480, 540, 720, 1080, 1440, 2160 |
| 5 | strict_filesize_constraint | bool | |
| 6 | write_filename_on_metadata | bool | |
| 7 | target_filesize | int | min=0, step=250 |
| 8 | crf | int | min=-1, step=1; -1 displays as "disabled" |
| 9 | fps | list | -1(source), 15, 24, 30, 48, 50, 60, 120, 240 |
| 10 | gif_dither | list | 0-5 (bayer_scale 0-5), 6 (sierra2_4a) — VISIBLE only when format=gif |
| 11 | force_square_pixels | bool | |

- Keybinds: LEFT, RIGHT, UP, DOWN, ENTER (confirmOpts), ESC (cancelOpts).

## Edge Cases
- **"raw" format in formatIds (L2368)**: `formats["raw"]` is nil — `formats["raw"].displayName` at L2380 would crash. This is a potential runtime error when EncodeOptionsPage is instantiated.
- confirmOpts sets `options.output_format` to the list widget's getValue() which returns the registry key (e.g., "mp4"), so the initial mismatch (default "mp4 (h264/AAC)") is resolved after first confirm.
- gif_dither option has `visibleCheckFn` that checks if output_format option widget's value is "gif".
- `twopass` option is always visible regardless of format support; no visibleCheckFn for formats with `supportsTwopass=false`.

## Security Notes
- confirmOpts writes directly to global `options` table with values from UI widgets — values are constrained by Option widget ranges, so injection is not possible through the UI.
