# Step 1A — Log Evidence

## 1. Exact mpv version string
`mpv v0.42.0-41-g649001d4e2`
[log:2] `[   0.000][v][cplayer] mpv v0.42.0-41-g649001d4e2 Copyright © 2000-2026 mpv/MPlayer/mplayer2 projects`

## 2. Build date and commit
`built on Nov 14 2026 12:34:42`
[log:3] `[   0.000][v][cplayer]  built on Nov 14 2026 12:34:42`
Commit: `649001d4e2` (from version string; build directory: `mpv-x86_64-20261114-git-649001d4e2`)

## 3. Every [webm] log line verbatim
[log:179] `[   0.047][d][webm] Loading lua script C:\Users\mmuel\AppData\Roaming/mpv/scripts/webm.lua...`
[log:187] `[   0.049][d][webm] loading mp.defaults`
[log:212] `[   0.054][d][webm] loading file C:\Users\mmuel\AppData\Roaming/mpv/scripts/webm.lua`
[log:286] `[   0.066][d][webm] reading options for webm`
[log:298] `[   0.068][v][webm] Opened config file script-opts/webm.conf.`
[log:337] `[   0.081][v][webm] Loaded mpv-webm script!`
[log:1280] `[  19.931][i][webm] Encoding to D:\ProgramData\asus/Rockford_High-School-Marching-Band-2026-BOA-Grand-National-Championships-Prelimi_001_1080p-[00.00.567-00.01.469]-audio.mp4`
[log:1281] `[  19.931][v][webm] Command line: mpv D:\Videos\Rockford_High-School-Marching-Band-2026-BOA-Grand-National-Championships-Prelimi_001_1080p.mp4 --start=0:00:00.567 --end=0:00:01.469 --loop-file=no --no-pause --ovc=libx264 --oac=aac --vid=1 --aid=1 --sid=no --sub-ass-override=force --sub-auto=fuzzy --sub-pos=97.000000 --sub-delay=0.000000 --video-rotate=0 --ytdl-format=bv*[height<=1080]+ba/b[height<=1080] --deinterlace=no --vf-add=lavfi-scale=-2:720 --vf-add=lavfi-eq=contrast=1:saturation=1:brightness=0 --ovcopts-add=b=86939k cq-level=28 --o=D:\ProgramData\asus/Rockford_High-School-Marching-Band-2026-BOA-Grand-National-Championships-Prelimi_001_1080p-[00.00.567-00.01.469]-audio.mp4`
[log:1442] `[  59.112][d][webm] Destroying client handle...`

## 4. Complete subprocess args array from Run command
[log:1282] Full line:
```
[  19.931][d][cplayer] Run command: run, flags=64, args=[command="mpv", args="D:\\Videos\\Rockford_High-School-Marching-Band-2026-BOA-Grand-National-Championships-Prelimi_001_1080p.mp4", args="--start=0:00:00.567", args="--end=0:00:01.469", args="--loop-file=no", args="--no-pause", args="--ovc=libx264", args="--oac=aac", args="--vid=1", args="--aid=1", args="--sid=no", args="--sub-ass-override=force", args="--sub-auto=fuzzy", args="--sub-pos=97.000000", args="--sub-delay=0.000000", args="--video-rotate=0", args="--ytdl-format=bv*[height<=1080]+ba/b[height<=1080]", args="--deinterlace=no", args="--vf-add=lavfi-scale=-2:720", args="--vf-add=lavfi-eq=contrast=1:saturation=1:brightness=0", args="--ovcopts-add=b=86939k", args="cq-level=28", args="--o=D:\\ProgramData\\asus/Rockford_High-School-Marching-Band-2026-BOA-Grand-National-Championships-Prelimi_001_1080p-[00.00.567-00.01.469]-audio.mp4"]
```

