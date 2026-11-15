# SEG-07 Reconciled Analysis
**Lines**: L1114-1216
**Description**: GIF format class

## Purpose
GIF is the most complex Format subclass. Its `postCommandModifier` completely rewrites the ffmpeg filter graph to implement a two-step GIF encoding pipeline: first generate a palette using palettegen, then apply it with paletteuse. It also integrates existing video filters (scale, crop, fps, eq) from the command into the lavfi filtergraph.

## Line Walkthrough
- **L1114**: `formats["mp3"] = MP3()` closes SEG-06.
- **L1115-1215**: `GIF` class definition.
  - `__init`: displayName="GIF", supportsTwopass=false, videoCodec="gif", audioCodec="", outputExtension="gif", acceptsBitrate=false.
  - `postCommandModifier(command, region, startTime, endTime)`:
    - Builds `cfilter` string starting with `[vid1]trim=start=X:end=Y[vidtmp]`.
    - Checks for `deinterlace` property; adds `yadif=mode=1` if set.
    - Iterates existing command flags; for `--vf-add=lavfi-scale`, `lavfi-crop`, `fps`, `lavfi-eq`: strips prefix and adds to filtergraph chain.
    - For `--video-rotate=90`: adds `transpose=1`.
    - Remaining flags kept as-is.
    - Appends `[vidtmp]split[vidtmp1][vidtmp2]` and palette generation/application chain.
    - Adds `--vf-add=lavfi=[filtergraph]`, `--of=lavfi`, `--ovc=gif`, `--gif-dither=N`.
- **L1216**: `formats["gif"] = GIF()` registered.

## Key Algorithm — GIF Palette Pipeline
```
[vid1]trim=start=X:end=Y[vidtmp]
→ [optional deinterlace/scale/crop/fps/eq]
→ [vidtmp]split[vidtmp1][vidtmp2]
→ [vidtmp1]palettegen=N[palette]
→ [vidtmp2][palette]paletteuse=dither=N[out]
```

This produces a palette-optimized GIF via ffmpeg's lavfi filtergraph.

## Edge Cases
- **L1123**: Uses raw seconds directly in `trim=start=X:end=Y` with `:` syntax. Comment notes "Fix: Use raw seconds directly to prevent colon syntax errors" — implies this was fixed from a previous version that used HH:MM:SS format.
- The filter graph uses `[vid1]` as input, which is a lavfi stream label — requires ffmpeg lavfi demuxer.
- If other command flags include `--vf-add=lavfi-` prefixed filters not in the handled list, they are silently dropped (not added to filtergraph or final command).
- `options.gif_dither` passed as a number to `--gif-dither`.
- If region is nil or invalid, crop filter may not be in command → trim directly feeds into split.

## mpv Interactions
- `mp.get_property("deinterlace")` — checked to add yadif filter.
