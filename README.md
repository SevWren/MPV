# MPV
Some of my Mpv Scripts & Script Configs etc


# MPV Scripts

Here is a list of Lua scripts included in this repository, each enhancing MPV's functionality in various ways.

- **SmartCopyPaste.lua**: Automatically detects and pastes copied URLs into MPV, streamlining the video playback process.
- **autoload.lua**: Loads files in the current directory automatically into the playlist when a video is opened.
- **collab_notebook_sub.lua**: Provides an interactive subtitle styling editor that mirrors the Google Colab Notebook subtitle controls. Features include real-time preview of font size, color, outline, shadow, position, and margins via an ASS overlay menu, plus JSON export of settings for use in Colab notebooks.
- **contact-sheet.lua**: Generates a contact sheet (a series of thumbnails) from the currently playing video.
- **gallery-thumbgen.lua**: Creates thumbnail images for a directory of videos, ideal for gallery or media management.
- **mpv_screenshot.lua**: Adds advanced screenshot functionality, including custom filename formatting and save locations.
- **pause-when-minimize.lua**: Automatically pauses the video when the MPV window is minimized and resumes playback when restored.
- **playlist-view.lua**: Provides an on-screen playlist viewer for easily navigating through the loaded playlist.
- **playlistmanager.lua**: Enhances playlist management with features like sorting, reordering, and advanced navigation.
- **seek-to.lua**: Allows for quick seeking to specific timestamps in the video using on-screen prompts.
- **seek_custom_timestamp.lua**: Enables precise seeking to custom timestamps defined by the user.
- **webm.lua**: Adds the ability to create WebM/MP4 video clips directly from the currently playing video. Fixed timestamp handling for ffmpeg filter syntax and removed unavailable fifo filter from GIF encoding chain.
- **ytdl_hook.lua**: Integrates `youtube-dl` or `yt-dlp` to stream online videos directly in MPV by pasting URLs.

Each script can be installed and customized to extend the functionality of MPV to fit your workflow.

# MPV Configuration Files

Top-level MPV configuration files that customize global player behavior.

- **input.conf**: Custom key bindings for subtitle styling (font size, color, outline, shadow, position, margins), playback control (seeking, speed, frame stepping, A-B loop), audio/subtitle switching, screenshot capture, and hardware decoding toggle.
- **mpv.conf**: Global MPV settings including YouTube resolution limits (1080p cap, strict 360p sort fix), subtitle style defaults (ASS override, font, border, shadow, margins), image display duration, looping profiles for GIF/WebP/MP4, window geometry and borderless mode, screenshot directory, and high-quality playback profile with auto-copy hardware decoding.

# Script Configuration Files

These are the configuration files (`.conf`) associated with the Lua scripts, allowing you to customize their behavior.

- **SmartCopyPaste.conf**: Configuration for `SmartCopyPaste.lua`, specifying how URLs are handled and pasted into MPV.
- **autoload.conf**: Options for `autoload.lua`, such as file types to include or exclude when loading a playlist automatically.
- **collab_notebook_sub.conf**: Configuration for `collab_notebook_sub.lua`, controlling the hotkey cheatsheet visibility and duration.
- **encode_slice.conf**: Settings for encoding a specific slice or segment of the video, such as quality and format options.
- **encode_webm.conf**: Configuration for `webm.lua`, defining parameters for creating WebM clips like bitrate, resolution, and audio settings.
- **gallery-thumbgen.conf**: Configuration for `gallery-thumbgen.lua`, setting thumbnail generation options like output size and interval.
- **gallery_worker.conf**: Supports `gallery-thumbgen.lua` with additional worker settings for batch thumbnail generation.
- **gif.conf**: Configuration for creating GIFs from videos, including frame rate, resolution, and looping options. Updated output directory to `D:\ProgramData\asus`.
- **playlist_view.conf**: Options for `playlist-view.lua`, such as display style, color, and sort order for the playlist viewer.
- **playlistmanager.conf**: Settings for `playlistmanager.lua`, like sorting preferences, hotkeys, and display formats.
- **seek_custom_timestamp.conf**: Configurations for `seek_custom_timestamp.lua`, defining custom seek points and related key bindings. Removed custom key bindings for `/` and `?`.
- **webm.conf**: Additional settings for WebM/MP4 encoding, like codec choices, compression levels, output directory (`D:\ProgramData\asus`), target filesize (9800 kB), strict filesize constraint, encoding threads, font size, and margin. Default output format set to MP4 (H.264).

Customize these files to tailor the behavior of each script according to your preferences.
