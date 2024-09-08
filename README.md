# MPV
Some of my Mpv Scripts & Script Configs etc


# MPV Scripts

Here is a list of Lua scripts included in this repository, each enhancing MPV's functionality in various ways.

- **SmartCopyPaste.lua**: Automatically detects and pastes copied URLs into MPV, streamlining the video playback process.
- **autoload.lua**: Loads files in the current directory automatically into the playlist when a video is opened.
- **contact-sheet.lua**: Generates a contact sheet (a series of thumbnails) from the currently playing video.
- **gallery-thumbgen.lua**: Creates thumbnail images for a directory of videos, ideal for gallery or media management.
- **mpv_screenshot.lua**: Adds advanced screenshot functionality, including custom filename formatting and save locations.
- **pause-when-minimize.lua**: Automatically pauses the video when the MPV window is minimized and resumes playback when restored.
- **playlist-view.lua**: Provides an on-screen playlist viewer for easily navigating through the loaded playlist.
- **playlistmanager.lua**: Enhances playlist management with features like sorting, reordering, and advanced navigation.
- **seek-to.lua**: Allows for quick seeking to specific timestamps in the video using on-screen prompts.
- **seek_custom_timestamp.lua**: Enables precise seeking to custom timestamps defined by the user.
- **webm.lua**: Adds the ability to create WebM video clips directly from the currently playing video.
- **ytdl_hook.lua**: Integrates `youtube-dl` or `yt-dlp` to stream online videos directly in MPV by pasting URLs.

Each script can be installed and customized to extend the functionality of MPV to fit your workflow.

# Script Configuration Files
These are the configuration files (`.conf`) associated with the Lua scripts, allowing you to customize their behavior.
- **SmartCopyPaste.conf**: Configuration for `SmartCopyPaste.lua`, specifying how URLs are handled and pasted into MPV.
- **autoload.conf**: Options for `autoload.lua`, such as file types to include or exclude when loading a playlist automatically.
- **encode_slice.conf**: Settings for encoding a specific slice or segment of the video, such as quality and format options.
- **encode_webm.conf**: Configuration for `webm.lua`, defining parameters for creating WebM clips like bitrate, resolution, and audio settings.
- **gallery-thumbgen.conf**: Configuration for `gallery-thumbgen.lua`, setting thumbnail generation options like output size and interval.
- **gallery_worker.conf**: Supports `gallery-thumbgen.lua` with additional worker settings for batch thumbnail generation.
- **gif.conf**: Configuration for creating GIFs from videos, including frame rate, resolution, and looping options.
- **playlist_view.conf**: Options for `playlist-view.lua`, such as display style, color, and sort order for the playlist viewer.
- **playlistmanager.conf**: Settings for `playlistmanager.lua`, like sorting preferences, hotkeys, and display formats.
- **seek_custom_timestamp.conf**: Configurations for `seek_custom_timestamp.lua`, defining custom seek points and related key bindings.
- **webm.conf**: Additional settings for WebM encoding, like codec choices, compression levels, and output location.

Customize these files to tailor the behavior of each script according to your preferences.
