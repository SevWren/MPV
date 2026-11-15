# Algorithms Guild Report

## 1. Coordinate Transform: Screen ↔ Video Pixels

**Function**: `VideoPoint:set_from_screen(sx, sy)` and `VideoPoint:to_screen()`
**Lines**: L470-485

```
Screen to Video:
  d = get_video_dimensions()  → {top_left, bottom_right, ratios}
  clamped_x = clamp(d.top_left.x, sx, d.bottom_right.x)
  clamped_y = clamp(d.top_left.y, sy, d.bottom_right.y)
  video_x = floor(d.ratios.w * (clamped_x - d.top_left.x) + 0.5)
  video_y = floor(d.ratios.h * (clamped_y - d.top_left.y) + 0.5)

Video to Screen (inverse):
  screen_x = floor(video_x / d.ratios.w + d.top_left.x + 0.5)
  screen_y = floor(video_y / d.ratios.h + d.top_left.y + 0.5)
```

Rounding: +0.5 before floor = nearest-integer rounding.

## 2. Panscan/Zoom Geometry

**Function**: `get_video_dimensions()` → `split_scaling()`
**Lines**: L341-425

The video display rectangle within the OSD window is computed as:
1. Start with fitted size (maintaining aspect ratio): fwidth × fheight.
2. Add panscan expansion: `scaled_width = fwidth + floor(vo_panscan_area * panscan * f_w)`.
3. For each axis, compute start/end pixel with zoom and alignment:
   - `scaled_src = floor(scaled_src_size * 2^zoom)`
   - `align = (align + 1) / 2`  (normalize from [-1,1] to [0,1])
   - `dst_start = floor((dst_size - scaled_src) * align + pan * scaled_src)`
   - `dst_end = dst_start + scaled_src`

## 3. Time Formatting

**Function**: `seconds_to_time_string(seconds, no_ms, full)`
**Lines**: L93-106

```
if full or seconds > 3600:
  format: "H:MM:SS[.mmm]"
else:
  format: "MM:SS[.mmm]"
```

Milliseconds: `seconds * 1000 % 1000` (integer modulo arithmetic)
Hours: `floor(seconds / 3600)`
Minutes: `floor(seconds / 60) % 60`
Seconds: `floor(seconds) % 60`

For path use: colons replaced with dots (`seconds_to_path_element`).

## 4. Bitrate Calculation

**Function**: `calculate_bitrate(active_tracks, format, length)`
**Lines**: L1657-1671

```
input: target_filesize (KB), length (seconds)
total_kilobits = target_filesize * 8

non-strict, video format:
  video_bitrate = floor(total_kilobits / length)   [kbps]
  audio_bitrate = nil (not constrained)

strict AND has_audio:
  audio_kilobits = length * strict_audio_bitrate    [kbps * s = kb]
  video_kilobits = total_kilobits - audio_kilobits
  video_bitrate = floor(video_kilobits / length)    [kbps]
  audio_bitrate = floor(audio_kilobits / length) = strict_audio_bitrate  [kbps]

audio-only (videoCodec == ""):
  audio_bitrate = target_filesize * 8 / length  [kbps]
  video_bitrate = nil
```

**Note**: `strict_bitrate_multiplier` option is declared but never applied.

## 5. Shell Escaping

**Function**: `shell_escape(args)`
**Lines**: L283-301

```
For each arg in argv:
  if arg contains non-safe chars ([^A-Za-z0-9_/:=-]):
    if Windows: wrap in " with internal " → \"
    if POSIX:   wrap in ' with internal ' → '\''

concatenate with spaces

if Windows: wrap entire result in " "
```

**Safe chars**: `A-Za-z0-9`, `_`, `/`, `:`, `=`, `-`
Notably excluded from "safe": `.`, `~`, `+`, `,`, `@`, `#`, `%`

## 6. Property Template Expansion

**Function**: `expand_properties(text, magic)`
**Lines**: L123-173

Supported patterns (magic default = "$"):
- `${prop}` → mp.get_property_osd(prop)
- `${=prop}` → mp.get_property(prop) (raw value)
- `${prop:fallback}` → value or fallback if error
- `${?prop:text}` → text if prop truthy
- `${!prop:text}` → text if prop falsy
- `${?prop==val:text}` → text if prop == val
- `${!prop==val:text}` → text if prop != val

