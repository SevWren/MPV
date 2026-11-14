# MPV configuration and script development

This repository serves two purposes: it contains a personal mpv configuration, and it is the source tree for scripts developed for that configuration. The repository root is not itself the runtime directory used by the development mpv installation.

## Configuration

- `mpv.conf` contains player-wide options and profiles, including subtitle styling, playback behavior, screenshots, and video output.
- `input.conf` contains custom key bindings for playback, seeking, subtitles, screenshots, and script actions.
- `script-opts/` contains per-script option files. Their names follow each script's `mp.options.read_options` call, which may differ from the script filename or header.

## Scripts

Lua scripts in `scripts/` extend mpv with playlist browsing, contact sheets and thumbnails, seeking, screenshots, encoding, playback behavior, and URL handling. `script-modules/` is the repository location for shared Lua modules when present. `MPV Script Back/` is an archive, not the live source tree.

During development, the running mpv installation loads working copies from:

| Purpose | Runtime location | Repository source |
| --- | --- | --- |
| Scripts | `%APPDATA%\mpv\scripts` | `scripts/` |
| Script options | `%APPDATA%\mpv\script-opts` | `script-opts/` |
| Shared script modules | `%APPDATA%\mpv\script-modules` | `script-modules/` |

Make changes in the repository source directories, then copy or sync the relevant files to the matching `%APPDATA%\mpv\` location before testing them in mpv. Check behavior by loading the configuration and scripts in mpv; this repository has no build system or automated test runner.

## Runtime and repository details

- `playlist-view.lua` and `contact-sheet.lua` load a shared `gallery` module. Their runtime dependency must be available as `gallery.lua` on mpv's `script-modules` path.
- `autoload.lua` and `ytdl_hook.lua` are vendored upstream mpv scripts; edit them only when a local configuration behavior requires it.
- Some output paths in `mpv.conf` and `script-opts/webm.conf` are machine-specific (`D:\ProgramData\asus`). Preserve them unless changing output locations is part of the task.

The repository `scripts/` and `script-opts/` directories are the source of truth when this README and a live file differ. See [AGENTS.md](AGENTS.md) for editing conventions and script-option naming details.