Parsed argv:
```
["mpv",
 "D:\\Videos\\Rockford_High-School-Marching-Band-2026-BOA-Grand-National-Championships-Prelimi_001_1080p.mp4",
 "--start=0:00:00.567",
 "--end=0:00:01.469",
 "--loop-file=no",
 "--no-pause",
 "--ovc=libx264",
 "--oac=aac",
 "--vid=1",
 "--aid=1",
 "--sid=no",
 "--sub-ass-override=force",
 "--sub-auto=fuzzy",
 "--sub-pos=97.000000",
 "--sub-delay=0.000000",
 "--video-rotate=0",
 "--ytdl-format=bv*[height<=1080]+ba/b[height<=1080]",
 "--deinterlace=no",
 "--vf-add=lavfi-scale=-2:720",
 "--vf-add=lavfi-eq=contrast=1:saturation=1:brightness=0",
 "--ovcopts-add=b=86939k",
 "cq-level=28",
 "--o=D:\\ProgramData\\asus/Rockford_High-School-Marching-Band-2026-BOA-Grand-National-Championships-Prelimi_001_1080p-[00.00.567-00.01.469]-audio.mp4"]
```

**KEY OBSERVATION**: Token `cq-level=28` appears at index 21 WITHOUT a `--` prefix. It is not a valid mpv option token.

## 5. Options set from mpv.conf (lines matching "Setting option")
[log:40] `Setting option 'log-file' = 'C:\Users\Public\mpv-log.txt'`
[log:41] `Setting option 'autocreate-playlist' = 'same'`
[log:42] `Setting option 'directory-filter-types' = 'ts'`
[log:43] `Setting option 'ytdl-format' = 'bv*[height<=1080]+ba/b[height<=1080]'`
[log:44] `Setting option 'ytdl-raw-options' = 'format-sort="res,fps"'`
[log:45] `Setting option 'resume-playback' = 'no'`
[log:46] `Setting option 'slang' = 'en'`
[log:47] `Setting option 'sub-auto' = 'no'`
[log:48] `Setting option 'sub-ass-override' = 'force'`
[log:49] `Setting option 'sub-font-provider' = 'auto'`
[log:50] `Setting option 'sub-auto' = 'fuzzy'`
[log:51] `Setting option 'sub-bold' = 'yes'`
[log:61] `Setting option 'save-position-on-quit' = 'yes'`
[log:62] `Setting option 'keep-open' = 'yes'`
[log:63] `Setting option 'border' = 'no'`
[log:77] `Setting option 'hwdec' = 'auto-copy'`

## 6. Source file codec/resolution/fps from [cplayer] track info
[log:1372] `[cplayer]  ● Video  --vid=1  (h264 1920x1080 59.8817 fps 5106 kbps) [default]`
[log:1373] `[cplayer]  ● Audio  --aid=1  (aac 2ch 44100 Hz 128 kbps) [default]`
Source file: `D:\Videos\Rockford_High-School-Marching-Band-2026-BOA-Grand-National-Championships-Prelimi_001_1080p.mp4`

## 7. Encode start timestamp and output path
[log:1280] Timestamp: `19.931` seconds
Output path: `D:\ProgramData\asus/Rockford_High-School-Marching-Band-2026-BOA-Grand-National-Championships-Prelimi_001_1080p-[00.00.567-00.01.469]-audio.mp4`

## 8. Error lines ([e] prefix)
[log:36] `[   0.000][e][cplayer] Invalid message level 'verbose'`
[log:37] `[   0.000][e][cplayer] Error parsing option msg-level (option parameter could not be parsed)`
[log:38] `[   0.000][e][cplayer] C:\Users\mmuel\AppData\Roaming/mpv/mpv.conf:2: setting option msg-level='webm=verbose' failed.`
(These are startup config errors, not encode-related.)
[log:351] `[   0.090][e][contact_sheet] Subprocess failed: init` (unrelated to webm encode)

No error lines appear after the encode command is issued at log:1282.