Expansion is recursive (expand_properties(prop_value)).

## 7. Output Filename Generation

**Function**: `format_filename(startTime, endTime, videoFormat)`
**Lines**: L175-239

Two-stage substitution:
1. First-pass aliases: `%mp` → `%mH.%mM.%mS`, `%p` → `%wH.%wM.%wS`, etc.
2. Time substitutions: `%wH/%wM/%wS/%wh` (start), `%mH/%mM/%mS/%mh` (end)
3. Property expansion: `%F`, `%T`, `%M` → via expand_properties()
4. Sanitization: replaces `%s%e` with safe versions.

## 8. IEEE-754 Double Encode/Decode

**Function**: `read_double(bytes)`, `write_double(num)`
**Lines**: L563-617

```
read_double (big-endian 8-byte array):
  sign = bytes[1] > 127 ? -1 : 1
  exponent = (bytes[1] % 128) * 16 + floor(bytes[2] / 16)
  mantissa = bytes[2] % 16, then accumulate bytes[3..8] (* 256 each)
  if exponent == 0: return 0
  mantissa = (ldexp(mantissa, -52) + 1) * sign
  return ldexp(mantissa, exponent - 1023)

write_double (num → big-endian 8-byte array):
  if num == 0: return 8 zeros
  if num < 0: sign=1, num = -num
  use math.frexp to get mantissa_f, exponent
  exponent += 1022
  mantissa_i = floor(mantissa_f * 2^53)
  encode sign + exponent + mantissa into 8 bytes
```

**Note on get_duration bug**: Uses `reversed_binary_duration` (undefined) instead of `big_endian_binary_duration`. This would cause a nil error if called, but `vp8_patch_logfile` only calls `set_duration`, never `get_duration`.

## 9. GIF Palette Filter Graph Construction

**Function**: `GIF:postCommandModifier()`
**Lines**: L1120-1210

```
cfilter = "[vid1]trim=start=X:end=Y[vidtmp]"
if deinterlace: "[vidtmp]yadif=mode=1[vidtmp];"
for each known --vf-add=lavfi- filter: strip prefix, append to chain
for --video-rotate=90: append "transpose=1"
"[vidtmp]split[vidtmp1][vidtmp2]"
"[vidtmp1]palettegen=N[palette]"  (N = options.gif_dither)
"[vidtmp2][palette]paletteuse=dither=N[out]"
→ "--vf-add=lavfi=cfilter"
→ "--of=lavfi" "--ovc=gif"
```

## 10. VP8 Firstpass Log Patching

**Function**: `vp8_patch_logfile(logfile_path, encode_total_duration)`
**Lines**: L736-749

Purpose: VP8 2-pass needs consistent frame duration in the firstpass log. After first pass with arbitrary timing, the script normalizes all frame durations to the average.

```
read binary log → array of FirstpassStats (144-byte records)
n = #stats_array
average_duration = encode_total_duration / n
for i = 1 to n-1: stats[i]:set_duration(average_duration)
stats[n]:set_duration(encode_total_duration)  (last frame gets total)
write binary log back
```

## 11. ASS Crop Box Drawing

**Function**: `CropPage:draw_box(ass)`
**Lines**: L1933-1950

Draws 4 rectangles to create a "letterbox" (vignette) effect around the crop region:
```
Top band:    (top_left.x, top_left.y) → (region.x + region.w, region.y)
Actually: 4 rectangles positioned:
  TL:  (d.top_left.x, d.top_left.y)      → (region.x, region.y+h)         [left of crop]
  TR:  (region.x, d.top_left.y)           → (d.bottom_right.x, region.y)   [top of crop]
  BL:  (d.top_left.x, region.y+h)        → (region.x+w, d.bottom_right.y) [bottom of crop]
  BR:  (region.x+w, region.y)             → (d.bottom_right.x, d.bottom_right.y) [right of crop]
```
Color: black (H000000), 47% transparency (alpha H77).
