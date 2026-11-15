# mpv API Surface Guild Report

## Complete API Inventory

### Properties Read (mp.get_property*)

| Property | Type | Function | Line(s) |
|----------|------|----------|---------|
| video-out-params | native | get_video_dimensions | L345 |
| keepaspect | bool | get_video_dimensions | L350 |
| video-rotate | number | get_video_dimensions | L355 |
| video-unscaled | native | get_video_dimensions | L366 |
| panscan | number | get_video_dimensions | L367 |
| video-zoom | number | get_video_dimensions | L409 |
| video-align-x | number | get_video_dimensions | L410 |
| video-pan-x | number | get_video_dimensions | L411 |
| video-align-y | number | get_video_dimensions | L413 |
| video-pan-y | number | get_video_dimensions | L414 |
| path | string | find_path | L1674 |
| file-format | string | find_path | L1681 |
| track-list | native | get_active_tracks | L1431 |
| mute | bool | get_active_tracks | L1423 |
| sub-visibility | bool | get_active_tracks | L1424 |
| brightness | string | get_contrast_brightness_saturation | L1526 |
| contrast | string | get_contrast_brightness_saturation | L1527 |
| saturation | string | get_contrast_brightness_saturation | L1528 |
| vf | native | apply_current_filters, PreviewPage | L1598, L2544 |
| sub-ass-override | string | get_playback_options | L1565 |
| sub-ass-vsfilter-aspect-compat | string | get_playback_options | L1567 |
| sub-auto | string | get_playback_options | L1568 |
| sub-pos | string | get_playback_options | L1569 |
| sub-delay | string | get_playback_options | L1570 |
| video-rotate | string | get_playback_options | L1571 |
| ytdl-format | string | get_playback_options | L1572 |
| deinterlace | string | get_playback_options, GIF | L1573, L1125 |
| speed | native | get_speed_flags | L1579 |
| filename/no-ext | string | get_metadata_flags | L1591 |
| time-pos | number | MainPage.setStartTime/EndTime | L2645, L2652 |
| time-pos | native | PreviewPage.__init | L2595 |
| pause | native | PreviewPage.__init | L2596 |
| duration | native | MainPage.setupStartAndEndTimes | L2659, L2661 |

### Properties Set (mp.set_property*)

| Property | Value | Function | Line |
|----------|-------|----------|------|
| vf | filter table | PreviewPage.prepare | ~L2560 |
| vf | original value | PreviewPage.dispose | ~L2570 |
| time-pos | startTime | PreviewPage.prepare | ~L2563 |
| time-pos | original | PreviewPage.dispose | ~L2572 |
| pause | false | PreviewPage.prepare | ~L2564 |
| pause | original | PreviewPage.dispose | ~L2573 |

### Observed Properties (mp.observe_property)

| Property | Callback | Registered At |
|----------|----------|--------------|
| keepaspect | set_dimensions_changed | monitor_dimensions L446 |
| video-out-params | set_dimensions_changed | monitor_dimensions L446 |
| video-unscaled | set_dimensions_changed | monitor_dimensions L446 |
| panscan | set_dimensions_changed | monitor_dimensions L446 |
| video-zoom | set_dimensions_changed | monitor_dimensions L446 |
| video-align-x | set_dimensions_changed | monitor_dimensions L446 |
| video-pan-x | set_dimensions_changed | monitor_dimensions L446 |
| video-align-y | set_dimensions_changed | monitor_dimensions L446 |
| video-pan-y | set_dimensions_changed | monitor_dimensions L446 |
| osd-width | set_dimensions_changed | monitor_dimensions L446 |
| osd-height | set_dimensions_changed | monitor_dimensions L446 |
| osd-width | Page.sizeCallback | Page.observe_properties L~1247 |
| osd-height | Page.sizeCallback | Page.observe_properties L~1247 |

### Commands (mp.commandv, mp.command_native)

| Command | Args | Function | Line |
|---------|------|----------|------|
| script-message | "webm-"+event_name | emit_event | L65 |
| expand-path | path | parse_directory | L~250 |
| dump_cache | start, end, path | find_path (HLS) | L1683 |

### Key Bindings

| Key | Name | Type | Registered At |
|-----|------|------|--------------|
| options.keybind (W) | display-webm-encoder | mp.add_key_binding | L2840 |
| (per-page keys) | (key name) | mp.add_forced_key_binding | Page.add_keybinds L1226 |

**MainPage keys**: c, 1, 2, o, p, e, ESC
**CropPage keys**: 1, 2, r, ESC, ENTER
**EncodeOptionsPage keys**: LEFT, RIGHT, UP, DOWN, ENTER, ESC
**PreviewPage keys**: ESC

### Script Messages

| Message | Handler | Line |
|---------|---------|------|
| mpv-webm-set-options | test_set_options | L74 |

### Events

| Event | Handler | Line |
|-------|---------|------|
| file-loaded | mainPage:setupStartAndEndTimes | L2849 |

### OSD Functions

| Function | Used In |
|---------|---------|
| mp.osd_message(text, duration) | message() |
| mp.set_osd_ass(w, h, text) | Page.show, CropPage.draw, EncodeWithProgress.draw, MainPage.draw |
| mp.get_osd_size() | calculate_scale_factor, Page, all draw functions |
| assdraw.ass_new() | all draw functions |

### Subprocess Functions

| Function | Used For |
|---------|---------|
| mp.utils.subprocess(params) | run_subprocess — blocking, argv |
| mp.utils.subprocess_detached(params) | encode() run_detached mode |
| mp.utils.file_info(name) | file_exists() |
| mp.utils.parse_json(json) | test_set_options |
| mp.utils.join_path(dir, file) | encode() output path |
| mp.utils.split_path(path) | encode() output directory |
| io.popen(command) | run_subprocess_popen — progress display |

## Notes

- `mp.add_forced_key_binding` is used for all in-page keys (overrides all other handlers including mpv defaults).
- `mp.add_key_binding` is used only for the main trigger key (non-forced).
- 13 property observers are registered at startup and never unregistered.
- PreviewPage observers are registered/unregistered via show/hide lifecycle.
